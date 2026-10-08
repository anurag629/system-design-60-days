---
title: "Day 56 build guide"
parent: "Day 56: capstone build"
grand_parent: "Week 8: putting it all together"
nav_order: 1
---

# Build guide: one real slice

The reference service `app.py` lives next to this file. Read it, run it, then build the equivalent slice of your own capstone.

## Run the reference

```
cd labs/day-56-capstone-build
python3 app.py            # listens on http://127.0.0.1:8080
```

In another terminal:

```
curl -s -X POST http://127.0.0.1:8080/shorten -d '{"url":"https://example.com"}'
curl -s -i http://127.0.0.1:8080/u/1
curl -s http://127.0.0.1:8080/metrics
curl -s http://127.0.0.1:8080/healthz
```

You will get a short code back, a 302 redirect when you resolve it, and live counters from `/metrics`. Stop it with Ctrl-C. It writes a `shortener.db` file (gitignored), which you can delete to reset.

## What to copy (the shape, not the domain)

- a persistent store (SQLite via `sqlite3`, or an append-only file), not a dict
- a read path and a write path from your Day 55 design
- an in-memory cache if your read path benefits from one
- `/healthz` so the load generator knows you are up
- `/metrics` exposing the three or four numbers that matter for your system
- a threaded HTTP server so many clients can connect at once

## The build checklist

1. Walking skeleton first: the thinnest end-to-end path that genuinely works.
2. Then add the cache / queue / extra endpoints your design calls for.
3. Run it, curl it, watch `/metrics` move as you use it.
4. Write down, before tomorrow, where you think it will break under load.

## The deliberate bottleneck

In `app.py`, every write and every uncached read takes one database lock, so the database serves one request at a time. The cache hides this for repeated reads; the write path cannot escape it. That is on purpose. Day 57's load generator will make it visible as a flat write-throughput line and a climbing p99. Your own slice has a bottleneck too. Guess where it is now, prove it tomorrow.

## It is fine to start from app.py

If your capstone is close enough to a shortener, or you are short on time, copy `app.py` and modify it into your slice. The goal is a running, measurable service by end of day, not heroics from scratch.
