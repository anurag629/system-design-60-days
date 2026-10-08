---
title: "Day 17 lab results"
parent: "Day 17: the thundering herd"
grand_parent: "Week 3: caching and the CDN"
nav_order: 1
---

# Day 17 results: the stampede, the lock, and the early refresh

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (naive source calls in the burst):
- P2 (single-flight source calls):
- P3 (single-flight waiters):
- P4 (early-recompute herd calls):

## The stampede, in my own words

One hot key went cold for an instant and the whole crowd missed together. How many calls hit the source, and why is that the spike that can take down the database the cache was meant to protect:

## Fix one: the per-key lock

Source calls dropped to 1. But how many readers still had to wait for that one recompute, and when is that wait a problem (hint: what if the recompute hangs)?

## Fix two: early recomputation

Why did refreshing the value before it expired mean nobody blocked and the source was untouched at the herd? What did it cost compared to the lock?

## The number that matters

Same key, same crowd. Naive = ___ calls. Lock = ___ call, ___ waiters. Early refresh = ___ calls, ___ blocked. Which fix would you reach for first on a real hot key, and why:

## Can't explain yet
