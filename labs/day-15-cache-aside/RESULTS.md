---
title: "Day 15 lab results"
parent: "Day 15: caching and the cache-aside pattern"
grand_parent: "Week 3: caching and the CDN"
nav_order: 1
---

# Day 15 results: a dict in front of a slow database

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (cache hit vs source read, the speedup floor):
- P2 (cache-aside hit rate on the Zipf workload):
- P3 (source load reduction, no cache vs cache-aside):
- P4 (load multiplier when hit rate drops 90% to 80%):

## The mechanism, in my own words

Walk the cache-aside read path for a hit and for a miss. On a miss, what two things happen before the value comes back:

## Why the cache changed everything

The hit rate I measured, the database calls with and without the cache, and how much faster the average read got:

## The non-linear bit that surprised me

Going from a 90% hit rate to 80% did what to database load, and why is that not a 10% change:

## The number that matters

A cache hit was ___ times faster than a source read. At a ___% hit rate the cache cut database calls by ___x. Dropping to 80% multiplied database load by ___x. One line on why hit rate, not raw speed, is the thing to watch:

## Can't explain yet
