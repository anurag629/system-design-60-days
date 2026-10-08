---
title: "Day 26 lab results"
parent: "Day 26: the outbox pattern"
grand_parent: "Week 4: async, queues and the log"
nav_order: 1
---

# Day 26 results: the dual write vs the outbox

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (naive lost events):
- P2 (outbox lost events):
- P3 (outbox duplicate events):
- P4 (idempotent distinct delivered):

## The dual write, in my own words

Where exactly is the gap? The order committed, and then what failed, and why does no reordering of the two writes close it:

## Why the outbox closes the gap

What rides in the same transaction as the order, and what does a crash leave behind for the relay to pick up:

## At-least-once, and the idempotency key

The relay delivered zero losses but some duplicates. Why is that the best a relay can do, and what does the Day 25 idempotency key add on top:

## The number that matters

Naive dual write lost ___ events silently. The outbox lost ___. The relay's at-least-once price was ___ duplicate copies, which idempotency collapsed back to ___ distinct orders:

## Can't explain yet
