---
title: "Day 36 lab results"
parent: "Day 36: how LLM inference actually works"
grand_parent: "Week 6: AI systems"
nav_order: 1
---

# Day 36 results: prefill vs decode, and the memory wall

Measured on: (machine, OS, Python version. The lab is a cost model, so your numbers should match the reference almost exactly. If they do not, your constants drifted.)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (TPOT, time per output token):
- P2 (one output token vs one input token):
- P3 (decode arithmetic intensity):
- P4 (500-token reply vs 50-token reply):

## Prefill vs decode, in my own words

Why is prefilling a 500-token prompt cheap while generating 500 output tokens is expensive, even though it is the same token count:

## The memory wall

What does arithmetic intensity 1 against a machine balance of 150 actually mean for the GPU, and why does batching fix it:

## The number that matters

One output token costs about ___ prompt tokens. Total latency is TTFT + M * ___ . The 500-token reply cost ___x the latency of the 50-token reply for the same prompt. Why output is where the time and the money go:

## Can't explain yet
