---
title: "Day 30 drills"
parent: "Day 30: CAP, for real, and PACELC"
grand_parent: "Week 5: distributed systems"
nav_order: 2
---

# Day 30 drills

Written on paper first. CAP stated correctly, the per-operation choice, quorums, and PACELC. Numbers where the drill asks for them.

D1 (state CAP properly: during a partition you choose between which two letters, why is partition tolerance not really optional for anything spanning a network, and in one line why is "pick two" a cartoon):

D2 (the per-operation point: can one database be both CP and AP? Give a real example of a single system where one operation is served consistent-or-refused and another is served available-but-stale, and say what actually decides which):

D3 (quorum arithmetic, from the lab: a 5-node cluster, strict majority quorum of 3. A partition splits it 3 and 2: which side serves writes, which refuses, and why are there zero conflicts afterwards? Now could any partition of 5 nodes ever leave two sides both holding a quorum at once? What does that impossibility buy you):

D4 (PACELC in the PA/EL notation: classify Dynamo-style stores and a fully synchronous primary-replica SQL setup. For a "PA/EC" system explain each half in plain words. Then the number: local apply 1 ms, cross-region round trip 80 ms, how much does synchronous cross-region replication add to every single write, and what does async trade for that):

D5 (the AP bill: after a heal you have two different values for one key. Name two honest reconciliation strategies and the specific thing last-write-wins silently throws away. Tie it back: the lab healed with 16 conflicts, so what would last-write-wins have quietly dropped there):
