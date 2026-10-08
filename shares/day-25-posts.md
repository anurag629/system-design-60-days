---
title: "Day 25 posts"
parent: "Day 25: delivery semantics and idempotency"
grand_parent: "Week 4: async, queues and the log"
nav_order: 3
---

# Day 25 posts: LinkedIn and X

The scoreboard makes a good screenshot: same 1000 payments and the same crashes, three outcomes. Ack-first loses 97 charges, process-first duplicates 107, and an idempotency key lands on exactly zero. Swap in your own numbers and voice.

## LinkedIn

Day 25 of 60 days of system design. Today I finally understood why "exactly-once delivery" is mostly a comforting lie, by charging a fake card 1000 times and crashing the worker on purpose.

Setup: a broker hands a payment to a consumer, the consumer posts a 100-rupee charge to a ledger, then acks. I made about 10 percent of deliveries crash after the charge but before the ack. The broker never heard the ack, so it redelivered, and the charge got posted again.

    at-least-once (process, then ack):  107 duplicate charges
    ledger balance: 110,700   (correct is 100,000)

So the card got charged an extra 10,700 rupees for nothing. That is not a rare edge case. Under retries, duplicates are the normal case.

Then I gave every message a unique id and had the consumer skip any id it had already applied. Same crashes, same redeliveries, same 1107 total deliveries:

    at-least-once + idempotency key:  0 duplicates
    ledger balance: 100,000   (exactly right)

Delivery is still at-least-once. The effect is now exactly-once. That gap between delivery and effect is the whole lesson.

The honest bit is Part 3. I flipped the order and acked before processing. Now a crash loses the message instead of duplicating it:

    at-most-once (ack, then process):  97 lost charges
    ledger balance: 90,300   (too low)

You cannot ack and process as one atomic action across a network. Process first and you risk a duplicate. Ack first and you risk a loss. One of those two is always your reality, so the real move is to pick at-least-once and make the processing idempotent.

This is the UPI story. Your payment screen says "failed", you tap again, and you are not charged twice. The retry is at-least-once delivery. The "not twice" is an idempotency key quietly doing its job.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #learninginpublic

## X thread

**1/**

"Exactly-once delivery" is mostly marketing. I proved it today by charging a fake card 1000 times and crashing the worker on purpose.

Day 25 of 60 days of system design.

**2/**

Setup: broker hands a payment to a consumer. Consumer posts a 100-rupee charge, then acks. I crash ~10% of deliveries AFTER the charge but BEFORE the ack.

The broker never heard the ack, so it redelivers. The charge posts again.

    107 duplicate charges
    ledger 110,700 (should be 100,000)

**3/**

That is at-least-once delivery. Under crashes and retries, duplicates are not rare. They are normal.

**4/**

Fix: give every message a unique id. The consumer skips any id it has already applied. Same crashes, same 1107 deliveries:

    0 duplicates
    ledger 100,000 (exactly right)

Delivery is still at-least-once. The EFFECT is now exactly-once.

**5/**

The honest part. Flip the order, ack BEFORE processing. Now a crash loses the message:

    97 lost charges
    ledger 90,300 (too low)

Process-first duplicates. Ack-first loses. You cannot do both steps atomically over a network.

**6/**

So the real goal is never "exactly-once delivery". It is at-least-once delivery plus idempotent processing.

This is UPI. Payment says "failed", you tap again, you are not charged twice. The retry is at-least-once. The "not twice" is an idempotency key.

Code: github.com/anurag629/system-design-60-days
