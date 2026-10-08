"""
Day 15 lab: caching and the cache-aside pattern.

Run it:      python3 cache_aside.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only (sqlite3 is the slow source). Runs in well under a minute,
holds its data in an in-memory SQLite database, and leaves no files behind.

The big ideas, all measured on your own machine:
  - The fastest read is the one that never reaches the database. A cache-aside
    layer is a dict in front of a slow source. On a hit you return from the dict.
    On a miss you pay the source once, store the answer, and every later read of
    that key is a hit. Part 1 shows the mechanism and counts database calls.
  - A cache hit is not "a bit faster" than a database read, it is orders of
    magnitude faster. Part 1 measures a single hit against a single source read,
    and the gap is well past 100x. Part 2 runs a realistic skewed (Zipf) workload
    and shows source load collapse to the miss rate while reads get much faster.
  - Hit rate is the whole ball game, and it is non-linear. Part 3 measures what
    the Day 2 lesson claimed: a cache at 90 percent hit rate sends 10 percent of
    reads to the database, and dropping to 80 percent sends 20 percent, so the
    database load does not go up by a tenth, it DOUBLES.

If you get stuck, the full working version is solution.py in this folder.
"""

import random
import sqlite3
import sys
import time

PREDICTIONS = {
    # P1: a cache HIT is a dict lookup; a source read is a database round trip.
    #     A cache only earns its keep if a hit beats the source by a lot. Predict
    #     the FLOOR: at least how many times faster is a hit than a source read?
    #     The rule of thumb for "worth caching" is about 100x. The real number is
    #     much bigger, and that is the point.
    "hit_vs_source_speedup_x": None,

    # P2: run a skewed (Zipf) workload of many reads through cache-aside. What
    #     fraction of reads are HITS, as a percentage? (With an unbounded cache,
    #     every key misses once and then hits forever, so this is set by how many
    #     distinct keys show up versus how many reads you do.)
    "cache_aside_hit_rate_pct": None,

    # P3: for that same workload, with no cache every read hits the database.
    #     With cache-aside, how many TIMES fewer database calls do you make?
    "source_load_reduction_x": None,

    # P4: the Day 2 number. Source load at an 80 percent hit rate divided by
    #     source load at a 90 percent hit rate. (10 percent misses versus 20
    #     percent misses.) How many times more database load at 80 than at 90?
    "load_multiplier_90_to_80_x": None,
}

N_KEYS = 500                 # distinct rows that live in the source
SOURCE_DELAY_S = 0.002       # a few ms per source read: the database round trip
N_REQUESTS = 5_000           # reads in the Part 2 workload
ZIPF_S = 1.1                 # skew of the Zipf workload (bigger = more skewed)
HOTRATE_REQUESTS = 5_000     # reads per scenario in Part 3
HIT_BENCH_ITERS = 1_000_000  # cache hits timed in the Part 1 micro-benchmark
SOURCE_BENCH_ITERS = 50      # source reads timed in the Part 1 micro-benchmark
SEED = 42

# A sentinel returned from an unfilled TODO so the lab can stop cleanly instead
# of looping forever or crashing. You will replace the TODOs, so you never see it.
_TODO = object()


class SlowSource:
    """A stand-in for a real database: a tiny SQLite table behind a few-ms delay.

    The SELECT is real. The time.sleep is the round trip you would pay talking to
    a database over a socket. Every read is counted, because "how many calls
    reached the database" is the number caching is trying to shrink.
    """

    def __init__(self, n_keys, delay_s):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE kv (k INTEGER PRIMARY KEY, v TEXT)")
        self.conn.executemany(
            "INSERT INTO kv VALUES (?, ?)",
            [(i, f"value-{i}") for i in range(n_keys)],
        )
        self.conn.commit()
        self.delay_s = delay_s
        self.calls = 0

    def get(self, key):
        self.calls += 1
        time.sleep(self.delay_s)                 # the database round trip
        row = self.conn.execute(
            "SELECT v FROM kv WHERE k = ?", (key,)
        ).fetchone()
        return row[0] if row else f"value-{key}"  # fresh keys compute a value


def cache_aside_get(key, cache, source, stats):
    """Read one key the cache-aside way.

    Check the cache first. On a hit, return the cached value and touch nothing
    else. On a miss, this is where the whole pattern lives.
    """
    if key in cache:
        stats["hits"] += 1
        return cache[key]

    stats["misses"] += 1
    # TODO 1 ------------------------------------------------------------------
    # The cache miss. This is the heart of cache-aside. Fetch the value from the
    # slow source, then STORE it in the cache, so the next read of this key is a
    # hit and never touches the database again:
    #     value = source.get(key)
    #     cache[key] = value
    # -------------------------------------------------------------------------
    value = None  # <-- replace: fetch from the source AND populate the cache
    if value is None:
        return _TODO
    return value


def make_zipf_workload(n_requests, n_keys, s, seed):
    """A skewed read workload: a few keys are red hot, most are cold.

    Real traffic looks like this. A handful of items (the viral tweet, the front
    page, the trending product) take most of the reads, and a long tail barely
    gets touched. We shuffle which key id is hot so the hot set is not just the
    low ids.
    """
    rng = random.Random(seed)
    ranks = range(1, n_keys + 1)
    weights = [1.0 / (r ** s) for r in ranks]
    key_ids = list(range(n_keys))
    rng.shuffle(key_ids)
    return rng.choices(key_ids, weights=weights, k=n_requests)


def part1(source):
    print("=" * 78)
    print("Part 1: cache-aside, the mechanism. Hit the dict, miss the database.")
    print("=" * 78)

    # Make sure TODO 1 is filled before we run anything that loops thousands of
    # times. A single probe read: if it comes back unfilled, stop cleanly.
    if cache_aside_get(0, {}, source, {"hits": 0, "misses": 0}) is _TODO:
        print("  (fill in TODO 1)")
        return None

    # A tiny, readable trace so you can watch the cache fill up.
    cache = {}
    stats = {"hits": 0, "misses": 0}
    source.calls = 0
    trace_keys = [10, 20, 10, 30, 20, 10]
    print("  reading keys " + ", ".join(str(k) for k in trace_keys) + ":")
    for k in trace_keys:
        before = source.calls
        cache_aside_get(k, cache, source, stats)
        hit = source.calls == before
        print(f"    key {k:<3} -> {'HIT (from cache)' if hit else 'MISS (go to source)'}")
    print(f"  {len(trace_keys)} reads, {stats['hits']} hits, {stats['misses']} misses, "
          f"{source.calls} database calls")
    print("  The 3 repeats of already-seen keys never touched the database.")

    # Micro-benchmark: one cache hit versus one source read, both through the
    # same cache-aside read path so the comparison is honest.
    warm = {7: source.get(7)}
    bench_stats = {"hits": 0, "misses": 0}
    t0 = time.perf_counter()
    for _ in range(HIT_BENCH_ITERS):
        cache_aside_get(7, warm, source, bench_stats)
    hit_ms = (time.perf_counter() - t0) / HIT_BENCH_ITERS * 1000

    source.calls = 0
    t0 = time.perf_counter()
    for i in range(SOURCE_BENCH_ITERS):
        source.get(i % N_KEYS)
    source_ms = (time.perf_counter() - t0) / SOURCE_BENCH_ITERS * 1000

    speedup = source_ms / hit_ms

    print()
    print(f"  one source read (database round trip): {source_ms:9.4f} ms")
    print(f"  one cache hit  (dict lookup):          {hit_ms:9.6f} ms")
    print(f"  a cache hit is about {speedup:,.0f}x faster than a source read")
    print("  Not 2x, not 10x. Orders of magnitude, well past the 100x that makes")
    print("  a cache worth adding. The fastest read never leaves your process.")
    return speedup


def part2(source):
    print("\n" + "=" * 78)
    print("Part 2: a skewed (Zipf) workload. No cache vs cache-aside, measured.")
    print("=" * 78)
    workload = make_zipf_workload(N_REQUESTS, N_KEYS, ZIPF_S, SEED)

    # No cache: every single read pays the slow source.
    source.calls = 0
    t0 = time.perf_counter()
    for k in workload:
        source.get(k)
    nocache_ms = (time.perf_counter() - t0) * 1000
    nocache_calls = source.calls

    # Cache-aside: the dict absorbs the repeats.
    cache = {}
    stats = {"hits": 0, "misses": 0}
    source.calls = 0
    t0 = time.perf_counter()
    for k in workload:
        cache_aside_get(k, cache, source, stats)
    cache_ms = (time.perf_counter() - t0) * 1000
    cache_calls = source.calls

    total = stats["hits"] + stats["misses"]
    # TODO 2 ------------------------------------------------------------------
    # The hit rate, as a percentage: what share of the reads were hits?
    #     hit_rate_pct = stats["hits"] / total * 100
    # -------------------------------------------------------------------------
    hit_rate_pct = None  # <-- replace this
    if hit_rate_pct is None:
        print("  (fill in TODO 2)")
        return None

    # TODO 3 ------------------------------------------------------------------
    # How many TIMES the cache cut database load: no-cache calls over cache-aside
    # calls. This is the headline of Part 2, source load collapsing to the misses.
    #     load_reduction = nocache_calls / cache_calls
    # -------------------------------------------------------------------------
    load_reduction = None  # <-- replace this
    if load_reduction is None:
        print("  (fill in TODO 3)")
        return None

    nocache_avg_ms = nocache_ms / N_REQUESTS
    cache_avg_ms = cache_ms / N_REQUESTS

    print(f"  workload: {N_REQUESTS:,} reads over {N_KEYS} keys, Zipf skew s={ZIPF_S}")
    print()
    print("  no cache:")
    print(f"    database calls:      {nocache_calls:>8,}   (every read)")
    print(f"    total time:          {nocache_ms:>8.0f} ms")
    print(f"    average read:        {nocache_avg_ms:>8.3f} ms")
    print("  cache-aside:")
    print(f"    hit rate:            {hit_rate_pct:>8.1f} %")
    print(f"    database calls:      {cache_calls:>8,}   (only the misses)")
    print(f"    total time:          {cache_ms:>8.0f} ms")
    print(f"    average read:        {cache_avg_ms:>8.3f} ms")
    print()
    print(f"  the cache cut database calls by {load_reduction:.1f}x and the average")
    print(f"  read got {nocache_avg_ms / cache_avg_ms:.0f}x faster. Source load collapsed to the")
    print("  miss rate: with an unbounded cache each key misses once, so the")
    print("  database only ever sees the first touch of each distinct key.")
    return hit_rate_pct, load_reduction


def run_at_hit_rate(source, target_hit_rate, n_requests, seed):
    """Drive a workload that lands at a known hit rate and count database calls.

    Warm keys are pre-loaded into the cache (guaranteed hits). On each request we
    flip a weighted coin: heads (probability target_hit_rate) reads a warm key,
    tails reads a brand-new key that has never been seen, which is guaranteed to
    miss and hit the database exactly once. So database calls = the misses.
    """
    rng = random.Random(seed)
    warm_keys = list(range(N_KEYS))
    cache = {k: f"value-{k}" for k in warm_keys}   # a warm cache, no source cost
    stats = {"hits": 0, "misses": 0}
    source.calls = 0
    fresh = 1_000_000                              # fresh ids never collide with warm
    for _ in range(n_requests):
        if rng.random() < target_hit_rate:
            key = rng.choice(warm_keys)            # a guaranteed hit
        else:
            key = fresh                            # a guaranteed miss
            fresh += 1
        cache_aside_get(key, cache, source, stats)
    return source.calls


def part3(source):
    print("\n" + "=" * 78)
    print("Part 3: hit rate is non-linear. 90 to 80 does not cost 10 percent.")
    print("=" * 78)

    calls_90 = run_at_hit_rate(source, 0.90, HOTRATE_REQUESTS, SEED)
    calls_80 = run_at_hit_rate(source, 0.80, HOTRATE_REQUESTS, SEED + 1)

    # TODO 4 ------------------------------------------------------------------
    # The Day 2 number. How many times more database load at an 80 percent hit
    # rate than at 90 percent? It is the 80-percent calls over the 90-percent
    # calls, and it should come out near 2, because 20 percent misses is double
    # 10 percent misses.
    #     load_multiplier = calls_80 / calls_90
    # -------------------------------------------------------------------------
    load_multiplier = None  # <-- replace this
    if load_multiplier is None:
        print("  (fill in TODO 4)")
        return None

    print(f"  same {HOTRATE_REQUESTS:,} reads, two different hit rates:")
    print(f"    at 90% hit rate:  {calls_90:>6,} database calls  (about 10% of reads)")
    print(f"    at 80% hit rate:  {calls_80:>6,} database calls  (about 20% of reads)")
    print(f"  dropping 10 points of hit rate multiplied database load by {load_multiplier:.2f}x")
    print("  Ten points of hit rate near the top is not a 10% change in database")
    print("  load, it is roughly double. This is why one bad cache key or a cold")
    print("  cache after a restart can tip a healthy database over on a sale day.")

    print()
    print("  The four cache patterns, and the staleness each one risks:")
    print("  " + "-" * 74)
    print(f"  {'pattern':<14}{'who writes the DB':<26}{'main staleness risk':<34}")
    print("  " + "-" * 74)
    print(f"  {'cache-aside':<14}{'app, on its own':<26}{'cache holds old value till TTL/evict':<34}")
    print(f"  {'read-through':<14}{'cache library, on miss':<26}{'same as cache-aside, hidden in lib':<34}")
    print(f"  {'write-through':<14}{'cache, synchronously':<26}{'little: cache and DB move together':<34}")
    print(f"  {'write-back':<14}{'cache, later in batch':<26}{'DB lags cache; data lost if cache dies':<34}")
    print("  " + "-" * 74)
    print("  Cache-aside is the default: simple, and a cache miss or a dead cache")
    print("  still finds the truth in the database. Write-back is the fastest for")
    print("  writes and the scariest, because the database is behind the cache.")
    return load_multiplier


def verdict(name, predicted, actual, unit="", floor=False):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>9,.1f} {unit}  (no prediction)")
        return
    if floor:
        # A floor prediction: you guessed "at least this much", and beating it is
        # the whole lesson, not a miss.
        if actual >= predicted:
            note = f"PASS, {actual / predicted:,.0f}x past the floor"
        else:
            note = "below the floor"
        print(f"  {name:<30} you >= {predicted:>7,.0f}  actual = {actual:>9,.0f} {unit}  {note}")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<30} you = {predicted:>8,.1f}  actual = {actual:>9,.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    source = SlowSource(N_KEYS, SOURCE_DELAY_S)
    try:
        speedup = part1(source)
        if speedup is None:
            sys.exit(1)

        p2 = part2(source)
        if p2 is None:
            sys.exit(1)
        hit_rate_pct, load_reduction = p2

        load_multiplier = part3(source)
        if load_multiplier is None:
            sys.exit(1)

        print("\n" + "=" * 78)
        print("Scoreboard")
        print("=" * 78)
        verdict("P1 hit vs source speedup", PREDICTIONS["hit_vs_source_speedup_x"], speedup, "x", floor=True)
        verdict("P2 cache-aside hit rate", PREDICTIONS["cache_aside_hit_rate_pct"], hit_rate_pct, "%")
        verdict("P3 source load reduction", PREDICTIONS["source_load_reduction_x"], load_reduction, "x")
        verdict("P4 load mult 90->80", PREDICTIONS["load_multiplier_90_to_80_x"], load_multiplier, "x")

        print("\n" + "=" * 78)
        print("The number to carry")
        print("=" * 78)
        print(f"  A cache hit came back about {speedup:,.0f}x faster than a database read,")
        print(f"  so a {hit_rate_pct:.0f}% hit rate cut database calls by roughly {load_reduction:.0f}x. But hit")
        print(f"  rate is non-linear: going from 90% to 80% did not add a tenth of")
        print(f"  the load, it multiplied it by {load_multiplier:.1f}x, because misses went from")
        print("  1 in 10 to 1 in 5. The fastest read is the one that never reaches")
        print("  the database, and a few points of hit rate is the whole game.")
        print("\nNow write labs/day-15-cache-aside/RESULTS.md.\n")
    finally:
        source.conn.close()


if __name__ == "__main__":
    main()
