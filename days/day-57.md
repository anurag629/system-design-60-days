---
title: "Day 57: capstone load test"
parent: "Week 8: putting it all together"
nav_order: 8
has_children: true
---

# Day 57
## Capstone load test, break your own thing before the world does 💥

Today's one idea: you point a load generator at the slice you built, turn the pressure up stage by stage, and watch for the knee, the point where adding more clients stops buying you throughput and only buys you latency. That knee is your bottleneck. Finding it on purpose, in a quiet room, is infinitely better than finding it at 2am when real users do it for you.

This is the most satisfying day of the course. You get to attack your own creation and measure exactly where it falls over.

---

## Before you start ⏪

Your service from Day 56 runs and serves real requests. You wrote down a prediction for where it breaks. Bring Day 1 and Day 4 (latency, the tail, why p99 is the number that matters), Day 17 (the thundering herd), and Day 48 (capacity: you size for about 70 percent of the knee, not 100).

---

## Words you will meet today 📖

Throughput is requests served per second. It rises as you add load, until the system saturates, then it flattens. The flat line is the ceiling.

A percentile is the latency that a fraction of requests beat. p99 of 50ms means 99 percent of requests finished in under 50ms and the slowest 1 percent took longer. You watch p99, not the average, because the average hides the tail (Day 1, Day 4).

The knee is the load at which throughput flattens but latency keeps climbing. Before the knee, more clients means more work done. After it, more clients just means everyone waits longer. The knee is where your bottleneck lives.

A stress test pushes past normal load to find the breaking point. A soak test holds moderate load for a long time to find leaks. A spike test slams sudden load to see if you recover. Today you mostly stress test.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these two:
- [Load test types](https://grafana.com/docs/k6/latest/testing-guides/test-types/) from the k6 docs. Load, stress, spike, soak, in plain terms. k6 is the industry-standard load tool, and this is its clearest conceptual page.
- [The USE method](https://www.brendangregg.com/usemethod.html) by Brendan Gregg. A sharp way to hunt a bottleneck: for every resource, check Utilisation, Saturation, and Errors. When your throughput flatlines, this tells you which resource to blame.

Watch, one of:
- [Basics of load testing with k6 and Grafana in 20 minutes](https://www.youtube.com/watch?v=gvounvDSDGg) by k6, about 20 minutes. The real tool, with a demo.
- [How to do performance testing with k6](https://www.youtube.com/watch?v=ghuo8m7AXEM) by Alex Hyett, about 10 minutes, if you want the shorter version.

We use our own tiny load generator today (pure standard library, nothing to install), but k6 is what you will reach for at work, so it is worth seeing.

### The shape of a load test, and the knee 📈

A load test tells a story in two lines: throughput and latency, both plotted against offered load. At low load, throughput rises almost linearly as you add clients, and latency barely moves, because the system is coasting. Then you hit the knee. Throughput flattens (the system is now serving as fast as its slowest resource allows) while latency climbs steeply (new clients just join a queue). Push further and latency goes vertical and errors may start. The knee is the single most useful number a load test gives you: it is your real capacity, and Day 48 said you run at about 70 percent of it, not at it.

When you see the knee, the next question is which resource caused it, and that is the USE method. For each resource (CPU, the database, the network, a lock), ask: how utilised is it, is it saturated (a queue forming), and is it erroring? The resource that is pinned at 100 percent utilisation or has a growing queue when throughput flatlines is your bottleneck. In the reference service it is the single database lock; in yours it might be CPU, or the database, or a connection limit. The load test finds the symptom, USE finds the cause.

### Predict, then break 🎯

Same loop as every day. Before you run, write your prediction: at how many concurrent clients does p99 cross, say, 100ms? What is your peak throughput? Which resource gives out first? Then run the load generator at rising concurrency and watch reality disagree with you. The gap is the lesson, and on your own code it lands harder than any lab, because you cannot blame the author. You are the author.

---

## Block 2: drill (40 min) ✍️

Paper first, into [`notes/day-57-drills.md`](../notes/day-57-drills.md). Predict before you run.

D1. Your prediction. For your service: peak throughput, the worker count where p99 crosses 100ms, and which resource you think gives out first. Write all three down now.

D2. Reading a result. Throughput rises 1 to 8 workers then stays flat from 8 to 32, while p99 goes 1ms, 2ms, 4ms, 12ms across those same stages. In one sentence, where is the knee and what is it telling you?

D3. p99 vs average. Why do you watch p99 and not the average throughput's latency? What does a healthy average hide (Day 1, Day 4)?

D4. The USE method. Your throughput flatlines. List the three things USE tells you to check on each resource, and name the resource you would check first for your specific service.

D5. Capacity. If your measured knee is 10,000 requests per second, what do you set your real capacity target at, and why not 10,000 (Day 48)?

---

## Block 3: build (100 min) 🔧

Break it. The load generator is [`labs/day-57-capstone-loadtest/loadgen.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-57-capstone-loadtest/loadgen.py), pure standard library. Start your Day 56 service, then in another terminal point the generator at it and run rising stages:

```
# terminal 1: your service (or the reference)
cd labs/day-56-capstone-build && python3 app.py

# terminal 2: push it, read-heavy then write-heavy
cd labs/day-57-capstone-loadtest
python3 loadgen.py --url http://127.0.0.1:8080 --stages 1,2,4,8,16,32 --duration 3 --write-ratio 0.1
python3 loadgen.py --url http://127.0.0.1:8080 --stages 1,2,4,8,16,32 --duration 3 --write-ratio 0.9
```

It prints throughput, error rate, and p50/p95/p99 per stage, and names the peak. Find your knee. Then do the real work: form a hypothesis about the bottleneck (use the USE method and your `/metrics`), make one change to try to raise the ceiling, and measure again. Did the knee move? That cycle, measure, hypothesise, change one thing, measure again, is exactly how performance work is done in the real world.

### What a good load test session produces

A table of throughput and p99 across rising load, the knee clearly identified, a named bottleneck (not a guess, a reasoned cause), and ideally one change you made that moved the knee, with the before and after numbers. If you raised your ceiling even a little and can explain why, you have done real performance engineering.

### Deliverable

Your load-test numbers (both mixes), the knee, the named bottleneck, and your prediction next to reality. Save them for the writeup tomorrow.

---

## Block 4: write (30 min) 📣

Your angle is the joy and humility of breaking your own thing. "I load tested the slice I built and found its knee: the exact point where throughput flatlines and latency takes off. My prediction was [right / hilariously wrong], and the real bottleneck turned out to be [X]." Share your throughput-vs-p99 numbers.

Example posts are on the [Day 57 posts](../shares/day-57-posts.md) page.

---

## End of day: log it 📝

Log the three: your knee and peak throughput, the real bottleneck, and how far off your prediction was.

Tomorrow you turn all of this into a clean architecture document: the design, the tradeoffs, the measured numbers, the failure modes, the cost. The numbers you found today are the heart of it, because a design backed by a load test is worth ten backed by hope.

---

## Solutions 🔑

Open after your own run.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. No single right answer; the point is to commit to three numbers before reality does. Most people underestimate how early the knee comes and overestimate peak throughput.

D2. The knee is at 8 workers. Throughput stopped rising there, so 8 workers already saturates the slowest resource; everything past 8 just lengthens the queue, which is why p99 keeps climbing (2ms to 12ms) while throughput stays flat. The system is telling you its capacity is whatever throughput it hit at 8 workers, and beyond that you are only adding latency.

D3. Because throughput is an aggregate and hides the experience of individual requests. A service can serve a healthy total while the slowest 1 percent of requests are timing out, and those are often your biggest or most important users (Day 18). The average latency is dragged down by the many fast requests and hides the tail; p99 is where the pain actually lives (Day 1, Day 4).

D4. For each resource: Utilisation (what fraction of the time it is busy), Saturation (how much work is queued waiting for it), and Errors. For a small HTTP service backed by SQLite, check the database and the lock around it first, because a single-writer store is the usual first ceiling; then CPU, then connection limits.

D5. You set your target at about 7,000 requests per second, roughly 70 percent of the knee (Day 48). Not 10,000, because at the knee latency is already climbing and you have zero headroom for a traffic spike, a failed node shifting its load onto you, or a slow dependency. Running at the cliff edge means the first bad moment pushes you over it.

</details>

<details markdown="1">
<summary>A reference run against app.py (one laptop)</summary>

Numbers from running the reference service and load generator on a developer laptop. Yours will differ; the shape is what matters.

Read-heavy (write-ratio 0.1), stages 1,2,4,8,16,32 workers:

```
 workers      req    thru/s   errors   p50 ms   p95 ms   p99 ms
       1    25664    8554.0    0.00%      0.1      0.3      0.4
       2    34609   11533.7    0.00%      0.1      0.4      0.6
       4    37063   12352.7    0.00%      0.3      0.6      0.8
       8    38320   12771.3    0.00%      0.6      1.0      1.3
      16    36780   12253.8    0.00%      1.4      2.0      2.4
      32    37752   12576.0    0.00%      2.8      3.5      4.0
```

The knee is at 8 workers: peak throughput about 12,700 req/s, and past it throughput is flat while p99 triples and quadruples (1.3ms to 4.0ms). The cache absorbs most reads, so the ceiling here is really the HTTP server and the Python runtime handling connections.

Write-heavy (write-ratio 0.9), same stages:

```
 workers      req    thru/s   errors   p50 ms   p95 ms   p99 ms
       1     9650    3216.5    0.00%      0.3      0.4      0.5
       2    12308    4102.2    0.00%      0.5      0.6      0.7
       4    12409    4135.3    0.00%      1.0      1.2      1.3
       8    12525    4172.7    0.00%      1.9      2.3      2.7
      16    12312    4099.6    0.00%      3.9      4.6      5.0
      32    12550    4172.6    0.00%      7.5      8.7     11.8
```

Peak throughput about 4,200 req/s, roughly a third of the read ceiling, and it flattens even earlier. That gap is the deliberate bottleneck doing its job: every write serialises through the single database lock, so no amount of extra concurrency helps, it just piles into the queue and p99 climbs from 2.7ms at the knee to 11.8ms at 32 workers.

The number to carry: reads are three times cheaper than writes here, and the write path is the bottleneck, exactly because of the shared lock. That is the single fact a writeup should lead with.

</details>

<details markdown="1">
<summary>How to actually raise the ceiling</summary>

If you want to move the knee on the reference service (or your own SQLite-backed slice), the realistic levers, roughly in order:

Turn on write-ahead logging (`PRAGMA journal_mode=WAL`), which lets reads proceed while a write is in progress and usually lifts write throughput noticeably. Batch multiple inserts into one transaction instead of committing every row, which amortises the expensive commit. Give reads their own connection so a write does not block an uncached read. And at the architecture level, the real fix is the one from the whole course: the single node is the ceiling, so you shard the store or put more nodes behind the balancer (Day 6, Day 13). The point of the exercise is not to make this toy fast, it is to feel how a single serialising resource caps a whole system no matter how much concurrency you throw at it, and to see a number move when you remove it.

</details>
