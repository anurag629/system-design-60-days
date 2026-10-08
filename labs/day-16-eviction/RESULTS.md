---
title: "Day 16 lab results"
parent: "Day 16: eviction and the working set"
grand_parent: "Week 3: caching and the CDN"
nav_order: 1
---

# Day 16 results: eviction and the working set

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here. The two ASCII curves in part 2 are the screenshot worth keeping.

```
```

## One sentence per prediction

- P1 (Zipf hit rate at a 1% cache):
- P2 (uniform hit rate at the same 1% cache):
- P3 (Zipf hit rate at a 20% cache):
- P4 (LRU minus FIFO, in points):

## The knee, in my own words

Under Zipf, a cache holding a tiny fraction of the keys already served most of the reads. How small was the fraction, how high was the hit rate, and why does the curve bend:

## Zipf vs uniform

Same cache, same sizes, two very different curves. Why is the uniform curve a near-straight diagonal while the Zipf one shoots up and flattens:

## Why LRU beat the dumber policies

LRU, FIFO and random at the same size. How many points did LRU win by, and what is LRU doing that FIFO and random are not:

## The number that matters

A cache of ___% of the keys served ___% of the Zipf reads (the knee), far above the uniform line, and LRU beat FIFO by ___ points. What that means for how big I would size a real cache:

## Can't explain yet
