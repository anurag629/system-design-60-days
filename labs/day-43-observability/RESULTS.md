---
title: "Day 43 lab results"
parent: "Day 43: observability"
grand_parent: "Week 7: production"
nav_order: 1
---

# Day 43 results: the mean that hid the fire

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (mean latency of the stream):
- P2 (p99 latency of the SAME stream):
- P3 (structured query, acme errors over 1 second):
- P4 (slowest span in the fan-out trace):

## The mean vs the p99, in my own words

Same stream, one mean and one p99. What did the mean say, what did the p99 say, and roughly how many times bigger was the p99? Why does an average hide the tail:

## Structured vs unstructured logs

The structured filter answered the on-call question exactly. What went wrong when I tried the same question against the blob of text, and what does "structure the log once or parse it forever" mean to you:

## The trace

Metrics reported one number for the slow request. The trace broke it into spans. Which span ate most of it, what fraction, and why could the metric never have told me that:

## The number that matters

The mean was ___ ms and looked healthy. The p99 was ___ ms, about ___x higher. The trace put ___ of ___ ms on one span. In one line, why you alert on the p99 and keep all three signals:

## Can't explain yet
