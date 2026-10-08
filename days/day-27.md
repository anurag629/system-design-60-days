---
title: "Day 27: backpressure and load shedding"
parent: "Week 4: async, queues and the log"
nav_order: 6
has_children: true
---

# Day 27
## What to do when the work arrives faster than you can do it 🌊

Today's one idea: a queue does not make an overloaded system faster. It just hides the overload for a while. If work arrives faster than you can finish it, an unbounded queue grows until memory or patience runs out, and nothing ever errors along the way. The real fixes are two, and you pick one per system: push back on the producer (backpressure) or turn work away fast (load shedding). Both start with the same move, capping the queue.

This is Day 4's queue cliff again, except now the queue is one you built, in your own process, and you get to decide what happens when it fills.

---

## Before you start ⏪

Keep Day 4 close today. The two things you need from it are Little's Law, L = λ × W, and the idea that a server below 100 percent busy is fine while one at or past 100 percent falls off a cliff. Today a work queue sits between a fast producer and a slow consumer, and Little's Law turns "the queue is deep" into "every new job waits this many seconds." You also met the word backpressure on Day 22, when you first put a bounded queue between a producer and a consumer. Today you measure what it actually does.

Day 2's comfort with Python is enough. The lab is standard library only.

---

## Words you will meet today 📖

A producer is whatever puts work into the queue: a web handler accepting requests, a thread reading from Kafka, a process tailing a file. A consumer is whatever takes work out and does it. The whole day is about what happens when the producer is faster than the consumer.

An unbounded queue has no size limit. Every offer is accepted, always. It feels safe and it is the trap at the centre of today.

A bounded queue has a fixed capacity. Once it is full, something has to give, and that choice is the lesson.

Backpressure is the full queue pushing back on the producer. With a blocking put, a producer that tries to add to a full bounded queue is made to wait until a slot frees up. That wait travels upstream and slows the producer down to the consumer's rate. The system stops accepting work faster than it can finish it.

Load shedding is refusing work fast when you are full, instead of queuing it. The web version is returning HTTP 429, Too Many Requests, in microseconds. You drop the excess on purpose so the work you did accept stays fast.

Head-of-line blocking is when one stuck item holds up everything behind it. It is why a producer blocked on a full queue can be worse than a request you simply dropped: the blocked producer is often a shared, limited resource, like a request thread, and while it waits it serves no one else.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Queues Don't Fix Overload](https://ferd.ca/queues-don-t-fix-overload.html) by Fred Hebert. Short, sharp, and it is exactly today's Part 1. A queue in front of an overloaded service does not absorb the overload, it defers and worsens it. If you read one thing, read this.
- [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/) by Marc Brooker, in the Amazon Builders' Library. The practitioner's view of the fast "no": why a server should reject early and cheaply, and how that keeps it standing under a flood.
- [Handling overload](https://sre.google/sre-book/handling-overload/) from Google's SRE book. The production framing: client-side throttling, graceful degradation, and why you shed the least important work first.

Watch, after the lab:
- [Backpressure in Software Development, simply explained](https://www.youtube.com/watch?v=3DTSIlj72Qs) by Software Developer Diaries, about 9 minutes. A clean picture of the producer, the consumer, and the signal that travels back up the pipe.
- [How to protect your systems with throttling and rate limiting](https://www.youtube.com/watch?v=CW4gVlU0xtU) by Arpit Bhayani, about 16 minutes. The 429 side of today, with real examples of turning work away to stay alive.

### Day 4 again, but the queue is yours now (14 min)

On Day 4 the queue was invisible: the socket backlog, the thread pool's task list, the database's connection wait list. You measured the cliff and moved on. Today you build the queue yourself, a `queue.Queue` between a producer thread and a consumer thread, and you get to watch it fill.

The arithmetic is the same. If the producer offers 500 jobs a second and the consumer finishes 300, the queue gains 200 jobs every second. There is no clever scheduling that fixes this. The consumer can only do 300, so 200 a second have to go somewhere, and in an unbounded queue they pile up. After ten minutes that is 120,000 jobs waiting.

Now point Little's Law at it. A job that joins the back of a 120,000-deep queue drained at 300 a second waits 120,000 / 300 = 400 seconds, almost seven minutes, before the consumer even looks at it. A minute later the queue is deeper and the wait is longer. There is no steady state, because arrival is greater than service. L and W both run off to infinity together. That is the whole problem in one line: in an overloaded system, queue depth and latency do not settle, they diverge.

### The unbounded queue is a trap (12 min)

Here is what makes it dangerous, and it is the opposite of what your instinct says. An unbounded queue never fails. Every `put` succeeds. No exception is raised, no request is rejected, every dashboard is green. The producer is happy. The queue is happy. And the system is dying.

What is actually happening is that memory climbs, because every unfinished job is sitting in RAM, and latency climbs, because every job waits behind a longer and longer line. The first thing a user notices is that responses got slow. The second thing, some minutes later, is that the process ran out of memory and died, or a timeout somewhere upstream fired and the retries made everything worse. By then the cause, a queue that quietly grew for ten minutes, is long gone from the logs.

This is why "we were getting overloaded, so we added a queue" is one of the most common ways to turn a small, visible problem (some requests are slow) into a large, invisible one (the service falls over an hour later and nobody knows why). A queue is a buffer for bursts, a short spike that drains in the quiet moments after. It is not a fix for a consumer that is simply too slow for the sustained load. For that you need fewer jobs or a faster consumer, and until you have one of those, the queue has to be bounded.

### Backpressure: the bounded queue that pushes back (12 min)

Cap the queue, and the interesting question appears: what happens on the offer that would overflow it? The first answer is backpressure. Make the producer wait.

With a blocking `put`, a producer that offers to a full bounded queue is parked right there until the consumer pulls something off and frees a slot. The producer cannot run ahead any more. Its rate is now pinned to the consumer's rate, because it only gets to place a job each time the consumer finishes one. The fast producer has been throttled, not by any rate limit you configured, but by the simple physics of a full queue and a blocking call. In the lab you watch the producer's 500-a-second intent collapse to the consumer's 200-a-second reality, and the queue depth go flat.

Picture a Swiggy order handed to a kitchen that is slammed. 🍔 If the counter keeps taking orders no matter what, the kitchen's ticket rail grows until food comes out cold an hour late. Backpressure is the kitchen telling the counter "hold on, we are full," so the counter slows down taking orders. The queue stops growing. The catch is that the counter is now busy waiting, and if the counter is a shared resource, say the one person who also greets walk-ins, then everything that person does is now stuck behind the kitchen. That is head-of-line blocking, and it is why backpressure is the right answer when the producer can afford to slow down, and the wrong one when the producer is a thread you need back immediately.

### Load shedding: the fast no (10 min)

Backpressure assumes the producer will wait politely. Incoming user requests do not. A browser hitting your checkout API at 10 AM on sale day is not going to block gracefully, it is going to time out and retry, which adds load. When you cannot slow the producer down, the second answer is to turn work away, fast.

Load shedding means that when the bounded queue is full, you reject the offer immediately instead of queuing it. On the web that is an HTTP 429 returned in microseconds. The job you shed costs almost nothing, a tiny fraction of the work of actually serving it, so you can say no to a flood very cheaply and keep the capacity you have for the work you did accept. In the lab you offer about 1,200 jobs, accept what fits, and shed the rest, and the jobs you accept keep a short, bounded wait the whole time.

This is the IRCTC tatkal flood in one move. 🚆 The booking opens, millions of phones hit the same endpoint in the same second, and the only way the site stays up is to admit a controlled trickle and turn the rest away at the door with a clear "try again," rather than queue ten million requests it can never serve. A fast, honest no protects the system. The unbounded yes buries it. And notice the tie back to Day 4: both backpressure and shedding only buy you sanity if you are normally running with headroom. Run at 70 percent, keep the queue bounded, and these are the safety behaviours at the edge. Run at 100 percent as the plan, and no queue policy saves you.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-27-drills.md`](../notes/day-27-drills.md). Use `wait = depth / drain_rate` and Little's Law. Nothing else is needed.

D1. A producer offers 500 jobs per second and the consumer drains 300 per second, into an unbounded queue. After 10 minutes, how many jobs are backed up? How long does a job joining the back now wait before it is even picked up? What happens to that wait as time goes on?

D2. Your consumer handles 200 jobs per second, and your SLA allows at most 300 ms of queueing delay per job. How big should you cap the queue? If someone sets the cap to 10,000 "to be safe," what does that do to the worst-case wait, and why is a big queue a bug and not a safety margin?

D3. A request handler puts a job on a bounded in-process queue that a worker pool drains. The queue fills and `put()` blocks. Walk the chain: what blocks next, and next, all the way to the user? When is a blocked producer worse than a dropped request?

D4. Requests arrive at 1,000 per second and your service handles 400 per second. You shed the excess with a 429 that costs about 1 percent of the work of serving a request. How many 429s per second? How much of your capacity does shedding burn? Why does the fast no keep the system alive where queuing the excess would not?

D5. For each, pick block (backpressure) or shed (429 or drop), and say why in a few words: an internal batch ETL reading from Kafka; a user-facing checkout API in a flash sale; a logging and metrics pipeline; a payment webhook receiver.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-27-backpressure/backpressure.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-27-backpressure/backpressure.py).

It is in three parts, one producer that always wants to run at about twice the consumer's rate, and three different queues between them. Part 1 uses an unbounded queue and samples the depth over time while it climbs. Part 2 caps the queue and uses a blocking `put`, so the producer is forced down to the consumer's rate and the depth goes flat. Part 3 caps the queue and sheds the excess with a non-blocking `put` that catches `queue.Full`, and counts accepted versus shed.

Standard library only, `queue` and `threading` and `time`. It runs in about 12 seconds, joins every thread, and leaves no files behind.

### Predict first

Fill in `PREDICTIONS` at the top of the file. The producer offers a job about every 2 ms (roughly 500 a second) and the consumer takes about 4 ms per job (roughly 250 a second), and each part runs for 3 seconds.

- P1. The unbounded queue, producer at about twice the consumer, for 3 seconds. Roughly how many jobs are backed up at the end?
- P2. Cap the queue at 50 and let `put` block. Roughly what queue depth do you see then, held steady?
- P3. By what factor does backpressure cut the producer's output versus the unbounded run? (jobs placed when unbounded, divided by jobs placed when bounded)
- P4. Switch to shedding at the same offered load. Of the roughly 1,200 jobs offered, how many get shed?

P1 is the one to feel in your gut. The producer adds about 250 a second more than the consumer removes, for 3 seconds. P3 is the one that teaches: write down what you think "forced to the consumer's rate" does to a producer that wanted to go twice as fast.

### Fill in the TODOs

1. TODO 1 is the unbounded offer, `q.put_nowait(item)`. The point is that it never blocks and never refuses. That "yes to everything" is what lets the backlog grow without bound.
2. TODO 2 is Little's Law for this queue, `wait_s = depth / consume_rate`. One line, straight from Day 4, and it turns a deep queue into a scary number of seconds.
3. TODO 3 is the blocking offer, `q.put(item, timeout=timeout)`. This one call is backpressure: when the queue is full it parks the producer until a slot frees up.
4. TODO 4 is the shed, the `except queue.Full` branch that returns "no" instead of queuing. The fast 429.

The comments above each TODO show the exact shape. If a TODO is still blank, the lab tells you which one and stops cleanly, it does not hang.

```bash
cd labs/day-27-backpressure
python3 backpressure.py
```

### What you're going to discover

Part 1 is the trap. The depth curve is a straight line up, 100, 200, 300, 400, 500, and nothing errors the whole time. Then Little's Law tells you a new job is already waiting almost 3 seconds, and that number only grows. This is the slow-motion outage, and it looks completely healthy until it isn't.

Part 2 is the relief, and the surprise in it is how little you had to do. One blocking `put` and a cap, and the depth goes flat at 50 and stays there. The producer that wanted 500 a second is now doing about 220, pinned to the consumer. You did not configure a rate limit. The full queue did it for you.

Part 3 is the choice you make when you cannot block the producer. Same flood, but now the excess gets a fast no. The consumer finishes the same amount of real work as in Part 2, the accepted jobs keep a short bounded wait, and a few hundred offers are turned away in microseconds instead of piling up in memory.

### Traps ⚠️

- The exact counts move a little run to run, because real threads and real `sleep` are never perfectly on time. The contrast is what is solid: unbounded climbs past 500, bounded sits flat at the cap of 50, shedding turns away a few hundred. Trust the shape, not the third digit.
- Part 1's "final depth" is the backlog at the moment the producer stops, which equals offered minus finished. It is not the queue draining, it is the queue that never got drained.
- In Part 2 the producer looks "slow," about 1.8x fewer jobs placed than in Part 1. That is not a bug, that is the whole point. Backpressure made the fast producer match the slow consumer.
- If your absolute numbers are far off (say your machine's timer is coarse), look at the three parts relative to each other, not at the exact values. The lesson is in the comparison.

### Deliverable

[`labs/day-27-backpressure/RESULTS.md`](../labs/day-27-backpressure/RESULTS.md) has a skeleton. Paste the output, and write one line: how deep did the unbounded queue get and what did Little's Law say about the wait, and which policy, backpressure or shedding, would you pick for a user-facing API, and why.

---

## Block 4: write (30 min) 📣

Your angle today is the trap: "I put an unbounded queue in front of a slow consumer and watched the backlog climb in a straight line while every dashboard stayed green. Then I bounded it and the problem went away." The depth-over-time curve, straight line versus flat line, is the screenshot.

Example posts are on the [Day 27 posts](../shares/day-27-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the unbounded queue's final depth and the Little's Law wait it implied, and one thing you still cannot explain.

Day 28 is the week's design day. You put the whole of week 4 together, a queue, a log, delivery semantics, and today's backpressure, into one async system under a timer. Today you learned the two ways a system survives more work than it can do. Tomorrow you decide where they go.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The queue gains 500 minus 300 = 200 jobs every second. Over 10 minutes (600 seconds) that is 200 times 600 = 120,000 jobs backed up. A job joining the back waits depth divided by drain rate = 120,000 / 300 = 400 seconds, almost 7 minutes, before it is even picked up. And it only gets worse: a second later the queue is 200 deeper and the wait is longer. Because arrivals exceed service, there is no steady state. Little's Law gives a finite answer only for a stable system, and this one is not, so L and W diverge together. That is the unbounded queue's real failure mode, not an error but an unbounded climb.

D2. The worst-case wait is the cap divided by the drain rate, so to keep it under 300 ms you need cap / 200 ≤ 0.3, which gives cap ≤ 60 jobs. Cap it around 60. If you set it to 10,000, the worst-case wait becomes 10,000 / 200 = 50 seconds, about 166 times your SLA. The big queue does not add safety, it adds latency: it lets the system accept work it cannot serve in time, so under overload every accepted job can wait up to 50 seconds instead of being turned away fast. The queue bound is the latency bound. A queue sized "to be safe" is a 50-second bug waiting for a busy afternoon.

D3. The handler thread blocks inside `put()`, so it is tied up and serving no one. The web server has a fixed pool of handler threads, and as more requests arrive and block on the full queue, the pool fills with parked threads. New requests now wait for a free handler, so the server's accept queue (the socket backlog) grows, and then the server stops accepting, or clients time out and retry, which adds load. So backpressure reached the user as responses that got slow, then connections that got refused. A blocked producer is worse than a dropped request when the producer is a shared, limited resource like a request thread: one slow downstream queue freezes the whole front end through head-of-line blocking, where a dropped request would have freed the thread at once. This is why user-facing front ends usually shed rather than block.

D4. You shed 1,000 minus 400 = 600 requests per second with a 429. Each shed costs about 1 percent of serving one, so 600 sheds per second cost the equivalent of about 6 served requests, which is 6 / 400 = roughly 1.5 percent of your capacity. Shedding burns almost nothing and leaves about 98.5 percent of capacity for real work, so you keep serving 400 a second at a bounded latency. If you queued the 600-per-second excess instead, the queue and the latency would grow without bound (see D1), memory and timeouts would eventually take the service down, and you would end up serving fewer than 400. A cheap no preserves good service for the 400 you can handle. The unbounded yes loses everyone.

D5. Internal batch ETL from Kafka: block, backpressure. Kafka is durable and patient, no user is waiting, and losing data is bad, so let the slow consumer slow the read down and Kafka holds the offset. User-facing checkout API in a flash sale: shed, a 429 with a retry hint, or a controlled waiting room. A human is holding a connection, blocking ties up threads and shows a spinner, so admit a trickle and turn the rest away fast. Logging and metrics pipeline: shed, drop or sample. Telemetry is lossy-tolerant, and logging must never backpressure the application it is observing, so drop samples rather than stall the hot path. Payment webhook receiver: accept fast to durable storage and return quickly, and when truly overloaded return a 429 or 503 so the sender retries. You must not silently drop a payment event, so here "shedding" means telling the sender to come back, not discarding, and the sender's retries are your backstop. The thread through all four: shed when a human or a shared thread is waiting, lean on backpressure when the producer is durable and patient, and in every case assume you normally run below 100 percent so these only fire at the edge.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-27-backpressure/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-27-backpressure/solution.py).

TODO 1, the unbounded offer, the "yes to everything" that lets the backlog grow without bound:

```python
q.put_nowait(item)
placed = True
```

TODO 2, Little's Law for this queue, straight from Day 4, turning a deep queue into seconds of waiting:

```python
wait_s = depth / consume_rate
```

TODO 3, the blocking offer, which is backpressure in one line: a full queue parks the producer until a slot frees up:

```python
q.put(item, timeout=timeout)
placed = True
```

TODO 4, the shed, the fast no that returns instead of queuing when the queue is full:

```python
shed = True
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. Three parts, each a 3-second run. Your exact counts will differ a little, the contrast will not.

```
==============================================================================
Part 1: the unbounded queue. Producer at ~2x the consumer, no limit.
==============================================================================
  jobs offered (all accepted):       1199
  jobs the consumer finished:        612
  jobs still stuck in the queue:      587
  queue depth over time:
    t= 0.0s  depth=    0  
    t= 0.5s  depth=  101  ########
    t= 1.0s  depth=  199  ###############
    t= 1.5s  depth=  300  #######################
    t= 2.0s  depth=  399  ##############################
    t= 2.5s  depth=  501  ######################################
  consumer drains about 204 jobs/sec, so by Little's Law a
  job joining the back now waits 2.9s to be picked up, and that
  wait grows every second the producer keeps running. Nothing errored.
  Memory and latency just climb until something falls over. This is the
  slow-motion outage an unbounded queue hides.

==============================================================================
Part 2: a bounded queue. put() blocks when full, so backpressure bites.
==============================================================================
  jobs the producer managed to place: 658
  jobs the consumer finished:        608
  queue depth at the end:             50  (cap is 50)
  average queue depth while running:  49.9
  queue depth over time:
    t= 0.0s  depth=    0  
    t= 0.5s  depth=   50  ##########################################
    t= 1.0s  depth=   50  ##########################################
    t= 1.5s  depth=   50  ##########################################
    t= 2.0s  depth=   50  ##########################################
    t= 2.5s  depth=   50  ##########################################
  producer rate 219/s vs consumer rate 203/s: the blocking
  put() pinned the fast producer to the consumer's pace. The queue
  filled to its cap of 50 and stayed there. Backpressure travelled
  upstream and the backlog stopped growing. No outage, just a slower
  producer, which is the whole point.

==============================================================================
Part 3: load shedding. Full queue? Reject fast (a 429), do not queue.
==============================================================================
  jobs offered:                       1201
  jobs accepted (fit in the queue):   664
  jobs shed fast (the 429s):          537
  queue depth at the end:             49  (cap is 50)
  queue depth over time:
    t= 0.0s  depth=    0  
    t= 0.5s  depth=   50  ##########################################
    t= 1.0s  depth=   49  #########################################
    t= 1.5s  depth=   49  #########################################
    t= 2.0s  depth=   50  ##########################################
    t= 2.5s  depth=   49  #########################################
  the consumer still finished 615 jobs, same as under backpressure.
  The ones it could not get to were turned away in microseconds, not
  parked in memory. Accepted jobs kept a bounded, predictable wait; the
  rest got an instant honest 'no'. That fast no is what keeps the system
  standing when the unbounded 'yes' would have buried it.

==============================================================================
Scoreboard
==============================================================================
  P1 unbounded final depth       you =   600.0   actual =    587.0        close enough
  P2 bounded final depth         you =    50.0   actual =     50.0        close enough
  P3 backpressure throttle       you =     2.0   actual =      1.8 x       close enough
  P4 shed count                  you =   500.0   actual =    537.0        close enough

==============================================================================
The number to carry
==============================================================================
  Same producer, same slow consumer, three different queues.
  Unbounded:    backlog ran to 587 and a new job waited 2.9s, climbing.
  Bounded:      backlog held flat at 50 (cap 50); the producer was
                throttled 1.8x down to the consumer's rate.
  Load shedding: 537 jobs got a fast 429 so the rest kept a bounded wait.
  An unbounded queue does not absorb overload, it defers the outage and
  makes it worse. Bound the queue, then choose: block the producer
  (backpressure) or reject the excess (shedding). Day 4's rule holds:
  run below 100 percent and keep the queue bounded.
```

Part 1 is the day. The depth climbs in a straight line, 101, 199, 300, 399, 501, and by the end 587 jobs are stuck. Nothing failed. No exception, no rejection, every offer accepted. That is exactly what makes it dangerous. Little's Law turns the 587-deep queue into a wait: at about 204 drained per second, a job joining now waits 587 / 204 = 2.9 seconds to be picked up, and a second later it is worse. Memory holds every one of those unfinished jobs, and the wait only grows. This is the outage that looks healthy right up until the process runs out of memory.

Part 2 is the fix that costs one line. Cap the queue at 50, use a blocking `put`, and the depth snaps to 50 and stays there. The producer that wanted 500 a second is now doing about 219, matched to the consumer's 203. Backpressure did that, not a rate limiter you tuned. A full queue and a blocking call forced the fast producer to wait for the slow consumer, and the backlog simply stopped growing. The producer is slower now, and that is the entire point.

Part 3 is the choice for when the producer will not wait. Same flood, 1,201 offered, but the queue is capped and the excess is rejected the instant it does not fit. 537 jobs got a fast no, 664 were accepted, and the consumer finished 615, the same real work as under backpressure. The difference is where the excess went: not into memory to rot, but back to the caller in microseconds. The jobs you kept stayed fast.

The one line to carry out of today: an unbounded queue does not absorb overload, it hides it and makes it worse. Bound the queue, then decide per system whether to push back on the producer or turn the excess away. And run below 100 percent so you rarely have to.

</details>
