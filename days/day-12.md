---
title: "Day 12: replication and lag"
parent: "Week 2: storage"
nav_order: 5
has_children: true
---

# Day 12
## Replication and lag, or why you post a comment, refresh, and it is gone for two seconds 🔁

Today's one idea: most systems keep more than one copy of your data. One copy takes the writes (the leader), the others copy those writes and serve reads (the followers). The copying is not instant. For a small window after every write, the followers still have the old value, and if your read lands on a follower in that window, you see stale data. That window has a name, replication lag, and once you can see it, a whole class of "ghost" bugs stops being mysterious.

You have met the single database all week. Today it becomes several, because one machine cannot serve a billion reads and because one machine dying should not take the whole product down. The moment you have more than one copy, you have a new and permanent problem: the copies are never perfectly in step.

---

## Before you start ⏪

You need Day 6's idea of more than one server behind a load balancer, and Day 11's transactions, because replication is about what a reader sees versus what has actually been written. Nothing heavy from today's code side. The lab is pure Python, standard library, in memory, no database files. If you can picture a queue of writes flowing from one box to another, you are ready.

---

## Words you will meet today 📖

A leader, also called the primary or the master in older writing, is the one node that accepts writes. Every change goes here first.

A follower, also called a replica, a read replica, or a secondary, is a copy that receives the leader's stream of writes and serves reads. You add followers to scale reads and to have a spare if the leader dies.

Replication lag is the gap between a write landing on the leader and that same write showing up on a follower. Usually milliseconds. Under load or a network hiccup it can stretch to seconds, and that is when users notice.

Read-your-writes consistency, sometimes read-after-write, is a promise that you can always see your own writes, even while other people might see the old value for a moment longer. Losing your own just-posted comment is the classic break.

Asynchronous replication is the leader confirming a write to the client without waiting for any follower. Writes are fast, but the followers lag, and if the leader dies before it ships the last few writes, those writes are gone.

Synchronous replication is the leader waiting for at least one follower to confirm it has the write before telling the client "done." No stale read on that follower, but the write now pays the replication delay, and if the follower is down the write cannot complete at all.

Eventual consistency is the honest small print of async replication: stop writing, wait, and every follower will converge on the leader's value. Eventually. Not now.

Failover is promoting a follower to leader when the leader dies. Under async replication, any write the old leader had not yet shipped is lost in the handover.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [DDIA chapter 5, replication](https://dataintensive.net/). The chapter this whole day is built on. Single-leader replication, the sync vs async choice, replication lag, and the read-your-writes problem by name. If you read one thing today, this.
- [Read-your-writes, the consistency model](https://jepsen.io/consistency/models/read-your-writes) from Jepsen. A tight, precise definition of the exact guarantee your feed quietly broke. Short, and it anchors the vocabulary.
- [PostgreSQL high availability and replication](https://www.postgresql.org/docs/current/high-availability.html). The real thing, not a toy. Skim it for how a production database actually offers synchronous and asynchronous modes, and what the docs warn you about each.

Watch, after the lab:
- [All types of database replication discussed](https://www.youtube.com/watch?v=aE2UPg3Ckck) by Hussein Nasser, about 19 minutes. Walks through single vs multi leader and synchronous vs asynchronous, which is exactly the Part 3 tradeoff drawn out.
- Shorter, for the wider picture: [7 must-know strategies to scale your database](https://www.youtube.com/watch?v=_1IKwnbscQU) by ByteByteGo, about 9 minutes. Read replicas sit in the middle of it, next to the other scaling moves you will meet this week.

### One writer, many readers (15 min)

Start with why replication exists at all, because it fixes two different problems with the same trick.

The first is read scale. An app is almost always read heavy. Think of any feed: one person posts, thousands read. A single database can only answer so many reads per second, so you keep copies, the followers, and you point most reads at them. Ten followers, roughly ten times the read capacity. The writes still all funnel to the one leader, which is fine, because writes are the smaller number.

The second is survival. If the single database dies, your product is down until someone restores a backup, which could be hours. With followers already running and holding a near-current copy, you promote one to leader and you are back in minutes. That promotion is failover.

So far it sounds free. Here is the catch, and it is the whole day. The leader does not teleport each write into the followers. It ships a stream of changes, and each follower applies them a little later. For a short moment after any write, the followers are behind. In the quiet, that lag is a few milliseconds and nobody cares. During an IPL final, when writes spike and the network strains, two score apps on two phones can disagree by a few seconds, because they are reading from two followers at two different lags. Same leader, same truth, different staleness. That is replication lag you can see with your own eyes.

### The lag, and reading your own writes (15 min)

Now the specific bug, because it is the one you will actually ship by accident. A user posts a comment. The write goes to the leader. A heartbeat later the UI refreshes the comment list, that read is sent to a follower to save the leader some load, and the follower has not applied the new comment yet. So the user's own comment is missing. They posted it, they can see it was accepted, and now it is gone. They post it again. Now you have two.

This is a read-your-writes violation. The rule you broke is simple to state: a user must always see their own writes, immediately, even if everyone else sees them a moment later. It is fine for a stranger's view of that comment to lag. It is not fine for the author's own view to lag, because they know what they just did.

There are two honest fixes, and you will build both.

The first is to read your own writes from the leader. Keep track of the fact that this user just wrote, and for a short window, send their reads for that data to the leader instead of a follower. The leader always has the latest value, so the author never sees stale. Everyone else still reads from followers. The cost is a little more load on the leader, but only for recent writers, which is a small slice.

The second is to wait for the follower to catch up. After the write, note its position in the replication stream, and hold the read until the chosen follower has applied up to that position, then read the follower. The read is correct, and it stays on the follower, but it now waits out the lag. For a feed that is a touch slower. For something where you must read a follower, it is the tool.

Both fixes share one truth worth saying out loud. Neither removes the lag. The follower is still behind. You are simply routing around the staleness at the one place it actually hurts.

### Synchronous, asynchronous, and the failover lie (10 min)

The obvious thought is: why tolerate lag at all? Make every write wait for the followers, then no read is ever stale. You can. That is synchronous replication, and it is not free.

Under asynchronous replication, the leader writes locally and immediately tells the client "done," then ships the change to followers in the background. Writes are as fast as a single machine. The price is lag on reads, and a sharper price on failure: if the leader dies holding writes it had not yet shipped, those writes vanish when a follower is promoted. You acknowledged them to the user and then lost them.

Under synchronous replication, the leader waits for a follower to confirm it has the write before it tells the client "done." Now that follower can never serve a stale read of that write, and a failover to it loses nothing. The price is latency: every write pays the round trip to the follower. In the lab you will measure a synchronous write at roughly the full replication delay while an async write is effectively free. And there is a nastier price. If the follower is down, a strict synchronous write cannot complete, so your writes stall until the follower returns or you drop it. You traded "might lose a write" for "might not be able to write."

Real systems split the difference, and it is worth knowing the move: semi-synchronous. Keep one follower synchronous so no acknowledged write is ever truly lost, and keep the rest asynchronous for read scale. If the synchronous follower falls over, another is promoted to take its synchronous role. You will not build that today, but when you see it in a design review you will know exactly what problem it is solving.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-12-drills.md`](../notes/day-12-drills.md).

D1. A user posts a comment. The write hits the leader. The UI immediately reads the comment list back from a follower that is 50 ms behind. Why is the comment missing, and what is the smallest change that fixes it without making the user wait?

D2. A leader takes 2,000 writes per second. A follower can only apply 1,500 per second. A burst of writes lasts 10 seconds, then stops. What happens to the lag during the burst, and roughly how long after the burst until the follower is caught up?

D3. A leader is in Mumbai, a follower in Singapore, round trip 60 ms. Roughly what is an asynchronous write's latency, and a synchronous write's latency (waiting for that one follower to acknowledge)? What happens to writes under each mode if the Singapore follower goes down?

D4. Asynchronous replication. The leader crashes holding 200 ms worth of writes it had not yet shipped. A follower is promoted to leader. What happens to those writes? What would synchronous replication change here, and what does that cost you day to day?

D5. For each read, say whether a follower is fine, it must read the leader, or it must wait for catch-up: showing a user the comment they just posted; showing a stranger's comments from last week; showing your bank balance right after you transferred money out; a dashboard of yesterday's signup counts.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-12-replication/replication.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-12-replication/replication.py).

It builds a leader and one follower in memory, joined by a replication stream, with the follower applying each write after a set lag. Part 1 writes a value and reads it straight back from the follower, many times, and counts how many reads are stale. Part 2 adds the two fixes and watches the stale count fall to zero. Part 3 races asynchronous against synchronous writes and shows what a down follower does to each.

Standard library only, in memory, no files to clean up, a few seconds to run.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. You write to the leader, then read the same key straight back from the follower. Out of 100 such reads, how many show the stale value?
- P2. Once a write happens, how long (in ms) does the follower keep serving the old value before it catches up? The lag is set to 40 ms.
- P3. A synchronous write waits for the follower before returning. How long does one take, in ms?
- P4. After the read-your-writes fix, what percent of reads are stale?

P1 and P4 are the pair to feel in your gut before you run it. Write them down.

### Fill in the TODOs

1. TODO 1 is the follower applying a write: sleep the lag, then store the value and advance how far it has caught up. This is the lag itself, the heart of the whole day.
2. TODO 2 is the Part 1 measurement: write to the leader, immediately read the follower, and decide whether the read is stale.
3. TODO 3 is the read-your-writes fix: if the follower has caught up to your write, read it, otherwise read the leader.
4. TODO 4 is the synchronous write: do not return until the follower has applied the write, or give up if it never does.

```bash
cd labs/day-12-replication
python3 replication.py
```

### What you're going to discover

Part 1 is blunt. At 40 ms of lag, with the read firing right after the write, essentially every single read comes back stale. Not half, not most. On the reference machine it was 300 of 300, a flat 100 percent, because the read always reached the follower before the follower had the write. That is "you refresh and your comment is gone," made exact.

Part 2 is the relief. Read your own writes, and the stale count drops to zero while reads stay fast. Wait for catch-up, and it also drops to zero, but each read now waits about one lag, around 44 ms. Two ways to zero, with different bills.

Part 3 is the tradeoff you can feel. The asynchronous write returns in microseconds. The synchronous write takes about 44 ms, the full replication delay, because it is now waiting for the follower on purpose. Then the follower is knocked down: the async write still returns instantly (and that write would be lost on a failover), while the synchronous write gives up unconfirmed after a quarter second (because a down follower stalls synchronous writes). No free side.

### Traps ⚠️

- If Part 1 shows a low stale percent, your Part 2 fix probably crept into Part 1, or the read is going to the leader. Part 1 must read the follower, straight after the write, with no wait.
- If the lab seems to hang, it is not meant to. Every wait in it is bounded by a timeout. A real hang means a wait is looping on a follower that never advances, usually TODO 1 left blank, and the starter catches that up front and tells you.
- Timings wobble with thread scheduling. The stale window and the synchronous write should both land near the 40 ms lag. If they are wildly off, run it again.

### Deliverable

[`labs/day-12-replication/RESULTS.md`](../labs/day-12-replication/RESULTS.md) has a skeleton. Paste the output, and write one line: at the given lag, what percent of reads were stale, and what took it to zero?

---

## Block 4: write (30 min) 📣

Your angle today is the bug with a name: "you post a comment, refresh, and it is gone for a second. That is not a glitch, it is replication lag, and I reproduced it in about 150 lines of Python, then fixed it two ways." The jump from 100 percent stale to 0 percent, and the async vs sync write-latency gap, both screenshot well.

Example posts are on the [Day 12 posts](../shares/day-12-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the stale percent you measured before and after the fix, and one thing you still cannot explain.

Day 13 is partitioning, also called sharding: splitting one big table across many machines when even a leader with followers is not enough. Today you made copies of the whole dataset. Tomorrow you cut the dataset into pieces, and you meet the hot shard, the one Kohli century that sends all the traffic to a single server.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The write landed on the leader, but the read went to a follower that is 50 ms behind and had not applied the new comment yet, so the follower returned the list without it. The read raced ahead of the replication. The smallest fix that does not make the user wait is read-your-writes: for a short window after someone writes, send that person's reads for that data to the leader, which always has the latest. The author sees their comment instantly, everyone else still reads from followers.

D2. During the burst the leader produces 2,000 per second and the follower drains 1,500 per second, so the backlog grows by 500 per second. Over 10 seconds that is a backlog of about 5,000 writes, which at the follower's apply rate is roughly 3.3 seconds of lag built up by the end. After the burst stops, the leader adds nothing new, and the follower keeps draining at 1,500 per second, so it clears the 5,000 backlog in about another 3.3 seconds. Lag is not a fixed property, it grows under load and shrinks when the load eases.

D3. Asynchronous: the write returns as soon as the leader has it locally, so latency is basically local disk, well under a millisecond, and the Singapore follower catches up later. Synchronous: the write waits for Singapore to acknowledge, so it pays the 60 ms round trip, making every write at least 60 ms. If the follower goes down: async writes keep going at full speed (Singapore just falls further behind, then catches up when it returns), while strict synchronous writes stall completely, because there is no follower left to acknowledge them, until you drop the follower from the synchronous set or it comes back.

D4. Those 200 ms of writes were acknowledged to clients but never shipped, so when the follower is promoted they are simply gone, and the users who made them believe they succeeded. That is the data-loss window of asynchronous replication on failover. Synchronous replication would have made the leader wait for the follower before acknowledging each write, so a promoted follower would hold every acknowledged write and lose nothing. The day-to-day cost is that every single write, forever, pays the replication round trip and stalls if the follower is unavailable, which you pay on all writes to protect against the rare crash.

D5. Your own just-posted comment: must read the leader (or wait for catch-up), it is read-your-writes. A stranger's comments from last week: a follower is fine, old and not yours, staleness does not matter. Your bank balance right after a transfer you made: must read the leader or wait, you just changed it and you will panic if it looks wrong. Yesterday's signup dashboard: a follower is completely fine, the data is a day old already and a few seconds of lag is nothing.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-12-replication/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-12-replication/solution.py).

TODO 1, the follower applies a write after the lag:

```python
def _apply(self, off, key, value):
    time.sleep(self.lag_s)
    with self._lock:
        self._data[key] = value
        self._applied = off
```

The `time.sleep(self.lag_s)` is the whole point. The write exists on the leader, but the follower does not reflect it until this delay passes. Advancing `self._applied` is how the rest of the lab knows how far behind the follower is.

TODO 2, the Part 1 measurement, write then read the follower straight back:

```python
leader.write(KEY, value)
got = follower.read(KEY)
is_stale = got != value
```

No wait between the write and the read. That is what makes almost every read stale.

TODO 3, read your own writes:

```python
if follower.applied >= write_off:
    return follower.read(key)
return leader.read(key)
```

If the follower has caught up to your write's position, it is safe to read it. If it is still behind, read the leader, which always has your write.

TODO 4, the synchronous write:

```python
ok = wait_until(lambda: follower.applied >= off, timeout)
return off if ok else None
```

Do not return until the follower has applied this write. Return `None` if it never does within the timeout, which is exactly what a down follower looks like to a synchronous write.

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 40 ms lag, one follower.

```
==============================================================================
Part 1: write to the leader, read it straight back from the follower
==============================================================================
  lag set to 40 ms, one follower, 300 write-then-read cycles
  stale reads:   300 of 300  =  100.0% served the OLD value
  stale window:  43.5 ms on average, 46.1 ms at worst
  You wrote your comment to the leader and read it back from the follower
  a heartbeat later. The follower had not applied it yet, so you saw the
  old value. Refresh, and your own comment is missing for a moment.

==============================================================================
Part 2: the two fixes, and the stale percent drops to zero
==============================================================================
  fix A, read your writes (route to leader when the follower is behind)
           stale reads: 0 of 300  =  0.0%,  read stays fast
  fix B, wait for the follower to catch up, then read it
           stale reads: 0 of 50  =  0.0%,  but the read now waits 44.2 ms
  Both kill the stale read. Fix A loads the leader a little more. Fix B
  keeps the read on the follower but makes it wait out the lag.

==============================================================================
Part 3: asynchronous vs synchronous replication, the write-latency gap
==============================================================================
  async write latency:  0.003 ms   (leader logs it and returns)
  sync  write latency:  43.850 ms   (leader waits for the follower)
  synchronous is 16529x slower per write, and that cost is the lag itself

  with the follower DOWN:
    async write returned in 0.012 ms, but the follower never
      got it, so a failover right now would lose that write
    sync write gave up after 250 ms, unconfirmed: one down
      follower stalls every write until it comes back or is dropped

==============================================================================
Scoreboard
==============================================================================
  P1 stale % at lag            you =   95.0   actual =    100.0 %       close enough
  P2 stale window              you =   40.0   actual =     43.5 ms       close enough
  P3 sync write time           you =   45.0   actual =     43.9 ms       close enough
  P4 stale % after fix         you =    0.0   actual =      0.0 %       nailed it
```

Part 1 is the day in one line: 100 percent stale. At 40 ms of lag, a read fired right after the write always beats the follower to the value, so every read is old. The stale window is about 43 ms, roughly the lag, which is how long the follower keeps serving the old value.

Part 2 takes both fixes to zero. Reading your own writes stays fast, because the author's read is routed to the leader only while the follower is behind. Waiting for catch-up also hits zero but each read now waits about 44 ms, the lag you chose to pay to keep the read on the follower.

Part 3 is the tradeoff made of numbers. The async write is effectively free. The synchronous write takes about 44 ms, the full replication delay, because that is what it is waiting for on purpose. The big multiplier there is just microseconds versus tens of milliseconds and will swing run to run, so do not over-read it, read the two latencies. Then the follower goes down, and the two modes split cleanly: async keeps returning instantly but that last write would be lost on a failover, while the synchronous write cannot complete at all. That is the whole tradeoff, measured on a laptop: fast and lossy, or safe and slow, and a down follower makes you pick.

</details>
