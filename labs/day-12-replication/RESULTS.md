---
title: "Day 12 lab results"
parent: "Day 12: replication and lag"
grand_parent: "Week 2: storage"
nav_order: 1
---

# Day 12 results: replication lag and the stale read

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (stale percent at the given lag):
- P2 (stale window in ms):
- P3 (one synchronous write in ms):
- P4 (stale percent after the fix):

## The stale read, in my own words

At 40 ms of lag, what fraction of my immediate follower reads were stale, and how long did the follower keep serving the old value:

## Which fix I would reach for

Read your writes (route recent reads to the leader) or wait for the follower to catch up, and why, for a feed like this:

## The number that matters

Stale percent at the given lag was ___ and after the read-your-writes fix it was ___. Synchronous writes cost ___ ms versus ___ for async. The tradeoff in one line:

## Can't explain yet
