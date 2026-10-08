---
title: "Day 18: hot keys and the celebrity problem"
parent: "Week 3: caching and the CDN"
nav_order: 4
has_children: true
---

# Day 18
## Hot keys, and why you cannot shard your way out of one viral key 🔥

Today's one idea: sharding spreads your keys, but it cannot spread a single key. When one key gets a huge slice of all the reads (a viral post, a cricketer's tweet, a product on sale), that key lives on exactly one cache node, and that node drowns while the others sit half idle. Adding more nodes does not help, because no amount of sharding ever splits one key. You fix a hot key by replicating it to every node or by absorbing it in a tiny cache on the app server itself.

On Day 13 you met the celebrity key and watched it make one data shard hot. You also saw me wave it away with "the hot key needs its own fix." Today is that fix. And notice the difference: Day 13 was about where your data lives and how much of it moves when you reshard. Today is about read traffic, piling onto one cache node, because of one key.

---

## Before you start ⏪

You need two things fresh. First, Day 13: routing by hash(key) % N, and the fact that one popular key cannot be split across shards. Second, this week's cache tier: a read-heavy service puts a sharded cache (think Redis or Memcached, several nodes) in front of the database, and the client picks a node by hashing the key. Today we point a celebrity read workload at exactly that tier and watch what happens.

If "Zipf" is a new word, do not worry, the first teaching section explains it with a cricket example. The lab is pure standard library Python, no database, no network, so Day 2's comfort is plenty.

---

## Words you will meet today 📖

A hot key is a single key that takes a disproportionate share of the traffic. Not a hot shard full of many busy keys, one key, all by itself, bigger than thousands of others combined.

The celebrity problem is the everyday name for it. On a social app, most users have a handful of followers and a celebrity has fifty million. One read for a normal user and one read for the celebrity are the same cost to serve, but the celebrity's key gets asked for millions of times more often. The popularity of keys is wildly uneven, and the system has to cope with the uneven part.

A Zipf or power-law workload is the shape of that unevenness. Rank the keys by popularity, and the request rate falls off steeply: the most popular key gets roughly twice the traffic of the second, three times the third, and so on. A small head of keys carries most of the load, and a long tail carries the rest. Real read workloads look like this far more often than they look flat.

A sharded cache tier is several cache nodes, with each key routed to one node by hash(key) % N. It gives you more total memory and more total throughput than a single node, which is exactly why people reach for it. It is also where the hot key does its damage.

The hottest node's share is today's headline number: of all the reads hitting the tier, what fraction lands on the single busiest node. A perfectly even tier of N nodes would put 100/N percent on each. The gap between the busiest node and that even share is the skew you are fighting.

Key replication, sometimes called key salting, is the first fix. You copy the hot key to every node (key#0, key#1, up to key#N), and a read picks one copy at random, so the celebrity's reads spread across the whole tier instead of hammering one node.

A local or in-process cache (an L1 cache) is the second fix. Each app server keeps a tiny cache of its own, just the few hottest keys, with a short time to live. Reads for the celebrity are served right there on the app server and never reach the shared tier at all.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [DDIA chapter 6](https://dataintensive.net/), partitioning, the short section called "Skewed Workloads and Relieving Hot Spots." Kleppmann states the problem exactly, hash partitioning spreads keys but not a single hot key, and then gives the standard fix of adding a random suffix to split that one key across partitions. That suffix trick is exactly the replication you will measure in Part 2. If you read one thing, read this.
- [Hot shards are a pain, but why do they occur](https://arpitbhayani.me/notes/hot-shards-are-a-pain-but-why-do-they-occur) by Arpit Bhayani. His list of causes is broader than our single-key case, but the framing is the one you want in your head: the cluster has plenty of capacity overall and one node is still drowning. That is always the smell of a hot key or a hot shard.
- [The Justin Bieber problem](https://queryncontext.beehiiv.com/p/the-justin-bieber-problem) by Harsh Kathiriya. The classic celebrity-key story, one account so popular it overloads the one shard that owns it, told plainly, with the key-salting fix worked through. A nice concrete companion to the lab.

Watch, after the lab:
- [They enabled Postgres partitioning and their backend fell apart](https://www.youtube.com/watch?v=YPorP8BsF_c) by Hussein Nasser, about 32 minutes. A real production story at the database layer: a team partitioned by a key, the traffic was skewed, and one partition became the bottleneck that took the backend down. It is the same failure as today, splitting the data did not split the hot traffic, and it is worth seeing it bite real engineers.

### Where hot keys come from (14 min)

Picture the last over of a close T20 match. A hundred million people are refreshing the same scorecard. On your backend, that scorecard is one cache key. Every other key in the system, every user profile, every old post, is getting a trickle of reads, and this one key is getting a firehose. That is a hot key, and the match is not special. Replace it with a viral tweet, a flash-sale product on Big Billion Day, a breaking-news article, a celebrity's profile. Same shape every time.

The shape has a name, Zipf. If you rank keys by how often they are read, the curve drops off a cliff. The number one key might be a fifth of all your reads on its own. The top ten might be close to half. And then a very long tail of keys that are each read almost never. In today's lab the single hottest key is 19.6% of a million reads. One key out of a hundred thousand, and it is a fifth of all the work.

Here is why that is a system design problem and not just a fun fact. Your cache is sharded. You have, say, eight nodes, and you route each key to a node with hash(key) % 8. For the hundred thousand distinct keys, that hashing is beautifully even, roughly the same number of keys on each node. But routing is per key, and the celebrity is one key. It hashes to one node, and every single one of its millions of reads goes to that one node. The hashing spread your keys perfectly and did nothing at all for your traffic.

### Why you cannot shard your way out (14 min)

When a node is overloaded, the instinct drilled into all of us is to add more nodes. More nodes, more capacity, problem solved. For a hot key, this instinct is wrong, and I want you to feel exactly why before the lab shows it to you.

Add nodes and the celebrity key still hashes to exactly one of them. That node still receives 100% of the celebrity's reads. What changed? Only the other keys got spread thinner, so the fair share per node dropped. With eight nodes the fair share is 12.5%. With 256 nodes it is 0.39%. But the celebrity's node cannot go below the celebrity's own share, about 20%, no matter how many nodes you add. The floor is fixed by one key.

So watch what happens to the imbalance. At eight nodes the hottest node is roughly twice the fair share. At 256 nodes it is fifty times the fair share. The absolute load on the hot node barely moved, but relative to where it should be, it got far worse. You spent money on 248 extra nodes and made the skew uglier. This is the single most important thing to carry out of today: a hot key is immune to sharding, because sharding is a tool for spreading keys and a hot key is one key.

There is a cousin of this on the write side. A single counter that everyone increments, the match's live view count, is a hot key for writes. Sharding does not help it either, for the same reason. The write-side fix is to split the counter into N sub-counters and sum them on read, which is the same idea as replication wearing different clothes. We stay on the read side today, but the logic is identical.

### The two fixes: replicate it, or absorb it (12 min)

If you cannot spread one key by hashing, you have to make more than one place that can answer for it. Two ways.

The first is replication. You detect the hot keys, there are only a handful, and you store each one on every node, as key#0, key#1, and so on. Now a read for the celebrity picks a copy at random, so those reads land on all nodes evenly. In the lab this drops the hottest node from 26.7% to 14.2%, basically flat. The cost is on the other side: every write to that key now has to update every copy, and every invalidation has to reach every node, with a short window where different nodes hold different versions. That is why you replicate only the hottest, most read-heavy, rarely-changing keys. A viral post is perfect for it. A hot counter is not.

The second is a local cache. Each app server keeps a tiny in-process cache, just the few hottest keys, with a short time to live, say one or two seconds. A read for the celebrity is served right there, in the app server's own memory, and never travels to the shared tier. In the lab a local cache of the top ten keys absorbs 48.5% of all reads before they reach the tier at all. The cost is staleness: a read can be up to the TTL out of date. For a like count or a viral post, two seconds of staleness is invisible, so you take it happily. The hotter your head of keys, the more this absorbs, and it is often the cheapest fix of all, one dict per server.

Both fixes start the same way, with detection. You sample the live traffic, find the top talkers by request count, and treat only those few specially. Everything else keeps using the plain sharded tier, which was never the problem.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-18-drills.md`](../notes/day-18-drills.md).

D1. A sharded cache has 8 nodes and routes reads by hash(key) % 8. The celebrity key is 20% of all reads. What is the lowest the hottest node's share can go, and why does moving to 64 nodes not change that floor?

D2. The celebrity is still 20%, and the even share is 100/N. Work out the ratio of hottest to even at 8, 64 and 256 nodes. In one line, say why adding nodes makes the imbalance relatively worse, not better.

D3. You replicate the hot key to all N nodes so its reads spread. What does this now cost you on every write to that key, and on every invalidation of it? How would you decide which keys earn replication?

D4. Instead you put a tiny in-process cache with a 2-second TTL in front of the shared tier. How stale can a read of the celebrity key be, why is that usually fine for a viral post, and what decides how much traffic this fix absorbs?

D5. Day 13 used consistent hashing to kill resharding churn. Does consistent hashing fix a single hot key? Then pick a fix for each of these: a viral read-heavy tweet, a single write-heavy counter, a product page during a flash sale.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-18-hot-keys/hot_keys.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-18-hot-keys/hot_keys.py).

It is in three parts. Part 1 sends a million celebrity (Zipf) reads at a sharded cache of 8 nodes, routes each read by hash(key) % N, and prints the load on every node, so you see one node at 26.7% while the rest sit near 12.5%. It then grows the tier to 64 and 256 nodes and shows the hottest node barely budges while the imbalance ratio explodes. Part 2 is the fix: replicate the top hot keys to every node and re-measure, then absorb them in a local cache and re-measure. Part 3 is the scoreboard and the one line to carry.

Standard library only, no files, no sockets, no threads, and it runs in a couple of seconds.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The single hottest celebrity key's share of all reads, as a percent. One key out of 100,000.
- P2. Before any fix, routing across 8 nodes, the hottest node's share of all reads. (An even tier would give each node 12.5%.)
- P3. After replicating the top hot keys to all 8 nodes, the hottest node's share. How close to 12.5% does it get?
- P4. With a local cache holding the top hot keys, what percent of all reads gets absorbed before reaching the shared tier?

P2 is the one to feel in your gut first. Most people guess something near the even share plus a little. Write a number down before you run it.

### Fill in the TODOs

1. TODO 1 is the routing rule, hash(key) % N, the one line that pins a key to a single node.
2. TODO 2 is the headline metric, the hottest node's share of all reads.
3. TODO 3 is the replication fix: a replicated key lives everywhere, so a read picks any node.
4. TODO 4 is the local-cache test: is this key one of the hot few we hold in process?

```bash
cd labs/day-18-hot-keys
python3 hot_keys.py
```

### What you're going to discover

Part 1 is the shock. The distinct keys land evenly, within a few percent of each other, and then one node stands at 26.7% because the celebrity hashes to it. The per-node bar chart makes it obvious at a glance: seven ordinary bars and one that runs off the edge.

The adding-nodes table is the lesson that sticks. The hottest node goes 26.7%, 22.1%, 19.9% as you grow from 8 to 64 to 256 nodes, hardly moving, while the even share collapses from 12.5% to 0.39%. The ratio of hottest to even climbs from 2.1x to 50.8x. More hardware, worse skew.

Part 2 is the relief. Replication flattens the tier to a 14.2% hottest node, near the even 12.5%. The local cache soaks up 48.5% of all reads on the app servers, so the shared tier sees a lighter and even load, its hottest node down at 8.1%. Two different tools, same goal, neither of them more sharding.

### Traps ⚠️

- Do not read the adding-nodes table as "adding nodes helped a little." The hottest number does drift down, but it is converging on the celebrity's own share and can never cross it. The honest reading is the ratio column, and that gets worse.
- Replication is not free, and the lab does not charge you for it. In Part 2 we only measure reads. In production, replicating a key means fanning out every write and every invalidation to all N nodes. Replicate read-heavy, rarely-changing keys, not hot counters.
- The local cache's absorbed percentage depends entirely on how concentrated your hot set is. A hotter head absorbs more. If your workload were flat, a local cache of ten keys would absorb almost nothing, and you would not bother. Measure the head before you reach for it.

### Deliverable

[`labs/day-18-hot-keys/RESULTS.md`](../labs/day-18-hot-keys/RESULTS.md) has a skeleton. Paste the output, and write one line: what was the hottest node's share before and after the fix, and why did adding nodes do nothing for it?

---

## Block 4: write (30 min) 📣

Your angle today is the counterintuitive one: "One key was a fifth of all my reads, and it melted one cache node. I tried the obvious fix, more nodes, and it made the imbalance worse, 2x to 50x. The real fix was not sharding at all." The per-node bar chart, seven short bars and one long one, is the screenshot.

Example posts are on the [Day 18 posts](../shares/day-18-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the hottest node's share before and after the fix, and one thing you still cannot explain.

Day 19 is Redis internals: single threaded on purpose, the rich data structures, how it survives a restart, and pipelining, which turns out to be last week's batching lesson in a Redis costume. Today you learned how one key can bully a whole tier. Tomorrow you get to know the node itself.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The hottest node holds the celebrity, so it carries at least the celebrity's 20%, plus its fair share of the other 80%. Move to 64 nodes and the celebrity still hashes to exactly one node, so that node still carries at least 20%. The floor is the celebrity's own share, and it does not move because one key is never split across nodes. Adding nodes only shrinks the contribution of the other keys to that node, so the hottest node creeps down toward 20% from above but can never go below it.

D2. The even share is 100/N, so the ratio of the floor (20%) to the even share is 20 / (100/N) = N/5. At 8 nodes that is 1.6x, at 64 nodes 12.8x, at 256 nodes 51.2x. (The lab measures a bit higher because the hottest node also catches its share of the tail, but the trend is identical.) The floor is fixed by one key while the even share keeps shrinking, so the gap between them grows without bound. More nodes make the imbalance relatively worse, not better.

D3. Every write to the key now has to update all N copies, so a single logical write becomes N writes, and every invalidation has to reach all N nodes, with a short window in which different nodes can serve different versions. So replication is cheap for read-heavy keys that change rarely (a viral post, a profile) and expensive or unsafe for write-heavy keys. You decide which keys earn it by measuring: sample the traffic, rank keys by request count, and replicate only the few whose read volume dwarfs their write volume. It is a small set, usually a handful.

D4. A 2-second TTL means a read can be up to 2 seconds stale, since the app server serves its cached copy until the TTL expires and only then refetches. For a viral post, a like count or a scorecard, 2 seconds behind is invisible to the user, so the trade is easy to accept. How much it absorbs depends on how concentrated the hot set is: if the keys you hold locally are, say, half of all reads, the local cache absorbs about half (minus one refetch per key per TTL window per server). The hotter the head, the more it absorbs.

D5. Consistent hashing fixes resharding churn, it moves only about 1/(N+1) of keys when you add a node, but it does not fix a hot key: the celebrity still maps to exactly one point on the ring, so one node still melts. Consistent hashing is about where keys live and how little they move, not about splitting one key's traffic. For the three cases: a viral read-heavy tweet, replicate it to all nodes or hold it in a local cache, both fit because it is read-heavy and changes rarely; a single write-heavy counter, do not replicate (every write would fan out), instead split the counter into N sub-counters, increment a random one, and sum on read; a product page in a flash sale, a short-TTL local cache on each app server absorbs the read stampede, with replication of the product key if the shared tier is still hot.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-18-hot-keys/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-18-hot-keys/solution.py).

TODO 1, the routing rule that pins a key to one node:

```python
return h % n
```

TODO 2, the headline metric, the hottest node's share of all reads:

```python
return max(loads) / sum(loads) * 100
```

TODO 3, the replication fix, a replicated key lives everywhere so a read picks any node:

```python
return rng.randrange(n)
```

TODO 4, the local-cache test, is this one of the hot keys we hold in process:

```python
return key in hot_keys
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 100,000 keys, 1,000,000 reads, Zipf exponent 1.2.

```
==============================================================================
Part 1: the hot key melts one node. Route reads by hash(key) % N.
==============================================================================
  100,000 keys, 1,000,000 reads, Zipf workload (exponent 1.2).
  the single hottest key (the celebrity) alone is 19.6% of all reads.

  Sharded cache, 8 nodes. An even tier would give each node 12.5%.
    node 0:   64,803    6.5%  ###########
    node 1:   81,745    8.2%  #############
    node 2:  182,587   18.3%  ##############################
    node 3:  113,803   11.4%  ###################
    node 4:   67,205    6.7%  ###########
    node 5:  123,445   12.3%  ####################
    node 6:   99,600   10.0%  ################
    node 7:  266,812   26.7%  ############################################  <-- celebrity lives here

  hottest node = 26.7% of all reads, vs 12.5% if even.
  the distinct keys are spread evenly, but one key cannot be, so the
  celebrity's node carries its 19.6% on top of its fair share.

==============================================================================
Does adding nodes fix it? Grow the tier and re-measure the hottest node
==============================================================================
       8 nodes: hottest =  26.7%   even share = 12.50%   hottest is  2.1x the even share
      64 nodes: hottest =  22.1%   even share =  1.56%   hottest is 14.1x the even share
     256 nodes: hottest =  19.9%   even share =  0.39%   hottest is 50.8x the even share
  More nodes slice the OTHER keys thinner, so the even share keeps
  shrinking, but the celebrity's node cannot drop below that one key's
  share. The gap between hottest and even gets RELATIVELY worse, not
  better. You cannot shard your way out of a single hot key.

==============================================================================
Part 2: the fix. Replicate the hot keys, and absorb them locally.
==============================================================================
  Fix A: replicate the top 10 hot keys to all 8 nodes.
    node 0:  125,305   12.5%  #######################################
    node 1:  128,181   12.8%  ########################################
    node 2:  141,688   14.2%  ############################################
    node 3:  121,498   12.1%  ######################################
    node 4:  127,769   12.8%  ########################################
    node 5:  120,025   12.0%  #####################################
    node 6:  122,965   12.3%  ######################################
    node 7:  112,569   11.3%  ###################################
  hottest node = 14.2%  (was far higher; even is 12.5%)
  The hot keys' reads now land on every node, so the tier evens out.

  Fix B: a local cache on each app server holds the top 10 hot keys.
    reads absorbed locally (never hit the shared tier): 48.5%
    hottest shared node now carries 8.1% of all reads
  The celebrity's reads are soaked up in front of the tier, so the
  shared nodes see a lighter, even load. One cheap dict per server.

==============================================================================
Scoreboard
==============================================================================
  P1 celebrity key share             you =   15.0   actual =    19.6 %       close enough
  P2 baseline hottest node           you =   28.0   actual =    26.7 %       close enough
  P3 hottest after replicating       you =   13.0   actual =    14.2 %       close enough
  P4 reads absorbed locally          you =   45.0   actual =    48.5 %       close enough

==============================================================================
The number to carry
==============================================================================
  One viral key was 19.6% of all reads, and with plain
  hash(key) % N routing it pushed its node to 26.7% while the
  rest sat near the even 12.5%. Adding nodes never helped: one key
  cannot be split. Replicating the hot keys to every node brought the
  hottest node down to 14.2%, and a tiny local cache absorbed
  48.5% of all reads before they ever reached the shared tier.
  You do not shard a hot key. You replicate it or you absorb it.
```

Part 1 is the whole point. The hundred thousand distinct keys spread evenly across the eight nodes, within a few percent of each other, and then node 7 stands at 26.7% because the celebrity key hashes to it and dumps its 19.6% there on top of a normal share. Nothing is wrong with the hashing. The hashing did its job on keys and had no answer for traffic.

The adding-nodes table is the part worth screenshotting. Growing the tier from 8 to 256 nodes drops the hottest node from 26.7% only to 19.9%, because that is closing in on the celebrity's own 19.6% and physically cannot go lower. Meanwhile the even share falls to 0.39%, so the imbalance ratio climbs from 2.1x to 50.8x. You added 248 nodes and the skew got five times worse in relative terms. That is the sentence to remember: sharding spreads keys, and a hot key is one key.

Part 2 shows the two real fixes. Replicating the top ten keys to every node lets their reads land anywhere, and the tier flattens to a 14.2% hottest node, a whisker above the even 12.5%. The local cache is even blunter: holding the top ten keys in each app server's own memory absorbs 48.5% of all reads before they ever reach the shared tier, and the tier's hottest node drops to 8.1%. Replication spreads the hot key, the local cache hides it, and both leave the ordinary keys on the plain tier where they were never a problem.

The one line to carry out of today: you cannot shard your way out of a single hot key, you replicate it so every node can serve it, or you absorb it in a cache close to the reader.

</details>
