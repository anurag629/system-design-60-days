---
title: "Day 34: the papers"
parent: "Week 5: distributed systems"
nav_order: 6
has_children: true
---

# Day 34
## The papers, where the ideas you simulated this week were actually born 📜

Today's one idea: every concept you built this week came from a handful of papers, and they are readable. Dynamo, Bigtable and Spanner are not written for mathematicians. They are written by working engineers explaining a system they shipped, and after five days of simulating their ideas, you will understand them better than most people who cite them.

No coding lab today. The work is reading three papers and writing a one-page summary of each in plain language. That act, compressing a paper into a page you could explain to a teammate, is how the ideas actually stick.

---

## Before you start ⏪

You have the vocabulary now. Day 31 built quorums, so Dynamo's R plus W will read as an old friend. Day 33 built vector clocks, so Dynamo's conflict detection is familiar. Day 29 showed why wall clocks lie, which is the entire reason Spanner exists. Day 9's LSM trees are Bigtable's storage. You are not meeting these ideas cold; you are seeing where they were first written down.

---

## Words you will meet today 📖

Consistent hashing is how Dynamo spreads keys across nodes so that adding or removing a node moves only a small fraction of keys. You measured exactly this on Day 13.

Sloppy quorum and hinted handoff are Dynamo's trick for staying available when nodes are down: write to the next healthy nodes instead, and hand the data back when the right node returns.

An SSTable and a tablet are Bigtable's storage unit (a sorted immutable file, the LSM run from Day 9) and its unit of distribution (a contiguous range of rows).

TrueTime is Spanner's clock that reports time as an interval with a guaranteed bound on error, so the database can wait out the uncertainty and give real consistency across datacentres. It is Day 29's clock problem, solved with atomic clocks and GPS.

External consistency is Spanner's strong guarantee: if transaction A finishes before B starts, every observer sees A before B, globally.

---

## Block 1: read (the whole session today)

### What to read 📚

Read these three, in this order. Budget the whole session; this is the reading day.

- [Amazon Dynamo](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) (2007). Read this one closely. It is the clearest statement of the availability tradeoff ever written, and you have already built its core: consistent hashing (Day 13), quorums with R plus W (Day 31), vector clocks for conflicts (Day 33), and the choice to stay available during a partition (Day 30).
- [Google Bigtable](https://research.google/pubs/pub27898/) (2006). Skim for the shape: how it stores data in SSTables (your Day 9 LSM runs), how it splits rows into tablets, and how it leans on other systems (GFS, Chubby) rather than doing everything itself.
- [Google Spanner](https://research.google/pubs/pub39966/) (2012). Read last. It is the one that reframes the week: Google decided that unreliable clocks (Day 29) were so painful that they would put atomic clocks and GPS in every datacentre to make time trustworthy, and get real global consistency as the reward.

### When a paper does not click (optional)

- [Martin Kleppmann's distributed systems lectures](https://www.youtube.com/playlist?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdiB). If a section fights you, the matching lecture usually unknots it. Use it as a reference, not a replacement for the reading.

### How to read a systems paper (10 min)

You do not read a systems paper front to back like a novel. Read the abstract, then the introduction, then jump to the conclusion, so you know where it is going before you climb in. Then read the body for the three things that matter in every one of these papers.

First, what problem were they actually facing? Dynamo existed because a shopping cart that is ever unavailable loses Amazon money, so availability won over consistency. Spanner existed because sharding across the globe with wall clocks kept corrupting order. The problem explains every choice that follows.

Second, what did they trade away? No system gets everything. Dynamo gave up strong consistency to stay always-writable and spent the rest of the paper managing the mess that creates. Bigtable gave up the relational model for scale and simplicity. Spanner spent money and hardware (atomic clocks) to buy back consistency. Name the trade and the paper snaps into focus.

Third, what one idea is worth stealing? Consistent hashing from Dynamo. The log-structured storage and the reliance on a lock service from Bigtable. TrueTime from Spanner. You are mining for the transferable idea, not memorising the system.

---

## Block 2: drill (40 min) ✍️

Paper first, from memory after reading. Write answers into [`notes/day-34-drills.md`](../notes/day-34-drills.md).

D1. Dynamo chooses availability over consistency during a partition. Name two specific mechanisms from the paper that let it stay writable when nodes are down, and say what mess that creates and how it cleans it up.

D2. Dynamo uses R plus W greater than N (your Day 31). Quote roughly what R, W and N mean in the paper, and explain why an always-writable store might actually set W low and accept the stale-read risk.

D3. Bigtable stores its data in SSTables. Connect that to your Day 9 lab: what kind of storage engine is this, and what does Bigtable get from it that a B-tree would not at that write volume?

D4. Spanner's TrueTime reports time as an interval, not a single instant, with a bound on the error. Why does returning a range let Spanner give stronger consistency than a normal clock, and what does it have to do to be safe (hint: it waits)?

D5. Across all three papers, each one leans on a trade. In one line each, name what Dynamo, Bigtable and Spanner each gave up and what they bought with it.

---

## Block 3: build (summaries)

Today you build understanding, not code. The template is [`labs/day-34-papers/SUMMARIES.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-34-papers/SUMMARIES.md). Copy it into your fork and write a one-page summary of each paper, in your own words, covering: the problem it solved, the key trade it made, the one idea worth stealing, and which day this week you saw that idea as a working simulation.

Keep each to a page. The compression is the point. If you cannot get Dynamo onto one page, you have not finished understanding it yet.

### Deliverable

Your three filled-in summaries, plus one line: which paper surprised you most, and why.

---

## Block 4: write (30 min) 📣

Your angle today is the realisation that these are approachable: "I read the Dynamo paper, and because I had already simulated quorums and vector clocks this week, it read like documentation for something I half-built. Here is the one idea from it I will not forget." Pick one paper and one idea.

Example posts are on the [Day 34 posts](../shares/day-34-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: which papers you read and summarised, the one idea that will stick, and one thing in a paper you still cannot explain.

Day 35 is the week 5 design finale: you design a distributed key-value store, which is essentially Dynamo, using everything you simulated and read this week. Today you read how Amazon did it. Tomorrow you do it yourself.

---

## Solutions 🔑

Open these only after you have read the papers and written your own summaries.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Dynamo stays writable through failures using a sloppy quorum and hinted handoff: if the nodes that should hold a key are down, it writes to the next healthy nodes in the ring instead, with a hint about where the data really belongs, and hands it back when the proper node returns. It also uses replication across N nodes so some can be down. The mess this creates is divergence: two sides of a partition can both accept writes to the same key, producing conflicting versions. It cleans up with vector clocks (your Day 33) to detect the conflict and either reconcile automatically or hand the conflicting versions ("siblings") to the application to merge, as the shopping cart does by unioning items.

D2. N is the number of replicas for a key, W is how many must acknowledge a write before it is considered successful, and R is how many are read. With R plus W greater than N, read and write sets overlap, so a read sees the latest write. An always-writable store might set W low (even 1) so a write succeeds even when most replicas are unreachable, accepting that reads may then be stale or see conflicts, because for Dynamo staying writable mattered more than every read being fresh. The parameters are a dial, exactly as you measured on Day 31.

D3. SSTables make Bigtable an LSM-tree store (your Day 9): writes are appended and flushed as immutable sorted files, merged by compaction. At Bigtable's write volume a B-tree would thrash on random in-place updates (the 11x slowdown you measured), while the LSM turns writes into cheap sequential flushes. Bigtable gets high write throughput and simple, immutable on-disk files that are easy to replicate and cache.

D4. A normal clock hands you a single instant that is silently wrong by some unknown amount, so two datacentres cannot agree on order (Day 29). TrueTime instead returns an interval [earliest, latest] that is guaranteed to contain the true time. Because Spanner knows the uncertainty, it can be safe by WAITING: after committing at time T, it waits until the interval guarantees that T is now in the past everywhere before it lets the result be seen. That commit-wait is how it gives external consistency, trading a few milliseconds of latency for globally correct order. It needs the atomic clocks and GPS to keep the interval tight, or the waits would be too long.

D5. Dynamo gave up strong consistency and bought always-on availability. Bigtable gave up the relational model and general transactions and bought massive scale and operational simplicity (and leaned on GFS and Chubby for storage and coordination). Spanner gave up cheap commodity timekeeping, spending money on atomic clocks and GPS, and bought back real global consistency across datacentres. Three different answers to the same question: what will you trade to make the hard part go away.

</details>

<details markdown="1">
<summary>One-paragraph plain-language summary of each paper</summary>

Dynamo. Amazon needed a store that never refuses a write, because an unavailable cart loses sales, so they built an always-writable key-value store that accepts the cost of eventual consistency. Keys are spread by consistent hashing, each replicated to N nodes; writes need W acknowledgements and reads R, tuned per use; when nodes are down it writes to healthy neighbours (sloppy quorum, hinted handoff) and heals later; conflicts from concurrent writes are tracked with vector clocks and reconciled by the application. You simulated its heart this week: consistent hashing, quorums, and vector clocks.

Bigtable. Google needed to store petabytes of semi-structured data (web pages, crawl data) with high write throughput and simple operations, so they built a distributed sorted map, not a relational database. Data lives in SSTables (immutable sorted files, an LSM engine) on top of GFS, split into tablets served by tablet servers, with Chubby (a lock service) for coordination. It gave up SQL and general transactions for scale and simplicity, and it is the ancestor of HBase and Cassandra's storage.

Spanner. Google wanted Bigtable's scale but with real SQL and real transactions across the globe, and the blocker was time: wall clocks across datacentres disagree, so you cannot order transactions. Their answer was TrueTime, a clock backed by atomic clocks and GPS that reports time as a bounded interval, letting the database wait out the uncertainty and guarantee global order (external consistency). It spent hardware to turn unreliable time into a reliable primitive, which is one of the boldest trades in systems.

</details>
