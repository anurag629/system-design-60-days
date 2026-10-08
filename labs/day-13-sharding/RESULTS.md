---
title: "Day 13 lab results"
parent: "Day 13: partitioning and sharding"
grand_parent: "Week 2: storage"
nav_order: 1
---

# Day 13 results: the hot shard, and the cost of adding a server

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (celebrity key's share of all traffic):
- P2 (range partitioning, hottest shard's share):
- P3 (modulo resharding 8 to 9, percent of keys remapped):
- P4 (consistent hashing 8 to 9, percent of keys remapped):

## The hot shard, in my own words

Hash sharding spread the distinct keys evenly, yet the hottest shard was still well above the ideal. Why, and what happened when I pushed the shard count up to 256:

## The number that matters

To add one shard, plain modulo moved ___ percent of the keys and consistent hashing moved ___ percent. In one line, why that is the difference between a weekend migration and a shrug:

## The trap I want to remember

Consistent hashing fixed the resharding churn but did not fix the ___ . The fix for that is a different thing entirely:

## Can't explain yet
