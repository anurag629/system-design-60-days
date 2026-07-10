"""
Day 2 lab: predict six numbers, then measure them.

Run it:      python3 estimate.py
Clean up:    rm -f messages.db*

Fill in PREDICTIONS below BEFORE you run anything. That is the whole exercise.
An estimate you make after seeing the answer is not an estimate.

Then fill in the four TODOs. SQLite ships with Python, so nothing to install.
Takes about 15 seconds to run.
"""

import os
import random
import sqlite3
import string
import sys
import time

# ---------------------------------------------------------------------------
# YOUR PREDICTIONS. Fill these in first. Paper, then here, then run.
# ---------------------------------------------------------------------------

PREDICTIONS = {
    # P1: total size of the .db file after 1,000,000 rows, in megabytes.
    #     Each row is roughly 8 + 8 + 200 + 8 = 224 bytes of actual data.
    "db_size_mb": None,

    # P2: seconds to insert 1,000,000 rows inside ONE transaction.
    "bulk_insert_seconds": None,

    # P3: rows per second when each row is its own transaction, with REAL
    #     durability (the database waits for the SSD to confirm the bytes
    #     physically landed). Yesterday you measured a 4 KB SSD read at ~85 us.
    #     A durable write costs more than a read. Reason from that.
    "durable_rows_per_sec": None,

    # P4: percent the file grows when you add an index on user_id (30 = 30%).
    "index_size_pct": None,

    # P5: milliseconds to find all rows for one user_id WITHOUT an index.
    "scan_ms": None,

    # P6: milliseconds for the same lookup WITH the index.
    "indexed_ms": None,
}

# ---------------------------------------------------------------------------

DB = "messages.db"
N_ROWS = 1_000_000
BODY_LEN = 200
N_USERS = 10_000

# One durable commit takes hundreds of microseconds, so a million of them would
# take several minutes. We measure this many and multiply.
#
# Extrapolation is a legitimate estimation tool. The only rule is that you say
# out loud that you used one, which is what this constant exists to make you do.
DURABLE_SAMPLE = 10_000


def fresh_db(journal="WAL", synchronous="FULL", fullfsync=1):
    """Open a brand new database with durability settings made explicit.

    Three knobs, and every database on earth has some version of all three.

    journal_mode
        How the database records what it is about to do, so a crash mid-write
        can be undone. WAL (write-ahead log) is what nearly everything uses in
        production, including Postgres and MySQL, under different names.

    synchronous
        FULL - call fsync() on every commit and wait for it.
        OFF  - hand the bytes to the operating system and immediately report
               success. Fast. Also a lie: a power cut loses committed data.

    fullfsync                                        <-- macOS only, and it matters
        On macOS, plain fsync() returns as soon as the SSD *accepts* the write
        into its own internal buffer. Not when the data is actually stored.
        Apple provides F_FULLFSYNC for people who meant it. SQLite exposes it
        as this pragma. On Linux, fsync() already does the real thing and this
        pragma is ignored.

        So a benchmark on a Mac with fullfsync off is measuring a database that
        merely *believes* it is durable. Yesterday the page cache lied to you
        about where your data was being read from. Today the disk lies to you
        about whether your data got written. Same shape. Different layer.
    """
    for suffix in ("", "-wal", "-shm", "-journal"):
        if os.path.exists(DB + suffix):
            os.unlink(DB + suffix)
    conn = sqlite3.connect(DB)
    conn.execute(f"PRAGMA journal_mode = {journal}")
    conn.execute(f"PRAGMA synchronous = {synchronous}")
    conn.execute(f"PRAGMA fullfsync = {fullfsync}")
    conn.execute("""
        CREATE TABLE messages (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER,
            body       TEXT,
            created_at INTEGER
        )
    """)
    conn.commit()
    return conn


def rows(n):
    """Generate n rows. Body is exactly BODY_LEN characters."""
    body = "".join(random.choices(string.ascii_letters, k=BODY_LEN))
    now = 1_752_000_000
    for i in range(n):
        yield (i + 1, random.randrange(N_USERS), body, now + i)


def file_mb(conn):
    """Size of the database, in MB, after folding the write-ahead log back in.

    A gotcha that cost me an hour: in WAL mode the recent writes live in a
    SEPARATE file, `messages.db-wal`, and only get merged into the main file at
    a checkpoint. If you just call getsize() on the main file you undercount. If
    you add both together you overcount, because the WAL still holds pages that
    are also already in the main file.

    So: checkpoint first, then measure. Otherwise you can watch a database
    apparently SHRINK by 45% when you add an index to it, which is what my
    first version of this lab confidently reported.
    """
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    return os.path.getsize(DB) / (1024 * 1024)


def verdict(name, predicted, actual, unit=""):
    """Print your guess next to the truth, and how far off you were."""
    if predicted is None:
        print(f"  {name:<24} actual = {actual:>12,.3f} {unit:<6}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.9 <= ratio <= 1.1:
        note = "     nailed it"
    elif ratio > 1:
        note = f"{ratio:>7.1f}x  too LOW"
    else:
        note = f"{1/ratio:>7.1f}x  too HIGH"
    print(f"  {name:<24} you = {predicted:>10,.3f}   "
          f"actual = {actual:>12,.3f} {unit:<6}  {note}")


# ---------------------------------------------------------------------------
# 1 & 2. Bulk insert: how fast, and how big?
# ---------------------------------------------------------------------------

def measure_bulk():
    """One transaction around a million inserts.

    Note what this actually means: SQLite writes all million rows, then calls
    fsync ONCE, at commit. The cost of durability is paid a single time instead
    of a million times.

    That is the entire trick behind every write-ahead log, every message queue,
    and every "we buffer writes and flush every 100ms" you have ever read about.
    """
    print("\n[1+2] Bulk insert: 1,000,000 rows in ONE transaction")
    conn = fresh_db()

    # TODO 1 ------------------------------------------------------------------
    # Time the insert. `executemany` streams the generator straight into SQLite.
    #
    #   start = time.perf_counter()
    #   conn.executemany("INSERT INTO messages VALUES (?, ?, ?, ?)", rows(N_ROWS))
    #   conn.commit()
    #   elapsed = time.perf_counter() - start
    # -------------------------------------------------------------------------
    elapsed = None  # <-- replace this

    if elapsed is None:
        print("  (fill in TODO 1)")
        conn.close()
        return None, None

    size = file_mb(conn)
    naive = N_ROWS * (8 + 8 + BODY_LEN + 8) / (1024 * 1024)

    print(f"  inserted in {elapsed:.2f}s   ({N_ROWS/elapsed:,.0f} rows/sec)")
    print(f"  naive estimate (just add up the field sizes): {naive:>7.1f} MB")
    print(f"  actual file size on disk:                     {size:>7.1f} MB")
    print(f"  overhead factor: {size/naive:.2f}x  "
          f"({size*1024*1024/N_ROWS:.1f} bytes per row)")
    conn.close()
    return size, elapsed


def measure_narrow_rows():
    """The same question for a skinny row, and the answer flips sign.

    Everyone's instinct for "how big is my table" is to add up the declared field
    sizes. Watch what that instinct does on two different shapes of row.
    """
    print("\n[1b] The same question, for a row with no text in it")
    path = "narrow.db"
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(path + suffix):
            os.unlink(path + suffix)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("CREATE TABLE narrow (id INTEGER PRIMARY KEY, user_id INTEGER)")
    conn.executemany("INSERT INTO narrow VALUES (?, ?)",
                     ((i + 1, i % N_USERS) for i in range(N_ROWS)))
    conn.commit()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    size = os.path.getsize(path) / (1024 * 1024)
    conn.close()
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(path + suffix):
            os.unlink(path + suffix)

    naive = N_ROWS * 16 / (1024 * 1024)  # two 8-byte integers
    print(f"  two INTEGER columns. naive: 8 + 8 = 16 bytes per row.")
    print(f"  naive estimate:  {naive:>7.1f} MB")
    print(f"  actual:          {size:>7.1f} MB   "
          f"({size*1024*1024/N_ROWS:.1f} bytes per row)")
    print(f"  overhead factor: {size/naive:.2f}x")
    print()
    print("  So the fat row came out slightly BIGGER than the naive sum, and the")
    print("  narrow row came out considerably SMALLER. Adding up field sizes is")
    print("  wrong in both directions, and you cannot even guess the sign without")
    print("  knowing how the engine encodes a value. SQLite stores small integers")
    print("  in as little as one byte, not eight. Meanwhile every row also carries")
    print("  a header, and rows live inside fixed-size pages that are never quite")
    print("  full. Two effects, pulling opposite ways. Week 2 is about those pages.")
    return size


# ---------------------------------------------------------------------------
# 3. Durable insert: one commit per row, three levels of honesty
# ---------------------------------------------------------------------------

def _commit_loop(conn, data):
    start = time.perf_counter()
    for r in data:
        conn.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", r)
        conn.commit()
    return time.perf_counter() - start


def measure_durable():
    """One transaction per row, at three different levels of "we mean it".

    This is what your ORM does when you write:
        for row in rows:
            session.add(row)
            session.commit()

    It is also what a REST endpoint does when it writes one record per request
    and nobody thought about batching.

    Expect the first number to be shockingly bad. That is the lesson. Expect the
    gap between the first and second to bother you. That is the better lesson.
    """
    print(f"\n[3] Durable insert: {DURABLE_SAMPLE:,} rows, ONE transaction each")
    data = list(rows(DURABLE_SAMPLE))
    results = {}

    # TODO 2 ------------------------------------------------------------------
    # Run the same loop under three configurations and record rows/sec for each.
    # The helper `_commit_loop(conn, data)` above returns elapsed seconds.
    #
    #   configs = [
    #       ("real durability   (fullfsync=1)", dict(synchronous="FULL", fullfsync=1)),
    #       ("plain fsync       (fullfsync=0)", dict(synchronous="FULL", fullfsync=0)),
    #       ("no durability     (sync=OFF)   ", dict(synchronous="OFF",  fullfsync=0)),
    #   ]
    #   for label, kw in configs:
    #       conn = fresh_db(**kw)
    #       elapsed = _commit_loop(conn, data)
    #       conn.close()
    #       results[label] = DURABLE_SAMPLE / elapsed
    #
    # Store rows/sec per label in `results`.
    # -------------------------------------------------------------------------
    # <-- write it here

    if not results:
        print("  (fill in TODO 2)")
        return None

    for label, rate in results.items():
        us = 1e6 / rate
        print(f"  {label}  {rate:>10,.0f} rows/sec   {us:>8,.0f} us per commit")

    real = list(results.values())[0]
    print(f"\n  EXTRAPOLATED: at the durable rate, 1,000,000 rows would take "
          f"{N_ROWS/real/60:,.1f} minutes.")
    print(f"  (we measured {DURABLE_SAMPLE:,} and multiplied. always say so.)")
    return results


# ---------------------------------------------------------------------------
# 4, 5, 6. Indexes: what they cost and what they buy
# ---------------------------------------------------------------------------

def plan(conn, sql):
    return " / ".join(r[-1] for r in conn.execute("EXPLAIN QUERY PLAN " + sql))


def measure_index():
    print("\n[4+5+6] Index: what it costs and what it buys")
    conn = fresh_db(synchronous="OFF")  # not timing writes here
    conn.executemany("INSERT INTO messages VALUES (?, ?, ?, ?)", rows(N_ROWS))
    conn.commit()
    size_before = file_mb(conn)
    target = random.randrange(N_USERS)
    q = "SELECT COUNT(*) FROM messages WHERE user_id = ?"

    print(f"  before index, the planner says:  {plan(conn, q.replace('?', '1'))}")

    # TODO 3 ------------------------------------------------------------------
    # Time the lookup with NO index. This is a full table scan: SQLite reads all
    # 1,000,000 rows and checks each one.
    #
    #   start = time.perf_counter()
    #   conn.execute(q, (target,)).fetchone()
    #   scan_ms = (time.perf_counter() - start) * 1000
    # -------------------------------------------------------------------------
    scan_ms = None  # <-- replace this

    start = time.perf_counter()
    conn.execute("CREATE INDEX idx_user ON messages(user_id)")
    conn.commit()
    build_s = time.perf_counter() - start
    size_after = file_mb(conn)

    print(f"  after index,  the planner says:  {plan(conn, q.replace('?', '1'))}")

    # TODO 4 ------------------------------------------------------------------
    # Time the identical lookup now that the index exists. Same query, same
    # target. Run it 5 times and keep the BEST.
    #
    # Why the best and not the average? The first call pays to warm caches, and
    # yesterday taught you not to trust a cold first measurement. We want the
    # cost of the operation, not the cost of the operation plus a page fault.
    #
    #   best = float("inf")
    #   for _ in range(5):
    #       start = time.perf_counter()
    #       conn.execute(q, (target,)).fetchone()
    #       best = min(best, (time.perf_counter() - start) * 1000)
    #   indexed_ms = best
    # -------------------------------------------------------------------------
    indexed_ms = None  # <-- replace this

    if scan_ms is None or indexed_ms is None:
        print("  (fill in TODO 3 and TODO 4)")
        conn.close()
        return None, None, None

    pct = (size_after - size_before) / size_before * 100
    print(f"\n  file before index: {size_before:>8.1f} MB")
    print(f"  file after index:  {size_after:>8.1f} MB   (+{pct:.1f}%)")
    print(f"  index built in {build_s:.2f}s")
    print(f"  lookup, full scan: {scan_ms:>8.2f} ms   "
          f"({scan_ms*1e6/N_ROWS:.0f} ns per row examined)")
    print(f"  lookup, indexed:   {indexed_ms:>8.3f} ms  "
          f"({scan_ms/indexed_ms:,.0f}x faster)")
    print("\n  Read the two planner lines above. SCAN means it looked at every")
    print("  row. SEARCH means it jumped straight to the ones it needed. Getting")
    print("  a database to tell you which one it plans to do, before you ship the")
    print("  query, is the single most useful habit in week 2.")
    conn.close()
    return pct, scan_ms, indexed_ms


# ---------------------------------------------------------------------------

def main():
    random.seed(7)
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! You have not written down a single prediction.")
        print("     Open this file, fill in PREDICTIONS, then run again.")
        print("     Measuring without predicting teaches you almost nothing.\n")
        sys.exit(1)

    print("=" * 78)
    print("Prediction vs reality")
    print("=" * 78)

    size, bulk_s = measure_bulk()
    measure_narrow_rows()
    durable = measure_durable()
    pct, scan_ms, indexed_ms = measure_index()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    if size:
        verdict("P1 db size", PREDICTIONS["db_size_mb"], size, "MB")
    if bulk_s:
        verdict("P2 bulk insert", PREDICTIONS["bulk_insert_seconds"], bulk_s, "s")
    if durable:
        verdict("P3 durable rows/sec", PREDICTIONS["durable_rows_per_sec"],
                list(durable.values())[0], "rows/s")
    if pct:
        verdict("P4 index size", PREDICTIONS["index_size_pct"], pct, "%")
        verdict("P5 scan", PREDICTIONS["scan_ms"], scan_ms, "ms")
        verdict("P6 indexed lookup", PREDICTIONS["indexed_ms"], indexed_ms, "ms")

    if durable and bulk_s:
        rates = list(durable.values())
        real, lying, none_ = rates[0], rates[1], rates[2]
        batched = N_ROWS / bulk_s
        print("\n" + "=" * 78)
        print("The two numbers to carry")
        print("=" * 78)
        print(f"  one commit per row, real durability: {real:>12,.0f} rows/sec")
        print(f"  one commit per row, fsync that lies: {lying:>12,.0f} rows/sec")
        print(f"  one commit per row, no durability:   {none_:>12,.0f} rows/sec")
        print(f"  one commit for all of them:          {batched:>12,.0f} rows/sec")
        print()
        print(f"  1. Batching buys you {batched/real:,.0f}x. It is the cheapest")
        print("     performance win in all of systems engineering, and it costs")
        print("     you nothing but a slightly later durability guarantee.")
        print()
        print(f"  2. Turning off fullfsync makes you {lying/real:.1f}x faster and")
        print("     silently stops your data from reaching the disk. The benchmark")
        print("     gets better. The database gets worse. Nothing warns you.")

    print("\nNow write labs/day-02-estimation/RESULTS.md.\n")


if __name__ == "__main__":
    main()
