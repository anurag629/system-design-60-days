"""
Day 18 lab: hot keys and the celebrity problem in a sharded cache.

Run it:      python3 hot_keys.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only. No files, no sockets, no threads. It samples a celebrity
(Zipf) read workload and routes every read to a cache node by hash(key) % N, the
exact rule a real sharded Redis/Memcached client uses. Then it measures how much
traffic each node actually gets. Runs in a few seconds.

The big ideas, all measured on your own machine:
  - Hash routing spreads the DISTINCT keys evenly across nodes, but a single
    viral key still dumps its whole share of reads on ONE node. That node melts
    while the others sit idle. This is the hot-key / celebrity problem, and it is
    different from Day 13: there we moved DATA between shards; here it is READ
    traffic piling onto one cache node because of one key.
  - Adding more nodes does NOT fix it. One key cannot be split across nodes, so
    the hottest node can never drop below the celebrity's own share.
  - The fix is not more sharding. You detect the hot keys and either REPLICATE
    them to every node (any node can then serve the read, so it spreads), or you
    ABSORB them in a tiny in-process local cache in front of the shared tier.

If you get stuck, the full working version is solution.py in this folder.
"""

import hashlib
import random
import sys
from collections import Counter

PREDICTIONS = {
    # P1: the single hottest "celebrity" key's share of ALL reads, as a percent.
    #     One key out of 100,000. How big a slice of the whole workload?
    "celebrity_share_pct": None,

    # P2: BEFORE any fix. Route the celebrity workload across 8 cache nodes with
    #     hash(key) % 8 and measure load. The hottest node's share of all reads,
    #     as a percent. (A perfectly even tier would give each node 12.5%.)
    "baseline_hottest_pct": None,

    # P3: AFTER the fix. Detect the top hot keys and replicate them to ALL 8
    #     nodes, so a read for a hot key can be served by any node. The hottest
    #     node's share now, as a percent. (How close to the even 12.5%?)
    "replicated_hottest_pct": None,

    # P4: the local-cache fix. A tiny in-process cache holds the top hot keys, so
    #     reads for them are absorbed on the app server and never reach the shared
    #     tier. What percent of ALL reads get absorbed this way?
    "local_absorbed_pct": None,
}

K = 100_000          # distinct keys (think post ids, user ids, hashtags)
ZIPF_S = 1.2         # skew of the read workload: higher means a hotter head
N = 8                # number of cache nodes in the sharded tier
REQUESTS = 1_000_000  # reads we send through the tier and count per node
TOP_K = 10           # how many hot keys we detect and treat specially
SEED = 42


def h64(key):
    """A stable 64-bit hash of a string, the same on every machine.

    Python's built-in hash() is randomised per process, so we use md5 (fine as a
    plain spreading hash here, nothing security-sensitive) and take 8 bytes. This
    stands in for the hash a real sharded cache client uses to pick a node.
    """
    return int.from_bytes(hashlib.md5(key.encode()).digest()[:8], "big")


def route(h, n):
    """Which cache node a key lands on: hash(key) modulo the node count. This is
    the whole routing rule of a sharded cache, and it is why one key is pinned to
    exactly one node no matter how much traffic that key gets."""
    # TODO 1 ------------------------------------------------------------------
    # Which cache node does a key land on? A sharded cache picks the node by
    # hashing the key and taking it modulo the number of nodes:
    #     return h % n
    # This one line is why a single key is pinned to exactly one node, however
    # much traffic that key gets. That is the whole hot-key problem.
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def hottest_share(loads):
    """The hottest node's share of all reads, as a percent. This is the headline
    number: a perfectly even tier would put sum/len on every node, so the gap
    between this and the even share is the skew."""
    # TODO 2 ------------------------------------------------------------------
    # The headline metric: the hottest node's share of all reads, as a percent.
    # loads is a list of per-node request counts.
    #     return max(loads) / sum(loads) * 100
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def spread_node(n, rng):
    """For a REPLICATED hot key: the key now lives on every node, so any node can
    serve the read. Pick one. Spreading these reads across all nodes is exactly
    what replication buys you."""
    # TODO 3 ------------------------------------------------------------------
    # The replication fix. A replicated hot key lives on EVERY node, so any node
    # can serve the read. Spread these reads by picking a node at random:
    #     return rng.randrange(n)
    # (Round-robin would work too. The point is the hot key's reads no longer
    # all land on one node.)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def is_absorbed(key, hot_keys):
    """The local-cache test: is this key one of the hot keys the app server keeps
    in its own tiny in-process cache? If so, the read is served locally and never
    reaches the shared tier."""
    # TODO 4 ------------------------------------------------------------------
    # The local-cache fix. Each app server keeps a tiny in-process cache of the
    # hottest keys. If this key is one of them, the read is served locally and
    # never reaches the shared tier. hot_keys is a set.
    #     return key in hot_keys
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def zipf_cumulative(k, s):
    """Cumulative weights for a Zipf workload over k keys. Key 0 is the most
    popular (the celebrity), key i has weight 1/(i+1)**s. Returns (cum, total)
    where cum is the running sum, used for sampling by bisect."""
    cum = []
    total = 0.0
    for i in range(k):
        total += 1.0 / (i + 1) ** s
        cum.append(total)
    return cum, total


def sample_requests(cum, total, r, seed):
    """Draw r reads from the Zipf workload. Each read is a key id in 0..K-1, the
    celebrity (key 0) showing up far more than any other."""
    import bisect
    rng = random.Random(seed)
    rand = rng.random
    bl = bisect.bisect_left
    return [bl(cum, rand() * total) for _ in range(r)]


def bar(count, maxcount, width=44):
    return "#" * max(1, int(round(width * count / maxcount)))


def part1(requests, H, key_counts):
    print("=" * 78)
    print("Part 1: the hot key melts one node. Route reads by hash(key) % N.")
    print("=" * 78)

    celeb_share = key_counts[0] / REQUESTS * 100
    print(f"  {K:,} keys, {REQUESTS:,} reads, Zipf workload (exponent {ZIPF_S}).")
    print(f"  the single hottest key (the celebrity) alone is {celeb_share:.1f}% "
          f"of all reads.")
    print()

    if route(H[0], N) is None:
        print("  (fill in TODO 1)")
        return None

    loads = [0] * N
    for key in requests:
        loads[route(H[key], N)] += 1

    celeb_node = route(H[0], N)
    even = 100.0 / N
    mx = max(loads)
    print(f"  Sharded cache, {N} nodes. An even tier would give each node {even:.1f}%.")
    for node in range(N):
        share = loads[node] / REQUESTS * 100
        tag = "  <-- celebrity lives here" if node == celeb_node else ""
        print(f"    node {node}: {loads[node]:>8,}  {share:5.1f}%  "
              f"{bar(loads[node], mx)}{tag}")

    hottest = hottest_share(loads)
    if hottest is None:
        print("  (fill in TODO 2)")
        return None
    print()
    print(f"  hottest node = {hottest:.1f}% of all reads, vs {even:.1f}% if even.")
    print(f"  the distinct keys are spread evenly, but one key cannot be, so the")
    print(f"  celebrity's node carries its {celeb_share:.1f}% on top of its fair share.")
    return celeb_share, hottest


def adding_nodes(requests, H):
    print("\n" + "=" * 78)
    print("Does adding nodes fix it? Grow the tier and re-measure the hottest node")
    print("=" * 78)
    for n in (8, 64, 256):
        loads = [0] * n
        for key in requests:
            loads[route(H[key], n)] += 1
        hottest = max(loads) / REQUESTS * 100
        even = 100.0 / n
        print(f"    {n:>4} nodes: hottest = {hottest:5.1f}%   even share = "
              f"{even:5.2f}%   hottest is {hottest / even:4.1f}x the even share")
    print("  More nodes slice the OTHER keys thinner, so the even share keeps")
    print("  shrinking, but the celebrity's node cannot drop below that one key's")
    print("  share. The gap between hottest and even gets RELATIVELY worse, not")
    print("  better. You cannot shard your way out of a single hot key.")


def part2(requests, H, hot_keys):
    print("\n" + "=" * 78)
    print("Part 2: the fix. Replicate the hot keys, and absorb them locally.")
    print("=" * 78)
    even = 100.0 / N

    # Fix A: replicate the top hot keys to every node. A read for a hot key can
    # now be served by ANY node, so those reads spread instead of piling up.
    probe_rng = random.Random(0)
    if spread_node(N, probe_rng) is None:
        print("  (fill in TODO 3)")
        return None
    rng = random.Random(SEED + 2)
    loads = [0] * N
    for key in requests:
        if key in hot_keys:
            node = spread_node(N, rng)
        else:
            node = route(H[key], N)
        loads[node] += 1
    repl_hottest = hottest_share(loads)
    print(f"  Fix A: replicate the top {TOP_K} hot keys to all {N} nodes.")
    for node in range(N):
        share = loads[node] / REQUESTS * 100
        print(f"    node {node}: {loads[node]:>8,}  {share:5.1f}%  "
              f"{bar(loads[node], max(loads))}")
    print(f"  hottest node = {repl_hottest:.1f}%  (was far higher; even is {even:.1f}%)")
    print("  The hot keys' reads now land on every node, so the tier evens out.")
    print()

    # Fix B: a tiny in-process local cache holds the top hot keys. Those reads
    # are served on the app server and never reach the shared tier at all.
    if is_absorbed(0, hot_keys) is None:
        print("  (fill in TODO 4)")
        return None
    loads = [0] * N
    absorbed = 0
    for key in requests:
        if is_absorbed(key, hot_keys):
            absorbed += 1
            continue
        loads[route(H[key], N)] += 1
    absorbed_pct = absorbed / REQUESTS * 100
    shared_hottest_pct = max(loads) / REQUESTS * 100
    print(f"  Fix B: a local cache on each app server holds the top {TOP_K} hot keys.")
    print(f"    reads absorbed locally (never hit the shared tier): {absorbed_pct:.1f}%")
    print(f"    hottest shared node now carries {shared_hottest_pct:.1f}% of all reads")
    print("  The celebrity's reads are soaked up in front of the tier, so the")
    print("  shared nodes see a lighter, even load. One cheap dict per server.")
    return repl_hottest, absorbed_pct


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>7,.1f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<34} you = {predicted:>6,.1f}   actual = {actual:>7,.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    H = [h64(str(i)) for i in range(K)]
    cum, total = zipf_cumulative(K, ZIPF_S)
    requests = sample_requests(cum, total, REQUESTS, SEED)
    key_counts = Counter(requests)
    hot_keys = set(k for k, _ in key_counts.most_common(TOP_K))

    p1 = part1(requests, H, key_counts)
    if p1 is None:
        sys.exit(1)
    celeb_share, baseline_hottest = p1

    adding_nodes(requests, H)

    p2 = part2(requests, H, hot_keys)
    if p2 is None:
        sys.exit(1)
    repl_hottest, absorbed_pct = p2

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 celebrity key share", PREDICTIONS["celebrity_share_pct"], celeb_share, "%")
    verdict("P2 baseline hottest node", PREDICTIONS["baseline_hottest_pct"], baseline_hottest, "%")
    verdict("P3 hottest after replicating", PREDICTIONS["replicated_hottest_pct"], repl_hottest, "%")
    verdict("P4 reads absorbed locally", PREDICTIONS["local_absorbed_pct"], absorbed_pct, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  One viral key was {celeb_share:.1f}% of all reads, and with plain")
    print(f"  hash(key) % N routing it pushed its node to {baseline_hottest:.1f}% while the")
    print(f"  rest sat near the even {100.0 / N:.1f}%. Adding nodes never helped: one key")
    print(f"  cannot be split. Replicating the hot keys to every node brought the")
    print(f"  hottest node down to {repl_hottest:.1f}%, and a tiny local cache absorbed")
    print(f"  {absorbed_pct:.1f}% of all reads before they ever reached the shared tier.")
    print("  You do not shard a hot key. You replicate it or you absorb it.")
    print()


if __name__ == "__main__":
    main()
