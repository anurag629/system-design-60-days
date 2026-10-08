---
title: "Day 19 drills"
parent: "Day 19: Redis internals and pipelining"
grand_parent: "Week 3: caching and the CDN"
nav_order: 2
---

# Day 19 drills

Written on paper first. Round trips, pipelining, the single thread, and rich commands.

D1 (a Redis GET costs about 1 us of CPU, but a round trip from your app server to Redis in the same datacenter is about 0.5 ms. A page needs 100 GETs. How long one at a time, how long pipelined into one round trip, and what does the gap tell you about where the time lives):

D2 (in the lab, throughput went 48,886 ops/sec at M = 1, to about 1.1 million at M = 100, to about 1.6 million at M = 500, then flattened. Why does it climb steeply at first, and what is the bottleneck once it stops climbing):

D3 (a colleague says: Redis is single threaded, so on our 8-core box it wastes 7 cores, let us move to a multi-threaded store for 8x throughput. Where is the hole in that reasoning, when would the single thread actually be your wall, and what do you do then):

D4 (you pipeline SET a 1 and SET b 2 in one batch, and the connection drops after the server applied SET a. What state are you in? What does pipelining guarantee, and what does it NOT guarantee that a MULTI/EXEC transaction would):

D5 (a user's cart is stored as 20 separate keys cart:u1:item1 .. cart:u1:item20, so reading the cart is 20 GETs. How does a hash (HSET / HGETALL) change the round-trip count? Give one more example where a rich structure collapses many round trips into one, and name the risk of leaning on one giant key):
