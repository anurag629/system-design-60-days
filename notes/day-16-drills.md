---
title: "Day 16 drills"
parent: "Day 16: eviction and the working set"
grand_parent: "Week 3: caching and the CDN"
nav_order: 2
---

# Day 16 drills

Written on paper first. Eviction, the working set, the knee, and why the miss rate is the number that bites.

D1 (a cache fronts a database and takes 10,000 reads per second at a 90% hit rate: reads per second reaching the database now, then after the hit rate slips to 80%, and the factor by which database load changed):

D2 (a Zipf workload where 1% of the keys serve about half the reads: the hit rate you expect from a cache that holds 1% of the keys, and why growing the cache from 1% to 2% does not get you to a full hit rate):

D3 (capacity 3, access order put A, put B, put C, get A, put D: which key does LRU evict on the put D, which key does FIFO evict, and why do they differ):

D4 (a one-pass scan reads a million distinct keys once each through an LRU cache that holds 10,000: the hit rate on the scan, what happens to the hot set that was resident before the scan, and what real databases do about it):

D5 (a workload with no hot set, every key equally likely, and a cache sized at 10% of the keyspace: the hit rate you can expect, and whether adding the cache is worth it):
