---
title: "Day 29: failure, time, and the eight fallacies"
parent: "Week 5: distributed systems"
nav_order: 1
has_children: true
---

# Day 29
## Failure, time, and the eight fallacies, or why trusting the wall clock quietly eats your data ⏰

Today's one idea: the moment your system runs on more than one machine, two things you took for granted stop being true. Machines fail one at a time instead of all together, and the clocks on those machines do not agree. Today we take the second one, the clocks, and we watch it silently delete a quarter of the writes to a key, with no error and no log line, purely because one machine's clock ran a little fast. Then we fix it.

Welcome to week 5. This is the week everyone warns you about, and they are right, it bends the brain. So we start gently, with one concrete, measurable bug that you can hold in your hand. If you understand today, the rest of the week has a thread to pull on.

---

## Before you start ⏪

You do not need anything from a previous day as machinery today. What you need is a shift in attitude. Up to now, when you wrote code, "now" meant one thing, because there was one clock. From today, there are many clocks and they lie to each other. Hold that thought loosely and let the lab make it concrete. If you did Day 25 (at-least-once and idempotency), you already met the idea that the same thing can happen twice. Today's cousin is that two things can happen in the wrong order, and nobody notices.

One small Python fact helps. `time.time()` gives you the wall clock, the time of day, and it can jump backwards when NTP corrects it. `time.monotonic()` only ever moves forward and is the one you use to measure how long something took. Today is about what happens when you compare one machine's time of day against another's.

---

## Words you will meet today 📖

Partial failure is the thing that makes distributed systems hard. On one machine, either your program runs or it crashes, all or nothing. Across many machines, one can be dead, one can be slow, one can be fine, and a fourth cannot tell which of the other three is which. Most of the week is tools for living with partial failure.

Clock skew is the difference between two machines' clocks at the same instant. If node A reads 10:00:00.200 while node B reads 10:00:00.000, the skew between them is 200 ms. It is never exactly zero, and it drifts as the machines warm up and cool down.

A wall clock, or time-of-day clock, is the one that tells you it is half past three. It is what you compare across machines, and it is the one that can jump forward or backward when it is corrected.

NTP, the Network Time Protocol, is how machines pull their clocks back toward real time by asking time servers. Good NTP keeps a fleet within a few milliseconds of each other. It never gets you to zero, and a bad NTP setup can be off by far more.

Last-write-wins (LWW) is a conflict resolution rule. When two writes to the same key meet, keep the one with the larger timestamp and discard the other. Simple, popular, and the villain of today.

A logical clock is a counter that captures the order events happened in without reading the time of day at all. Lamport timestamps and version vectors are the famous ones, and they are Day 33. Today you meet the idea by watching it fix the bug.

The eight fallacies of distributed computing are a list of eight things programmers keep assuming about the network that are all false. We meet them at the end, because today's clock bug is their close relative.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [DDIA chapter 8](https://dataintensive.net/), "The Trouble with Distributed Systems." This is the chapter for the whole week's attitude, and the "Unreliable Clocks" section is exactly today. Kleppmann walks through clock drift, NTP's limits, and why timestamp ordering across machines is a trap. If you read one thing, read this.
- [The trouble with timestamps](https://aphyr.com/posts/299-the-trouble-with-timestamps) by Kyle Kingsbury (aphyr). Short, sharp, and precisely today's lab written up by the person who stress-tests these databases for a living. He shows why last-write-wins on wall-clock timestamps loses data in Cassandra and Riak. Read it right after the lab and it will click hard.
- [Fallacies of distributed systems](https://architecturenotes.co/p/fallacies-of-distributed-systems) by Mahdi Yusuf. A clear, well-drawn tour of the eight fallacies with a concrete bug for each. This is the vocabulary the whole week leans on.

Watch, after you have done the lab:
- [Clock Skew and Distributed Systems](https://www.youtube.com/watch?v=IjsJLTriLzs) by Donny Nadolny of PagerDuty, about 34 minutes. A real war story: a production outage traced to a clock jumping, inside ZooKeeper. This is today's lab happening to real engineers at 3 am.
- [Keeping Time in Real Systems](https://www.youtube.com/watch?v=BRvj8PykSc4) by Kavya Joshi, about 39 minutes. The best single talk on what a clock actually is in a computer, wall versus monotonic, drift, NTP, and why none of it is as simple as it looks.

### The thing nobody tells you about clocks (12 min)

When you write code on one machine, there is a clock, and it is good enough. You call `time.time()`, you get a number, and if you call it again later you get a bigger number. The world is sane.

Now put two machines side by side. Each has its own clock, a little quartz crystal that counts out the seconds. Those crystals are not identical, and they are not perfect. One runs a hair fast, one a hair slow, and the rate changes with temperature, so a machine working hard in a warm rack drifts differently from an idle one. Left alone, two servers' clocks wander apart by seconds a day. NTP fights this by regularly nudging each clock back toward a time server's notion of real time. On a healthy fleet, NTP keeps everyone within a few milliseconds. On an unhealthy one, I have personally seen machines minutes apart.

Here is the part that trips people. NTP does not only nudge gently. When a clock has drifted too far, NTP corrects it in a jump, and that jump can go backwards. So the wall clock, the time-of-day clock, is not monotonic. Call `time.time()` twice and the second value can be smaller than the first. Any code that assumed "later call, bigger number" has a bug waiting for the next NTP correction. That is why you measure durations with `time.monotonic()`, which only ever goes forward, and never with the wall clock.

Sit with the consequence. You cannot look at a timestamp from machine A and a timestamp from machine B and conclude which event happened first. The timestamps are each honest about their own machine's idea of the time, and those ideas disagree. We are about to build a system that ignores this, and watch it lose data.

### The bug: last-write-wins trusts a clock it should not (14 min)

Here is one of the most common conflict resolution rules in all of distributed data, and it is wrong in a way that is easy to miss.

You have a key-value store with two nodes, and both accept writes to the same key. This is an active-active, or multi-leader, setup, and it is exactly how Cassandra, DynamoDB's LWW mode, and old Riak work. Two nodes means two writes to the same key can happen without either node knowing about the other yet, so when they reconcile, you need a rule to pick a winner. The popular rule is last-write-wins: each write carries the wall-clock timestamp of the node that took it, and when two writes meet, you keep the one with the larger timestamp.

Think of two branches of a bank, each stamping passbook entries by the clock on their own wall, and head office keeping only the entry with the latest stamp. As long as both wall clocks agree, the latest stamp really is the latest entry. Now let one branch's clock run ten minutes fast. A deposit made later at the correct branch carries an earlier stamp than an older deposit at the fast branch, so head office keeps the older one and quietly drops the newer. Nobody made a mistake. The clock did.

That is the whole bug, and here it is in numbers. Node A's clock is 80 ms ahead. A client writes value X on node A at true time 100 ms, so it carries timestamp 180. Then 40 ms later, genuinely later, the client writes value Y on node B at true time 140 ms, which carries timestamp 140. Y is the newer value, the one the user actually wants to keep. But last-write-wins sees 140 is less than 180, keeps X, and throws Y away. The newer write is gone. There is no error, no exception, no log line. As far as the store is concerned, Y never happened.

Now scale it up, which is what the lab does. Twenty thousand writes to one hot key, split across the two nodes, node A's clock running some skew ahead of node B's. Count how many of the newer writes get silently discarded. At 50 ms of skew it is about 16 percent. At 200 ms it is about a quarter. One bad clock on one node, and a quarter of the updates to that key vanish.

One detail that matters, and it tells you where the bug lives. Two writes that both land on the same node can never be misordered by skew, because they share one clock, and that clock, however wrong, is at least consistent with itself. The bug only bites when a write crosses from the fast node to the slow one. That is why this is specifically a multi-leader problem. Route every write for a key through a single leader and the whole bug disappears, because there is only one clock and one order. Hold that thought, it is one of the fixes.

### Tightening the clocks helps, it does not save you (10 min)

The first instinct is "fine, I will just sync the clocks better." It is a reasonable instinct, and it genuinely helps, but it does not get you to safe, and the reason why is the sharpest idea of the day.

A newer write is only lost when the older write's clock lead is bigger than the gap in time between the two writes. Stare at that. If two writes are 50 ms apart and the skew is 10 ms, the later write's timestamp is still comfortably larger, so it wins, correctly. If the skew grows past 50 ms, the older write's stamp overtakes the newer one and LWW keeps the wrong value. For a fixed gap, the loss is a cliff, not a slope: exactly zero while skew is under the gap, then it appears the moment skew reaches the gap. You will see this cliff in the lab, clean and sudden at 50 ms.

So skew only hurts once it is larger than the time between the writes you are trying to order. Now you see why NTP helps: it shrinks the skew below most of your gaps, so most pairs order correctly. At 2 ms of skew the lab's loss falls to under one percent. Much better. But not zero, and here is why it can never be zero on a hot key. A popular key gets bursts of nearly simultaneous writes, two updates a fraction of a millisecond apart. Those gaps are smaller than even a couple of ms of skew, so those pairs can still flip. Tightening the clocks pushes the problem into the corner of near-concurrent writes, but it cannot promise the skew is smaller than every single gap, so it cannot promise zero loss. Syncing clocks is a mitigation, not a fix.

### The eight fallacies, and the real fixes (10 min)

The real fix is to stop ordering cross-machine events by the wall clock at all. The resolution rule, keep the larger value, was never the problem. The problem is what you feed it. Feed it wall-clock timestamps and you lose data. Feed it a logical version, a counter that each write takes one higher than the value it replaces, and skew becomes irrelevant, because a logical clock never reads the time of day. In the lab you re-run the exact same writes ordered by a logical version and the loss goes to zero. What used to be a silent loss becomes either a correct ordering, when the writes really did follow one another, or a detectable conflict, when they were truly concurrent, which a version vector flags for the application to resolve instead of silently dropping. That is Day 33, Lamport clocks and version vectors, and today is the reason they exist.

There are two other honest fixes worth naming. One is a dedicated time service with bounded uncertainty. Google's Spanner does not pretend its clocks are exact. It reads a clock that reports "the real time is somewhere in this interval" and simply waits out the interval before it commits, so it never orders two events it is not sure about. Google made the interval small by putting GPS receivers and atomic clocks in every data centre, which is both brilliant and a little mad. The other is the one from earlier: route all writes for a key through a single leader, so there is one clock and no cross-machine comparison at all. Most systems that need a clean order pick one of these rather than trusting wall clocks.

Finally, the eight fallacies of distributed computing, the list every engineer rediscovers the hard way. The network is reliable. Latency is zero. Bandwidth is infinite. The network is secure. Topology never changes. There is one administrator. Transport cost is zero. The network is homogeneous. Every one is false, and every outage story you will ever hear is someone having assumed one of them. Today's clock bug is their close cousin, a ninth you should add in your head: there is no global clock either. Assume none of these, and the week ahead is you building the tools that let you keep promises anyway.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Then copy your answers into [`notes/day-29-drills.md`](../notes/day-29-drills.md). About 8 minutes each.

D1. Node A's clock is 120 ms ahead of node B's. A client writes value X on node A at true time 1000 ms, then writes value Y on node B 40 ms later, at true time 1040 ms. Conflict resolution is last-write-wins by timestamp. What timestamp does each write carry? Which value survives, and which one did the user actually intend to keep? How small must the skew get before Y correctly wins?

D2. Writes to a key arrive on average every 50 ms, and two nodes are kept within 10 ms of each other by NTP. Roughly what fraction of consecutive write pairs could the skew possibly misorder, that is, have a gap smaller than the skew? If you tighten NTP to 1 ms, what happens to that fraction, and why can you never drive it to a guaranteed zero on a hot key?

D3. Explain why two writes that both land on the same node can never be misordered by that node's clock skew, however wrong its clock is. Then explain why that makes the clock-skew bug specifically a multi-leader problem, and what a single-leader design buys you here.

D4. List as many of the eight fallacies of distributed computing as you can from memory. Then pick two and give a one-sentence example of a concrete bug that assuming each one causes. Add "there is a global clock" as the ninth, and say what believing it costs you.

D5. You run a multi-leader store and you are losing writes to clock skew under LWW. For each fix, say what it costs and when you would reach for it: (a) tighten clocks with NTP or PTP, (b) switch conflict resolution to version vectors and keep siblings, (c) route all writes for a key through a single leader. Which one actually eliminates the silent loss, and which only shrinks it?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-29-clocks/clock_skew.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-29-clocks/clock_skew.py).

It is a deterministic simulation, standard library only, no network, no threads, no files, and it runs in well under a second. It builds one seeded stream of 20,000 writes to a single key and replays it under different clock conditions. Part 1 is the clock-skew bug: watch a newer write get eaten by an older one, then sweep the skew and count how many newer writes last-write-wins silently loses, then pin the exact threshold where loss begins. Part 2 tightens the clocks to NTP quality and shows the loss shrink but not vanish. Part 3 throws away the wall clock, orders the same writes by a logical version, and watches the loss go to zero.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. Node A's clock runs 200 ms ahead, writes arrive about 50 ms apart. What percent of the newer writes does last-write-wins silently discard?
- P2. Fix the gap between writes at exactly 50 ms and grow the skew from zero. At what skew, in ms, does the first newer write start getting lost?
- P3. Tighten the clocks to 2 ms of skew. What percent of newer writes are still lost?
- P4. Order the same writes by a logical version instead of the wall clock, at 200 ms of skew. What percent are lost now?

P2 is the one to feel in your gut before you run it. The answer is not a vague "some skew." It is a specific number, and it is equal to something already on the page.

### Fill in the TODOs

The lab is four small functions, and they are the whole lesson. Two of them are clocks, two of them are the same resolution rule applied to each clock.

1. TODO 1 is the wall-clock stamp: the time a write happened plus the node's own clock offset. This one line is the mistake, trusting a local clock to mean the same thing everywhere.
2. TODO 2 is last-write-wins: the newer write is lost when its timestamp is not strictly greater than the stored one.
3. TODO 3 is the fix, a logical stamp: take the next version up from the value you are replacing, no clock involved.
4. TODO 4 is the same win-or-lose check as TODO 2, but on versions instead of timestamps. The point is that the rule never changed. Only what you fed it did.

```bash
cd labs/day-29-clocks
python3 clock_skew.py
```

### What you're going to discover

Part 1 is the shock. A single node with a clock 200 ms fast makes last-write-wins silently drop about a quarter of the newer writes to a hot key, and nothing anywhere reports an error. Then the threshold sweep gives you the crisp version: with a fixed 50 ms gap, loss is exactly zero until skew reaches 50 ms, then it jumps straight up. Skew is harmless until it is bigger than the gap between your writes.

Part 2 is the "but surely NTP fixes it" moment, answered honestly. At 2 ms of skew the loss falls under one percent. A huge improvement, and still not zero, because the near-simultaneous writes to a hot key have gaps smaller than even 2 ms. You cannot sync your way to safe.

Part 3 is the relief. Order the same writes by a logical version and the loss is zero, at any skew, because the logical clock does not read the time of day. That is the whole argument for Day 33 in one measured number.

### Traps ⚠️

- The simulation measures each write against the one it is directly replacing, which is the clean way to see the mechanism. Real last-write-wins keeps a running maximum timestamp, so a single very fast clock can "poison" a key for a window as long as its whole skew, blocking many later writes at once. In other words, reality is worse than the lab's number, not better. Do not walk away thinking a quarter is the ceiling.
- Ties go to the older write, because the loser's stamp has to be strictly greater to win. That is a real and deliberate detail. Two writes with the exact same timestamp, one on each node, and one of them just loses. Do not treat equal timestamps as safe.
- Part 3's zero is not magic and it is not the whole story. The logical version loses nothing here because the writes in the stream genuinely follow one another. Two truly concurrent writes would get the same version and become a detectable conflict, which a version vector surfaces rather than silently dropping. Zero silent loss, not zero conflicts. Keep that distinction.

### Deliverable

[`labs/day-29-clocks/RESULTS.md`](../labs/day-29-clocks/RESULTS.md) has a skeleton. Paste the output, and write one line: a skew of how many ms made last-write-wins drop what percent of newer writes, and why did ordering by a logical version take it to zero?

---

## Block 4: write (30 min) 📣

Your angle today is the quiet horror of it: "I made a database silently delete a quarter of the writes to a key using nothing but one clock that ran 200 ms fast, and it logged no error at all. The fix is to stop trusting the wall clock to order events across machines." The sweep table and the clean 50 ms threshold both make good screenshots.

Example posts are on the [Day 29 posts](../shares/day-29-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the percent of newer writes you measured lost at 200 ms of skew, and one thing you still cannot explain. If your brain hurts, good, that is the week working. Message me when it does and we slow down together.

Day 30 is CAP for real, and its grown-up cousin PACELC. The famous "pick two" is a cartoon, and the truth is more useful. Today you saw one way a distributed system quietly breaks a promise. Tomorrow you learn the language for the choice every distributed system makes about which promise to keep when the network splits.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Write X carries 1000 plus the 120 ms skew, so timestamp 1120. Write Y carries 1040 plus nothing, so timestamp 1040. Last-write-wins keeps the larger stamp, which is X's 1120, so X survives and Y is silently discarded, even though Y is the newer value the user actually meant to keep. Y wins correctly only when its true-time lead over X, which is 40 ms, exceeds the skew. So the skew has to drop below 40 ms. At exactly 40 ms they tie at 1040, and since ties go to the older write, Y still loses. The skew must be strictly under 40 ms, the gap between the two writes.

D2. A pair can be misordered only when its gap is smaller than the skew. With gaps averaging 50 ms and a 10 ms skew, the share of pairs closer together than 10 ms is modest, roughly a fifth if arrivals are Poisson, so a meaningful but minority slice is at risk. Tighten NTP to 1 ms and that share drops sharply, to a few percent of pairs, because far fewer writes land within 1 ms of each other. You can never reach a guaranteed zero on a hot key because a hot key always gets some near-simultaneous writes, pairs with sub-millisecond gaps, and any nonzero skew is larger than those. Tighter clocks shrink the risk toward the near-concurrent corner, they do not remove it.

D3. Two writes on the same node are stamped by the same clock. That clock may be wildly wrong in absolute terms, but it is consistent with itself: a later call returns a stamp at least as large as an earlier one (ignoring the NTP-jump case, which same-node code guards with a monotonic clock). So same-node writes are ordered correctly regardless of skew. The bug needs two different clocks to disagree, which only happens when a write crosses from one node to another. That makes it a multi-leader problem specifically: more than one node accepts writes to the same key, so their clocks get compared. A single-leader design routes every write for a key through one node, so there is one clock and one order and nothing to compare. It buys you a clean order for free, at the cost of funnelling all writes for that key through one machine.

D4. The eight: the network is reliable; latency is zero; bandwidth is infinite; the network is secure; topology never changes; there is one administrator; transport cost is zero; the network is homogeneous. Two examples. Assuming the network is reliable means you fire a request and never handle the case where the response is lost, so a payment looks failed and the user retries and pays twice. Assuming latency is zero means you make one remote call per item in a loop, and a page that was instant in testing takes nine seconds in production because each call crossed a region. The ninth, there is a global clock, is today's whole lab: believe it and you order events across machines by wall-clock timestamps, and a skewed clock silently eats your newer writes.

D5. (a) Tighten clocks with NTP or PTP. Cost is operational, running and monitoring time sync, and it only shrinks the loss, never removes it, because you cannot promise skew is under every gap. Reach for it always as hygiene, never as the whole answer. (b) Version vectors and keep siblings. Cost is that your application now has to resolve conflicts, since concurrent writes come back as multiple values instead of one, and your data model has to carry the version metadata. This one actually eliminates the silent loss, because nothing is dropped on a wall-clock comparison. Reach for it when you genuinely need multi-writer availability and can define a sensible merge. (c) Single leader per key. Cost is that all writes for a key go through one node, a throughput ceiling and a failover story for that node. It also eliminates the silent loss, by removing the cross-clock comparison entirely. Reach for it when a clean order matters more than multi-writer availability. The headline: (a) only shrinks the loss, while (b) and (c) actually eliminate it.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-29-clocks/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-29-clocks/solution.py).

TODO 1, the wall-clock stamp, which is the whole mistake of the day in one line:

```python
return true_time_ms + skew_ms
```

TODO 2, last-write-wins: the newer write is lost when its stamp is not strictly greater than the stored one, so ties go to the older write:

```python
return incoming_ts <= stored_ts
```

TODO 3, the fix, a logical stamp that takes the next version up from the value it replaces and never reads a clock:

```python
return stored_version + 1
```

TODO 4, the same resolution rule as TODO 2, but on versions. Because TODO 3 hands out an ever-rising version, this never fires, which is the point: the rule was fine, the wall clock was the problem:

```python
return incoming_version <= stored_version
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. The numbers are identical on every machine because the write stream is seeded.

```
==============================================================================
Part 1: the clock-skew bug. A newer write, silently eaten by an older one
==============================================================================
  One pair, by hand. Node A's clock is 80 ms ahead of node B's.
    write A: true time 100 ms on node A  ->  timestamp 180
    write B: true time 140 ms on node B  ->  timestamp 140
    B really happened 40 ms AFTER A, so B is the newer value.
    but last-write-wins sees 140 <= 180, keeps A, and drops B.
    the newer write is gone. No error, no log line. That is the bug.

  Now the real thing: 20,000 writes to one key, gaps averaging
  50 ms (Poisson), split across the two nodes. Node A's clock runs
  ahead by a growing skew. Percent of NEWER writes that LWW silently loses:

     skew (ms)     newer writes lost
          0          0.0%  
          1          0.5%  
          2          0.9%  #
          5          2.3%  ##
         10          4.7%  #####
         20          8.5%  ########
         50         15.9%  ################
        100         21.9%  ######################
        200         24.7%  #########################
        500         25.1%  #########################

  Zero skew loses nothing. As the clock lead grows the loss climbs and
  then levels off: once A is reliably ahead, every write that crosses from
  the fast node to the slow one is at risk. One bad clock, a quarter of the
  updates to a hot key quietly vanishing.

  The threshold, made crisp. Fix the gap between writes at exactly
  50 ms and grow the skew. Loss is a cliff, not a ramp:
     skew   0 ms   ->     0.0% lost
     skew  10 ms   ->     0.0% lost
     skew  30 ms   ->     0.0% lost
     skew  49 ms   ->     0.0% lost
     skew  50 ms   ->    50.0% lost
     skew  51 ms   ->    50.0% lost
     skew  80 ms   ->    50.0% lost
  Loss is exactly zero until skew reaches 50 ms, which is the gap
  between writes. Below the gap, skew cannot reorder two writes. At or above
  it, the older write's stamp overtakes the newer one and LWW keeps the wrong
  value. Skew only hurts you once it is larger than the time between writes.

==============================================================================
Part 2: tighten the clocks (NTP). It shrinks the loss, it does not kill it
==============================================================================
  NTP keeps machine clocks within a few milliseconds of each other. So the
  skew is tiny now, not 200 ms. Same write stream, small skews:

     skew (ms)     newer writes lost
        0.5         0.19%
          1         0.47%
          2         0.92%
          5         2.35%
         10         4.75%

  Far better: at a couple of ms of skew the loss is a fraction of a percent,
  not a quarter. But look closely, it is not zero. A hot key gets bursts of
  nearly simultaneous writes, and any two writes closer together than the
  skew can still be reordered. Tightening the clocks pushes the problem into
  the corner of near-concurrent writes. It never promises to remove it,
  because you cannot promise skew is smaller than EVERY gap.

==============================================================================
Part 3: the real fix. Stop ordering cross-machine events by the wall clock
==============================================================================
  The resolution rule was never the problem. Keeping the larger value is
  fine. The problem is what we fed it: a wall-clock stamp that means
  different things on different machines. So feed it something else.

  Replay the SAME 20,000 writes, at the same 200 ms of skew, but order
  them by a logical version (each write takes the next number up from the
  one it replaces) instead of a timestamp:
    newer writes silently lost = 0.0%

  Zero. A logical clock never reads the time of day, so no amount of skew can
  reorder two writes that truly follow one another. What used to be a silent
  loss becomes either a correct ordering (if the writes are causally related)
  or, for writes that really were concurrent, a conflict a version vector can
  DETECT and hand to the application, instead of a value that just disappears.
  That is Day 33: Lamport clocks and version vectors.

  Two other honest fixes:
    - A dedicated time service with BOUNDED uncertainty. Google's Spanner
      reads a clock that tells it 'the real time is within these bounds' and
      simply waits out the uncertainty before committing. It made the bound
      small with GPS and atomic clocks in every data centre, which is both
      brilliant and slightly mad.
    - Single-writer ordering: route all writes for a key through one leader,
      so there is one clock and one order, no cross-machine comparison at all.

  And the eight fallacies of distributed computing, the list everyone
  rediscovers the hard way: the network is reliable; latency is zero;
  bandwidth is infinite; the network is secure; topology never changes;
  there is one administrator; transport cost is zero; the network is
  homogeneous. Today's clock-skew bug is their close cousin: time is not
  global either. Assume none of these and you will not be surprised.

==============================================================================
Scoreboard
==============================================================================
  P1 LWW loss at 200 ms skew         you =  20.00   actual =   24.68 %       close enough
  P2 loss threshold vs gap           you =  50.00   actual =   50.00 ms       close enough
  P3 LWW loss at 2 ms (NTP)          you =   1.00   actual =    0.92 %       close enough
  P4 logical-clock loss              you =   0.00   actual =    0.00 %       close enough

==============================================================================
The number to carry
==============================================================================
  A single node whose clock ran 200 ms ahead made last-write-wins
  silently drop 25% of the newer writes to a hot key. For a fixed gap
  the loss is zero only while the skew stays under that gap (50 ms here);
  past it, the newer write loses. NTP shrank the loss to a fraction of a
  percent (0.92% at 2 ms) but never to a guaranteed zero. Ordering by a
  logical version instead of the wall clock took it to 0%. The lesson:
  never trust the wall clock to order events across machines.
```

Part 1 is the day. The hand-worked pair makes the mechanism undeniable: write B happened later in real time, yet it carried the smaller timestamp, so last-write-wins kept the older A and dropped B without a murmur. The sweep then shows how expensive this gets, about a quarter of the newer writes to a hot key gone at 200 ms of skew, from one node's bad clock. And the fixed-gap cliff is the sharp lesson under it all: loss is exactly zero while the skew stays below the 50 ms gap between writes, then it appears the instant skew reaches the gap. Skew is harmless until it is bigger than the time between the events you are ordering.

Part 2 answers the obvious objection honestly. Yes, NTP helps, a lot, dropping the loss to under one percent at 2 ms of skew. No, it does not save you, because a hot key always has some near-simultaneous writes whose gaps are smaller than even that tiny skew. Syncing clocks is good hygiene and a genuine mitigation. It is not a guarantee.

Part 3 is the point of the whole week starting to show. Keep the exact same writes and the exact same 200 ms of skew, but order by a logical version instead of a timestamp, and the loss is zero. The resolution rule never changed. All that changed is that the logical clock does not read the time of day, so skew cannot touch it. That is why Lamport clocks and version vectors exist, and it is Day 33. The one line to carry out of today: never trust the wall clock to order events across machines.

</details>
