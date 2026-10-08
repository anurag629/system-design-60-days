---
title: "Day 18 drills"
parent: "Day 18: hot keys and the celebrity problem"
grand_parent: "Week 3: caching and the CDN"
nav_order: 2
---

# Day 18 drills

Written on paper first. Hot keys, the celebrity, and why more nodes do not help.

D1 (a sharded cache, 8 nodes, reads routed by hash(key) % 8, and the celebrity key is 20% of all reads: what is the lowest the hottest node's share can go, and why does going to 64 nodes not move that floor):

D2 (celebrity still 20%, even share is 100/N: work out the hottest-vs-even ratio at 8, 64 and 256 nodes, and say in one line why adding nodes makes the imbalance relatively worse, not better):

D3 (you replicate the hot key to all N nodes so reads spread: what does this now cost you on every write and every invalidation of that key, and how would you decide which keys earn replication):

D4 (instead you put a tiny in-process cache with a 2-second TTL in front of the shared tier: how stale can a read of the celebrity key be, why is that usually fine for a viral post, and what decides how much traffic this absorbs):

D5 (Day 13 used consistent hashing to kill resharding churn: does consistent hashing fix a single hot key, and which fix would you pick for each of a viral read-heavy tweet, a single write-heavy counter, and a product page in a flash sale):
