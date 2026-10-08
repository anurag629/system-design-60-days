---
title: "Day 31: replication and quorums"
parent: "Week 5: distributed systems"
nav_order: 3
has_children: true
---

# Day 31
## Replication and quorums, or how Amazon's cart stayed up while the servers were on fire 🛒

Today's one idea: when you keep N copies of your data, you do not have to write to all of them or read from all of them. You write to W copies, you read from R copies, and if R plus W is greater than N, the set you read and the set you wrote are forced to share at least one copy. That shared copy holds your latest write, so the read is guaranteed to see it. One inequality, R + W > N, and strong consistency falls out of plain counting. Turn the knob the other way, let R + W drop to N or below, and reads start missing writes in a fraction you can measure.

Yesterday CAP told you that during a partition you must choose between staying consistent and staying available. Today you meet the actual machinery that lets you make that choice per operation, and you see that it is not a mysterious database setting. It is three small numbers you pick yourself.

This is the hard week, so one reassurance before we start. Quorums look like arithmetic trivia the first time, and then one day the overlap clicks and you cannot unsee it. Today is the day we make it click, by measuring it.

---

## Before you start ⏪

You need Day 12 fresh: one leader, many followers, and replication lag. Today we drop the single leader entirely and let any replica take a write, which is the leaderless, Dynamo style. You also want yesterday's CAP framing in mind, because a quorum is how you dial the consistency-versus-availability tradeoff in practice. The lab is pure Python, standard library, no network and no threads, so Day 2's comfort is plenty. If you can picture N copies and someone asking a few of them a question, you are ready.

---

## Words you will meet today 📖

N, W and R are the three numbers that define a quorum. N is how many replicas hold a copy of each key. W is how many of them a write must reach before it is called done. R is how many of them a read asks before it answers.

A quorum is just "enough replicas". A write quorum is W replicas, a read quorum is R replicas. The word sounds grand, but it only ever means "the number you insist on hearing from".

The quorum condition is R + W > N. When it holds, every read quorum and every write quorum overlap in at least one replica, so a read is guaranteed to see the latest completed write. This is the whole day in five symbols.

A version is a number that climbs with every write, so the newest value is simply the one with the highest version. A read that asks several replicas keeps the highest version it sees. In real systems this is a vector clock or a timestamp; here it is a plain counter.

Read-repair is the trick where a read that notices some replicas are behind writes the newest value back to them, healing the laggards as a side effect of being read. The system fixes itself while answering you.

A sloppy quorum is what Dynamo does when the usual replicas are unreachable: it writes to whatever N healthy nodes it can find and hands the data back to the right homes later (hinted handoff). It keeps you writable through a partition, at the cost of a weaker guarantee for a while.

Eventual consistency is the honest name for what a low quorum gives you: the copies disagree for a moment, and if writes stop they converge. Not now, but soon.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [DDIA chapter 5, the quorums section](https://dataintensive.net/). Kleppmann builds leaderless replication, writes to W, reads from R, and the R + W > N condition, then the honest small print about when quorums still go stale. This is the spine of today.
- [Amazon Dynamo paper](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf), 2007. The origin of everything today. Read sections 4.5 (replication and consistency), 4.6 (versioning), and 4.8 (handling failures, sloppy quorum and hinted handoff). It is written by working engineers and it reads easily.
- [Cassandra's Dynamo architecture](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html), the official docs. Dynamo's ideas as a live, tunable database: consistency levels, the W + R > RF rule by name, read-repair and hinted handoff. The cleanest modern map of today onto a real system.

Watch, when you want the whiteboard version:
- [Distributed Systems 5.2: Quorums](https://www.youtube.com/watch?v=uNxl3BFcKSA) by Martin Kleppmann, about 14 minutes. The overlap drawn out properly, by the person who wrote DDIA. Watch this one.
- Optional, to bridge from Day 12: [Distributed Systems 5.1: Replication](https://www.youtube.com/watch?v=mBUCF1WGI_I), also Kleppmann, about 17 minutes. Single-leader, multi-leader and leaderless, side by side, so you see where quorums fit.

### Many copies, and nobody in charge (14 min)

Day 12 had a leader. Every write went to one machine, and that machine shipped the change to the followers. Simple, but the leader is a single point of failure and a single bottleneck for writes. Dynamo asked a sharp question: what if there is no leader at all? What if every replica can take a write, and we sort out agreement afterwards?

Picture it like this. You and four friends are planning a trip, five of you, and each of you keeps the plan in your own head. That is N equals 5. Now the venue changes. You do not call all five friends, that is slow and one of them never picks up. You call some of them, say three, and consider the plan updated. That is W equals 3. Later, someone wants to know the current venue. They do not survey all five either. They ask three friends and take the most recent answer. That is R equals 3.

Here is the question that is the whole day. Is the person who asks three friends guaranteed to reach at least one friend who knows the new venue? You told 3 friends. They ask 3 friends. There are only 5 friends in total. Three plus three is six, and six is bigger than five, so the two groups cannot be completely separate. At least one friend is in both groups, and that friend knows the new venue. The asker is guaranteed to hear it.

That is a quorum. N copies, write to W, read from R, and the guarantee is R + W > N. It is not a database feature you switch on. It is a counting fact about overlapping groups.

### The quorum condition, R + W > N (12 min)

Let me say the overlap precisely, because it is the one thing to carry out of today.

A write of the newest value reaches some set of W replicas. A read asks some set of R replicas. Both sets are drawn from the same N replicas. If those two sets never shared a replica, you could line them up side by side with no overlap, and that would need W plus R distinct replicas. But you only have N. So the moment W + R is strictly greater than N, a no-overlap arrangement is impossible. The two sets must collide in at least one replica, and that replica carries the newest write. The read sees it. Every time, not most of the time.

Flip it around and the failure is just as clean. If R + W is less than or equal to N, you can arrange the read set and the write set to be completely separate. Say N is 3, you write to one replica and read from one replica. The replica you read might simply not be the one you wrote. Now the read misses the latest value and hands you something older. Nobody did anything wrong. The arithmetic left a gap, and the read fell through it.

This is why the condition is strict, greater than, not greater than or equal. R + W equal to N is not enough. With N equals 6, W equals 3, R equals 3, the write set and the read set can be exactly the two halves of the cluster, touching nowhere. Three plus three equals six equals N, and a read can miss a write. You need to tip it over, R + W > N, even by one.

In the lab you will set R + W > N and watch 100 percent of reads come back fresh, across several different W and R choices. Then you will set R + W <= N and watch a measurable slice go stale, matching the combinatorics to the decimal. The overlap is not a story you take on faith. It is a number you print.

### Breaking the rule on purpose, and healing later (12 min)

So far this sounds like you should always keep R + W > N and never think about it again. But Dynamo, the thing that ran Amazon's shopping cart, often did not. It deliberately chose a low W so that a write almost never fails, even when replicas are down or the network is split. An add-to-cart that gets rejected is lost revenue and an annoyed customer. Amazon decided it would rather accept the write onto whatever replicas it could reach and clean up the mess afterwards. That is the availability half of yesterday's CAP choice, made concrete.

What is the mess? With a low quorum the copies disagree for a while. Two replicas might hold two different versions of your cart because a write reached one and not the other. Dynamo's answer has two parts. First, versioning, so the system can tell which value is newer, or notice that two values conflict and neither is strictly newer. Second, read-repair: when a read gathers R replicas and sees that some are behind, it writes the newest value back to the stale ones before answering. The cluster heals as a side effect of being read. For replicas that no read happens to touch, a background anti-entropy process and hinted handoff finish the job. In the lab you will write a value to just one replica out of five and watch a handful of repairing reads drag the whole cluster up to date.

There is a famous wart worth knowing. Because the cart was modeled so that no write is ever lost, a deleted item could occasionally come back. Two divergent carts get merged by union, and if one copy still had the item you removed, the merge keeps it. For a cart that is a tiny, recoverable annoyance, you remove it again. For a bank balance, merging two versions by union is nonsense and losing a write is a disaster. That is the whole point: the quorum is a knob, and where you set it depends on whether a stale or resurrected value costs you a shrug or a lawsuit.

### Tuning the knob: write-heavy, read-heavy, balanced (10 min)

The same N gives you a family of choices, and they all keep R + W > N if you want strong reads. What changes is where the cost and the fragility land.

Set W to 1 and R to N. A write waits for a single acknowledgement, so writes are fast and almost never blocked, even with several replicas down. But a read now needs every replica to answer, so one dead replica takes all reads down. This is the write-heavy corner: cheap, durable writes, brittle reads. Good for something you write constantly and read rarely.

Set W to N and R to 1. The mirror image. Reads are instant and survive almost any failure, writes must reach every replica and one dead replica stalls all writes. The read-heavy corner, good for data written once and read a million times.

Set W and R both to N/2 + 1, a simple majority each. Now both pay a medium cost, and here is the nice part: both survive the most failures. On N equals 5, a majority is 3, and 3 of 5 tolerates 2 replicas being down, for reads and for writes alike. This balanced middle is why "majority quorum" is the sensible default when you do not have a strong reason to lean one way. In the lab you will measure all three under a 10 percent per-replica failure rate, and the balanced setting will post about 99 percent availability for both reads and writes while the lopsided ones sit near 59 percent on their weak side.

One last thing to hold onto. A quorum keeps you available through failure as long as you can still gather W replicas for a write, or R for a read. With a majority quorum on five nodes, two can be down and you carry on, reading fresh and writing durably. That resilience, and not the raw speed, is the real reason this design runs so much of the internet.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-31-drills.md`](../notes/day-31-drills.md).

D1. N=5. Which of these give strong consistency, R + W > N: W=3 R=3, W=2 R=3, W=1 R=4, W=4 R=1? For W=3, what is the smallest R that still guarantees a read sees the latest write, and why?

D2. The overlap, proved. N=6, W=4, R=3: show a read is guaranteed to see the latest write. Then N=6, W=3, R=3: is it still guaranteed? If not, write down an actual write set and read set that miss each other.

D3. Stale odds. N=3, W=1, R=1: a write lands on one random replica, a read asks one random replica. What is the chance the read misses the write? Now W=2, R=1 on N=3: strong or not, and what fraction of reads are stale?

D4. Tuning for a goal. N=5. You want writes to survive 2 replicas being down and reads to stay strongly consistent. What is the largest W that survives 2 failures, what is then the smallest R with R + W > N, and what does that R cost you compared to reads that did not care about strong consistency?

D5. The Dynamo cart. Amazon's cart used a low W so an add-to-cart is almost never rejected. What consistency did that trade away, what odd thing can a customer see, and why do read-repair and merging divergent carts make that acceptable for a cart but wrong for a bank balance?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-31-quorums/quorums.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-31-quorums/quorums.py).

It is a pure simulation, standard library only, and it runs in about a second. N replicas each hold a (version, value). A write lands a new, higher version on W of them. A read asks R of them and keeps the newest version it sees. Part 1 sets R + W > N and measures how often reads see the latest write. Part 2 breaks the rule and measures the stale fraction, against the exact combinatorics. Part 3 tunes W and R three ways and measures availability under random replica failures, then shows read-repair healing a cluster that got a weak write.

Everything is deterministic. A logical version clock steps once per write, and every random choice comes from a seeded RNG, so your run matches the reference to the digit.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. Strong quorum, N=5, W=3, R=3 (R + W = 6 > 5). Out of 100 reads, how many see the latest write?
- P2. Weak quorum, N=3, W=1, R=1 (R + W = 2 <= 3). What percent of reads come back stale?
- P3. Weak quorum, N=5, W=2, R=2 (R + W = 4 <= 5). What percent are stale?
- P4. Balanced W = R = 3 on N=5, each replica down 10 percent of the time. What percent of operations, reads and writes, can still be served?

P1 and P2 are the pair to feel in your gut. One should be a round, confident number. The other surprises people.

### Fill in the TODOs

1. TODO 1 is the write side: pick W replicas to receive the new version. One line, `rng.sample(up, w)`.
2. TODO 2 is the read side: from the R replicas that answered, keep the newest version. `max(versions[i] for i in responders)`.
3. TODO 3 is the whole day in one line: a read and a write are guaranteed to overlap exactly when `(r + w) > n`.
4. TODO 4 is availability: an operation that needs so many replicas can run only if at least that many are up, `up_count >= needed`.

```bash
cd labs/day-31-quorums
python3 quorums.py
```

### What you're going to discover

Part 1 is the clean one. Every setting with R + W > N reads 100 percent fresh, and the theory column agrees exactly, because the overlap is forced, not probable. Seeing W=1, R=5 and W=5, R=1 and W=3, R=3 all hit a flat 100 percent is the moment the counting argument stops being abstract.

Part 2 is the surprise. N=3, W=1, R=1 comes back about 66.5 percent stale. Two reads in three miss the write, because the one replica you read is usually not the one you wrote. Then the N=5 sweep shows the gap shrinking as R + W climbs toward N: 80 percent at W1R1, 30 percent at W2R2, 10 percent at W2R3. The closer you get to the rule, the smaller the hole.

Part 3 is the tradeoff, measured. Write-heavy keeps writes at 100 percent available but reads at 59 percent. Read-heavy is the mirror. Balanced sits near 99 percent for both, because a majority of five survives two failures. Then read-repair: a value written to one replica is dragged across the whole cluster in a handful of reads. Availability and healing, the two things that make this design worth its weirdness.

### Traps ⚠️

- R + W > N is strict. If you ever see a stale read in a setting you thought was strong, check whether R + W actually exceeds N or merely equals it. Equal is not enough, and it is the most common off-by-one in this whole topic.
- The stale percentages in Part 2 wobble by a fraction of a percent run to run around the theory value. That is sampling noise over 50,000 trials, not a bug. Trust the match to theory, not the third decimal.
- The write-heavy and read-heavy availability numbers look alarming (59 percent) until you remember what they mean: R=N or W=N makes that side need every single replica, so one failure is enough to stop it. That is the lesson, not a mistake.
- Do not confuse "the write reached W replicas" with "the write is on a majority". A low W is a deliberate availability choice, and it is exactly why read-repair and anti-entropy exist to clean up after it.

### Deliverable

[`labs/day-31-quorums/RESULTS.md`](../labs/day-31-quorums/RESULTS.md) has a skeleton. Paste the output, and write one line: with R + W > N what percent of reads were fresh, and with N=3, W=1, R=1 what percent were stale, and why is the overlap the whole trick?

---

## Block 4: write (30 min) 📣

Your angle today is the inequality that does real work: "a database keeps N copies of your data, and whether a read sees your latest write comes down to one line, R + W > N. I simulated it: above the line, 100 percent fresh, no luck involved. On the line or below, up to two thirds of reads went stale. The overlap is the whole trick." The Part 1 versus Part 2 contrast is the screenshot.

Example posts are on the [Day 31 posts](../shares/day-31-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the stale percent you measured when you broke the rule, and one thing you still cannot explain.

Day 32 is consensus and Raft, the next rung up. A quorum lets replicas agree on the value of one key by overlapping. Consensus is how a whole group agrees on an ordered sequence of decisions, a log, even while machines crash and messages drop. You will see that a majority quorum sits right at the heart of Raft too, so today's counting argument is not left behind, it is the foundation the next idea stands on.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Strong means R + W > 5. W=3 R=3 gives 6, strong. W=2 R=3 gives 5, not strong. W=1 R=4 gives 5, not strong. W=4 R=1 gives 5, not strong. So only W=3 R=3 clears the bar; the other three sit exactly at N and a read can miss a write. For W=3, you need R > 5 minus 3, that is R > 2, so the smallest R that works is 3. With R=2 the read set of 2 and the write set of 3 add up to exactly 5, so they can be made disjoint and the read can miss the write. One more replica in the read set, R=3, forces the overlap.

D2. N=6, W=4, R=3. If the read set and the write set never shared a replica they would need 4 plus 3 equals 7 distinct replicas, but there are only 6, so they must overlap in at least one, and that one holds the latest write. Guaranteed. N=6, W=3, R=3: now 3 plus 3 equals 6, exactly N, not greater, so they can be arranged with no overlap. Concretely, write set {1, 2, 3} and read set {4, 5, 6}. The write landed on 1, 2, 3; the read asks 4, 5, 6; they touch nowhere, and the read sees only the old value. R + W equal to N is not enough, you need strictly greater.

D3. N=3, W=1, R=1. The write is on one random replica, the read asks one random replica. The read misses whenever it picks a different replica than the write, which is 2 of the other 3, so 2/3, about 66.7 percent stale. This is exactly the lab's Part 2 headline. Now W=2, R=1 on N=3: R + W = 3, equal to N, not greater, so not strong. The read's one replica falls inside the written 2 with probability 2/3, and misses with probability 1/3, so about 33 percent of reads are stale. Adding one to W halved the staleness but did not kill it, because 3 is still not greater than 3.

D4. A write needs W replicas up. To survive 2 of 5 being down you have 3 up, so W can be at most 3, and the largest such W is 3. With W=3, strong consistency needs R > 5 minus 3, so the smallest R is 3. The cost shows up against what you could have had: if you did not care about strong reads you could set R=1, and a read would then survive 4 replicas being down. Forcing R=3 for strong consistency means reads now also need 3 of 5 up, so they tolerate only 2 failures instead of 4. With a single replica down you are still fine either way (4 up covers R=3), but you have given up the near-unkillable R=1 read. That trade, fragility on reads in exchange for freshness, is the quorum choice in one sentence.

D5. The cart used a low W so a write lands on whatever replicas are reachable and is almost never rejected, which keeps add-to-cart working through failures. The trade is strong consistency: with a low W the copies diverge, reads can be stale, and two replicas can hold two different carts. The odd thing a customer can see is an item they deleted coming back, because Dynamo merges divergent carts by union and never drops a write, so a removal can be undone by a stale copy. Read-repair pushes the newest version onto stale replicas as reads happen, and the union merge means no add is ever lost, so for a cart the worst case is a resurrected item you remove again, a shrug. For a bank balance, merging two versions by union is meaningless and losing a debit is catastrophic, so a balance cannot use this trade; it needs strong consistency or real consensus. The business logic decides the quorum, not the other way round.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-31-quorums/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-31-quorums/solution.py).

TODO 1, the write side, pick W replicas for the new version:

```python
return rng.sample(up, w)
```

TODO 2, the read side, keep the newest version the responders held:

```python
return max(versions[i] for i in responders)
```

TODO 3, the whole day in one line, the overlap is guaranteed when R + W exceeds N:

```python
return (r + w) > n
```

TODO 4, availability, an operation can run only if enough replicas are up:

```python
return up_count >= needed
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, seeded, 50,000 trials per measurement.

```
==============================================================================
Part 1: R + W > N. The read set and the write set must overlap, so
        every read sees the latest write
==============================================================================
  N = 5 replicas. Each write lands on W of them with a new version.
  Each read asks R of them and keeps the newest version it sees.

  config            R+W  overlap?   sees latest    theory
  W=3, R=3             6       yes        100.0%    100.0%
  W=4, R=2             6       yes        100.0%    100.0%
  W=1, R=5             6       yes        100.0%    100.0%
  W=5, R=1             6       yes        100.0%    100.0%

  Every row has R + W > N, so the R replicas a read asks can never
  completely miss the W that took the write. At least one replica sits
  in both sets, and it carries the newest version. 100 percent fresh,
  and not by luck: the overlap is forced by counting.

==============================================================================
Part 2: R + W <= N. Break the overlap, and reads start missing writes
==============================================================================
  The classic Dynamo-fast setting: N=3, W=1, R=1. A write touches
  one replica, a read asks one replica, and R + W = 2 is not above 3.

  N=3, W=1, R=1:   66.5% of reads are STALE (theory 66.7%)
  Two times in three the one replica you read is not the one the write
  touched, so you get an older version. That is the cost of R + W <= N:
  no overlap guarantee, measurable staleness.

  Same story on N=5, swept across weak settings (R + W <= 5):
  config            R+W     stale    theory
  W=1, R=1             2     79.8%     80.0%
  W=2, R=2             4     30.1%     30.0%
  W=1, R=4             5     19.9%     20.0%
  W=2, R=3             5     10.1%     10.0%

  The fewer replicas a write and a read touch between them, the wider
  the gap they can slip past each other through. Push W + R back above
  N and the gap shuts completely.

==============================================================================
Part 3: tuning W and R on the same N, and what each setting trades
==============================================================================
  N = 5. All three settings below keep R + W > 5, so all three give
  fresh reads. What changes is where the cost and the fragility land.
  Each replica is independently down 10% of the time.

  setting         W  R   write avail  read avail    both
  write-heavy     1  5       100.00%      59.15%  59.15%
  read-heavy      5  1        59.15%     100.00%  59.15%
  balanced        3  3        99.18%      99.18%  99.18%

  write-heavy (W=1): a write waits for a single ack, so writes almost
    never block. But R=N means a read needs ALL replicas, so one dead
    replica takes reads down. Cheap durable writes, brittle reads.
  read-heavy (W=N): the mirror. Reads fly on R=1, but one dead replica
    stalls every write.
  balanced (W=R=3): both pay a medium cost, and both survive the most
    failures, 2 replicas down, for reads and for writes alike.
  Same N, three bets. This knob is what Dynamo hands the operator.

  Read-repair: healing the laggards as a side effect of reading.
    wrote the newest version to 1 of 5 replicas; 4 are behind.
    after 6 repaired reads, replicas still behind: 0.
    A read does double duty: it answers the client AND pushes the
    newest version onto any stale replica it touched, so the cluster
    converges even though the write only reached W. That is how a
    Dynamo store runs on a low W, stays available, and still heals
    toward agreement. Anti-entropy and hinted handoff finish the job
    for replicas no read happened to touch.

==============================================================================
Scoreboard
==============================================================================
  P1 strong W3R3 sees latest       you =  100.0   actual =   100.0 %       close enough
  P2 weak N=3 W1R1 stale           you =   67.0   actual =    66.5 %       close enough
  P3 weak N=5 W2R2 stale           you =   30.0   actual =    30.1 %       close enough
  P4 balanced availability         you =   99.0   actual =    99.2 %       close enough

==============================================================================
The number to carry
==============================================================================
  With R + W > N, every read overlapped the latest write: 100% fresh,
  no exceptions. Drop to R + W <= N and the floor falls out: 67% of
  reads on N=3, W=1, R=1 came back stale. The overlap is the whole
  trick. You tune W and R to shift cost between reads and writes, but
  the instant R + W stops exceeding N you have swapped a strong read
  for a faster one.
```

Part 1 is the counting argument made visible. Four different splits of the work, from W=1, R=5 to W=5, R=1, and every one reads a flat 100 percent fresh, matching the theory column exactly. That is the difference between a guarantee and a probability. When R + W > N the overlap is not likely, it is forced, so no run will ever show a stale read in these settings.

Part 2 is the hole. N=3, W=1, R=1 lands about 66.5 percent stale, right on the 66.7 percent the combinatorics predict, because the single replica you read is usually not the single replica you wrote. The N=5 sweep shows the gap closing as R + W rises toward N, from 80 percent down to 10 percent, and it only reaches zero once you cross the line.

Part 3 is the tradeoff you will actually argue about in a design review. All three settings give fresh reads, so the choice is about failure. Write-heavy keeps writes up through almost anything but takes reads down on the first dead replica; read-heavy is the mirror; balanced, a majority each way, holds near 99 percent for both because it survives two of five being down. Then read-repair drags a one-replica write across the whole cluster in six reads, which is how a low W store still converges. Available, tunable, self-healing, and the price is that for a window the copies disagree.

</details>
