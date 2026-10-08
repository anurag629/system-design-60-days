---
title: "Day 10 lab results"
parent: "Day 10: indexes in depth"
grand_parent: "Week 2: storage"
nav_order: 1
---

# Day 10 results: composite, covering, and the ignored index

Measured on: (machine, OS, Python version)

## Output

Paste part 1 through part 4 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (single-column index speedup):
- P2 (leftmost-prefix penalty):
- P3 (covering index speedup):
- P4 (function-defeat penalty):

## The five plans, in my own words

For each case, write the EXPLAIN QUERY PLAN line you saw and whether it was a SCAN or a SEARCH.

- a, no index:
- b, index on user_id:
- c, composite (country, city), filter on country / country+city / city only:
- d, non-covering vs covering:
- e, email = ? vs lower(email) = ?:

## The two ignored indexes

Both are a real index the planner chose NOT to use. In one line each, why:

- the composite index, for the city-only filter:
- the email index, for lower(email) = ?:

## The number that matters

The covering index was ___ times faster than the plain one. Why, in terms of table lookups:

## Can't explain yet
