#!/usr/bin/env python3
"""
Day 57 load generator: point it at a running HTTP service and push until
it breaks.

Pure standard library. It spins up N worker threads, each firing requests
as fast as it can for a fixed time, times every single request, and then
prints throughput, error rate, and the latency percentiles that actually
matter (p50, p95, p99). Run it at rising worker counts and watch for the
knee: the point where adding load stops buying you throughput and only
buys you latency. That knee is your bottleneck.

Example, against the Day 56 reference service:

    # terminal 1
    cd ../day-56-capstone-build && python3 app.py

    # terminal 2
    python3 loadgen.py --url http://127.0.0.1:8080 --stages 1,2,4,8,16 --duration 4 --write-ratio 0.5

--write-ratio is the fraction of requests that are writes (POST /shorten).
The rest are reads (GET /u/<code>). Turn it up to hammer the write path,
down to hammer the read path, and watch which one has the knee.

Predict before you run: at how many workers does p99 cross 100ms? Write it
down. The gap between your guess and the graph is the lesson, same as every
other day.
"""

import argparse
import http.client
import json
import random
import threading
import time
from urllib.parse import urlparse


class Worker(threading.Thread):
    def __init__(self, host, port, deadline, write_ratio, known_codes):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.deadline = deadline
        self.write_ratio = write_ratio
        self.known_codes = known_codes  # shared list of codes we can read back
        self.latencies = []             # seconds, one per request
        self.ok = 0
        self.errors = 0

    def run(self):
        conn = http.client.HTTPConnection(self.host, self.port, timeout=10)
        while time.time() < self.deadline:
            is_write = random.random() < self.write_ratio or not self.known_codes
            t0 = time.perf_counter()
            try:
                if is_write:
                    body = json.dumps({"url": "https://example.com/" + str(random.random())})
                    conn.request("POST", "/shorten", body=body)
                    resp = conn.getresponse()
                    data = resp.read()
                    if resp.status == 200:
                        code = json.loads(data).get("code")
                        if code and len(self.known_codes) < 5000:
                            self.known_codes.append(code)
                else:
                    code = random.choice(self.known_codes)
                    conn.request("GET", "/u/" + code)
                    resp = conn.getresponse()
                    resp.read()
                dt = time.perf_counter() - t0
                self.latencies.append(dt)
                # a redirect (302) and an OK (200) both count as success
                if 200 <= resp.status < 400:
                    self.ok += 1
                else:
                    self.errors += 1
            except Exception:
                self.errors += 1
                # a broken connection has to be rebuilt before the next try
                try:
                    conn.close()
                except Exception:
                    pass
                conn = http.client.HTTPConnection(self.host, self.port, timeout=10)
        conn.close()


def percentile(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def run_stage(host, port, workers, duration, write_ratio, known_codes):
    deadline = time.time() + duration
    threads = [Worker(host, port, deadline, write_ratio, known_codes) for _ in range(workers)]
    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall = time.time() - t0

    lat = sorted(l for t in threads for l in t.latencies)
    ok = sum(t.ok for t in threads)
    errors = sum(t.errors for t in threads)
    total = ok + errors
    return {
        "workers": workers,
        "requests": total,
        "throughput": round(ok / wall, 1) if wall else 0.0,
        "error_rate": round(errors / total, 4) if total else 0.0,
        "p50_ms": round(percentile(lat, 0.50) * 1000, 1),
        "p95_ms": round(percentile(lat, 0.95) * 1000, 1),
        "p99_ms": round(percentile(lat, 0.99) * 1000, 1),
    }


def main():
    ap = argparse.ArgumentParser(description="A tiny concurrent HTTP load generator.")
    ap.add_argument("--url", default="http://127.0.0.1:8080", help="base URL of the service")
    ap.add_argument("--stages", default="1,2,4,8,16", help="comma-separated worker counts to run in turn")
    ap.add_argument("--duration", type=float, default=4.0, help="seconds per stage")
    ap.add_argument("--write-ratio", type=float, default=0.5, help="fraction of requests that are writes (0..1)")
    args = ap.parse_args()

    parsed = urlparse(args.url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    stages = [int(s) for s in args.stages.split(",") if s.strip()]

    # Seed a few codes so the very first reads have something to resolve.
    known_codes = []
    seed = Worker(host, port, time.time() + 1.0, 1.0, known_codes)
    seed.start()
    seed.join()
    if not known_codes:
        print("warning: could not seed any codes. Is the service running at", args.url, "?")

    print(f"target {args.url}  write-ratio {args.write_ratio}  {args.duration}s per stage\n")
    header = f"{'workers':>8} {'req':>8} {'thru/s':>9} {'errors':>8} {'p50 ms':>8} {'p95 ms':>8} {'p99 ms':>8}"
    print(header)
    print("-" * len(header))
    results = []
    for w in stages:
        r = run_stage(host, port, w, args.duration, args.write_ratio, known_codes)
        results.append(r)
        print(f"{r['workers']:>8} {r['requests']:>8} {r['throughput']:>9} "
              f"{r['error_rate']*100:>7.2f}% {r['p50_ms']:>8} {r['p95_ms']:>8} {r['p99_ms']:>8}")

    # Find the knee: the stage after which throughput stops rising much.
    best = max(results, key=lambda r: r["throughput"])
    print(f"\npeak throughput {best['throughput']} req/s at {best['workers']} workers "
          f"(p99 {best['p99_ms']} ms there).")
    print("the number to carry: the worker count where throughput flatlines but p99 keeps climbing is your bottleneck.")


if __name__ == "__main__":
    main()
