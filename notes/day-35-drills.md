---
title: "Day 35 drills"
parent: "Day 35: designing a distributed key-value store"
grand_parent: "Week 5: distributed systems"
nav_order: 2
---

# Day 35 drills

Written on paper first. The distributed key-value store, broken into its decisions.

D1 (consistent hashing: fraction of keys that move when a node is added, and why):

D2 (quorum tuning on N=3: always-writable (W,R) vs read-sees-latest (W,R), which overlaps):

D3 (concurrent writes on two sides of a partition: wall-clock LWW vs vector clocks, which for a cart):

D4 (failure: sloppy quorum and hinted handoff, how the write succeeds and the data gets home):

D5 (CAP in practice: the AP consequence and reconciliation, and one product where you pick CP):
