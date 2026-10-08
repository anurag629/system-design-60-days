---
title: "Day 24 lab results"
parent: "Day 24: Kafka, partitions and consumer groups"
grand_parent: "Week 4: async, queues and the log"
nav_order: 1
---

# Day 24 results: partitions, consumer groups, and the ordering guarantee

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (how many partitions one key's records land on):
- P2 (throughput speedup at C = P consumers):
- P3 (idle consumers at C = 2P):
- P4 (per-key order violations):

## Partitioning, in my own words

Why does one key always go to one partition, and why do many different keys spread across all of them:

## Consumer groups: where the line goes flat

Throughput climbed to about ___x at C = P, then stopped. How many consumers sat idle at C = 2P, and why can you never have more useful consumers than partitions:

## The ordering guarantee people get wrong

Within a partition the out-of-order count was ___, across two partitions it was ___, and per key it was ___. Say the guarantee Kafka actually gives in one sentence:

## The number that matters

Parallelism is capped at the partition count, and order holds only inside a partition (so pick your key to match the thing you need ordered):

## Can't explain yet
