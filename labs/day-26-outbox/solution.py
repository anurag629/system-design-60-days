"""
Day 26 lab: the outbox pattern and the dual-write problem.

This is the full working solution. The starter file is outbox.py.
Run it:      python3 solution.py

Standard library only (sqlite3 is the database, a plain list is the "queue").
Single threaded and deterministic, runs in a couple of seconds, and deletes the
database file it makes.

The story, measured on your own machine:
  - The dual write. You place an order: first you INSERT the order row and commit
    it, then, as a SECOND step, you publish an event to the queue so downstream
    work (email, inventory, the week 3 fan-out) can happen. If the process dies
    after the commit but before the publish, the order is in the database and the
    event is simply gone. Part 1 runs many orders with occasional publish crashes
    and counts the orders whose event vanished. That count is a permanent, silent
    inconsistency: nothing in the logs, nothing retries it, it is just wrong.
  - The outbox. Write the order row AND an "outbox" row in the SAME database
    transaction, so they commit together or not at all. A separate relay reads
    unsent outbox rows, publishes them, and marks them sent. A crash anywhere
    leaves the outbox row intact, so the relay just retries later. Part 2 re-runs
    the same crashes and shows zero lost events.
  - The catch. The relay is at-least-once: it can publish an event, crash before
    it marks the row sent, and publish the same event again on the next pass. So
    the queue now holds duplicates. Part 3 counts them and shows the fix is the
    Day 25 idempotency key: dedupe on it and every order is processed exactly
    once. The outbox fixes "did the event get out at all". Idempotency fixes "did
    it get out twice".
"""

import os
import random
import sqlite3
import sys

PREDICTIONS = {
    # P1: the naive dual write. 5,000 orders, and the publish step crashes about
    #     20% of the time AFTER the order is already committed. How many orders
    #     end up in the database with NO event published (lost, silent)?
    "naive_lost_events": 1000,

    # P2: the outbox. Same 5,000 orders, the same crash rate, but now the event
    #     is written in the same transaction and a relay retries. How many orders
    #     end up with no event at all?
    "outbox_lost_events": 0,

    # P3: the relay is at-least-once. It can publish and then crash before it
    #     marks the row sent, so it republishes on the next pass. How many
    #     DUPLICATE events (copies beyond the 5,000 the orders needed) land in
    #     the queue?
    "outbox_duplicate_events": 700,

    # P4: a consumer that dedupes on the event's idempotency key. After the
    #     outbox (nothing lost) and idempotency (nothing processed twice), how
    #     many distinct orders are delivered downstream exactly once?
    "idempotent_distinct_delivered": 5000,
}

DB_PATH = "outbox_demo.db"
N_ORDERS = 5000
FAIL_PROB = 0.20          # a publish / relay step crashes this often
RELAY_FAILURE_PASSES = 6  # the first few relay passes can crash; after that the
                          # relay keeps running cleanly until the outbox drains,
                          # the way a real relay eventually gets a clean pass
MAX_RELAY_PASSES = 60     # a seatbelt so the relay loop can never spin forever
SEED = 42


def fresh_db():
    """A clean database with an orders table and an outbox table."""
    if os.path.exists(DB_PATH):
        os.unlink(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, item TEXT, amount INTEGER)")
    conn.execute("CREATE TABLE outbox (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                 "order_id INTEGER, payload TEXT, sent INTEGER NOT NULL DEFAULT 0)")
    conn.commit()
    return conn


def event_for(order_id):
    """The event we want downstream to see for one order. The order id doubles
    as the idempotency key, so a republished event is recognisably the same."""
    return "order_placed:" + str(order_id)


def naive_publish(queue, order_id):
    """Publish one order's event to the queue, the SECOND write of the dual
    write. In the naive design this is a separate step from the DB commit."""
    queue.append(event_for(order_id))


def idempotent_deliveries(queue):
    """A consumer that dedupes on each event's idempotency key, so a republished
    event is acted on only once. Returns how many events it actually processes."""
    seen = set()
    processed = 0
    for ev in queue:
        if ev not in seen:
            seen.add(ev)
            processed += 1
    return processed


# ---------------------------------------------------------------------------
# Part 1: the dual write. Commit the order, then publish as a second step.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: the dual write. Order to the DB, event to the queue, SEPARATELY.")
    print("=" * 78)
    conn = fresh_db()
    rng = random.Random(SEED)
    queue = []        # the "event stream": a plain in-memory list
    lost = 0

    for order_id in range(1, N_ORDERS + 1):
        # Step one: write the business row and commit it. After this line the
        # order is durable. A customer has been told "order placed".
        conn.execute("INSERT INTO orders (id, item, amount) VALUES (?, ?, ?)",
                     (order_id, "widget", 100))
        conn.commit()

        # The process can die right here, after the commit, before the publish.
        if rng.random() < FAIL_PROB:
            lost += 1          # the event is gone, and nothing will ever retry it
            continue

        # Step two, a SEPARATE write to a SEPARATE system. This is the dual write.
        naive_publish(queue, order_id)

    orders_in_db = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()

    print(f"  orders committed to the database:   {orders_in_db}")
    print(f"  events published to the queue:      {len(queue)}")
    print(f"  orders with a LOST event:           {lost}")
    print("  Every one of these orders is in the database, the customer was told")
    print("  it went through, but no event was ever published. The email never")
    print("  goes out, inventory is never decremented, the fan-out never fires.")
    print("  Nothing errored, nothing retries. It is a silent, permanent lie.")
    return lost


# ---------------------------------------------------------------------------
# Part 2: the outbox. Order row and outbox row in ONE transaction, plus a relay.
# ---------------------------------------------------------------------------

def place_order_with_outbox(conn, order_id):
    """Write the order and its outbox row in the SAME transaction."""
    conn.execute("INSERT INTO orders (id, item, amount) VALUES (?, ?, ?)",
                 (order_id, "widget", 100))
    # The outbox row rides in the SAME transaction as the order. Either both land
    # or neither does. There is no window where the order exists but the event
    # was never recorded.
    conn.execute("INSERT INTO outbox (order_id, payload) VALUES (?, ?)",
                 (order_id, event_for(order_id)))
    conn.commit()


def relay_pass(conn, queue, rng, inject_failures):
    """One sweep of the relay: publish unsent outbox rows, mark them sent.

    Returns the number of rows that were still unsent at the start of the pass.
    A real relay is a separate process looping forever; we call it pass by pass.
    """
    rows = conn.execute("SELECT id, order_id FROM outbox WHERE sent = 0").fetchall()
    for row_id, order_id in rows:
        if inject_failures and rng.random() < FAIL_PROB:
            # The relay crashes on this row. Two ways it can happen:
            if rng.random() < 0.5:
                # it already published, then died before marking the row sent.
                # The event IS in the queue, but the row stays unsent, so the
                # next pass will publish it AGAIN. This is where duplicates come
                # from, and it is exactly why at-least-once is the best you get.
                queue.append(event_for(order_id))
            # otherwise it died before publishing: nothing in the queue, row
            # stays unsent, next pass retries. Either way, the row is NOT lost.
            continue

        # The healthy path: publish, THEN mark sent. The order matters. If we
        # marked sent first and crashed, we would lose the event, which is the
        # whole bug we are trying to kill.
        queue.append(event_for(order_id))
        conn.execute("UPDATE outbox SET sent = 1 WHERE id = ?", (row_id,))
    conn.commit()
    return len(rows)


def part2():
    print("\n" + "=" * 78)
    print("Part 2: the outbox. One transaction for both, a relay that retries.")
    print("=" * 78)
    conn = fresh_db()
    rng = random.Random(SEED + 1)
    queue = []

    # Place every order. Order row and outbox row commit atomically.
    for order_id in range(1, N_ORDERS + 1):
        place_order_with_outbox(conn, order_id)

    # Run the relay. The first few passes can crash; after that it runs cleanly
    # and keeps going until the outbox is fully drained.
    passes = 0
    while passes < MAX_RELAY_PASSES:
        inject = passes < RELAY_FAILURE_PASSES
        remaining = relay_pass(conn, queue, rng, inject)
        passes += 1
        if remaining == 0:
            break

    orders_in_db = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    outbox_rows = conn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
    unsent = conn.execute("SELECT COUNT(*) FROM outbox WHERE sent = 0").fetchone()[0]
    conn.close()

    distinct_delivered = len(set(queue))
    lost = orders_in_db - distinct_delivered
    duplicates = len(queue) - distinct_delivered

    print(f"  orders committed to the database:   {orders_in_db}")
    print(f"  outbox rows written (same txn):     {outbox_rows}")
    print(f"  relay passes until fully drained:   {passes}")
    print(f"  outbox rows still unsent:           {unsent}")
    print(f"  distinct orders delivered:          {distinct_delivered}")
    print(f"  orders with a LOST event:           {lost}")
    print("  The relay crashed on plenty of rows, but a crash only ever leaves")
    print("  the outbox row unsent, never lost. The next pass picks it up. So the")
    print("  database and the event stream end up agreeing on every single order.")
    return lost, duplicates, distinct_delivered, queue


# ---------------------------------------------------------------------------
# Part 3: the at-least-once catch, and the idempotency fix from Day 25.
# ---------------------------------------------------------------------------

def part3(queue, distinct_delivered, duplicates):
    print("\n" + "=" * 78)
    print("Part 3: at-least-once. The relay can publish twice, so consumers dedupe.")
    print("=" * 78)
    total_events = len(queue)

    # A consumer that trusts the stream blindly does the downstream work once per
    # event, so every duplicate is a second email, a double stock decrement, a
    # repeated charge.
    naive_side_effects = total_events

    # An idempotent consumer remembers the idempotency key of each event it has
    # already handled and skips repeats. (Here the key is the event string; in a
    # real system it is the outbox row id or an explicit idempotency key.)
    idempotent_side_effects = idempotent_deliveries(queue)

    print(f"  events sitting in the queue:        {total_events}")
    print(f"  of those, duplicate copies:         {duplicates}")
    print(f"  naive consumer, work done:          {naive_side_effects}  (over-counts!)")
    print(f"  idempotent consumer, work done:     {idempotent_side_effects}")
    print("  The outbox guaranteed nothing was LOST, but it hands you duplicates.")
    print("  That is at-least-once, and it is the best a relay can promise. The")
    print("  idempotency key from Day 25 turns at-least-once into effectively")
    print("  exactly-once at the consumer: each order is acted on one time.")
    return idempotent_side_effects


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>7,} {unit}  (no prediction)")
        return
    if abs(actual - predicted) <= 1:
        note = "     close enough"
    elif predicted and 0.6 <= actual / predicted <= 1.6:
        note = "     close enough"
    elif actual > predicted:
        note = "     too LOW"
    else:
        note = "     too HIGH"
    print(f"  {name:<34} you = {predicted:>6,}   actual = {actual:>7,} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    try:
        naive_lost = part1()
        outbox_lost, duplicates, distinct_delivered, queue = part2()
        idempotent_delivered = part3(queue, distinct_delivered, duplicates)

        print("\n" + "=" * 78)
        print("Scoreboard")
        print("=" * 78)
        verdict("P1 naive lost events", PREDICTIONS["naive_lost_events"], naive_lost)
        verdict("P2 outbox lost events", PREDICTIONS["outbox_lost_events"], outbox_lost)
        verdict("P3 outbox duplicate events", PREDICTIONS["outbox_duplicate_events"], duplicates)
        verdict("P4 idempotent distinct delivered", PREDICTIONS["idempotent_distinct_delivered"], idempotent_delivered)

        print("\n" + "=" * 78)
        print("The number to carry")
        print("=" * 78)
        print(f"  Same {N_ORDERS:,} orders, same {int(FAIL_PROB * 100)}% crash rate, two designs.")
        print(f"  Dual write:  {naive_lost} orders committed with their event LOST forever,")
        print(f"               silently. No error, no retry, just permanent drift.")
        print(f"  Outbox:      {outbox_lost} lost. The event rides the same transaction as the")
        print(f"               order, and the relay retries until it is delivered.")
        print(f"  The relay's price is at-least-once: {duplicates} duplicate copies in the")
        print(f"  queue. The Day 25 idempotency key collapses them, so all {idempotent_delivered:,}")
        print(f"  orders are acted on exactly once. Outbox stops loss, idempotency")
        print(f"  stops doubles. You need both.")
        print("\nNow write labs/day-26-outbox/RESULTS.md.\n")
    finally:
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)


if __name__ == "__main__":
    main()
