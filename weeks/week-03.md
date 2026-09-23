# Week 3: caching and the CDN, or how to be fast by being lazy 🚀

Days 15 to 21.

Caching is the most loved and most feared idea in system design. Loved because it is the single easiest way to make a slow thing fast. Feared because, as the old joke goes, there are only two hard problems in computer science: cache invalidation, naming things, and off-by-one errors. 😅

Here is the whole idea in one line. Some data is expensive to compute or fetch, and you read it far more often than it changes, so you keep a copy somewhere fast and cheap. That is a cache. Your RAM caches your disk. Redis caches your database. The CDN caches your server. Your browser caches the CDN. It is the same trick at every layer, all the way down.

The catch, and the reason this week is dangerous, is that a copy can go stale, and a cache that fails badly does not just get slow. It can take down the healthy database sitting behind it. Most of the big outages you read about have a cache somewhere in the story.

## What you will be able to do by Sunday

You can explain cache-aside, read-through, write-through and write-back and say which one you would pick for a given feature. You know what a thundering herd is and three ways to stop one. You can look at a cache hit rate of 90% and immediately tell me that dropping it to 80% does not add 10% load to the database, it doubles the load. That one insight has saved many a Diwali sale. 🪔

## The days 🗓️

Day 15: why cache, and the four patterns. Cache-aside is the default and you should know it cold. Lab: bolt a cache-aside layer onto last week's database and watch the read latency fall off a cliff.

Day 16: eviction and the working set. Your cache is smaller than your data, so what do you throw out? LRU, LFU, and the hit-rate-versus-size curve that decides your Redis bill. Lab: implement LRU yourself, then plot hit rate against cache size.

Day 17: the thundering herd, also called a cache stampede. One popular key expires, ten thousand requests all miss at the same instant, and they all hammer the database together. Think IRCTC at 10 AM when tatkal opens. 🚆 Lab: reproduce a stampede, then fix it with a lock and with early recomputation.

Day 18: hot keys and the celebrity problem. When Virat Kohli tweets, one key in one shard gets a million reads a second while the rest sit idle. Lab: send Zipf-distributed load and watch a single key melt one shard.

Day 19: Redis internals. Single threaded on purpose, rich data structures, and how it survives a restart. Also pipelining, which is last week's batching lesson wearing a Redis costume. Lab: benchmark simple ops and measure what pipelining buys you.

Day 20: the CDN and cache invalidation. TTLs, purges, and the lovely stale-while-revalidate trick that serves slightly old content instantly while quietly fetching fresh. Lab: read real cache headers and watch edge behaviour.

Day 21: caching design. You design something like a news feed or a rate limiter that leans on caching, timed, then a retro.

## Core resources for the week 📚

Read:
- Kleppmann, *DDIA*, the caching and derived-data sections.
- [AWS Builders' Library: caching challenges and strategies](https://aws.amazon.com/builders-library/caching-challenges-and-strategies/), written by people who run it at scale.
- Redis docs on data types and persistence, redis.io, short and practical.

Watch:
- [Hussein Nasser](https://www.youtube.com/@hnasr) on caching and Redis. He has felt this pain and it shows.

## What trips people up this week ⚠️

They treat caching as free performance you sprinkle on top. It is not free. Every cache is a second copy of the truth, and now you own the hard job of keeping two copies agreeing. Add a cache only when you have measured that you need one, cache the thing that is actually hot, and always, always have an answer for "what happens when the cache is empty or down." A cache you cannot survive losing is not a cache, it is a load-bearing wall you forgot you built.
