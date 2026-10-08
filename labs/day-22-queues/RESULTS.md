---
title: "Day 22 lab results"
parent: "Day 22: sync vs async, and why queues exist"
grand_parent: "Week 4: async, queues and the log"
nav_order: 1
---

# Day 22 results: sync vs async, and the queue as a buffer

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3, part 4 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (synchronous caller latency per job):
- P2 (asynchronous caller latency, the enqueue):
- P3 (burst peak queue depth):
- P4 (backpressure, blocked puts on the bounded queue):

## The sync-to-async jump, in my own words

Same work, same machine. How much faster did the caller return once it handed the job to a queue, and what exactly moved (and what did not):

## The queue as a buffer

The burst of jobs arrived all at once but the worker could only do one every 50 ms. Describe what the queue depth did (rose to what, drained over how long), and why no caller had to wait for it:

## The first taste of backpressure

On the bounded queue, how many puts blocked, and why? What is the queue actually telling the producer when put() blocks:

## The number that matters

Synchronous caller latency was ___ ms (the whole job). Asynchronous caller latency was ___ ms (just the enqueue). That is the whole reason queues exist. One line on when you would NOT make a call async:

## Can't explain yet
