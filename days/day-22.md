---
title: "Day 22: sync vs async, and why queues exist"
parent: "Week 4: async, queues and the log"
nav_order: 1
has_children: true
---

# Day 22
## Sync vs async, and why queues exist, or how to hand the work to someone else and walk away 📨

Today's one idea: there are two ways to do a slow piece of work. You can do it yourself and wait for it to finish, which is synchronous. Or you can hand it to a queue and carry on with your life, letting a worker pick it up and do it later, which is asynchronous. The queue is the small, boring thing that sits in between and lets a fast caller and a slow worker run at completely different speeds. Once this clicks, a surprising amount of backend design turns out to be one question asked over and over: does this have to happen now, or can I hand it off?

Think about tapping "Pay" on a Swiggy order. 🍔 The second you tap, a pile of things need to happen: charge your card, tell the restaurant, find a delivery partner, send you an SMS, update some dashboard somewhere. If your screen had to wait for all of that to finish before it said "Order placed", you would sit staring at a spinner for ten seconds every single time. Instead the order goes onto a queue, your screen says done at once, and the rest happens in the background. Today you build that exact move on your own machine and measure both sides of it.

---

## Before you start ⏪

You need Day 6's comfort with threads, because that is all a worker is here: a thread that sits in a loop, pulls a job off a queue, and does it. No Redis, no RabbitMQ, no Kafka yet. The whole lab is Python's standard library, `queue.Queue` and `threading`, with a `time.sleep` standing in for the slow work and a tiny SQLite table so you can prove afterwards that every job really did get done.

Keep one thing from last week in your pocket too. In week 3 the danger was a cache going cold under load. This week the move is different: instead of making the work faster, you take the caller off the hook for waiting on it at all. Same slow work, different question about who has to stand there while it runs.

---

## Words you will meet today 📖

Synchronous work is work the caller does and waits for. You call a function, it runs, it returns, and only then do you get your next line of code. The caller's latency is the whole job, every time.

Asynchronous work is work the caller hands off and does not wait for. You drop the job somewhere and return immediately. The job still runs, but on someone else's time, and you find out it finished later (or you never look).

A producer is whoever creates work and puts it on the queue. In the Swiggy picture it is the app server handling your tap. A consumer, or worker, is whoever takes work off the queue and actually does it. One queue can have many producers and many workers.

A queue here is a buffer that holds jobs waiting to be done, in order, first in first out. It lets the producer run ahead of the consumer: the producer drops jobs and leaves, the consumer takes them at its own slower pace, and the queue holds the difference.

Latency is how long one caller waits for one thing. Throughput is how many things the whole system finishes per second. They are not the same number, and today's lab pulls them apart on purpose: async slashes the caller's latency without touching throughput at all.

Backpressure is what a full queue does to a producer that is going too fast. If the queue can only hold so much and the consumer is behind, the producer's `put()` is made to wait. That waiting is the system pushing back, saying slow down, I cannot take more right now.

A bounded queue has a maximum size and therefore gives you backpressure. An unbounded queue has no limit, so it never pushes back. That sounds friendlier and it is actually more dangerous, because it hides overload until you run out of memory.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these:
- [`queue`, a synchronized queue class](https://docs.python.org/3/library/queue.html) in the Python docs. This is the exact tool the lab uses. Read the top section and the methods `put`, `get`, and the note on `maxsize` and blocking. It is short, and seeing that the whole producer-consumer pattern ships in the standard library tells you how fundamental it is.
- [What is a message queue?](https://aws.amazon.com/message-queue/) by AWS. The production framing of what you build today: decoupling a producer from a consumer, absorbing spikes, and letting each side scale on its own. Ignore the SQS sales pitch at the end and keep the first half.
- [Asynchronous messaging options](https://learn.microsoft.com/en-us/azure/architecture/guide/technology-choices/messaging) in the Microsoft architecture guide. A clear map of the shapes async communication can take (queues, topics, pub-sub). You only need the "message queues" idea today, but it helps to see where it sits.

Watch:
- [What is a MESSAGE QUEUE and Where is it used?](https://www.youtube.com/watch?v=oUJbuFMyBDk) by Gaurav Sen, about 10 minutes. A friendly overview of why a queue goes between two services and what it buys you. Good to watch before the lab.
- [Synchronous and Asynchronous Communication between Microservices](https://www.youtube.com/watch?v=ewUw0sUxHI4) by Arpit Bhayani, about 40 minutes. A deeper, careful walk through exactly today's fork in the road, when each one is right, and the costs async quietly adds. Save it for after the lab.

### Synchronous: do it yourself, and wait (13 min)

Start with the honest, simple way, the way almost every function you have ever written works. A request comes in. You do the work. You return the answer. The caller waited the whole time.

There is nothing wrong with this. It is easy to reason about, the stack trace is one straight line, and when the function returns you know for certain the work is done. For a read that fills a web page, this is exactly right: the user is literally waiting to see the data, so you may as well fetch it and hand it over.

The trouble starts when the work is slow and the caller does not actually need to wait for it. Picture the Swiggy server handling your tap on "Pay". Suppose it does five things in a row, inline: charge the card (120 ms), tell the restaurant (80 ms), find a rider (200 ms), send the SMS (60 ms), update analytics (40 ms). Done synchronously, your "Order placed" screen cannot appear until all five finish. That is 500 ms of staring, and every one of those steps is a different service that might be slow or flaky today. The user is held hostage to the slowest thing in the chain, for work they do not need to see finish.

In Part 1 of the lab you measure this directly. A caller runs a 50 ms job inline, and you time it. The answer is not a surprise, it is the point: the caller's latency is the whole job, about 50 ms, every single call. Whatever the work costs, the caller pays it in full.

### Asynchronous: hand it off, and walk away (13 min)

Now the move. Instead of doing the slow work, the caller writes down "please do this job" on a queue and returns immediately. A separate worker thread sits in a loop, pulls jobs off the queue one by one, and does them. The producer and the consumer are now decoupled: they do not run at the same speed, they do not even run at the same time.

Watch what happens to the caller's latency. It is no longer the 50 ms job. It is just the cost of dropping a job on the queue, which is a few microseconds. In the lab you will see something like 50 ms collapse to around 0.001 ms. That is roughly fifty thousand times faster, on the same machine, for the same work.

And here is the sentence to sit with, because it is the one people get wrong: the work did not get faster. Each job still takes 50 ms. Nothing was optimised. The 50 ms simply moved off the caller's thread and onto the worker's thread. The caller stopped waiting, that is the entire change. In the lab the worker still grinds through all twenty jobs, still takes a full second of wall-clock time to finish them, and every order still lands in the database. You just are not standing there while it happens.

This is why it is worth separating two words that get muddled. Latency is what one caller waits. Throughput is how many jobs the system finishes per second. Async crushes the caller's latency and does nothing at all for throughput: one worker doing 50 ms jobs still finishes twenty a second whether you call it sync or async. If you want more throughput, you add more workers, and the queue happily feeds all of them, until you hit the real bottleneck behind the work (the database, the payment gateway, the CPU). The queue moves the waiting around. It does not conjure capacity.

### The queue is a buffer, and buffers fill up (12 min)

The real reason a queue earns its place is not a single call. It is a crowd of them. Traffic is spiky. A burst of orders lands in one second, then a quiet stretch, then another burst. A synchronous server meets a burst by making every caller wait in line behind the slow work. A queue meets the same burst by swallowing it.

In Part 3 you fire a burst of forty jobs at the async queue all at once, with one worker draining at 50 ms each. All forty callers return in well under a millisecond, because each one just dropped its job and left. The queue depth shoots up to forty, and then drains back down to zero over about two seconds as the worker chews through the backlog. You sample the depth and watch it rise and fall. Nobody queued up behind the worker. The queue did, and the callers went free.

That smoothing is the gift, but it has a floor, and the floor is simple arithmetic. Call the arrival rate lambda and the service rate mu. If arrivals come in faster than the worker can serve them, on average and for long enough, the queue does not smooth anything, it grows without bound. Forty jobs drained fine because the burst was finite. But if a producer sends 100 jobs a second forever and one worker can only do 50 a second forever, the backlog climbs for the rest of time, and with it the wait for every job at the back. There is a tidy way to hold this in your head, Little's Law: the average number of jobs sitting in the system equals the arrival rate times how long each one spends there. When arrivals outrun service, that number has no ceiling. The honest fix is never "a bigger queue". It is more workers or less load.

### Backpressure: when the queue says slow down (12 min)

So what should a queue do when it is full and the producer keeps pushing? This is where bounded and unbounded part ways, and it matters more than it first looks.

An unbounded queue never says no. Push as fast as you like and it keeps accepting, quietly, while the backlog and the memory behind it climb. It feels generous. It is actually the dangerous one, because it hides the lambda-greater-than-mu problem right up until the process runs out of memory and dies, usually at the worst possible moment, under the heaviest load. A queue that can never reject is a queue that fails all at once instead of early.

A bounded queue has a cap, and the cap is what gives you backpressure. In Part 4 you make a queue that holds only five waiting jobs and fire forty at it. The first few go in instantly. Then the queue is full, and every `put()` after that blocks: it cannot return until the worker takes one and frees a slot. In the run you will see roughly 34 of the 40 puts forced to wait. The producer is no longer allowed to run ahead; it is dragged down to the worker's pace. That blocking is not a failure, it is the queue telling the producer, in the only language it has, slow down, I am full.

When a real system hits a full queue it has three honest choices, and it is worth knowing all three. It can block the producer, which is what today's lab does and what a thread pool with a bounded work queue does. It can reject fast and tell the caller to try again later, which is an HTTP 429 or load shedding. Or it can drop something on purpose, the oldest item or a random sample, which is what metrics and logging pipelines do when they would rather lose a data point than fall over. Blocking, rejecting, dropping. Pick one deliberately. The one trap is pretending there is a fourth option where you store everything forever, because that is just an unbounded queue, and it only defers the choice to the day you run out of memory.

This is IRCTC at 10 AM when tatkal opens. 🚆 A flood of requests arrives in one minute, far faster than the booking system can confirm seats. The system cannot magically confirm them all at once, so something has to give: you wait in a queue, or you get a "please try again" and come back, or the request is dropped. What you do not want is a system that silently accepts ten lakh requests into an unbounded buffer and then falls over with all of them half-done. Backpressure is how a system stays up by admitting its limits. You get the full treatment on Day 27; today you just feel it push back once.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-22-drills.md`](../notes/day-22-drills.md).

D1. A request does four slow side effects inline before it replies: charge the card (120 ms), notify the restaurant (80 ms), find a rider (200 ms), send the SMS (60 ms). What is the user-visible latency done synchronously? If the request instead enqueues all four and returns, with one worker doing them serially, what does the user see and how long does the work actually take? What changed, and what did not?

D2. Making the caller async did not make the work any faster. Define latency and throughput, explain why a queue plus one worker slashes the first but not the second, say when adding workers raises throughput, and name what sets the ceiling.

D3. A queue gets arrivals at lambda = 100 per second and one worker serves at mu = 50 per second. What happens to the queue depth over time? Now lambda = 30 and mu = 50: is it stable, and roughly why? Using Little's Law, L = lambda times W, explain why an unbounded queue hides the lambda-greater-than-mu problem instead of solving it.

D4. A bounded queue of maxsize M is full and a producer calls `put()`. List the three things the queue could do, give a real system for each, and say what the producer should do in response to each.

D5. Async plus a queue is not free. Give two concrete costs it adds to a system, and name one kind of operation where the synchronous answer is the right one.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-22-queues/async_queue.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-22-queues/async_queue.py).

It is in four parts. Part 1 runs a 50 ms job synchronously, inline, and times the caller. Part 2 hands the same job to a queue with a background worker and times the caller again, plus the end-to-end completion. Part 3 fires a burst of forty jobs and samples the queue depth rising and then draining. Part 4 makes the queue bounded and watches `put()` block, which is your first taste of backpressure.

Standard library only: `queue`, `threading`, `sqlite3`, `time`. The slow job is a `time.sleep` plus one SQLite row, so afterwards you can count the rows and see every job really ran. The whole thing finishes in well under a minute and cleans up every file it makes.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The synchronous caller does the slow job inline. Its latency is the whole job. How many milliseconds is one call? (The job sleeps 50 ms.)
- P2. The asynchronous caller just drops the job on the queue and returns. Its latency is only the enqueue. Bet an upper bound in milliseconds: you are saying "the enqueue stays under this".
- P3. Fire a burst of forty jobs into the async queue at once, with one worker draining at 50 ms each. How deep does the queue get at its peak?
- P4. Now a bounded queue of maxsize five, a fast producer, the same slow worker. Of the forty puts, how many have to block and wait because the queue was full?

P2 is the one to feel in your gut first. You know the job is 50 ms. Write down how long you think it takes to just put a job on a queue, before you measure it. The gap between P1 and P2 is the whole lesson.

### Fill in the TODOs

1. TODO 1 is the synchronous caller doing the job inline. This one line is why its latency is the whole job.
2. TODO 2 is the async move: drop the job on the queue and return. The caller never touches the slow work.
3. TODO 3 is the worker pulling the next job off the queue. `get()` blocks until there is one, so an idle worker sleeps for free.
4. TODO 4 is the bounded queue. The maxsize is the entire source of backpressure, so this is where "slow down" comes from.

```bash
cd labs/day-22-queues
python3 async_queue.py
```

### What you're going to discover

Part 1 is the baseline, and it is exactly what you expect: the caller waits about 50 ms per call, because it is doing the work itself. No trick, just the honest cost.

Part 2 is the jump. The same job, called async, returns in around 0.001 ms. That is the caller handing off a job and walking away. The end-to-end line underneath it is the honest footnote: the work still took a full second to finish on the worker, and every order still made it into the database. Nothing got faster. The waiting moved.

Part 3 is the buffer. Forty callers all return in under a millisecond, and the queue depth jumps to forty and then slides back to zero over about two seconds as the one worker drains it. You will see the little depth chart rise and fall. That is a spike absorbed instead of forty people made to wait in line.

Part 4 is the push-back. On a queue that holds only five, most of the forty puts block, because once it is full the producer cannot get ahead of the worker. The producer that fired forty jobs instantly in Part 3 now takes nearly two seconds, dragged down to the worker's pace. That is backpressure, and it is a feature, not a bug.

### Traps ⚠️

- If your async caller latency in Part 2 is not far smaller than Part 1, you have probably put the slow work on the caller's thread by mistake. The caller must only call `q.put(job)` and return. The 50 ms must happen on the worker, inside `do_slow_job`, nowhere near the enqueue timing.
- Always stop your worker. The lab sends a sentinel object down the queue to tell the worker there are no more jobs, then joins the thread with a timeout. If you invent your own worker loop, make sure it has a way to end, or your program will hang forever waiting on a thread that is still blocked on an empty `get()`.
- In Part 4 the point is that `put()` blocks on a full bounded queue. If you reach for `put_nowait()` instead, it will raise `queue.Full` rather than wait, which is a different (and also valid) backpressure choice, but it is not the one this part is measuring. Use the plain blocking `put()` here.
- The exact blocked-put count will wobble by one between runs (34 or 35), depending on whether the worker grabbed the very first job before the queue filled. That is fine. The lesson is "most of them blocked", not the third decimal.

### Deliverable

[`labs/day-22-queues/RESULTS.md`](../labs/day-22-queues/RESULTS.md) has a skeleton. Paste the output, and write one line: the synchronous caller waited about 50 ms, the asynchronous caller returned in about 0.001 ms, the queue absorbed a burst of forty, and a bounded queue blocked most of the puts. Then answer the one that matters: name an operation you would NOT make async, and why.

---

## Block 4: write (30 min) 📣

Your angle today is the measured jump: "I ran the same 50 ms job two ways. When the caller did it itself: 50 ms. When the caller dropped it on a queue and walked away: 0.001 ms. The work did not get faster, I just stopped waiting for it." The scoreboard, 50 ms next to 0.001 ms, is the screenshot.

Example posts are on the [Day 22 posts](../shares/day-22-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the sync-versus-async caller latency you measured and the one-line reason the work did not actually get faster, and one thing you still cannot explain.

Day 23 is the worker on the other side of the queue: what it means to actually process a job, what happens when it crashes halfway through, and why "I took the job off the queue" and "I finished the job" are two different events you must not confuse. Today you learned to hand work off. Tomorrow you learn to do it reliably on the receiving end.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Done synchronously, the user-visible latency is the sum, because the steps run one after another: 120 + 80 + 200 + 60 = 460 ms of staring at a spinner before "Order placed" appears. Done async, the request enqueues all four and returns, so the user sees "Order placed" in the time it takes to drop four jobs on a queue, a handful of microseconds. The work itself still takes about 460 ms on the worker (one worker, serial), it just happens after the user has moved on. What changed is who waits: the user no longer does. What did not change is the total work, the 460 ms still gets spent, and you have quietly accepted a new model where the SMS and the rider assignment land a moment after the screen says done.

D2. Latency is how long one caller waits for one job. Throughput is how many jobs the whole system completes per second. A queue plus one worker slashes latency, because the caller returns the instant it enqueues instead of waiting out the 50 ms. It does nothing for throughput, because the same single worker still does one 50 ms job at a time, twenty a second, async or not. Adding workers raises throughput: with N workers pulling from the same queue you finish roughly N times as many jobs per second. The ceiling is set not by the queue but by the real resource behind the work, the database, the payment API, the CPU, and by any ordering or locking that forces jobs to serialise. The queue redistributes waiting; it does not create capacity.

D3. With lambda = 100 and mu = 50, arrivals come in twice as fast as the single worker can serve them, so the queue depth climbs forever and the wait for a job at the back of the line grows without bound. The system is unstable, and no size of queue saves it, you need more workers or less load. With lambda = 30 and mu = 50, the worker is faster than the arrivals (utilisation is 30/50 = 0.6), so the queue stays finite and jobs clear in bounded time. Little's Law, L = lambda times W, says the average number of jobs in the system is the arrival rate times the time each one spends there. When lambda is below mu, W is finite so L is finite. When lambda exceeds mu, W grows without limit, so L does too. An unbounded queue hides this because it keeps accepting work it can never drain: instead of pushing back when lambda passes mu, it swallows the overload into memory, and latency balloons silently until the process dies. A bounded queue surfaces the same problem early, as backpressure, while you can still react.

D4. When a bounded queue of maxsize M is full and a producer calls `put()`, the three honest options are: block the producer until a slot frees (Python's `queue.Queue.put`, a thread pool with a bounded work queue, a bounded Go channel), in which case the producer naturally slows to the consumer's pace; reject and fail fast (`put_nowait` raising `Full`, an HTTP 429, load shedding at the edge), in which case the producer should back off and retry later or give up; or drop something on purpose (drop the newest, drop the oldest, or sample, as metrics, logging and UDP pipelines do), in which case the producer accepts that some data is lost. The move to avoid is an unbounded queue, which pretends there is a fourth option where you simply store everything, and only defers the failure to the moment you run out of memory.

D5. Two concrete costs async adds: first, eventual consistency, the caller gets "accepted" rather than "done", so you now need status tracking, callbacks or polling, and your UI has to show an "in progress" state and handle the job failing after the user has left. Second, operational complexity, a new component to run and watch (queue depth, worker health, a dead-letter queue for poison jobs), plus retries and the idempotency you need because a job can run more than once, and a harder time debugging since there is no single clean stack trace and ordering is no longer guaranteed. An operation that should stay synchronous is any one where the caller genuinely needs the result to proceed: a read that returns the data to render the page, a strong-consistency check like "is this username already taken" at signup, or a payment where the user must see success or failure before they leave the screen. If the answer has to be known now, synchronous is the correct choice.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-22-queues/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-22-queues/solution.py).

TODO 1, the synchronous caller doing the job inline. This is why its latency is the whole job:

```python
done = do_slow_job(conn, job)
```

TODO 2, the async move. Drop the job on the queue and return at once, the caller never touches the slow work:

```python
q.put(job)
```

TODO 3, the worker pulling the next job off the queue. `get()` blocks until one is there, so an idle worker waits for free:

```python
job = q.get()
```

TODO 4, the bounded queue. The maxsize is the whole source of backpressure:

```python
q = queue.Queue(maxsize=BOUND)
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop (M4 Pro), macOS, Python 3, 50 ms job.

```
==============================================================================
Part 1: synchronous. The caller does the slow job itself and waits.
==============================================================================
  jobs run:                          20
  average caller latency per job:     54.04 ms
  wall-clock time for all 20 jobs:    1080.8 ms
  orders persisted:                  20
  The caller runs the 50 ms job on its own thread, so it is stuck for
  the whole job every single time. Latency per call IS the work, and
  the jobs run one after another, so the total is just N times the job.

==============================================================================
Part 2: asynchronous. The caller drops the job on a queue and returns.
==============================================================================
  jobs enqueued:                     20
  average caller latency (enqueue):  0.0011 ms
  time for the caller to fire all 20:   0.025 ms
  end-to-end (last job finishes):    1077.9 ms
  orders persisted:                  20
  The caller touched the slow work zero times. It put each job on the
  queue in a few microseconds and was free. The 50 ms per job still
  happened, on the worker's thread, and every order still landed in
  the store. The work did not vanish; the caller just stopped waiting.

==============================================================================
Part 3: the queue as a buffer. A burst lands, the queue absorbs it.
==============================================================================
  burst size:                        40 jobs
  time to fire the whole burst:       0.040 ms  (callers all freed)
  peak queue depth:                  40
  time to drain the backlog:         2144.9 ms  (~40 x 50 ms)
  orders persisted:                  40
  queue depth over time (rose to the peak in microseconds, then fell
  as the worker chewed through it at one job per 50 ms):
    t=0.00s  depth=40  ########################################   <- burst just landed
    t=0.15s  depth=38  ######################################
    t=0.31s  depth=35  ###################################
    t=0.46s  depth=32  ################################
    t=0.61s  depth=29  #############################
    t=0.77s  depth=26  ##########################
    t=0.92s  depth=23  #######################
    t=1.08s  depth=20  ####################
    t=1.23s  depth=17  #################
    t=1.39s  depth=15  ###############
    t=1.54s  depth=12  ############
    t=1.70s  depth=9   #########
    t=1.85s  depth=6   ######
    t=2.00s  depth=3   ###
    t=2.14s  depth=0   (drained)
  The callers did not queue up behind the slow worker. They dropped
  their jobs and left, and the queue held the backlog for the worker.

==============================================================================
Part 4: backpressure. A bounded queue makes a fast producer wait.
==============================================================================
  bounded queue maxsize:             5
  jobs the producer fired:           40
  puts that returned instantly:      6  (the queue had room)
  puts that BLOCKED (backpressure):  34  (the queue was full)
  slowest single put:                  56.2 ms  (~one job of work)
  total time the producer took:      1814.9 ms
  orders persisted:                  40
  In Part 3 the unbounded queue let the producer dump everything and
  leave. Here the bound pushes back: once BOUND jobs are waiting, the
  producer cannot run ahead of the worker, so put() blocks and the
  producer moves at the worker's pace. That is backpressure, the
  queue's way of saying slow down. Full treatment on Day 27.

==============================================================================
Scoreboard
==============================================================================
  P1 sync caller latency           you =     50.0   actual =       54.0 ms       close enough
  P2 async caller latency (<= bet) you =   1.0000   actual =     0.0011 ms       close enough
  P3 burst peak depth              you =       40   actual =         40        close enough
  P4 backpressure blocked puts     you =       35   actual =         34        close enough

==============================================================================
The number to carry
==============================================================================
  Synchronous, the caller waited the whole job: 54.0 ms per call.
  Asynchronous, the caller just enqueued:       0.0011 ms per call.
  Same work, same machine. The caller got about 50,864x faster by
  handing the job to a queue and walking away. The work did not get
  cheaper, it moved off the caller's thread, and the queue held the
  backlog so a burst did not make every caller wait. Bound that queue
  and it pushes back: 34 of 40 puts had to wait. That is backpressure.
```

Part 1 is the baseline. Twenty jobs, 50 ms each, done inline, and the caller waits about 54 ms every time. The few extra milliseconds over 50 are the SQLite write and thread scheduling, nothing to read into. The caller pays the full cost of the work because the caller is the one doing it.

Part 2 is the jump that makes queues worth having. The same 50 ms job, called async, returned in about 0.001 ms, because the caller only dropped the job on the queue and left. Look at the end-to-end line though: the worker still spent about 1.08 seconds finishing all twenty, and all twenty orders still landed in the database. The work did not shrink. It moved off the caller's thread. That is the only thing that happened, and it is enough to turn a 54 ms wait into a microsecond.

Part 3 is why a queue beats just spawning a thread per request. A burst of forty jobs arrived at once, every caller returned in well under a millisecond, and the queue held the backlog, its depth rising to forty and then draining to zero over about two seconds at the worker's steady one-job-per-50-ms pace. The spike was absorbed by the queue instead of being paid for by forty waiting callers.

Part 4 is the first taste of the limit. On a queue that can hold only five, thirty-four of the forty puts blocked, because a full bounded queue makes the producer wait for the worker to free a slot. The producer that dumped forty jobs instantly in Part 3 was dragged out to nearly two seconds here. That blocking is backpressure, the queue refusing to let a fast producer outrun a slow consumer, and it is the honest alternative to an unbounded queue that would have swallowed all forty and hidden the imbalance until something broke. Day 27 is the full story.

The one line to carry out of today: async does not make the work cheaper, it changes who has to wait for it, and a bounded queue is the part that is honest about how much waiting the system can actually hold.

</details>
