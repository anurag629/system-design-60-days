---
title: "Day 26 posts"
parent: "Day 26: the outbox pattern"
grand_parent: "Week 4: async, queues and the log"
nav_order: 3
---

# Day 26 posts: LinkedIn and X

The scoreboard makes a good screenshot: 986 orders committed with their event lost forever under the naive dual write, zero lost with the outbox, and the at-least-once duplicates that idempotency then cleans up. Swap in your own numbers and voice.

## LinkedIn

Day 26 of 60 days of system design. Today I reproduced one of the most common bugs in backend systems on my own laptop, and then fixed it.

The bug is the dual write. You place an order: you write the order row to your database and commit it, then you publish an event to a queue so the rest of the system can react (send the email, decrement stock, fan out to followers). Two writes, two systems, no shared transaction. If the process dies in the gap after the commit but before the publish, the order is saved and the event is simply gone.

I ran 5,000 orders with the publish step crashing about 20% of the time:

    orders committed to the database:   5000
    events published to the queue:      4014
    orders with a LOST event:           986

986 orders that the customer was told went through, with no event ever published. No error in the logs. Nothing retries them. It is the IRCTC "paisa kat gaya, ticket nahi aaya" feeling, two systems quietly disagreeing about what happened.

The fix is the outbox pattern. Instead of publishing as a second step, you write the event into an outbox table in the SAME transaction as the order. Both land or neither does. A separate relay process then reads unsent outbox rows, publishes them, and marks them sent. A crash anywhere just leaves the row unsent, so the relay retries later. Same 5,000 orders, same crash rate:

    distinct orders delivered:          5000
    orders with a LOST event:           0

Zero lost. The database and the event stream never disagree.

One honest catch. The relay can publish an event and then crash before it marks the row sent, so it publishes the same event again next pass. That gave me 608 duplicate copies in the queue. The outbox guarantees at-least-once, not exactly-once. The fix for that is the idempotency key from yesterday: dedupe on it and all 5,000 orders are acted on exactly once.

The outbox fixes "did the event get out at all". Idempotency fixes "did it get out twice". You need both.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #learninginpublic

## X thread

**1/**

Today I reproduced the most common bug in event-driven backends, then fixed it.

The dual write: save the order to the DB, then publish an event to the queue. Two steps. Crash in between and the order exists but the event is gone.

Day 26 of 60 days of system design.

**2/**

5,000 orders, publish step crashing ~20% of the time:

orders in DB:        5000
events published:    4014
LOST events:          986

986 orders the customer thinks went through, with no email, no inventory update, no fan-out. Nothing errored. Nothing retries. Silent.

**3/**

No reordering saves you. Publish first, then write the DB? Now you can publish an event for an order that never got saved. There is no order of two separate writes that is atomic. That is the dual-write problem.

**4/**

The fix: the outbox pattern.

Write the event into an outbox TABLE in the same transaction as the order. Both commit or neither does. A separate relay reads unsent outbox rows, publishes them, marks them sent.

Same 5,000 orders, same crashes:

LOST events: 0

**5/**

Why zero? A crash can never split the order from its event anymore, they are one commit. And a crash in the relay just leaves the outbox row unsent, so the next pass retries it. Nothing is lost, ever.

**6/**

The catch: the relay can publish, then crash before marking the row sent, so it republishes. I got 608 duplicate events.

The outbox gives you at-least-once, not exactly-once.

**7/**

The duplicates are fixed by yesterday's idempotency key: dedupe on it, and all 5,000 orders are processed exactly once.

Outbox stops loss. Idempotency stops doubles. You need both.

Code: github.com/anurag629/system-design-60-days
