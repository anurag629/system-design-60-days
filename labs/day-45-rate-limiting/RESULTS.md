---
title: "Day 45 lab results"
parent: "Day 45: rate limiting"
grand_parent: "Week 7: production"
nav_order: 1
---

# Day 45 results: token bucket, the fixed-window trap, and leaky vs token

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (token burst accepted):
- P2 (token sustained accept rate):
- P3 (fixed-window accepted across the boundary):
- P4 (sliding-window accepted across the boundary):
- P5 (leaky bucket output rate):
- P6 (token bucket peak output in one second):

## The token bucket, in my own words

What did the instant burst get capped at, and why did a sustained 3x overload still settle to the refill rate:

## The fixed-window trap

How did the fixed window let 2x the limit through at the boundary, and what does the sliding window do differently:

## Leaky vs token

Why was the leaky bucket's output flat while the token bucket's was spiky, and what did the leaky bucket pay for that smoothness:

## The number that matters

Fixed window let ___ through a "100 per minute" limit at the boundary (about 2x). Token bucket capped a burst at ___. Leaky bucket emitted a flat ___/s. Which one would I put in front of a fragile downstream, and why:

## Can't explain yet
