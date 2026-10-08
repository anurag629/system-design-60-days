---
title: "Day 46 lab results"
parent: "Day 46: multi-tenancy and isolation"
grand_parent: "Week 7: production"
nav_order: 1
---

# Day 46 results: the noisy neighbour, and the quota that contains it

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (quiet tenant served, no isolation):
- P2 (greedy tenant served, no isolation):
- P3 (quiet tenant served, with quota):
- P4 (greedy tenant capped at, with quota):

## The noisy neighbour, in my own words

One greedy tenant flooded a shared pool. What happened to a well-behaved tenant that changed nothing, and why did the shared queue hand the flood such a big slice:

## The fix

A per-tenant token bucket at the fair share. Why does capping the greedy tenant at the door give the quiet tenants their throughput back, and where did the greedy tenant's rejected requests go:

## Quota versus fair scheduling

A hard quota and fair-share scheduling both protected the quiet tenants under the flood. What is the difference when one tenant goes idle, and why do real systems often run both:

## The isolation spectrum

Shared everything, shared with quotas, dedicated per tenant. In one line each: what isolation you get and what it costs, and where the cost comes from for the dedicated model:

## The number that matters

The well-behaved tenant went from ___/tick (flood, no isolation) to ___/tick (same flood, with a quota), while the greedy tenant was capped at ___/tick. Why that is the whole case for isolation:

## Can't explain yet
