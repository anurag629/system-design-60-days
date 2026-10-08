---
title: "Day 31 drills"
parent: "Day 31: replication and quorums"
grand_parent: "Week 5: distributed systems"
nav_order: 2
---

# Day 31 drills

Written on paper first. N replicas, write to W, read from R, and the one inequality that makes a read see the latest write.

D1 (N=5. Which of these give strong consistency, R+W>N: W=3 R=3, W=2 R=3, W=1 R=4, W=4 R=1? For W=3, what is the smallest R that still guarantees a read sees the latest write, and why):

D2 (the overlap, proved. N=6, W=4, R=3: show a read is guaranteed to see the latest write. Then N=6, W=3, R=3: is it still guaranteed? If not, write down an actual write set and read set that miss each other):

D3 (stale odds. N=3, W=1, R=1: a write lands on one random replica, a read asks one random replica. What is the chance the read misses the write? Now W=2, R=1 on N=3: strong or not, and what fraction of reads are stale):

D4 (tuning for a goal. N=5. You want writes to survive 2 replicas being down AND reads to stay strongly consistent. What is the largest W that survives 2 failures, what is then the smallest R with R+W>N, and what does that R cost you in read availability when one replica is down):

D5 (the Dynamo cart. Amazon's shopping cart used a low W so an add-to-cart is almost never rejected. What consistency did that trade away, what odd thing can a customer see, and how do read-repair and "merge the divergent carts" make that acceptable for a cart but wrong for a bank balance):
