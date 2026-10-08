---
title: "Day 13 drills"
parent: "Day 13: partitioning and sharding"
grand_parent: "Week 2: storage"
nav_order: 2
---

# Day 13 drills

Written on paper first. Hash vs range, the hot shard, and the cost of adding a server.

D1 (hash sharding, one key is 20% of traffic: the floor on the hottest shard's load, no matter how many shards you add, and why):

D2 (modulo resharding, 10 shards to 11, and 100 to 101: fraction of keys that must move, using the N/(N+1) rule):

D3 (consistent hashing, 10 shards to 11: fraction of keys that move, and where exactly they go):

D4 (partition users by id range when the oldest users are the biggest celebrities: what breaks, and does switching to hash sharding fully fix it):

D5 (consistent hashing with virtual nodes gives even key counts but one shard still sits at 40% because of a celebrity key: name two concrete fixes and the cost of each):
