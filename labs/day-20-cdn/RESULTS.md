---
title: "Day 20 lab results"
parent: "Day 20: the CDN and cache invalidation"
grand_parent: "Week 3: caching and the CDN"
nav_order: 1
---

# Day 20 results: the CDN, 304s, and serving stale on purpose

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (origin hits, no cache):
- P2 (origin hits, TTL cache):
- P3 (cheap 304 revalidations):
- P4 (blocking spike, ms):

## What the TTL cache bought me

Same 120 requests for 3 resources. How many reached the origin with no cache vs with the TTL cache, and why did so many of the cache's origin trips come back as 304:

## Why the conditional request matters

The edge already had a copy. What did If-None-Match let the origin skip, and what did it still have to pay:

## Stale-while-revalidate vs blocking

Under blocking revalidation, who waited and for how long? Under stale-while-revalidate, why did the worst user latency stay flat even though the origin was hit the same number of times:

## The number that matters

Origin hits went from ___ to ___. The blocking spike was ___ ms while stale-while-revalidate's worst was ___ ms. Why that gap is the whole reason CDNs serve stale on purpose:

## Can't explain yet
