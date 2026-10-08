"""
Day 22 lab: sync vs async, and why queues exist.

This is the full working solution. The starter file is async_queue.py.
Run it:      python3 solution.py

Standard library only (queue, threading, sqlite3, time). Runs in well under a
minute and cleans up every file it makes.

The story, measured on your own machine:
  - Synchronous. The caller does the slow job itself, inline, and only returns
    when the whole job is finished. So the caller's latency IS the whole job,
    about 50 ms here. Part 1 measures it.
  - Asynchronous. The caller drops the job into a queue and returns at once. A
    background worker thread pulls jobs off the queue and does the slow work.
    Now the caller's latency is just the enqueue, a few microseconds, while the
    work still happens, off to the side. Part 2 measures both.
  - The queue as a buffer. Fire a burst of jobs faster than the worker can
    handle them. With the async queue the callers all return fast and the queue
    absorbs the burst, draining at worker speed. Part 3 samples the depth rising
    and then falling. Then, with a BOUNDED queue, a sustainedly fast producer is
    forced to wait: put() blocks when the queue is full, which is backpressure.
    Part 4 shows that first taste (the full treatment is Day 27).

This is a Swiggy order handed to a queue. You tap "Pay" and the screen says
"Order placed" at once. Charging the card, pinging the restaurant, finding a
rider, sending the SMS: all of that is dropped on a queue and done by workers
later. You did not wait for it, but it still happened.
"""

import os
import queue
import sqlite3
import sys
import threading
import time

PREDICTIONS = {
    # P1: the SYNCHRONOUS caller does the slow job inline. Its latency is the
    #     whole job. How many milliseconds is one call? (The job sleeps 50 ms.)
    "sync_caller_latency_ms": 50,

    # P2: the ASYNCHRONOUS caller just drops the job on the queue and returns.
    #     Its latency is only the enqueue. Bet an UPPER BOUND in milliseconds:
    #     you are saying "the enqueue stays under this". 1.0 ms is a safe bet.
    "async_caller_latency_ms": 1.0,

    # P3: fire a burst of 40 jobs into the async queue, all at once, while one
    #     worker drains at 50 ms per job. How deep does the queue get at its peak
    #     before it starts draining?
    "burst_peak_depth": 40,

    # P4: now a BOUNDED queue of maxsize 5, with a fast producer and the same
    #     slow worker. Of the 40 put() calls, how many have to BLOCK and wait
    #     because the queue was full? (That blocking is backpressure.)
    "backpressure_blocked_puts": 35,
}

# ---------------------------------------------------------------------------
# Knobs. The defaults make the contrast sharp and the numbers repeatable.
# ---------------------------------------------------------------------------
WORK_MS = 50                 # the slow job: 50 ms of "real work" per job
N_CALLS = 20                 # how many jobs Parts 1 and 2 push through
N_BURST = 40                 # the size of the burst in Part 3
BOUND = 5                    # the bounded queue's maxsize in Part 4
N_BACKPRESSURE = 40          # how many jobs the fast producer fires in Part 4
DRAIN_SAMPLE_MS = 150        # how often the sampler reads the queue depth
BLOCK_THRESHOLD_MS = 1.0     # a put slower than this must have waited on a full queue
JOIN_TIMEOUT = 20            # safety: never hang joining a worker

DB_SYNC = "orders_sync.db"
DB_ASYNC = "orders_async.db"
DB_BURST = "orders_burst.db"
DB_BP = "orders_backpressure.db"

SENTINEL = object()          # a worker that pulls this knows there are no more jobs


class TODONotDone(Exception):
    """Raised by a blank TODO in the starter so the lab can stop cleanly."""
    def __init__(self, n):
        super().__init__(f"TODO {n} is not filled in yet")
        self.n = n


# ---------------------------------------------------------------------------
# A tiny durable store, so we can prove the work actually happened
# ---------------------------------------------------------------------------

def wipe(*paths):
    for path in paths:
        for suffix in ("", "-wal", "-shm", "-journal"):
            if os.path.exists(path + suffix):
                os.unlink(path + suffix)


def connect(path):
    """Open a SQLite connection with fsync off, so a commit does not add disk
    latency to our timings. We are measuring sync vs async, not the disk."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA journal_mode = MEMORY")
    return conn


def init_db(path):
    """Create a fresh orders table. The worker (or the sync caller) will open its
    own connection to this same file and insert into it."""
    wipe(path)
    conn = connect(path)
    conn.execute("CREATE TABLE orders (id INTEGER)")
    conn.commit()
    conn.close()


def row_count(path):
    conn = connect(path)
    n = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    return n


def do_slow_job(conn, job):
    """The real work behind one request: 50 ms of effort, then persist the
    result. In a real system this is charge the card, render the page, call the
    shipping API. Here it is a sleep plus one durable row, so afterwards we can
    count the rows and prove every job was done. Returns the job id."""
    time.sleep(WORK_MS / 1000)
    conn.execute("INSERT INTO orders (id) VALUES (?)", (job,))
    conn.commit()
    return job


# ---------------------------------------------------------------------------
# The caller, the enqueue, the worker's pull, the bounded queue.
# These four tiny functions are the heart of the lab (the four TODOs).
# ---------------------------------------------------------------------------

def sync_caller(conn, job):
    """The synchronous caller. It does the slow job itself and only returns when
    the whole thing is finished, so its latency is the entire job."""
    done = do_slow_job(conn, job)
    return done


def async_enqueue(q, job):
    """The asynchronous caller. It hands the job to the queue and returns at
    once. It does NOT wait for the work; a worker will pick the job up later."""
    q.put(job)


def worker_get(q):
    """The worker pulls the next job off the queue. This blocks until a job is
    available, which is exactly what you want: an idle worker sleeps for free."""
    job = q.get()
    return job


def make_bounded_queue():
    """A queue with a hard cap on how many jobs can wait in it. The cap is what
    gives you backpressure: once it is full, a producer's put() has to wait."""
    q = queue.Queue(maxsize=BOUND)
    return q


# ---------------------------------------------------------------------------
# The worker loop: pull jobs, do them, stop on the sentinel. Always terminates.
# ---------------------------------------------------------------------------

def run_worker(q, db_path, stats):
    """One consumer thread. It opens its own connection to the store, pulls jobs
    until it sees the sentinel, and does each one. stats records progress so the
    main thread can read it after the worker has joined."""
    conn = connect(db_path)
    try:
        while True:
            job = worker_get(q)
            if job is SENTINEL:
                break
            do_slow_job(conn, job)
            stats["done"] += 1
            stats["last_done"] = time.perf_counter()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Part 1: synchronous. The caller does the work and waits.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: synchronous. The caller does the slow job itself and waits.")
    print("=" * 78)
    init_db(DB_SYNC)
    conn = connect(DB_SYNC)

    latencies = []
    start = time.perf_counter()
    for job in range(N_CALLS):
        t0 = time.perf_counter()
        sync_caller(conn, job)
        latencies.append((time.perf_counter() - t0) * 1000)
    wall_ms = (time.perf_counter() - start) * 1000
    conn.close()

    avg = sum(latencies) / len(latencies)
    print(f"  jobs run:                          {N_CALLS}")
    print(f"  average caller latency per job:  {avg:8.2f} ms")
    print(f"  wall-clock time for all {N_CALLS} jobs:  {wall_ms:8.1f} ms")
    print(f"  orders persisted:                  {row_count(DB_SYNC)}")
    print("  The caller runs the 50 ms job on its own thread, so it is stuck for")
    print("  the whole job every single time. Latency per call IS the work, and")
    print("  the jobs run one after another, so the total is just N times the job.")
    wipe(DB_SYNC)
    return avg


# ---------------------------------------------------------------------------
# Part 2: asynchronous. The caller drops the job and walks away.
# ---------------------------------------------------------------------------

def part2():
    print("\n" + "=" * 78)
    print("Part 2: asynchronous. The caller drops the job on a queue and returns.")
    print("=" * 78)
    init_db(DB_ASYNC)
    q = queue.Queue()
    stats = {"done": 0, "last_done": None}
    worker = threading.Thread(target=run_worker, args=(q, DB_ASYNC, stats))
    worker.start()

    enqueue_latencies = []
    start = time.perf_counter()
    for job in range(N_CALLS):
        t0 = time.perf_counter()
        async_enqueue(q, job)
        enqueue_latencies.append((time.perf_counter() - t0) * 1000)
    caller_total_ms = (time.perf_counter() - start) * 1000

    q.put(SENTINEL)
    worker.join(timeout=JOIN_TIMEOUT)
    end_to_end_ms = (stats["last_done"] - start) * 1000 if stats["last_done"] else 0.0

    avg_enqueue = sum(enqueue_latencies) / len(enqueue_latencies)
    print(f"  jobs enqueued:                     {N_CALLS}")
    print(f"  average caller latency (enqueue):{avg_enqueue:8.4f} ms")
    print(f"  time for the caller to fire all {N_CALLS}:{caller_total_ms:8.3f} ms")
    print(f"  end-to-end (last job finishes):  {end_to_end_ms:8.1f} ms")
    print(f"  orders persisted:                  {row_count(DB_ASYNC)}")
    print("  The caller touched the slow work zero times. It put each job on the")
    print("  queue in a few microseconds and was free. The 50 ms per job still")
    print("  happened, on the worker's thread, and every order still landed in")
    print("  the store. The work did not vanish; the caller just stopped waiting.")
    wipe(DB_ASYNC)
    return avg_enqueue


# ---------------------------------------------------------------------------
# Part 3: the queue as a buffer. A burst rises, then drains.
# ---------------------------------------------------------------------------

def part3():
    print("\n" + "=" * 78)
    print("Part 3: the queue as a buffer. A burst lands, the queue absorbs it.")
    print("=" * 78)
    init_db(DB_BURST)
    q = queue.Queue()
    stats = {"done": 0, "last_done": None}
    worker = threading.Thread(target=run_worker, args=(q, DB_BURST, stats))
    worker.start()

    # Fire the whole burst as fast as we can, recording the queue depth right
    # after each put. That is the RISE: the depth climbs toward N as the jobs
    # pile up faster than the one worker can take them.
    rise = []
    t0 = time.perf_counter()
    for job in range(N_BURST):
        async_enqueue(q, job)
        rise.append(q.qsize())
    burst_ms = (time.perf_counter() - t0) * 1000
    peak = max(rise)

    # Now sample the depth while the worker drains the backlog. That is the FALL.
    series = []
    stop = threading.Event()

    def sampler():
        while not stop.is_set():
            series.append(((time.perf_counter() - t0) * 1000, q.qsize()))
            time.sleep(DRAIN_SAMPLE_MS / 1000)

    sampler_t = threading.Thread(target=sampler)
    sampler_t.start()

    q.put(SENTINEL)
    worker.join(timeout=JOIN_TIMEOUT)
    stop.set()
    sampler_t.join(timeout=5)

    drain_ms = (stats["last_done"] - t0) * 1000 if stats["last_done"] else 0.0

    print(f"  burst size:                        {N_BURST} jobs")
    print(f"  time to fire the whole burst:    {burst_ms:8.3f} ms  (callers all freed)")
    print(f"  peak queue depth:                  {peak}")
    print(f"  time to drain the backlog:       {drain_ms:8.1f} ms  (~{N_BURST} x {WORK_MS} ms)")
    print(f"  orders persisted:                  {row_count(DB_BURST)}")
    print("  queue depth over time (rose to the peak in microseconds, then fell")
    print("  as the worker chewed through it at one job per 50 ms):")
    print(f"    t=0.00s  depth={peak:<3d} {'#' * peak}   <- burst just landed")
    for ms, depth in series:
        if depth <= 0 or ms < DRAIN_SAMPLE_MS / 2:
            continue   # skip the near-zero sample; the line above already shows the peak
        print(f"    t={ms / 1000:4.2f}s  depth={depth:<3d} {'#' * depth}")
    print(f"    t={drain_ms / 1000:4.2f}s  depth=0   (drained)")
    print("  The callers did not queue up behind the slow worker. They dropped")
    print("  their jobs and left, and the queue held the backlog for the worker.")
    wipe(DB_BURST)
    return peak


# ---------------------------------------------------------------------------
# Part 4: the first taste of backpressure. A bounded queue pushes back.
# ---------------------------------------------------------------------------

def part4():
    print("\n" + "=" * 78)
    print("Part 4: backpressure. A bounded queue makes a fast producer wait.")
    print("=" * 78)
    init_db(DB_BP)
    q = make_bounded_queue()
    stats = {"done": 0, "last_done": None}
    worker = threading.Thread(target=run_worker, args=(q, DB_BP, stats))
    worker.start()

    # The producer wants to fire all N jobs instantly, like in Part 3. But the
    # queue only holds BOUND of them. Once it is full, put() blocks until the
    # worker takes one and frees a slot, so each of these puts is timed.
    put_latencies = []
    start = time.perf_counter()
    for job in range(N_BACKPRESSURE):
        t0 = time.perf_counter()
        async_enqueue(q, job)
        put_latencies.append((time.perf_counter() - t0) * 1000)
    producer_ms = (time.perf_counter() - start) * 1000

    q.put(SENTINEL)
    worker.join(timeout=JOIN_TIMEOUT)

    blocked = sum(1 for ms in put_latencies if ms > BLOCK_THRESHOLD_MS)
    free = len(put_latencies) - blocked
    slowest = max(put_latencies)
    print(f"  bounded queue maxsize:             {BOUND}")
    print(f"  jobs the producer fired:           {N_BACKPRESSURE}")
    print(f"  puts that returned instantly:      {free}  (the queue had room)")
    print(f"  puts that BLOCKED (backpressure):  {blocked}  (the queue was full)")
    print(f"  slowest single put:              {slowest:8.1f} ms  (~one job of work)")
    print(f"  total time the producer took:    {producer_ms:8.1f} ms")
    print(f"  orders persisted:                  {row_count(DB_BP)}")
    print("  In Part 3 the unbounded queue let the producer dump everything and")
    print("  leave. Here the bound pushes back: once BOUND jobs are waiting, the")
    print("  producer cannot run ahead of the worker, so put() blocks and the")
    print("  producer moves at the worker's pace. That is backpressure, the")
    print("  queue's way of saying slow down. Full treatment on Day 27.")
    wipe(DB_BP)
    return blocked


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit="", mode="ratio", decimals=1):
    afmt = f"{actual:>10,.{decimals}f}"
    if predicted is None:
        print(f"  {name:<32} actual = {afmt} {unit}  (no prediction)")
        return
    pfmt = f"{predicted:>8,.{decimals}f}"
    if mode == "ceiling":
        note = "     close enough" if actual <= predicted else "   slower than your bet"
    else:
        ratio = actual / predicted if predicted else float("inf")
        if 0.7 <= ratio <= 1.4:
            note = "     close enough"
        elif ratio > 1:
            note = f"{ratio:>6.1f}x  too LOW"
        else:
            note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<32} you = {pfmt}   actual = {afmt} {unit}  {note}")


def self_test():
    """Exercise each TODO once, single threaded and instant, before we launch a
    single worker. A blank TODO raises TODONotDone, which we turn into a clean
    'fill in TODO N' message instead of a crash or a hang."""
    missing = set()

    # TODO 1: the synchronous caller runs the job inline.
    try:
        init_db(DB_SYNC)
        c = connect(DB_SYNC)
        sync_caller(c, -1)
        c.close()
    except TODONotDone as e:
        missing.add(e.n)
    finally:
        wipe(DB_SYNC)

    # TODO 2: the async enqueue puts the job on the queue.
    try:
        async_enqueue(queue.Queue(), -1)
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 3: the worker pulls a job (we pre-load one so it never blocks).
    try:
        probe = queue.Queue()
        probe.put(SENTINEL)
        worker_get(probe)
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 4: the bounded queue.
    try:
        make_bounded_queue()
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

    try:
        sync_latency = part1()
        async_latency = part2()
        peak = part3()
        blocked = part4()

        print("\n" + "=" * 78)
        print("Scoreboard")
        print("=" * 78)
        verdict("P1 sync caller latency", PREDICTIONS["sync_caller_latency_ms"],
                sync_latency, "ms", decimals=1)
        verdict("P2 async caller latency (<= bet)", PREDICTIONS["async_caller_latency_ms"],
                async_latency, "ms", mode="ceiling", decimals=4)
        verdict("P3 burst peak depth", PREDICTIONS["burst_peak_depth"],
                peak, "", decimals=0)
        verdict("P4 backpressure blocked puts", PREDICTIONS["backpressure_blocked_puts"],
                blocked, "", decimals=0)

        speedup = sync_latency / async_latency if async_latency else float("inf")
        print("\n" + "=" * 78)
        print("The number to carry")
        print("=" * 78)
        print(f"  Synchronous, the caller waited the whole job: {sync_latency:.1f} ms per call.")
        print(f"  Asynchronous, the caller just enqueued:       {async_latency:.4f} ms per call.")
        print(f"  Same work, same machine. The caller got about {speedup:,.0f}x faster by")
        print(f"  handing the job to a queue and walking away. The work did not get")
        print(f"  cheaper, it moved off the caller's thread, and the queue held the")
        print(f"  backlog so a burst did not make every caller wait. Bound that queue")
        print(f"  and it pushes back: {blocked} of {N_BACKPRESSURE} puts had to wait. That is backpressure.")
        print("\nNow write labs/day-22-queues/RESULTS.md.\n")
    finally:
        wipe(DB_SYNC, DB_ASYNC, DB_BURST, DB_BP)


if __name__ == "__main__":
    main()
