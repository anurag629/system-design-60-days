---
title: "Day 56: capstone build"
parent: "Week 8: putting it all together"
nav_order: 7
has_children: true
---

# Day 56
## Capstone build, one real slice, all the way through 🔨

Today's one idea: you build one vertical slice of your capstone, end to end, so a real request comes in, something real happens to real data, and you can measure it. Not a whole layer, not a toy, one thin feature that genuinely works. And because staring at a blank file is the worst way to start, the lab has a complete working reference service you can read, run, and copy the shape from.

Yesterday you designed. Today you make something that runs and serves traffic.

---

## Before you start ⏪

Your design doc from Day 55 is open. You know the one slice you are building and the number you predicted for it. Bring the whole course: the HTTP service (Day 6), the storage choice (week 2), the cache (week 3), a queue if your slice needs async (week 4). Have Python 3 and a terminal. Pure standard library, nothing to install.

---

## Words you will meet today 📖

A walking skeleton is the thinnest possible end-to-end version of your system: a request goes in, the real path runs, a response comes out, even if almost every part is minimal. You get something alive first, then grow it, rather than building a perfect database layer that does nothing for a week.

A health check is a trivial endpoint (like `/healthz`) that returns "I am alive," used by load balancers and your load test to know the service is up before they send real traffic.

A metrics endpoint exposes the numbers your service tracks (request counts, cache hit rate) so you can see what it is doing, which is what makes a slice measurable instead of a black box (Day 43).

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these two, both short, both about how to build a slice rather than a new system topic:
- [Walking skeleton](https://wiki.c2.com/?WalkingSkeleton) on the c2 wiki. The idea in a few paragraphs: get a thin end-to-end thing running first, then flesh it out. This is how you avoid the classic trap of building a beautiful foundation that never becomes a system.
- [The twelve-factor app](https://12factor.net/), skim it. You do not need all twelve, but the ones about config, logs as streams, port binding, and disposability are exactly the habits that make a small service behave well under a load test tomorrow.

No video today. This is a build day. The best thing in your ears is nothing, so you can think, and the best thing on your screen is your own code and the reference service.

### Read the reference service, then build your own 📖

Open [`labs/day-56-capstone-build/app.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-56-capstone-build/app.py). It is a complete, runnable slice of a URL shortener: an HTTP server, a real SQLite database, an in-memory read cache, and a metrics endpoint. Around 200 lines, pure standard library. Run it:

```
cd labs/day-56-capstone-build
python3 app.py
```

Then poke it:

```
curl -s -X POST http://127.0.0.1:8080/shorten -d '{"url":"https://example.com"}'
curl -s -i http://127.0.0.1:8080/u/1
curl -s http://127.0.0.1:8080/metrics
```

This is here so you have a model of what "a real slice, not a toy" looks like: it has a read path and a write path, a cache that makes reads cheap, a database that makes writes durable, and metrics that make it observable. It also has a deliberate bottleneck (every write and every uncached read serialises through one database lock), which is the thing you will discover with the load generator tomorrow. Read it until you understand every part, then build the equivalent slice of your own system.

### What "real, not toy" means 🎯

A toy stores things in a Python dict and forgets them when it stops. A real slice persists to something (a file, SQLite), has a read path and a write path, and exposes metrics so you can see it work. It does not need to be big. The reference service is small. But it does need to be honest: the request does the real work, the data really lands, and you can measure the result. That honesty is what makes tomorrow's load test meaningful. If your slice fakes the work, the load test measures nothing.

So build your slice with: a persistent store (SQLite via the standard library's `sqlite3`, or an append-only file), the actual read and write paths from your design, a `/healthz` endpoint so the load generator knows you are up, and a `/metrics` endpoint that counts what matters for your system. Keep it to one file if you can. Make it run.

---

## Block 2: drill (40 min) ✍️

Paper first, into [`notes/day-56-drills.md`](../notes/day-56-drills.md). Plan before you type.

D1. The walking skeleton. Write the thinnest end-to-end path through your slice: the one request, the one thing it does, the one response. What is the smallest version that genuinely works?

D2. Persistence. What really stores your data, and why not a plain dict? What happens to your data when the process restarts?

D3. Metrics. List the three or four numbers your `/metrics` endpoint should expose for your system to be observable. For a shortener it is writes, reads, cache hit rate. For yours?

D4. The predicted bottleneck. Before you build, where do you think your slice will be slow or cap out under load, and why? Write it down; tomorrow proves you right or wrong.

D5. Read the reference. In `app.py`, find the deliberate bottleneck (hint: what does every write and every uncached read have to take?). Explain in one sentence why that serialises the service no matter how many clients hammer it.

---

## Block 3: build (100 min) 🔧

Build your slice. Read `app.py` first for the shape, then write your own service for your own design in [`labs/day-56-capstone-build/`](https://github.com/anurag629/system-design-60-days/tree/main/labs/day-56-capstone-build) (or wherever you keep your fork's capstone). It must run, persist real data, expose `/healthz` and `/metrics`, and implement the slice you designed yesterday.

Get it to the walking-skeleton stage first: the thinnest path that works end to end. Only then add the cache, the async counter, or whatever your design calls for. Run it, curl it, watch the metrics move. When it serves real requests and the numbers change as you poke it, you are done for the day.

If you are short on time or your system is close enough, it is completely fine to take `app.py` as your starting point and modify it into your slice. The point is a running, measurable thing by end of day, not heroics.

### What a finished slice looks like

It starts with one command. It answers `/healthz`. It does the real work of your slice and persists it. Its `/metrics` endpoint shows sensible numbers that move when you use it. And you have a guess, written down, about where it will break tomorrow.

### Deliverable

A running service (yours, or the reference modified into your slice), the curl commands that exercise it, and your written prediction for tomorrow's load test.

---

## Block 4: write (30 min) 📣

Your angle is the walking skeleton and the honesty of a real slice. "I built one slice of my capstone today, end to end. Not a whole layer, not a toy that fakes the work. A thin path where a real request hits a real store and the metrics move. Tomorrow I find out where it breaks." Share your `/metrics` output and your prediction.

Example posts are on the [Day 56 posts](../shares/day-56-posts.md) page.

---

## End of day: log it 📝

Log the three: the slice you got running, the hardest part of making it real, and your prediction for where it breaks under load.

Tomorrow you break it. The load generator in the lab points at your service and pushes until the numbers bend. You find your true bottleneck, and you find out how good your prediction was.

---

## Solutions 🔑

Open after you have built your own slice.

<details markdown="1">
<summary>A guided tour of the reference service</summary>

`app.py` is a URL shortener slice in four parts.

The encode/decode helpers turn an integer id into a short base62 string and back. Id 1 becomes "1", id 125 becomes "21". This is the counter approach from Day 51: no collisions, codes are short, and they are sequential (which is fine for a demo).

The Store class is the data layer: one SQLite connection guarded by one lock. The create method inserts a row and returns the base62 of its id, caching the mapping. The resolve method checks an in-memory cache first (no lock, no database) and only falls through to the database (under the lock) on a miss. That cache is what makes reads cheap.

The Metrics class is plain counters behind their own lock: writes, reads, cache hits, and a computed hit rate. This is what `/metrics` returns, and it is the difference between a measurable service and a black box.

The Handler wires it to HTTP: POST /shorten creates, GET /u/<code> resolves and returns a 302 redirect, GET /metrics and GET /healthz report. It runs on a ThreadingHTTPServer so many clients can connect at once.

The deliberate bottleneck (D5): every write and every uncached read has to take the single store lock, so the database serves one request at a time no matter how many threads are hammering the front door. The cache hides this for repeated reads, but the write path cannot escape it. Tomorrow's load test makes this visible as a flat write-throughput line and a climbing p99.

</details>

<details markdown="1">
<summary>If your slice will not persist or will not start</summary>

The two most common beginner snags, and their fixes.

"It forgets everything on restart." You are storing in a dict, not persisting. Use `sqlite3` (standard library) or append to a file. A dict is a toy; a store survives a restart.

"sqlite3 complains about threads." The threaded server runs handlers on different threads, and a SQLite connection is not shared across threads by default. Open the connection with `check_same_thread=False` and guard all access with a lock, exactly as `app.py` does. That lock is also your deliberate bottleneck, which is a feature today, not a bug.

</details>
