---
title: "Day 26 drills"
parent: "Day 26: the outbox pattern"
grand_parent: "Week 4: async, queues and the log"
nav_order: 2
---

# Day 26 drills

Written on paper first. The dual-write gap, the outbox transaction, the relay, and where idempotency still has to do its job.

D1 (you write the order to the database and publish an event to the queue as two steps: describe the two possible orderings, DB-first-then-publish and publish-first-then-DB, and say exactly what inconsistency a crash in the gap leaves behind for each; then say why no reordering ever makes the pair atomic):

D2 (a service takes 2,000,000 orders a day, and the publish step fails independently 0.1% of the time with the naive dual write: how many orders a day end up committed with no event, how many over a 30-day month, and why does nobody notice until much later):

D3 (the outbox move: explain why writing the outbox row in the SAME transaction as the order removes the failure window, what the single thing that must now succeed is, and what a crash before the commit versus after the commit leaves behind):

D4 (the relay publishes an event and then crashes before it marks the outbox row sent: what does the next relay pass do, what does the consumer end up seeing, and why can a relay reading an outbox never promise exactly-once on its own):

D5 (a teammate says "we have the outbox now, so we can drop the idempotency keys": correct them in two or three sentences, saying what the outbox guarantees and what it does not; then name one difference between a polling relay and a log-tailing relay like Debezium reading the database's write-ahead log):
