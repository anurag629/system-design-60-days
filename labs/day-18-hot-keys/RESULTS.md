---
title: "Day 18 lab results"
parent: "Day 18: hot keys and the celebrity problem"
grand_parent: "Week 3: caching and the CDN"
nav_order: 1
---

# Day 18 results: one hot key, and the node that melted

Measured on: (machine, OS, Python version)

## Output

Paste Part 1, the adding-nodes table, Part 2, the scoreboard and the closing lines here.

```
```

## One sentence per prediction

- P1 (celebrity key's share of all reads):
- P2 (baseline hottest node share, 8 nodes):
- P3 (hottest node after replicating the hot keys):
- P4 (reads absorbed by the local cache):

## What the hottest node was doing, in my own words

The distinct keys spread evenly across the 8 nodes, yet one node carried far more than its share. Which node, and why:

## Why adding nodes did not help

Write the floor in one line: the hottest node could not drop below ___% no matter how many nodes I added, because:

## The two fixes, side by side

Replicating the hot keys to every node brought the hottest node from ___% down to ___%. The local cache absorbed ___% of all reads before they reached the shared tier. When would you reach for one over the other:

## The number that matters

Before: hottest node ___% on a tier that should sit at 12.5%. After: ___%. One line on why you cannot shard your way out of a single hot key:

## Can't explain yet
