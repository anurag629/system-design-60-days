---
title: "Day 38 lab results"
parent: "Day 38: vector search and embeddings"
grand_parent: "Week 6: AI systems"
nav_order: 1
---

# Day 38 results: recall versus speed, the one dial

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (brute-force recall@k):
- P2 (IVF nprobe=1 recall@k):
- P3 (IVF nprobe=1 speedup over brute force):
- P4 (IVF nprobe=8 recall@k):

## The wall, in my own words

Brute force was exact, 100 percent recall. Why is it exact, and why does its cost grow with the number of vectors:

## The IVF bargain

Probing one cell, what recall and what speedup did I get, and what exactly caused the recall it missed:

## The dial

As I turned nprobe up, what happened to recall and what happened to latency, and at what point did probing more stop buying any recall:

## The number that matters

At one cell, IVF hit ___ percent recall at ___ times the speed of brute force. Turn the dial to 8 cells and recall came back to ___ percent. In one line, why "approximate" is a setting you choose, not a flaw:

## Can't explain yet
