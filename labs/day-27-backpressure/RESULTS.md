---
title: "Day 27 lab results"
parent: "Day 27: backpressure and load shedding"
grand_parent: "Week 4: async, queues and the log"
nav_order: 1
---

# Day 27 results: the queue between a fast producer and a slow consumer

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (unbounded final depth):
- P2 (bounded final depth):
- P3 (backpressure throttle factor):
- P4 (shed count):

## The unbounded disaster, in my own words

Producer at about twice the consumer, no limit on the queue. What did the depth curve do over the run, and what does Little's Law say happens to a new job's wait as it keeps running:

## Backpressure

Once I capped the queue and used a blocking put(), what happened to the producer's rate and to the queue depth, and why:

## Load shedding

When I rejected the excess instead of queuing it: how many were shed, what stayed steady, and why a fast "no" protects the system where an unbounded "yes" does not:

## The number that matters

Unbounded depth climbed to ___ (and kept climbing), the bounded queue held flat at ___, and shedding turned away ___ jobs to keep the rest fast. Which policy would I pick for a user-facing API, and why:

## Can't explain yet
