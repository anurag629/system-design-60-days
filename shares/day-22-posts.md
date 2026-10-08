---
title: "Day 22 posts"
parent: "Day 22: sync vs async, and why queues exist"
grand_parent: "Week 4: async, queues and the log"
nav_order: 3
---

# Day 22 posts: LinkedIn and X

The scoreboard makes a good screenshot: the same job took 54 ms when the caller did it itself, and 0.001 ms when the caller just dropped it on a queue. Swap in your own numbers and voice.

## LinkedIn

Day 22 of 60 days of system design. Week 4 starts, and the first idea is the one behind an enormous amount of real architecture: hand the work to someone else and walk away.

I wrote a 50 ms "job" (a sleep plus a database write, standing in for charge the card, call the shipping API, render the page). Then I called it two ways on the same machine.

Synchronous, the caller does the job itself and waits:

    average caller latency per job:   54.0 ms

Asynchronous, the caller drops the job on a queue and a background worker does it:

    average caller latency (enqueue):  0.001 ms

That is about fifty thousand times faster for the caller. And here is the part that took me a second to really accept: the work did not get any faster. Each job still takes 50 ms. It just moved off the caller's thread onto the worker's. The caller stopped waiting, that is all. Every order still landed in the database.

Then I fired a burst of 40 jobs at once. With the queue in front, all 40 callers returned in well under a millisecond and the queue held the backlog, its depth rising to 40 and then draining over two seconds at the worker's pace. Nobody queued up behind the slow worker. The queue did.

Last part was my first taste of backpressure. I made the queue bounded (it can hold only 5 waiting jobs) and fired 40 at it. Now 34 of the 40 puts had to block and wait, because once the queue is full, put() cannot return until the worker frees a slot. That blocking is the queue telling a fast producer to slow down. It is not a bug, it is the feature. (Full treatment on Day 27.)

The thing to remember: async does not make work cheaper, it changes who waits. And a bounded queue is honest about its limits, while an unbounded one just hides the problem until you run out of memory.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #queues #async #learninginpublic

## X thread

**1/**

Day 22 of 60 days of system design.

Same 50 ms job, same machine, two ways to call it:

caller does it itself:        54.0 ms
caller drops it on a queue:    0.001 ms

~50,000x faster for the caller. But the work did not get faster. Read on.

**2/**

The job still takes 50 ms every time. Async did not make it cheaper. It moved the work off the caller's thread onto a background worker's thread.

The caller stopped waiting. That is the entire trick. The order still got processed, still hit the database.

**3/**

This is a Swiggy order. You tap Pay, the screen says "Order placed" instantly. Charging the card, pinging the restaurant, finding a rider, SMS: all dropped on a queue, done by workers later. You did not wait for it. It still happened.

**4/**

Then I fired 40 jobs at once.

All 40 callers returned in under a millisecond. The queue absorbed the burst: depth rose to 40, then drained over 2 seconds at one job per 50 ms.

Nobody queued behind the slow worker. The queue did.

**5/**

Last bit: backpressure.

I made the queue bounded (holds only 5). Fired 40 at it.

34 of the 40 puts BLOCKED. Once the queue is full, put() can't return until the worker frees a slot.

That blocking is the queue saying "slow down". It's the feature.

**6/**

So:

async = change who waits, not how much work there is.
unbounded queue = hides overload until you OOM.
bounded queue = honest, pushes back.

Measured all of it on my own laptop with pure stdlib (queue, threading).

Code: github.com/anurag629/system-design-60-days
