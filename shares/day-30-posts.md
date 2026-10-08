---
title: "Day 30 posts"
parent: "Day 30: CAP, for real, and PACELC"
grand_parent: "Week 5: distributed systems"
nav_order: 3
---

# Day 30 posts: LinkedIn and X

The scoreboard makes a good screenshot: one partition, driven by the same workload under two policies, ending in opposite failures. CP rejected 38 percent of operations and healed with zero conflicts. AP rejected nothing and healed with 16 conflicts. Swap in your own numbers and voice.

## LinkedIn

Day 30 of 60 days of system design. Today I finally stopped misremembering the CAP theorem, by simulating it.

Everyone recites "consistency, availability, partition tolerance, pick two." That is a cartoon. Partition tolerance is not something you pick; if your system spans a network, partitions will happen whether you like it or not. The real theorem is smaller and sharper: when a partition happens, each operation has to choose between staying consistent and staying available. That is it.

So I built a tiny five-node key-value store, cut it into a majority side (3 nodes) and a minority side (2 nodes), and drove the same 1,000 operations through it under two policies.

    CP policy (consistency first):
      operations rejected: 383  (38% unavailable)
      conflicts after heal: 0

    AP policy (availability first):
      operations rejected: 0
      conflicts after heal: 16

Same partition. Same workload. CP refused every operation on the minority side, because that side could not reach a quorum, so it went unavailable but never let a key take two values. AP accepted everything, stayed fully available, and ended with 16 keys holding different values on the two sides that something now has to reconcile.

The database did not choose a letter. The operation's policy did.

Then the part nobody teaches: PACELC. Even with no partition at all, there is still a trade. A synchronous write waits for the replica to acknowledge, so it paid a full network round trip: 11.5 ms versus 1 ms for an async write, about 11 times slower. The async write returned instantly but left a window where a replica served a stale read, 12 percent of reads in my run. CAP is only about the partition. You are trading consistency against latency every single day.

So the next time someone asks "is Postgres CP or AP?", the honest answer is "which operation, and how is it configured?"

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #learninginpublic

## X thread

**1/**

Everyone recites CAP as "consistency, availability, partition tolerance, pick two."

That is a cartoon. Today I simulated the real thing. Day 30 of 60 days of system design.

**2/**

First, partition tolerance is not a choice. If your system spans a network, partitions happen. You do not opt out.

The real theorem: WHEN a partition happens, each operation chooses between consistency and availability. That is the whole thing.

**3/**

So I built a 5-node key-value store, cut it into a majority side (3 nodes) and a minority side (2 nodes), and ran the SAME 1,000 ops under two policies.

**4/**

CP policy (consistency first):
  rejected: 383 ops (38% unavailable)
  conflicts after heal: 0

The minority side had no quorum, so it refused everything. It went DOWN but never let a key split into two values.

**5/**

AP policy (availability first):
  rejected: 0
  conflicts after heal: 16

Nobody was turned away. But both sides wrote the same keys to different values, so the heal found 16 conflicts to reconcile.

Same partition. Opposite failure.

**6/**

The database did not pick a letter. The OPERATION'S policy did.

**7/**

Then PACELC, the part nobody teaches. Even with NO partition there is a trade.

sync write (waits for the replica): 11.5 ms
async write (returns immediately):   1.0 ms

~11x slower for consistency. And async served 12% stale reads.

**8/**

CAP is only about the partition. PACELC says you trade consistency against latency all the time, on a perfectly healthy day.

So "is Postgres CP or AP?" has one honest answer: which operation, and configured how?

Code: github.com/anurag629/system-design-60-days
