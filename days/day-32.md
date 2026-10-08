---
title: "Day 32: consensus and Raft"
parent: "Week 5: distributed systems"
nav_order: 4
has_children: true
---

# Day 32
## How a cluster agrees on a leader, and why the timeouts are random 🗳️

Today's one idea: when several machines must act as one, they need to agree on a single boss, and the whole trick of agreeing is "a majority says yes." Raft is the algorithm that makes that happen and keeps happening as machines crash. You pick a leader by election, the leader needs votes from a majority of the cluster, and the elections use random timers so that everyone does not nominate themselves at the same moment and jam the vote. Once you see those three pieces, consensus stops feeling like magic.

This is the middle of the hard week, so let me say it plainly: Raft bends the brain the first time, and that is normal. The good news is that the heart of it, leader election and the majority rule, is genuinely simple once you watch it move. We will not touch the other half (log replication) today. Election first. It carries the whole intuition.

---

## Before you start ⏪

Bring Day 30 and Day 31 with you. Day 30 gave you CAP: when a partition hits, a system either stays consistent or stays available, not both. Day 31 gave you quorums: R plus W greater than N, and the idea that a majority of replicas has to be involved for a read or write to be safe. Today's majority is that same majority wearing a different hat. Raft is firmly on the CP side: when it cannot reach a majority, it stops rather than risk two leaders. If "quorum" and "a majority must overlap" are fresh in your head, today is mostly putting them to work.

---

## Words you will meet today 📖

A term is Raft's clock, but counted in elections, not seconds. Every time an election starts, the term number goes up by one. A term has at most one leader, and the term number lets everyone ignore stale messages from an older, deposed leader.

A follower, a candidate and a leader are the three states a node can be in. A follower just listens. A candidate is a node that is trying to get itself elected. A leader is the one node currently in charge, sending heartbeats so the followers know it is alive.

An election timeout is how long a follower waits without hearing from a leader before it gives up and nominates itself. In Raft this is randomized per node, and that randomization is the star of today.

A heartbeat is an empty "I am still here" message the leader sends to every follower on a fixed interval. As long as the heartbeats keep arriving, followers reset their election timers and stay followers.

A majority is more than half of the whole cluster: floor(N/2) plus 1. For 5 nodes it is 3. A candidate needs a majority of votes to win, and because any two majorities of the same set must share at least one node, two different leaders can never both win the same term.

A split vote is a failed election: two or more candidates stand up at once, the votes divide, nobody reaches a majority, the term is wasted, and everyone tries again. Randomized timeouts are the fix.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Do this first, before anything else:
- [The Secret Lives of Data: Raft](https://thesecretlivesofdata.com/raft/). Raft as a slow, clickable animation. Watch a leader get elected, then watch one fail and a new one take over. Twenty minutes here will make the paper feel obvious.

Then read:
- [The Raft paper](https://raft.github.io/raft.pdf), "In search of an understandable consensus algorithm" by Ongaro and Ousterhout. It was written to be read, and it succeeds. Today, read section 5.1 (Raft basics), 5.2 (leader election) and 5.4.1 (the majority / election restriction). Skip log replication for now; you will not miss it.
- [raft.github.io](https://raft.github.io/). The home page has a live visualization you can poke, plus a list of real implementations. Kill a node in the visualization and watch the re-election.

Watch, after you have done the lab:
- [Designing for Understandability: The Raft Consensus Algorithm](https://www.youtube.com/watch?v=vYp4LYbnnW8) by Diego Ongaro, the author, about 35 minutes. The clearest single talk on why Raft looks the way it does.
- Optional, if you want the deep version: [MIT 6.824 Lecture 6: Raft (1)](https://www.youtube.com/watch?v=64Zp3tzNbpE), about 80 minutes. A graduate lecture that takes its time. Save it for when the paper has sunk in.

### Why a cluster needs one leader, and what a term is (12 min)

Start with the problem. You have five machines that together pretend to be one reliable thing, say the brain that decides the order of writes. They cannot all decide independently, or they will disagree the moment the network hiccups. So Raft funnels every decision through a single leader. The leader is the one node that may accept writes and tell the others what happened, in order. Followers just copy. One boss, and the hard part is only this: choosing that one boss, and choosing a new one the instant the old one dies, without ever accidentally having two.

That "without ever two" is where the term comes in. A term is a counter that ticks up by one every time an election starts. Think of it like "the third government since independence," a label for a stretch of time with at most one person in charge. Every message a node sends carries its term. If a node hears a message from a higher term, it knows its own view is stale and it steps down to follower immediately. If it hears a message from a lower term, it ignores it as the ramblings of a deposed leader who has not yet noticed. The term is how a distributed group agrees on "that was then, this is now" without a shared clock, which, remember from Day 29, they do not have.

### Leader election, step by step (14 min)

Here is the whole dance for a 5-node cluster. Everyone starts as a follower. The leader sends a heartbeat every so often, and each heartbeat makes a follower reset its election timer. As long as heartbeats arrive, nothing happens, which is the point.

Now the leader crashes. The heartbeats stop. One follower's election timer runs out first. That follower does four things, and these four are the beating heart of today: it increments its term (a new election), it switches from follower to candidate, it votes for itself, and it sends a RequestVote to all the others. Each other node, if it has not already voted this term, grants its vote and resets its own timer (so it does not also stand up). The candidate counts votes as they come back. The moment it has a majority, 3 of 5, it declares itself leader and starts sending heartbeats, which tells everyone the election is over and resets the cluster to calm.

Notice what the majority buys you. The new leader got 3 votes out of 5. Any rival would also need 3, and there are only 5 votes to go around, so a rival cannot also get 3 without sharing a voter, and no node votes twice in a term. Two majorities must overlap, so there can be only one leader per term. That single sentence is why Raft is safe. The lab's Part 1 runs exactly this: it kills the leader and shows a follower timing out, winning 3 votes, and taking over, with the cluster leaderless for only a couple of hundred ticks in between.

### Why the timeouts are random (14 min)

Now the part that looks like a detail and is actually the cleverest idea in the algorithm. Go back to the moment the leader dies. What if two followers, or three, time out at the same instant? They all become candidates for the same term, they all vote for themselves, and they all beg the others for votes. The votes split. With three candidates and only two followers left to give votes away, nobody can reliably reach 3, so the term produces no leader at all. Everyone shrugs, waits, and tries again, and if their timers are still synchronized, they collide again. The cluster can sit there holding elections and electing nobody. This is a split vote, and it is a real way for a naive design to stall.

Raft's fix is almost insultingly simple: do not let the nodes wait the same amount of time. Give each node a random election timeout inside a window. Now one node almost always wakes up clearly before the others, nominates itself, and collects a majority before anyone else even stirs. The others get its RequestVote, grant it, and reset. One round, one leader, done. Randomization breaks the symmetry that causes the pile-up.

The lab's Part 2 measures this, and the gap is large. Run thousands of cold-start elections with equal timeouts and more than half of the rounds split and waste a term. Switch to randomized timeouts and that drops to a couple of percent, so elections settle in about one round. Same algorithm, same majority rule, one knob changed. It is the cleanest "small change, huge effect" you will see this week.

### The majority rule is also your fault tolerance (10 min)

One more thing falls straight out of "a leader needs a majority," and it is the most practical number you will carry from today. A leader needs a majority of the whole cluster, always, not a majority of whoever happens to be alive. So a 5-node cluster needs 3 votes even if two nodes are on fire. That means it keeps working with 2 nodes down (3 alive is still a majority) but goes dark with 3 down (2 alive can never reach 3). The formula is: N nodes tolerate floor((N-1)/2) failures. Five tolerates two.

This is why cluster sizes are almost always odd. A 6-node cluster needs 4 for a majority and still only tolerates 2 failures, exactly the same as 5, while costing you an extra machine and an extra vote to collect every election. The even size buys nothing and adds the risk of a perfect tie. Odd sizes, 3, 5, 7, are the sweet spots. Part 3 of the lab kills nodes one at a time and shows the cliff: elected every time with 2 down, never once with 3 down. And the same majority is what log replication uses to commit an entry, so the half of Raft we are skipping today rides on this exact rule.

---

## Block 2: drill (40 min) ✍️

Paper first, with the two formulas in front of you: `majority = floor(N/2) + 1` and `failures tolerated = floor((N-1)/2)`. Then copy your answers into [`notes/day-32-drills.md`](../notes/day-32-drills.md). About 8 minutes each.

D1. A 5-node cluster, the leader dies. Trace what one follower does, step by step, until a new leader exists. How many votes must the winner collect, and why is that number 3 and not 5?

D2. Three followers time out in the same instant and all become candidates for the same term. Why can the term fail to produce any leader, what does each candidate do next, and what single change to the timeouts makes this almost never repeat?

D3. Work out the majority and the failures tolerated for N = 3, 4, 5, 6, 7. Then explain why 4 nodes tolerate the same number of failures as 3, and why odd cluster sizes are the sensible choice.

D4. A 5-node cluster has 3 nodes down. The surviving 2 keep timing out, bumping the term, and requesting votes forever. Why is no leader ever elected, what can and cannot the cluster do in this state, and what has to happen for it to recover?

D5. A network partition splits a 5-node cluster into a group of 3 and a group of 2, each cut off from the other. Which side (if any) can elect a leader and keep serving writes, which cannot, and why does this stop the classic split-brain where both sides accept writes?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-32-raft/raft_election.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-32-raft/raft_election.py).

It is a discrete-event simulation, which is a fancy way of saying there is no real network and no real clock. We advance a made-up clock one tick at a time and deliver messages after a small, seeded delay, so the whole thing is deterministic: the same seed gives the same run on every laptop, and it finishes in about a second. Standard library only, no threads, no sockets, nothing to install, and it leaves no files behind. We build leader election and the majority rule only, not log replication.

It is in three parts. Part 1 stands up a 5-node cluster with one leader, kills the leader, and shows a follower timing out and winning a majority to become the new one. Part 2 runs thousands of cold-start elections with fixed timeouts and then randomized ones, and measures the split-vote rate of each. Part 3 kills nodes one at a time and shows exactly how many failures a 5-node cluster survives.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. After the leader dies, how many ticks does the cluster spend with no leader before a new one is elected? (Hint: it is bounded by the election timeout window, 150 to 200 ticks.)
- P2. With fixed (equal) timeouts, what percent of election rounds end in a split vote, electing nobody?
- P3. With randomized timeouts, what percent of rounds split this time?
- P4. How many node failures can a 5-node cluster tolerate and still elect a leader?

P2 is the one to feel in your gut before you run it. Equal timeouts, everyone waking together. Write down a number for how often that splits. Most people guess something small, and the real answer is more than half.

### Fill in the TODOs

The four TODOs are the four ideas of the day, nothing more.

1. TODO 1 is `majority(n)`, the single most important line in the file: `return n // 2 + 1`. Every part leans on it.
2. TODO 2 is becoming a candidate: bump the term, switch to candidate, vote for yourself, and start the tally with that self-vote. The four lines that start an election.
3. TODO 3 is the vote-granting rule, `return voted_for is None or voted_for == candidate_id`. One vote per term, which is precisely what makes split votes possible.
4. TODO 4 is the randomized election timeout, `return rng.randint(ELECTION_MIN, ELECTION_MAX)`. The one line that fixes split votes.

The comments above each TODO show the exact shape. If a TODO is still blank, the lab tells you which one and stops cleanly, it does not hang or crash.

```bash
cd labs/day-32-raft
python3 raft_election.py
```

### What you're going to discover

Part 1 is the reassuring one. You kill the leader and, a couple of hundred ticks later, the cluster has quietly picked a new one with 3 of 5 votes and carried on. No human, no central coordinator, just timers and votes. That is self-healing, and it is the thing people mean when they say a system is "highly available."

Part 2 is the lesson. Fixed timeouts split the vote about 55 percent of the time on the reference run, so on average it takes more than two rounds to elect anyone, and the worst trial needed a dozen. Flip to randomized timeouts and the split rate collapses to about 2 percent, settling in one round almost always. You changed one line and the election went from flaky to boring, which in distributed systems is the highest compliment.

Part 3 is the number to tattoo somewhere. With 2 nodes down, a 5-node cluster elects a leader every single time. With 3 down, it never does, not once across 200 seeds, because 2 survivors can never reach 3 votes. That cliff is the whole meaning of "tolerates floor((N-1)/2) failures," and it is why you run 3 or 5 or 7, never 6.

### Traps ⚠️

- A tick is not a second. It is a unit of simulated time. Do not read "167 ticks with no leader" as 167 milliseconds of wall clock on your machine. The whole run takes about a second of real time because nothing actually waits.
- The majority is of the whole cluster, not the survivors. The lab computes `majority(N)` with the full N on purpose. If you ever change it to a majority of alive nodes, Part 3 breaks and a 2-node remnant happily "elects" a leader, which is exactly the split-brain that Raft exists to prevent.
- The randomized split rate wobbles a point or two if you change the seed, and the fixed rate moves if you widen the timeout spread. The contrast, 55 against 2, is what is solid. Trust the shape, not the third digit.
- The run is deterministic only because it is seeded. That is a feature for a lab (everyone sees the same numbers) and a lie about real life, where timing is genuinely random. The randomness is what the real algorithm depends on; we just pin the seed so your run matches the reference.

### Deliverable

[`labs/day-32-raft/RESULTS.md`](../labs/day-32-raft/RESULTS.md) has a skeleton. Paste the output, and write one line: how much did randomizing the timeout cut the split-vote rate, and why can a 5-node cluster survive 2 failures but not 3?

---

## Block 4: write (30 min) 📣

Your angle today is the one-line trick: "A cluster of machines agrees on a leader by majority vote, and the only thing stopping the vote from jamming is that each node waits a random amount of time. I changed fixed timeouts to random ones in a simulation and the split-vote rate fell from 55 percent to 2 percent." The scoreboard, fixed against randomized, plus the fault-tolerance cliff, is the screenshot.

Example posts are on the [Day 32 posts](../shares/day-32-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the split-vote rates you measured for fixed versus randomized timeouts, and one thing you still cannot explain.

Day 33 is logical clocks. Since the real clocks lie to us (Day 29), we invent clocks that count causality instead of seconds: Lamport timestamps and vector clocks, and how they capture "this happened before that" without trusting any wall clock. Today you saw a cluster agree on who is in charge. Tomorrow you give it a way to agree on what happened first.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The follower was quietly listening, resetting its election timer every time a heartbeat arrived. When the leader dies the heartbeats stop, and after its randomized timeout the follower's timer fires. It then does the four heart-of-Raft things: increment its term (say term 1 becomes 2), switch to candidate, vote for itself, and send a RequestVote to the other four. Each node that has not yet voted this term grants its vote and resets its own timer, so it does not also stand up. As soon as the candidate has collected 3 votes (itself plus 2 others) it has a majority and declares itself leader, immediately sending heartbeats to stop anyone else from starting. The winner needs 3, not 5, because a majority is floor(5/2) plus 1, and it must be a majority of the whole cluster so that any two majorities overlap in at least one node. That overlap is what guarantees two candidates can never both win the same term.

D2. With 5 nodes the majority is 3. If three nodes become candidates at once for the same term, each has already voted for itself, so three votes are spoken for and only two followers are left to hand out. For a candidate to win it needs both of those free votes plus its own, making 3; if the two free votes go to different candidates, or one goes to the third candidate, no one reaches 3 and the term elects nobody. (If all five become candidates it is guaranteed to fail, since each has only its own single vote.) Each candidate that did not win waits out its election timer again and starts a fresh election at the next term. The single change that fixes this is randomizing the election timeout, so the nodes stop waking in lockstep: one wakes clearly first and locks up a majority before the others time out. The lab shows this is the difference between a 55 percent split rate and a 2 percent one.

D3. Using majority = floor(N/2) plus 1 and failures tolerated = floor((N-1)/2):

| N | majority | failures tolerated |
|---|----------|--------------------|
| 3 | 2 | 1 |
| 4 | 3 | 1 |
| 5 | 3 | 2 |
| 6 | 4 | 2 |
| 7 | 4 | 3 |

Four nodes tolerate the same one failure as three, because moving from 3 to 4 pushes the majority up from 2 to 3, so you can still only afford to lose one node and keep a majority. The extra node bought you nothing in fault tolerance, it just added a vote you now have to collect and a chance of a 2-2 tie. That is why odd sizes are the sensible choice: 3, 5 and 7 give you the most failure tolerance per node and cannot tie. You go even only for brief moments during a membership change.

D4. The majority is 3, and only 2 nodes are alive, so the most votes any candidate can ever gather is 2 (itself plus the one other survivor), which is short of 3. No candidate wins, so both survivors keep timing out, incrementing the term, and re-requesting votes, and the term number climbs forever with no leader at the end of any of it. In this state the cluster cannot elect a leader, which means it cannot accept writes or commit anything, because a commit needs a leader and a majority. It can still sit on its data and, if the system permits, answer possibly-stale reads, but for the consensus-backed work it is unavailable. To recover, at least one of the down nodes has to come back (or be replaced), so that 3 are alive again and a majority becomes reachable; the next election then elects a leader and the cluster resumes. This is the CP choice from Day 30 in the flesh: with no majority reachable, Raft stops rather than risk two leaders.

D5. The side with 3 nodes still holds a majority of the whole 5-node cluster, so it can elect a leader and keep accepting writes. The side with 2 cannot reach 3 votes, so its would-be candidates just keep timing out and it refuses writes. Because a leader needs a majority of the whole cluster, and any two majorities must overlap in at least one node, only one side of any partition can ever have a majority, so there is at most one leader across the entire system at any time. That is precisely what prevents split-brain, the failure where both sides believe they are in charge and accept conflicting writes. Raft deliberately trades the minority side's availability for the guarantee of a single leader. Note that this clean "one side wins" only works because the cluster is odd-sized; an even split that left neither side with a majority would stall the whole cluster, which is the argument for odd sizes all over again.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-32-raft/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-32-raft/solution.py).

TODO 1, the majority threshold, the single most important line in the lab:

```python
return n // 2 + 1
```

TODO 2, becoming a candidate: a new term, your own vote, and the tally started with it:

```python
node.term += 1
node.role = "candidate"
node.voted_for = node.id
node.votes = {node.id}
```

TODO 3, the vote-granting rule, one vote per term, which is what makes split votes possible:

```python
return voted_for is None or voted_for == candidate_id
```

TODO 4, the randomized election timeout, the one line that fixes split votes:

```python
return rng.randint(ELECTION_MIN, ELECTION_MAX)
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, seed 629. The run is deterministic, so with the shipped seed your numbers will match these exactly.

```
==============================================================================
Part 1: the leader dies. A follower times out and wins a majority.
==============================================================================
  cluster of 5, node 0 is the leader, heartbeating every 15 ticks.
  at tick 500 the leader crashes and the heartbeats stop.

  node 2 timed out, became a candidate, and asked for votes.
  it won with 3 of 5 votes (majority is 3) and became
  the leader for term 2 at tick 667.
  the cluster had NO leader for 167 ticks, then healed itself.
  3 >= 3, so a strict majority of the whole cluster
  agreed on one leader. No two nodes can both hold a majority in the
  same term, which is exactly why there is never more than one leader.

==============================================================================
Part 2: split votes. Fixed timeouts stall; randomized ones converge.
==============================================================================
  2,000 cold-start elections per mode, cluster of 5, majority 3.
  A 'round' is one term. If a round elects nobody, the votes split and
  everyone tries again on the next term.

  FIXED timeouts (everyone waits ~150 ticks, tiny jitter):
    split-vote rate:      55.4% of rounds elected nobody
    rounds to a leader:  2.24 on average, 12 in the worst trial

  RANDOMIZED timeouts (each waits a random 150-200 ticks):
    split-vote rate:       2.0% of rounds elected nobody
    rounds to a leader:  1.02 on average, 3 in the worst trial

  Randomizing the timeout cut the split-vote rate about 28x.
  With fixed timeouts the nodes keep waking together, splitting the vote,
  and burning term after term. Spreading the timeouts means one node
  almost always wakes first and locks up a majority before the rest
  stir. That one change is why Raft elections settle in about one round.

==============================================================================
Part 3: the majority rule is fault tolerance.
==============================================================================
  cluster of 5, so a leader needs 3 votes, a majority of the WHOLE
  cluster, not of whoever is still alive. Count how often a leader is
  elected across 200 seeds as we kill more nodes:

    0 down, 5 alive:  elected in 200/200 seeds   majority reachable? yes
    1 down, 4 alive:  elected in 200/200 seeds   majority reachable? yes
    2 down, 3 alive:  elected in 200/200 seeds   majority reachable? yes
    3 down, 2 alive:  elected in   0/200 seeds   majority reachable? NO (majority impossible)
    4 down, 1 alive:  elected in   0/200 seeds   majority reachable? NO (majority impossible)
    5 down, 0 alive:  elected in   0/200 seeds   majority reachable? NO (majority impossible)

  A 5-node cluster tolerated 2 failures: with 2 down the
  surviving 3 are still a majority and always elect a leader.
  With 3 down only 2 remain, which can never reach 3
  votes, so no leader is elected and the cluster is UNAVAILABLE. That is
  floor((N-1)/2) failures tolerated, straight out of the majority rule.
  Log replication (the other half of Raft) commits an entry only once a
  majority has stored it, so it rides on this very same majority.

==============================================================================
Scoreboard
==============================================================================
  P1 new-leader gap              you =   200.0   actual =    167.0 ticks       close enough
  P2 fixed split rate            you =    55.0   actual =     55.4 %       close enough
  P3 randomized split rate       you =     2.0   actual =      2.0 %       close enough
  P4 failures tolerated          you =     2.0   actual =      2.0        close enough

==============================================================================
The number to carry
==============================================================================
  Fixed timeouts split the vote 55% of rounds; randomizing them
  dropped that to 2%, so elections settle in about one round.
  And a 5-node cluster elected a leader with 2 nodes down but never
  with 3: a majority of the whole cluster is the line between
  available and stuck. Consensus is just 'a majority agrees', and the
  random timeout is the trick that stops everyone agreeing to disagree.
```

Part 1 is the self-healing. The leader died at tick 500 and node 2 had taken over by tick 667, a gap of 167 ticks, with 3 of 5 votes. Nobody coordinated that. A timer fired, a node asked for votes, a majority said yes. That is a cluster surviving the loss of its leader with no human in the loop, which is the practical magic of consensus.

Part 2 is the whole reason the timeouts are random. With equal timeouts the nodes kept waking together and splitting the vote 55 percent of the time, dragging the average election out past two rounds. Randomizing the timeout, a single line, dropped that to 2 percent and brought the average down to essentially one round. The algorithm did not change. The symmetry did.

Part 3 is the fault-tolerance cliff, and it is sharp. Two nodes down, elected every time. Three down, never. The 2 survivors simply cannot reach 3 votes, so the cluster has no leader and stops. That is floor((N-1)/2), which for 5 is 2, and it is the reason real clusters are odd-sized: a sixth node would need 4 for a majority and still tolerate only 2 failures, all cost and no benefit.

The one line to carry out of today: consensus is "a majority agrees," and the random election timeout is the small, almost silly-looking trick that keeps the majority from deadlocking on itself.

</details>
