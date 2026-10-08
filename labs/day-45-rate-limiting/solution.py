"""
Day 45 lab: rate limiting at the front door. Token bucket, the fixed-window
trap, and leaky bucket versus token bucket. This is the client-facing limiter,
the thing at the API gateway that decides who gets in and returns 429 to the
rest. It is NOT Day 27's internal queue backpressure (that was work already
inside the system, pushing back on a producer). This is the bouncer at the door.

This is the full working solution. The starter file is rate_limiting.py.
Run it:      python3 solution.py

Standard library only, no network, no threads, no files. Everything is a
deterministic simulation on a virtual clock measured in seconds, so a "request
at t=59.0" is just a number, nothing sleeps. The one place we use randomness
(a bursty arrival stream for the sustained token-bucket test) is driven by a
seeded RNG, so the run is reproducible to the digit.

The three ideas, each measured:
  - Token bucket. Tokens drip in at a steady rate up to a cap. Each request
    takes one token or is rejected. It lets a controlled BURST through, up to
    the bucket size, then settles to the drip rate. We fire an instant burst and
    watch it get capped at the bucket size, then feed a sustained overload and
    watch the long-run accept rate settle onto the refill rate.
  - The fixed-window trap. A counter of N requests per minute that resets on the
    minute lets a client send N at 11:59:59 and N more at 12:00:00: 2N requests
    in two seconds, straddling the boundary. We reproduce that 2x burst, then
    show a sliding-window counter that counts the TRAILING window closes it.
  - Leaky bucket versus token bucket. A leaky bucket drains at a constant rate,
    so its OUTPUT is a smooth, steady stream no matter how bursty the input: no
    bursts out. A token bucket lets bursts out. We feed both the same bursty
    input and compare the output rate pattern. Use leaky to protect a fragile
    downstream, token to allow friendly bursts.
"""

import collections
import random
import sys

PREDICTIONS = {
    # P1: token bucket, refill rate 10/s, capacity 20, starts full. An instant
    #     burst of 50 requests all arrive at the same moment. How many get in?
    "token_burst_accepted": 20,

    # P2: same bucket, now a sustained overload (about 30 req/s offered for 60s,
    #     three times the refill rate). Over the whole minute, what is the
    #     long-run ACCEPT rate in requests per second? (settles onto what?)
    "token_sustained_rate": 10,

    # P3: fixed-window counter, limit 100 per 60s window. A client sends 100 just
    #     before the boundary and 100 just after. How many get accepted across
    #     that boundary in total?
    "fixed_window_boundary": 200,

    # P4: the exact same request stream, through a sliding-window counter that
    #     counts the trailing 60s. How many get accepted now?
    "sliding_window_boundary": 100,

    # P5: leaky bucket, leak rate 10/s, fed a bursty input. What is its output
    #     rate in requests per second during the active seconds? (constant at?)
    "leaky_output_rate": 10,

    # P6: token bucket fed that same bursty input. What is the MOST requests it
    #     lets out in any single one-second window? (the burst out)
    "token_peak_output": 20,
}

# ---- token bucket knobs ----
TB_RATE = 10            # tokens refill at 10 per second
TB_CAP = 20             # bucket holds at most 20 tokens (the burst allowance)
BURST_SIZE = 50         # instant burst for P1: 50 requests at the same instant
SUSTAINED_LAMBDA = 30   # sustained offered load for P2: ~30 req/s (3x the rate)
SUSTAINED_SECS = 60     # how long the sustained overload runs

# ---- window knobs ----
WINDOW = 60             # a 60-second window
LIMIT = 100             # 100 requests per window
BATCH = 100             # requests fired on each side of the boundary

# ---- leaky bucket knobs ----
LEAK_RATE = 10          # the leaky bucket drains at 10 per second
LEAK_QUEUE = 40         # how many requests can wait in the bucket before overflow
BURSTS_AT = (0, 3, 6, 9, 12)   # bursty input: a burst at each of these seconds
BURST_EACH = 40         # 40 requests in each burst
SIM_SECS = 20           # bin the output over this many seconds

SEED = 45


# ---------------------------------------------------------------------------
# The four TODOs. Each is one load-bearing line, the heart of one algorithm.
# ---------------------------------------------------------------------------

def token_refill_and_take(tokens, capacity, rate, elapsed):
    """TODO 1, the token bucket. `elapsed` seconds have passed since we last
    looked. First drip new tokens in: add elapsed * rate, but never above the
    capacity (that cap is the whole burst allowance). Then, if there is at least
    one whole token, take it and allow the request. Return (new_tokens, allowed).
    This refill-then-take is the entire token bucket."""
    tokens = min(capacity, tokens + elapsed * rate)
    if tokens >= 1.0:
        return tokens - 1.0, True
    return tokens, False


def window_index(now, window):
    """TODO 2, the fixed-window trap in one line. Which fixed window does `now`
    fall into? Requests in the same integer window share one counter, and
    crossing to the next index resets it to zero. That hard reset on the integer
    boundary is exactly what lets a client dump a full limit on each side of it."""
    return int(now // window)


def is_expired(timestamp, now, window):
    """TODO 3, the sliding-window fix. A past request at `timestamp` only counts
    if it falls inside the trailing `window` seconds ending at `now`. Return True
    if it is OLDER than that, so it should be evicted and no longer counted.
    Counting the trailing window instead of a fixed box is what closes the trap."""
    return timestamp <= now - window


def leaky_emit_time(now, next_emit, leak_interval):
    """TODO 4, the leaky bucket. An admitted request leaves the bucket no sooner
    than it arrived (`now`) and no sooner than the previous drip plus one leak
    interval (`next_emit`). Return when it leaves. Because the caller then sets
    the next slot to this time plus one interval, emissions come out spaced
    exactly leak_interval apart: a constant output rate however bursty the input."""
    return max(now, next_emit)


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in. This lets the
    starter stop cleanly with 'fill in TODO N' instead of crashing or hanging."""
    if token_refill_and_take(20.0, 20, 10, 0.0) is None:
        return 1
    if window_index(60.0, 60) is None:
        return 2
    if is_expired(0.0, 60.0, 60) is None:
        return 3
    if leaky_emit_time(5.0, 3.0, 0.1) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# The limiters, each built on one TODO.
# ---------------------------------------------------------------------------

class TokenBucket:
    """Tokens drip in at `rate` per second up to `capacity`. Each request takes
    one token or is rejected. Lazy refill: we only top up when a request shows
    up, using the time since the last one."""

    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)   # start full, so the first burst is allowed
        self.last = 0.0

    def allow(self, now):
        elapsed = now - self.last
        self.last = now
        self.tokens, allowed = token_refill_and_take(
            self.tokens, self.capacity, self.rate, elapsed)
        return allowed


class FixedWindow:
    """A counter of `limit` requests per `window` seconds that resets the instant
    the clock ticks into a new window. Cheap, and quietly broken at the edges."""

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.count = 0
        self.cur = None

    def allow(self, now):
        w = window_index(now, self.window)
        if w != self.cur:
            self.cur = w
            self.count = 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False


class SlidingWindowLog:
    """Keep the timestamps of recent accepts. On each request, drop the ones that
    have aged out of the trailing window, then allow only if fewer than `limit`
    remain. Exact, at the cost of remembering the timestamps."""

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.times = collections.deque()

    def allow(self, now):
        while self.times and is_expired(self.times[0], now, self.window):
            self.times.popleft()
        if len(self.times) < self.limit:
            self.times.append(now)
            return True
        return False


class LeakyBucket:
    """Requests queue in a bucket that drains at a constant `leak_rate`. Admitted
    requests leave spaced exactly one leak interval apart, so the output is a
    steady stream. If the backlog would exceed the queue depth, the request
    overflows and is dropped. Modelled by scheduling each emission's time."""

    def __init__(self, leak_rate, queue_cap):
        self.interval = 1.0 / leak_rate
        self.queue_cap = queue_cap
        self.next_emit = None

    def admit(self, now):
        """Return the time this request leaves the bucket, or None if it overflows
        and is dropped."""
        if self.next_emit is None:
            self.next_emit = now
        emit_time = leaky_emit_time(now, self.next_emit, self.interval)
        # The backlog, in seconds, is how far in the future this would leave.
        # If that is more than the bucket can hold, the bucket is full: drop it.
        if emit_time - now > self.queue_cap * self.interval:
            return None
        self.next_emit = emit_time + self.interval
        return emit_time


# ---------------------------------------------------------------------------
# A seeded bursty arrival stream (the only randomness in the lab).
# ---------------------------------------------------------------------------

def poisson_arrivals(rng, rate, duration):
    """Arrival times of a Poisson process at `rate` per second over `duration`
    seconds. Bursty and clumpy, like real traffic, not evenly spaced."""
    t = 0.0
    out = []
    while True:
        t += rng.expovariate(rate)
        if t >= duration:
            break
        out.append(t)
    return out


# ---------------------------------------------------------------------------
# Part 1: the token bucket. A capped burst, then the drip rate.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: the token bucket. Allow a burst up to the bucket size, then")
    print("        settle to the refill rate.")
    print("=" * 78)
    print(f"  bucket: {TB_RATE} tokens/s refill, capacity {TB_CAP}, starts full.")
    print()

    # The instant burst: BURST_SIZE requests all at the same moment t=0. No time
    # passes between them, so no tokens drip in: the bucket can only pay out what
    # it is already holding, which is its capacity.
    tb = TokenBucket(TB_RATE, TB_CAP)
    burst_ok = sum(1 for _ in range(BURST_SIZE) if tb.allow(0.0))
    print(f"  instant burst of {BURST_SIZE} requests at the same moment:")
    print(f"    accepted {burst_ok}, rejected {BURST_SIZE - burst_ok}")
    print(f"  The burst is capped at the bucket size ({TB_CAP}). A full bucket is")
    print("  the most you can ever spend at once. That is the burst allowance.")
    print()

    # The sustained overload: offer ~3x the refill rate for a full minute.
    rng = random.Random(SEED)
    arrivals = poisson_arrivals(rng, SUSTAINED_LAMBDA, SUSTAINED_SECS)
    tb = TokenBucket(TB_RATE, TB_CAP)
    accepted = sum(1 for t in arrivals if tb.allow(t))
    offered_rate = len(arrivals) / SUSTAINED_SECS
    accept_rate = accepted / SUSTAINED_SECS

    # The steady-state rate, measured after the opening burst has drained, is the
    # refill rate almost exactly.
    warm = SUSTAINED_SECS // 6
    tb2 = TokenBucket(TB_RATE, TB_CAP)
    steady_ok = 0
    for t in arrivals:
        ok = tb2.allow(t)
        if ok and t >= warm:
            steady_ok += 1
    steady_rate = steady_ok / (SUSTAINED_SECS - warm)

    print(f"  sustained overload: {len(arrivals)} requests offered over "
          f"{SUSTAINED_SECS}s ({offered_rate:.1f}/s, {offered_rate / TB_RATE:.1f}x the rate):")
    print(f"    accepted {accepted}, long-run accept rate = {accept_rate:.1f}/s")
    print(f"    steady-state rate after warm-up = {steady_rate:.1f}/s")
    print(f"  Offer three times as much and you still get through at the refill")
    print(f"  rate ({TB_RATE}/s). The bucket caps the burst, then meters the rest.")
    return burst_ok, accept_rate


# ---------------------------------------------------------------------------
# Part 2: the fixed-window trap, and the sliding-window fix.
# ---------------------------------------------------------------------------

def boundary_stream():
    """BATCH requests just before the window boundary (end of window 0) and BATCH
    just after (start of window 1), straddling t = WINDOW. Returns the arrival
    times in order."""
    before = [WINDOW - 1.0 + 0.009 * i for i in range(BATCH)]   # ~59.0 .. 59.9
    after = [WINDOW + 0.009 * i for i in range(BATCH)]           # ~60.0 .. 60.9
    return before + after


def max_in_trailing_window(times, window):
    """The most requests found in any trailing `window`-second span across the
    accepted times: slide a window and count. This is the honest 'rate' a client
    actually achieved, regardless of where the counter drew its boxes."""
    times = sorted(times)
    best = 0
    left = 0
    for right in range(len(times)):
        while times[right] - times[left] >= window:
            left += 1
        best = max(best, right - left + 1)
    return best


def part2():
    print("\n" + "=" * 78)
    print("Part 2: the fixed-window trap. N per minute, reset on the minute, lets")
    print("        a client push 2N across the boundary.")
    print("=" * 78)
    stream = boundary_stream()
    print(f"  limit {LIMIT} per {WINDOW}s window. A client sends {BATCH} just before")
    print(f"  the boundary (t~{WINDOW - 1}) and {BATCH} just after (t~{WINDOW}).")
    print()

    fw = FixedWindow(LIMIT, WINDOW)
    fw_ok_times = [t for t in stream if fw.allow(t)]
    fw_ok = len(fw_ok_times)
    fw_worst = max_in_trailing_window(fw_ok_times, WINDOW)
    print(f"  fixed window:   accepted {fw_ok} across the boundary "
          f"({fw_ok // LIMIT}x the limit)")
    print(f"                  most in any trailing {WINDOW}s = {fw_worst}")
    print(f"  Both batches pass: the first fills window 0, then the counter resets")
    print(f"  on the boundary and the second fills window 1. {fw_ok} requests in about")
    print("  two seconds, through a limiter that promised 100 a minute.")
    print()

    sw = SlidingWindowLog(LIMIT, WINDOW)
    sw_ok_times = [t for t in stream if sw.allow(t)]
    sw_ok = len(sw_ok_times)
    sw_worst = max_in_trailing_window(sw_ok_times, WINDOW)
    print(f"  sliding window: accepted {sw_ok} across the boundary "
          f"({sw_ok // LIMIT}x the limit)")
    print(f"                  most in any trailing {WINDOW}s = {sw_worst}")
    print(f"  The second batch still sees the first batch inside its trailing")
    print(f"  {WINDOW}s, so the counter is already full and the excess is rejected.")
    print("  Counting the trailing window instead of a fixed box closes the trap.")
    return fw_ok, sw_ok


# ---------------------------------------------------------------------------
# Part 3: leaky bucket (smooth output) vs token bucket (bursty output).
# ---------------------------------------------------------------------------

def bursty_input():
    """A clumpy input: BURST_EACH requests at each second in BURSTS_AT, all at the
    same instant. Returns arrival times in order."""
    out = []
    for sec in BURSTS_AT:
        out.extend([float(sec)] * BURST_EACH)
    return out


def bin_counts(times, secs):
    """Count events per one-second bin, bins 0..secs-1. We round to the
    microsecond first so that an emission scheduled for a whole second does not
    land in the second below it through floating-point drift (adding 0.1 ten
    times does not give exactly 1.0)."""
    bins = [0] * secs
    for t in times:
        b = int(round(t, 6))
        if 0 <= b < secs:
            bins[b] += 1
    return bins


def part3():
    print("\n" + "=" * 78)
    print("Part 3: leaky bucket vs token bucket. Same bursty input, very different")
    print("        output.")
    print("=" * 78)
    arrivals = bursty_input()
    print(f"  input: {len(arrivals)} requests in {len(BURSTS_AT)} bursts of "
          f"{BURST_EACH}, at t = {', '.join(str(s) for s in BURSTS_AT)}.")
    print()

    # Token bucket: a request is let out the instant it is accepted, so the output
    # time is the arrival time. Bursts pass straight through, up to the cap.
    tb = TokenBucket(TB_RATE, TB_CAP)
    tb_out = [t for t in arrivals if tb.allow(t)]
    tb_bins = bin_counts(tb_out, SIM_SECS)
    tb_peak = max(tb_bins)

    # Leaky bucket: admitted requests are scheduled to leave at a constant rate.
    # The output time is the emit time, not the arrival time.
    lb = LeakyBucket(LEAK_RATE, LEAK_QUEUE)
    lb_out, dropped = [], 0
    max_wait = 0.0
    for t in arrivals:
        emit = lb.admit(t)
        if emit is None:
            dropped += 1
        else:
            lb_out.append(emit)
            max_wait = max(max_wait, emit - t)
    lb_bins = bin_counts(lb_out, SIM_SECS)
    # Measure the output rate from the spacing of emissions, which is robust to
    # the bin-edge jitter above: a steady stream of k emissions spanning T
    # seconds comes out at (k-1)/T per second, exactly the leak rate.
    if len(lb_out) >= 2:
        lb_rate = (len(lb_out) - 1) / (lb_out[-1] - lb_out[0])
    else:
        lb_rate = 0.0

    print("  token bucket output per second (bin -> count):")
    print("    " + spark(tb_bins))
    print(f"    peak second = {tb_peak} (a burst of up to the bucket size gets out)")
    print(f"    accepted {len(tb_out)} of {len(arrivals)}, rejected on the spot.")
    print()
    print("  leaky bucket output per second (bin -> count):")
    print("    " + spark(lb_bins))
    print(f"    steady output rate = {lb_rate:.1f}/s (the constant leak rate, {LEAK_RATE}/s)")
    print(f"    emitted {len(lb_out)} of {len(arrivals)}, overflowed {dropped}, "
          f"worst wait {max_wait:.1f}s.")
    print()
    print("  The token bucket lets bursts straight out: spikes at each input")
    print("  burst, nothing in between. The leaky bucket holds them and drips a")
    print("  flat stream, paying for it in queueing delay. Use leaky to shield a")
    print("  fragile downstream, token when friendly bursts are fine.")
    return tb_peak, lb_rate


def spark(bins):
    """A tiny per-second bar line: 'b0:20 b1:0 ...' kept short."""
    return " ".join(f"{i}:{c}" for i, c in enumerate(bins))


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>7.1f} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    note = "     close enough" if diff <= max(3.0, 0.15 * abs(predicted)) \
        else f"  off by {diff:.1f}"
    print(f"  {name:<34} you = {predicted:>6.1f}   actual = {actual:>7.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The guess is the point, so make it first.\n")
        sys.exit(1)

    missing = first_blank_todo()
    if missing:
        print(f"\n  !! TODO {missing} is still blank. Fill in the four numbered")
        print("     TODOs, then run again. Nothing below works until each one")
        print(f"     returns a real value. Start with TODO {missing}.\n")
        sys.exit(0)

    burst_ok, token_rate = part1()
    fixed_ok, sliding_ok = part2()
    tb_peak, lb_rate = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 token burst accepted", PREDICTIONS["token_burst_accepted"], burst_ok)
    verdict("P2 token sustained rate", PREDICTIONS["token_sustained_rate"], token_rate, "/s")
    verdict("P3 fixed-window boundary", PREDICTIONS["fixed_window_boundary"], fixed_ok)
    verdict("P4 sliding-window boundary", PREDICTIONS["sliding_window_boundary"], sliding_ok)
    verdict("P5 leaky output rate", PREDICTIONS["leaky_output_rate"], lb_rate, "/s")
    verdict("P6 token peak output", PREDICTIONS["token_peak_output"], tb_peak)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  The fixed window let {fixed_ok} requests through a '100 per minute'")
    print(f"  limit across one boundary, about 2x, because it resets on the clock.")
    print(f"  The sliding window held the same stream to {sliding_ok}. The token bucket")
    print(f"  caps a burst at the bucket size ({burst_ok}) and then meters at the refill")
    print(f"  rate; the leaky bucket emits a flat {lb_rate:.0f}/s no matter the input.")
    print("  Same job, 'who gets in', three different shapes of yes and no.")
    print()


if __name__ == "__main__":
    main()
