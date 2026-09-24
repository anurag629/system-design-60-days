---
title: "Day 4: latency, throughput and the queue"
parent: "Week 1: ground truth"
nav_order: 4
has_children: true
---

# Day 4, Friday 2026-09-25
## Latency, throughput, and the queue that eats your server 🚦

Today's one idea: a server doesn't get gradually slower as it gets busier. It stays fine, then fine, then fine, then falls off a cliff somewhere past 90%. The cause is the queue in front of it, and the math behind it fits on a chai napkin.

If you remember one thing from week 1, make it today's graph. It explains more production outages than any other single idea in this guide.

---

## Before you start ⏪

Nothing from earlier labs is needed today, and there's no network in this lab at all. Everything runs on your laptop. If you skipped Day 3's stretch, that's fine too.

---

## Words you will meet today 📖

Latency is how long one request takes, start to finish. You've been measuring it since Day 1.

Throughput is how many requests a system finishes per second. It's a different number from latency, and the two get confused constantly. A Mumbai local train has terrible latency if you just want to go one stop, and enormous throughput.

Service time, or work, is how long the server spends actually working on one request, not counting any waiting.

Capacity is the most throughput a server can manage. If each request needs 10 ms of work, one server can do at most 100 requests per second.

Utilization is how much of that capacity you're using. 80 requests per second on a server with capacity 100 is 80% utilization. People also say "80% busy."

A queue is the line of requests waiting for the server to be free. Every server has one, even if nobody drew it on the diagram: the operating system's socket backlog, a thread pool's task list, a database's connection wait list.

Arrival rate is how many new requests show up per second. When it's random (users don't coordinate with each other), requests arrive in clumps, and clumps are what fill queues.

Little's Law says the average number of requests inside a system equals the arrival rate times the average time each one spends inside. L = λ × W. It sounds like a tautology until you use it, and then it's everywhere.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [The most important thing to understand about queues](https://blog.danslimmon.com/2016/08/26/the-most-important-thing-to-understand-about-queues/) by Dan Slimmon. Short, and it's the graph from today's lab with one sentence of wisdom attached.
- [Latency sneaks up on you](https://brooker.co.za/blog/2021/08/05/utilization.html) by Marc Brooker, a long-time senior engineer at AWS. It explains why teams that watch average utilization get blindsided.
- [Little's Law on Wikipedia](https://en.wikipedia.org/wiki/Little%27s_law). Read the intro and the examples, and skip the proofs.

Watch these two, after the lab:
- [Queuing theory on a cocktail napkin](https://www.youtube.com/watch?v=tcfyDJgLOVc) by Dan Slimmon, 27 minutes. The same author as the first reading, working through the math you just ran, on a napkin.
- Optional, if you're hooked: ["Stop rate limiting! Capacity management done right"](https://www.youtube.com/watch?v=m64SWl9bfvk) by Jon Moore, 42 minutes. Little's Law used to protect a real system. We come back to this idea in week 7.

### The chai tapri model (15 min)

A chai tapri outside an office. One chaiwala. Making one cup takes him 30 seconds on average. Some cups are quicker, some slower, depending on whether he has to top up the milk.

Customers arrive about once a minute, at random. He's busy half the time. Most people walk up, wait a little, get their chai. Fine.

Now it's 4 pm and people arrive every 35 seconds on average. He can make a cup every 30 seconds, so on paper he keeps up with room to spare. But arrivals are random. Sometimes four people show up in the same minute, and the line grows. Then there's a quiet gap, but he can't make chai for customers who haven't arrived yet, so that idle time is gone forever. He never catches up on the busy bursts using the quiet bits. The line only drains at the speed he makes chai.

That's the whole mechanism. Random arrivals plus a server that can't bank idle time means queues form even when the server is below 100% busy. And the closer you get to 100%, the less idle time there is to drain the bursts, so the line grows and grows.

For the simplest version of this (random arrivals, random work, one server), the average latency is:

```
average latency = work / (1 - utilization)
```

| Utilization | Average latency, in units of "work" |
|---|---|
| 50% | 2x |
| 80% | 5x |
| 90% | 10x |
| 95% | 20x |
| 99% | 100x |

Look at the right column. From 50% to 80% busy, latency goes from 2x to 5x. From 90% to 99%, which is just 10% more traffic, it goes from 10x to 100x. That's the cliff. Today's lab draws it with your own simulated numbers.

### Why this matters in real systems (10 min)

Three things follow, and you'll use all three for the rest of the guide.

First, you plan capacity for 60 to 70% busy at peak, not 95%. The spare 30% isn't waste. It's the room the bursts need so latency stays sane. Teams that run hot to save money spend it later on incidents.

Second, a slow dependency makes you run out of everything. By Little's Law, if your traffic stays the same and each request takes twice as long (say the database got slow), twice as many requests are inside your system at once. Twice as many threads, connections and memory buffers are in use. That's how one slow database takes down every service that calls it.

Third, sharing a queue beats splitting it. Two chaiwalas working from one line do far better than two separate tapris with two separate lines, because nobody gets stuck behind a slow order while the other chaiwala stands idle. The lab measures how much better. Remember this when you meet load balancers on Day 6 and worker pools in week 4.

And for anyone who has tried tatkal booking on IRCTC at 10:00 sharp: that's arrivals at many times capacity for a few minutes, a queue that can only grow, and a site that falls over. The usual fix for that kind of rush, a virtual waiting room that lets people in at a controlled rate, is queue management. You'll build one in week 7.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-04-drills.md`](../notes/day-04-drills.md). Use `work / (1 - utilization)` and Little's Law. Nothing else is needed.

D1. The chaiwala makes one cup in 30 seconds on average. Customers arrive at random, one every 40 seconds on average. How busy is he? What's the average time from joining the line to getting your chai? At the 4 pm rush, customers come every 32 seconds. What is it now?

D2. A food delivery API gets 20,000 requests per second, and the average request takes 150 ms. How many requests are in progress at any moment? If each request holds one database connection the whole time, how many connections do you need? The database has a bad day and the average request now takes 600 ms, at the same traffic. Now how many?

D3. Your server runs at 80% busy at peak. Traffic grows 15% before the next festival sale. How much worse does average latency get? Give a factor.

D4. Your team promises an average latency of no more than 4 times the work time. What's the highest utilization you can run at? Peak traffic is 1,000 requests per second, and one server can handle at most 100. How many servers do you need?

D5. A Mumbai local line runs a train every 3 minutes. Each train carries 4,000 people and the ride takes 60 minutes. What's the throughput in people per hour? What's the latency? The railway adds three coaches to every train, going from 12 to 15. Which of the two numbers changes, and by how much? Then use Little's Law to work out how many people are on trains on this line at any moment, and check it against a count of trains.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-04-queues/queue_lab.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-04-queues/queue_lab.py).

It has two parts. Part 1 simulates a server with a queue, 300,000 requests at a time, at utilizations from 50% to 99%, and compares the result with the formula. It also shows what happens to the same traffic with two and three servers sharing one queue. Part 2 runs a real worker thread with a real `queue.Queue` and real clocks for 8 seconds at a time, and checks Little's Law against a thread that counts what's in the system.

Standard library only, about 40 seconds to run.

### Predict first

Fill in `PREDICTIONS` at the top of the file. The server needs 10 ms of work per request on average, so its capacity is 100 requests per second.

- Q1. What's the average latency at 50% busy (50 req/s)?
- Q2. What's the average latency at 90% busy (90 req/s)?
- Q3. What's the average latency at 99% busy (99 req/s)?
- Q4. Keep 90 req/s, but have two servers share one queue. What's the average latency?

You've read the formula, so Q1 to Q3 are almost a gift. Predict them anyway. Q4 is the one that separates people, because the formula above doesn't cover it. Reason it out.

### Fill in the TODOs

1. TODO 1 is the one-server simulation. It's three lines, and it really is the heart of all queueing: a request starts when it has arrived and the server is free, and finishes after its work.
2. TODO 2 is the same thing for several servers. A heap (Python's `heapq`) hands you whichever server frees up soonest.
3. TODO 3 records each request's latency in the real worker thread.
4. TODO 4 computes what Little's Law predicts, from the arrival rate and the average latency.

The comments above each TODO show the shape. Type it out. For TODO 1 especially, understand why it's `max(arrival, free_at)` before you move on. That one line is the queue.

```bash
cd labs/day-04-queues
python3 queue_lab.py
```

### What you're going to discover

The simulated averages will sit right on top of the formula, and the p99 column will be several times the average. That tail is the part your users actually feel.

The "more servers" rows will surprise you. Adding a second server doesn't halve latency at 90% busy. It does much better than that.

Part 2 will be messier than part 1. Real `sleep()` calls overshoot, so the real server is busier than its label, and you'll see what a small hidden overload does near the cliff. Little's Law will hold anyway, which is the whole point of it.

### Traps ⚠️

- The 99% row is noisy even in simulation. That close to the wall, one unlucky burst builds a queue that takes ages to drain, so two runs can disagree by 20% or more. That's the lesson, not a bug.
- Latency in this lab means time in the system: waiting plus being served. Some sources quote waiting time only. The formula for waiting time alone is different, and mixing the two up is a classic interview slip.
- Part 2 runs in real time. Don't run heavy things alongside it, or your own laptop's CPU becomes part of the queue.
- If part 2's "sent/s" is well under the target, your machine's timer is coarse. Look at the latency column relative to part 1, not at the exact numbers.

### Deliverable

[`labs/day-04-queues/RESULTS.md`](../labs/day-04-queues/RESULTS.md) has a skeleton. Paste the output, then sketch the curve by hand on paper: utilization on the x axis, average latency on the y axis. Photograph it and put it in the file. Drawing it once by hand does more for your intuition than any chart library.

---

## Block 4: write (30 min) 📣

Your angle today is the cliff: "I simulated a server at 50%, 90% and 99% busy. Here's what happened to latency." One table with the utilization column and the latency column does the whole job. The two-servers result makes a strong second post.

Example posts, written with the reference run's numbers, are on the [Day 4 posts](../shares/day-04-posts.md) page. Swap in your own numbers and rewrite them in your voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Add a Day 4 entry to your progress log with these three things:

1. What you completed, and what you skipped.
2. Your average latency at 90% and 99% busy, and your two-server number.
3. One thing you still can't explain.

Then compare your work with the solutions below. Day 5 is designing an API, and why the obvious way to paginate falls over at scale.

---

## Solutions 🔑

Open these only after you've done the day. Reading answers first feels like learning and isn't.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Utilization = 30 / 40 = 75%. Average time = 30 / (1 - 0.75) = 120 seconds, 2 minutes from joining the line to chai in hand. At the rush: 30 / 32 = 93.75% busy, and 30 / (1 - 0.9375) = 480 seconds, 8 minutes. Arrivals got 25% faster. The wait got 4x longer.

D2. Little's Law: L = 20,000 per second × 0.15 seconds = 3,000 requests in progress, so 3,000 connections. At 600 ms: 20,000 × 0.6 = 12,000 connections. Same traffic, four times the connections. If the pool is capped at, say, 5,000, requests start waiting for a connection, which adds latency, which pushes the number in flight up further. This is a very common way for a slow database to take down a healthy app server.

D3. Before: 1 / (1 - 0.8) = 5x the work time. After: utilization 0.8 × 1.15 = 0.92, so 1 / (1 - 0.92) = 12.5x. Latency gets 2.5x worse for 15% more traffic.

D4. 1 / (1 - u) ≤ 4 means u ≤ 0.75, so 75% busy at most. At 75% each server handles 75 req/s, so 1,000 / 75 = 13.3, round up to 14 servers. This assumes the traffic is spread evenly. And from the lab: one shared queue behaves better than 14 separate ones, so real load balancers try to send each request to the least busy server instead of picking at random.

D5. 20 trains per hour × 4,000 = 80,000 people per hour of throughput. Latency is 60 minutes. Adding coaches raises throughput by 25% to 100,000 per hour, and latency stays at 60 minutes. Making the trains faster would do the opposite. Little's Law: L = 80,000 per hour × 1 hour = 80,000 people on trains. Check: a 60-minute ride with a train every 3 minutes means 20 trains on the line at once, × 4,000 = 80,000. It matches, and it always will.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-04-queues/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-04-queues/solution.py).

TODO 1, one server:

```python
start = max(arrival, free_at)
free_at = start + work
latencies.append(free_at - arrival)
```

`max(arrival, free_at)` is the queue. If the server is free before you arrive, you start at once. If not, you start when it frees up, and the difference is your wait.

TODO 2, several servers sharing one queue:

```python
soonest = heapq.heappop(free_times)
start = max(arrival, soonest)
done = start + work
heapq.heappush(free_times, done)
latencies.append(done - arrival)
```

TODO 3, in the real worker thread:

```python
latencies.append((done - arrived) * 1000)
with lock:
    in_system[0] -= 1
```

The lock matters. The producer thread increments that counter while the worker decrements it, and without the lock two updates can collide and one gets lost.

TODO 4, Little's Law:

```python
littles_L = rate * (avg_ms / 1000)
```

Rate is per second, so the latency has to be in seconds. Getting the units wrong gives you an answer 1,000 times too big, which is the most common bug in capacity math everywhere.

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. Your part 1 numbers should be close to these. Part 2 depends on your machine's timers.

```
Part 1: one server, 10 ms of work per request on average, so 100 req/s max
    busy   req/s    avg ms    p50 ms    p99 ms   formula  avg / work
    50%      50      19.9      13.8      91.1      20.0        2.0x
    70%      70      33.5      23.1     157.9      33.3        3.3x
    80%      80      50.2      34.2     236.9      50.0        5.0x
    90%      90      98.1      66.0     481.2     100.0        9.8x
    95%      95     221.4     155.5     893.8     200.0       22.1x
    99%      99    1223.7     917.8    4485.6    1000.0      122.4x

  Same traffic at 90 req/s, more servers sharing one queue:
    1 server   each  90% busy   avg    99.9 ms   p99   437.4 ms
    2 servers  each  45% busy   avg    12.5 ms   p99    53.8 ms
    3 servers  each  30% busy   avg    10.3 ms   p99    46.7 ms

Part 2: real threads, real clock, 8 s per row
    busy  sent/s    avg ms    p99 ms  avg in system  Little says
    50%    51.7      33.9     171.9           1.73         1.75
    80%    76.7      91.2     334.0           7.00         6.99
    90%    84.5     477.5     732.1          38.16        40.36
```

Q1 to Q3: 20 ms, 100 ms and 1,000 ms by the formula. The simulation gave 19.9, 98.1 and 1,224. The 99% row overshoots because that close to the wall, the queue needs a very long run to settle to its average. Run it with a different seed and it moves a lot.

Q4: about 12.5 ms. Most people guess 50 ms ("half of 100"). The real answer is 8 times better than one server, because each server is now only 45% busy, which is far from the wall, and a shared line means no request waits behind a slow one while the other server is idle. For the curious, the exact textbook answer for two servers comes from the Erlang C formula, and it gives 12.5 ms too.

The p99 column: at 90% busy, 1 request in 100 takes about 5 times the average. Averages hide this. Your users feel the p99.

Part 2: at 50% the real server averaged 34 ms instead of 20. Each `sleep(0.010)` on macOS overshoots, so the real work per request was more like 13 ms, which quietly made the server about 65% busy instead of 50%. At 90% the same overshoot pushes it to the edge, and latency jumps to 478 ms. A few percent of hidden extra work does little at low load and a lot near the wall. That's the practical lesson: your real headroom is always smaller than the dashboard says. Meanwhile Little's Law matched to within a few percent in every row (1.73 vs 1.75, 7.00 vs 6.99), even though nothing else about part 2 was clean.

</details>
