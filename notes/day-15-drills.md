---
title: "Day 15 drills"
parent: "Day 15: caching and the cache-aside pattern"
grand_parent: "Week 3: caching and the CDN"
nav_order: 2
---

# Day 15 drills

Written on paper first. Cache-aside, hit rate, the four patterns, and the danger of a cache that fails.

D1 (walk the cache-aside read path for a hit and a miss, naming every step. Then: when the underlying row is updated, cache-aside can either delete the cached entry or overwrite it with the new value. Which is safer, and what race does the other one risk):

D2 (a service does 100,000 reads/sec through a cache. How many reads/sec reach the database at a 90% hit rate, at an 80% hit rate, and at a 50% hit rate? Is database load linear in hit rate? Why does losing 10 points near the top cost so much more than losing 10 points near the bottom):

D3 (a source read is 20 ms, a cache hit is 0.1 ms. What is the average read latency at a 90% hit rate, and at a 20% hit rate? Give a one-line rule of thumb for when a cache is actually worth adding):

D4 (pick a cache pattern, a rough TTL, and the staleness you accept for each: a user profile page read constantly and edited rarely; a live cricket score read by millions and changing every ball; a 'last seen at' timestamp written on every heartbeat and read almost never):

D5 (your cache serves 100,000 reads/sec at a 95% hit rate, so the database sees about 5,000/sec and is comfortable. The cache process restarts and comes back empty. What read rate hits the database for the next few seconds, what is likely to happen to it, and what does this say about treating a cache as optional):
