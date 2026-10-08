---
title: "Day 13: partitioning and sharding"
parent: "Week 2: storage"
nav_order: 6
has_children: true
---

# Day 13
## Partitioning and sharding, the hot shard, and why adding a server should not move all your data 🪓

Today's one idea: splitting one big table across many machines sounds simple, and the splitting itself is simple. The hard parts are two. One key can get so hot that no amount of shards saves it. And a naive split means that adding one server forces you to move almost all your data. Both of these you will measure yourself today, in plain Python, and both of them decide real architectures.

So far this week the data lived on one disk. One machine, one file, a stack of pages. That works until it does not fit, or until one machine cannot take the traffic. Then you split the data across many machines, and a whole new set of problems walks in the door. This is the day those problems get names and numbers.

---

## Before you start ⏪

You need Day 8's picture of data as rows on a disk, and the hashing idea you have met in passing (a hash function turns a key into a number that looks random but is always the same for the same key). You do not need anything fancy. If you can read a dictionary and a for loop, you can do today's lab. The maths is one division: 1 divided by the number of shards.

---

## Words you will meet today 📖

A partition is one slice of your data. You cut a big table into slices so that each slice is small enough to handle. Cut it by rows and that is horizontal partitioning, which is the one we care about today.

A shard is a partition that lives on its own machine. Sharding is just horizontal partitioning where each slice sits on a separate server, so the word carries the extra meaning of "on a different box."

A shard key, or partition key, is the column you split on. User id, order id, hashtag. Everything about how your traffic lands depends on this one choice, and it is painful to change later.

Hash partitioning runs the key through a hash function and uses the result to pick a shard, usually hash(key) modulo the shard count. It scatters neighbouring keys all over the place, which is usually what you want.

Range partitioning keeps neighbours together. Keys 1 to a million on shard 0, the next million on shard 1, and so on. Good for range scans, dangerous when popularity clusters in one range.

A hot shard is a shard getting far more than its fair share of traffic while the others sit idle. The thing that goes wrong. Today is mostly about how hot shards happen and what you can and cannot do about them.

Consistent hashing is a smarter way to assign keys to shards, using a ring, so that adding or removing a shard moves only a small slice of the keys instead of nearly all of them.

A virtual node, or vnode, is a trick inside consistent hashing where each real shard is placed on the ring in many spots instead of one, so the load comes out even.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [DDIA chapter 6](https://dataintensive.net/), partitioning. This is the chapter for today, start to finish. Kleppmann walks through hash vs range, skewed workloads and the hot spot, and rebalancing, in exactly the order we are doing it. If you read one thing, read this.
- [Consistent hashing, what it is and how to implement it](https://arpitbhayani.me/blogs/consistent-hashing/) by Arpit Bhayani. He builds the ring with a sorted array and binary search, which is precisely what your lab does with `bisect`. Read it alongside Part 3.
- [The System Design Primer, sharding section](https://github.com/donnemartin/system-design-primer). Scroll to "Sharding." Short, practical, and it lists the real downsides people hit, like joins across shards and the celebrity problem.

Watch, after the lab:
- [What is consistent hashing and where is it used?](https://www.youtube.com/watch?v=zaRkONvyGr8) by Gaurav Sen, about 11 minutes. The classic explainer. The ring, the rebalancing, the why. Watch this one.
- [Algorithms you should know before system design interviews](https://www.youtube.com/watch?v=xbgzl2maQUU) by ByteByteGo, about 7 minutes. Consistent hashing sits inside a short tour of the handful of ideas that keep coming up.

### Splitting one table across many machines (12 min)

Picture the users table from last week, except now it has grown past what one machine can hold or serve. You have two honest options. One, buy a bigger machine. This is vertical scaling, and it works for a long time, further than people admit, but it has a ceiling and the biggest machines cost a silly amount. Two, split the table across many machines. This is sharding, and it has no ceiling, but it brings the problems we spend today on.

Be careful not to mix this up with replication, which was Day 12. Replication makes copies of the same data on many machines, so every replica has everything. Sharding splits different data onto different machines, so each shard has only its slice. Replication is for reads and for surviving a machine dying. Sharding is for when the data or the write load is simply too big for one box. Real systems do both at once: each shard is itself replicated. Today we hold replication still and look only at the split.

The whole game comes down to one decision, the shard key. You pick a column, and a rule that turns that column into a shard number. Pick well and traffic spreads evenly and queries stay fast. Pick badly and you get a hot shard, or queries that have to visit every shard and glue the results back together. The rule is easy to write. Living with it is the hard part, because changing the shard key later usually means rebuilding the whole dataset.

### Hash, range, and the hot shard (16 min)

There are two common rules, and they fail in opposite ways.

Range partitioning keeps neighbours together. Users with id 1 to a million on shard 0, the next million on shard 1. This is lovely for range queries, "give me every order from last Tuesday" lands on one shard. The danger is when your traffic is not spread evenly across the range. Think of a table partitioned by signup date, where yesterday's rows are red hot and last year's are cold. Every new write piles onto the newest shard while the rest nap. Or think of user id, where your oldest accounts happen to be your biggest celebrities. One range holds all the heat. In the lab you will see a range split where a single shard takes 94.9% of all traffic while seven shards share the scraps. That is a range hot shard, and it is brutal.

Hash partitioning fixes that by scattering. Run the key through a hash and neighbouring keys fly to different shards, so no single range can be hot. The distinct keys come out beautifully even, roughly the same count on every shard. You will measure this: 100,000 keys across 8 shards land at about 12,000 to 12,700 per shard. Lovely.

But here is the catch, and it is the heart of the day. Even load spreads the keys, not the traffic. Traffic is never even. It follows a power law, a Zipf shape, where the top few keys are enormous and there is a long thin tail. One Virat Kohli, one viral tweet, one celebrity user. That one key is a big fraction of all your requests on its own, and a hash sends that one key to exactly one shard. It cannot be split. One key, one shard, always.

So the shard holding the celebrity runs hot, and now ask the question everyone asks: can I fix it by adding more shards? You will test this directly. Push from 8 shards to 64 to 256. The hottest shard drops a bit, from about 26.7% to 22% to 19.9%, and then it stops. It can never go below the celebrity's own share, which in the lab is 19.6%. Adding servers spreads the ordinary keys thinner and thinner, and does nothing at all for the one key that is too big. This is the hot shard problem stated as a number, and it is why "we will just add shards" is not an answer to a skewed workload. The IPL final does not get less popular because you bought more servers.

### Adding a server should not move all your data (14 min)

Now the second problem, which is about change, not about heat.

You are running 8 shards with the simple rule, shard = hash(key) % 8. It works. Traffic grows, and you want a 9th shard. So you change the rule to hash(key) % 9 and restart. What just happened to your existing data?

Almost all of it is now on the wrong shard. A key that hashed to 100 was on shard 100 % 8 = 4, and it is now supposed to be on 100 % 9 = 1. The modulo changed for nearly every key, because dividing by 9 instead of 8 reshuffles the remainders across the board. In the lab you will measure 89% of keys needing to move when going from 8 to 9, and it gets worse as the cluster grows: 98.4% when going from 64 shards to 65. There is a clean formula behind it, N over N plus 1, which marches toward 100% as N gets large. In real life, "89% of keys move" means copying almost your entire dataset across the network, with the cluster half-broken while it happens, just to add one machine. Teams genuinely lose weekends to this.

Consistent hashing is the fix, and the idea is simple once you see it. Instead of hash modulo shard count, imagine a big circle of hash values, say 0 up to a huge number and then wrapping back to 0. Place each shard at a few points on this circle by hashing the shard's name. To find a key's shard, hash the key to a point on the circle and walk clockwise until you hit the first shard. That shard owns the key.

Why does this help? When you add a shard, it drops onto the circle at its own points and steals only the slice of arc just behind each of its points. Every other key keeps walking to the same shard it always did. Only the keys in those small new arcs move, and they move onto the new shard, nobody else is disturbed. The fraction that moves is about 1 over N plus 1. In the lab, 8 shards to 9 moves 11.7% of keys, almost exactly the 1/9 the theory promises, against modulo's 89%. That is the difference between a weekend-long migration and a shrug.

One detail makes it actually work: virtual nodes. If each shard sat at a single point on the ring, the arcs would come out wildly uneven, one shard owning a huge slice by luck. So each shard is placed at many points, a couple of hundred in the lab, and the law of averages evens the load out. Real systems like Cassandra and DynamoDB do exactly this.

Now the part people forget, and you should not. Consistent hashing fixes the cost of moving data when the cluster changes. It does not fix the hot key. The celebrity still hashes to one point and lands on one shard, and that shard still melts. You will see it in the lab: even with the ring and vnodes, the hottest shard sits at 39.3% because the celebrity is on it. Consistent hashing and the hot shard are two different problems. The hot key needs a different tool: split that one key across shards, or cache it, or give it a dedicated shard. Keep them separate in your head and you will be ahead of most people in the room.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-13-drills.md`](../notes/day-13-drills.md).

D1. You hash-shard your keys so they spread evenly, but one celebrity key is 20% of all traffic on its own. What is the lowest the hottest shard's load can go, no matter how many shards you add? Why can you not get below it?

D2. You run 10 shards with shard = hash(key) % 10 and add one to make 11. Using the N over N plus 1 rule, roughly what fraction of keys must move? Now do it for 100 shards going to 101.

D3. Same move, 10 shards to 11, but now you use consistent hashing with virtual nodes. Roughly what fraction of keys move this time, and where exactly do those keys go?

D4. You partition users by id into ranges, and it turns out your oldest users (the lowest ids) are your biggest celebrities. What breaks? If you switch to hash partitioning, does that fully fix it, or only part of it?

D5. You use consistent hashing with vnodes, so every shard holds about the same number of keys. One shard still sits at 40% CPU because of a single celebrity key. Name two concrete fixes, and say what each one costs you.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-13-sharding/sharding.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-13-sharding/sharding.py).

It builds a realistic skewed traffic distribution over 100,000 keys, then does three things. Part 1 shards the keys by hash and by range and measures the load per shard, so you watch a celebrity key melt one shard and watch adding servers fail to save it. Part 2 grows the cluster by one shard with plain modulo and measures how many keys have to move. Part 3 does the same move with consistent hashing and measures how few move.

Standard library only, no database files, runs in a few seconds.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The single hottest celebrity key's share of all traffic, as a percent.
- P2. Range partitioning across 8 shards, where popularity lines up with the range. The hottest shard's share, as a percent.
- P3. Modulo resharding, 8 shards to 9. What percent of keys end up on a different shard?
- P4. Consistent hashing, 8 shards to 9. What percent of keys move this time?

P3 and P4 are the pair to feel in your gut before you run it. Write a number for each. The gap between them is the whole day.

### Fill in the TODOs

1. TODO 1 is hash sharding: the shard for a key is its hash modulo the shard count. One line.
2. TODO 2 is range partitioning: the shard for key index `i` is `i` divided by the block size, clamped to the last shard.
3. TODO 3 is the modulo remap test: a key moved if `hash % n` is not equal to `hash % (n + 1)`.
4. TODO 4 is the consistent hashing lookup: binary search the sorted ring for the first point at or after the key's hash, wrap around with modulo, and read off which shard owns that point.

```bash
cd labs/day-13-sharding
python3 sharding.py
```

### What you're going to discover

Part 1 is the hot shard, twice. Hash sharding spreads the distinct keys almost perfectly even, and yet the hottest shard is well above its fair share, because the celebrity key dumps 19.6% onto one shard. Then you crank the shard count to 256 and watch the hottest shard refuse to drop below that 19.6% floor. Range partitioning is worse in a different way: one shard swallows 94.9% of traffic because the popular head all sits in one range.

Part 2 and Part 3 are the headline. Adding one shard with modulo moves 89% of your keys, and that climbs toward 100% as the cluster grows. The same move with consistent hashing moves 11.7%, about 1 over N plus 1, and only onto the new shard. Then the sting in the tail: consistent hashing's hottest shard is still at 39.3%, because it never promised to fix the celebrity, only the migration.

### Traps ⚠️

- Python's built-in `hash()` is randomised per run for strings, so it would give different shard numbers every time you start the program. The lab uses md5 instead so the numbers are stable and identical on every machine. If you swap in `hash()`, do not be surprised when your scoreboard wanders.
- Consistent hashing with one point per shard gives lumpy, uneven load. The virtual nodes are not an optional nicety, they are the thing that makes the load even. Try dropping `VNODES` to 1 and watch the per-shard load go haywire.
- Do not confuse "keys spread evenly" with "traffic spread evenly." Hash sharding gives you the first. The celebrity key is why you do not get the second.

### Deliverable

[`labs/day-13-sharding/RESULTS.md`](../labs/day-13-sharding/RESULTS.md) has a skeleton. Paste the output, and write one line: to add a single shard, how many keys did modulo move versus consistent hashing, and why is that the difference between a weekend and a shrug?

---

## Block 4: write (30 min) 📣

Your angle today is the number that surprises people: "adding one server to a sharded database can mean copying almost all your data, unless you use the right trick, and even then your celebrity user still melts one shard." The celebrity floor and the 89% versus 12% comparison both make clean screenshots.

Example posts are on the [Day 13 posts](../shares/day-13-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the two numbers you measured (modulo remap versus consistent hashing remap), and one thing you still cannot explain.

Day 14 is the first real storage design, done on paper and timed. You take everything from this week, pages and row stores, B-trees and LSM-trees, indexes, transactions, replication, and today's sharding, and you design the database layer for something real. Today you learned the last big piece. Tomorrow you put the week together.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The hottest shard can never go below 20%, the celebrity's own share. A hash sends one key to one shard, and one key cannot be split across machines. Adding shards spreads all the other keys thinner, so the hottest shard creeps down toward 20% and stops there. The celebrity is a floor you cannot push through by buying servers.

D2. Modulo remap is N over N plus 1. For 10 to 11 that is 10/11, about 90.9% of keys moving. For 100 to 101 it is 100/101, about 99.0%. The bigger the cluster, the closer to 100%, which is the opposite of what you want: the more shards you have, the more painful adding one becomes.

D3. With consistent hashing the move is about 1 over N plus 1. For 10 to 11 that is 1/11, roughly 9%. Those keys move only onto the new shard, the one you just added. Every other key still walks clockwise to the same shard it always did, so no other shard is disturbed. That locality is the whole point.

D4. Range partitioning by id puts all the low ids, your celebrities, into the first range, so shard 0 takes almost all the traffic. A classic range hot shard. Switching to hash partitioning fixes the range clustering: the celebrities scatter across shards so no single range is hot. But it only fixes part of it. Each individual celebrity key still lands on one shard and makes that shard hot. Hash cures the clustering, not the single hot key.

D5. Two fixes, pick any two. One, split the hot key: write it as key#1, key#2 and so on across several shards and merge on read, which costs you fan-out and a merge step on every read of that key. Two, put a cache in front of the hot key so most reads never reach the shard, which costs you staleness and a cache to run. Three, give the hot key its own dedicated shard or replica set sized for it, which costs operational complexity and a special case in your routing. The theme: the hot key needs a targeted fix, not a general one.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-13-sharding/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-13-sharding/solution.py).

TODO 1, hash sharding:

```python
return h % n
```

The hash scatters the key, and the modulo folds it into one of `n` shards. This is the whole of plain hash sharding, and also the whole of why resharding hurts.

TODO 2, range partitioning:

```python
return min(i // per, n - 1)
```

`per` is the block size, keys per shard. Key index `i` falls in block `i // per`. The `min` clamps the leftover keys into the last shard instead of overflowing past the end.

TODO 3, the modulo remap test:

```python
return (h % n) != (h % (n + 1))
```

Where the key sits today, `h % n`, versus where it sits after adding one shard, `h % (n + 1)`. If those differ, the key has to move. For most keys, they differ.

TODO 4, the consistent hashing lookup:

```python
idx = bisect.bisect_left(positions, h) % len(positions)
return owners[idx]
```

`positions` is the sorted ring. `bisect_left` finds the first ring point at or after the key's hash, which is the "walk clockwise" step. The modulo wraps a key that is past the last point back around to the first point. `owners[idx]` tells you which shard sits there.

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 100,000 keys, Zipf exponent 1.2. The numbers are identical on every machine because the lab uses md5, not the randomised built-in `hash()`.

```
==============================================================================
Part 1: the hot shard. Spread the keys, and watch one key melt a shard
==============================================================================
  100,000 keys, Zipf-like traffic (exponent 1.2).
  the single hottest key alone is 19.6% of all traffic.

  Hash sharding, 8 shards. Ideal per shard would be 12.5%.
    distinct keys per shard: 12,227 to 12,683  (even)
    traffic per shard, hottest = 26.7%  (shard 7)
    the celebrity key sits on shard 7, and it alone is 19.6%.

  Does adding shards fix the hot shard? Hottest shard's traffic share:
       8 shards -> hottest =  26.7%  (floor is the celebrity, 19.6%)
      64 shards -> hottest =  22.1%  (floor is the celebrity, 19.6%)
     256 shards -> hottest =  19.9%  (floor is the celebrity, 19.6%)
  More shards spread the OTHER keys thinner, but one key cannot split,
  so the hottest shard can never drop below the celebrity's own share.

  Range partitioning, 8 shards (popularity correlates with range).
    traffic per shard, hottest = 94.9%  (shard 0)
  One range holds the whole popular head, so that shard gets almost
  everything while the rest sit idle. This is the range hot shard.

==============================================================================
Part 2: resharding pain. Grow from N shards to N+1 with plain modulo
==============================================================================
  Going 8 shards -> 9 shards, hash % count.
    88,962 of 100,000 keys change shard = 89.0% remapped.

  Watch it get worse as the cluster grows:
      2 -> 3   shards:   66.7% remapped   (theory N/(N+1) = 66.7%)
      4 -> 5   shards:   80.1% remapped   (theory N/(N+1) = 80.0%)
      8 -> 9   shards:   89.0% remapped   (theory N/(N+1) = 88.9%)
     16 -> 17  shards:   94.3% remapped   (theory N/(N+1) = 94.1%)
     32 -> 33  shards:   96.9% remapped   (theory N/(N+1) = 97.0%)
     64 -> 65  shards:   98.4% remapped   (theory N/(N+1) = 98.5%)
  Almost every key moves. In real life that is copying your entire
  dataset across the network just to add one machine.

==============================================================================
Part 3: consistent hashing. Put shards on a ring, add one, measure churn
==============================================================================
  8 shards, 200 virtual nodes each, 1600 points on the ring.
  Add one shard (8 -> 9):
    11,688 of 100,000 keys change shard = 11.7% remapped.
    theory says about 1/(N+1) = 11.1%.

  The keys that move only move onto the new shard. Everyone else stays.

  But consistent hashing does NOT fix the hot key. Traffic per shard,
  hottest = 39.3%: the celebrity still lands on one shard and melts it.
  Consistent hashing fixes the MIGRATION cost, not the skew. The hot key
  needs its own fix: split it, cache it, or give it a dedicated shard.

==============================================================================
Scoreboard
==============================================================================
  P1 celebrity key share           you =   15.0   actual =     19.6 %       close enough
  P2 range hottest shard           you =   80.0   actual =     94.9 %       close enough
  P3 modulo remap 8->9             you =   85.0   actual =     89.0 %       close enough
  P4 consistent remap 8->9         you =   12.0   actual =     11.7 %       close enough

==============================================================================
The number to carry
==============================================================================
  To add one shard, plain modulo moved 89% of the keys, and that
  climbs toward 100% as the cluster grows. Consistent hashing moved only
  12%, about 1/(N+1). Same goal, but one is a weekend-long
  migration copying the whole dataset, and the other is a shrug.
  Neither one saves you from the celebrity key. That is a separate fight.
```

Part 1 is the hot shard made concrete. Hash sharding spreads the 100,000 distinct keys evenly, 12,227 to 12,683 per shard, textbook. And yet the hottest shard is at 26.7%, more than double the 12.5% ideal, because the celebrity key alone is 19.6% and it all lands on shard 7. The sweep is the lesson: at 256 shards the hottest shard is still 19.9%, pinned to the celebrity's own share. You cannot buy your way under it. Range partitioning is the other failure, a single shard at 94.9% because the whole popular head sits in one range.

Part 2 and Part 3 are the day. Adding one shard with plain modulo moves 89% of the keys, and the little table shows it getting worse, 98.4% by the time you are at 64 shards, because the ratio is N over N plus 1 and that marches to 100%. Consistent hashing with virtual nodes moves 11.7% for the same 8-to-9 change, close to the 1/9 the theory predicts, and those keys move only onto the new shard. That is the gap between copying your whole dataset and copying a ninth of it.

And the quiet warning at the end of Part 3: even with the ring, the hottest shard is 39.3%, because the celebrity is still on it. Consistent hashing solved the migration, not the skew. Two problems, two fixes. Most people conflate them. You will not.

</details>
