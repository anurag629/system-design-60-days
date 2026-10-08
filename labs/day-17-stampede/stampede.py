"""
Day 17 lab: the thundering herd, also called a cache stampede.

Run it:      python3 stampede.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only. Pure threads, no sockets, no files, nothing to clean up.
Runs in a few seconds.

The story, measured on your own machine:
  - One popular key lives in a cache with a short TTL. It expires. At that exact
    instant a crowd of readers all look, all miss together, and all run the slow
    recompute at once. Part 1 counts the source calls in that burst. It is about
    N, the whole crowd, for one key that went cold for a moment.
  - Fix one, a per-key lock (single flight). Only the first reader recomputes.
    Everyone else waits on the lock and then reads the value the first one just
    wrote. Part 2 shows the source calls drop from N to 1. The catch: the whole
    crowd still waits for that one recompute.
  - Fix two, early recomputation. Refresh the value a little BEFORE it expires,
    using the normal trickle of traffic, so it is never cold when the crowd
    arrives. Part 3 shows the source stays cheap and not one reader blocks.

This is IRCTC at 10 AM tatkal in miniature: the booking opens, every phone in
the country hits the same page in the same second, and the thing behind the
cache either holds or it does not.

If you get stuck, the full working version is solution.py in this folder.
"""

import sys
import threading
import time

PREDICTIONS = {
    # P1: the naive herd. One hot key is cold, N readers all miss at the same
    #     instant. How many times does the slow source get called in that burst?
    "naive_source_calls": None,

    # P2: now with a per-key lock (single flight). Only the first reader should
    #     recompute. How many source calls now?
    "singleflight_source_calls": None,

    # P3: single flight fixes the source load, but what does it cost the crowd?
    #     Of the N readers, how many had to BLOCK and wait for that one
    #     recompute before they got their answer?
    "singleflight_waiters": None,

    # P4: early recomputation keeps the value warm ahead of expiry. When the
    #     same herd arrives now, how many source calls happen in the burst?
    "early_herd_source_calls": None,
}

# ---------------------------------------------------------------------------
# Knobs. The defaults make the race real and the numbers repeatable.
# ---------------------------------------------------------------------------
HOT_KEY = "home:feed:popular"
N_READERS = 100              # the size of the crowd that hits the cache at once
RECOMPUTE_S = 0.05           # the slow source: 50 ms of "work" per miss
TTL = 0.5                    # how long a cached value stays fresh
EARLY_WINDOW = 0.2           # refresh this long BEFORE expiry (fix two)
TRICKLE_READERS = 2          # the steady background traffic in part 3
TRICKLE_INTERVAL = 0.02      # a trickle reader looks every 20 ms
TRICKLE_RUN_S = 1.2          # how long the trickle runs before the herd
BARRIER_TIMEOUT = 10         # safety: never wait forever at the start line
JOIN_TIMEOUT = 10            # safety: never hang joining the crowd

_UNSET = object()            # marks a TODO you have not filled in yet


class TODONotDone(Exception):
    """Raised by a blank TODO so the lab can stop cleanly."""
    def __init__(self, n):
        super().__init__(f"TODO {n} is not filled in yet")
        self.n = n


# ---------------------------------------------------------------------------
# A cache entry and the cache itself
# ---------------------------------------------------------------------------

class Entry:
    __slots__ = ("value", "expiry")

    def __init__(self, value, expiry):
        self.value = value
        self.expiry = expiry


class Cache:
    """A tiny in-memory cache with per-entry expiry, like Redis with a TTL."""

    def __init__(self):
        self._d = {}
        self._lock = threading.Lock()

    def get(self, key):
        """Cache-aside view: the value if present and still fresh, else None."""
        e = self._d.get(key)
        if e is None or time.monotonic() >= e.expiry:
            return None
        return e.value

    def get_entry(self, key):
        """The raw entry, fresh or stale, so early recompute can read expiry."""
        return self._d.get(key)

    def set(self, key, value, ttl):
        with self._lock:
            self._d[key] = Entry(value, time.monotonic() + ttl)


# ---------------------------------------------------------------------------
# The slow source behind the cache, with a thread-safe call counter
# ---------------------------------------------------------------------------

class SlowSource:
    """The expensive thing a miss falls through to: a database query, a page
    render, a fan-out API call. Every call is counted."""

    def __init__(self, recompute_s):
        self.recompute_s = recompute_s
        self._calls = 0
        self._lock = threading.Lock()

    @property
    def calls(self):
        with self._lock:
            return self._calls

    def recompute(self, key):
        with self._lock:
            self._calls += 1
        time.sleep(self.recompute_s)        # the slow part: this is the DB hit
        return "payload-for-" + str(key)


# ---------------------------------------------------------------------------
# One lock per key, created on demand. The heart of single flight.
# ---------------------------------------------------------------------------

class KeyedLocks:
    def __init__(self):
        self._locks = {}
        self._guard = threading.Lock()

    def get(self, key):
        with self._guard:
            lk = self._locks.get(key)
            if lk is None:
                lk = threading.Lock()
                self._locks[key] = lk
            return lk


# ---------------------------------------------------------------------------
# The three read strategies
# ---------------------------------------------------------------------------

def naive_lookup(cache, source, key):
    """Plain cache-aside: check the cache, and on a miss, recompute and store.
    Returns (value, did_recompute). Every reader in the herd runs the miss
    branch at the same instant, which is exactly the stampede."""
    value = cache.get(key)
    if value is not None:
        return value, False

    # MISS. Nothing stops the whole crowd from running the next line together.
    # TODO 1 ------------------------------------------------------------------
    # On a miss, call the slow source to rebuild the value. This one line is
    # what the entire herd runs at the same moment, so it is what you are
    # counting in Part 1.
    #     value = source.recompute(key)
    # -------------------------------------------------------------------------
    value = _UNSET  # <-- replace this (TODO 1)
    if value is _UNSET:
        raise TODONotDone(1)

    cache.set(key, value, TTL)
    return value, True


def singleflight_lookup(cache, source, locks, key):
    """Cache-aside with a per-key lock. Returns (value, status) where status is
    'hit', 'computed' (this reader did the one recompute) or 'waited' (this
    reader blocked on the lock, then read what the first reader stored)."""
    value = cache.get(key)
    if value is not None:
        return value, "hit"

    lock = locks.get(key)
    lock.acquire()
    try:
        # TODO 2 --------------------------------------------------------------
        # You now hold the per-key lock. BEFORE you recompute, look in the cache
        # ONE more time. While you were waiting for this lock, the first reader
        # has already recomputed and stored the value. Re-reading here is the
        # whole trick that turns N recomputes into 1.
        #     cached = cache.get(key)
        # ---------------------------------------------------------------------
        cached = _UNSET  # <-- replace this (TODO 2)
        if cached is _UNSET:
            raise TODONotDone(2)
        if cached is not None:
            return cached, "waited"

        value = source.recompute(key)
        cache.set(key, value, TTL)
        return value, "computed"
    finally:
        lock.release()


def maybe_start_refresh(cache, source, key, gate):
    """Kick off at most one background refresh, without blocking the caller."""
    # TODO 4 ------------------------------------------------------------------
    # Early recompute must not stall the reader and must not start a fresh
    # recompute every time. Try to grab the gate WITHOUT waiting. If you get it,
    # you are the one refresher; the code below starts a background thread. If
    # you do not get it, someone else is already refreshing, so just return.
    #     got = gate.acquire(blocking=False)
    # -------------------------------------------------------------------------
    got = _UNSET  # <-- replace this (TODO 4)
    if got is _UNSET:
        raise TODONotDone(4)
    if not got:
        return

    def _refresh():
        try:
            value = source.recompute(key)
            cache.set(key, value, TTL)
        finally:
            gate.release()

    threading.Thread(target=_refresh, daemon=True).start()


def early_lookup(cache, source, key, gate):
    """Read with early recomputation. Returns (value, status) where status is
    'cold' (the value had expired, so this reader had to block and rebuild it)
    or 'hit' (the value was still fresh and came back immediately)."""
    entry = cache.get_entry(key)
    now = time.monotonic()

    if entry is None or now >= entry.expiry:
        # Cold. We had to block on the source. The whole point of fix two is
        # that a well-timed refresh means the crowd never lands here.
        value = source.recompute(key)
        cache.set(key, value, TTL)
        return value, "cold"

    # The value is still fresh, so this reader is served instantly.
    # TODO 3 ------------------------------------------------------------------
    # Decide whether to refresh AHEAD of expiry. If we are inside the last
    # EARLY_WINDOW seconds before this entry expires, trigger a refresh now, so
    # the value is rebuilt before it ever goes cold. Otherwise leave it alone.
    #     should_refresh = now >= entry.expiry - EARLY_WINDOW
    # -------------------------------------------------------------------------
    should_refresh = _UNSET  # <-- replace this (TODO 3)
    if should_refresh is _UNSET:
        raise TODONotDone(3)

    if should_refresh:
        maybe_start_refresh(cache, source, key, gate)
    return entry.value, "hit"


# ---------------------------------------------------------------------------
# Fire N readers at the same instant, using a barrier as the starting line
# ---------------------------------------------------------------------------

def run_herd(target):
    """Launch N_READERS threads, hold them at a barrier, release them together,
    and collect each one's (value, status) result."""
    barrier = threading.Barrier(N_READERS)
    results = [None] * N_READERS

    def worker(i):
        try:
            barrier.wait(timeout=BARRIER_TIMEOUT)
        except threading.BrokenBarrierError:
            results[i] = (None, "error")
            return
        try:
            results[i] = target()
        except Exception as exc:                 # keep one bad reader from hanging the run
            results[i] = (None, "error:" + type(exc).__name__)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N_READERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=JOIN_TIMEOUT)
    return results


# ---------------------------------------------------------------------------
# Part 1: reproduce the stampede
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: the stampede. One hot key goes cold, the whole crowd misses.")
    print("=" * 78)
    cache = Cache()
    source = SlowSource(RECOMPUTE_S)

    before = source.calls
    results = run_herd(lambda: naive_lookup(cache, source, HOT_KEY))
    calls = source.calls - before
    recomputed = sum(1 for r in results if r and r[1] is True)

    print(f"  readers in the crowd:              {N_READERS}")
    print(f"  readers that ran the recompute:    {recomputed}")
    print(f"  calls to the slow source:          {calls}")
    print("  The key was cold for one instant and every reader missed together,")
    print("  so every reader rebuilt it. One expiry, N trips to the database.")
    print("  That burst is the thundering herd. On a real system it is the spike")
    print("  that knocks over the database the cache was meant to protect.")
    return calls


# ---------------------------------------------------------------------------
# Part 2: fix one, the per-key lock (single flight)
# ---------------------------------------------------------------------------

def part2():
    print("\n" + "=" * 78)
    print("Part 2: fix one. A per-key lock, so only the first reader rebuilds.")
    print("=" * 78)
    cache = Cache()
    source = SlowSource(RECOMPUTE_S)
    locks = KeyedLocks()

    before = source.calls
    results = run_herd(lambda: singleflight_lookup(cache, source, locks, HOT_KEY))
    calls = source.calls - before
    computed = sum(1 for r in results if r and r[1] == "computed")
    waited = sum(1 for r in results if r and r[1] == "waited")

    print(f"  readers in the crowd:              {N_READERS}")
    print(f"  readers that ran the recompute:    {computed}")
    print(f"  readers that waited for it:        {waited}")
    print(f"  calls to the slow source:          {calls}")
    print("  The lock lets exactly one reader rebuild the value. Everyone else")
    print("  waits on the lock, then reads what that one reader just stored. The")
    print("  source goes from a herd to a single call. The catch is right there")
    print(f"  in the numbers: all {waited} other readers still blocked for one recompute.")
    return calls, waited


# ---------------------------------------------------------------------------
# Part 3: fix two, early recomputation
# ---------------------------------------------------------------------------

def part3():
    print("\n" + "=" * 78)
    print("Part 3: fix two. Refresh early, so the value is never cold at the herd.")
    print("=" * 78)
    cache = Cache()
    source = SlowSource(RECOMPUTE_S)
    gate = threading.Lock()

    # Cold start: the first look fills the cache (one call).
    early_lookup(cache, source, HOT_KEY, gate)

    # A steady trickle of normal traffic keeps the key warm. Each time the value
    # drifts into the last EARLY_WINDOW seconds of its life, one reader quietly
    # refreshes it in the background while everyone keeps reading the fresh copy.
    stop = threading.Event()

    def trickle():
        while not stop.is_set():
            early_lookup(cache, source, HOT_KEY, gate)
            time.sleep(TRICKLE_INTERVAL)

    trickles = [threading.Thread(target=trickle, daemon=True)
                for _ in range(TRICKLE_READERS)]
    for t in trickles:
        t.start()
    time.sleep(TRICKLE_RUN_S)
    stop.set()
    for t in trickles:
        t.join(timeout=1)

    # Let any background refresh in flight settle, then top the value up once so
    # the herd below lands on a freshly warm key. (Early recompute has been
    # keeping it warm all along; this just pins the measurement down.)
    time.sleep(RECOMPUTE_S + 0.05)
    cache.set(HOT_KEY, source.recompute(HOT_KEY), TTL)
    warmed_calls = source.calls

    # Now the same crowd as Parts 1 and 2 arrives.
    before = source.calls
    results = run_herd(lambda: early_lookup(cache, source, HOT_KEY, gate))
    herd_calls = source.calls - before
    blocked = sum(1 for r in results if r and r[1] == "cold")

    print(f"  source calls over the whole warm-up ({TRICKLE_RUN_S:.1f}s of trickle): {warmed_calls}")
    print(f"  readers in the herd:               {N_READERS}")
    print(f"  readers that blocked (cold miss):  {blocked}")
    print(f"  source calls during the herd:      {herd_calls}")
    print("  The value was refreshed just before each expiry by a single reader,")
    print("  in the background, while the rest kept reading the fresh copy. So")
    print("  when the crowd arrives the key is warm: everyone gets an instant hit,")
    print("  nobody blocks, and the source is not touched at all in the burst.")
    return herd_calls, blocked, warmed_calls


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>6} {unit}  (no prediction)")
        return
    if abs(actual - predicted) <= 1:
        note = "     close enough"
    elif predicted and 0.6 <= actual / predicted <= 1.6:
        note = "     close enough"
    elif actual > predicted:
        note = "     too LOW"
    else:
        note = "     too HIGH"
    print(f"  {name:<34} you = {predicted:>4}   actual = {actual:>6} {unit}  {note}")


def self_test():
    """Exercise each TODO once, single threaded and instant, before we launch a
    single herd. A blank TODO raises TODONotDone, which we turn into a clean
    'fill in TODO N' message instead of a crash or a hang."""
    missing = set()

    # TODO 1: naive miss path recomputes.
    try:
        c = Cache()
        s = SlowSource(0.0)
        naive_lookup(c, s, "t1")
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 2: single flight double-check under the lock.
    try:
        c = Cache()
        s = SlowSource(0.0)
        singleflight_lookup(c, s, KeyedLocks(), "t2")
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 3: the early-refresh decision (entry fresh, not yet in the window).
    try:
        c = Cache()
        s = SlowSource(0.0)
        c.set("t3", "v", TTL)
        early_lookup(c, s, "t3", threading.Lock())
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 4: the non-blocking single-refresh gate.
    try:
        c = Cache()
        s = SlowSource(0.0)
        maybe_start_refresh(c, s, "t4", threading.Lock())
    except TODONotDone as e:
        missing.add(e.n)

    return sorted(missing)


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

    naive_calls = part1()
    sf_calls, sf_waiters = part2()
    herd_calls, blocked, warmed = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 naive source calls", PREDICTIONS["naive_source_calls"], naive_calls)
    verdict("P2 single-flight source calls", PREDICTIONS["singleflight_source_calls"], sf_calls)
    verdict("P3 single-flight waiters", PREDICTIONS["singleflight_waiters"], sf_waiters)
    verdict("P4 early-recompute herd calls", PREDICTIONS["early_herd_source_calls"], herd_calls)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Same hot key, same crowd of {N_READERS} readers, same slow source.")
    print(f"  Naive cache-aside:  {naive_calls} calls to the source in one burst.")
    print(f"  Per-key lock:        {sf_calls} call, but {sf_waiters} readers had to wait for it.")
    print(f"  Early recompute:     {herd_calls} calls at the herd, {blocked} readers blocked.")
    print("  A stampede is not a caching detail. It is the difference between a")
    print("  cache that shields your database and one that lines the whole crowd")
    print("  up to hit it the moment a popular key expires.")
    print("\nNow write labs/day-17-stampede/RESULTS.md.\n")


if __name__ == "__main__":
    main()
