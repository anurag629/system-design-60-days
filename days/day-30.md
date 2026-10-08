---
title: "Day 30: CAP, for real, and PACELC"
parent: "Week 5: distributed systems"
nav_order: 2
has_children: true
---

# Day 30
## CAP for real, and its grown-up cousin PACELC 🌐

Today's one idea: the famous "consistency, availability, partition tolerance, pick two" is a cartoon. The real theorem is smaller and far more useful. Partition tolerance is not something you choose, it is something the network does to you. The actual choice is this: when a partition happens, each operation must pick between staying consistent and staying available. And that choice is made per operation, by a policy, not stamped once on the whole database. Today you feel that choice by building it.

Yesterday you admitted that networks fail and clocks lie. Today you take the single most quoted, most misquoted idea in distributed systems and make it concrete, by partitioning a toy store and watching the same workload fail in two opposite ways depending only on the policy you picked.

This is the reading-heavy day of a hard week. Go slow. If your brain bends, that is the day working, not you failing.

---

## Before you start ⏪

Bring Day 29: partial failure and the fact that a node cannot tell "the other side is dead" apart from "the link to the other side is dead." That ambiguity is the whole reason today is hard. A partition looks exactly like a crash from the far side, and you still have to decide what to do.

One concept from Week 2 helps a lot: replication (Day 12). Today a write may have to reach more than one copy, and whether it waits for those copies is the hinge the entire day turns on.

---

## Words you will meet today 📖

A network partition is when the link between two groups of nodes drops, so each group can still talk within itself but not across. Both halves are alive and serving. They just cannot reach each other. This is not a crash, it is a split.

Consistency, in the CAP sense, means every read sees the most recent write, as if there were one copy. This is the strong, linearizable kind, stricter than the "eventual" kind you will meet tomorrow.

Availability, in the CAP sense, means every request to a living node gets a non-error response. Not "fast," just "it answered instead of refusing."

A quorum is a majority of the nodes, floor(N/2) + 1. For five nodes that is three. The trick of a quorum is that two different majorities must overlap in at least one node, so two sides of a partition can never both have one. That overlap is what prevents split-brain.

CP and AP are the two ways to resolve the partition. CP (consistent and partition-tolerant) refuses service on the side that cannot reach a quorum, so it never diverges but goes unavailable there. AP (available and partition-tolerant) keeps serving on both sides, so it stays up but the copies diverge.

PACELC is the fuller rule, from Daniel Abadi. It reads: if there is a Partition, trade Availability against Consistency (that is CAP). Else, with no partition at all, trade Latency against Consistency. The "else" half is the part CAP leaves out, and it is the part you live with every single day.

Reconciliation is what AP owes you later. When a partition heals and two copies disagree, something has to merge them: last write wins, or vector clocks, or an application-level merge. More on this tomorrow and on Day 33.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these, in this order:
- [Please stop calling databases CP or AP](https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html) by Martin Kleppmann. Short, sharp, and it is the thesis of the whole day: CAP's definitions are so specific that labelling a real database "CP" or "AP" is usually wrong. Read this first.
- [Problems with CAP, and Yahoo's little known NoSQL system](https://dbmsmusings.blogspot.com/2010/04/problems-with-cap-and-yahoos-little.html) by Daniel Abadi. This is where PACELC comes from. The key insight: CAP ignores latency, and latency is the trade you actually make most days.
- [CAP Twelve Years Later: How the "Rules" Have Changed](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/) by Eric Brewer, who stated CAP in the first place. He walks back the slogan himself and explains that the choice is narrow, per-operation, and only during a partition.
- [Jepsen: consistency models](https://jepsen.io/consistency), as a reference. You do not need to memorise the lattice, but look at it once so you know "consistency" is a whole family, not a single switch.

Watch, when a paper does not click:
- [What is CAP Theorem?](https://www.youtube.com/watch?v=eWMgsk7mpFc) by IBM Technology, about 9 minutes. A clean whiteboard walkthrough of the three properties and the partition choice.
- [CAP Theorem and PACELC in distributed systems](https://www.youtube.com/watch?v=BaKtC-VIYrM) by SoftwareDude, about 15 minutes. Covers the CAP-to-PACELC jump that most explanations skip.

### Why "pick two" is a cartoon (14 min)

The slogan says you get two of consistency, availability, and partition tolerance. The problem is that it quietly puts all three on the same footing, as if you sat down and picked your favourite two. You do not.

Partition tolerance is not a feature you choose. It is a fact of the world. The moment your system runs on more than one machine talking over a network, that network can drop, and when it drops you have a partition. You cannot tick a box that says "no partitions please." A single machine on one power supply can refuse partition tolerance, and nothing else can. So for any real distributed system, partition tolerance is forced, and the honest question is only about the other two.

Here is the sharper version. When there is no partition, there is no dilemma: a healthy system is happily consistent and available at the same time. CAP has nothing to say about the good times. The choice only appears during a partition, and in that moment it is a straight either-or. Either you keep serving on both sides and let the copies drift apart (you gave up consistency to keep availability), or you refuse service where you cannot guarantee correctness (you gave up availability to keep consistency). You cannot have both, because the two sides cannot talk, so a write accepted on one side simply cannot be seen by a read on the other.

That is the whole theorem, correctly stated: during a partition, consistency and availability trade off against each other. "Pick two" turns a narrow, temporary, per-operation decision into a permanent personality trait of the database. It is not. Kleppmann's piece says this better than I can, and it is why the title of his post is a plea.

### The train ticket counter: a partition you can picture (12 min)

Picture a railway reservation office with two counters, A and B, both selling seats from the same chart. Normally they share one live register, so when counter A sells berth 42, counter B sees it instantly and will not sell it again. Consistent and available, no drama. That is the no-partition world.

Now the phone line between the two counters drops. Both counters are still open, still have queues, but they can no longer see each other's sales. This is the partition. One berth is left on the chart, and a passenger walks up to each counter at the same time asking for it. What do you do?

One answer is the CP answer. Counter B, which cannot confirm with the main register, simply refuses: "sorry, system is down, please wait." Annoying, a lost sale, an unhappy passenger. But the berth is never sold twice. You chose correctness over service. The minority counter went unavailable.

The other answer is the AP answer. Both counters sell the last berth, because refusing a paying customer feels worse than the risk. Both passengers walk away happy, for now. The office stayed fully available. But when the phone line comes back, the register has two people holding berth 42, and someone in a back office has to sort that out: upgrade one, bump one, refund one. That is a conflict, and reconciliation is the cost AP deferred to later.

Same partition. Same single berth. CP lost a sale and kept the data clean. AP kept every sale and created a mess to clean up. Neither is wrong. They are different promises to the passenger, and crucially, the office could run counter A one way and counter B the other, or treat seat sales strictly and seat enquiries loosely. The policy is per operation, which is exactly what the lab makes you feel.

### The per-operation truth, and why "is Postgres CP or AP" is the wrong question (12 min)

Here is the part that separates people who have read the slogan from people who understand it. The CP-or-AP choice is not a property of the database. It is a property of each operation, set by configuration and by what that operation asks for.

Take a Dynamo-style store like Cassandra. A single cluster will happily serve one query at consistency level ONE (reply from any one replica, fast, possibly stale: that is an AP-flavoured operation) and the very next query at QUORUM or ALL (wait for a majority, refuse if you cannot get it: that is a CP-flavoured operation). Same database, same data, same partition, opposite behaviour, decided by the operation. So "is Cassandra CP or AP" has no single answer. The honest reply is "which operation, tuned how?"

Even a classic leader-based SQL database is not simply "CP." It depends on whether replicas are synchronous or asynchronous, whether you allow reads off a replica, what happens to the minority side when the leader is cut off. These are knobs, and each knob is a point on the CAP line for that path.

This is why the lab drives one single workload through two policies rather than two databases. The partition is identical. The workload is identical. The only thing that changes is the policy each operation follows, and that alone flips the system from "unavailable but clean" to "available but divergent." When you have watched that happen on your own screen, you will never again say a database "is CP." You will ask which operation, and how it is configured.

### PACELC: the trade that is there even on a perfect day (12 min)

CAP has a blind spot, and Abadi named it. CAP only speaks during a partition. But partitions are rare. What about the 99.9 percent of the time when the network is fine? CAP says nothing, and yet you are still making a consistency trade in that time, constantly.

PACELC fills the gap. The rule: if Partition, then Availability versus Consistency (the CAP part), Else Latency versus Consistency. Read the "else" slowly, because it is the useful half. Even with no partition anywhere, if you want strong consistency you must pay latency, and if you want low latency you must give up some consistency.

Why? Replication. If a write must be seen by every reader immediately (strong consistency), the write has to reach the replicas and wait for them to acknowledge before it returns. That is synchronous replication, and it costs a network round trip on every write. If instead the write returns as soon as the local node has it and the replicas catch up a moment later (asynchronous replication), the write is fast, but for a short window a reader hitting a lagging replica sees an old value. You did not touch the "pick two." You traded consistency for latency, on a completely healthy system.

The lab measures this directly. A synchronous write waits for the replica and comes out around 11 times slower than an asynchronous one. The asynchronous one is quick but leaves a staleness window, and a slice of reads fall into it. This is the trade you make every day, in every geo-distributed system, long before any cable gets cut. People argue about CAP in interviews. People lose sleep over PACELC in production. Abadi's framing is the one you will reach for most, so give the second reading real attention.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-30-drills.md`](../notes/day-30-drills.md). About 8 minutes each.

D1. State CAP properly. During a partition you choose between which two letters, why is partition tolerance not really optional for anything that spans a network, and in one line, why is "pick two" a cartoon?

D2. The per-operation point. Can one database be both CP and AP? Give a real example of a single system where one operation is served consistent-or-refused and another is served available-but-stale, and say what actually decides which.

D3. Quorum arithmetic, straight from the lab. A 5-node cluster with a strict majority quorum of 3. A partition splits it 3 and 2: which side keeps serving writes, which refuses, and why are there zero conflicts afterwards? Now, could any partition of those 5 nodes ever leave two sides both holding a quorum at once? What does that impossibility buy you?

D4. PACELC in the PA/EL notation. Classify a Dynamo-style store and a fully synchronous primary-replica SQL setup. For a "PA/EC" system, explain each half in plain words. Then the number: local apply is 1 ms and a cross-region round trip is 80 ms, so how much does synchronous cross-region replication add to every single write, and what does going async trade for that?

D5. The AP bill. After a heal you have two different values for one key. Name two honest reconciliation strategies and the specific thing last-write-wins silently throws away. Then tie it back: the lab healed with 16 conflicts, so what exactly would last-write-wins have quietly dropped there?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-30-cap/cap.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-30-cap/cap.py).

It is a deterministic simulation, standard library only, no sockets and no threads, and it runs in under a second. Five nodes. A partition splits them into a majority side (three nodes, a quorum) and a minority side (two nodes, no quorum). Part 1 runs a workload with no partition and confirms all five nodes agree. Part 2 switches the partition on and replays one single workload under two policies, CP and AP, and you watch them fail in opposite ways. Part 3 drops the partition entirely and measures the PACELC trade: synchronous versus asynchronous replication, latency against staleness.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. During the partition, under the CP policy, what percent of operations get rejected because they land on the minority side? (Hint: the minority is 2 of the 5 nodes.)
- P2. During the partition, under the AP policy, how many of the 16 keys end up in conflict and need reconciling after the heal?
- P3. With no partition, synchronous write latency divided by asynchronous write latency. How many times slower is the write that waits for the replica? (Local apply is about 1 ms, a replica round trip about 10 ms.)
- P4. With no partition, under asynchronous replication, what percent of reads land inside the replication window and come back stale?

P1 and P2 are the pair to feel in your gut. CP's failure is a rejection count. AP's failure is a conflict count. Write both down before you look.

### Fill in the TODOs

1. TODO 1 is the CP choice itself, in one line: an operation may proceed only if its side can still reach a quorum. This is why the minority refuses.
2. TODO 2 is the AP cost, measured: a key is a conflict only if both sides wrote it and the two values disagree.
3. TODO 3 is the PACELC latency half: a synchronous write waits for the replica, so its cost is the local apply plus a full network round trip.
4. TODO 4 is the PACELC staleness half: under async, a read is stale if it lands before the replication window closes.

```bash
cd labs/day-30-cap
python3 cap.py
```

### What you're going to discover

Part 1 is calm on purpose. No partition, every write reaches all five nodes, every read is fresh, zero divergence. This is the baseline, and it is worth seeing so you register exactly what the partition takes away.

Part 2 is the lesson. The same 1,000 operations, the same split, run twice. Under CP, the minority side cannot reach a quorum, so it refuses every operation that lands on it: around 38 percent rejected, the store is unavailable for those, and the heal finds zero conflicts because only one side ever wrote. Under AP, nothing is refused, the store stays fully available, and the heal finds all 16 keys in conflict because both sides wrote them to different values. Read those two scoreboards side by side. That contrast is the entire day.

Part 3 is the one people have never seen. With no partition at all, the synchronous write comes out about 11 times slower than the asynchronous one, purely from waiting on the replica, and the asynchronous path serves roughly 12 percent stale reads from its replication window. CAP never enters. You are trading consistency for latency on a perfectly healthy system, which is what PACELC is trying to tell you.

### Traps ⚠️

- Do not read "38 percent rejected" as a flaw in CP. It is CP doing its job: refusing where it cannot be correct. The zero conflicts next to it is the reward for that refusal. The two numbers are a pair.
- Equally, AP's 16 conflicts is not AP being broken. It stayed up through the whole partition, which was the goal. The conflicts are the bill, payable at reconciliation time, and for many systems that is a fine deal.
- The PACELC latency gap is not about a partition. Re-read that if it feels strange. There is no partition in Part 3 at all. The cost is the replica round trip on every synchronous write, full stop.
- The exact percentages will be identical for you, because the simulation is seeded. If your numbers differ, you changed the seed or the constants, not discovered a new truth. Trust the contrast between the two policies, which is the point.

### Deliverable

[`labs/day-30-cap/RESULTS.md`](../labs/day-30-cap/RESULTS.md) has a skeleton. Paste the output, and write one line: during the partition, how many operations did CP reject (and with how many conflicts), how many did AP reject (and with how many conflicts), and what does that tell you about the question "is this database CP or AP?"

---

## Block 4: write (30 min) 📣

Your angle today is the correction most people need: "I always thought CAP was 'pick two.' Today I simulated it and learned the truth is narrower and more useful. During a partition, each operation chooses between consistency and availability, and the database does not decide, the operation's policy does." The scoreboard, CP rejecting 38 percent with zero conflicts next to AP rejecting nothing with 16 conflicts, is the screenshot. If you have room, add the PACELC punchline: even with no partition, strong consistency cost about 11 times the write latency.

Example posts are on the [Day 30 posts](../shares/day-30-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the CP-rejected-versus-AP-conflicts pair you measured, and one thing you still cannot explain.

Day 31 picks up exactly where AP left you hanging. If both sides accepted writes and diverged, how does a real system like Amazon's Dynamo heal that without a human in a back office? The answer is quorums done properly (R plus W greater than N), read repair, and eventual consistency. Today you felt the problem. Tomorrow you build the machinery that lives with it on purpose.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. During a partition you choose between Consistency and Availability. Partition tolerance is not optional for anything spanning a network, because a partition is something the network does to you, not a feature you enable; the only way to refuse partitions is to run on a single node, which is not a distributed system at all. So for a real distributed system P is forced, and the genuine choice is just C versus A, and only during a partition. "Pick two" is a cartoon because it pretends all three are equal menu items you choose once and for all, when really P is forced on you and the C-or-A choice is narrow, temporary (it only bites during a partition), and made per operation.

D2. Yes, easily, and that is the whole point. Cassandra is the clean example: one query at consistency level ONE replies from any single replica (fast, possibly stale, available even when most replicas are unreachable: AP-flavoured), while the next query at QUORUM or ALL waits for a majority and refuses if it cannot reach one (consistent-or-refused: CP-flavoured). Same cluster, same data, same partition. What decides is the operation's requested consistency level, set per query, not any fixed property of "the database." This is why "is X CP or AP" is the wrong question; the right one is "which operation, configured how."

D3. The majority side (3 nodes) keeps serving writes, because 3 is a quorum. The minority side (2 nodes) refuses, because 2 is not a quorum, so it goes unavailable for the duration. There are zero conflicts afterwards because only the majority side ever accepted writes, so no key was ever given two different values, and the heal simply catches the minority up. No, two sides can never both hold a quorum of 5 at once: any two majorities of 5 (each at least 3) must share at least one node, and a single node cannot be on both sides of a partition. That overlap is exactly what a quorum buys you: it makes split-brain arithmetically impossible, which is why a CP system refuses rather than risks it.

D4. A Dynamo-style store is PA/EL: during a Partition it favours Availability, and Else it favours low Latency, both at the cost of strong consistency. A fully synchronous primary-replica SQL setup is PC/EC: during a Partition it favours Consistency (the minority refuses), and Else it still favours Consistency by waiting for replicas, paying latency. A "PA/EC" system means: when partitioned, stay Available (let copies diverge), but when healthy, be strongly Consistent (wait for replicas, accept the latency). The number: synchronous cross-region replication adds a full round trip, 80 ms, to every single write, so a 1 ms local write becomes about 81 ms. Going async drops that back to roughly 1 ms, trading it for a staleness window in which a reader on a lagging replica sees an old value.

D5. Two honest strategies: last-write-wins (keep the value with the highest timestamp, discard the other) and causal merge using vector clocks (keep both as siblings when they are genuinely concurrent, and let the application or the next write resolve them); a third common one is an application-level merge, like taking the union of two shopping carts. What last-write-wins silently throws away is the losing write entirely: one of the two concurrent updates just vanishes, with no trace, even though a real user made it. Tied to the lab: it healed with 16 conflicts because both sides wrote all 16 keys to different values during the partition. Last-write-wins would have "resolved" all 16 by keeping one side's value per key and dropping the other, so up to 16 genuine writes would disappear without anyone being told. That silent data loss is exactly why Dynamo keeps siblings instead, which is tomorrow's topic.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-30-cap/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-30-cap/solution.py).

TODO 1, the CP choice in one line. An operation may proceed only if its side can still reach a quorum, which is why the minority refuses:

```python
return side_live_count >= QUORUM
```

TODO 2, the AP cost measured. A key is a conflict only if both sides wrote it and the two values disagree:

```python
return val_a is not None and val_b is not None and val_a != val_b
```

TODO 3, the PACELC latency half. A synchronous write waits for the replica, so it pays the local apply plus a full network round trip:

```python
return LOCAL_MS + RTT_MS + net_jitter
```

TODO 4, the PACELC staleness half. Under async, a read is stale if it lands before the replication window has closed:

```python
return now < last_write_time + REPL_DELAY_MS
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. The simulation is seeded, so these numbers are exactly reproducible.

```
==============================================================================
Part 1: no partition. Replication keeps all five nodes agreeing.
==============================================================================
  1,000 ops over 16 keys, all five nodes connected.
    writes replicate to all 5 nodes synchronously.
    reads served: 380, of which stale: 0
    keys where the nodes disagree: 0
  Everyone agrees, every read is fresh. This is the baseline that the
  partition is about to break. Nothing here forced a hard choice yet.

==============================================================================
Part 2: partition ON. One workload, two policies, opposite failures.
==============================================================================
  CP policy (consistency first): refuse any op without a quorum.
    majority side ([0, 1, 2]) has 3 nodes, a quorum, serves.
    minority side ([3, 4]) has 2 nodes, no quorum, refuses.
    operations served:   617
    operations REJECTED: 383  (38.3% unavailable)
    conflicts to reconcile after heal: 0
    the minority is DOWN for the whole partition, but no key ever got
    two values, so the data comes out clean. CP traded availability.

  AP policy (availability first): every node accepts every op.
    operations served:   1,000
    operations REJECTED: 0  (0.0% unavailable)
    conflicts to reconcile after heal: 16
    nobody was ever turned away, but the two sides wrote the same keys
    to different values, so the heal finds a pile of conflicts. AP
    stayed up and traded consistency.

  Same partition. Same workload. CP went unavailable to stay
  consistent; AP stayed available and went inconsistent. The database
  did not pick a letter. The OPERATION'S policy did.

==============================================================================
Part 3: PACELC. No partition, and STILL a trade: latency vs consistency.
==============================================================================
  Synchronous replication: the write waits for the replica to ack.
    average write latency: 11.50 ms
  Asynchronous replication: the write returns after the local apply.
    average write latency: 1.00 ms
    sync is 11.5x slower per write, for the SAME write.

  Staleness over 2,016 reads (simulated clock, 1 ms per step):
    async stale reads: 251  (12.5% of reads)
    sync  stale reads: 0  (0.0% of reads)
  Async bought the low latency with a window where a replica serves
  an old value. Sync bought the fresh read with a round trip on every
  write. No partition anywhere. The trade is there on a good day too.

==============================================================================
Scoreboard
==============================================================================
  P1 CP rejected                 you =  40.0   actual =    38.3 %       close enough
  P2 AP conflicts                you =  16.0   actual =    16.0 keys       close enough
  P3 sync / async latency        you =  11.0   actual =    11.5 x       close enough
  P4 async stale reads           you =  15.0   actual =    12.5 %       close enough

==============================================================================
The number to carry
==============================================================================
  During the SAME partition, under the SAME workload:
    CP rejected 38% of ops to stay consistent, and healed with
       0 conflicts. It chose consistency and gave up availability.
    AP rejected 0% of ops and stayed fully available, but healed
       with 16 conflicts to reconcile. It chose availability and
       gave up consistency.
  The database did not choose a letter. Each operation's policy did.
  And PACELC: even with no partition, sync writes were 11x slower while
  async served 12% stale reads. You trade C against L all the time.
```

Part 1 is the baseline. No partition, writes replicate to all five nodes, so every node holds the same thing and every one of the 380 reads was fresh. Zero divergence. This is CAP's good times, the part the slogan never mentions, and it is here so you can see precisely what the partition removes.

Part 2 is the day. One workload, one partition, two policies. CP refused the 383 operations that landed on the minority side, because that side could not reach a quorum of 3, so roughly 38 percent of traffic got an error and the store was unavailable for it. The payoff sits right beside it: zero conflicts, because only the majority ever wrote, so no key was ever given two values. AP did the opposite. It refused nothing, stayed fully available through the entire partition, and in exchange all 16 keys came out of the partition holding different values on the two sides, 16 conflicts that reconciliation has to clean up. Put the two scoreboards next to each other and the lesson is unmissable: the partition was identical, the workload was identical, and the only thing that changed was the per-operation policy.

Part 3 is PACELC, and there is no partition anywhere in it. The synchronous write waited for the replica to acknowledge and came out at 11.5 ms against the asynchronous write's 1.0 ms, about 11 times slower, purely from the network round trip. The asynchronous path was fast but left a replication window, and 12.5 percent of reads fell inside it and saw a stale value. This is the trade you make on a perfectly healthy day, and it is the one that matters most in practice, because partitions are rare but every write you serve is paying one side of this bargain right now.

The one line to carry out of today: during a partition, consistency and availability trade off per operation (CP rejected 38 percent to heal clean, AP rejected nothing and healed with 16 conflicts), and even with no partition, PACELC says you are still trading consistency against latency, which is why "is this database CP or AP" is a question with no answer until you say which operation and how it is configured.

</details>
