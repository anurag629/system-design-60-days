---
title: "Day 33 lab results"
parent: "Day 33: logical clocks"
grand_parent: "Week 5: distributed systems"
nav_order: 1
---

# Day 33 results: logical clocks, and the concurrency a wall clock cannot see

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (ordered pairs):
- P2 (concurrent pairs, the number):
- P3 (Lamport mis-orderings):
- P4 (Dynamo sibling conflicts):

## Lamport's guarantee, and its blind spot

Write the one-way rule in your own words. On how many ordered pairs did Lamport(a) < Lamport(b) hold, and how many concurrent pairs did it still slap a strict order on:

## What vector clocks recovered

How many pairs were genuinely concurrent, and why can a vector clock prove concurrency where a single Lamport integer cannot:

## The number that matters

Genuinely concurrent pairs: ___. In the cart run, vector clocks preserved ___ items and last-write-wins kept ___. Why that gap is the Day 29 bug meeting the Day 31 sibling:

## Can't explain yet
