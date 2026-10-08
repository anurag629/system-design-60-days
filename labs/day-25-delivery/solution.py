"""
Day 25 lab: delivery semantics and idempotency.

This is the full working solution. The starter file is idempotency.py.
Run it:      python3 solution.py

Standard library only (queue + threading for a real broker and a real consumer).
No files, nothing to clean up. Runs in well under a second.

The story, measured on your own machine:
  - A broker hands a message to a consumer. The consumer processes it (here,
    posts a 100-rupee charge to a ledger) and THEN acks. If it crashes after
    processing but before the ack, the broker never heard the ack, so it
    redelivers the message and the charge is posted AGAIN. Part 1 runs 1000
    payments with a deterministic sprinkling of crashes and counts the duplicate
    charges. The ledger ends up too high.
  - Part 2 keeps the exact same crashes and redeliveries, but gives every message
    a unique id and makes the consumer record the ids it has already applied. A
    redelivered id is now a no-op. The ledger ends up exactly right, zero
    duplicates. That is exactly-once EFFECT on top of at-least-once delivery.
  - Part 3 is the honest part. Flip the order: ack BEFORE processing. Now a crash
    loses the message instead of duplicating it (at-most-once), and the ledger
    ends up too low. You cannot make "process" and "ack" one atomic step across a
    network, so you must pick which way to be wrong. At-least-once plus
    idempotency is the pick that a payment system can live with.

This is the UPI story in miniature: your payment screen says "failed", you tap
again, and you are not charged twice. The retry is at-least-once delivery. The
"not twice" is an idempotency key doing its job behind the scenes.
"""

import collections
import queue
import sys
import threading

PREDICTIONS = {
    # P1: at-least-once, no idempotency. 1000 payments, each a 100-rupee charge.
    #     A deterministic ~10% of deliveries crash AFTER the charge but BEFORE the
    #     ack, so the broker redelivers and the charge is posted again. How many
    #     DUPLICATE charges end up in the ledger?
    "at_least_once_duplicates": 110,

    # P2: same messages, same crashes, same redeliveries, but now each message
    #     carries a unique id and the consumer skips any id it has already
    #     applied. How many duplicate charges now?
    "idempotent_duplicates": 0,

    # P3: flip to ack-BEFORE-processing (at-most-once). A crash after the ack now
    #     loses the message, and the broker never redelivers it. How many charges
    #     are LOST (messages that never hit the ledger at all)?
    "at_most_once_lost": 100,

    # P4: back to at-least-once. Counting the first delivery plus every
    #     redelivery, how many total deliveries did the consumer handle for 1000
    #     messages?
    "at_least_once_deliveries": 1110,
}

# ---------------------------------------------------------------------------
# Knobs. The defaults make the crashes deterministic and the numbers repeatable.
# ---------------------------------------------------------------------------
N = 1000                     # number of payment messages
AMOUNT = 100                 # rupees charged per message
CRASH_P = 0.10               # chance a given delivery's ack is lost to a crash
MAX_CRASHES = 5              # cap on lost acks per message, so it always settles
SEED = 42
JOIN_TIMEOUT = 10            # safety: never hang joining the consumer
MAX_TOTAL_DELIVERIES = N * (MAX_CRASHES + 2)   # safety: never loop forever

SENTINEL = object()          # poison pill that tells the consumer to stop

Message = collections.namedtuple("Message", ["id", "amount"])


# ---------------------------------------------------------------------------
# The crash plan: for each message, how many times its ack gets lost before it
# finally sticks. Drawn once from a seeded RNG so Part 1, Part 2 and Part 3 all
# replay the SAME crashes and the SAME redeliveries.
# ---------------------------------------------------------------------------

def make_crash_counts():
    import random
    rng = random.Random(SEED)
    counts = {}
    for i in range(N):
        c = 0
        while c < MAX_CRASHES and rng.random() < CRASH_P:
            c += 1
        counts[i] = c
    return counts


# ---------------------------------------------------------------------------
# The ledger (the effect), the broker (delivery), and the consumer loop
# ---------------------------------------------------------------------------

class Ledger:
    """The thing a message changes. Here, a running balance plus a count of how
    many times a charge was actually posted. Correct behaviour is exactly one
    post per message."""

    def __init__(self):
        self.balance = 0
        self.applications = 0

    def apply(self, msg):
        self.balance += msg.amount
        self.applications += 1
        return self.balance


class Broker:
    """A toy message broker with at-least-once delivery. It hands messages to the
    consumer over a queue and only forgets a message once it is acked. A message
    whose ack is lost (a crash) is redelivered. crash_counts says, per message,
    how many of its acks get lost before one finally lands."""

    def __init__(self, crash_counts):
        self.queue = queue.Queue()
        self.crash_counts = crash_counts
        self.delivered = collections.defaultdict(int)   # deliveries so far, per id
        self.redeliveries = 0

    def deliver(self, msg):
        self.queue.put(msg)

    def redeliver(self, msg):
        self.redeliveries += 1
        self.queue.put(msg)


def ack_or_retry(msg, broker):
    """Process-then-ack bookkeeping. The broker only drops a message once it is
    acked, so when our ack is lost to a crash the broker redelivers. This message
    has had its ack lost crash_counts[id] times, so the first crash_counts[id]
    deliveries end in a lost ack ('retry') and the next one finally acks."""
    if broker.delivered[msg.id] <= broker.crash_counts[msg.id]:
        return "retry"      # our ack was lost; the broker will hand it to us again
    return "ack"            # ack landed; the broker forgets the message


def handle_at_least_once(msg, broker, ledger):
    """Part 1. Process first, then ack. The charge is posted on EVERY delivery."""
    broker.delivered[msg.id] += 1
    # TODO 1 ------------------------------------------------------------------
    # At-least-once processes on EVERY delivery. Decide whether to post the
    # charge for this delivery. In plain at-least-once the answer is always yes,
    # and that is exactly why a redelivery charges the card a second time.
    #     should_charge = True
    # -------------------------------------------------------------------------
    should_charge = True
    if should_charge:
        ledger.apply(msg)
    return ack_or_retry(msg, broker)


def handle_idempotent(msg, broker, ledger, seen):
    """Part 2. Same at-least-once delivery, but skip any id already applied."""
    broker.delivered[msg.id] += 1
    # TODO 2 ------------------------------------------------------------------
    # The idempotency-key check. Before posting the charge, ask whether this
    # message id has already been applied. If it has, this is a redelivery, so
    # skip the charge. This one check turns N charges into 1, no matter how many
    # times the broker redelivers.
    #     already_applied = msg.id in seen
    # -------------------------------------------------------------------------
    already_applied = msg.id in seen
    if not already_applied:
        ledger.apply(msg)
        seen.add(msg.id)
    return ack_or_retry(msg, broker)


def handle_at_most_once(msg, broker, ledger):
    """Part 3. Ack FIRST, then process. A crash after the ack loses the message,
    and because it is already acked the broker never redelivers it."""
    broker.delivered[msg.id] += 1
    # TODO 3 ------------------------------------------------------------------
    # We acked before processing, so if this delivery crashes the charge is lost
    # for good. A message is lost exactly when it was slated to crash at all,
    # that is, when its crash count is one or more.
    #     lost = broker.crash_counts[msg.id] >= 1
    # -------------------------------------------------------------------------
    lost = broker.crash_counts[msg.id] >= 1
    if lost:
        return "ack"        # acked, then crashed before the charge posted: gone
    ledger.apply(msg)
    return "ack"


def duplicate_count(applications, n_messages):
    """The headline number. The ledger posts one charge per delivery, and the
    correct behaviour is exactly one charge per message, so every charge beyond
    the message count is a duplicate."""
    # TODO 4 ------------------------------------------------------------------
    # How many EXTRA charges (duplicates) ended up in the ledger? It is the
    # number of charges posted minus the number of messages that should each
    # have been charged exactly once.
    #     extra = applications - n_messages
    # -------------------------------------------------------------------------
    extra = applications - n_messages
    return extra


def run_consumer(messages, handler, broker):
    """Load every message into the broker's queue and run ONE consumer thread
    that pulls, processes via `handler`, and acks or asks for redelivery. Returns
    once the queue has fully drained, including every redelivery. The final
    numbers are deterministic regardless of thread timing, and it always
    terminates: crash counts are capped, so every message settles."""
    q = broker.queue

    def consume():
        processed = 0
        while True:
            msg = q.get()
            if msg is SENTINEL:
                q.task_done()
                return
            processed += 1
            if processed > MAX_TOTAL_DELIVERIES:      # hard safety, cannot loop forever
                q.task_done()
                return
            decision = handler(msg)
            if decision == "retry":
                broker.redeliver(msg)                 # put back BEFORE task_done
            q.task_done()

    worker = threading.Thread(target=consume, name="consumer", daemon=True)
    worker.start()
    for m in messages:
        broker.deliver(m)                             # first delivery of each message
    q.join()                                          # waits out every redelivery
    q.put(SENTINEL)
    worker.join(timeout=JOIN_TIMEOUT)


# ---------------------------------------------------------------------------
# The three parts
# ---------------------------------------------------------------------------

def part1(messages, crash_counts, correct_balance):
    print("=" * 78)
    print("Part 1: at-least-once. Process, then ack. A crash before the ack means")
    print("        the broker redelivers, and the charge is posted twice.")
    print("=" * 78)
    broker = Broker(crash_counts)
    ledger = Ledger()
    run_consumer(messages, lambda m: handle_at_least_once(m, broker, ledger), broker)

    duplicates = duplicate_count(ledger.applications, len(messages))
    deliveries = len(messages) + broker.redeliveries

    print(f"  messages sent:                     {len(messages)}")
    print(f"  deliveries handled (with retries): {deliveries}")
    print(f"  charges posted to the ledger:      {ledger.applications}")
    print(f"  duplicate charges:                 {duplicates}")
    print(f"  ledger balance:                    {ledger.balance:,}  (correct is {correct_balance:,})")
    print(f"  overcharged by:                    {ledger.balance - correct_balance:,} rupees")
    print("  Every redelivery ran the charge again, because the handler posts the")
    print("  charge on every delivery. At-least-once delivery means duplicates are")
    print("  not an edge case, they are the normal case under crashes and retries.")
    return duplicates, deliveries, ledger.balance


def part2(messages, crash_counts, correct_balance):
    print("\n" + "=" * 78)
    print("Part 2: idempotency keys. Same crashes, same redeliveries, but each id")
    print("        is applied at most once. The redelivered charge is a no-op.")
    print("=" * 78)
    broker = Broker(crash_counts)
    ledger = Ledger()
    seen = set()
    run_consumer(messages, lambda m: handle_idempotent(m, broker, ledger, seen), broker)

    duplicates = duplicate_count(ledger.applications, len(messages))
    deliveries = len(messages) + broker.redeliveries

    print(f"  messages sent:                     {len(messages)}")
    print(f"  deliveries handled (with retries): {deliveries}")
    print(f"  charges posted to the ledger:      {ledger.applications}")
    print(f"  duplicate charges:                 {duplicates}")
    print(f"  ledger balance:                    {ledger.balance:,}  (correct is {correct_balance:,})")
    print(f"  distinct ids remembered:           {len(seen)}")
    print("  The broker still redelivered exactly as often as in Part 1. The only")
    print("  change is the consumer checked an id against a set before charging.")
    print("  Delivery is still at-least-once. The EFFECT is now exactly-once.")
    return duplicates, deliveries, ledger.balance


def part3(messages, crash_counts, correct_balance):
    print("\n" + "=" * 78)
    print("Part 3: why exactly-once DELIVERY is a lie. Ack BEFORE processing, and")
    print("        a crash loses the message instead of duplicating it.")
    print("=" * 78)
    broker = Broker(crash_counts)
    ledger = Ledger()
    run_consumer(messages, lambda m: handle_at_most_once(m, broker, ledger), broker)

    lost = len(messages) - ledger.applications
    deliveries = len(messages) + broker.redeliveries

    print(f"  messages sent:                     {len(messages)}")
    print(f"  deliveries handled (no retries):   {deliveries}")
    print(f"  charges posted to the ledger:      {ledger.applications}")
    print(f"  lost charges (never posted):       {lost}")
    print(f"  ledger balance:                    {ledger.balance:,}  (correct is {correct_balance:,})")
    print(f"  undercharged by:                   {correct_balance - ledger.balance:,} rupees")
    print("  Acking first means a crash takes the message with it, and because the")
    print("  broker was told the message was done, it never comes back. That is")
    print("  at-most-once: no duplicates, but silent loss. Process-first gives")
    print("  duplicates; ack-first gives loss. You cannot ack and process as one")
    print("  atomic action across a network, so one of these two is always your")
    print("  reality. The honest answer is at-least-once plus Part 2's idempotency.")
    return lost, deliveries, ledger.balance


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>6,} {unit}  (no prediction)")
        return
    if abs(actual - predicted) <= 1:
        note = "     close enough"
    elif predicted and 0.6 <= actual / predicted <= 1.6:
        note = "     close enough"
    elif actual > predicted:
        note = "     too LOW"
    else:
        note = "     too HIGH"
    print(f"  {name:<34} you = {predicted:>5,}   actual = {actual:>6,} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    messages = [Message(i, AMOUNT) for i in range(N)]
    crash_counts = make_crash_counts()
    correct_balance = N * AMOUNT

    al_dupes, al_deliveries, al_balance = part1(messages, crash_counts, correct_balance)
    idem_dupes, idem_deliveries, idem_balance = part2(messages, crash_counts, correct_balance)
    amo_lost, amo_deliveries, amo_balance = part3(messages, crash_counts, correct_balance)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 at-least-once duplicates", PREDICTIONS["at_least_once_duplicates"], al_dupes)
    verdict("P2 idempotent duplicates", PREDICTIONS["idempotent_duplicates"], idem_dupes)
    verdict("P3 at-most-once lost", PREDICTIONS["at_most_once_lost"], amo_lost)
    verdict("P4 at-least-once deliveries", PREDICTIONS["at_least_once_deliveries"], al_deliveries)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Same 1000 payments, same crashes, same redeliveries.")
    print(f"  At-least-once, no key:   {al_dupes} duplicate charges, ledger {al_balance:,} (too high).")
    print(f"  At-least-once + idem key: {idem_dupes} duplicates, ledger {idem_balance:,} (exactly right).")
    print(f"  At-most-once (ack first): {amo_lost} lost charges, ledger {amo_balance:,} (too low).")
    print(f"  Exactly-once delivery would mean zero duplicates AND zero loss with")
    print(f"  no dedupe logic. Nobody can promise that across a network. What you")
    print(f"  CAN have is at-least-once delivery and an idempotency key, which is")
    print(f"  how a UPI retry after a 'failed' screen does not charge you twice.")
    print("\nNow write labs/day-25-delivery/RESULTS.md.\n")


if __name__ == "__main__":
    main()
