---
title: "Day 17 posts"
parent: "Day 17: the thundering herd"
grand_parent: "Week 3: caching and the CDN"
nav_order: 3
---

# Day 17 posts: LinkedIn and X

The scoreboard is the screenshot: 100 source calls in the naive herd, 1 with a lock, 0 with early refresh. Swap in your own numbers and your own voice.

## LinkedIn

Day 17 of 60 days of system design. Today I reproduced the thundering herd on my own laptop, the thing that quietly takes down more databases than any slow query.

The setup is simple. One popular key sits in a cache with a short TTL. It expires. At that exact instant a crowd of readers all look, all miss, and all run the slow recompute together. I fired 100 concurrent readers at one cold key and counted how many times they hit the slow source:

    naive cache-aside:   100 calls in one burst

One hundred. The whole crowd. One key going cold for a fraction of a second turned 100 reads into 100 trips to the database. This is IRCTC at 10 AM when tatkal opens, in miniature.

Then two fixes.

Fix one, a per-key lock (single flight). Only the first reader rebuilds the value; everyone else waits on the lock and then reads what that reader just wrote.

    per-key lock:   1 call, but 99 readers waited for it

Source load solved. The catch is right there in the numbers: all 99 other readers still blocked for one recompute. Fine when the recompute is quick, dangerous when it hangs, because now the whole crowd hangs with it.

Fix two, early recomputation. Refresh the value a little before it expires, in the background, triggered by a single reader, while everyone else keeps reading the still-fresh copy.

    early refresh:   0 calls at the herd, 0 readers blocked

The key is never cold when the crowd arrives, so there is no herd to tame. Nobody waits, nothing hits the source in the burst.

The lesson I am taking: a cache does not fail when it is empty. It fails when a popular key expires under load, and the cache you added for protection becomes the thing that lines the whole crowd up to hit your database at once.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #caching #redis #learninginpublic

## X thread

**1/**

I fired 100 requests at ONE cache key the instant it expired. Counted how many hit the slow database behind it.

Answer: 100.

That is the thundering herd. Day 17 of 60 days of system design.

**2/**

Naive cache-aside has no protection. The key goes cold for a fraction of a second, every concurrent reader misses at once, and every one of them runs the slow recompute.

One expired key, N trips to the DB. This is IRCTC tatkal at 10 AM in miniature.

**3/**

Fix one: a per-key lock (single flight).

Only the first reader rebuilds the value. The rest wait on the lock, then read what it wrote.

    source calls: 100 -> 1

Huge win. But 99 readers still blocked waiting for that one recompute. If it hangs, they all hang.

**4/**

Fix two: early recomputation.

Refresh the value a little BEFORE it expires, in the background, triggered by one reader, while everyone else keeps reading the still-fresh copy.

    calls at the herd: 0
    readers blocked:   0

The key is never cold, so there is no herd.

**5/**

The real lesson:

A cache does not fail when it is empty. It fails when a popular key expires under heavy load, and the cache you added for protection becomes the thing that marches the whole crowd into your database at the same instant.

**6/**

Three strategies, same key, same crowd of 100:

naive:        100 DB calls
single flight:  1 call, 99 waiters
early refresh:  0 calls, 0 waiters

I got to watch all three happen on my own machine.

Code: github.com/anurag629/system-design-60-days
