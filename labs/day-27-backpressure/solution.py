"""
Day 27 lab: backpressure and load shedding.

This is the full working solution. The starter file is backpressure.py.
Run it:      python3 solution.py

Standard library only (queue, threading, time). Runs in about 12 seconds and
leaves nothing behind: no files, no temp databases, every thread joined.

The story, all measured on your own machine, is Day 4's queue cliff made real
for a work queue. A producer offers jobs about twice as fast as the consumer
can finish them. What happens next depends entirely on the queue between them.

  - Part 1, the unbounded queue disaster. The queue says yes to everything, so
    it grows without bound. Memory climbs and, by Little's Law (Day 4), the time
    a new job waits before it is even picked up heads to infinity. Nothing
    errors. It just gets slowly, quietly, fatally worse.
  - Part 2, the bounded queue and backpressure. Cap the queue. Now a blocking
    put() parks the producer whenever the queue is full, so the fast producer is
    forced down to the consumer's rate. Backpressure has travelled upstream. The
    queue depth holds steady and the producer stops running flat out.
  - Part 3, load shedding. Real incoming requests do not wait politely for a
    slot. So when the bounded queue is full we REJECT the excess fast, the moral
    equivalent of returning HTTP 429, instead of queuing it. We count accepted
    vs shed and watch the system stay alive. A fast "no" protects you where an
    unbounded "yes" kills you.

The one lesson, straight out of Day 4: run below 100 percent and keep the queue
bounded. An unbounded queue is not a safety net, it is a slow-motion outage.
"""

import queue
import sys
import threading
import time

PREDICTIONS = {
    # P1: the producer offers about twice as fast as the consumer drains, into
    #     an UNBOUNDED queue, for RUN_S seconds. Roughly how many jobs are
    #     backed up in the queue at the end?
    "unbounded_final_depth": 600,

    # P2: now cap the queue at CAP and let put() block when it is full. The
    #     producer is forced down to the consumer's rate. Roughly what queue
    #     depth do you see then, held steady?
    "bounded_final_depth": 50,

    # P3: backpressure means the producer can no longer run flat out. By what
    #     factor does it cut the producer's output versus the unbounded run?
    #     (jobs placed when unbounded / jobs placed when bounded)
    "backpressure_throttle_x": 2.0,

    # P4: switch to load shedding (reject fast when full) at the same offered
    #     load. Of the roughly 1200 jobs offered over the run, how many get
    #     shed, the quick 429s that keep the system alive?
    "shed_count": 500,
}

# ---------------------------------------------------------------------------
# Knobs. The defaults make the producer clearly faster than the consumer, so
# the contrast is unmistakable, and keep the whole run near 12 seconds.
# ---------------------------------------------------------------------------
SERVICE_S = 0.004      # the consumer: about 4 ms of work per job (~250/s)
PRODUCE_S = 0.002      # the producer WANTS to offer a job every 2 ms (~500/s)
RUN_S = 3.0            # how long the producer offers jobs, per part
CAP = 50               # the bounded queue's capacity (Parts 2 and 3)
SAMPLE_S = 0.25        # sample the queue depth this often, to draw the curve
PUT_TIMEOUT = 0.5      # a blocking put gives up after this, so nothing can hang
GET_TIMEOUT = 0.05     # a consumer get wakes this often to check the stop flag
JOIN_TIMEOUT = 10      # safety net: never hang forever joining a thread

_UNSET = object()      # marks a TODO you have not filled in yet


class TODONotDone(Exception):
    """Raised by a blank TODO so the lab can stop cleanly instead of hanging."""
    def __init__(self, n):
        super().__init__(f"TODO {n} is not filled in yet")
        self.n = n


# ---------------------------------------------------------------------------
# The consumer: one worker thread that drains the queue at a fixed rate
# ---------------------------------------------------------------------------

class Consumer(threading.Thread):
    """A single slow worker. It pulls one job off the queue, spends SERVICE_S
    doing the 'work', and counts what it finished. It stops promptly when the
    stop flag is set, and it never blocks forever (get has a timeout), so the
    lab always terminates."""

    def __init__(self, q, stop):
        super().__init__(daemon=True)
        self.q = q
        self.stop = stop
        self.done = 0

    def run(self):
        while not self.stop.is_set():
            try:
                self.q.get(timeout=GET_TIMEOUT)
            except queue.Empty:
                continue
            time.sleep(SERVICE_S)        # the slow part: this is the real work
            self.done += 1


def sample_depth(q, stop, samples, t0):
    """A tiny monitor thread. Every SAMPLE_S it records (seconds, queue depth)
    so we can see the depth climb in Part 1 and hold flat in Parts 2 and 3."""
    while not stop.is_set():
        samples.append((time.monotonic() - t0, q.qsize()))
        time.sleep(SAMPLE_S)


# ---------------------------------------------------------------------------
# The four pieces you fill in. Each is a small, sharp bit of the lesson.
# ---------------------------------------------------------------------------

def enqueue_unbounded(q, item):
    """Part 1's offer: into an UNBOUNDED queue. It never blocks and never
    refuses, it always accepts. That 'yes to everything' is exactly what lets
    the backlog climb without bound."""
    # TODO 1 (solved) ---------------------------------------------------------
    q.put_nowait(item)
    placed = True
    # -------------------------------------------------------------------------
    if placed is _UNSET:
        raise TODONotDone(1)


def littles_law_wait(depth, consume_rate):
    """Day 4's Little's Law, pointed at this work queue. A job that joins the
    back of a queue holding `depth` items, drained at `consume_rate` jobs per
    second, waits depth / consume_rate seconds before it is even picked up. As
    depth climbs in Part 1, so does this wait, with no ceiling."""
    # TODO 2 (solved) ---------------------------------------------------------
    wait_s = depth / consume_rate
    # -------------------------------------------------------------------------
    if wait_s is _UNSET:
        raise TODONotDone(2)
    return wait_s


def enqueue_blocking(q, item, timeout):
    """Part 2's offer: a BLOCKING put into the bounded queue. When the queue is
    full this call parks the producer until the consumer frees a slot. That wait
    IS backpressure: it travels up the pipe and throttles the producer down to
    the consumer's rate. Returns True if placed, False if it timed out."""
    try:
        # TODO 3 (solved) -----------------------------------------------------
        q.put(item, timeout=timeout)
        placed = True
        # ---------------------------------------------------------------------
        if placed is _UNSET:
            raise TODONotDone(3)
        return True
    except queue.Full:
        return False


def enqueue_or_shed(q, item):
    """Part 3's offer: load shedding. Try to place the job without waiting. If
    the queue is full, do NOT block and do NOT grow anything, reject it fast,
    the moral equivalent of an HTTP 429. Returns True if accepted, False if
    shed."""
    try:
        q.put_nowait(item)
        return True
    except queue.Full:
        # TODO 4 (solved) -----------------------------------------------------
        shed = True
        # ---------------------------------------------------------------------
        if shed is _UNSET:
            raise TODONotDone(4)
        return False


# ---------------------------------------------------------------------------
# A small helper to draw the depth-over-time curve
# ---------------------------------------------------------------------------

def show_curve(samples, points=6, width=42):
    """Print a handful of evenly spaced (time, depth) samples as little bars."""
    if not samples:
        return
    peak = max(d for _, d in samples) or 1
    step = max(1, len(samples) // points)
    for i in range(0, len(samples), step):
        t, d = samples[i]
        bar = "#" * int(round(d / peak * width))
        print(f"    t={t:4.1f}s  depth={d:5d}  {bar}")


# ---------------------------------------------------------------------------
# Part 1: the unbounded queue disaster
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: the unbounded queue. Producer at ~2x the consumer, no limit.")
    print("=" * 78)
    q = queue.Queue()                 # maxsize=0 means unbounded
    stop = threading.Event()
    consumer = Consumer(q, stop)
    samples = []
    t0 = time.monotonic()
    sampler = threading.Thread(target=sample_depth, args=(q, stop, samples, t0),
                               daemon=True)
    consumer.start()
    sampler.start()

    produced = 0
    item = 0
    deadline = time.monotonic() + RUN_S
    while time.monotonic() < deadline:
        enqueue_unbounded(q, item)
        produced += 1
        item += 1
        time.sleep(PRODUCE_S)

    stop.set()
    consumer.join(JOIN_TIMEOUT)
    sampler.join(JOIN_TIMEOUT)

    final_depth = q.qsize()
    consumed = consumer.done
    consume_rate = consumed / RUN_S
    wait_s = littles_law_wait(final_depth, consume_rate)

    print(f"  jobs offered (all accepted):       {produced}")
    print(f"  jobs the consumer finished:        {consumed}")
    print(f"  jobs still stuck in the queue:      {final_depth}")
    print("  queue depth over time:")
    show_curve(samples)
    print(f"  consumer drains about {consume_rate:,.0f} jobs/sec, so by Little's Law a")
    print(f"  job joining the back now waits {wait_s:,.1f}s to be picked up, and that")
    print("  wait grows every second the producer keeps running. Nothing errored.")
    print("  Memory and latency just climb until something falls over. This is the")
    print("  slow-motion outage an unbounded queue hides.")
    return produced, consumed, final_depth, wait_s


# ---------------------------------------------------------------------------
# Part 2: the bounded queue and backpressure
# ---------------------------------------------------------------------------

def part2():
    print("\n" + "=" * 78)
    print("Part 2: a bounded queue. put() blocks when full, so backpressure bites.")
    print("=" * 78)
    q = queue.Queue(maxsize=CAP)
    stop = threading.Event()
    consumer = Consumer(q, stop)
    samples = []
    t0 = time.monotonic()
    sampler = threading.Thread(target=sample_depth, args=(q, stop, samples, t0),
                               daemon=True)
    consumer.start()
    sampler.start()

    produced = 0
    item = 0
    deadline = time.monotonic() + RUN_S
    while time.monotonic() < deadline:
        placed = enqueue_blocking(q, item, PUT_TIMEOUT)
        if placed:
            produced += 1
            item += 1
            time.sleep(PRODUCE_S)

    stop.set()
    consumer.join(JOIN_TIMEOUT)
    sampler.join(JOIN_TIMEOUT)

    final_depth = q.qsize()
    consumed = consumer.done
    produce_rate = produced / RUN_S
    consume_rate = consumed / RUN_S
    steady = [d for _, d in samples if d > 0]
    avg_depth = sum(steady) / len(steady) if steady else 0

    print(f"  jobs the producer managed to place: {produced}")
    print(f"  jobs the consumer finished:        {consumed}")
    print(f"  queue depth at the end:             {final_depth}  (cap is {CAP})")
    print(f"  average queue depth while running: {avg_depth:5.1f}")
    print("  queue depth over time:")
    show_curve(samples)
    print(f"  producer rate {produce_rate:,.0f}/s vs consumer rate {consume_rate:,.0f}/s: the blocking")
    print("  put() pinned the fast producer to the consumer's pace. The queue")
    print(f"  filled to its cap of {CAP} and stayed there. Backpressure travelled")
    print("  upstream and the backlog stopped growing. No outage, just a slower")
    print("  producer, which is the whole point.")
    return produced, consumed, final_depth, avg_depth


# ---------------------------------------------------------------------------
# Part 3: load shedding, for when you cannot block the producer
# ---------------------------------------------------------------------------

def part3(unbounded_produced, bounded_produced):
    print("\n" + "=" * 78)
    print("Part 3: load shedding. Full queue? Reject fast (a 429), do not queue.")
    print("=" * 78)
    q = queue.Queue(maxsize=CAP)
    stop = threading.Event()
    consumer = Consumer(q, stop)
    samples = []
    t0 = time.monotonic()
    sampler = threading.Thread(target=sample_depth, args=(q, stop, samples, t0),
                               daemon=True)
    consumer.start()
    sampler.start()

    offered = 0
    accepted = 0
    item = 0
    deadline = time.monotonic() + RUN_S
    while time.monotonic() < deadline:
        ok = enqueue_or_shed(q, item)
        offered += 1
        if ok:
            accepted += 1
        item += 1
        time.sleep(PRODUCE_S)

    stop.set()
    consumer.join(JOIN_TIMEOUT)
    sampler.join(JOIN_TIMEOUT)

    final_depth = q.qsize()
    consumed = consumer.done
    shed = offered - accepted
    throttle_x = unbounded_produced / bounded_produced if bounded_produced else 0

    print(f"  jobs offered:                       {offered}")
    print(f"  jobs accepted (fit in the queue):   {accepted}")
    print(f"  jobs shed fast (the 429s):          {shed}")
    print(f"  queue depth at the end:             {final_depth}  (cap is {CAP})")
    print("  queue depth over time:")
    show_curve(samples)
    print(f"  the consumer still finished {consumed} jobs, same as under backpressure.")
    print("  The ones it could not get to were turned away in microseconds, not")
    print("  parked in memory. Accepted jobs kept a bounded, predictable wait; the")
    print("  rest got an instant honest 'no'. That fast no is what keeps the system")
    print("  standing when the unbounded 'yes' would have buried it.")
    return offered, accepted, shed, throttle_x


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>8,.1f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<30} you = {predicted:>7,.1f}   actual = {actual:>8,.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    produced1, consumed1, depth1, wait1 = part1()
    produced2, consumed2, depth2, avg2 = part2()
    offered3, accepted3, shed3, throttle = part3(produced1, produced2)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 unbounded final depth", PREDICTIONS["unbounded_final_depth"], depth1)
    verdict("P2 bounded final depth", PREDICTIONS["bounded_final_depth"], depth2)
    verdict("P3 backpressure throttle", PREDICTIONS["backpressure_throttle_x"], throttle, "x")
    verdict("P4 shed count", PREDICTIONS["shed_count"], shed3)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Same producer, same slow consumer, three different queues.")
    print(f"  Unbounded:    backlog ran to {depth1} and a new job waited {wait1:,.1f}s, climbing.")
    print(f"  Bounded:      backlog held flat at {depth2} (cap {CAP}); the producer was")
    print(f"                throttled {throttle:.1f}x down to the consumer's rate.")
    print(f"  Load shedding: {shed3} jobs got a fast 429 so the rest kept a bounded wait.")
    print("  An unbounded queue does not absorb overload, it defers the outage and")
    print("  makes it worse. Bound the queue, then choose: block the producer")
    print("  (backpressure) or reject the excess (shedding). Day 4's rule holds:")
    print("  run below 100 percent and keep the queue bounded.")
    print("\nNow write labs/day-27-backpressure/RESULTS.md.\n")


if __name__ == "__main__":
    main()
