---
title: "Day 31 posts"
parent: "Day 31: replication and quorums"
grand_parent: "Week 5: distributed systems"
nav_order: 3
---

# Day 31 posts: LinkedIn and X

Two screenshots carry this day. The first is Part 1: R + W > N, every setting reading 100 percent fresh. The second is Part 2 next to it: R + W <= N, and a third to two thirds of reads coming back stale. Swap in your own numbers and voice.

## LinkedIn

Day 31 of 60 days of system design. Today was quorums, the trick that lets a database keep several copies of your data and still promise a read will see your latest write. I built a small simulator and watched the promise hold, then break.

The setup is Dynamo style. You keep N copies. A write has to land on W of them. A read asks R of them and keeps the newest version it sees. The whole game is one inequality: R + W > N.

Here is why it works. If a write touched W replicas and a read asks R replicas, and R + W is bigger than N, those two sets cannot avoid each other. At least one replica is in both, and that replica has the latest write. Pure counting, no luck involved. In my run, every setting with R + W > N read 100 percent fresh. N=5, W=3, R=3. N=5, W=1, R=5. All of them, 100 percent.

Then I broke the rule. N=3, W=1, R=1. The write goes to one replica, the read asks one replica, and R + W = 2 is not above 3. Result: 66.5 percent of reads were stale. Two times in three, the one replica I read was simply not the one the write touched. The read set and the write set missed each other, and the read got an old value.

The last part was the tuning. On the same N=5, you can point the knob three ways:

    write-heavy (W=1, R=5):  writes 100% available, reads 59%
    read-heavy  (W=5, R=1):  reads 100% available, writes 59%
    balanced    (W=3, R=3):  both 99%

All three keep R + W > 5, so all three give fresh reads. What changes is where the fragility lands. W=1 means a write waits for one ack and almost never blocks, but R=5 means one dead replica takes every read down. Balanced survives two replicas being down, for reads and writes alike. That is the knob, and it is why Amazon's cart chose a low W: never reject an add-to-cart, heal the copies later with read-repair.

The overlap is the whole trick. Once R + W stops exceeding N, you have traded a strong read for a faster one.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #learninginpublic

## X thread

**1/**

Quorums, measured instead of hand-waved. Day 31 of 60 days of system design.

You keep N copies. Write to W of them. Read from R of them, keep the newest. One inequality decides if a read sees your latest write:

R + W > N

**2/**

Why it works is just counting.

A write touched W replicas. A read asks R replicas. If R + W > N, those two sets cannot be disjoint inside N replicas. At least one replica is in both, and it holds the latest write.

My run, every strong setting: 100% of reads fresh.

**3/**

Then I broke it. N=3, W=1, R=1. Write hits one replica, read asks one replica. R + W = 2, not above 3.

66.5% of reads came back STALE.

Two times in three the replica I read was not the one the write touched. The sets missed each other.

**4/**

Same N=5, swept across weak settings:

W1,R1 -> 80% stale
W2,R2 -> 30% stale
W2,R3 -> 10% stale

The fewer replicas a write and a read touch between them, the wider the gap they slip past each other through. Push W + R above N and it shuts.

**5/**

Tuning on the same N=5, all keeping R + W > 5:

write-heavy W1,R5: writes 100% up, reads 59%
read-heavy  W5,R1: reads 100% up, writes 59%
balanced    W3,R3: both 99%

Same freshness. Different fragility. Balanced survives 2 dead replicas.

**6/**

This is why Amazon's cart runs a low W: never reject an add-to-cart, let the copies disagree for a moment, and heal them with read-repair on the next read.

Right for a cart. Wrong for a bank balance.

The overlap is the whole trick.

Code: github.com/anurag629/system-design-60-days
