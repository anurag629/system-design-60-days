"""
Day 4 lab: why a server at 90% busy feels fine and at 99% falls over.

Run it:      python3 queue_lab.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only. Takes about 40 seconds, most of it in part 2, which
runs in real time on purpose.

Part 1 simulates a server with a queue in front of it, a few hundred thousand
requests at a time, so the numbers are smooth. Part 2 runs a real worker thread
with a real queue and real clocks, so the numbers are noisy but honest. If the
two disagree wildly, trust neither and find out why.
"""

import heapq
import queue
import random
import statistics
import sys
import threading
import time

# ---------------------------------------------------------------------------
# YOUR PREDICTIONS. Paper first, then here, then run.
# ---------------------------------------------------------------------------

PREDICTIONS = {
    # One server. Each request needs 10 ms of work on average, so the server
    # can handle at most 100 requests per second. "Utilization" is how much of
    # that capacity the incoming traffic uses: 50 req/s is 50% utilization.
    #
    # Latency here means the full time a request spends in the system:
    # waiting in the queue PLUS being served.

    # Q1: average latency in ms at 50% utilization (50 req/s).
    "avg_ms_at_50pct": None,

    # Q2: average latency in ms at 90% utilization (90 req/s).
    "avg_ms_at_90pct": None,

    # Q3: average latency in ms at 99% utilization (99 req/s).
    "avg_ms_at_99pct": None,

    # Q4: same 90 req/s of traffic, but now TWO identical servers share one
    #     queue. Each server is still 10 ms per request. Average latency in ms?
    "avg_ms_at_90rps_two_servers": None,
}

# ---------------------------------------------------------------------------

SERVICE_MS = 10.0               # average work per request
CAPACITY = 1000 / SERVICE_MS    # requests per second one server can handle
SIM_REQUESTS = 300_000
UTILIZATIONS = [0.5, 0.7, 0.8, 0.9, 0.95, 0.99]


def percentile(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * p / 100))]


def arrivals_and_work(rate_per_ms, n, rng):
    """Generate n requests: (arrival time, how much work it needs), in ms.

    Arrivals are random, the way real users are: nobody coordinates with anybody
    else, so sometimes three requests land in the same millisecond and sometimes
    nothing arrives for a while. The same goes for work: most requests are
    quick, a few are slow. expovariate() produces exactly that kind of
    randomness. (The textbook name for this setup is an M/M/1 queue.)
    """
    t = 0.0
    out = []
    for _ in range(n):
        t += rng.expovariate(rate_per_ms)
        out.append((t, rng.expovariate(1 / SERVICE_MS)))
    return out


# ---------------------------------------------------------------------------
# Part 1: simulate one server with a queue
# ---------------------------------------------------------------------------

def simulate_one_server(requests):
    """Return the latency of every request, in ms, for ONE server.

    Requests are served first come, first served. The server can only work on
    one request at a time. If it's busy when a request arrives, the request
    waits in the queue.
    """
    latencies = []
    free_at = 0.0   # the moment the server finishes its current work

    for arrival, work in requests:
        # TODO 1 --------------------------------------------------------------
        # Three lines. This is the whole of queueing, honestly.
        #
        # A request can start when BOTH it has arrived AND the server is free:
        #     start = max(arrival, free_at)
        # It finishes after its work is done, and the server is busy until then:
        #     free_at = start + work
        # Its latency is the gap between arriving and finishing:
        #     latencies.append(free_at - arrival)
        # ---------------------------------------------------------------------
        pass  # <-- replace this

    return latencies


def simulate_many_servers(requests, n_servers):
    """Same idea, but n_servers identical servers share ONE queue.

    Like a bank with one line and several counters: whoever is at the front
    goes to whichever counter frees up first.
    """
    # A heap is a list that always gives you its smallest item quickly. Here it
    # holds the "free_at" time of every server, so heap[0] is always the server
    # that will be free soonest.
    free_times = [0.0] * n_servers
    heapq.heapify(free_times)
    latencies = []

    for arrival, work in requests:
        # TODO 2 --------------------------------------------------------------
        # Same three steps as TODO 1, but first take the soonest-free server
        # off the heap, and put it back with its new free time afterwards:
        #
        #     soonest = heapq.heappop(free_times)
        #     start = max(arrival, soonest)
        #     done = start + work
        #     heapq.heappush(free_times, done)
        #     latencies.append(done - arrival)
        # ---------------------------------------------------------------------
        pass  # <-- replace this

    return latencies


def part1():
    print("=" * 78)
    print(f"Part 1: one server, {SERVICE_MS:.0f} ms of work per request on average, "
          f"so {CAPACITY:.0f} req/s max")
    print(f"        {SIM_REQUESTS:,} simulated requests per row")
    print("=" * 78)
    print(f"  {'busy':>6} {'req/s':>7} {'avg ms':>9} {'p50 ms':>9} {'p99 ms':>9} "
          f"{'formula':>9} {'avg / work':>11}")
    rng = random.Random(4)
    out = {}
    for u in UTILIZATIONS:
        reqs = arrivals_and_work(u * CAPACITY / 1000, SIM_REQUESTS, rng)
        lat = simulate_one_server(reqs)
        if not lat:
            print("  (fill in TODO 1)")
            return None
        avg = statistics.fmean(lat)
        formula = SERVICE_MS / (1 - u)
        out[u] = avg
        print(f"  {u:>5.0%} {u * CAPACITY:>7.0f} {avg:>9.1f} {percentile(lat, 50):>9.1f} "
              f"{percentile(lat, 99):>9.1f} {formula:>9.1f} {avg / SERVICE_MS:>10.1f}x")

    print("\n  'formula' is the textbook answer for this kind of queue:")
    print("      average latency = work / (1 - utilization)")
    print("  At 50% busy you wait as long as the work itself. At 90% you wait nine")
    print("  times as long. At 99%, ninety-nine times. The curve isn't a line.")
    print("  It's a wall, and it lives just before 100%.")

    print(f"\n  Same traffic at 90 req/s, more servers sharing one queue:")
    reqs = arrivals_and_work(0.9 * CAPACITY / 1000, SIM_REQUESTS, random.Random(5))
    for n in (1, 2, 3):
        lat = simulate_many_servers(reqs, n)
        if not lat:
            print("  (fill in TODO 2)")
            return out
        avg = statistics.fmean(lat)
        if n == 2:
            out["two"] = avg
        print(f"    {n} server{'s' if n > 1 else ' '}  each {0.9 / n:>4.0%} busy   "
              f"avg {avg:>7.1f} ms   p99 {percentile(lat, 99):>7.1f} ms")
    print("  Adding one server halves the utilization but cuts latency by far more")
    print("  than half. You're not buying speed, you're buying distance from the wall.")
    return out


# ---------------------------------------------------------------------------
# Part 2: a real queue, a real worker thread, real time
# ---------------------------------------------------------------------------

REAL_SECONDS = 8
REAL_UTILIZATIONS = [0.5, 0.8, 0.9]


def run_real(u):
    """Push requests into a real queue.Queue at random times, and let one real
    worker thread serve them, sleeping for each request's 'work'.

    Meanwhile a third thread peeks at the system every few ms and counts how
    many requests are inside it (waiting + being served).
    """
    q = queue.Queue()
    latencies = []
    in_system = [0]           # waiting + being served, right now
    lock = threading.Lock()
    samples = []
    stop = threading.Event()
    rng = random.Random(int(u * 100))
    rate_per_s = u * CAPACITY

    def worker():
        while True:
            item = q.get()
            if item is None:
                return
            arrived, work_ms = item
            time.sleep(work_ms / 1000)
            done = time.perf_counter()
            # TODO 3 ----------------------------------------------------------
            # Record this request's latency in ms, and note that it has left
            # the system:
            #
            #     latencies.append((done - arrived) * 1000)
            #     with lock:
            #         in_system[0] -= 1
            # -----------------------------------------------------------------
            pass  # <-- replace this

    def sampler():
        while not stop.is_set():
            with lock:
                samples.append(in_system[0])
            time.sleep(0.002)

    w = threading.Thread(target=worker, daemon=True)
    s = threading.Thread(target=sampler, daemon=True)
    w.start()
    s.start()

    start = time.perf_counter()
    sent = 0
    next_at = start
    while True:
        next_at += rng.expovariate(rate_per_s)
        if next_at - start > REAL_SECONDS:
            break
        # Sleep until the next arrival is due. Sleeping in a loop and checking
        # the clock keeps the arrivals on schedule even when sleep overshoots.
        while (delay := next_at - time.perf_counter()) > 0:
            time.sleep(delay)
        with lock:
            in_system[0] += 1
        q.put((time.perf_counter(), rng.expovariate(1 / SERVICE_MS)))
        sent += 1

    elapsed = time.perf_counter() - start
    stop.set()
    q.put(None)
    w.join(timeout=30)
    return latencies, samples, sent / elapsed


def part2():
    print("\n" + "=" * 78)
    print(f"Part 2: real threads, real clock, {REAL_SECONDS} s per row. Noisy on purpose.")
    print("=" * 78)
    print(f"  {'busy':>6} {'sent/s':>7} {'avg ms':>9} {'p99 ms':>9} "
          f"{'avg in system':>14} {'Little says':>12}")
    for u in REAL_UTILIZATIONS:
        lat, samples, rate = run_real(u)
        if not lat:
            print("  (fill in TODO 3)")
            return
        avg_ms = statistics.fmean(lat)
        measured_L = statistics.fmean(samples) if samples else 0

        # TODO 4 --------------------------------------------------------------
        # Little's Law: the average number of requests inside a system equals
        # the arrival rate times the average time each one spends inside.
        #     L = arrival rate x average latency
        # Mind the units: `rate` is per SECOND, `avg_ms` is in MILLISECONDS.
        #
        #     littles_L = rate * (avg_ms / 1000)
        # ---------------------------------------------------------------------
        littles_L = None  # <-- replace this

        little = f"{littles_L:>12.2f}" if littles_L is not None else "  (TODO 4)"
        print(f"  {u:>5.0%} {rate:>7.1f} {avg_ms:>9.1f} {percentile(lat, 99):>9.1f} "
              f"{measured_L:>14.2f} {little}")

    print("\n  'avg in system' was counted by a thread peeking every 2 ms.")
    print("  'Little says' was computed from just two numbers, rate and latency.")
    print("  They should roughly agree. Little's Law holds for any stable system,")
    print("  whatever the arrival pattern, which is why it's the one queueing")
    print("  formula worth tattooing somewhere.")
    print(f"\n  Real sleeps overshoot, often by a millisecond or more, so each request")
    print(f"  costs more than {SERVICE_MS:.0f} ms and the real server is busier than its label.")
    print("  Compare these rows with part 1. A small overshoot barely shows at 50%,")
    print("  and at 90% it pushes you right up against the wall.")


# ---------------------------------------------------------------------------

def verdict(name, predicted, actual):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>9,.1f} ms  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.8 <= ratio <= 1.25:
        note = "     nailed it"
    elif ratio > 1:
        note = f"{ratio:>7.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>7.1f}x  too HIGH"
    print(f"  {name:<34} you = {predicted:>8,.1f}   actual = {actual:>9,.1f} ms  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    sim = part1()
    if sim is None:
        sys.exit(1)
    part2()

    print("\n" + "=" * 78)
    print("Scoreboard   (simulated numbers, part 1)")
    print("=" * 78)
    verdict("Q1 avg latency at 50% busy", PREDICTIONS["avg_ms_at_50pct"], sim[0.5])
    verdict("Q2 avg latency at 90% busy", PREDICTIONS["avg_ms_at_90pct"], sim[0.9])
    verdict("Q3 avg latency at 99% busy", PREDICTIONS["avg_ms_at_99pct"], sim[0.99])
    if "two" in sim:
        verdict("Q4 90 req/s on two servers", PREDICTIONS["avg_ms_at_90rps_two_servers"], sim["two"])

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Going from 90% to 99% busy is only 10% more traffic. Average latency")
    print(f"  went from {sim[0.9]:.0f} ms to {sim[0.99]:.0f} ms, {sim[0.99] / sim[0.9]:.0f}x worse. Nothing broke. No code")
    print("  changed. The server just ran out of slack. This is why production")
    print("  systems are planned to run at 60 to 70% busy, not 95.")
    print("\nNow write labs/day-04-queues/RESULTS.md.\n")


if __name__ == "__main__":
    main()
