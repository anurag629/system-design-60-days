"""
Day 24 lab: Kafka's real design, partitions and consumer groups.

This is the full working solution. The starter file is partitions.py.
Run it:      python3 solution.py

Standard library only (threading, time, zlib, collections). Pure in-memory,
no sockets, no files, nothing to clean up. Runs in well under 40 seconds.

The three things we measure on your own machine:
  - Partitioning. A producer sends each record to one of P partitions by
    hash(key) % P. Every record that shares a key lands in the SAME partition,
    so a key's records keep their order. Different keys spread across all the
    partitions. Part 1 shows both.
  - Consumer groups. A group of C consumers splits the P partitions between
    them, each partition owned by exactly one consumer. Add consumers and
    throughput climbs, but only up to C = P. Past that the extra consumers get
    no partition and sit idle: you cannot have more useful consumers than
    partitions. Part 2 measures the climb and the flat line after it.
  - Ordering. Records are strictly ordered WITHIN a partition, never across
    partitions. Interleave two partitions and global order falls apart. But
    because a key's records all share one partition, per-key order survives.
    That is the exact guarantee Kafka gives, and the one people misremember.
    Part 3 shows all three.
"""

import sys
import threading
import time
import zlib
from collections import defaultdict

PREDICTIONS = {
    # P1: partitioning. You send the SAME key through the producer 50 times.
    #     Records go to partition hash(key) % P. How many different partitions
    #     do those 50 records land in?
    "same_key_partitions": 1,

    # P2: consumer groups. With P = 8 partitions, you grow the group from 1
    #     consumer to 8 (C = P). How many times higher is the throughput at
    #     C = 8 than at C = 1?
    "speedup_at_p_consumers": 8,

    # P3: now push the group to C = 16 (two consumers per partition's worth).
    #     A partition is owned by exactly one consumer. How many of the 16
    #     consumers end up with no partition at all and sit idle?
    "idle_consumers_at_2p": 8,

    # P4: ordering. A key's records all share one partition, and a partition is
    #     read in order. Across the whole stream, how many times does a single
    #     key's records come out in the wrong order?
    "per_key_order_violations": 0,
}

# ---------------------------------------------------------------------------
# Knobs. The defaults keep the numbers clean and the run short.
# ---------------------------------------------------------------------------
NUM_PARTITIONS = 8            # P, the number of partitions in the topic
DISTINCT_KEYS = 240           # how many different keys we spread in part 1
HOT_KEY = "user-42"           # the single key we send over and over in part 1
HOT_KEY_RECORDS = 50          # how many times we send it

RECORDS_PER_PARTITION = 100   # part 2 gives every partition an equal load, so
                              # the only thing that changes is how many consumers
WORK_S = 0.008                # simulated work per record (a DB write, say). It is
                              # a sleep, so consumer threads genuinely overlap.
CONSUMER_COUNTS = [1, 2, 4, 8, 16]   # must include 1, P and 2P

STREAM_LEN = 40               # part 3: length of the ordered stream we produce
ORDER_KEYS = ["alpha", "beta", "gamma", "delta", "epsilon"]

BARRIER_TIMEOUT = 30          # safety: never wait forever at the start line
JOIN_TIMEOUT = 30             # safety: never hang joining the consumers


def hash_key(key):
    """A stable hash of the key, the same in every run and every process.

    Python's built-in hash() is randomised per process for strings, so two runs
    would disagree. crc32 is boring, fast and identical everywhere, which is
    exactly what a partitioner needs."""
    return zlib.crc32(str(key).encode("utf-8"))


# ---------------------------------------------------------------------------
# The four ideas, each one line, each measured below
# ---------------------------------------------------------------------------

def partition_for(key, num_partitions):
    """Which partition does this record go to? The whole partitioning rule.

    Same key in means same partition out, every time, because the hash of the
    key is fixed. That single fact is what makes per-key ordering possible."""
    return hash_key(key) % num_partitions


def assign_partitions(num_partitions, num_consumers):
    """Hand each partition to exactly one consumer in the group.

    Round robin: partition p goes to consumer p % C. A partition is never split
    between two consumers, which is why a consumer past the partition count has
    nothing left to own."""
    return {p: p % num_consumers for p in range(num_partitions)}


def compute_throughput(total_records, wall_seconds):
    """Records per second for the whole group. The group is only as fast as its
    slowest consumer, so wall_seconds is that slowest consumer's time."""
    return total_records / wall_seconds


def count_out_of_order(seqs):
    """Count how many times a value is smaller than the one just before it.

    Feed it a list of production sequence numbers in the order they were
    consumed. A stream that kept its order scores 0. A scrambled one scores
    more. We use it three ways in part 3."""
    return sum(1 for a, b in zip(seqs, seqs[1:]) if b < a)


# ---------------------------------------------------------------------------
# The consumer group: C threads, each owning some partitions, run together
# ---------------------------------------------------------------------------

def run_consumer_group(partitions, num_consumers, work_s):
    """Split the partitions among num_consumers consumers and run them at the
    same time. Returns (group_wall_seconds, idle_consumers).

    Each consumer processes every record in the partitions it owns, one at a
    time, each record costing work_s of simulated work. All consumers start
    together at a barrier, and the group is done when its SLOWEST consumer is
    done, so the group's wall time is the longest consumer's time."""
    num_partitions = len(partitions)
    assignment = assign_partitions(num_partitions, num_consumers)
    if assignment is None:
        return None

    owned = {c: [] for c in range(num_consumers)}
    for p, c in assignment.items():
        owned[c].append(p)

    elapsed = [0.0] * num_consumers
    barrier = threading.Barrier(num_consumers)

    def worker(c):
        try:
            barrier.wait(timeout=BARRIER_TIMEOUT)
        except threading.BrokenBarrierError:
            elapsed[c] = 0.0
            return
        start = time.perf_counter()
        for p in owned[c]:
            for _record in partitions[p]:
                time.sleep(work_s)      # the per-record work a consumer does
        elapsed[c] = time.perf_counter() - start

    threads = [threading.Thread(target=worker, args=(c,))
               for c in range(num_consumers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=JOIN_TIMEOUT)

    group_wall = max(elapsed) if elapsed else 0.0
    idle = sum(1 for c in range(num_consumers) if not owned[c])
    return group_wall, idle


# ---------------------------------------------------------------------------
# Part 1: partitioning
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: partitioning. hash(key) %% P decides where a record goes.".replace("%%", "%"))
    print("=" * 78)

    counts = [0] * NUM_PARTITIONS
    for i in range(DISTINCT_KEYS):
        p = partition_for(f"user-{i}", NUM_PARTITIONS)
        counts[p] += 1
    partitions_used = sum(1 for c in counts if c > 0)

    hot_partitions = set()
    for _ in range(HOT_KEY_RECORDS):
        hot_partitions.add(partition_for(HOT_KEY, NUM_PARTITIONS))
    same_key_partitions = len(hot_partitions)

    print(f"  {DISTINCT_KEYS} different keys spread across the {NUM_PARTITIONS} partitions:")
    print("    partition:  " + "  ".join(f"p{p}" for p in range(NUM_PARTITIONS)))
    print("    records:    " + "  ".join(f"{c:2d}" for c in counts))
    print(f"    partitions that got at least one key: {partitions_used} of {NUM_PARTITIONS}")
    print()
    examples = ["cart-9", "order-7", "user-42", "payment-3"]
    for k in examples:
        print(f"    key {k:<10} -> partition p{partition_for(k, NUM_PARTITIONS)}")
    print()
    print(f"  the one key {HOT_KEY!r}, sent {HOT_KEY_RECORDS} times, landed in"
          f" {same_key_partitions} partition(s)")
    print("  Different keys fan out across every partition, which is the")
    print("  parallelism. But one key is pinned to one partition, which is what")
    print("  lets that key's records stay in order. Both come from the same rule.")
    return same_key_partitions, partitions_used


# ---------------------------------------------------------------------------
# Part 2: consumer groups
# ---------------------------------------------------------------------------

def part2():
    print("\n" + "=" * 78)
    print("Part 2: consumer groups. Add consumers, but only up to the partition count.")
    print("=" * 78)

    partitions = [[(i, "payload") for i in range(RECORDS_PER_PARTITION)]
                  for _ in range(NUM_PARTITIONS)]
    total = NUM_PARTITIONS * RECORDS_PER_PARTITION

    rows = []
    base_tp = None
    for c in CONSUMER_COUNTS:
        group_wall, idle = run_consumer_group(partitions, c, WORK_S)
        tp = compute_throughput(total, group_wall)
        if c == 1:
            base_tp = tp
        speedup = tp / base_tp
        rows.append((c, group_wall, tp, speedup, idle))

    print(f"  {NUM_PARTITIONS} partitions, {RECORDS_PER_PARTITION} records each,"
          f" {total} records total, {WORK_S * 1000:.0f} ms of work per record.")
    print()
    print("    consumers   wall(s)   records/s   speedup   idle")
    for c, wall, tp, speedup, idle in rows:
        marker = "   <- C = P" if c == NUM_PARTITIONS else ""
        print(f"      {c:>3}      {wall:7.2f}   {tp:9.0f}   {speedup:6.2f}x   {idle:>3}{marker}")

    by_c = {c: (wall, tp, speedup, idle) for c, wall, tp, speedup, idle in rows}
    speedup_at_p = by_c[NUM_PARTITIONS][2]
    speedup_at_2p = by_c[2 * NUM_PARTITIONS][2]
    idle_at_2p = by_c[2 * NUM_PARTITIONS][3]

    print()
    print(f"  throughput climbs almost linearly to C = P = {NUM_PARTITIONS}"
          f" ({speedup_at_p:.1f}x), then stops.")
    print(f"  at C = {2 * NUM_PARTITIONS} it is still about {speedup_at_2p:.1f}x,"
          f" no better, and {idle_at_2p} consumers")
    print("  own nothing at all. A partition goes to exactly one consumer, so the")
    print("  partition count is the hard ceiling on useful parallelism. Want more")
    print("  consumers to help? You have to add partitions first.")
    return speedup_at_p, speedup_at_2p, idle_at_2p


# ---------------------------------------------------------------------------
# Part 3: ordering
# ---------------------------------------------------------------------------

def part3():
    print("\n" + "=" * 78)
    print("Part 3: ordering. Inside a partition yes, across partitions no.")
    print("=" * 78)

    # Produce an ordered stream. seq is the production order, 0, 1, 2, ...
    partitions = defaultdict(list)       # partition id -> [(seq, key), ...]
    for seq in range(STREAM_LEN):
        key = ORDER_KEYS[seq % len(ORDER_KEYS)]
        p = partition_for(key, NUM_PARTITIONS)
        partitions[p].append((seq, key))

    # Within a partition: are the production seq numbers still ascending?
    within = sum(count_out_of_order([s for s, _ in recs])
                 for recs in partitions.values())

    # Per key: a key's records all sit in one partition, in production order.
    per_key = 0
    for key in ORDER_KEYS:
        kp = partition_for(key, NUM_PARTITIONS)
        seqs = [s for s, k in partitions[kp] if k == key]
        per_key += count_out_of_order(seqs)

    # Across partitions: two consumers read two partitions at the same time but
    # at different speeds, so records come out interleaved by WHEN each consumer
    # finishes, not by production order. We simulate the finish times.
    busy = sorted(partitions.keys(), key=lambda p: (-len(partitions[p]), p))[:2]
    events = []
    for rank, p in enumerate(busy):
        rate = WORK_S if rank == 0 else WORK_S * 0.55   # second consumer faster
        for j, (seq, _key) in enumerate(partitions[p]):
            events.append(((j + 1) * rate, seq))
    events.sort()
    global_seqs = [seq for _, seq in events]
    global_viol = count_out_of_order(global_seqs)

    p0, p1 = busy
    print(f"  partition p{p0}, production seq order: {[s for s, _ in partitions[p0]]}")
    print(f"  partition p{p1}, production seq order: {[s for s, _ in partitions[p1]]}")
    print(f"    each partition on its own is in order, out-of-order count: {within}")
    print()
    print(f"  now two consumers read p{p0} and p{p1} together at different speeds.")
    print(f"  the order the app actually sees: {global_seqs}")
    print(f"    out-of-order count across the two partitions: {global_viol}  (not 0)")
    print()
    print(f"  per-key check: every key's own records, across the whole stream,")
    print(f"    out-of-order count: {per_key}")
    print("  So global order is gone the moment you use more than one partition.")
    print("  But a key lives in one partition and a partition is read in order,")
    print("  so that key's records are still perfectly ordered. That, and only")
    print("  that, is what Kafka promises you.")
    return within, per_key, global_viol


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>7.1f} {unit}  (no prediction)")
        return
    if abs(actual - predicted) <= 0.6:
        note = "     close enough"
    elif predicted and 0.6 <= actual / predicted <= 1.5:
        note = "     close enough"
    elif actual > predicted:
        note = "     too LOW"
    else:
        note = "     too HIGH"
    print(f"  {name:<34} you = {predicted:>5.1f}   actual = {actual:>7.1f} {unit}  {note}")


def self_test():
    """Run each of the four TODO one-liners once, instantly, before we launch a
    single thread. A blank TODO returns None here, which we turn into a clean
    'fill in TODO N' message instead of a crash or a hung consumer."""
    missing = []
    if partition_for("probe", NUM_PARTITIONS) is None:
        missing.append(1)
    if assign_partitions(NUM_PARTITIONS, 2) is None:
        missing.append(2)
    if compute_throughput(10, 1.0) is None:
        missing.append(3)
    if count_out_of_order([1, 2, 3]) is None:
        missing.append(4)
    return missing


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    gaps = self_test()
    if gaps:
        print("\n  !! Some TODOs are not filled in yet:")
        for n in gaps:
            print(f"       - fill in TODO {n}")
        print("     Fill them in and run again. See solution.py if you get stuck.\n")
        sys.exit(1)

    same_key_partitions, _ = part1()
    speedup_at_p, speedup_at_2p, idle_at_2p = part2()
    within, per_key, global_viol = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 same key -> partitions", PREDICTIONS["same_key_partitions"], same_key_partitions)
    verdict("P2 speedup at C = P", PREDICTIONS["speedup_at_p_consumers"], speedup_at_p, "x")
    verdict("P3 idle consumers at C = 2P", PREDICTIONS["idle_consumers_at_2p"], idle_at_2p)
    verdict("P4 per-key order violations", PREDICTIONS["per_key_order_violations"], per_key)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Partitions are the unit of parallelism: {NUM_PARTITIONS} of them, and throughput")
    print(f"  rose about {speedup_at_p:.1f}x going from 1 consumer to {NUM_PARTITIONS}, then went flat")
    print(f"  ({speedup_at_2p:.1f}x at {2 * NUM_PARTITIONS} consumers, with {idle_at_2p} sitting idle). You cannot")
    print(f"  have more useful consumers than partitions. And ordering is the")
    print(f"  guarantee people get wrong: within a partition it held (0 out of")
    print(f"  order), across partitions it broke ({global_viol} out of order), but every")
    print(f"  key's own records stayed in order ({per_key}), because a key maps to one")
    print(f"  partition. Parallelism and per-key order from the one hashing rule.")
    print("\nNow write labs/day-24-partitions/RESULTS.md.\n")


if __name__ == "__main__":
    main()
