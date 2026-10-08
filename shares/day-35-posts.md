---
title: "Day 35 posts"
parent: "Day 35: designing a distributed key-value store"
grand_parent: "Week 5: distributed systems"
nav_order: 3
---

# Day 35 posts: LinkedIn and X

The angle is arrival: a distributed database stopped being a wall because you built its parts all week. Swap in your own voice.

## LinkedIn

Day 35 of 60 days of system design, end of week 5, the hard week. Today I designed a distributed key-value store, which is basically Amazon's Dynamo, and the striking thing is that it was not intimidating any more. Every piece was something I had already simulated this week.

Where does a key live? A consistent-hashing ring. Add a node and only about 1/N of the keys move, instead of reshuffling everything. I measured that on Day 13.

How many copies, and how many must answer? Quorums: replicate to N, write to W, read from R. Set R plus W greater than N and a read sees the latest write. Set W low and you stay writable even when most replicas are down, trading freshness for availability. That dial was Day 31.

Two clients write the same key on two sides of a partition. A wall-clock "last write wins" would silently throw one away, and if the clocks are skewed it might even keep the older one. Vector clocks instead keep both as conflicting siblings for the app to merge, the way a shopping cart unions its items. Days 29 and 33.

During a partition, the store stays available and reconciles afterward, which is the right call for a cart and the wrong call for a bank ledger. That is the real CAP, a per-operation choice, from Day 30.

A week ago "design a distributed database" would have been a blank page and a rising panic. The hard week did not make distributed systems easy. It gave me a map: I know what CAP actually says, why quorums are a dial, how consensus works, and why clocks are not to be trusted. That map is enough to reason about anything.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #learninginpublic

## X thread

**1/**

Day 35, end of week 5 (the hard week) of 60 days of system design. I designed a distributed key-value store, basically Dynamo, and it was not a wall any more. Every piece was something I simulated this week.

**2/**

Where a key lives: a consistent-hashing ring. Add a node, only ~1/N of keys move, not the whole dataset. (Day 13)

How many copies answer: quorums. Replicate to N, write W, read R. R + W > N means reads see the latest write. (Day 31)

**3/**

Two clients write one key on two sides of a partition. Wall-clock "last write wins" silently drops one (and with skew, maybe the newer one). Vector clocks keep both as siblings to merge, like a cart unioning items. (Days 29, 33)

**4/**

During a partition: stay available and reconcile later (right for a cart), or refuse writes to stay consistent (right for a bank ledger). That is the real CAP, a per-operation choice. (Day 30)

**5/**

A week ago "design a distributed database" was a blank page and panic. The hard week did not make distributed systems easy. It gave me a map: what CAP says, why quorums are a dial, how consensus works, why clocks lie.

Week 6 points all of it at a GPU.

Code: github.com/anurag629/system-design-60-days
