---
title: "Day 31 lab results"
parent: "Day 31: replication and quorums"
grand_parent: "Week 5: distributed systems"
nav_order: 1
---

# Day 31 results: the overlap that makes a read see the latest write

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (strong quorum, N=5 W=3 R=3, percent of reads that see the latest write):
- P2 (weak quorum, N=3 W=1 R=1, percent of stale reads):
- P3 (weak quorum, N=5 W=2 R=2, percent of stale reads):
- P4 (balanced W=R=3 on N=5, availability with 10 percent per-replica downtime):

## The overlap, in my own words

With R + W > N, every read came back fresh, and not by luck. Why are the read set and the write set forced to share at least one replica, and what does that one shared replica carry:

## Breaking the rule

With R + W <= N I measured a real fraction of stale reads. Which setting was worst, and what was the read set doing when it missed the latest write:

## The number that matters

With R + W > N, ___ percent of reads saw the latest write. With N=3, W=1, R=1, ___ percent were stale. In one line, why the overlap is the whole trick:

## Tuning, and what each setting trades

Write-heavy (W=1), read-heavy (W=N) and balanced (W=R=N/2+1) all kept R + W > N, so all gave fresh reads. What did each one trade on availability, and why did balanced survive the most failures:

## Read-repair

The weak write reached one replica, and repeated reads with repair on dragged the whole cluster up to date. In my own words, what is read-repair doing, and what finishes the job for replicas no read touches:

## Can't explain yet
