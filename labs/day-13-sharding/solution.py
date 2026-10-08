"""
Day 13 lab: partitioning and sharding, the hot shard, and why adding a server
should not force you to move all your data.

This is the full working solution. The starter file is sharding.py.
Run it:      python3 solution.py

Standard library only, no database files, runs in a few seconds. We take a
realistic skewed (Zipf-like) traffic distribution over 100,000 keys and split
those keys across shards three ways, measuring what actually happens.

The big ideas:
  - Hash sharding spreads the DISTINCT keys evenly, but a single celebrity key
    still dumps its whole share of traffic on one shard. Adding more shards does
    not help: one key cannot be split, so the hottest shard can never drop below
    the celebrity's share. That is the hot-shard problem.
  - Range partitioning puts neighbouring keys together, so if popularity happens
    to cluster by range (recent data, early-adopter celebrities), one shard gets
    almost everything.
  - Plain modulo sharding is a trap at resharding time. Going from N to N+1
    shards remaps almost every key, which in real life means copying your whole
    dataset to add one server.
  - Consistent hashing puts shards on a ring. Adding one shard moves only about
    1/(N+1) of the keys. It fixes the resharding churn. It does NOT fix the hot
    key: the celebrity still lands on one shard.
"""

import bisect
import hashlib
import sys

PREDICTIONS = {
    # P1: the single hottest "celebrity" key's share of ALL traffic, as a
    #     percent. One key, how big a slice?
    "celebrity_share_pct": 15,

    # P2: range partitioning across 8 shards, where popularity correlates with
    #     the key range. The hottest shard's share of all traffic, as a percent.
    "range_hottest_pct": 80,

    # P3: resharding with plain modulo, going from 8 shards to 9. What percent of
    #     the keys now map to a DIFFERENT shard?
    "modulo_remap_pct": 85,

    # P4: resharding with consistent hashing, 8 shards to 9. What percent of the
    #     keys move this time?
    "consistent_remap_pct": 12,
}

K = 100_000          # distinct keys (think user ids or hashtags)
ZIPF_S = 1.2         # skew: higher means a more dominant head
N = 8                # base shard count
VNODES = 200         # virtual nodes per shard on the consistent-hash ring


def h64(key):
    """A stable 64-bit hash of a string, same on every machine.

    Python's built-in hash() is randomised per process, so we use md5 (fine as a
    plain spreading hash here, nothing security-sensitive) and take 8 bytes.
    """
    return int.from_bytes(hashlib.md5(key.encode()).digest()[:8], "big")


def hash_shard(h, n):
    """Which shard a key lands on under hash sharding: hash modulo shard count."""
    return h % n


def range_shard(i, k, n):
    """Which shard key index i lands on under range partitioning.

    Contiguous ranges: keys 0..(k/n - 1) go to shard 0, the next block to shard
    1, and so on. The last shard mops up any remainder.
    """
    per = k // n
    return min(i // per, n - 1)


def moved_under_modulo(h, n):
    """True if this key changes shard when we grow from n shards to n+1."""
    return (h % n) != (h % (n + 1))


def build_ring(n, vnodes):
    """Place n shards on a hash ring, each as `vnodes` points, and return the
    sorted list of positions plus a parallel list of which shard owns each.
    """
    pairs = []
    for shard in range(n):
        for v in range(vnodes):
            pos = h64(f"shard-{shard}#vnode-{v}")
            pairs.append((pos, shard))
    pairs.sort()
    positions = [p for p, _ in pairs]
    owners = [s for _, s in pairs]
    return positions, owners


def ring_owner(positions, owners, h):
    """The shard that owns key-hash h: the first ring point at or after h,
    wrapping past the end back to the start.
    """
    idx = bisect.bisect_left(positions, h) % len(positions)
    return owners[idx]


def zipf_shares(k, s):
    """Traffic share per key. Key i has weight 1/(i+1)**s, so key 0 is the most
    popular (the celebrity). Returns a list that sums to 1.0.
    """
    weights = [1.0 / (i + 1) ** s for i in range(k)]
    total = sum(weights)
    return [w / total for w in weights]


def part1(shares, H):
    print("=" * 78)
    print("Part 1: the hot shard. Spread the keys, and watch one key melt a shard")
    print("=" * 78)

    celeb_share = shares[0]
    print(f"  {K:,} keys, Zipf-like traffic (exponent {ZIPF_S}).")
    print(f"  the single hottest key alone is {celeb_share * 100:.1f}% of all traffic.")

    # Hash sharding across N shards: assign each key, add up its traffic share.
    loads = [0.0] * N
    counts = [0] * N
    for i in range(K):
        s = hash_shard(H[i], N)
        loads[s] += shares[i]
        counts[s] += 1
    ideal = 100.0 / N
    hot = max(loads) * 100
    celeb_shard = hash_shard(H[0], N)
    print()
    print(f"  Hash sharding, {N} shards. Ideal per shard would be {ideal:.1f}%.")
    print(f"    distinct keys per shard: {min(counts):,} to {max(counts):,}  (even)")
    print(f"    traffic per shard, hottest = {hot:.1f}%  (shard {loads.index(max(loads))})")
    print(f"    the celebrity key sits on shard {celeb_shard}, and it alone is "
          f"{celeb_share * 100:.1f}%.")

    # Adding shards does not save you from a celebrity.
    print()
    print("  Does adding shards fix the hot shard? Hottest shard's traffic share:")
    for n in (N, 64, 256):
        ld = [0.0] * n
        for i in range(K):
            ld[hash_shard(H[i], n)] += shares[i]
        print(f"    {n:>4} shards -> hottest = {max(ld) * 100:5.1f}%  "
              f"(floor is the celebrity, {celeb_share * 100:.1f}%)")
    print("  More shards spread the OTHER keys thinner, but one key cannot split,")
    print("  so the hottest shard can never drop below the celebrity's own share.")

    # Range partitioning: neighbours together, popularity clustered in one range.
    rloads = [0.0] * N
    for i in range(K):
        rloads[range_shard(i, K, N)] += shares[i]
    rhot = max(rloads) * 100
    print()
    print(f"  Range partitioning, {N} shards (popularity correlates with range).")
    print(f"    traffic per shard, hottest = {rhot:.1f}%  (shard {rloads.index(max(rloads))})")
    print("  One range holds the whole popular head, so that shard gets almost")
    print("  everything while the rest sit idle. This is the range hot shard.")
    return celeb_share * 100, rhot


def part2(H):
    print("\n" + "=" * 78)
    print("Part 2: resharding pain. Grow from N shards to N+1 with plain modulo")
    print("=" * 78)
    moved = sum(1 for i in range(K) if moved_under_modulo(H[i], N))
    frac = moved / K * 100
    print(f"  Going {N} shards -> {N + 1} shards, hash % count.")
    print(f"    {moved:,} of {K:,} keys change shard = {frac:.1f}% remapped.")
    print()
    print("  Watch it get worse as the cluster grows:")
    for n in (2, 4, 8, 16, 32, 64):
        m = sum(1 for i in range(K) if (H[i] % n) != (H[i] % (n + 1)))
        print(f"    {n:>3} -> {n + 1:<3} shards:  {m / K * 100:5.1f}% remapped   "
              f"(theory N/(N+1) = {n / (n + 1) * 100:.1f}%)")
    print("  Almost every key moves. In real life that is copying your entire")
    print("  dataset across the network just to add one machine.")
    return frac


def part3(shares, H):
    print("\n" + "=" * 78)
    print("Part 3: consistent hashing. Put shards on a ring, add one, measure churn")
    print("=" * 78)

    pos_n, own_n = build_ring(N, VNODES)
    pos_n1, own_n1 = build_ring(N + 1, VNODES)

    moved = 0
    loads = [0.0] * N
    for i in range(K):
        before = ring_owner(pos_n, own_n, H[i])
        after = ring_owner(pos_n1, own_n1, H[i])
        loads[before] += shares[i]
        if before != after:
            moved += 1
    frac = moved / K * 100

    print(f"  {N} shards, {VNODES} virtual nodes each, {N * VNODES} points on the ring.")
    print(f"  Add one shard ({N} -> {N + 1}):")
    print(f"    {moved:,} of {K:,} keys change shard = {frac:.1f}% remapped.")
    print(f"    theory says about 1/(N+1) = {100 / (N + 1):.1f}%.")
    print()
    print("  The keys that move only move onto the new shard. Everyone else stays.")
    print()
    hot = max(loads) * 100
    print(f"  But consistent hashing does NOT fix the hot key. Traffic per shard,")
    print(f"  hottest = {hot:.1f}%: the celebrity still lands on one shard and melts it.")
    print("  Consistent hashing fixes the MIGRATION cost, not the skew. The hot key")
    print("  needs its own fix: split it, cache it, or give it a dedicated shard.")
    return frac


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<32} actual = {actual:>8,.1f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<32} you = {predicted:>6,.1f}   actual = {actual:>8,.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    shares = zipf_shares(K, ZIPF_S)
    H = [h64(str(i)) for i in range(K)]

    celeb_pct, range_hot_pct = part1(shares, H)
    modulo_pct = part2(H)
    consistent_pct = part3(shares, H)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 celebrity key share", PREDICTIONS["celebrity_share_pct"], celeb_pct, "%")
    verdict("P2 range hottest shard", PREDICTIONS["range_hottest_pct"], range_hot_pct, "%")
    verdict("P3 modulo remap 8->9", PREDICTIONS["modulo_remap_pct"], modulo_pct, "%")
    verdict("P4 consistent remap 8->9", PREDICTIONS["consistent_remap_pct"], consistent_pct, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  To add one shard, plain modulo moved {modulo_pct:.0f}% of the keys, and that")
    print(f"  climbs toward 100% as the cluster grows. Consistent hashing moved only")
    print(f"  {consistent_pct:.0f}%, about 1/(N+1). Same goal, but one is a weekend-long")
    print("  migration copying the whole dataset, and the other is a shrug.")
    print("  Neither one saves you from the celebrity key. That is a separate fight.")
    print()


if __name__ == "__main__":
    main()
