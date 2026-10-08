---
title: "Day 35: designing a distributed key-value store"
parent: "Week 5: distributed systems"
nav_order: 7
has_children: true
---

# Day 35
## Designing a distributed key-value store, which is basically Dynamo, from the parts you built this week 🗝️

Today's one idea: you can design Amazon's Dynamo now, because you built it in pieces all week. Consistent hashing placed the keys (Day 13), quorums decided reads and writes (Day 31), vector clocks caught the conflicts (Day 33), the CAP choice kept it writable through a partition (Day 30), and logical clocks saved you from trusting the wall clock (Day 29). Today you assemble them into one always-available store and defend every choice.

This is the week 5 finale, a design day. The hard week ends not with more theory but with you putting the theory to work on a real, nasty, distributed problem.

---

## Before you start ⏪

Bring all of week 5, and Day 13's consistent hashing. Yesterday's papers, especially Dynamo, are the reference answer to today's exercise, so if you read them, today is you proving you understood them. If a week-5 idea is still shaky, today is where it either clicks or shows you exactly what to revisit.

---

## Words you will meet today 📖

A key-value store is the simplest database: get(key) and put(key, value), no joins, no queries, just a giant distributed dictionary. Dynamo, Cassandra and Riak are this shape.

A coordinator is the node that handles a given request and talks to the replicas on the client's behalf. In Dynamo any node can coordinate any request.

Sloppy quorum and hinted handoff let a write succeed when the proper replica nodes are down: write to the next healthy nodes with a hint, and hand the data back when the right nodes return.

Anti-entropy is the background repair that compares replicas (often with Merkle trees) and fixes the ones that drifted, so replicas converge even after failures.

Gossip is how nodes learn who is alive and who owns what, by periodically exchanging state with a few peers, so the cluster needs no central registry.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Cassandra deep dive](https://www.hellointerview.com/learn/system-design/deep-dives/cassandra) from Hello Interview. Cassandra is a Dynamo-style store, and this walks the exact pieces you need today: consistent hashing, replication, tunable quorums, and conflict handling.
- [The Dynamo paper](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf), again or for the first time. It is the reference design for today. If you did Day 34, skim your own summary.
- [DDIA](https://dataintensive.net/), the replication and partitioning chapters (5 and 6), for the vocabulary one more time.

Watch, after you have done your own design:
- [Designing a distributed key-value store, Dynamo style](https://www.youtube.com/watch?v=j8iDY_RudJw) by TheSystemSage, about 10 minutes, for a quick full pass.
- Optional deeper: [The Dynamo paper walkthrough](https://www.youtube.com/watch?v=SKlOU7NAUgU) by The Stupid CS Guy, about 25 minutes.

### The whole store, as five decisions you already made (15 min)

A distributed key-value store sounds intimidating until you see it is five of your week-5 days stacked up.

Where does a key live? Consistent hashing (Day 13). Nodes sit on a hash ring, a key hashes to a point, and it belongs to the next N nodes clockwise. This is why adding a node only moves about 1/N of the keys instead of reshuffling everything, and it is the first thing Dynamo describes.

How many copies, and how many must answer? Quorums (Day 31). Each key is replicated to N nodes; a write needs W acknowledgements and a read queries R. Set R plus W greater than N and reads see the latest write. Dynamo lets you tune this per request, and an always-writable store often picks a low W so writes succeed even when nodes are down.

What about concurrent writes to the same key? Vector clocks (Day 33). Two clients writing on two sides of a partition produce versions neither of which happened-before the other. Vector clocks detect that they are concurrent (siblings) rather than silently picking one, and the application reconciles them, the way a shopping cart unions its items.

What happens during a partition? The CAP choice (Day 30). Dynamo chooses availability: both sides keep accepting writes and reconcile afterward, because for a cart, refusing a write is worse than a brief inconsistency. A different product (a bank ledger) would choose consistency and refuse.

And why not just timestamp everything? Because clocks lie (Day 29). Last-write-wins by wall clock silently loses data when clocks skew, so you reach for logical clocks or accept LWW only where losing a concurrent write is genuinely fine.

Add the failure machinery on top, sloppy quorums and hinted handoff to stay writable when nodes are down, anti-entropy to repair drifted replicas, and gossip so the cluster tracks membership without a central registry, and you have Dynamo. Every piece is a day you simulated.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Write your answers into [`notes/day-35-drills.md`](../notes/day-35-drills.md). About 8 minutes each.

D1. Placement. Nodes sit on a consistent-hashing ring and each key is replicated to the next 3 nodes (N=3). When you add one node to a 10-node ring, roughly what fraction of keys change ownership, and why is that the whole reason Dynamo uses the ring (Day 13)?

D2. Quorum tuning. With N=3, give the (W, R) you would choose to stay writable even when 2 of the 3 replicas are down, and separately the (W, R) that guarantees a read sees the latest write. Which satisfies R plus W greater than N, and what does the always-writable choice give up (Day 31)?

D3. Conflict. Two clients put different values to the same key on two sides of a network partition. What does a wall-clock last-write-wins store do (Day 29), and what does a vector-clock store do instead (Day 33)? Which would you want for a shopping cart, and why?

D4. Failure. A write comes in but the nodes that should hold the key are down. Describe sloppy quorum and hinted handoff: how the write still succeeds, and how the data reaches the right nodes once they recover.

D5. CAP in practice. During a partition your store stays available (AP). State the consequence the client must live with and how the store reconciles afterward. Then name one product where you would instead choose CP and refuse writes, and why (Day 30).

---

## Block 3: build (100 min) 🔧

Today you build a design, not code. The template is [`labs/day-35-kv-store/DESIGN.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-35-kv-store/DESIGN.md). Copy it into your fork and fill it in.

Do it against the clock, 45 minutes for a first full pass: requirements and the consistency stance, key placement, replication and quorums, conflict handling, failure handling, and membership. Do not open the Solutions or the Dynamo paper until your 45 minutes are up.

Then improve it with the readings open, marking what you added. That delta is the hard week landing.

### What a strong design has

A weak one says "use Cassandra." A strong one places keys with consistent hashing and says the resharding cost, tunes N, W and R and states what each setting trades, detects concurrent writes with vector clocks instead of silently dropping one, stays writable through a partition with sloppy quorums, and repairs with anti-entropy. In short, it rebuilds Dynamo from parts and can defend each one. Aim for that.

### Deliverable

Your filled-in `DESIGN.md`, and one honest paragraph: which week-5 day did the store lean on hardest, and which part are you still least sure about?

---

## Block 4: write (30 min) 📣

Your angle is the arrival: "A week ago, 'design a distributed database' would have been a wall. Today I designed a Dynamo-style key-value store, and every piece was something I had already simulated: consistent hashing for placement, quorums for reads and writes, vector clocks for conflicts, and the choice to stay available through a partition." Pick the two pieces that clicked hardest.

Example posts are on the [Day 35 posts](../shares/day-35-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it, and look back 📝

Log the three: what you completed, your N, W, R choice and why, and one thing you still cannot explain.

Then the week 5 retrospective, and be honest, because this was the hard week. Write down the three distributed-systems ideas that went from scary words to things you can reason about, and the one that is still fuzzy. The fuzzy one is not a failure; it is your map for what to revisit.

Week 6 is the one you have been waiting for: AI systems. LLM inference serving, the KV cache and batching, vector search, RAG, and agents. The good news is that it is all distributed systems with an expensive GPU in the middle, and you now have five weeks of distributed systems behind you.

---

## Solutions 🔑

Open these only after your own 45-minute design pass.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Adding one node to a 10-node ring changes ownership of roughly 1/11 of the keys, about 9 percent, because only the keys in the arc the new node takes over move; everything else stays put. That is the whole point of the ring (Day 13): plain modulo sharding would remap almost every key when the node count changes, turning "add a server" into "copy the entire dataset," while consistent hashing makes it a small, local shuffle.

D2. To stay writable with 2 of 3 replicas down, you need W = 1 (a write succeeds if any one replica acknowledges), and you would pair it with R = 1 for symmetry, giving fast, always-available reads and writes. To guarantee a read sees the latest write you need R plus W greater than N, for example W = 2 and R = 2 on N = 3 (2 plus 2 is 4, greater than 3), so the read and write sets overlap. W = 1, R = 1 does NOT satisfy the overlap rule, so the always-writable choice gives up read-your-writes freshness: a read can miss a very recent write and see a stale or conflicting value, which you accept because staying available mattered more.

D3. A wall-clock last-write-wins store compares the two writes' timestamps and keeps the larger one, silently discarding the other, and if the clocks are skewed it may even keep the older write (Day 29), losing data with no warning. A vector-clock store (Day 33) sees that neither write happened-before the other, marks them as concurrent siblings, and keeps both for the application to reconcile. For a shopping cart you want the vector-clock behaviour: if two devices added items during a partition, you union the carts rather than throwing one device's additions away. Losing a cart item is a bug report; a duplicate is a shrug.

D4. With sloppy quorum, if the N nodes that should hold a key are down, the coordinator writes to the next N healthy nodes on the ring instead, so the write still reaches W replicas and succeeds. Each such stand-in stores the data with a hint saying which node it really belongs to (hinted handoff). When the proper node comes back, the stand-in notices (via gossip) and hands the data over, then drops its copy. The write stayed available during the failure, and the data found its correct home afterward, without anyone blocking.

D5. Staying available (AP) during a partition means both sides accept writes, so the client must live with the possibility of reading a stale value or getting conflicting versions that need reconciling; the store reconciles afterward with vector clocks and anti-entropy (comparing replicas and merging or picking winners). You would instead choose CP, refusing writes on the minority side, for something like a bank ledger or an inventory count where a double-spend or overselling is unacceptable: there, a brief unavailability is far better than an inconsistency, so you require a real quorum and reject writes you cannot make safely.

</details>

<details markdown="1">
<summary>A worked reference design</summary>

One good answer, and it is essentially Dynamo. Yours will differ in emphasis; what matters is that each piece is justified.

Requirements. Functional: get(key) and put(key, value) across a large cluster. Non-functional: always writable, horizontally scalable by adding nodes, survives node and partition failures, eventual consistency with conflict resolution. This is the Dynamo stance; a CP store would make different calls.

Consistency stance, from D5: AP. Stay writable through partitions and reconcile, because the target workload (carts, sessions, profiles) prefers availability. Note explicitly where you would flip to CP.

Placement, from D1: a consistent-hashing ring. Each key hashes onto the ring and is owned by the next N nodes clockwise, with virtual nodes so load spreads evenly. Adding or removing a node moves only about 1/N of keys.

Replication and quorums, from D2: replicate each key to N nodes (say 3). Tunable W and R per request; default to a quorum (W = R = 2 on N = 3) for overlap, drop W for write-availability when the workload demands it. Any node can coordinate.

Conflicts, from D3: version each value with a vector clock. Concurrent writes become siblings returned to the client to merge; never silently drop one by wall-clock time.

Failure handling, from D4: sloppy quorum and hinted handoff keep writes succeeding when owners are down; anti-entropy with Merkle trees repairs replicas that drifted; gossip spreads membership and liveness so there is no central coordinator to fail. Metadata that truly must be consistent (ring membership in some designs) can sit behind a small consensus group (Day 32), but the data path itself avoids consensus to stay fast and available.

The sentence that makes this sound senior: "it is Dynamo: consistent hashing places keys, tunable quorums trade freshness for availability, vector clocks keep conflicts instead of losing them, and sloppy quorums plus anti-entropy keep it writable and self-healing through failure."

</details>

<details markdown="1">
<summary>Week 5 in one page</summary>

The hard week. One truth underneath it: the network is unreliable, machines fail independently, and clocks lie, and the whole field is ideas for keeping promises anyway.

Day 29, time and failure. Wall clocks across machines disagree, so ordering events by timestamp silently loses data. Partial failure is the normal case, not the exception.

Day 30, CAP and PACELC. During a partition you must choose availability or consistency; it is a per-operation choice, not a database label. And even with no partition, you trade consistency against latency all the time.

Day 31, quorums. Replicate to N, write to W, read from R; R plus W greater than N makes reads see the latest write. The parameters are a dial between consistency and availability.

Day 32, consensus and Raft. A cluster agrees on a leader by majority vote, with randomized timeouts to avoid split votes, and tolerates a minority failing. Agreement is expensive, so you use it sparingly.

Day 33, logical clocks. Lamport gives a consistent order but cannot spot concurrency; vector clocks can, which is how you detect conflicts instead of losing writes.

Day 34, the papers. Dynamo, Bigtable and Spanner, each naming the one thing it traded.

Day 35, today. A distributed key-value store assembled from all of it.

If this week bent your brain, that is correct; it bends everyone's. What you have now is not mastery of distributed systems, which takes years, but a working map: you know what CAP really says, why quorums are a dial, how consensus works, and why clocks are not to be trusted. That map is enough to reason about any distributed system you meet, and to read any paper that comes next. Week 6 points all of it at a GPU.

</details>
