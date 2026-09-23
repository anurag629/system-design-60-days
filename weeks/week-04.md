# Week 4: async, queues and the log 📨

Days 22 to 28, Tue 2026-10-13 to Mon 2026-10-19.

So far everything you built was synchronous. Request comes in, you do the work, you send the answer, the caller waits. Simple and honest. But some work is too slow, too spiky, or too important to lose, and for that you need to break the chain. The caller drops the job in a queue and walks away. Someone else picks it up later. This one move, doing work later instead of now, is behind a huge amount of real-world architecture.

Think about placing a Swiggy order. 🍔 The moment you tap "Pay", a dozen things need to happen: charge the card, tell the restaurant, find a delivery partner, send you an SMS, update analytics. If all of that had to finish before your screen said "Order placed", you would be staring at a spinner for ten seconds. Instead, the order goes into a queue, your screen says done instantly, and the rest happens in the background. That is this week.

The star of the week is the log. Not the "print debug statement" kind. The append-only log, the deceptively simple idea that you only ever add to the end and never edit the middle. Kafka is built on it. Databases use it internally, you met it in week 2 as the write-ahead log. Once the log clicks, a lot of distributed systems suddenly make sense.

## What you will be able to do by the end of the week

You can explain why a queue decouples a fast producer from a slow consumer, and what happens when the consumer cannot keep up. You know why "exactly-once delivery" is mostly a comforting lie and how idempotency keys give you the real thing anyway. You can draw the outbox pattern and say what problem it solves. You have personally killed a worker mid-job and watched the system heal.

## The days 🗓️

Day 22: sync vs async, and why queues exist. Decoupling, buffering a spike, and the scary word backpressure. Lab: a producer and consumer with a bounded queue between them.

Day 23: the log as a primitive. Append-only, offsets, and replay. The whole magic is that consumers remember their own position, so you can add a new consumer that re-reads all of history. Lab: build a tiny append-only log and a consumer that tracks its offset.

Day 24: Kafka's actual design. Partitions for parallelism, consumer groups for sharing work, and the ordering guarantee that only holds inside one partition. Lab: a partitioned log with a consumer group splitting the load.

Day 25: delivery semantics. At-least-once, at-most-once, and why exactly-once is more marketing than physics. The fix in practice is idempotency keys, the same idea that stops you getting charged twice when your UPI payment "fails" and you retry. 💸 Lab: crash a consumer, watch duplicates appear, then dedupe them cleanly.

Day 26: the outbox pattern and the dual-write problem. What goes wrong when you write to your database and publish to a queue as two separate steps, and one succeeds while the other fails. Lab: reproduce the inconsistency, then fix it with an outbox.

Day 27: backpressure and rate control. When consumers fall behind, the queue grows, memory fills, and things get ugly. What do you drop, slow, or push back on? Lab: a deliberately slow consumer, a growing queue, and backpressure applied.

Day 28: async design. You design a notification system or a payment pipeline, timed, then a retro.

## Core resources for the week 📚

Read:
- Kleppmann, *DDIA*, chapter 11 on streaming. The best single chapter on this topic anywhere.
- [Kafka: a distributed messaging system for log processing](https://notes.stephenholiday.com/Kafka.pdf), the original paper, short and readable.
- Confluent's blog on "exactly-once semantics", to see the nuance from the people who sell it.

Watch:
- [Ben Dicken on write-ahead logs](https://www.youtube.com/watch?v=s3hKYMOpp3E), 11 minutes, for the log intuition in pictures.

## What trips people up this week ⚠️

They reach for Kafka the moment they hear the word "scale", and end up running a distributed streaming platform to send a hundred emails a day. A queue is a real operational thing you now have to monitor, drain, and reason about when it backs up. For a lot of jobs a humble database table used as a queue is the correct, boring, wonderful answer. Reach for the big hammer when you can name the specific reason the small one is not enough.
