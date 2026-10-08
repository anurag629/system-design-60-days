---
title: "Day 19 lab results"
parent: "Day 19: Redis internals and pipelining"
grand_parent: "Week 3: caching and the CDN"
nav_order: 1
---

# Day 19 results: round trips, and what pipelining buys

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (one-at-a-time ops/sec):
- P2 (pipelined round trips at M = 100):
- P3 (pipeline speedup at M = 100):
- P4 (pipelined ops/sec at M = 100):

## Where the time actually went

One op is a dict lookup, microseconds of CPU. So why was the one-at-a-time rate so low, and what were you really paying for on every op:

## What pipelining changed, and what it did not

Same 50,000 ops, same server, same dict. Pipelining at M = 100 was how many times faster, and why (what dropped from 50,000 to 500):

The throughput climbed with the batch size and then flattened. What is the bottleneck once it flattens:

## Single threaded and rich commands

Why is one thread fine for a server like this, and how did the one MGET beat 100 separate GETs:

## The number that matters

One at a time: ___ ops/sec. Pipelined at M = 100: ___ ops/sec, about ___x faster, from 50,000 round trips down to 500. In one line, why that gap is the whole point of pipelining:

## Can't explain yet
