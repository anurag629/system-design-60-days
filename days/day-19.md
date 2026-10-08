---
title: "Day 19: Redis internals and pipelining"
parent: "Week 3: caching and the CDN"
nav_order: 5
has_children: true
---

# Day 19
## Redis internals and pipelining, or why one round trip beats a thousand 🔁

Today's one idea: a Redis command is almost free. A GET or a SET is a lookup in a hash table, well under a microsecond of real work. So when Redis feels slow, it is almost never Redis doing the thinking. It is the round trip, your request travelling to the server and the reply travelling back, paid once for every single command. Pipelining is the fix, and it is not a Redis trick, it is Day 2's batching lesson wearing a Redis costume. Once you see that the round trip is the whole bill, two famous facts stop being trivia and start making sense: why Redis is single threaded, and why it bothers to ship hashes and sorted sets instead of just GET and SET.

Yesterday you watched one hot key melt a single shard. Today you go one level down, into the server itself, and measure the thing that decides its speed on your own laptop.

---

## Before you start ⏪

You need three earlier days warm in your head. Day 1, where you measured that a network round trip costs far more than any bit of local work. Day 2, where batching turned many small calls into one and the time collapsed. Day 6, where you ran a real server on 127.0.0.1 with sockets. Today stitches all three together: a tiny socket server, a round trip you can time, and batching that pays it less often. You do not need to have installed Redis. We build a small one so you can see inside it.

---

## Words you will meet today 📖

A round trip is one request out to the server and one reply back. Over a network it is the dominant cost of a small operation, because the work at each end is tiny next to the time spent in flight and waiting.

A request-response protocol is the shape Redis speaks: you send a command, you wait for its reply, then you send the next. Simple and strict. That strictness is exactly what makes naive clients slow, because the waiting is serial.

Pipelining is sending many commands in one write without waiting for each reply, then reading all the replies together. N commands now cost N divided by your batch size in round trips, instead of N.

An event loop is the single thread at the heart of Redis. It watches many connections at once and processes whatever is ready, one command at a time, never blocking on any one client.

I/O multiplexing is the operating system call (epoll on Linux, kqueue on macOS and BSD) that lets that one thread watch thousands of sockets and wake only for the ones with data. It is how one thread serves a crowd.

A multi-key command, like MGET, HGETALL or ZRANGE, does in one command what would otherwise be many. It is pipelining baked into the server: one round trip, many values.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Redis pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/), the official docs. The spine of today. It explains the request-response round trip, then shows pipelining collapsing it. Read the whole page, it is short and it is exactly our lab in words.
- [Redis benchmark](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/benchmarks/), also official. Skim to the "Using pipelining" and "Pitfalls" sections. The real numbers are here: about 180,000 SET per second without pipelining, and over 1.5 million with a pipeline of 16. It says plainly that Redis throughput is limited by the network well before the CPU, and that Redis favours fast CPUs with large caches, not many cores. That one page justifies the whole day.
- [Redis data types](https://redis.io/docs/latest/develop/data-types/). A quick tour of strings, hashes, lists, sets and sorted sets. Read it with one question in mind: which of these lets me do in one command what I would otherwise do in ten.

Watch, after the lab:
- [Why and How Is Single-Threaded Redis Fast](https://www.youtube.com/watch?v=h30k7YixrMo) by Arpit Bhayani, Redis Internals. The clearest explanation of how one thread serves thousands of connections with an event loop.
- [Implementing Command Pipelining](https://www.youtube.com/watch?v=2q7RuEb9z-M), also Arpit Bhayani. Pipelining from the inside, the same thing you build today.

### The round trip is the whole bill (14 min)

Picture ordering groceries from your kirana shop over the phone. You call, you say "one kilo atta", he says "done", you hang up. Then you call again, "half kilo sugar", "done", hang up. Twenty items, twenty phone calls, and each call is mostly the ringing and the hello, not the writing down. The man is fast. The phone call is slow. If your list has a hundred items you will spend your whole evening dialling.

That is a Redis client doing one command at a time, and it is exactly what the request-response protocol forces if you are not careful. Send GET, wait for the reply, send the next GET. The waiting is the cost. In the lab you will measure a single GET taking around twenty microseconds end to end on loopback, which is the fastest possible network, your own machine talking to itself with no real network at all. The actual dictionary lookup inside the server is a fraction of a microsecond. So of those twenty microseconds, almost all of it is the round trip, and loopback is the best case. Put a real datacenter network between client and server and the round trip jumps to half a millisecond or more, while the lookup stays a fraction of a microsecond. The ratio only gets more lopsided.

This is Day 1 again, stated as a rule you will now feel in your fingers: for a small operation over a network, the time is the round trip, not the work. Any design that pays one round trip per item will be slow no matter how fast the server is, because the server was never the slow part.

### Pipelining: say the whole list in one breath (14 min)

Now send the kirana list on WhatsApp. One message, twenty items. He reads it, packs everything, and sends back one message with the total. One round trip for the lot. The packing work did not change, you simply stopped paying for the phone call twenty times.

That is pipelining. The client writes many commands into the socket in one go, without waiting between them, and then reads all the replies together. The server was built for this: it reads whatever the socket hands it, often many commands in a single read, processes them in order, and writes the replies back, often in a single write. Nothing about the server got faster. You just stopped making it wait for you, and stopped waiting for it, after every command.

In the lab you send the same 50,000 GETs, first one at a time, then in batches. At a batch of 100 the round trips drop from 50,000 to 500, and the throughput jumps by roughly twenty times. Then you sweep the batch size and watch something important: the throughput climbs steeply at first, then flattens. The flattening is the lesson. Once the round trip is spread thin enough across a big batch, it stops being the bottleneck, and what is left is the server's own tiny per-command work: parse, look up, serialise the reply, copy bytes. You have finally made Redis CPU bound, and it took a batch of several hundred to get there. That plateau is the single most honest picture of where a cache's time goes.

One caution you will meet in the drills: pipelining batches the network, nothing more. It is not a transaction. The commands run in order and you get every reply, but there is no all-or-nothing. If you need that, you reach for MULTI and EXEC, which is a different tool.

### Why one thread is enough, and why hashes exist (12 min)

Here is the fact that confuses everyone the first time: Redis runs your commands on a single thread. On an eight core box, seven cores sit idle as far as command execution goes. People hear this and assume it must be a bottleneck. It is usually the opposite.

Think about what you just measured. Each command is microseconds of CPU, and the real wall is the network round trip and the cost of moving bytes in and out. If the CPU work is already a sliver, adding threads does not help, because the thread was never the thing you were waiting on. Worse, the moment two threads touch the same data structure you need locks, and locks bring contention, cache bouncing between cores, and a pile of subtle bugs. A single thread owning all the data needs none of that. Every command is atomic for free, because nothing else is running. The model is dead simple, and simple is fast. Notice the little server you build today never takes a single lock, and it does not need one. That is a railway counter with one very quick clerk: the queue flies because he never stops to coordinate with anyone. Put eight clerks on one register and they spend the day arguing over who writes next.

The one thread stays busy by not blocking. An event loop, built on epoll or kqueue, watches thousands of connections and only wakes for the ones with data ready. So one thread can serve a huge crowd, as long as no single command hogs it. That caveat is the whole danger: a command like a huge sorted-set range or a fat Lua script runs on that one thread and makes everyone else wait, which is why big O matters more in Redis than almost anywhere else. When one instance truly saturates its core, the answer is not threads inside it, it is more instances with the keys sharded across them. That is what Redis Cluster does.

And this is where the rich data types come in. A hash, a sorted set, a list: each one lets the server do in a single command what you would otherwise stitch together from many round trips. A user's session is one HSET and one HGETALL, not fifteen GETs. A leaderboard is one ZADD to write a score and one ZREVRANGE to read the top ten, sorted on the server, not a thousand GETs and a sort in your app. It is the same batching idea as pipelining, except the batching is designed into the command instead of assembled by the client. In the lab you will see one MGET of 100 keys beat 100 separate GETs by around fifty times, and now you know exactly why: it is 1 round trip against 100.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-19-drills.md`](../notes/day-19-drills.md).

D1. A Redis GET costs about 1 microsecond of CPU, but a round trip from your app server to Redis in the same datacenter is about 0.5 ms. A page needs 100 GETs. How long does it take one at a time? How long pipelined into a single round trip? What does the gap tell you about where the time lives?

D2. In the lab the throughput went from about 49,000 ops per second at a batch of 1, to about 1.1 million at a batch of 100, to about 1.6 million at a batch of 500, and then it flattened. Why does it climb steeply at first, and what is the bottleneck once it stops climbing?

D3. A colleague says: Redis is single threaded, so on our eight core box it wastes seven cores, let us move to a multi-threaded store for eight times the throughput. Where is the hole in that reasoning? When would the single thread actually be your wall, and what do you do then?

D4. You pipeline SET a 1 and SET b 2 in one batch, and the connection drops right after the server applied SET a. What state are you in? What does pipelining guarantee, and what does it not guarantee that a MULTI/EXEC transaction would?

D5. A user's cart is stored as 20 separate keys, cart:u1:item1 through cart:u1:item20, so reading the cart is 20 GETs. How does a hash (HSET and HGETALL) change the round-trip count? Give one more example where a rich structure collapses many round trips into one, and name the risk of leaning on one giant key.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-19-redis/pipelining.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-19-redis/pipelining.py).

It is a real, tiny, single-threaded key-value server on 127.0.0.1 with an OS-assigned port, speaking a simple text protocol over a socket: SET, GET, and MGET. One thread, one connection, one dictionary, no locks. Part 1 fetches 50,000 keys one at a time and measures the throughput the round trip pins you to. Part 2 pipelines the same 50,000 keys at a sweep of batch sizes and measures the speedup. Part 3 shows single threading and rich commands with one MGET against a hundred GETs.

Standard library only, a few seconds to run, and it cleans up its socket and leaves no files behind.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. 50,000 GETs, one at a time, send one and wait for the reply before the next. Roughly how many ops per second?
- P2. Pipelining at a batch of 100. For 50,000 ops, how many round trips is that?
- P3. The headline. Pipelined throughput at a batch of 100 divided by the one-at-a-time throughput. How many times faster?
- P4. Pipelined throughput at a batch of 100, in ops per second.

P3 is the one to feel in your gut first. Write a number. Most people say 2 or 3, because they are still picturing the server doing the work. The server is not the point.

### Fill in the TODOs

1. TODO 1 is one full round trip: send one command, wait for its one reply. This is the unit of cost in Part 1.
2. TODO 2 is the throughput, ops divided by seconds. The headline number of Part 1.
3. TODO 3 is the pipeline: send a whole batch in one write, then read all the replies together. This one function is the entire idea of Part 2.
4. TODO 4 is the speedup, pipelined throughput over one-at-a-time throughput. The headline of the day.

```bash
cd labs/day-19-redis
python3 pipelining.py
```

### What you're going to discover

Part 1 is the setup. A single GET comes out around twenty microseconds on loopback, and the throughput is a few tens of thousands of ops per second. Sit with how slow that is for a dictionary lookup, and remember the lookup itself is a fraction of a microsecond. You are watching the round trip, not the work.

Part 2 is the payoff. At a batch of 100 the throughput is roughly twenty times higher, for the identical 50,000 ops, because the round trips fell from 50,000 to 500. Then the sweep shows the curve climbing and flattening. The flat top is where the round trip is finally cheap enough that the server's own per-op work is all that is left. That is the moment Redis becomes CPU bound, and it tells you why pushing the batch size higher and higher stops helping.

Part 3 is the why. One MGET of 100 keys beats 100 separate GETs by around fifty times, the same batching win from the server side. And the whole server ran on one thread with no locks, which is the point about single threading made concrete: when each op is microseconds, one thread is not a limit, it is a simplification.

### Traps ⚠️

- If your one-at-a-time number is wildly erratic, something is adding latency to each round trip. The lab sets TCP_NODELAY on both sockets on purpose, to switch off Nagle's algorithm, which otherwise batches tiny writes and can stall a ping-pong workload by tens of milliseconds. Do not remove it and then wonder why the numbers went strange.
- The pipelined throughput wobbles run to run, and the plateau might sit anywhere from one to two million ops per second depending on your machine. That is fine. The lesson is the shape, a steep climb then a flat top, and the roughly twenty times gap at a batch of 100. Trust the contrast, not the third digit.
- Do not read the Part 3 MGET win as "MGET is a faster command". It is not faster per key. It is one round trip instead of a hundred. Same lesson, wearing the server's clothes.
- This is a toy. A real Redis has RESP, persistence, eviction, replication and far more. We stripped it to the one organ that explains its speed. Do not ship this.

### Deliverable

[`labs/day-19-redis/RESULTS.md`](../labs/day-19-redis/RESULTS.md) has a skeleton. Paste the output, and write one line: pipelining at a batch of 100 was how many times faster than one at a time, and what actually changed to make it so?

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise: "I asked a tiny key-value server for 50,000 keys. One at a time: 49,000 per second. Pipelined: 1.1 million per second, about 23 times faster, for the exact same work. The server never got busier. I just stopped waiting for a reply after every command." The batch-size sweep, climbing then flattening, is the screenshot.

Example posts are on the [Day 19 posts](../shares/day-19-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the pipelining speedup you measured at a batch of 100, and one thing you still cannot explain.

Day 20 is the CDN and cache invalidation: the same caching idea pushed all the way out to the edge, near the user, plus TTLs, purges and the stale-while-revalidate trick. Today you learned why one round trip beats a thousand inside the datacenter. Tomorrow you cut the round trip to the datacenter out of the picture entirely for the things that can live at the edge.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. One at a time: 100 times (0.5 ms round trip plus 1 microsecond of work) is about 100 times 0.501 ms, roughly 50 ms. Pipelined into one round trip: one 0.5 ms round trip plus 100 microseconds of total work, about 0.6 ms. That is roughly an 80 times speedup, and the work (100 microseconds in total) is a rounding error next to the round trips (50 ms). The time lives in the waiting, not the computing. This is the lab as a back-of-envelope, and it is why a page that does a hundred sequential cache reads feels slow even though the cache is instant.

D2. It climbs steeply because while the round trip dominates, cutting the number of round trips cuts the time almost proportionally: doubling the batch roughly halves the trips, so throughput roughly scales with batch size. It flattens once the round trip is spread so thin across a big batch that it is no longer the bottleneck. What remains is the server's own per-command work: parsing, the dictionary lookup, serialising the reply, copying bytes through the socket. At the plateau you are CPU and serialisation bound, which is the regime the single thread actually lives in. Pushing the batch higher past that point buys almost nothing and costs memory for bigger buffers and latency, because the first reply now waits for the whole batch to be sent.

D3. The hole is assuming the workload is CPU bound. It is not. The per-op CPU is microseconds and the wall is the network round trip and serialisation, so seven idle cores would not have helped, and a multi-threaded store would have added locking overhead for no real gain while trading a simple correct model for a complex one. The single thread becomes your wall only when one instance genuinely saturates its core, which happens with expensive commands (wide sorted-set ranges, big Lua scripts, large values) or very high throughput on one shard. The fix then is not threads inside one instance, it is more instances: run several Redis processes and shard the keys across them, which is exactly what Redis Cluster does, and what the docs mean by launching several instances to use several cores.

D4. After the drop, a is set and b is not. Pipelining batched the network trips and nothing more. It guarantees that commands on one connection execute in the order you sent them, and that you receive every reply, but it does not make the batch atomic: there is no all-or-nothing and no rollback, and a command from another client on another connection can land in between. If you need a and b to apply together or not at all, you want MULTI and EXEC, a transaction that queues the commands and runs them as one atomic unit with no other client interleaved. Pipelining is about speed, MULTI is about atomicity, and you can pipeline a MULTI/EXEC block to get both.

D5. A hash stores all 20 items under one key as fields, so HGETALL cart:u1 reads the whole cart in one command and one round trip instead of 20. That is 20 trips down to 1. Another example is a leaderboard: keeping each score as its own key forces many GETs and a sort in your app, while a sorted set lets you ZADD a score and ZREVRANGE the top ten, sorted on the server, in one round trip. The risk is the hot key and the big command: pour everything into one giant hash or sorted set and that single key lives on one shard (Day 18's celebrity problem), and O(n) commands like HGETALL or a wide range on a huge structure can block the single thread for everyone. Keep rich structures bounded.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-19-redis/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-19-redis/solution.py).

TODO 1, one full round trip, send one command and wait for its one reply:

```python
client.send(cmd)
return client.read_line()
```

TODO 2, the throughput of Part 1, ops over seconds:

```python
throughput = n / elapsed
```

TODO 3, the pipeline, the whole idea in two lines, send the batch in one write and read all the replies together:

```python
client.send(b"".join(batch))
return client.read_lines(len(batch))
```

TODO 4, the headline speedup, pipelined over one-at-a-time:

```python
speedup = pipe_through / one_throughput
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, loopback, 50,000 ops.

```
==============================================================================
Part 1: N = 50,000 GETs, ONE AT A TIME. Each op is a full round trip.
==============================================================================
  ops:                       50,000
  round trips:               50,000   (one per op)
  total time:               1022.8 ms
  throughput:                48,886 ops/sec
  time per round trip:        20.5 us
  The server work per op is a dict lookup, well under a microsecond.
  Almost all of that per-op time is the round trip: send, wait, recv.
  You are not CPU bound here. You are latency bound.

==============================================================================
Part 2: PIPELINING. Send M commands in one write, read M replies.
==============================================================================
   batch M  round trips        ops/sec   vs one-at-a-time
         1       50,000         46,564              1.0x
         2       25,000         95,244              1.9x
         5       10,000        214,183              4.4x
        10        5,000        355,566              7.3x
        50        1,000        874,585             17.9x
       100          500      1,136,593             23.2x
       500          100      1,595,306             32.6x
      1000           50      1,675,215             34.3x

  At M = 100: 500 round trips instead of 50,000, and the
  throughput is 23.2x the one-at-a-time rate. Same server, same
  ops, same dict. The ONLY thing that changed is how many times you
  stopped to wait for a reply. Notice the climb flattens at the top:
  once the round trip is amortised away, the server's own per-op cost
  is all that is left, and that cost is tiny.

==============================================================================
Part 3: why single threaded, and how rich commands save round trips.
==============================================================================
  fetch 100 keys, 200 times over:
    100 single GETs each time:     20,000 round trips     389.2 ms
    one MGET of 100 keys each:         200 round trips       6.8 ms
    the one rich command is 57.6x faster, for the same data

  Single threaded, on purpose. Each op is a handful of microseconds of
  CPU, so the bottleneck is the network and (de)serialisation, not the
  core. One thread means no locks, no contention, no race conditions,
  and a simple mental model. This whole server never took a lock.

  Rich data structures (hashes, sorted sets, lists) and multi-key
  commands (MGET, HSET, ZADD) are the same lesson as pipelining, baked
  into the server: do in ONE command and ONE round trip what would
  otherwise be many. A leaderboard ZADD, a session HSET, an MGET of a
  user's keys. The round trip was always the expensive part.

==============================================================================
Scoreboard
==============================================================================
  P1 one-at-a-time ops/sec           you =     45,000   actual =     48,886        close enough
  P2 pipelined round trips @100      you =        500   actual =        500        close enough
  P3 pipeline speedup @100           you =         20   actual =         23 x       close enough
  P4 pipelined ops/sec @100          you =  1,000,000   actual =  1,136,593        close enough

==============================================================================
The number to carry
==============================================================================
  The same 50,000 GETs. One at a time: 48,886 ops/sec. Pipelined
  at a batch of 100: 1,136,593 ops/sec, about 23x faster, from
  50,000 round trips down to 500. The server never got busier.
  You just stopped waiting for a reply after every single command.
  Round trips, not server CPU, were the wall the whole time. That is
  also why Redis is single threaded and loves one rich command over
  a hundred small ones.
```

Part 1 sets the trap you fall into by accident. A GET is a hash-table lookup, a fraction of a microsecond, yet one round trip took about twenty microseconds and the whole 50,000 ran at under 50,000 per second. Every bit of that gap is the round trip, send and wait and receive, and this is loopback, the kindest network there is. On a real datacenter network the per-op time would be dominated even harder by the trip.

Part 2 is the day. The same 50,000 ops, pipelined at a batch of 100, ran about 23 times faster, because the round trips dropped from 50,000 to 500. The sweep is the part to stare at: throughput climbs almost in step with the batch size while round trips are the bottleneck, then flattens near one and a half to one and three-quarter million as the round trip stops mattering and the server's own tiny per-op work becomes the limit. That flat top is Redis finally running CPU bound, and it is why a batch of several hundred is plenty and more buys little.

Part 3 closes the loop. One MGET of 100 keys beat 100 single GETs by about 57 times, the identical batching win moved into the command itself. And every number here came off a server running on one thread with not a single lock, which is the honest answer to why Redis is single threaded: when each command is microseconds, one thread is not the bottleneck, it is the thing that keeps the whole design simple and correct.

The one line to carry out of today: round trips, not server CPU, are the wall for a cache, and both pipelining and rich commands win the same way, by paying that wall fewer times.

</details>
