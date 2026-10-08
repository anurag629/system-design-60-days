---
title: "Day 18 posts"
parent: "Day 18: hot keys and the celebrity problem"
grand_parent: "Week 3: caching and the CDN"
nav_order: 3
---

# Day 18 posts: LinkedIn and X

The per-node bar chart is the screenshot: seven nodes near the even 12.5%, one node at 26.7% because the celebrity key lives there. Swap in your own numbers and voice.

## LinkedIn

Day 18 of 60 days of system design. Today I watched a single key take down one cache node while the other seven sat half idle, and then I learned why adding more nodes does nothing about it.

I sent 1,000,000 reads at a sharded cache of 8 nodes. The reads followed a celebrity (Zipf) pattern: a few keys are wildly popular, most are not. Routing is the normal thing every sharded cache does, hash(key) % 8 picks the node.

One key, the celebrity, was 19.6% of all reads on its own. Here is where those reads landed:

    node 0:  6.5%
    node 2: 18.3%
    node 7: 26.7%  <- the celebrity lives here
    (an even tier would put 12.5% on each)

The distinct keys spread perfectly evenly. The traffic did not, because one key cannot be split. It lives on exactly one node, and all of its reads go there.

Then the part that surprised me. I tried the obvious fix, add more nodes:

    8 nodes:   hottest 26.7%, that is 2.1x the even share
    64 nodes:  hottest 22.1%, that is 14.1x
    256 nodes: hottest 19.9%, that is 50.8x

More nodes slice the other keys thinner, so the fair share keeps shrinking, but the celebrity's node cannot drop below that one key's 19.6%. The imbalance gets relatively worse, not better. You cannot shard your way out of a single hot key.

What actually works is not sharding at all. Detect the hot keys and either replicate them to every node (any node can then serve the read, so they spread) or hold them in a tiny in-process cache on each app server. Replicating brought my hottest node down to 14.2%, basically even. The local cache absorbed 48.5% of all reads before they ever reached the shared tier.

You do not shard a hot key. You replicate it or you absorb it.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #caching #learninginpublic

## X thread

**1/**

I sent 1,000,000 reads at a sharded cache of 8 nodes today.

One key (a celebrity) was 19.6% of all reads. It melted one node:

node 7: 26.7%
the other nodes: near the even 12.5%

Day 18 of 60 days of system design.

**2/**

Why? Routing is hash(key) % N, like every sharded cache.

The distinct keys spread evenly. But one key cannot be split. It lives on exactly ONE node, so all of its reads pile onto that node while the rest sit idle.

**3/**

So I did the obvious thing: add more nodes.

8 nodes:   hottest 26.7%  (2.1x the even share)
64 nodes:  hottest 22.1%  (14.1x)
256 nodes: hottest 19.9%  (50.8x)

The hottest node will not drop below the celebrity's 19.6%. Adding nodes makes the imbalance RELATIVELY worse.

**4/**

The lesson: you cannot shard your way out of a single hot key.

More nodes only thins the other keys. The hot key is still one key on one node.

**5/**

What works is not sharding. Two fixes:

Replicate the hot keys to every node, any node serves the read. Hottest node fell to 14.2%, even.

Or a tiny in-process cache on each app server. It absorbed 48.5% of all reads before the shared tier ever saw them.

**6/**

You do not shard a hot key. You replicate it or you absorb it.

Code: github.com/anurag629/system-design-60-days
