---
title: "Day 32 lab results"
parent: "Day 32: consensus and Raft"
grand_parent: "Week 5: distributed systems"
nav_order: 1
---

# Day 32 results: leader election, split votes, and the majority rule

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (ticks with no leader after the old one dies):
- P2 (fixed-timeout split-vote rate):
- P3 (randomized-timeout split-vote rate):
- P4 (failures a 5-node cluster tolerates):

## How the cluster healed, in my own words

The leader died and the heartbeats stopped. What did a follower do next, how many votes did the new leader need and get, and how long was the cluster without a leader:

## Why the timeouts are random

With fixed (equal) timeouts, what kept happening every round, and what did randomizing the timeout change so that elections settled in about one round:

## The majority rule as fault tolerance

A 5-node cluster elected a leader with 2 nodes down but not with 3. Why can 2 survivors never elect a leader, and what is the general formula for failures tolerated:

## The number that matters

Fixed timeouts split the vote ___ % of rounds; randomizing dropped that to ___ %. A 5-node cluster tolerates ___ failures. Why does a majority of the whole cluster, not of the survivors, decide whether the cluster is available:

## Can't explain yet
