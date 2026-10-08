---
title: "Day 29 lab results"
parent: "Day 29: failure, time, and the eight fallacies"
grand_parent: "Week 5: distributed systems"
nav_order: 1
---

# Day 29 results: the clock-skew bug and last-write-wins

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (LWW loss at 200 ms skew):
- P2 (loss threshold vs the inter-write gap):
- P3 (LWW loss at 2 ms, NTP-tight):
- P4 (loss when ordering by a logical version):

## The bug, in my own words

A write that truly happened later carried a smaller timestamp than an older one, because of the skew. What did last-write-wins do with it, and why was there no error:

## The threshold

Loss was exactly zero until skew reached the inter-write gap, then it appeared. Why does the gap set the cliff:

## Why NTP is not enough

Tightening the clocks shrank the loss a lot but not to zero. What writes were still at risk, and why can you never promise zero on a hot key:

## The number that matters

A clock skew of ___ ms made LWW silently drop ___ % of the newer writes. Ordering by a logical version instead took it to ___ %. Why does a logical clock make skew irrelevant:

## Can't explain yet
