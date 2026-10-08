"""
Day 30 lab: CAP for real, and PACELC. The choice is per-operation, during a
partition, not a label you stick on a database.

Run it:      python3 cap.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only, no sockets, no threads, no files. It is a DETERMINISTIC
simulation: a small replicated key-value store with a network partition we can
switch on and off, driven by a seeded workload so every run gives the same
numbers. Runs in well under a second.

The setup. Five nodes, 0 1 2 3 4. A partition cuts the cluster into a majority
side (nodes 0 1 2) and a minority side (nodes 3 4). A client op lands on some
node; which side that node is on decides what happens to the op during the
partition. Majority = 3 of 5, which is a quorum. Minority = 2 of 5, which is not.

The three parts:

  Part 1: no partition. Every write replicates to all nodes, so all five agree
          and every read is consistent. Divergent keys: zero. This is the happy
          path, and it is the baseline the next part breaks.

  Part 2: switch the partition on and replay ONE workload under TWO policies.
            CP (consistency): an op succeeds only if its side has a quorum. The
            minority side has no quorum, so it REFUSES every op landing there. It
            is UNAVAILABLE for the whole partition. Nobody ever writes two
            different values for a key, so after healing there are ZERO conflicts.
            AP (availability): every node accepts every op locally. Nothing is
            refused, the store stays fully AVAILABLE. But the two sides write the
            same keys to different values and DIVERGE, so when the partition heals
            you are left with CONFLICTS that something has to reconcile.
          Same partition, same workload. CP loses availability. AP loses
          consistency. The database did not choose. The operation's policy did.

  Part 3: PACELC. Even with NO partition there is still a trade. Synchronous
          replication (the write waits for the replica to ack) is consistent but
          pays a network round trip on every write. Asynchronous replication
          returns after the local write and ships the change in the background,
          so it is fast but there is a window where a replica serves a STALE read.
          We measure both: the latency gap, and the stale-read rate. CAP is only
          about the partition. PACELC says you are trading consistency against
          latency all the time, even on a good day.

If you get stuck, the full working version is solution.py in this folder.
"""

import random
import sys

PREDICTIONS = {
    # P1: during the partition, under the CP policy, what PERCENT of operations
    #     get rejected (because they land on the minority side, which has no
    #     quorum)? Hint: the minority is 2 of the 5 nodes.
    "cp_reject_pct": None,

    # P2: during the partition, under the AP policy, how many keys end up in
    #     CONFLICT (written to different values on the two sides) and have to be
    #     reconciled after the heal? There are 16 keys in play.
    "ap_conflicts": None,

    # P3: PACELC, no partition. Synchronous write latency divided by asynchronous
    #     write latency. How many times slower is the write that waits for the
    #     replica? (local apply is ~1 ms, a replica round trip is ~10 ms.)
    "sync_over_async_latency": None,

    # P4: PACELC, no partition, asynchronous replication. What PERCENT of reads
    #     land inside the replication window and come back STALE?
    "async_stale_pct": None,
}

# ---- the cluster ----------------------------------------------------------
CLUSTER = 5                       # five nodes: 0 1 2 3 4
QUORUM = CLUSTER // 2 + 1         # 3 nodes is a majority
MAJORITY_NODES = {0, 1, 2}       # the side that keeps a quorum during a partition
MINORITY_NODES = {3, 4}          # the side that does not

# ---- the workload ---------------------------------------------------------
KEYS = [f"key{i:02d}" for i in range(16)]   # 16 keys the clients fight over
N_OPS = 1000                                 # ops driven during the partition
WRITE_FRACTION = 0.6                         # 60% writes, 40% reads
SEED = 30                                    # seed everything, so runs repeat

# ---- PACELC latency model (milliseconds) ----------------------------------
LOCAL_MS = 1.0            # cost to apply a write to the local node
RTT_MS = 10.0            # round trip to a replica and back
REPL_DELAY_MS = 5.0      # one-way time for an async change to reach a replica
N_LAT = 5000             # writes timed for the latency average
N_TIMELINE = 4000        # ops on the staleness timeline
STEP_MS = 1.0            # simulated clock tick between timeline ops


def side_of(node):
    """Which side of the partition a node sits on: 'maj' or 'min'."""
    return "maj" if node in MAJORITY_NODES else "min"


def cp_allows(side_live_count):
    """CP policy: an op is allowed only if its side can reach a quorum.

    `side_live_count` is how many nodes are reachable on the op's side during
    the partition (3 on the majority side, 2 on the minority side).
    """
    # TODO 1 ------------------------------------------------------------------
    # This one line IS the CP choice. An op may proceed only when its side can
    # still reach a quorum of the cluster. The majority side can (3 >= 3), the
    # minority side cannot (2 >= 3 is false), so the minority refuses and goes
    # unavailable. Return the comparison:
    #     return side_live_count >= QUORUM
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def in_conflict(val_a, val_b):
    """After the heal, is this key a conflict that needs reconciling?

    A conflict is when BOTH sides wrote the key during the partition and the two
    values disagree. If only one side wrote it, the heal just takes that value;
    there is nothing to reconcile.
    """
    # TODO 2 ------------------------------------------------------------------
    # A key is a conflict only if each side holds a value (neither is None) AND
    # the two values differ. That is the whole cost of the AP choice, measured:
    #     return val_a is not None and val_b is not None and val_a != val_b
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def sync_write_latency(net_jitter):
    """PACELC, synchronous replication: the write applies locally AND waits for
    the replica to acknowledge before returning. So it pays a network round trip
    (plus that round trip's jitter) on top of the local apply.
    """
    # TODO 3 ------------------------------------------------------------------
    # A sync write cannot return until the replica has acked, so its latency is
    # the local apply PLUS a full network round trip (with its jitter). This is
    # the "consistency costs latency" half of PACELC, in one line:
    #     return LOCAL_MS + RTT_MS + net_jitter
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def async_write_latency():
    """PACELC, asynchronous replication: the write applies locally and returns.
    The replica is updated in the background, off the write's critical path, so
    the write never waits on the network at all.
    """
    return LOCAL_MS


def read_is_stale(now, last_write_time):
    """Async read staleness: a read is stale if it reaches a replica inside the
    replication window, i.e. a write happened to this key but has not propagated
    yet. No write seen for the key means nothing to be stale about.
    """
    if last_write_time is None:
        return False
    # TODO 4 ------------------------------------------------------------------
    # Under async replication the replica only has the new value REPL_DELAY_MS
    # after the write committed locally. A read is stale when it lands before
    # that: the current time is still inside the replication window. This is the
    # "latency win costs consistency" half of PACELC:
    #     return now < last_write_time + REPL_DELAY_MS
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def make_workload():
    """A deterministic stream of client ops. Each op is a dict with the node it
    lands on, whether it is a read or a write, the key, and (for writes) a value
    that is unique to the op so divergence is always detectable.
    """
    rng = random.Random(SEED)
    ops = []
    for t in range(N_OPS):
        node = rng.randrange(CLUSTER)
        is_write = rng.random() < WRITE_FRACTION
        key = rng.choice(KEYS)
        ops.append({
            "node": node,
            "write": is_write,
            "key": key,
            "val": f"w{t}",   # unique per op
        })
    return ops


def part1_no_partition(ops):
    print("=" * 78)
    print("Part 1: no partition. Replication keeps all five nodes agreeing.")
    print("=" * 78)

    # With the network whole, a write goes to every node, so the nodes are
    # really one logical store. We model that as a single dict, then confirm
    # every node holds exactly the same thing.
    nodes = [dict() for _ in range(CLUSTER)]
    reads = 0
    stale_reads = 0
    for op in ops:
        if op["write"]:
            for store in nodes:            # synchronous replication to all
                store[op["key"]] = op["val"]
        else:
            reads += 1
            seen = nodes[op["node"]].get(op["key"])
            truth = nodes[0].get(op["key"])
            if seen != truth:
                stale_reads += 1

    divergent = 0
    for key in KEYS:
        values = {store.get(key) for store in nodes}
        if len(values) > 1:
            divergent += 1

    print(f"  {N_OPS:,} ops over {len(KEYS)} keys, all five nodes connected.")
    print(f"    writes replicate to all {CLUSTER} nodes synchronously.")
    print(f"    reads served: {reads:,}, of which stale: {stale_reads}")
    print(f"    keys where the nodes disagree: {divergent}")
    print("  Everyone agrees, every read is fresh. This is the baseline that the")
    print("  partition is about to break. Nothing here forced a hard choice yet.")
    return divergent


def part2_partition(ops):
    print("\n" + "=" * 78)
    print("Part 2: partition ON. One workload, two policies, opposite failures.")
    print("=" * 78)

    if cp_allows(QUORUM) is None:
        print("  (fill in TODO 1)")
        return None
    if in_conflict("a", "b") is None:
        print("  (fill in TODO 2)")
        return None

    maj_live = len(MAJORITY_NODES)   # 3 reachable on the majority side
    min_live = len(MINORITY_NODES)   # 2 reachable on the minority side

    # ---- CP policy: refuse any op that cannot reach a quorum ---------------
    cp_store = dict()
    cp_rejected = 0
    cp_served = 0
    for op in ops:
        live = maj_live if side_of(op["node"]) == "maj" else min_live
        if not cp_allows(live):
            cp_rejected += 1         # minority side: unavailable
            continue
        cp_served += 1
        if op["write"]:
            cp_store[op["key"]] = op["val"]
    cp_conflicts = 0
    cp_reject_pct = cp_rejected / N_OPS * 100

    # ---- AP policy: every node accepts every op, sides diverge -------------
    maj_store = dict()
    min_store = dict()
    ap_rejected = 0
    ap_served = 0
    for op in ops:
        ap_served += 1               # AP never refuses
        if op["write"]:
            if side_of(op["node"]) == "maj":
                maj_store[op["key"]] = op["val"]
            else:
                min_store[op["key"]] = op["val"]
    ap_conflicts = sum(
        1 for key in KEYS if in_conflict(maj_store.get(key), min_store.get(key))
    )
    ap_reject_pct = ap_rejected / N_OPS * 100

    print("  CP policy (consistency first): refuse any op without a quorum.")
    print(f"    majority side ({sorted(MAJORITY_NODES)}) has {maj_live} nodes, a quorum, serves.")
    print(f"    minority side ({sorted(MINORITY_NODES)}) has {min_live} nodes, no quorum, refuses.")
    print(f"    operations served:   {cp_served:,}")
    print(f"    operations REJECTED: {cp_rejected:,}  ({cp_reject_pct:.1f}% unavailable)")
    print(f"    conflicts to reconcile after heal: {cp_conflicts}")
    print("    the minority is DOWN for the whole partition, but no key ever got")
    print("    two values, so the data comes out clean. CP traded availability.")
    print()
    print("  AP policy (availability first): every node accepts every op.")
    print(f"    operations served:   {ap_served:,}")
    print(f"    operations REJECTED: {ap_rejected:,}  ({ap_reject_pct:.1f}% unavailable)")
    print(f"    conflicts to reconcile after heal: {ap_conflicts}")
    print("    nobody was ever turned away, but the two sides wrote the same keys")
    print("    to different values, so the heal finds a pile of conflicts. AP")
    print("    stayed up and traded consistency.")
    print()
    print("  Same partition. Same workload. CP went unavailable to stay")
    print("  consistent; AP stayed available and went inconsistent. The database")
    print("  did not pick a letter. The OPERATION'S policy did.")
    return cp_reject_pct, cp_conflicts, ap_reject_pct, ap_conflicts


def part3_pacelc():
    print("\n" + "=" * 78)
    print("Part 3: PACELC. No partition, and STILL a trade: latency vs consistency.")
    print("=" * 78)

    if sync_write_latency(0.0) is None:
        print("  (fill in TODO 3)")
        return None
    if read_is_stale(10.0, 1.0) is None:
        print("  (fill in TODO 4)")
        return None

    # ---- the latency gap ---------------------------------------------------
    rng = random.Random(SEED)
    sync_total = 0.0
    async_total = 0.0
    for _ in range(N_LAT):
        net_jitter = rng.uniform(0.0, 1.0)   # network round-trip variance, seeded
        sync_total += sync_write_latency(net_jitter)
        async_total += async_write_latency()
    sync_avg = sync_total / N_LAT
    async_avg = async_total / N_LAT
    ratio = sync_avg / async_avg

    # ---- the staleness window ----------------------------------------------
    rng2 = random.Random(SEED + 1)
    last_write = {}            # key -> time of its most recent local write
    clock = 0.0
    reads = 0
    async_stale = 0
    sync_stale = 0
    for _ in range(N_TIMELINE):
        clock += STEP_MS
        key = rng2.choice(KEYS)
        if rng2.random() < 0.5:
            last_write[key] = clock          # a write commits locally now
        else:
            reads += 1
            if read_is_stale(clock, last_write.get(key)):
                async_stale += 1             # async: replica not caught up yet
    async_stale_pct = async_stale / reads * 100
    sync_stale_pct = sync_stale / reads * 100

    print("  Synchronous replication: the write waits for the replica to ack.")
    print(f"    average write latency: {sync_avg:.2f} ms")
    print("  Asynchronous replication: the write returns after the local apply.")
    print(f"    average write latency: {async_avg:.2f} ms")
    print(f"    sync is {ratio:.1f}x slower per write, for the SAME write.")
    print()
    print(f"  Staleness over {reads:,} reads (simulated clock, {STEP_MS:.0f} ms per step):")
    print(f"    async stale reads: {async_stale:,}  ({async_stale_pct:.1f}% of reads)")
    print(f"    sync  stale reads: {sync_stale:,}  ({sync_stale_pct:.1f}% of reads)")
    print("  Async bought the low latency with a window where a replica serves")
    print("  an old value. Sync bought the fresh read with a round trip on every")
    print("  write. No partition anywhere. The trade is there on a good day too.")
    return ratio, async_stale_pct


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>7,.1f} {unit}  (no prediction)")
        return
    if predicted == 0:
        note = "     close enough" if abs(actual) < 0.5 else "   you said 0, it is not"
        print(f"  {name:<30} you = {predicted:>5,.1f}   actual = {actual:>7,.1f} {unit}  {note}")
        return
    ratio = actual / predicted
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>5.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>5.1f}x  too HIGH"
    print(f"  {name:<30} you = {predicted:>5,.1f}   actual = {actual:>7,.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    ops = make_workload()

    part1_no_partition(ops)

    res2 = part2_partition(ops)
    if res2 is None:
        sys.exit(1)
    cp_reject_pct, cp_conflicts, ap_reject_pct, ap_conflicts = res2

    res3 = part3_pacelc()
    if res3 is None:
        sys.exit(1)
    ratio, async_stale_pct = res3

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 CP rejected", PREDICTIONS["cp_reject_pct"], cp_reject_pct, "%")
    verdict("P2 AP conflicts", PREDICTIONS["ap_conflicts"], ap_conflicts, "keys")
    verdict("P3 sync / async latency", PREDICTIONS["sync_over_async_latency"], ratio, "x")
    verdict("P4 async stale reads", PREDICTIONS["async_stale_pct"], async_stale_pct, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  During the SAME partition, under the SAME workload:")
    print(f"    CP rejected {cp_reject_pct:.0f}% of ops to stay consistent, and healed with")
    print(f"       {cp_conflicts} conflicts. It chose consistency and gave up availability.")
    print(f"    AP rejected {ap_reject_pct:.0f}% of ops and stayed fully available, but healed")
    print(f"       with {ap_conflicts} conflicts to reconcile. It chose availability and")
    print(f"       gave up consistency.")
    print("  The database did not choose a letter. Each operation's policy did.")
    print(f"  And PACELC: even with no partition, sync writes were {ratio:.0f}x slower while")
    print(f"  async served {async_stale_pct:.0f}% stale reads. You trade C against L all the time.")
    print()


if __name__ == "__main__":
    main()
