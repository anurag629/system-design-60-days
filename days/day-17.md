---
title: "Day 17: the thundering herd"
parent: "Week 3: caching and the CDN"
nav_order: 3
has_children: true
---

# Day 17
## The thundering herd, or what happens the instant a popular key expires 🚆

Today's one idea: a cache does not fail when it is empty. It fails when one popular key expires while a crowd is reading it. For that fraction of a second the key is cold, every concurrent request misses together, and they all run the slow recompute at the same instant. The cache you added to protect the database becomes the thing that marches the whole crowd into it. That is the thundering herd, also called a cache stampede, and today you reproduce it on your own machine and then kill it two different ways.

Picture IRCTC at 10 AM when tatkal opens. For the rest of the day the booking page sits quietly in cache. At 10:00:00 the window opens, every phone in the country hits the same few pages in the same second, and whatever is behind that cache either holds or it does not. That is the whole lesson, scaled down to 100 threads and one key.

---

## Before you start ⏪

You need Day 15 and Day 16 in your head. Day 15 gave you cache-aside: check the cache, and on a miss, read the source and fill the cache. Day 16 gave you TTLs and eviction: a cached value does not live forever, it expires. Today lives in the exact moment one expires. If "cache-aside" and "TTL" are not yet reflexes, go back and skim them first, because the stampede is just those two ideas colliding under load.

The lab is pure Python threads, standard library only. No database, no Redis, no sockets. The slow source is a `time.sleep`, which is all a database query is from the caller's point of view: a wait. Day 6's comfort with threads is plenty.

---

## Words you will meet today 📖

A cache stampede, or thundering herd, is a burst of identical cache misses that all hit the slow source at once because a popular key expired or was evicted at the same moment a crowd was reading it. The dogpile effect is another name for the same thing.

A hot key is a single cache entry that takes a large share of the traffic. A product page during a Big Billion Day sale, a cricketer's profile the moment he walks out to bat, the tatkal booking page at 10 AM. The herd is dangerous precisely because it is one key, so no amount of sharding spreads the load.

Single flight, also called request coalescing, is the first fix: when many callers want the same missing key, let exactly one of them compute it and make the rest wait for that one result instead of each computing their own.

Early recomputation, or refresh-ahead, is the second fix: rebuild the value a little before it expires, in the background, so the cache is never actually cold when the crowd arrives.

Probabilistic early expiration (the XFetch trick) is early recomputation done with a dice roll, so that one request refreshes ahead of time and the rest keep reading the valid value, without the refresh itself turning into a smaller, earlier herd.

TTL jitter is spreading expiry times out with a little randomness, so a thousand keys that were all loaded together do not all expire together.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these:
- [Cache stampede](https://en.wikipedia.org/wiki/Cache_stampede) on Wikipedia. Short and unusually clear. It names the problem and lays out the same three fixes you will build: locking, external recomputation, and probabilistic early expiration. Read this one first, it is the map for the whole day.
- [AWS Builders' Library: caching challenges and strategies](https://aws.amazon.com/builders-library/caching-challenges-and-strategies/). Written by people who run caches at a scale where a stampede is a very bad afternoon. Look for the sections on request coalescing and on what happens when a cache node goes away.
- [`golang.org/x/sync/singleflight`](https://pkg.go.dev/golang.org/x/sync/singleflight). The single-flight idea as a tiny, battle-tested library that Go services actually ship. Read the package doc and the `Do` signature. It is Part 2 of your lab in production form, and seeing how small it is tells you something.

Optional, if you want the real mathematics behind Part 3:
- [Optimal probabilistic cache stampede prevention](https://cseweb.ucsd.edu/~avattani/papers/cache_stampede.pdf) by Vattani, Chierichetti and Lowenstein. This is the XFetch paper. The formula `now - delta * beta * ln(random()) >= expiry` comes from here. Four pages, and the first two are very readable.

Watch, after the lab:
- [Thundering herd problem and how not to do API retries](https://www.youtube.com/watch?v=8sTuCPh3s0s) by Arpit Bhayani, about 11 minutes. He comes at the herd from the retry side, which is the other common way to cause one. Good companion to the caching view you build today.

### What a stampede actually is (16 min)

Go back to cache-aside, the pattern from Day 15. A request comes in, you look in the cache, and if the value is there you return it. If it is not, you call the slow source, store the result, and return it. Ninety-nine times out of a hundred the value is there and the source never gets touched. That is the whole point of a cache.

Now watch the hundredth case closely, because there is a gap in it that most people never notice. A value has a TTL, say 60 seconds. At second 60 it expires. The very next request looks in the cache, finds nothing, and goes to the slow source. That source takes some time, call it 200 milliseconds, to compute the value and put it back. For those 200 milliseconds the cache is cold.

Here is the trap. If the key is popular, a lot of requests arrive during those 200 milliseconds, and every single one of them looks in the cache, finds nothing, and also goes to the source. They do not wait for the first one to finish. They have no idea the first one is even happening. So instead of one call to the source, you get one call for every request that arrives in the gap.

How big is that burst? It is just arrival rate times recompute time. A key taking 50,000 requests per second with a 200 millisecond recompute produces about 50,000 times 0.2, which is 10,000 simultaneous calls to a source that normally sees almost none. That is the herd. Ten thousand requests, triggered by one key going cold for one fifth of a second.

And notice what makes it vicious. It is one key, so you cannot shard your way out of it. It happens at the moment of highest traffic, because that is when the most requests fall into the gap. And the recompute is the slow thing, so the more loaded your database already is, the longer the gap, the bigger the herd, the more loaded the database, the longer the gap. The spike feeds itself. Plenty of real outages are exactly this: a cache node restarts or a hot key expires, the herd hits, the database slows, the gap widens, and the whole thing snowballs until something falls over.

In Part 1 of the lab you reproduce this precisely. One hot key, 100 reader threads released at the same instant by a barrier, naive cache-aside. You count the calls to the source. The answer is 100. The whole crowd.

### Fix one: single flight, one cook in the kitchen (12 min)

The first fix is the obvious one once you see the problem. If ten thousand requests all want the same missing value, there is no reason for ten thousand of them to compute it. Let one compute it and make the rest wait for that answer. This is single flight, also called request coalescing.

The mechanism is a per-key lock. When a request misses, it does not go straight to the source. It grabs a lock for that key first. The first request to arrive gets the lock and starts the recompute. Every other request blocks on the same lock. When the first one finishes, it stores the value and releases the lock, and now here is the one line that matters: each waiter, the moment it gets the lock, looks in the cache again before computing. The value is there now. So it returns the cached value and never touches the source. That second look, the double check after you get the lock, is the entire trick. Without it you would just recompute one after another in a queue, which is no better.

The result is dramatic and you will measure it. The source goes from 100 calls to exactly 1. But single flight has a cost, and the lab shows it to you honestly in the same breath: all 99 other readers still had to wait for that one recompute. Single flight does not make the crowd faster, it makes the database safer. Everyone still pays the recompute latency once.

That waiting is also where single flight can bite you. All your waiters are now parked on one lock, trusting one request to finish. If that recompute hangs, say the database is slow or the downstream call times out, the whole crowd hangs with it. So real single-flight implementations always carry a timeout and a fallback: if the leader does not return in time, the waiters give up gracefully rather than pile up forever. The Go `singleflight` package is worth reading precisely because it is so small, and because production code wraps it with exactly these guards.

### Fix two: refresh before it goes cold (14 min)

Single flight fixes the symptom. It still lets the key go cold and then scrambles to protect the source while a hundred readers wait. The second fix is better in spirit: do not let the key go cold at all.

The idea is early recomputation, or refresh-ahead. While the value is still valid, a little before it is due to expire, one request quietly rebuilds it in the background and swaps in the fresh copy. Everyone else keeps reading the value that is still there, instantly, with no blocking. By the time the old expiry would have hit, the value has already been replaced, so the moment of coldness that the whole herd depends on simply never happens. When the crowd arrives, the key is warm. There is nothing to stampede.

Two details make this real rather than hand-wavy. First, the refresh has to be single flight too, or you have just invented a smaller herd of refreshers. In the lab a non-blocking gate lets exactly one reader start the background refresh and sends the others straight back to reading the valid value. Nobody blocks, not even the one that triggers the refresh.

Second, the clever version makes the "a little before expiry" decision probabilistic. If every request refreshed at exactly "expiry minus two seconds", they would all try at the same instant and you would get a herd again, just two seconds early. The XFetch trick rolls a weighted dice on each read: the closer the value gets to expiry, the higher the chance that this particular read is the one that triggers the refresh. So the refresh happens once, early, from a single request, and it spreads naturally instead of synchronizing. The lab uses a simple fixed early window to keep the code readable, and the paper in the reading list has the probabilistic version if you want it.

There is a close cousin worth knowing by name: stale-while-revalidate, which you will meet again on the CDN day. Same instinct. Serve the slightly old value right now, refresh it in the background, never make the reader wait for a recompute. And one more humble fix that belongs here: TTL jitter. If you load a thousand keys at boot with the same flat TTL, they all expire at the same second and you get a herd across all of them at once. Add a little randomness to each TTL and the expiries smear out over time. It is one line of code and it quietly prevents a whole class of self-inflicted stampedes.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-17-drills.md`](../notes/day-17-drills.md).

D1. A hot key gets 50,000 requests per second, and the recompute takes 200 ms. The key expires. Roughly how many requests pile onto the source in the gap before the first recompute refills the cache, and what is the general formula for the size of that herd?

D2. Single flight pins the source to one call. The other requests from D1 still arrive during the recompute: what do they do, what latency do they see, and what is the danger if that one recompute hangs or fails?

D3. Early recomputation refreshes the value before it expires. Why does that make the herd disappear instead of just shrink, and why is probabilistic early expiry, `now - delta * beta * ln(random()) >= expiry`, better than every request refreshing at a fixed "expiry minus X"?

D4. Your service boots and warms 10,000 cache keys at once, all with a flat 60 s TTL. What happens at the 60 s mark, and how does adding random jitter to each TTL fix it, and how much jitter is enough?

D5. A cache running at a 90% hit rate drops to an 80% hit rate under the same request volume. By how much does the load on the database behind it go up, and how is a stampede the most violent version of this same arithmetic?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-17-stampede/stampede.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-17-stampede/stampede.py).

It is in three parts. Part 1 fires 100 reader threads at one cold hot key with naive cache-aside and counts the calls to the slow source. Part 2 puts a per-key lock in front of the recompute and counts again. Part 3 keeps the key warm with early recomputation driven by a trickle of background traffic, then fires the same crowd and watches the source stay untouched.

Standard library only. The slow source is a 50 ms `time.sleep`, which is enough to make the race real. The whole thing runs in under two seconds and writes no files.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The naive herd. One hot key is cold, 100 readers all miss at the same instant. How many times does the slow source get called in that burst?
- P2. Now with a per-key lock (single flight). Only the first reader should recompute. How many source calls now?
- P3. Single flight fixes the source load, but what does it cost the crowd? Of the 100 readers, how many had to block and wait for that one recompute?
- P4. Early recomputation keeps the value warm ahead of expiry. When the same herd arrives now, how many source calls happen in the burst?

P1 is the one to feel in your gut first. Many people guess "surely not all of them, the cache would catch up". Write down a number before you run it.

### Fill in the TODOs

1. TODO 1 is the naive miss: call the slow source. This is the one line the entire herd runs at the same moment, so it is what Part 1 counts.
2. TODO 2 is the single-flight double check: after you grab the per-key lock, look in the cache one more time before recomputing. This one re-read is what turns 100 calls into 1.
3. TODO 3 is the early-refresh decision: trigger a refresh when you are inside the last `EARLY_WINDOW` seconds before expiry, so the value is rebuilt before it ever goes cold.
4. TODO 4 is the non-blocking gate: try to claim the single background refresh without waiting, so exactly one reader refreshes and nobody blocks.

```bash
cd labs/day-17-stampede
python3 stampede.py
```

### What you're going to discover

Part 1 is the shock. One key, cold for a fraction of a second, and all 100 readers recompute it. The source is called 100 times for a value that one call could have produced. That is the herd, and it is the spike that knocks over the database the cache was supposed to shield.

Part 2 is the relief, with a sting in the tail. The lock drops the source to exactly 1 call. But the output also tells you that 99 readers still blocked waiting for that single recompute. Single flight protects the database, it does not make the crowd fast, and if the recompute ever hangs, those 99 waiters hang too.

Part 3 is the one that feels like a magic trick until you see why. A steady trickle of normal traffic keeps the key warm by refreshing it, in the background, just before each expiry. So when the same crowd of 100 arrives, the key is already fresh. Zero source calls in the burst, zero readers blocked. There was never a cold moment for them to stampede into.

### Traps ⚠️

- If Part 1 does not give you close to 100, your readers are not actually arriving together. The lab uses a `threading.Barrier` so all 100 threads wait at a start line and are released at the same instant, before any of them finishes the 50 ms recompute. Do not remove the barrier and then wonder why the herd shrank.
- In Part 2, the one line that matters is the second cache read after you acquire the lock. If you skip it and recompute straight away, you get 100 calls in a slow queue, which is worse than the naive version, not better. The double check is the whole idea.
- In Part 3, the refresh must be non-blocking and single flight, or you just moved the herd into the refresh path. The gate uses `acquire(blocking=False)`: one reader gets it and refreshes in the background, the rest read the valid value and move on. If the background refresh blocked the reader, "nobody waits" would quietly become false.

### Deliverable

[`labs/day-17-stampede/RESULTS.md`](../labs/day-17-stampede/RESULTS.md) has a skeleton. Paste the output, and write one line: with the naive version the source took 100 calls, with the lock it took 1 but 99 readers waited, and with early refresh it took 0 and nobody waited. Which fix would you reach for first on a real hot key, and why?

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise: "I fired 100 requests at one cache key the instant it expired and counted 100 trips to the database. One key going cold for a fraction of a second. Then I fixed it two ways." The scoreboard, 100 then 1 then 0, is the screenshot.

Example posts are on the [Day 17 posts](../shares/day-17-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the herd size you measured and how far each fix cut it, and one thing you still cannot explain.

Day 18 is the hot key itself: when one key takes a million reads a second while the rest of the shard sits idle, the celebrity problem. Today the danger was one key going cold. Tomorrow it is one key being too popular to live on a single shard at all.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The herd is arrival rate times recompute time. 50,000 requests per second times 0.2 seconds is about 10,000 requests landing on the source in the gap before the first recompute refills the cache. The general formula is `herd ≈ λ × T`, where λ is the request rate for that key and T is how long the recompute takes. Two things fall straight out of it. A slower source makes a bigger herd, so the stampede is worst exactly when the database is already struggling. And it scales with the popularity of the one key, which is why you cannot shard your way out of it.

D2. With single flight, the first request computes and the other roughly 10,000 that arrive during the recompute block on the per-key lock. When the leader finishes and fills the cache, each waiter wakes, re-reads the cache, finds the value, and returns it. So the source sees 1 call instead of 10,000, which is the whole win. The latency those waiters see is about one recompute, T, because they all waited for the leader. That is the honest cost: single flight protects the database, it does not make the crowd fast. The danger is that every waiter now depends on one request. If that recompute hangs or the source times out, all 10,000 waiters hang with it, which is why real single-flight code always has a timeout and a fallback so the waiters can give up instead of piling up.

D3. Early recomputation refreshes the value while it is still valid, so the cache is never cold. The herd depends on a gap, the stretch of time when the key has expired and the first recompute has not finished. Single flight shrinks what happens during that gap to one call. Early recomputation removes the gap, so there is no moment for a herd to form at all. Probabilistic early expiry beats a fixed "expiry minus X" because a fixed threshold is itself a synchronized instant: every request that reads just after it would try to refresh together, and you would get a herd again, just earlier. The `now - delta * beta * ln(random()) >= expiry` roll makes each read's chance of triggering the refresh rise as expiry approaches, so one request refreshes early and alone, and the decision spreads out instead of snapping to a boundary. The `delta` term scales the window by how long the recompute takes, so slower values start refreshing earlier.

D4. At the 60 second mark all 10,000 keys expire in the same second, and if any of them are being read you get a stampede across all of them at once, a self-inflicted herd caused purely by loading them together. Jitter fixes it by setting each TTL to the base value plus a random spread, for example 60 seconds plus or minus up to 10 seconds, so the expiries smear out over a 20 second window instead of landing on one instant. Enough jitter is "wider than your recompute gap and wide enough that the per-second expiry rate is something the source can absorb". A spread comparable to the TTL itself, say 10 to 20 percent, is the usual rule of thumb. It costs one line and removes a whole category of outage.

D5. At a 90% hit rate, 10% of requests miss and reach the database. At an 80% hit rate, 20% miss. The request volume did not change, but the miss rate doubled from 10% to 20%, so the load on the database doubles. This is the insight from the start of the week: a 10 point drop in hit rate is not a 10% increase in database load, it is a doubling. Push it further and it gets worse fast, 90% to 50% is a fivefold increase. A stampede is this same arithmetic taken to its violent extreme: for one hot key, for a fraction of a second, the hit rate does not drop to 80%, it drops to 0%, and every single request for that key becomes a miss at the same instant. The gentle version is a rising database bill. The violent version is an outage.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-17-stampede/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-17-stampede/solution.py).

TODO 1, the naive miss. The one line the whole herd runs at the same moment:

```python
value = source.recompute(key)
```

TODO 2, the single-flight double check. After you hold the per-key lock, look in the cache again before recomputing. This re-read is what turns 100 calls into 1:

```python
cached = cache.get(key)
```

TODO 3, the early-refresh decision. Trigger a refresh when you are inside the last `EARLY_WINDOW` seconds before this entry expires:

```python
should_refresh = now >= entry.expiry - EARLY_WINDOW
```

TODO 4, the non-blocking single-refresh gate. Try to claim the refresh without waiting, so exactly one reader refreshes and nobody blocks:

```python
got = gate.acquire(blocking=False)
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, one hot key, 100 reader threads.

```
==============================================================================
Part 1: the stampede. One hot key goes cold, the whole crowd misses.
==============================================================================
  readers in the crowd:              100
  readers that ran the recompute:    100
  calls to the slow source:          100
  The key was cold for one instant and every reader missed together,
  so every reader rebuilt it. One expiry, N trips to the database.
  That burst is the thundering herd. On a real system it is the spike
  that knocks over the database the cache was meant to protect.

==============================================================================
Part 2: fix one. A per-key lock, so only the first reader rebuilds.
==============================================================================
  readers in the crowd:              100
  readers that ran the recompute:    1
  readers that waited for it:        99
  calls to the slow source:          1
  The lock lets exactly one reader rebuild the value. Everyone else
  waits on the lock, then reads what that one reader just stored. The
  source goes from a herd to a single call. The catch is right there
  in the numbers: all 99 other readers still blocked for one recompute.

==============================================================================
Part 3: fix two. Refresh early, so the value is never cold at the herd.
==============================================================================
  source calls over the whole warm-up (1.2s of trickle): 5
  readers in the herd:               100
  readers that blocked (cold miss):  0
  source calls during the herd:      0
  The value was refreshed just before each expiry by a single reader,
  in the background, while the rest kept reading the fresh copy. So
  when the crowd arrives the key is warm: everyone gets an instant hit,
  nobody blocks, and the source is not touched at all in the burst.

==============================================================================
Scoreboard
==============================================================================
  P1 naive source calls              you =  100   actual =    100        close enough
  P2 single-flight source calls      you =    1   actual =      1        close enough
  P3 single-flight waiters           you =   99   actual =     99        close enough
  P4 early-recompute herd calls      you =    0   actual =      0        close enough

==============================================================================
The number to carry
==============================================================================
  Same hot key, same crowd of 100 readers, same slow source.
  Naive cache-aside:  100 calls to the source in one burst.
  Per-key lock:        1 call, but 99 readers had to wait for it.
  Early recompute:     0 calls at the herd, 0 readers blocked.
  A stampede is not a caching detail. It is the difference between a
  cache that shields your database and one that lines the whole crowd
  up to hit it the moment a popular key expires.
```

Part 1 is the day in one number. A hundred readers, one key, and because the key was cold for the instant they all arrived, the source was called a hundred times for a value a single call could have produced. Nothing about the readers was special. They just happened to miss together, which is exactly what a popular key guarantees when it expires under load.

Part 2 is the fix you reach for first, and the honest cost next to it. The per-key lock cut the source to one call. The same output shows 99 readers blocked waiting for that one recompute, which is the thing to remember: single flight saves the database, not the crowd. Everybody still pays the recompute latency once, and if that recompute ever hangs, all 99 hang with it.

Part 3 is the better idea. A thin trickle of ordinary traffic kept the key warm by refreshing it in the background just before each expiry, so the cold moment the herd needs never arrived. The crowd of 100 found a fresh value, returned instantly, and touched the source zero times. Over the whole warm-up the source was called only a handful of times, one refresh per TTL, never a burst. That is the shape you want for a genuinely hot key: not a wall to funnel the herd through, but a value that is simply never cold when the herd shows up.

The one line to carry out of today: a cache fails at the worst possible moment, when a popular key expires under load, so the real work of caching a hot key is making sure that moment never happens.

</details>
