---
title: "Day 19 posts"
parent: "Day 19: Redis internals and pipelining"
grand_parent: "Week 3: caching and the CDN"
nav_order: 3
---

# Day 19 posts: LinkedIn and X

The scoreboard makes a good screenshot: one-at-a-time throughput next to pipelined throughput, and the batch-size sweep climbing then flattening. Swap in your own numbers and voice.

## LinkedIn

Day 19 of 60 days of system design. Today I stopped guessing why Redis is fast and measured the one thing that actually decides it.

I wrote a tiny single-threaded key-value server on localhost, GET and SET over a socket, and then asked it for 50,000 keys two different ways.

First, one at a time. Send a command, wait for the reply, send the next.

    one at a time:   48,886 ops/sec   (50,000 round trips)

Then with pipelining. Batch the commands, send a hundred in one write, read a hundred replies together.

    pipelined (M=100):  1,136,593 ops/sec   (500 round trips)

About 23 times faster. Same server, same dict, same 50,000 ops. The server never got busier. The only thing that changed was how many times I stopped to wait for a reply.

That is the whole lesson. A GET is a dict lookup, well under a microsecond of CPU. The expensive part was never the work, it was the round trip: your bytes going to the server and back. One at a time, I paid that round trip 50,000 times. Pipelined, I paid it 500 times.

Two things fell out of this that I used to just repeat without understanding:

Why Redis is single threaded. Each op is so cheap that the bottleneck is the network and serialization, not the CPU. One thread means no locks, no contention, a simple model, and it is plenty. My toy server never took a single lock.

Why Redis ships hashes, sorted sets and multi-key commands. I fetched 100 keys with 100 GETs, then with one MGET. The single rich command was about 58 times faster, because it is the same batching idea baked into the server. A leaderboard ZADD, a session HSET, an MGET of a user's keys: one command, one round trip, instead of many.

Round trips, not server CPU, were the wall the whole time.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #redis #caching #learninginpublic

## X thread

**1/**

I wrote a tiny single-threaded key-value server today and asked it for 50,000 keys two ways.

one at a time:      48,886 ops/sec
pipelined (M=100):   1,136,593 ops/sec

23x faster. Same server, same ops. Day 19 of 60 days of system design.

**2/**

A GET is a dict lookup, under a microsecond of CPU. So where did the time go one at a time?

The round trip. Send a command, WAIT for the reply, send the next. I paid that wait 50,000 times.

I was never CPU bound. I was latency bound.

**3/**

Pipelining fixes it. Send 100 commands in one write, read 100 replies together. Now 50,000 ops cost 500 round trips, not 50,000.

I swept the batch size and watched throughput climb, then flatten once the round trip was amortised away.

**4/**

This is why Redis is single threaded.

Each op is microseconds. The bottleneck is network + serialization, not the core. One thread = no locks, no contention, a simple model, and it is enough. My server never took a lock.

**5/**

And why Redis has hashes, sorted sets, MGET, HSET, ZADD.

I read 100 keys with 100 GETs, then with one MGET. The rich command was ~58x faster. Same batching idea, baked into the server.

**6/**

The one line to carry:

Round trips, not server CPU, were the wall the whole time. Pipelining and rich commands both win by paying that wall fewer times.

Code: github.com/anurag629/system-design-60-days
