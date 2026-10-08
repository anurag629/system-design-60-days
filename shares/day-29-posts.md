---
title: "Day 29 posts"
parent: "Day 29: failure, time, and the eight fallacies"
grand_parent: "Week 5: distributed systems"
nav_order: 3
---

# Day 29 posts: LinkedIn and X

The scoreboard makes a clean screenshot: a clock that ran 200 ms fast silently deleted about a quarter of the newer writes, the loss was zero only while skew stayed under the gap between writes, NTP shrank it to a fraction of a percent but not to zero, and a logical clock took it to zero. Swap in your own numbers and voice.

## LinkedIn

Day 29 of 60 days of system design. First day of the hard week, distributed systems, and I started it by watching a database silently eat my data because of one wrong clock.

The setup is the classic one. Two nodes both accept writes to the same key, and when two writes meet they keep the one with the larger timestamp. Last-write-wins. Cassandra, DynamoDB and old Riak all do this. Sounds reasonable.

The problem is that the two machines' clocks do not agree. I made node A's clock run 200 ms ahead of node B's, then sent 20,000 writes to one key, split across the nodes. A write that genuinely happened later, on the slow node, carried a smaller timestamp than an older write on the fast node. Last-write-wins kept the older one and threw the newer one away.

    skew   0 ms   ->   0.0% of newer writes lost
    skew  50 ms   ->  15.9%
    skew 100 ms   ->  21.9%
    skew 200 ms   ->  24.7%

About a quarter of the newer writes to that key, gone. No error. No log line. The value just never existed as far as the store was concerned. That is the thing that makes it scary: it is silent.

Then two more findings:

1. The loss is a cliff, not a slope. For a fixed 50 ms gap between writes, loss was exactly zero until the skew reached 50 ms, then it appeared. Skew only reorders two events once it is larger than the gap between them.

2. NTP helps but does not save you. At 2 ms of skew the loss dropped to 0.92%. Better, not zero, because a hot key gets near-simultaneous writes whose gap is smaller than even a couple of ms.

The real fix is to stop ordering cross-machine events by the wall clock at all. I re-ran the same writes ordered by a logical version instead of a timestamp, and the loss went to 0%. A logical clock never reads the time of day, so no amount of skew can reorder two writes that truly follow one another. That is Lamport clocks and version vectors, which is where this week is heading.

The lesson I am taking: never trust the wall clock to order events across machines.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #learninginpublic

## X thread

**1/**

Day 29 of 60 days of system design. I made a database silently delete a quarter of my writes, on purpose, using nothing but one wrong clock.

Welcome to distributed systems week.

**2/**

The setup: two nodes both accept writes to the same key. When two writes collide, keep the one with the bigger timestamp. Last-write-wins.

Cassandra, DynamoDB, old Riak all resolve conflicts this way. Looks fine.

**3/**

The catch: the two machines' clocks disagree.

I set node A's clock 200 ms ahead of node B's. Now a write that happened LATER on node B can carry a SMALLER timestamp than an older write on node A.

Last-write-wins keeps the older one. The newer value is gone.

**4/**

20,000 writes to one hot key, split across the nodes:

skew   0 ms -> 0.0% lost
skew  50 ms -> 15.9%
skew 100 ms -> 21.9%
skew 200 ms -> 24.7%

A quarter of the newer writes, silently discarded. No error, no log line.

**5/**

It is a cliff, not a slope.

Fix the gap between writes at 50 ms and grow the skew: loss is exactly 0% until skew hits 50 ms, then it appears.

Skew only reorders two events once it is bigger than the gap between them.

**6/**

Does NTP save you? It helps, it does not save you.

At 2 ms of skew the loss was 0.92%. Small, not zero. A hot key gets near-simultaneous writes whose gap is under a couple of ms, and those still flip.

**7/**

The actual fix: stop ordering cross-machine events by the wall clock.

Same writes, ordered by a logical version instead of a timestamp: 0% lost.

A logical clock never reads the time of day, so skew cannot touch it. Lamport clocks, version vectors. That is the week ahead.

**8/**

The one line to carry:

never trust the wall clock to order events across machines.

Code: github.com/anurag629/system-design-60-days
