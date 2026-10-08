---
title: "Day 37 lab results"
parent: "Day 37: the KV cache and continuous batching"
grand_parent: "Week 6: AI systems"
nav_order: 1
---

# Day 37 results: the KV cache and continuous batching

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (requests that fit at 2048 tokens):
- P2 (requests that fit at 8192 tokens):
- P3 (continuous throughput multiple over static):
- P4 (static batching GPU utilisation):

## The KV cache, in my own words

Why does GPU memory, not compute, cap the batch, and what happens to the batch when the sequence length doubles:

## Static vs continuous batching

Why did static batching leave the GPU so idle, and what single change did continuous batching make to keep it full:

## The number that matters

Continuous batching gave ___ x the throughput of static on the same requests, because static ran the GPU at only ___ % useful slot-time. In one line, why is this the same lesson as Day 4 (keep the server busy, shared queue beats separate lines):

## Can't explain yet
