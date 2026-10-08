---
title: "Day 25 lab results"
parent: "Day 25: delivery semantics and idempotency"
grand_parent: "Week 4: async, queues and the log"
nav_order: 1
---

# Day 25 results: duplicates, dedupe, and the honest middle

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (at-least-once duplicate charges):
- P2 (idempotent duplicate charges):
- P3 (at-most-once lost charges):
- P4 (at-least-once total deliveries):

## Why the duplicates happened

Same crashes, process-then-ack. How many duplicate charges, and what was the consumer doing on every redelivery:

## What the idempotency key changed

The broker redelivered exactly as often as in Part 1. So why did the ledger come out exactly right this time:

## The dilemma in Part 3

Ack-first lost messages, process-first duplicated them. In one line, why can you not just do both steps atomically and get neither problem:

## The number that matters

Without a key, ___ duplicate charges (ledger too high). With a key, ___ duplicates (exactly right), same crashes. Why that is the real meaning of "exactly-once":

## Can't explain yet
