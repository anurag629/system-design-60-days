---
title: "Day 34 posts"
parent: "Day 34: the papers"
grand_parent: "Week 5: distributed systems"
nav_order: 3
---

# Day 34 posts: LinkedIn and X

The angle is that the famous papers are approachable once you have built their ideas. Swap in your own voice.

## LinkedIn

Day 34 of 60 days of system design. Today was papers day: Dynamo, Bigtable and Spanner, the three that half the industry cites and far fewer have actually read.

Here is what surprised me. They are readable. Not because I got smarter overnight, but because I spent this week simulating their ideas before reading them. By the time I opened the Dynamo paper, consistent hashing, quorums with R plus W, and vector clocks for conflicts were things I had already built in small Python labs. The paper read like documentation for something I had half-written.

The three trades, in one line each:

- Dynamo gave up strong consistency to be always writable, because an Amazon cart that ever refuses a write loses money. It spends the rest of the paper managing the divergence that creates.
- Bigtable gave up the relational model for scale and simplicity, storing everything in LSM-style SSTables on top of other Google systems.
- Spanner gave up cheap timekeeping. Google put atomic clocks and GPS in every datacentre so that time itself became trustworthy, and bought back real global consistency.

That last one is the boldest idea I have read in a while. Clocks across machines disagree, and instead of working around it like everyone else, Google decided to make time reliable with hardware and let the database wait out the remaining uncertainty.

The lesson that cuts across all three: no system gets everything. Each one names the thing it will trade and then spends the whole paper owning that choice. That is the real skill, not knowing the systems, but reading the trade.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #learninginpublic

## X thread

**1/**

Day 34 of 60 days of system design: papers day. Dynamo, Bigtable, Spanner. The ones everyone cites and fewer have read.

The surprise: they are readable, because I spent this week simulating their ideas first.

**2/**

By the time I opened Dynamo, I had already built consistent hashing, quorums (R + W > N), and vector clocks in small labs. The paper read like docs for something I half-wrote. Reading after building beats reading cold.

**3/**

The three trades, one line each:

Dynamo: gave up strong consistency, bought always-writable.
Bigtable: gave up the relational model, bought scale + simplicity (LSM SSTables).
Spanner: gave up cheap clocks, bought global consistency with atomic clocks.

**4/**

Spanner is the boldest. Clocks across machines disagree, so instead of working around it, Google made time reliable with atomic clocks + GPS (TrueTime), then had the database WAIT out the leftover uncertainty to guarantee global order.

**5/**

The thread through all three: no system gets everything. Each names the one thing it will trade, then owns it for 14 pages.

The skill is not knowing the systems. It is reading the trade.

Code: github.com/anurag629/system-design-60-days
