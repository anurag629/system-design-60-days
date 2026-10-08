#!/usr/bin/env python3
"""
Day 56 reference service: one real slice of a URL shortener.

This is here so you are not staring at a blank file. It is a working,
runnable example of what "a real slice, not a toy" means: an HTTP server,
a real database, a read cache, and a metrics endpoint. It is small on
purpose, and it has a real bottleneck on purpose, which you will find on
Day 57 with the load generator.

Run it:
    python3 app.py            # listens on http://127.0.0.1:8080

Then, in another terminal:
    curl -s -X POST http://127.0.0.1:8080/shorten -d '{"url":"https://example.com"}'
    curl -s -i http://127.0.0.1:8080/u/1          # the code it gave you
    curl -s http://127.0.0.1:8080/metrics

Pure standard library. Nothing to install.

Your actual capstone build is YOUR system, not this one. Read this for the
shape, then build the interesting slice of your own design the same way:
a request comes in, something real happens to real data, and you can
measure it.
"""

import json
import sqlite3
import threading
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB_PATH = "shortener.db"
CACHE_CAPACITY = 1000  # how many code to long mappings we keep hot in memory

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode_base62(n):
    """Turn an integer id into a short string. id 1 -> '1', id 125 -> '21'."""
    if n == 0:
        return "0"
    out = []
    while n > 0:
        n, rem = divmod(n, 62)
        out.append(ALPHABET[rem])
    return "".join(reversed(out))


def decode_base62(s):
    n = 0
    for ch in s:
        n = n * 62 + ALPHABET.index(ch)
    return n


class Store:
    """
    The data layer. One SQLite connection, guarded by one lock.

    That single lock is the deliberate bottleneck. Every write AND every
    uncached read has to take it, so the database serves one request at a
    time no matter how many workers hammer the front door. The cache is what
    saves you: a cached read never touches the lock. Day 57 is where you see
    this show up as a flat throughput line and a climbing p99.
    """

    def __init__(self, path):
        # check_same_thread=False lets the threaded server share one connection.
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        with self.lock:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS urls (id INTEGER PRIMARY KEY AUTOINCREMENT, long TEXT NOT NULL)"
            )
            self.conn.commit()
        self.cache = OrderedDict()  # code -> long, most-recently-used at the end

    def create(self, long_url):
        with self.lock:
            cur = self.conn.execute("INSERT INTO urls (long) VALUES (?)", (long_url,))
            self.conn.commit()
            new_id = cur.lastrowid
        code = encode_base62(new_id)
        self._cache_put(code, long_url)
        return code

    def resolve(self, code):
        # Fast path: in the cache, no lock, no database.
        hit = self.cache.get(code)
        if hit is not None:
            self.cache.move_to_end(code)
            return hit, True
        # Slow path: take the lock, hit the database.
        try:
            row_id = decode_base62(code)
        except ValueError:
            return None, False
        with self.lock:
            row = self.conn.execute("SELECT long FROM urls WHERE id = ?", (row_id,)).fetchone()
        if row is None:
            return None, False
        self._cache_put(code, row[0])
        return row[0], False

    def _cache_put(self, code, long_url):
        self.cache[code] = long_url
        self.cache.move_to_end(code)
        while len(self.cache) > CACHE_CAPACITY:
            self.cache.popitem(last=False)  # evict the least-recently-used


class Metrics:
    """The numbers you look at. Counters, guarded by their own lock."""

    def __init__(self):
        self.lock = threading.Lock()
        self.writes = 0
        self.reads = 0
        self.cache_hits = 0
        self.not_found = 0
        self.started = time.time()

    def snapshot(self):
        with self.lock:
            reads = self.reads
            hits = self.cache_hits
            return {
                "writes": self.writes,
                "reads": reads,
                "cache_hits": hits,
                "cache_hit_rate": round(hits / reads, 3) if reads else 0.0,
                "not_found": self.not_found,
                "uptime_s": round(time.time() - self.started, 1),
            }


STORE = Store(DB_PATH)
METRICS = Metrics()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body, headers=None):
        payload = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path != "/shorten":
            self._send(404, json.dumps({"error": "not found"}))
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            long_url = json.loads(raw).get("url")
        except (ValueError, AttributeError):
            long_url = None
        if not long_url:
            self._send(400, json.dumps({"error": "send {\"url\": \"...\"}"}))
            return
        code = STORE.create(long_url)
        with METRICS.lock:
            METRICS.writes += 1
        self._send(200, json.dumps({"short": "/u/" + code, "code": code}))

    def do_GET(self):
        if self.path == "/healthz":
            self._send(200, json.dumps({"ok": True}))
            return
        if self.path == "/metrics":
            self._send(200, json.dumps(METRICS.snapshot()))
            return
        if self.path.startswith("/u/"):
            code = self.path[len("/u/"):]
            long_url, was_cached = STORE.resolve(code)
            with METRICS.lock:
                METRICS.reads += 1
                if was_cached:
                    METRICS.cache_hits += 1
                if long_url is None:
                    METRICS.not_found += 1
            if long_url is None:
                self._send(404, json.dumps({"error": "no such code"}))
                return
            self._send(302, json.dumps({"location": long_url}), {"Location": long_url})
            return
        self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, *args):
        pass  # quiet; the load generator is the thing doing the talking


def main():
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"listening on http://127.0.0.1:{port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
        server.shutdown()


if __name__ == "__main__":
    main()
