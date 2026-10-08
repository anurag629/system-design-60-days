"""
Day 16 lab: eviction and the working set.

Run it:      python3 eviction.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only. Pure in-memory, no files, no sockets, no threads. Runs in
a few seconds and is fully deterministic (fixed seed), so the numbers come out
the same every time.

The one idea, measured on your own machine:
  A cache is almost always smaller than the data behind it, so it cannot hold
  everything. What it throws out decides your hit rate, and your hit rate decides
  your database bill. Three things fall out of today's run:

  - LRU in a dozen lines. collections.OrderedDict already remembers insertion
    order, so least-recently-used is just "the key at the front". A read bumps
    its key to the back (most-recently-used), and when the cache is full you evict
    the front. Part 1 builds it and checks it evicts the right key.

  - The knee. Under a Zipf workload (a few keys are very hot, a long cold tail),
    a cache holding a tiny fraction of the keys already captures most of the
    reads, because those few hot keys ARE most of the reads. Plot hit rate against
    cache size and the curve shoots up then flattens. Under a UNIFORM workload
    there is no hot set to capture, so the same plot is a near-straight diagonal:
    hit rate just tracks the fraction of keys you can afford to hold. Part 2 draws
    both curves side by side.

  - Policy matters. At one fixed size, LRU beats a dumber policy (FIFO, or random
    eviction) on the Zipf workload, because LRU notices which keys keep getting
    read and keeps the hot set resident. FIFO evicts by age alone and keeps
    throwing hot keys out on schedule. Part 3 runs all three head to head.

If you get stuck, the full working version is solution.py in this folder.
"""

import random
import sys
from collections import OrderedDict

PREDICTIONS = {
    # P1: the KNEE. Zipf reads, a cache that holds just 1 percent of the keys.
    #     What hit rate (percent) do you get? (A few hot keys dominate the reads,
    #     so this is much higher than 1 percent.)
    "zipf_hit_at_1pct": None,

    # P2: the CONTRAST. The SAME 1 percent cache, but a UNIFORM workload where
    #     every key is equally likely. What hit rate (percent) now? (With no hot
    #     set, the cache can only win on the fraction of keys it happens to hold.)
    "uniform_hit_at_1pct": None,

    # P3: COVERING the working set. Zipf reads, a cache grown to 20 percent of the
    #     keys. What hit rate (percent)? (You are now past the knee, so growing
    #     the cache buys less and less.)
    "zipf_hit_at_20pct": None,

    # P4: POLICY. At the 1 percent cache on the Zipf workload, by how many
    #     PERCENTAGE POINTS does LRU beat FIFO?
    "lru_minus_fifo_points": None,
}

K = 10_000             # keyspace: this many distinct keys exist behind the cache
N = 200_000            # this many reads in the workload trace
ZIPF_S = 1.1           # Zipf skew. Real web and CDN traffic sits around 0.8 to 1.2
SEED = 42

# cache sizes to sweep, as a count of keys, from 0.1 percent up to 20 percent of K
CAPACITIES = [10, 50, 100, 200, 500, 1000, 2000]
KNEE_CAP = 100         # 1 percent of K, the size we quote for P1, P2 and P4
COVER_CAP = 2000       # 20 percent of K, the size we quote for P3
BAR_WIDTH = 40         # width of the ASCII bars, in characters, for 100 percent


class Cache:
    """A fixed-capacity cache with a pluggable eviction policy.

    policy is one of:
      "lru"    least recently used: a read bumps the key to most-recently-used,
               and eviction drops the least-recently-used (the front).
      "fifo"   first in, first out: a read does NOT change anything, eviction
               drops whatever was inserted longest ago (also the front).
      "random" eviction drops a uniformly random resident key.

    LRU and FIFO differ by exactly one thing: whether a read counts as a "use".
    That single difference is the whole reason LRU keeps the hot set resident.
    """

    def __init__(self, capacity, policy="lru"):
        self.capacity = capacity
        self.policy = policy
        self.data = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.unfilled = None            # set if a TODO is still blank
        self._rng = random.Random(SEED + 99)

    def get(self, key):
        """Look the key up. Return its value, or None on a miss."""
        if key in self.data:
            self.hits += 1
            if self.policy == "lru":
                # TODO 1 ----------------------------------------------------------
                # A read is a "use". LRU must mark this key MOST-recently-used, so
                # it is the LAST thing evicted. OrderedDict has exactly this move:
                #     self.data.move_to_end(key)
                # Write that line, then delete the one marker line below.
                self.unfilled = 1       # <-- delete this line once TODO 1 is done
                # -----------------------------------------------------------------
            return self.data[key]
        self.misses += 1
        return None

    def put(self, key, value):
        """Store the key, evicting one entry if that puts us over capacity.

        In this lab put is only ever called right after a miss, so the key is
        always new. That keeps the whole LRU story in two moves: the read bump in
        get, and the front eviction here.
        """
        self.data[key] = value
        if len(self.data) > self.capacity:
            self._evict()

    def _evict(self):
        if self.policy == "random":
            victim = self._rng.choice(list(self.data))
            del self.data[victim]
        else:
            # TODO 2 --------------------------------------------------------------
            # The cache is over capacity. Both LRU and FIFO evict the FRONT of the
            # OrderedDict. For FIFO that is the oldest insertion. For LRU, because
            # every read moved its key to the back, the front is the LEAST-recently
            # -used key. OrderedDict pops the front with:
            #     self.data.popitem(last=False)
            # Write that line, then delete the two marker lines below.
            self.unfilled = 2           # <-- delete this line once TODO 2 is done
            return                      # <-- delete this line too
            # ---------------------------------------------------------------------

    def hit_rate(self):
        """Hits as a percentage of all lookups."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        # TODO 3 ------------------------------------------------------------------
        # Hit rate as a PERCENT: hits out of all lookups, times 100.
        #     return 100.0 * self.hits / total
        # Replace the None below with that.
        return None  # <-- replace this
        # -------------------------------------------------------------------------


def make_zipf_trace():
    """N reads over K keys, Zipf-skewed: key 1 is the hottest, key K the coldest.

    random.choices with weights proportional to 1/rank^s draws the trace in one
    pass. The weights are built once, so this is cheap even at N = 200,000.
    """
    random.seed(SEED)
    keys = range(1, K + 1)
    weights = [1.0 / (rank ** ZIPF_S) for rank in keys]
    return random.choices(keys, weights=weights, k=N)


def make_uniform_trace():
    """N reads over K keys, every key equally likely. No hot set at all."""
    random.seed(SEED + 1)
    return random.choices(range(1, K + 1), k=N)


def replay(trace, capacity, policy):
    """Run a trace through a fresh cache, cache-aside style, return the cache.

    Cache-aside: on a miss, the app would fetch from the database and store the
    value. Here the value is just the key itself, because we only care about
    whether the lookup hit or missed, not what was stored.
    """
    cache = Cache(capacity, policy)
    for key in trace:
        if cache.get(key) is None:
            cache.put(key, key)
    return cache


def pct_label(cap):
    return f"{100.0 * cap / K:g}%"


def bar(rate):
    filled = int(round(rate / 100.0 * BAR_WIDTH))
    return "#" * filled + " " * (BAR_WIDTH - filled)


def part1():
    print("=" * 78)
    print("Part 1: build the LRU cache, and check it evicts the RIGHT key.")
    print("=" * 78)

    cache = Cache(capacity=2, policy="lru")
    cache.put("A", 1)          # cache: [A]
    cache.put("B", 2)          # cache: [A, B]   (B is most recent)
    cache.get("A")             # read A: now A is most recent, B is least recent
    if cache.unfilled is not None:
        print(f"  (fill in TODO {cache.unfilled})")
        return None
    cache.put("C", 3)          # over capacity: LRU must evict B, NOT A
    if cache.unfilled is not None:
        print(f"  (fill in TODO {cache.unfilled})")
        return None

    resident = set(cache.data.keys())
    evicted_right = resident == {"A", "C"}

    print("  put A, put B, read A, put C   (capacity is 2)")
    print(f"  after the read, A is most-recently-used and B is least-recently-used")
    print(f"  so putting C should evict B. resident keys now: {sorted(resident)}")
    if evicted_right:
        print("  PASS: B was evicted, A survived because the read kept it warm.")
    else:
        print("  FAIL: wrong key evicted. Check TODO 1 (the read bump) and TODO 2.")
    assert evicted_right, "LRU evicted the wrong key"
    return True


def part2():
    print("\n" + "=" * 78)
    print("Part 2: the hit-rate-vs-size curve. Zipf vs uniform, same cache.")
    print("=" * 78)

    zipf = make_zipf_trace()
    uniform = make_uniform_trace()

    zipf_rates = {}
    uniform_rates = {}
    for cap in CAPACITIES:
        zr = replay(zipf, cap, "lru").hit_rate()
        if zr is None:
            print("  (fill in TODO 3)")
            return None
        ur = replay(uniform, cap, "lru").hit_rate()
        if ur is None:
            print("  (fill in TODO 3)")
            return None
        zipf_rates[cap] = zr
        uniform_rates[cap] = ur

    print("  ZIPF reads (a few keys are very hot): hit rate as the cache grows")
    for cap in CAPACITIES:
        print(f"    {pct_label(cap):>5} of keys |{bar(zipf_rates[cap])}| {zipf_rates[cap]:5.1f}%")
    print()
    print("  UNIFORM reads (every key equally likely): same cache, same sizes")
    for cap in CAPACITIES:
        print(f"    {pct_label(cap):>5} of keys |{bar(uniform_rates[cap])}| {uniform_rates[cap]:5.1f}%")

    print()
    print("  The Zipf curve shoots up then flattens: that bend is the KNEE. A")
    print("  cache of 1 percent of the keys already serves about half the reads,")
    print("  because a handful of hot keys ARE half the reads. The uniform curve")
    print("  is a near-straight diagonal: with no hot set, hit rate can only track")
    print("  the fraction of keys you can afford to hold. Same cache, same sizes,")
    print("  wildly different payoff, decided entirely by the shape of the demand.")
    return zipf_rates, uniform_rates


def part3():
    print("\n" + "=" * 78)
    print(f"Part 3: policy matters. Same Zipf load, same size ({pct_label(KNEE_CAP)}), 3 policies.")
    print("=" * 78)

    zipf = make_zipf_trace()
    lru_rate = replay(zipf, KNEE_CAP, "lru").hit_rate()
    fifo_rate = replay(zipf, KNEE_CAP, "fifo").hit_rate()
    rand_rate = replay(zipf, KNEE_CAP, "random").hit_rate()

    # TODO 4 ----------------------------------------------------------------------
    # The headline: how many PERCENTAGE POINTS does LRU beat FIFO by? It is just
    # the difference of the two hit rates.
    #     gap = lru_rate - fifo_rate
    # Replace the None below with that.
    gap = None  # <-- replace this
    # -----------------------------------------------------------------------------
    if gap is None:
        print("  (fill in TODO 4)")
        return None

    print(f"    LRU     |{bar(lru_rate)}| {lru_rate:5.1f}%")
    print(f"    FIFO    |{bar(fifo_rate)}| {fifo_rate:5.1f}%")
    print(f"    random  |{bar(rand_rate)}| {rand_rate:5.1f}%")
    print()
    print(f"  LRU beats FIFO by {gap:.1f} points on the very same workload and size.")
    print("  FIFO and random land together, a little behind, because neither looks")
    print("  at how often a key is read. They evict a hot key on schedule and then")
    print("  pay to fetch it again. LRU notices the re-reads and keeps the hot set")
    print("  resident, so it spends its scarce slots on the keys that earn them.")
    return lru_rate, fifo_rate, rand_rate, gap


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>7,.1f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<30} you = {predicted:>5,.1f}   actual = {actual:>7,.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    p1 = part1()
    if p1 is None:
        sys.exit(1)

    p2 = part2()
    if p2 is None:
        sys.exit(1)
    zipf_rates, uniform_rates = p2

    p3 = part3()
    if p3 is None:
        sys.exit(1)
    lru_rate, fifo_rate, rand_rate, gap = p3

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 Zipf hit @ 1% cache", PREDICTIONS["zipf_hit_at_1pct"], zipf_rates[KNEE_CAP], "%")
    verdict("P2 uniform hit @ 1% cache", PREDICTIONS["uniform_hit_at_1pct"], uniform_rates[KNEE_CAP], "%")
    verdict("P3 Zipf hit @ 20% cache", PREDICTIONS["zipf_hit_at_20pct"], zipf_rates[COVER_CAP], "%")
    verdict("P4 LRU - FIFO (points)", PREDICTIONS["lru_minus_fifo_points"], gap, "pts")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  A cache holding just {pct_label(KNEE_CAP)} of the keys served {zipf_rates[KNEE_CAP]:.0f}% of the Zipf")
    print(f"  reads. The same size on a uniform workload served only {uniform_rates[KNEE_CAP]:.0f}%. Growing")
    print(f"  the cache to {pct_label(COVER_CAP)} of the keys got Zipf to {zipf_rates[COVER_CAP]:.0f}%, so most of the")
    print(f"  win came from the first slice: that is the knee. And at a fixed size,")
    print(f"  LRU beat FIFO by {gap:.0f} points just by treating a read as a vote to keep.")
    print(f"  This is why Redis is small next to the database it fronts, and why the")
    print(f"  question is never 'cache everything', it is 'cache the hot set'.")
    print("\nNow write labs/day-16-eviction/RESULTS.md.\n")


if __name__ == "__main__":
    main()
