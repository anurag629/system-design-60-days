---
title: "Day 9 lab results"
parent: "Day 9: B-trees and LSM trees"
grand_parent: "Week 2: storage"
nav_order: 1
---

# Day 9 results: B-tree vs LSM, the write-order gap

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (B-tree random slowdown):
- P2 (LSM write ratio random / sequential):
- P3 (LSM sorted runs):
- P4 (LSM read places on a miss):

## The B-tree's weakness, in my own words

Same rows, same keys, only the order changed. How much slower was random, and what was the tree actually doing:

## The LSM's bargain

Why was the append write path flat for sequential vs random, and what did it cost on the read side:

## The number that matters

Random B-tree inserts were ___ slower than sequential. Append-only writes came out ___ (flat). Why that gap sends write-heavy systems to an LSM:

## Can't explain yet
