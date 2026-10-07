"""
Day 6 lab: run three real servers behind a real load balancer, then kill one
while it is serving traffic and watch what happens.

Run it:      python3 load_balancer_lab.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
The lab runs a self-check first and tells you exactly which TODO is missing, so
you can never get stuck watching it hang. If you get stuck, solution.py in this
folder is the full working version.

Everything here is real. Real TCP sockets, real HTTP, real threads, a real
reverse proxy. Nothing is simulated. When we "crash" a backend we actually shut
its socket, so the balancer gets a real connection error, the same one it would
get if a server fell over in production.

Standard library only. Takes roughly 30 seconds, most of it spent waiting in
real time while load runs, on purpose.

Three things we measure:
  Part 1  a healthy balancer spreading load across three backends
  Part 2  kill one backend mid-traffic, with and without health checks and retry
  Part 3  round robin vs least-connections when one backend is slow
"""

import http.client
import http.server
import socketserver
import statistics
import sys
import threading
import time

WORK_MS = 10          # normal backend work per request
SLOW_MS = 60          # the one slow backend in part 3
N_CLIENTS = 20        # concurrent load generator threads
HEALTH_INTERVAL = 0.2  # how often the balancer probes /health

PREDICTIONS = {
    # P1: three backends, round robin, no health checks. You kill one backend.
    #     What percentage of requests fail AFTER the kill? (the balancer keeps
    #     routing to the dead one because nothing told it to stop)
    "fail_pct_no_health": None,

    # P2: now with active health checks every 200 ms. After the kill, for how
    #     many milliseconds do errors keep happening before they stop?
    "error_window_ms_with_health": None,

    # P3: health checks plus retry-on-failure. Roughly how many user-visible
    #     errors in total? (an order of magnitude is fine)
    "user_errors_with_retry": None,

    # P4: one backend is 6x slower than the others. How many times more requests
    #     does least-connections complete than round robin? (a ratio)
    "leastconn_throughput_ratio": None,
}


def _silence(*a, **k):
    pass


# ---------------------------------------------------------------------------
# A backend: a real HTTP server in its own thread
# ---------------------------------------------------------------------------

class Backend:
    def __init__(self, name, work_ms):
        self.name = name
        self.work_ms = work_ms
        self.healthy = True
        backend = self

        class Handler(http.server.BaseHTTPRequestHandler):
            log_message = _silence

            def do_GET(self):
                if self.path == "/health":
                    code = 200 if backend.healthy else 503
                    self.send_response(code)
                    self.end_headers()
                    self.wfile.write(b"ok")
                    return
                time.sleep(backend.work_ms / 1000)   # the "work"
                self.send_response(200)
                self.end_headers()
                self.wfile.write(backend.name.encode())

        self.srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        self.srv.daemon_threads = True
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def crash(self):
        """A real crash: close the socket. New connections get refused."""
        try:
            self.srv.shutdown()
            self.srv.server_close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# The two load balancing decisions (TODO 1 and TODO 2 in the starter file)
# ---------------------------------------------------------------------------

def pick_round_robin(healthy, state):
    """Next backend in a rotation. state["rr"] remembers where we were."""
    # TODO 1 ------------------------------------------------------------------
    # Return the next backend in a rotation. state["rr"] is where the last pick
    # landed. Move it on by one, wrapping around the list, and return that one:
    #     state["rr"] = (state["rr"] + 1) % len(healthy)
    #     return healthy[state["rr"]]
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def pick_least_conn(healthy, inflight):
    """The backend with the fewest requests in flight right now."""
    # TODO 2 ------------------------------------------------------------------
    # Return the backend holding the fewest requests in flight right now.
    # inflight maps a backend name to its current count:
    #     return min(healthy, key=lambda b: inflight[b.name])
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def probe(backend):
    """Health check: True if GET /health returns 200, False on anything else."""
    # TODO 3 ------------------------------------------------------------------
    # Probe the backend's /health endpoint. Return True only if it answers 200,
    # and False on a non-200 or any connection error (a crashed backend refuses
    # the connection, which raises):
    #     try:
    #         c = http.client.HTTPConnection("127.0.0.1", backend.port, timeout=0.2)
    #         c.request("GET", "/health")
    #         r = c.getresponse()
    #         ok = r.status == 200
    #         r.read(); c.close()
    #         return ok
    #     except Exception:
    #         return False
    # -------------------------------------------------------------------------
    return None  # <-- replace this


# ---------------------------------------------------------------------------
# The balancer: a real reverse proxy in front of the backends
# ---------------------------------------------------------------------------

class Balancer:
    def __init__(self, backends, algo="rr", health=True, retry=False):
        self.backends = backends
        self.algo = algo
        self.retry = retry
        self.healthy = list(backends)
        self.inflight = {b.name: 0 for b in backends}
        self.served = {b.name: 0 for b in backends}
        self.lock = threading.Lock()
        self.state = {"rr": -1}
        self.stop = threading.Event()
        bal = self

        if health:
            threading.Thread(target=self._health_loop, daemon=True).start()

        class Handler(http.server.BaseHTTPRequestHandler):
            log_message = _silence

            def do_GET(self):
                max_tries = 2 if bal.retry else 1
                for _ in range(max_tries):
                    b = bal.pick()
                    if b is None:
                        break
                    with bal.lock:
                        bal.inflight[b.name] += 1
                    try:
                        c = http.client.HTTPConnection("127.0.0.1", b.port, timeout=1.0)
                        c.request("GET", "/")
                        r = c.getresponse()
                        r.read()
                        c.close()
                        with bal.lock:
                            bal.inflight[b.name] -= 1
                            bal.served[b.name] += 1
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b.name.encode())
                        return
                    except Exception:
                        with bal.lock:
                            bal.inflight[b.name] -= 1
                        continue
                self.send_response(502)
                self.end_headers()
                self.wfile.write(b"no healthy backend")

        self.srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        self.srv.daemon_threads = True
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def pick(self):
        with self.lock:
            healthy = list(self.healthy)
        if not healthy:
            return None
        if self.algo == "leastconn":
            return pick_least_conn(healthy, self.inflight)
        return pick_round_robin(healthy, self.state)

    def _health_loop(self):
        while not self.stop.is_set():
            self._health_sweep()
            time.sleep(HEALTH_INTERVAL)

    def _health_sweep(self):
        """One pass: probe every backend and update the healthy list."""
        for b in self.backends:
            ok = probe(b)
            with self.lock:
                # TODO 4 ----------------------------------------------------------
                # Update the healthy list from the probe result. Add the backend
                # back if it is ok and missing, remove it if it is not ok and
                # present. This one line is what makes the balancer self-heal:
                #     if ok and b not in self.healthy:
                #         self.healthy.append(b)
                #     if not ok and b in self.healthy:
                #         self.healthy.remove(b)
                # -----------------------------------------------------------------
                pass  # <-- replace this

    def shutdown(self):
        self.stop.set()
        self.crash_all()
        try:
            self.srv.shutdown()
            self.srv.server_close()
        except Exception:
            pass

    def crash_all(self):
        for b in self.backends:
            b.crash()


# ---------------------------------------------------------------------------
# The load generator: real concurrent clients hitting the balancer
# ---------------------------------------------------------------------------

def generate_load(bal, seconds, kill_at=None, kill_backend=None):
    """Return a list of (timestamp, ok, latency_ms) and the kill time."""
    events = []
    ev_lock = threading.Lock()
    stop = threading.Event()
    kill_time = [None]

    def worker():
        while not stop.is_set():
            t = time.perf_counter()
            try:
                c = http.client.HTTPConnection("127.0.0.1", bal.port, timeout=2.0)
                c.request("GET", "/")
                r = c.getresponse()
                r.read()
                c.close()
                now = time.perf_counter()
                ok = r.status == 200
                with ev_lock:
                    events.append((now, ok, (now - t) * 1000 if ok else None))
            except Exception:
                with ev_lock:
                    events.append((time.perf_counter(), False, None))

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(N_CLIENTS)]
    for t in threads:
        t.start()

    if kill_at and kill_backend:
        time.sleep(kill_at)
        kill_time[0] = time.perf_counter()
        kill_backend.crash()
        time.sleep(seconds - kill_at)
    else:
        time.sleep(seconds)

    stop.set()
    for t in threads:
        t.join(timeout=3)
    return events, kill_time[0]


# ---------------------------------------------------------------------------
# Part 1: a healthy balancer spreading load
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: three healthy backends, round robin. Who gets the work?")
    print("=" * 78)
    backends = [Backend(f"backend-{i}", WORK_MS) for i in range(3)]
    bal = Balancer(backends, algo="rr", health=True)
    time.sleep(HEALTH_INTERVAL * 2)
    events, _ = generate_load(bal, 2.0)
    oks = sum(1 for _, ok, _ in events if ok)
    for b in backends:
        share = bal.served[b.name] / oks * 100 if oks else 0
        print(f"  {b.name}: {bal.served[b.name]:>5} requests  ({share:>4.1f}%)")
    print(f"  total served: {oks} in 2 s. The balancer spread them evenly, which")
    print("  is the whole point: one address in front, many servers behind.")
    bal.shutdown()


# ---------------------------------------------------------------------------
# Part 2: kill a backend mid-traffic
# ---------------------------------------------------------------------------

def one_kill_run(health, retry):
    backends = [Backend(f"backend-{i}", WORK_MS) for i in range(3)]
    bal = Balancer(backends, algo="rr", health=health, retry=retry)
    time.sleep(HEALTH_INTERVAL * 2)
    events, kill_time = generate_load(bal, 4.0, kill_at=1.5, kill_backend=backends[0])
    bal.shutdown()

    after = [(t, ok) for t, ok, _ in events if t >= kill_time]
    fails_after = [t for t, ok in after if not ok]
    total_after = len(after)
    fail_pct = len(fails_after) / total_after * 100 if total_after else 0
    window_ms = (max(fails_after) - kill_time) * 1000 if fails_after else 0
    return len(fails_after), fail_pct, window_ms


def part2():
    print("\n" + "=" * 78)
    print("Part 2: kill one of three backends 1.5 s in. What do users feel?")
    print("=" * 78)
    print(f"  {'config':<34} {'errors':>8} {'fail% after':>12} {'error window':>14}")
    results = {}
    for label, health, retry in [
        ("no health check, no retry", False, False),
        ("health check every 200 ms", True, False),
        ("health check + retry", True, True),
    ]:
        errs, pct, window = one_kill_run(health, retry)
        results[label] = (errs, pct, window)
        wtxt = "never stopped" if (not health and errs) else f"{window:>6.0f} ms"
        print(f"  {label:<34} {errs:>8} {pct:>11.1f}% {wtxt:>14}")
    print("\n  No health check: the balancer never learns the backend is dead, so")
    print("  it keeps sending one in three requests into a wall, forever.")
    print("  Health check: errors stop about one check-interval after the crash.")
    print("  Retry: a failed request quietly tries another backend, so the user")
    print("  barely sees anything at all. Same crash, three very different days.")
    return results


# ---------------------------------------------------------------------------
# Part 3: round robin vs least-connections with a slow backend
# ---------------------------------------------------------------------------

def one_algo_run(algo):
    backends = [Backend("fast-1", WORK_MS), Backend("fast-2", WORK_MS),
                Backend("slow", SLOW_MS)]
    bal = Balancer(backends, algo=algo, health=True)
    time.sleep(HEALTH_INTERVAL * 2)
    events, _ = generate_load(bal, 3.0)
    bal.shutdown()
    oks = sum(1 for _, ok, _ in events if ok)
    lats = [lat for _, ok, lat in events if ok and lat is not None]
    p99 = statistics.quantiles(lats, n=100)[-1] if len(lats) > 2 else 0
    to_slow = bal.served["slow"]
    return oks, p99, to_slow


def part3():
    print("\n" + "=" * 78)
    print("Part 3: one backend is 6x slower. Round robin vs least-connections.")
    print("=" * 78)
    print(f"  {'algorithm':<18} {'completed':>10} {'p99 ms':>8} {'sent to slow':>13}")
    out = {}
    for algo, label in [("rr", "round robin"), ("leastconn", "least-connections")]:
        oks, p99, to_slow = one_algo_run(algo)
        out[algo] = oks
        print(f"  {label:<18} {oks:>10} {p99:>8.0f} {to_slow:>13}")
    print("\n  Round robin sends a third of all traffic to the slow backend no")
    print("  matter what, and those requests pile up behind each other. Least-")
    print("  connections notices the slow one is holding more requests and steers")
    print("  around it, so the whole system finishes far more work. This is the")
    print("  Day 4 lesson again: don't shove work at the server that can't keep up.")
    return out


# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<36} actual = {actual:>8,.1f} {unit}  (no prediction)")
        return
    if actual == 0:
        note = "     better than predicted"
    else:
        ratio = actual / predicted if predicted else float("inf")
        if 0.5 <= ratio <= 2:
            note = "     close enough"
        elif ratio > 1:
            note = f"{ratio:>6.1f}x  too LOW"
        else:
            note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<36} you = {predicted:>7,.1f}   actual = {actual:>8,.1f} {unit}  {note}")


def self_test():
    """Check the four TODOs are implemented before we run any load. Returns a
    list of human-readable complaints, empty if everything is wired up."""
    missing = []
    a = Backend("self-a", WORK_MS)
    b = Backend("self-b", WORK_MS)
    bal = Balancer([a, b], algo="rr", health=False)
    try:
        state = {"rr": -1}
        if pick_round_robin([a, b], state) is None:
            missing.append("TODO 1: pick_round_robin returns None")
        if pick_least_conn([a, b], {"self-a": 0, "self-b": 1}) is None:
            missing.append("TODO 2: pick_least_conn returns None")
        if probe(a) is not True:
            missing.append("TODO 3: probe does not return True for a healthy backend")
        b.crash()
        bal._health_sweep()
        if b in bal.healthy:
            missing.append("TODO 4: the health sweep did not remove a crashed backend")
    finally:
        bal.shutdown()
    return missing


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    gaps = self_test()
    if gaps:
        print("\n  !! Some TODOs are not filled in yet:")
        for g in gaps:
            print(f"       - {g}")
        print("     Fill them in and run again. See solution.py if you get stuck.\n")
        sys.exit(1)

    part1()
    p2 = part2()
    p3 = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 fail% after kill, no health", PREDICTIONS["fail_pct_no_health"],
            p2["no health check, no retry"][1], "%")
    verdict("P2 error window with health", PREDICTIONS["error_window_ms_with_health"],
            p2["health check every 200 ms"][2], "ms")
    verdict("P3 user errors with retry", PREDICTIONS["user_errors_with_retry"],
            p2["health check + retry"][0], "")
    verdict("P4 leastconn / rr throughput", PREDICTIONS["leastconn_throughput_ratio"],
            p3["leastconn"] / p3["rr"] if p3["rr"] else 0, "x")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    no_h = p2["no health check, no retry"][0]
    with_r = p2["health check + retry"][0]
    print(f"  Same backend crash, same traffic. Without health checks and retry it")
    print(f"  caused {no_h} failed requests. With them, {with_r}. The crash did not change.")
    print("  What changed is whether the balancer noticed and whether it tried")
    print("  again. That is the whole job of the thing in front of your servers.")
    print("\nNow write labs/day-06-load-balancer/RESULTS.md.\n")


if __name__ == "__main__":
    main()
