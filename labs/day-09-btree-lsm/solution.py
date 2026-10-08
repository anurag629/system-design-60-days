"""
Day 9 lab: the two families of storage engine, B-tree and LSM tree.

This is the full working solution. The starter file is storage_engines.py.
Run it:      python3 solution.py

Standard library only (sqlite3 is the B-tree). Runs in a few seconds, cleans up
every file it makes.

The big ideas, all measured on your own machine:
  - A B-tree (SQLite, Postgres, MySQL) keeps data sorted and updates it in
    place. Great for reads. But random-key writes are expensive: the tree splits
    pages and writes land scattered all over the file. Sequential keys just keep
    extending the rightmost leaf. Part 1 times both and the gap is large.
  - An LSM tree (RocksDB, Cassandra, LevelDB) never updates in place. It appends
    to an in-memory memtable, and flushes sorted runs to disk. Appending does not
    look at the key, so the write path is flat whether keys arrive in order or
    shuffled. Part 2 shows that flatness.
  - Nothing is free. An LSM read has to check the memtable plus every sorted run,
    so a point read touches several places where a B-tree walks one path. Part 3
    counts those places. That read tax is why real LSMs add bloom filters and
    compaction.
"""

import bisect
import glob
import os
import random
import sqlite3
import sys
import time

PREDICTIONS = {
    # P1: inserting 300,000 rows with RANDOM primary keys vs SEQUENTIAL ones,
    #     into the same B-tree. How many times SLOWER is random?
    "btree_random_slowdown_x": 10,

    # P2: the LSM write path is append-to-memtable. Writing the same 300,000
    #     rows in random key order vs sequential order. What is the time ratio
    #     random / sequential? (1.0 means key order does not matter at all.)
    "lsm_write_ratio_x": 1.0,

    # P3: the LSM flushes a sorted run every 70,000 writes. For 300,000 writes,
    #     how many sorted runs land on disk?
    "lsm_sorted_runs": 4,

    # P4: to answer a point read, the LSM checks the memtable plus every run.
    #     For a key that is absent, how many places must it touch? (A B-tree
    #     walks exactly one root-to-leaf path.)
    "lsm_read_places": 5,
}

ROW_DB = "btree_seq.db"
RND_DB = "btree_rnd.db"
RUN_DIR = "lsm_runs"
WAL = "lsm_wal.log"

N = 300_000
PAYLOAD = "x" * 100          # a ~100-byte value on every row
CACHE_PAGES = 2000           # pin SQLite's page cache to 8 MB, so the result
                             # does not depend on your build's default
PAGE_BYTES = 4096
COMMIT_EVERY = 5_000         # a realistic durable workload commits in batches
FLUSH_EVERY = 70_000         # memtable size before the LSM flushes a sorted run
SEED = 42


def wipe(*paths):
    for path in paths:
        for suffix in ("", "-wal", "-shm", "-journal"):
            if os.path.exists(path + suffix):
                os.unlink(path + suffix)


def clean_runs():
    for f in glob.glob(os.path.join(RUN_DIR, "*")):
        os.unlink(f)
    if os.path.isdir(RUN_DIR):
        os.rmdir(RUN_DIR)
    wipe(WAL)


def make_keys():
    """Sequential keys 1..N, and N unique random keys over a huge range.

    Both key sets hold the same number of unique keys and the same payload. The
    only thing that differs is the order the B-tree sees them in.
    """
    random.seed(SEED)
    sequential = list(range(1, N + 1))
    random_keys = random.sample(range(1, 2 ** 62), N)
    return sequential, random_keys


def btree_insert(path, keys, insert_sql):
    """Insert every key into a fresh SQLite B-tree, committing in batches.

    synchronous is OFF, so there is no fsync in the timing. What is left is pure
    engine work: random keys split pages and dirty scattered pages that spill out
    of the cache on each commit, while sequential keys keep hitting the same hot
    rightmost page.
    """
    wipe(path)
    conn = sqlite3.connect(path)
    conn.execute(f"PRAGMA page_size = {PAGE_BYTES}")
    conn.execute("PRAGMA journal_mode = DELETE")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute(f"PRAGMA cache_size = {CACHE_PAGES}")
    conn.execute("CREATE TABLE t (k INTEGER PRIMARY KEY, v TEXT)")

    start = time.perf_counter()
    batch = []
    for k in keys:
        batch.append((k, PAYLOAD))
        if len(batch) >= COMMIT_EVERY:
            conn.executemany(insert_sql, batch)
            conn.commit()
            batch.clear()
    if batch:
        conn.executemany(insert_sql, batch)
        conn.commit()
    elapsed_ms = (time.perf_counter() - start) * 1000

    conn.close()
    return elapsed_ms


def lsm_write(keys):
    """A toy LSM writer. Returns (write_path_ms, flush_ms, runs, memtable).

    The write path is: append to the memtable (a list) and append a line to the
    write-ahead log. Neither looks at the key's value, so it is O(1) and order
    blind. When the memtable fills, we flush: sort it and write a run file. That
    sort is background work in a real engine, so we time it separately.
    """
    clean_runs()
    os.makedirs(RUN_DIR, exist_ok=True)
    memtable = []
    runs = []
    flush_ms = 0.0

    wal = open(WAL, "w")
    start = time.perf_counter()
    for k in keys:
        memtable.append((k, PAYLOAD))          # write path: append to memtable
        wal.write(f"{k} {PAYLOAD}\n")           # write path: append to the WAL
        if len(memtable) >= FLUSH_EVERY:
            t0 = time.perf_counter()
            run = sorted(memtable)              # flush: sort the run
            run_path = os.path.join(RUN_DIR, f"run_{len(runs):03d}.txt")
            with open(run_path, "w") as f:
                f.writelines(f"{kk} {vv}\n" for kk, vv in run)
            flush_ms += (time.perf_counter() - t0) * 1000
            runs.append(run_path)
            memtable = []
    wal.flush()
    os.fsync(wal.fileno())
    total_ms = (time.perf_counter() - start) * 1000
    wal.close()

    write_path_ms = total_ms - flush_ms
    return write_path_ms, flush_ms, runs, memtable


def load_runs(runs):
    """Load each run's keys into a sorted list, the way an LSM keeps an index of
    each sorted run in memory so it can binary-search instead of scanning."""
    loaded = []
    for path in runs:
        keys = [int(line.split(" ", 1)[0]) for line in open(path)]
        keys.sort()
        loaded.append(keys)
    return loaded


def point_read(key, memtable_keys, loaded_runs):
    """Read one key the LSM way: newest first. Check the memtable, then each run
    from newest to oldest. Count how many places we touch before we find it (or
    give up). Returns (places_touched, found)."""
    places = 1
    if key in memtable_keys:
        return places, True
    for keys in reversed(loaded_runs):
        places += 1
        i = bisect.bisect_left(keys, key)
        if i < len(keys) and keys[i] == key:
            return places, True
    return places, False


def part1(sequential, random_keys):
    print("=" * 78)
    print("Part 1: the B-tree. Insert 300,000 rows, sequential vs random keys.")
    print("=" * 78)
    insert_sql = "INSERT INTO t (k, v) VALUES (?, ?)"

    seq_ms = btree_insert(ROW_DB, sequential, insert_sql)
    rand_ms = btree_insert(RND_DB, random_keys, insert_sql)
    slowdown = rand_ms / seq_ms

    print(f"  sequential keys (1, 2, 3, ...):  {seq_ms:8.1f} ms")
    print(f"  random keys (shuffled):          {rand_ms:8.1f} ms")
    print(f"  random inserts are {slowdown:.1f}x slower, for the SAME rows")
    print("  Sequential keys keep extending the rightmost leaf of the tree, so")
    print("  the same few pages stay hot. Random keys land all over the tree,")
    print("  splitting pages and dirtying scattered pages that get written out")
    print("  on every commit. This is the B-tree's weakness.")
    return seq_ms, rand_ms, slowdown


def part2(sequential, random_keys):
    print("\n" + "=" * 78)
    print("Part 2: the LSM. The write path is append-only, so order is free.")
    print("=" * 78)
    seq_write, seq_flush, _, _ = lsm_write(sequential)
    rnd_write, rnd_flush, runs, memtable = lsm_write(random_keys)
    write_ratio = rnd_write / seq_write

    print(f"  write path (append to memtable + WAL):")
    print(f"    sequential keys:  {seq_write:8.1f} ms")
    print(f"    random keys:      {rnd_write:8.1f} ms")
    print(f"    ratio random / sequential = {write_ratio:.2f}x  (1.0 = order does not matter)")
    print(f"  background flush (sort each run before writing it):")
    print(f"    sequential keys:  {seq_flush:8.1f} ms")
    print(f"    random keys:      {rnd_flush:8.1f} ms")
    print(f"  sorted runs written to disk: {len(runs)}  ({FLUSH_EVERY:,} rows each)")
    print("  Appending does not look at the key, so the write path is flat. The")
    print("  only order cost is sorting a run at flush time, and even that writes")
    print("  the run out sequentially, never the scattered page writes Part 1 paid.")
    return write_ratio, len(runs), runs, memtable


def part3(runs, memtable):
    print("\n" + "=" * 78)
    print("Part 3: the LSM read tax. One read touches many sorted places.")
    print("=" * 78)
    memtable_keys = set(k for k, _ in memtable)
    loaded = load_runs(runs)
    read_places = len(loaded) + 1   # the memtable, plus every run

    random.seed(SEED + 1)
    all_keys = [int(line.split(" ", 1)[0])
                for r in runs for line in open(r)]
    all_keys.extend(memtable_keys)
    present = random.sample(all_keys, 2000)
    absent = random.sample(range(1, 2 ** 62), 2000)

    present_places = [point_read(k, memtable_keys, loaded)[0] for k in present]
    absent_places = [point_read(k, memtable_keys, loaded)[0] for k in absent]
    avg_present = sum(present_places) / len(present_places)
    avg_absent = sum(absent_places) / len(absent_places)

    print(f"  the store right now: 1 memtable + {len(loaded)} sorted runs")
    print(f"  a present key is found after touching {avg_present:.2f} places on average")
    print(f"  an absent key must touch all {read_places} places before giving up")
    print(f"  a B-tree answers the same read by walking ONE root-to-leaf path")
    print("  That is read amplification. Real LSMs cut it with a bloom filter per")
    print("  run (skip runs that cannot hold the key) and by compacting many runs")
    print("  into fewer. It is the price paid for the cheap, order-free writes.")
    return read_places, avg_present, avg_absent


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<28} actual = {actual:>8,.1f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<28} you = {predicted:>6,.1f}   actual = {actual:>8,.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    try:
        sequential, random_keys = make_keys()
        seq_ms, rand_ms, slowdown = part1(sequential, random_keys)
        write_ratio, run_count, runs, memtable = part2(sequential, random_keys)
        read_places, avg_present, avg_absent = part3(runs, memtable)

        print("\n" + "=" * 78)
        print("Scoreboard")
        print("=" * 78)
        verdict("P1 B-tree random slowdown", PREDICTIONS["btree_random_slowdown_x"], slowdown, "x")
        verdict("P2 LSM write ratio r/s", PREDICTIONS["lsm_write_ratio_x"], write_ratio, "x")
        verdict("P3 LSM sorted runs", PREDICTIONS["lsm_sorted_runs"], run_count, "")
        verdict("P4 LSM read places (miss)", PREDICTIONS["lsm_read_places"], read_places, "")

        print("\n" + "=" * 78)
        print("The number to carry")
        print("=" * 78)
        print(f"  Same 300,000 rows, same keys, only the order changed. The B-tree")
        print(f"  took {slowdown:.1f}x longer on random keys than sequential. The LSM write")
        print(f"  path did not care: random vs sequential came out {write_ratio:.2f}x, basically")
        print(f"  flat. That gap is the whole reason write-heavy systems (logs, events,")
        print(f"  time series, messaging) reach for an LSM engine and not a B-tree.")
        print(f"  The LSM pays it back on reads: {read_places} places to check instead of 1.")
        print("\nNow write labs/day-09-btree-lsm/RESULTS.md.\n")
    finally:
        wipe(ROW_DB, RND_DB)
        clean_runs()


if __name__ == "__main__":
    main()
