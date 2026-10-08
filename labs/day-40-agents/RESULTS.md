---
title: "Day 40 lab results"
parent: "Day 40: agents, and why the token bill explodes"
grand_parent: "Week 6: AI systems"
nav_order: 1
---

# Day 40 results: the agent loop and the quadratic token bill

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (cost factor when steps double, 10 to 20):
- P2 (naive total tokens vs 20 first-calls):
- P3 (trim saving, percent of naive tokens):
- P4 (chance at least one of 20 steps is slow):

## Why the loop is quadratic, in my own words

The model keeps no memory between calls, so each step re-sends the whole context. What did the per-call input tokens do across the 20 steps, and why does summing a growing input over K steps go as K squared:

## The context lever

Keeping the last few steps and summarising the rest. How much did it save on the 20-step task, and why does the naive/trimmed gap get wider as the task gets longer:

## Fan-out and the tail

One request became 20 sequential model calls. What did that do to wall-clock latency, and why did a 5% per-call tail end up hitting 64% of whole runs:

## The number that matters

A naive 20-step agent processed ___ tokens, about ___x the budget for 20 plain calls. Doubling the steps cost ___x, not 2x. Trimming saved ___%. Why that makes context management the single biggest cost lever on an agent:

## Can't explain yet
