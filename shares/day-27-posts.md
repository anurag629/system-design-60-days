---
title: "Day 27 posts"
parent: "Day 27: backpressure and load shedding"
grand_parent: "Week 4: async, queues and the log"
nav_order: 3
---

# Day 27 posts: LinkedIn and X

The depth-over-time curve makes the screenshot: the unbounded queue climbing in a straight line while the bounded one sits flat at its cap. Swap in your own numbers and voice.

## LinkedIn

Day 27 of 60 days of system design. Today I learned, by measuring it, that an unbounded queue is not a safety net. It is a slow-motion outage.

I wired up a producer that offers jobs about twice as fast as a single consumer can finish them, and ran it three ways with three different queues between them.

First, an unbounded queue. It accepts everything, so the backlog just grows:

    t=0.5s  depth=101
    t=1.0s  depth=199
    t=1.5s  depth=300
    t=2.0s  depth=399
    t=2.5s  depth=501

A straight line up. By the end about 587 jobs were stuck waiting. The consumer drains roughly 200 a second, so by Little's Law (Day 4) a job joining the back now waits almost 3 seconds to even be picked up, and that wait grows every second the producer keeps running. Nothing errored. Memory and latency just climb until something falls over.

Then I capped the queue at 50 and used a blocking put(). Now when the queue is full the producer is forced to wait for a free slot. The depth went flat and stayed at 50, and the producer slowed down to exactly the consumer's rate. That is backpressure: the "I am full" signal travels upstream and throttles the source. The fast producer became a 1.8x slower producer, and the system stopped digging its own grave.

But real user requests do not wait politely for a slot. So the third run rejected the excess instead of queuing it, the moral equivalent of returning HTTP 429. Of about 1,200 jobs offered, 537 got a fast "no" and the rest kept a short, bounded wait. The consumer still finished the same amount of real work. A quick, honest rejection protected the system where the unbounded "yes" would have buried it.

The one rule, straight from Day 4: run below 100 percent, and keep the queue bounded. Then decide, per system, whether to block the producer or shed the load.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #backpressure #learninginpublic

## X thread

**1/**

Day 27 of 60 days of system design.

An unbounded queue is not a safety net. It is a slow-motion outage. I measured it on my own laptop today.

**2/**

A producer offering jobs at ~2x what one consumer can drain, into an unbounded queue. The backlog just climbs:

    t=0.5s depth=101
    t=1.0s depth=199
    t=1.5s depth=300
    t=2.0s depth=399
    t=2.5s depth=501

A straight line. Nothing errors. It just gets worse.

**3/**

By Little's Law (Day 4), a job joining the back of a 587-deep queue drained at ~200/sec waits ~3 seconds before it is even picked up, and that wait grows every second. Memory and latency climb until something topples.

**4/**

Fix one: cap the queue at 50 and use a BLOCKING put().

Now a full queue makes the producer wait for a slot. Depth went flat at 50. The producer dropped to the consumer's exact rate.

That is backpressure: "I'm full" travels upstream and throttles the source.

**5/**

But incoming user requests do not wait politely.

Fix two: reject the excess fast (an HTTP 429) instead of queuing it.

Of ~1,200 jobs offered, 537 got an instant "no". The rest kept a short, bounded wait, and the consumer did the same real work.

**6/**

A fast "no" protects the system. An unbounded "yes" kills it slowly.

The rule from Day 4 holds: run below 100%, keep the queue bounded, then choose block (backpressure) or shed (429).

Code: github.com/anurag629/system-design-60-days
