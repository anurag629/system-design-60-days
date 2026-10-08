---
title: "Day 30 lab results"
parent: "Day 30: CAP, for real, and PACELC"
grand_parent: "Week 5: distributed systems"
nav_order: 1
---

# Day 30 results: one partition, two policies, opposite failures

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (CP rejected percent during the partition):
- P2 (AP conflicts to reconcile after the heal):
- P3 (sync write latency over async):
- P4 (async stale-read percent):

## The forced choice, in my own words

Same partition, same workload. Under CP, who went unavailable and why, and how many conflicts did the heal find? Under AP, who stayed available and what was left to reconcile?

## PACELC: the trade with no partition in sight

Why was the sync write so much slower than the async one, and where did the stale reads come from under async?

## The number that matters

During the partition, CP rejected ___ percent of operations and healed with ___ conflicts. AP rejected ___ percent and healed with ___ conflicts. The database did not choose; the operation's policy did. In one line, what does that change about how you will answer "is Postgres CP or AP?" in an interview:

## Can't explain yet
