---
title: "Day 15 posts"
parent: "Day 15: caching and the cache-aside pattern"
grand_parent: "Week 3: caching and the CDN"
nav_order: 3
---

# Day 15 posts: LinkedIn and X

The scoreboard makes a good screenshot: a cache hit tens of thousands of times faster than a database read, and the database load doubling when hit rate slips from 90% to 80%. Swap in your own numbers and voice.

## LinkedIn

Day 15 of 60 days of system design. Week 3 is caching, and today I put a plain dictionary in front of a slow database and measured what it bought me.

The pattern is cache-aside, the one you should know cold. On a read, check the cache first. Hit? Return it. Miss? Go to the database once, store the answer, and every later read of that key is a hit. That is the whole thing.

First I timed a single read both ways:

    one database read (round trip):   2.5 ms
    one cache hit (dict lookup):       0.00008 ms

A cache hit came back about 30,000 times faster. Not twice as fast, not ten times. Orders of magnitude. The fastest read is the one that never leaves your process to reach the database at all.

Then I ran a realistic skewed workload, 5,000 reads where a few keys are red hot and most are cold:

    no cache:      5,000 database calls
    cache-aside:     431 database calls, 91% hit rate

The cache cut database load by about 12x, because with the repeats absorbed the database only ever sees the first touch of each distinct key.

Here is the part I will not forget. Hit rate is not linear. I measured the same traffic at a 90% hit rate and an 80% hit rate:

    90% hit rate:   454 database calls
    80% hit rate: 1,008 database calls

Dropping ten points of hit rate did not add ten percent of load. It roughly doubled it, because misses went from 1 in 10 to 1 in 5. That is why a cold cache after a restart, or one bad key, can tip a perfectly healthy database over on a sale day.

Reads love a cache. But a cache is a second copy of the truth, and now you own keeping two copies agreeing. More on that this week.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #caching #learninginpublic

## X thread

**1/**

Day 15 of 60 days of system design. I put a dictionary in front of a slow database today and timed one read both ways:

database read:  2.5 ms
cache hit:      0.00008 ms

About 30,000x faster. The fastest read is the one that never reaches the database.

**2/**

The pattern is cache-aside, and it is the one to know cold.

Read: check the cache. Hit, return it. Miss, go to the database once, store the answer, and every later read of that key is a hit.

Simple, and if the cache is empty or dead you still find the truth in the DB.

**3/**

Then a realistic skewed workload, 5,000 reads, a few hot keys and a long cold tail:

no cache:      5,000 DB calls
cache-aside:     431 DB calls (91% hit rate)

About 12x less load on the database. The cache absorbs all the repeats.

**4/**

The part that stuck with me. Hit rate is NOT linear. Same traffic:

90% hit rate:   454 DB calls
80% hit rate: 1,008 DB calls

Ten points of hit rate did not cost 10% more load. It DOUBLED it. Misses went from 1 in 10 to 1 in 5.

**5/**

That one fact explains a lot of outages. A cache restarts empty, the hit rate craters for a few seconds, and the database behind it suddenly takes 10x the traffic it was built for. On a sale day that is a bad afternoon.

**6/**

So for week 3, the rule I am starting with:

A cache is not free performance you sprinkle on top. It is a second copy of the truth. Add one when you have measured you need it, and always have an answer for "what happens when it is empty or down."

Code: github.com/anurag629/system-design-60-days
