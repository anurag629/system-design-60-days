"""
Day 12 lab: leader and follower replication, and the lag in the middle.

This is the full working solution. The starter file is replication.py.
Run it:      python3 solution.py

Standard library only, in memory, no database files. We build a tiny leader
and one follower, joined by a replication stream, with the follower applying
each write after an artificial delay (the lag). Then:

  Part 1  You write a value to the leader and immediately read it back from the
          follower. Because the follower is behind, it usually still has the old
          value. That is a read-your-writes violation: you refresh and your own
          comment is gone. We run many such cycles and report the stale percent
          and how long the stale window lasts.

  Part 2  The two fixes. Read your own recent writes from the leader, or wait for
          the follower to catch up before reading. Either one drops the stale
          percent to zero.

  Part 3  The tradeoff. Asynchronous replication makes writes fast but lets reads
          go stale and can lose data on failover. Synchronous replication makes
          stale reads impossible but the write now pays the replication delay, and
          a single down follower stalls every write. We measure the write-latency
          gap.

The number to carry: the stale read percent at a given lag, versus zero after
the fix.
"""

import queue
import sys
import threading
import time

PREDICTIONS = {
    # P1: you write to the leader, then read the SAME key straight back from the
    #     follower. Out of 100 such reads, how many show the stale (old) value?
    "stale_pct_at_lag": 95,

    # P2: once a write happens, how long (in ms) does the follower keep serving
    #     the old value before it catches up? The lag below is 40 ms.
    "stale_window_ms": 40,

    # P3: a synchronous write waits for the follower before it returns. How long
    #     does one synchronous write take, in ms?
    "sync_write_ms": 45,

    # P4: after you apply the read-your-writes fix, what percent of reads are
    #     stale?
    "stale_pct_after_fix": 0,
}

LAG_S = 0.040                 # the follower reflects a write 40 ms after it lands
P1_CYCLES = 300               # write-then-read-immediately cycles for the stale rate
WINDOW_SAMPLES = 15           # paced cycles to time the stale window
P2_FIX_A_CYCLES = 300         # read-your-writes cycles (fast, routed to the leader)
P2_FIX_B_CYCLES = 50          # wait-for-catch-up cycles (paced, one lag each)
ASYNC_SAMPLES = 300           # async writes to time
SYNC_SAMPLES = 50             # sync writes to time
STALL_TIMEOUT = 0.25          # how long a sync write waits on a down follower
KEY = "post:42:comment"       # the one row everybody is fighting over


class Leader:
    """Takes every write, hands out a monotonic offset, streams writes out."""

    def __init__(self):
        self._data = {}
        self._offset = 0
        self._lock = threading.Lock()
        self.stream = queue.Queue()   # the replication log the follower tails

    def write(self, key, value):
        with self._lock:
            self._offset += 1
            off = self._offset
            self._data[key] = value
        self.stream.put((off, key, value))
        return off

    def read(self, key):
        with self._lock:
            return self._data.get(key)

    @property
    def offset(self):
        with self._lock:
            return self._offset


class Follower:
    """Tails the leader's stream and applies each write, but only after the lag."""

    def __init__(self, leader, lag_s):
        self.leader = leader
        self.lag_s = lag_s
        self._data = {}
        self._applied = 0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._paused = threading.Event()   # set this and the follower "goes down"
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _apply(self, off, key, value):
        # The heart of replication lag: the write does not land on the follower
        # the instant the leader took it. The follower gets the record, then takes
        # a while (network, disk, replay) before the value is readable here.
        time.sleep(self.lag_s)
        with self._lock:
            self._data[key] = value
            self._applied = off

    def _run(self):
        while not self._stop.is_set():
            if self._paused.is_set():
                time.sleep(0.01)
                continue
            try:
                off, key, value = self.leader.stream.get(timeout=0.02)
            except queue.Empty:
                continue
            self._apply(off, key, value)

    def read(self, key):
        with self._lock:
            return self._data.get(key)

    @property
    def applied(self):
        with self._lock:
            return self._applied

    def pause(self):
        self._paused.set()

    def resume(self):
        self._paused.clear()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=1.0)


def new_cluster(lag_s=LAG_S):
    leader = Leader()
    follower = Follower(leader, lag_s)
    return leader, follower


def wait_until(cond, timeout):
    """Spin until cond() is true or the timeout passes. Returns True if it became
    true. Always bounded, so a follower that never moves cannot hang us."""
    deadline = time.perf_counter() + timeout
    while not cond():
        if time.perf_counter() >= deadline:
            return False
        time.sleep(0.001)
    return True


def read_your_writes(leader, follower, key, write_off):
    """Fix A. If the follower has caught up to our write, the follower is safe to
    read. If it is still behind, read the leader so we always see our own write."""
    if follower.applied >= write_off:
        return follower.read(key)
    return leader.read(key)


def read_after_catchup(leader, follower, key, write_off, timeout):
    """Fix B. Hold the read until the follower has applied our write, then read
    the follower. The read is correct but it now waits out the lag."""
    wait_until(lambda: follower.applied >= write_off, timeout)
    return follower.read(key)


def sync_write(leader, follower, key, value, timeout):
    """A synchronous write: take the write, then block until the follower has it
    before returning. Returns the offset, or None if the follower never confirms
    in time (a down or slow follower stalls the write)."""
    off = leader.write(key, value)
    ok = wait_until(lambda: follower.applied >= off, timeout)
    return off if ok else None


def replication_ready(lag_s):
    """Prove the follower actually applies a write before we lean on it."""
    leader, follower = new_cluster(lag_s)
    off = leader.write("__probe__", 1)
    ok = wait_until(lambda: follower.applied >= off, timeout=lag_s * 5 + 0.5)
    follower.stop()
    return ok


def part1():
    print("=" * 78)
    print("Part 1: write to the leader, read it straight back from the follower")
    print("=" * 78)

    # The stale rate: fire write-then-read cycles with no pause between them.
    leader, follower = new_cluster()
    stale = 0
    for i in range(1, P1_CYCLES + 1):
        value = i
        leader.write(KEY, value)
        got = follower.read(KEY)   # immediate read, the follower is still behind
        if got != value:
            stale += 1
    follower.stop()
    stale_pct = 100.0 * stale / P1_CYCLES

    # The stale window: one write at a time, timed until the follower catches up.
    windows = []
    for i in range(WINDOW_SAMPLES):
        leader, follower = new_cluster()
        value = 1000 + i
        off = leader.write(KEY, value)
        start = time.perf_counter()
        wait_until(lambda: follower.applied >= off, timeout=LAG_S * 5 + 0.5)
        windows.append((time.perf_counter() - start) * 1000)
        follower.stop()
    window_ms = sum(windows) / len(windows)
    window_max = max(windows)

    print(f"  lag set to {LAG_S * 1000:.0f} ms, one follower, {P1_CYCLES} write-then-read cycles")
    print(f"  stale reads:   {stale} of {P1_CYCLES}  =  {stale_pct:.1f}% served the OLD value")
    print(f"  stale window:  {window_ms:.1f} ms on average, {window_max:.1f} ms at worst")
    print("  You wrote your comment to the leader and read it back from the follower")
    print("  a heartbeat later. The follower had not applied it yet, so you saw the")
    print("  old value. Refresh, and your own comment is missing for a moment.")
    return stale_pct, window_ms


def part2():
    print("\n" + "=" * 78)
    print("Part 2: the two fixes, and the stale percent drops to zero")
    print("=" * 78)

    # Fix A: read your own writes. Route the read to the leader while the follower
    # is still behind, otherwise read the follower.
    leader, follower = new_cluster()
    stale_a = 0
    for i in range(1, P2_FIX_A_CYCLES + 1):
        value = i
        off = leader.write(KEY, value)
        got = read_your_writes(leader, follower, KEY, off)
        if got != value:
            stale_a += 1
    follower.stop()
    stale_a_pct = 100.0 * stale_a / P2_FIX_A_CYCLES

    # Fix B: wait for the follower to catch up, then read it. Correct, but the read
    # now pays the lag. We time that added read latency too.
    leader, follower = new_cluster()
    stale_b = 0
    read_waits = []
    for i in range(1, P2_FIX_B_CYCLES + 1):
        value = i
        off = leader.write(KEY, value)
        start = time.perf_counter()
        got = read_after_catchup(leader, follower, KEY, off, timeout=LAG_S * 5 + 0.5)
        read_waits.append((time.perf_counter() - start) * 1000)
        if got != value:
            stale_b += 1
    follower.stop()
    stale_b_pct = 100.0 * stale_b / P2_FIX_B_CYCLES
    read_wait_ms = sum(read_waits) / len(read_waits)

    print(f"  fix A, read your writes (route to leader when the follower is behind)")
    print(f"           stale reads: {stale_a} of {P2_FIX_A_CYCLES}  =  {stale_a_pct:.1f}%,  read stays fast")
    print(f"  fix B, wait for the follower to catch up, then read it")
    print(f"           stale reads: {stale_b} of {P2_FIX_B_CYCLES}  =  {stale_b_pct:.1f}%,  but the read now waits {read_wait_ms:.1f} ms")
    print("  Both kill the stale read. Fix A loads the leader a little more. Fix B")
    print("  keeps the read on the follower but makes it wait out the lag.")
    return stale_a_pct


def part3():
    print("\n" + "=" * 78)
    print("Part 3: asynchronous vs synchronous replication, the write-latency gap")
    print("=" * 78)

    # Async writes: the leader returns the instant it logs the write.
    leader, follower = new_cluster()
    async_times = []
    for i in range(ASYNC_SAMPLES):
        start = time.perf_counter()
        leader.write(KEY, i)
        async_times.append((time.perf_counter() - start) * 1000)
    follower.stop()
    async_ms = sum(async_times) / len(async_times)

    # Sync writes: the leader waits for the follower to apply before returning.
    leader, follower = new_cluster()
    sync_times = []
    for i in range(SYNC_SAMPLES):
        start = time.perf_counter()
        sync_write(leader, follower, KEY, i, timeout=LAG_S * 5 + 0.5)
        sync_times.append((time.perf_counter() - start) * 1000)
    follower.stop()
    sync_ms = sum(sync_times) / len(sync_times)

    # What happens when a follower is down.
    leader, follower = new_cluster()
    follower.pause()
    start = time.perf_counter()
    leader.write(KEY, -1)                          # async: returns anyway
    async_down_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    res = sync_write(leader, follower, KEY, -2, timeout=STALL_TIMEOUT)   # sync: stalls
    sync_down_ms = (time.perf_counter() - start) * 1000
    follower.resume()
    follower.stop()

    print(f"  async write latency:  {async_ms:.3f} ms   (leader logs it and returns)")
    print(f"  sync  write latency:  {sync_ms:.3f} ms   (leader waits for the follower)")
    print(f"  synchronous is {sync_ms / async_ms:.0f}x slower per write, and that cost is the lag itself")
    print()
    print(f"  with the follower DOWN:")
    print(f"    async write returned in {async_down_ms:.3f} ms, but the follower never")
    print(f"      got it, so a failover right now would lose that write")
    print(f"    sync write gave up after {sync_down_ms:.0f} ms, unconfirmed: one down")
    print(f"      follower stalls every write until it comes back or is dropped")
    return sync_ms


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<28} actual = {actual:>8,.1f} {unit}  (no prediction)")
        return
    if abs(predicted) < 1 and abs(actual) < 1:
        note = "     nailed it"
    elif predicted == 0:
        note = f"     you said 0, got {actual:,.1f}"
    else:
        ratio = actual / predicted
        if 0.6 <= ratio <= 1.6:
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

    stale_pct, window_ms = part1()
    stale_after = part2()
    sync_ms = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 stale % at lag", PREDICTIONS["stale_pct_at_lag"], stale_pct, "%")
    verdict("P2 stale window", PREDICTIONS["stale_window_ms"], window_ms, "ms")
    verdict("P3 sync write time", PREDICTIONS["sync_write_ms"], sync_ms, "ms")
    verdict("P4 stale % after fix", PREDICTIONS["stale_pct_after_fix"], stale_after, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  At {LAG_S * 1000:.0f} ms of replication lag, {stale_pct:.0f}% of reads straight after a write")
    print(f"  were stale: you saw the old value. After the read-your-writes fix that")
    print(f"  dropped to {stale_after:.0f}%. The lag never went away. We just stopped reading")
    print("  from a replica that had not caught up yet. That is the whole game:")
    print("  asynchronous replication is fast but eventually consistent, and you")
    print("  route around the staleness where it actually matters.")
    print("\nNow write labs/day-12-replication/RESULTS.md.\n")


if __name__ == "__main__":
    main()
