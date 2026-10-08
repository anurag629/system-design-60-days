---
title: "Day 41 lab results"
parent: "Day 41: serving concerns, caching, limiting and fallback"
grand_parent: "Week 6: AI systems"
nav_order: 1
---

# Day 41 results: semantic cache, token bucket, and fallback

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (semantic cache hit rate):
- P2 (exact-match hit rate on the same workload):
- P3 (request cap overspend on big requests, as a multiple of budget):
- P4 (outage success rate with fallback):

## Why the exact-match cache saved almost nothing

Same workload, two caches. What did the exact-match cache actually catch, and why did every paraphrase slip past it:

## Meter the token, not the request

On the small workload the request cap under-spent the budget. On the large workload it blew past it. In one line, why a request-per-minute limit is the wrong meter for an LLM:

## Retries vs fallback

When failures were independent blips, retries did most of the work. When the primary went fully down, retries did nothing and only fallback held the line. Say why in your own words:

## The number that matters

Semantic cache hit ___% vs exact-match ___%. The request cap let ___x the token budget through on big requests. Outage success was ___% without fallback and ___% with it. Which of these would you fix first in a real system, and why:

## Can't explain yet
