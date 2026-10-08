---
title: "Day 25 drills"
parent: "Day 25: delivery semantics and idempotency"
grand_parent: "Week 4: async, queues and the log"
nav_order: 2
---

# Day 25 drills

Written on paper first. Delivery semantics, the two-step problem, and idempotency keys.

D1 (name the three delivery semantics: at-most-once, at-least-once, exactly-once. For each, say whether it risks loss or duplicates, and which order of the two steps, process and ack, produces it):

D2 (a consumer must do two things on a message: apply the effect and ack it. Explain in two or three sentences why you cannot make those one atomic step across a network, and what that means for the phrase "exactly-once delivery"):

D3 (you add an idempotency key per message so a redelivery is a no-op. Where must the "I have already applied this id" record live for the dedupe to survive the consumer crashing right after it applies the effect? What breaks if that record and the effect are written separately):

D4 (a payment request is "charge this card 500 rupees for order 123". Who should generate the idempotency key and when, the client before the first attempt or the server on each request? Give one good key and one bad key, and say why the bad one fails to stop a double charge):

D5 (a broker delivers 5000 messages, and 8 percent of deliveries crash after processing but before the ack, each losing its ack exactly once. How many total deliveries does the consumer handle, how many duplicate effects land without an idempotency key, and how many effects are actually applied with one):
