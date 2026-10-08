---
title: "Day 15: caching and the cache-aside pattern"
parent: "Week 3: caching and the CDN"
nav_order: 1
has_children: true
---

# Day 15
## Caching and the cache-aside pattern, or the fastest read is the one that never reaches the database ⚡

Today's one idea: some data is read far more often than it changes, so instead of asking the database for it every time, you keep a copy somewhere fast and cheap and read that instead. That copy is a cache, and the single most important pattern for using one is cache-aside: check the cache, and only on a miss do you bother the database, storing the answer on the way back so the next read is free. Get this one pattern into your bones and most of caching follows.

Last week you spent five days making the database itself fast, with the right engine, the right index, the right shard key. Today you learn the move that beats all of them when it applies, which is not touching the database at all. You will bolt a cache in front of a slow source on your own machine and watch the read latency fall off a cliff.

---

## Before you start ⏪

You need Week 2 in your head, especially the idea that a database read is not free. It is a round trip: across a socket, into the engine, down a B-tree or across a few LSM runs, and back. That is milliseconds on a good day. A cache turns the common read into a memory lookup, which is sub-microsecond. The whole week is about spending a little memory and a lot of care to avoid those round trips. Day 2's comfort with simple Python and SQLite is all you need for the lab.

---

## Words you will meet today 📖

A cache is a fast, cheap copy of data whose real home is somewhere slower. Your CPU caches RAM, RAM caches disk, Redis caches the database, the CDN caches your server. Same trick at every layer.

A cache hit is a read the cache could answer by itself. A cache miss is one it could not, so you fall back to the slow source. The fraction of reads that are hits is the hit rate, and it is the number that decides whether a cache is worth anything.

Cache-aside, also called lazy loading, is the pattern where the application talks to both the cache and the database. On a read it checks the cache, and on a miss it reads the database and populates the cache itself. The cache sits beside the database and knows nothing about it.

The source of truth is the place that holds the real, authoritative data, the database here. A cache is only ever a copy, which is why a cache can go stale and the database cannot.

Staleness is how out of date a cached copy is allowed to get. Every cache trades a little staleness for a lot of speed, and the art is deciding how much staleness each piece of data can tolerate.

Eviction is throwing something out of the cache to make room, because a cache is almost always smaller than the data behind it. That is tomorrow's topic; today the cache is unbounded so we can study the pattern on its own.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Caching challenges and strategies](https://aws.amazon.com/builders-library/caching-challenges-and-strategies/) from the AWS Builders' Library. Written by people who run caches at enormous scale, and honest about the ways a cache bites back. The spine of this week.
- [Cache-Aside pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside) in the Microsoft Azure Architecture Center. Short, precise, and exactly today's pattern, including the write and invalidation side you will meet in the drills.
- [Caching strategies and how to choose the right one](https://codeahoy.com/2017/08/11/caching-strategies-and-how-to-choose-the-right-one/) on CodeAhoy. The clearest side-by-side of cache-aside, read-through, write-through and write-back, with the staleness each one risks. Read this before Part 3 of the lab.

Watch, after the lab:
- [Cache Systems Every Developer Should Know](https://www.youtube.com/watch?v=dGAgxozNWFE) by ByteByteGo, about 6 minutes. A tight tour of the patterns, good to lock in the vocabulary.
- Optional, for the distributed and consistency angle: [What are Distributed Caches and how do they manage data consistency?](https://www.youtube.com/watch?v=U3RkDLtS7uY) by Gaurav Sen, about 13 minutes. Takes today's idea out to many machines, which is where staleness gets interesting.

### Why cache at all: the fastest read never reaches the database (15 min)

Picture the records room in an old government office. Every time a clerk needs a file, someone walks into the stacks, finds it, walks back. If the same ten files are requested all day, that walk is madness. So the clerk keeps those ten on the desk. Now the common request is answered without moving. That is a cache, and the walk you avoided is the database round trip.

Here is why it matters so much, and you will measure it today. A database read in the lab takes about 2.5 milliseconds, a realistic figure for a round trip. A cache hit, a plain dictionary lookup in memory, takes about 0.00008 milliseconds. That is not twice as fast or ten times as fast. It is roughly thirty thousand times faster. When something is that much faster, the game is simply to do it as often as you can.

But the latency per read, nice as it is, is not even the main prize. The real prize is load. Every read the cache answers is a read the database never sees. If ninety percent of reads hit the cache, your database does a tenth of the work, which means it can be a tenth of the size, or survive ten times the traffic. That is the lever caching gives you, and it is why a cache sits in front of almost every busy database in the world.

The catch, and the reason this week is dangerous, is that a cache is a second copy of the truth. The moment you keep a copy, you own the problem of keeping it in step with the original. Add a cache only when you have measured that you need one, cache the thing that is actually read a lot and changes a little, and always have an answer for what happens when the cache is empty or down.

### Cache-aside: the pattern to know cold (15 min)

Cache-aside is five lines, and you should be able to write them in your sleep.

On a read, the application does this. Look in the cache. If the key is there, that is a hit, return it, done. If it is not there, that is a miss: go to the database, get the value, put it in the cache, and return it. The next read of that same key is now a hit. The cache fills itself lazily, one miss at a time, which is why it is also called lazy loading.

The name cache-aside comes from where the cache sits. It is off to the side. The application talks to the cache and the database directly, and the cache has no idea the database exists. Your code is the one orchestrating the two. That sounds like a downside, more code to write, but it buys the property that makes cache-aside the default everywhere: if the cache is empty, or slow, or completely dead, your reads still work. They just fall through to the database and are slower. A cache-aside system degrades; it does not break.

Now the write side, which the drills push on. When the underlying row changes, you must deal with the stale copy in the cache. The safe move is to delete the cached key, not to overwrite it with the new value. Deleting is self-healing: the next read misses and repopulates from the database, which is the source of truth. Overwriting looks tidier but it races. Two updates landing close together, or an update interleaved with a slow miss that is still fetching the old value, can leave the older value sitting in the cache with no one to correct it. Invalidate, do not update, is the rule to remember.

Cache-aside has two honest weaknesses. The first read of every key is always a miss, so a cold cache is slow until it warms up. And there is a small window after a write where a concurrent reader can repopulate a stale value. Both have fixes, and both are later this week. Today you just need the pattern itself, solid.

### The other three patterns, and the staleness each risks (8 min)

Cache-aside is the one to know cold, but name the other three so you can place them in an interview.

Read-through is cache-aside with the miss logic moved into the cache layer instead of your application. On a miss, the cache itself loads from the database and fills itself. Same behaviour, same staleness risk, just a tidier application. The trade is that you depend on a cache library or service that knows how to reach your database.

Write-through sends writes through the cache to the database synchronously. You write to the cache, it writes to the database, and only then does the write return. The cache and the database move together, so a reader hitting the cache never sees a value older than the last completed write. The cost is slower writes, because every write now waits for two hops, and you may cache things no one ever reads again.

Write-back, also called write-behind, is the fast and frightening one. A write lands in the cache, the cache acknowledges immediately, and the cache flushes to the database later, in batches. Writes feel instant and the database takes far fewer, bigger writes. But now the database is behind the cache, and if the cache dies before it flushes, those writes are gone. You reach for write-back only where losing a little recent data is acceptable, like counters or metrics, never for money.

The lab prints all four side by side with the staleness each risks. Cache-aside is the default because it is simple and survives a dead cache. Write-back is the fastest for writes and the one most likely to lose your data.

### Hit rate is the whole game, and it is non-linear (12 min)

This is the part to carry into every system design conversation you ever have. The load a cache lets through to the database is set by the miss rate, which is one minus the hit rate. So the database sees a fraction (1 minus hit rate) of the reads. Simple enough. The trap is that people treat this as linear and it is not, not where it matters.

Take a service doing 100,000 reads a second. At a 90 percent hit rate, 10 percent miss, so 10,000 reads a second reach the database. Now the hit rate slips to 80 percent. Misses are 20 percent, so 20,000 reads a second reach the database. You lost ten points of hit rate and the database load did not go up by ten percent, it doubled. Slip from 80 to 70 and it goes from 20,000 to 30,000, a 1.5x jump. Near the top, every single point of hit rate is precious, because the miss rate is small and a few points is a huge fraction of it.

This is where caches cause outages, and it is the insight that has saved many a Diwali sale. Think of a Big Billion Day spike. Your cache is humming along at 95 percent and the database is comfortable at a twentieth of the traffic. Then the cache process restarts and comes back empty, or a very hot key expires all at once, or your cache gets so full it starts evicting things people still want. The hit rate drops for a few seconds, and because the relationship is multiplicative, the database suddenly takes five or ten times its normal load. A database sized for the steady state falls over, queries time out, clients retry, and the retries pile on even more load. The cache did not just stop helping; its failure took down a healthy database.

So the number to be able to compute in your head: given a hit rate, what fraction of reads reach the database, and what happens to that fraction if the hit rate drops ten points. You will measure the 90-to-80 doubling yourself in Part 3.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-15-drills.md`](../notes/day-15-drills.md).

D1. Walk the cache-aside read path for a hit and for a miss, naming every step. Then: when the underlying row is updated, cache-aside can either delete the cached entry or overwrite it with the new value. Which is safer, and what race does the other one risk?

D2. A service does 100,000 reads a second through a cache. How many reads a second reach the database at a 90 percent hit rate, at 80 percent, and at 50 percent? Is database load linear in hit rate? Why does losing ten points near the top cost so much more than losing ten points near the bottom?

D3. A source read is 20 ms and a cache hit is 0.1 ms. What is the average read latency at a 90 percent hit rate, and at a 20 percent hit rate? Give a one-line rule of thumb for when a cache is actually worth adding.

D4. Pick a cache pattern, a rough TTL, and the staleness you accept for each: a user profile page read constantly and edited rarely; a live cricket score read by millions and changing every ball; a "last seen at" timestamp written on every heartbeat and read almost never.

D5. Your cache serves 100,000 reads a second at a 95 percent hit rate, so the database sees about 5,000 a second and is comfortable. The cache restarts and comes back empty. What read rate hits the database for the next few seconds, what is likely to happen to it, and what does that say about treating a cache as optional?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-15-cache-aside/cache_aside.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-15-cache-aside/cache_aside.py).

It is in three parts. Part 1 builds the cache-aside read path over a deliberately slow source, a small SQLite table behind a few-millisecond delay that stands in for a database round trip, and times a single cache hit against a single source read. Part 2 runs a realistic skewed (Zipf) workload of 5,000 reads, once with no cache and once with cache-aside, and measures the hit rate, the database calls, and the average latency both ways. Part 3 measures the Day 2 lesson: database load at a 90 percent hit rate versus an 80 percent hit rate.

Standard library only, the slow source is an in-memory SQLite database, and it runs in well under a minute and leaves no files behind.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. A cache hit is a memory lookup, a source read is a database round trip. Predict the floor: at least how many times faster is a hit? The rule of thumb for "worth caching" is about 100x.
- P2. Run the skewed workload through cache-aside. What fraction of the 5,000 reads are hits, as a percentage?
- P3. With no cache every read hits the database. With cache-aside, how many times fewer database calls do you make?
- P4. The Day 2 number. Database load at an 80 percent hit rate divided by load at a 90 percent hit rate. How many times more?

P4 is the one to feel in your gut before you run it. Most people say "a bit more, maybe ten or twenty percent." Write down your number.

### Fill in the TODOs

1. TODO 1 is the cache miss, the heart of cache-aside: fetch the value from the slow source and store it in the cache so the next read is a hit.
2. TODO 2 is the hit rate, hits over total reads. The number that decides everything.
3. TODO 3 is the load reduction, no-cache database calls over cache-aside database calls. The headline of Part 2.
4. TODO 4 is the doubling, the 80 percent call count over the 90 percent call count. The headline of Part 3.

```bash
cd labs/day-15-cache-aside
python3 cache_aside.py
```

### What you're going to discover

Part 1 is the motivation, made concrete. The same read, answered from a dictionary instead of the database, comes back tens of thousands of times faster. Not a little faster. Orders of magnitude. That gap is the whole reason caches exist.

Part 2 is the payoff. The skewed workload, where a few keys are red hot and most are cold, hits about a 91 percent rate with a plain unbounded cache, because once each distinct key has been seen once it hits forever. The database went from 5,000 calls to about 430, roughly a 12x cut, and the average read got much faster. Source load collapsed to the miss rate, exactly as advertised.

Part 3 is the one that should change how you think. Dropping the hit rate from 90 percent to 80 percent did not add ten percent of database load. It roughly doubled it, because misses went from one in ten to one in five. Ten points of hit rate near the top is worth double, not a tenth.

### Traps ⚠️

- If your Part 1 speedup looks small, check you are timing a real cache hit and not accidentally calling the source. A hit must never reach the database; the whole point is that it does not.
- The hit rate in Part 2 depends on how many distinct keys show up in the workload, not on the skew alone. With an unbounded cache every key misses exactly once, so the hit rate is set by distinct keys over total reads. Tomorrow, when the cache is too small to hold everything, this gets much more interesting.
- The exact speedup in Part 1 wobbles run to run, because you are comparing a millisecond-scale sleep to a nanosecond-scale lookup. Do not chase the third digit. It is tens of thousands of times either way, which is all the lesson needs.
- Part 3 counts database calls, not time. The doubling is in the call count, the load on the database. That is the thing that falls over on a sale day, not the latency of a single read.

### Deliverable

[`labs/day-15-cache-aside/RESULTS.md`](../labs/day-15-cache-aside/RESULTS.md) has a skeleton. Paste the output, and write one line: how much faster was a cache hit than a source read, and why did dropping the hit rate from 90 to 80 percent roughly double the database load?

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise, and there are two good ones. The first: "I put a dictionary in front of a slow database and reads got thirty thousand times faster." The second, sharper one: "dropping a cache hit rate from 90 percent to 80 percent does not add ten percent of database load, it doubles it, and that is how caches cause outages." The scoreboard, the 90-to-80 call counts side by side, is the screenshot.

Example posts are on the [Day 15 posts](../shares/day-15-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the hit rate and the 90-to-80 load multiplier you measured, and one thing you still cannot explain.

Day 16 is eviction and the working set. Today the cache was unbounded, so every key stayed forever and the hit rate was easy. Tomorrow the cache is smaller than the data, so you have to decide what to throw out, and you will plot the hit rate against cache size, the curve that quietly decides your Redis bill. Today you learned the pattern. Tomorrow you learn what happens when the cache runs out of room.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Hit path: the read checks the cache (a dict), finds the key, returns the value, and never touches the database. Miss path: the key is not in the cache, so the read goes to the database once, gets the value, stores it in the cache, and returns it, so the next read of that key is a hit. On an update to the underlying row, the safer move is to delete the cached entry, not overwrite it. Overwriting races: two concurrent updates, or an update interleaved with a slow miss that is still fetching the old value, can leave the older value stuck in the cache with nothing to correct it. Deleting is self-healing, because the next read misses and repopulates from the database, which is the source of truth. The cost of delete is one extra miss; the cost of a bad overwrite is silent stale data. Invalidate, do not update.

D2. At 100,000 reads a second: 90 percent hit means 10 percent miss, so 10,000 a second reach the database. 80 percent means 20,000 a second. 50 percent means 50,000 a second. Database load is driven by the miss rate, one minus the hit rate. The jump from 90 to 80 doubles the misses (10 percent to 20 percent), while 50 to 40 takes misses from 50 to 60 percent, only a 1.2x jump. The same ten-point drop multiplies load far more near the top, because up there the miss rate is tiny and ten points is a big fraction of it. Every point of hit rate near 95 to 99 percent is worth defending hard.

D3. Average latency is hit_rate times hit_cost plus miss_rate times miss_cost. A miss pays the source, about 20 ms; a hit about 0.1 ms. At 90 percent: 0.9 times 0.1 plus 0.1 times 20 equals about 2.1 ms. At 20 percent: 0.2 times 0.1 plus 0.8 times 20 equals about 16 ms. Rule of thumb: a cache helps in proportion to the hit rate times how much faster a hit is than a miss. It is worth adding when the data is read far more than it changes (so you can reach a high hit rate) and the source is much slower than the cache. At a 20 percent hit rate you still pay the source four reads out of five, so the cache barely helps and may not earn its complexity.

D4. Profile page, read constantly and edited rarely: cache-aside with a TTL of minutes, and invalidate on edit; you accept that an edit might show to others a few seconds late. Live cricket score, read by millions and changing every ball: cache hard with a very short TTL of a second or two (or push updates), and accept readers being a second behind, because the alternative melts the database; this is read-heavy with unavoidable staleness, so you make the staleness window tiny rather than refuse to cache. The "last seen at" timestamp, written on every heartbeat and read almost never: this is write-heavy and read-light, the opposite shape, so a read cache buys nothing; batch or write-back the writes and accept that presence can lag a few seconds and can be lost if the buffer dies, which is fine for a last-seen dot. The pattern follows the read/write ratio and how much staleness the feature tolerates.

D5. At 95 percent the database sees about 5,000 reads a second. When the cache comes back empty, every read is a miss until it refills, so for the next few seconds the database sees close to the full 100,000 a second, roughly 20x its normal load. A database sized for 5,000 a second will not absorb 100,000: latency climbs, connections pile up, queries time out, and the timeouts make clients retry, which piles on even more load. That is how a cache failure takes down a healthy database. It means a cache is not optional decoration; if losing it would take the system down, it is a load-bearing wall, and you must plan for the empty-cache case: warm it before taking traffic, refill gradually, cap the concurrent misses, and size the database for some multiple of its steady load. Days 16 and 17 are exactly these defenses.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-15-cache-aside/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-15-cache-aside/solution.py).

TODO 1, the cache miss, the heart of cache-aside: fetch from the slow source and store it so the next read is a hit:

```python
value = source.get(key)
cache[key] = value
```

TODO 2, the hit rate, the number that decides everything:

```python
hit_rate_pct = stats["hits"] / total * 100
```

TODO 3, the load reduction, the headline of Part 2:

```python
load_reduction = nocache_calls / cache_calls
```

TODO 4, the doubling, the headline of Part 3:

```python
load_multiplier = calls_80 / calls_90
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 5,000 reads over 500 keys.

```
==============================================================================
Part 1: cache-aside, the mechanism. Hit the dict, miss the database.
==============================================================================
  reading keys 10, 20, 10, 30, 20, 10:
    key 10  -> MISS (go to source)
    key 20  -> MISS (go to source)
    key 10  -> HIT (from cache)
    key 30  -> MISS (go to source)
    key 20  -> HIT (from cache)
    key 10  -> HIT (from cache)
  6 reads, 3 hits, 3 misses, 3 database calls
  The 3 repeats of already-seen keys never touched the database.

  one source read (database round trip):    2.5054 ms
  one cache hit  (dict lookup):           0.000080 ms
  a cache hit is about 31,429x faster than a source read
  Not 2x, not 10x. Orders of magnitude, well past the 100x that makes
  a cache worth adding. The fastest read never leaves your process.

==============================================================================
Part 2: a skewed (Zipf) workload. No cache vs cache-aside, measured.
==============================================================================
  workload: 5,000 reads over 500 keys, Zipf skew s=1.1

  no cache:
    database calls:         5,000   (every read)
    total time:             12617 ms
    average read:           2.523 ms
  cache-aside:
    hit rate:                91.4 %
    database calls:           431   (only the misses)
    total time:              1100 ms
    average read:           0.220 ms

  the cache cut database calls by 11.6x and the average
  read got 11x faster. Source load collapsed to the
  miss rate: with an unbounded cache each key misses once, so the
  database only ever sees the first touch of each distinct key.

==============================================================================
Part 3: hit rate is non-linear. 90 to 80 does not cost 10 percent.
==============================================================================
  same 5,000 reads, two different hit rates:
    at 90% hit rate:     454 database calls  (about 10% of reads)
    at 80% hit rate:   1,008 database calls  (about 20% of reads)
  dropping 10 points of hit rate multiplied database load by 2.22x
  Ten points of hit rate near the top is not a 10% change in database
  load, it is roughly double. This is why one bad cache key or a cold
  cache after a restart can tip a healthy database over on a sale day.

  The four cache patterns, and the staleness each one risks:
  --------------------------------------------------------------------------
  pattern       who writes the DB         main staleness risk               
  --------------------------------------------------------------------------
  cache-aside   app, on its own           cache holds old value till TTL/evict
  read-through  cache library, on miss    same as cache-aside, hidden in lib
  write-through cache, synchronously      little: cache and DB move together
  write-back    cache, later in batch     DB lags cache; data lost if cache dies
  --------------------------------------------------------------------------
  Cache-aside is the default: simple, and a cache miss or a dead cache
  still finds the truth in the database. Write-back is the fastest for
  writes and the scariest, because the database is behind the cache.

==============================================================================
Scoreboard
==============================================================================
  P1 hit vs source speedup       you >=     100  actual =    31,429 x  PASS, 314x past the floor
  P2 cache-aside hit rate        you =     90.0  actual =      91.4 %       close enough
  P3 source load reduction       you =     10.0  actual =      11.6 x       close enough
  P4 load mult 90->80            you =      2.0  actual =       2.2 x       close enough

==============================================================================
The number to carry
==============================================================================
  A cache hit came back about 31,429x faster than a database read,
  so a 91% hit rate cut database calls by roughly 12x. But hit
  rate is non-linear: going from 90% to 80% did not add a tenth of
  the load, it multiplied it by 2.2x, because misses went from
  1 in 10 to 1 in 5. The fastest read is the one that never reaches
  the database, and a few points of hit rate is the whole game.
```

Part 1 is the motivation. A single read answered from the dictionary came back about 31,000 times faster than the same read from the database. The exact figure wobbles run to run, because it is a millisecond sleep against a nanosecond lookup, but it is always tens of thousands. That gap, not any clever indexing, is why the first question about a slow read is often "can we cache it" rather than "can we speed up the query."

Part 2 is the cache doing its job. The skewed workload hit about 91 percent, so the database saw 431 calls instead of 5,000, a bit under 12x less load, and the average read dropped from 2.5 ms to 0.22 ms. With an unbounded cache every distinct key misses exactly once and hits forever after, so the database only ever sees the first touch of each key. Source load collapsed to the miss rate, which is the sentence to remember.

Part 3 is the lesson that outlives the lab. The same 5,000 reads at a 90 percent hit rate sent 454 calls to the database; at 80 percent they sent 1,008. Ten points of hit rate did not cost ten percent more load, it multiplied the load by 2.2x, because the misses went from one in ten to one in five. This is why a cold cache after a restart, or a single very hot key expiring, can double or worse the load on a database that was perfectly healthy a second ago. Defend the top of your hit-rate curve.

The one line to carry out of today: the fastest read is the one that never reaches the database, cache-aside is how you arrange that, and hit rate is the number that decides whether your cache is a shield or a liability.

</details>
