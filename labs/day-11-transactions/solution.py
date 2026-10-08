"""
Day 11 lab: the lost update, and why transactions exist.

This is the full working solution. The starter file is transactions.py.
Run it:      python3 solution.py

Standard library only (sqlite3, threading). It opens one shared SQLite file and
points many threads at a single bank balance.

The big ideas:
  - A read-modify-write done in three steps (SELECT the balance into Python, add
    1, UPDATE the row back) is NOT safe when more than one thread does it at
    once. Two threads read the same value, both add 1, both write back the same
    number, and one increment just vanishes. That is a lost update.
  - The money really disappears. Start at 0, run 8 threads x 2000 increments,
    and the balance ends far below 16,000. That gap is corrupted money.
  - The fix is a transaction. Either do the whole increment in one statement
    (UPDATE ... SET balance = balance + 1, which the engine runs atomically), or
    wrap the same read-modify-write in BEGIN IMMEDIATE ... COMMIT so a lock is
    held across the read and the write. Same threads, same work. Zero lost.
  - Part 3 names the classic isolation anomalies and shows a real one happening.
"""

import os
import sqlite3
import sys
import threading
import time

PREDICTIONS = {
    # P1: 8 threads each add 1 to the balance 2,000 times, so the correct final
    #     balance is 16,000. In the NAIVE version (read, +1 in Python, write
    #     back), what do you think the balance actually ends at?
    "naive_final_balance": 2200,

    # P2: the lost updates, which is 16,000 minus the naive final balance. How
    #     many increments do you think just vanish?
    "naive_lost_updates": 13800,

    # P3: the first fix, UPDATE ... SET balance = balance + 1. How many lost now?
    "atomic_lost_updates": 0,

    # P4: the second fix, the same read-modify-write wrapped in BEGIN IMMEDIATE.
    #     How many lost now?
    "txn_lost_updates": 0,
}

DB = "bank.db"
PROBE_DB = "bank_probe.db"
N_THREADS = 8
ITERS = 2000
EXPECTED = N_THREADS * ITERS
THINK = 0.0001  # a tiny pause between the read and the write, to widen the race

TODO = "__TODO__"  # sentinel the starter returns from an unfilled TODO


# ---------------------------------------------------------------------------
# The four pieces of the lab. In the starter these are blanked out as TODOs.
# ---------------------------------------------------------------------------

def naive_increment(conn):
    """TODO 1: the unsafe read-modify-write. Read the balance into Python, add
    one, write it back as three separate steps."""
    bal = conn.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
    time.sleep(THINK)  # the gap where another thread sneaks in and reads the same value
    conn.execute("UPDATE accounts SET balance = ? WHERE id = 1", (bal + 1,))


def atomic_increment(conn):
    """TODO 2: the one-line fix. Let the database do the read and the write in a
    single statement, which it runs atomically."""
    conn.execute("UPDATE accounts SET balance = balance + 1 WHERE id = 1")


def txn_increment(conn):
    """TODO 3: the same read-modify-write as the naive version, but wrapped in a
    transaction that grabs the write lock up front. BEGIN IMMEDIATE takes the
    lock now, so no other writer can slip in between the read and the write."""
    conn.execute("BEGIN IMMEDIATE")
    bal = conn.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
    time.sleep(THINK)
    conn.execute("UPDATE accounts SET balance = ? WHERE id = 1", (bal + 1,))
    conn.execute("COMMIT")


def lost_updates(expected, final):
    """TODO 4: how many increments vanished? The correct total minus what the
    balance actually ended at."""
    return expected - final


# ---------------------------------------------------------------------------
# Plumbing.
# ---------------------------------------------------------------------------

def connect(path):
    # isolation_level=None means autocommit: every statement commits on its own,
    # so the naive SELECT and UPDATE are two separate transactions. That is the
    # whole point. busy_timeout makes a writer wait for the lock instead of
    # erroring out with "database is locked".
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def build_db(path):
    for s in ("", "-wal", "-shm", "-journal"):
        if os.path.exists(path + s):
            os.unlink(path + s)
    conn = sqlite3.connect(path)
    # WAL lets many readers run alongside one writer, which makes the race easy
    # to see: readers never block, so they happily read stale values.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance INTEGER)")
    conn.execute("INSERT INTO accounts VALUES (1, 0)")
    conn.commit()
    conn.close()


def reset_balance(path, value=0):
    conn = connect(path)
    conn.execute("UPDATE accounts SET balance = ? WHERE id = 1", (value,))
    conn.close()


def read_balance(path):
    conn = connect(path)
    bal = conn.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
    conn.close()
    return bal


def worker(op, iters):
    conn = connect(DB)
    try:
        for _ in range(iters):
            op(conn)
    finally:
        conn.close()


def run_strategy(op):
    reset_balance(DB, 0)
    threads = [threading.Thread(target=worker, args=(op, ITERS)) for _ in range(N_THREADS)]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start
    return read_balance(DB), elapsed


# ---------------------------------------------------------------------------
# Parts.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: the naive read-modify-write. Watch the money vanish.")
    print("=" * 78)
    final, elapsed = run_strategy(naive_increment)
    lost = lost_updates(EXPECTED, final)
    pct = 100 * lost / EXPECTED
    print(f"  {N_THREADS} threads x {ITERS:,} increments each, starting from 0")
    print(f"  correct final balance:  {EXPECTED:,}")
    print(f"  actual final balance:   {final:,}")
    print(f"  lost updates:           {lost:,}  ({pct:.1f}% of the money, gone)")
    print(f"  (took {elapsed:.2f}s)")
    print("  Each thread read the balance, added 1 in Python, then wrote it back.")
    print("  Two threads read the same number, both wrote the same number+1, and")
    print("  one increment disappeared. Do that thousands of times and most of the")
    print("  money is gone. In a real bank this is a fraud report, not a bug.")
    return final, lost, elapsed


def part2(naive_elapsed):
    print("\n" + "=" * 78)
    print("Part 2: the fix is a transaction. Same threads, same work, zero lost.")
    print("=" * 78)

    atomic_final, atomic_elapsed = run_strategy(atomic_increment)
    atomic_lost = lost_updates(EXPECTED, atomic_final)
    print("  Fix A, one line different: UPDATE accounts SET balance = balance + 1")
    print(f"    final balance:  {atomic_final:,}   lost: {atomic_lost:,}   ({atomic_elapsed:.2f}s)")
    print("    The database reads and writes inside one statement, holding the lock")
    print("    the whole time. No gap for another thread to slip into.")

    txn_final, txn_elapsed = run_strategy(txn_increment)
    txn_lost = lost_updates(EXPECTED, txn_final)
    print("  Fix B, the SAME read-modify-write wrapped in BEGIN IMMEDIATE ... COMMIT:")
    print(f"    final balance:  {txn_final:,}   lost: {txn_lost:,}   ({txn_elapsed:.2f}s)")
    print("    BEGIN IMMEDIATE grabs the write lock up front, so the read and the")
    print("    write are one indivisible unit. Correct, but notice it is slower.")
    if atomic_elapsed > 0:
        print(f"    It ran about {txn_elapsed / atomic_elapsed:.0f}x the one-line fix, because every thread now")
        print("    waits its turn for the lock. That cost is the price of strict isolation.")
    return atomic_final, atomic_lost, txn_final, txn_lost


def part3():
    print("\n" + "=" * 78)
    print("Part 3: the isolation anomalies, and the one you can watch happen.")
    print("=" * 78)
    print("  Weaker isolation lets more anomalies through, in exchange for speed.")
    print("  The classic four, and which level first makes each one safe:")
    print()

    def row(label, a, b, c, d):
        return f"    {label:<21}{a:<18}{b:<16}{c:<17}{d}"

    print(row("anomaly", "read uncommitted", "read committed", "repeatable read", "serializable"))
    print(row("dirty read", "can happen", "safe", "safe", "safe"))
    print(row("non-repeatable read", "can happen", "can happen", "safe", "safe"))
    print(row("phantom read", "can happen", "can happen", "can happen", "safe"))
    print(row("lost update", "can happen", "can happen", "safe", "safe"))
    print()
    print("  Dirty read: you read another transaction's uncommitted change, then it")
    print("    rolls back, so you acted on a number that never existed.")
    print("  Non-repeatable read: you read a row twice in one transaction and get two")
    print("    different values, because someone committed a change in between.")
    print("  Phantom read: you run the same WHERE twice and new rows appear, because")
    print("    someone inserted rows that match.")
    print("  Lost update: exactly Part 1. Two read-modify-writes clobber each other.")
    print()

    # A real non-repeatable read, shown deterministically.
    reset_balance(DB, 1000)
    reader = connect(DB)
    writer = connect(DB)
    first = reader.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
    writer.execute("UPDATE accounts SET balance = 1500 WHERE id = 1")
    second = reader.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
    reader.close()
    writer.close()
    print("  Live demo, a reader in autocommit (read-committed style):")
    print(f"    read balance -> {first},  a writer commits 1500,  read again -> {second}")
    print(f"    the same query gave two answers in a row. That is a non-repeatable read.")

    reset_balance(DB, 1000)
    reader = connect(DB)
    writer = connect(DB)
    reader.execute("BEGIN")  # take a stable snapshot for this transaction
    first = reader.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
    writer.execute("UPDATE accounts SET balance = 1500 WHERE id = 1")
    second = reader.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
    reader.execute("COMMIT")
    after = reader.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
    reader.close()
    writer.close()
    print("  Same thing, but the reader is inside one transaction (snapshot):")
    print(f"    read -> {first},  a writer commits 1500,  read again -> {second},  after commit -> {after}")
    print(f"    inside the transaction the value held steady. The anomaly is gone.")
    print()
    print("  Real engines bend these names. Postgres defaults to read committed, and")
    print("  its 'repeatable read' is actually snapshot isolation. The pattern holds:")
    print("  stronger isolation forbids more anomalies, and serializable forbids all")
    print("  of them by making conflicting transactions run as if one at a time. It is")
    print("  the safest and the costliest, which is the slowdown you saw in Fix B.")


# ---------------------------------------------------------------------------
# Scoreboard and guards.
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<28} actual = {actual:>9,.1f} {unit}  (no prediction)")
        return
    if actual == predicted:
        note = "     spot on"
    elif predicted == 0:
        note = f"  you said 0, got {actual:,.0f}"
    else:
        ratio = actual / predicted
        if 0.7 <= ratio <= 1.4:
            note = "     close enough"
        elif ratio > 1:
            note = f"{ratio:>6.1f}x  too LOW"
        else:
            note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<28} you = {predicted:>8,.1f}   actual = {actual:>9,.1f} {unit}  {note}")


def _probe_op(op):
    conn = connect(PROBE_DB)
    try:
        conn.execute("UPDATE accounts SET balance = 0 WHERE id = 1")
        return op(conn) == TODO
    finally:
        conn.close()


def first_blank_todo():
    """Return the number of the first unfilled TODO, or None if all are done.

    Runs each piece once on a throwaway database, before any threads start, so a
    blank starter stops cleanly here instead of hanging or crashing later.
    """
    build_db(PROBE_DB)
    try:
        if _probe_op(naive_increment):
            return 1
        if _probe_op(atomic_increment):
            return 2
        if _probe_op(txn_increment):
            return 3
        if lost_updates(EXPECTED, 0) is None:
            return 4
        return None
    finally:
        for s in ("", "-wal", "-shm", "-journal"):
            if os.path.exists(PROBE_DB + s):
                os.unlink(PROBE_DB + s)


def cleanup():
    for path in (DB, PROBE_DB):
        for s in ("", "-wal", "-shm", "-journal"):
            if os.path.exists(path + s):
                os.unlink(path + s)


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    blank = first_blank_todo()
    if blank is not None:
        print(f"\n  !! TODO {blank} is not filled in yet. Open this file, complete it,")
        print("     then run again. Each TODO has a comment showing exactly what to write.\n")
        sys.exit(1)

    build_db(DB)
    try:
        naive_final, naive_lost, naive_elapsed = part1()
        atomic_final, atomic_lost, txn_final, txn_lost = part2(naive_elapsed)
        part3()

        print("\n" + "=" * 78)
        print("Scoreboard")
        print("=" * 78)
        verdict("P1 naive final balance", PREDICTIONS["naive_final_balance"], naive_final, "")
        verdict("P2 naive lost updates", PREDICTIONS["naive_lost_updates"], naive_lost, "")
        verdict("P3 atomic fix lost", PREDICTIONS["atomic_lost_updates"], atomic_lost, "")
        verdict("P4 transaction fix lost", PREDICTIONS["txn_lost_updates"], txn_lost, "")

        print("\n" + "=" * 78)
        print("The number to carry")
        print("=" * 78)
        print(f"  Same {N_THREADS} threads, same {EXPECTED:,} increments, three ways of writing one line.")
        print(f"  Naive read-modify-write:  {naive_lost:,} lost updates. Corrupted money.")
        print(f"  Atomic UPDATE + 1:        {atomic_lost} lost. Correct.")
        print(f"  BEGIN IMMEDIATE wrap:     {txn_lost} lost. Correct.")
        print("  The read and the write have to be one indivisible step. That is what a")
        print("  transaction gives you, and it is the whole reason transactions exist.")
        print("\nNow write labs/day-11-transactions/RESULTS.md.\n")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
