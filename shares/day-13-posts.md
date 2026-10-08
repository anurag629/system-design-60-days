---
title: "Day 13 posts"
parent: "Day 13: partitioning and sharding"
grand_parent: "Week 2: storage"
nav_order: 3
---

# Day 13 posts: LinkedIn and X

The two screenshots that carry this day are the celebrity floor (hottest shard barely drops as you add shards) and the head to head: modulo moving 89% of keys, consistent hashing moving 12%. Swap in your own numbers and voice.

## LinkedIn

Day 13 of 60 days of system design. Today was sharding, and I finally measured two things I had only ever hand-waved about.

First, the hot shard. I split 100,000 keys across 8 shards with hash(key) % 8. The distinct keys landed almost perfectly even, about 12,000 per shard. So far so good. But the traffic was skewed, like real traffic always is, and one celebrity key was 19.6% of all requests on its own. That key sits on exactly one shard, and it cannot be split. So the hottest shard was at 26.7% while the others idled.

Then I asked the obvious question: does adding more shards fix this? I pushed it to 64 shards, then 256. The hottest shard dropped to 22%, then 19.9%, and stopped. It can never go below 19.6%, because one key lives on one shard no matter how big the cluster gets. More servers spread the ordinary keys thinner. They do nothing for the celebrity. That is the hot shard, and it is why "just add shards" is not an answer.

Second, the cost of adding a server. With plain modulo, going from 8 shards to 9 remapped 89% of the keys. At 64 to 65 it was 98.4%. In real life that is copying almost your entire dataset across the network to add one machine. Consistent hashing, the same 8 to 9 move, touched only 11.7% of the keys, and those keys only moved onto the new shard. About 1/(N+1), exactly as the theory promises.

One honest surprise: consistent hashing does not fix the hot key. The celebrity still melts whichever shard owns it. Consistent hashing solves the migration cost, not the skew. Those are two different problems with two different fixes.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #databases #learninginpublic

## X thread

**1/**

Sharding, measured instead of hand-waved. Day 13 of 60 days of system design.

Split 100,000 keys across 8 shards with hash % 8. Distinct keys spread perfectly even, ~12k each.

But traffic is skewed. One celebrity key was 19.6% of all requests. It lives on one shard. That shard runs hot.

**2/**

So I added shards. Surely that fixes it?

   8 shards  -> hottest 26.7%
  64 shards  -> hottest 22.1%
 256 shards  -> hottest 19.9%

It flatlines at 19.6%, the celebrity's own share. One key cannot be split. More servers do nothing for it. That is the hot shard.

**3/**

Now the resharding trap. Going from 8 shards to 9 with plain modulo:

89% of keys move.

At 64 -> 65 it is 98.4%. That is copying your whole dataset over the network to add one box. This is why modulo sharding is a trap.

**4/**

Fix: put the shards on a hash ring (consistent hashing). Same 8 -> 9 move:

11.7% of keys move. About 1/(N+1).

And they only move onto the new shard. Nobody else is disturbed. Weekend migration becomes a shrug.

**5/**

The catch I did not expect: consistent hashing does NOT fix the hot key. The celebrity still lands on one shard and melts it.

Consistent hashing fixes the migration cost. The skew is a separate fight: split the key, cache it, or give it its own shard.

Code: github.com/anurag629/system-design-60-days
