---
title: "Day 16: eviction and the working set"
parent: "Week 3: caching and the CDN"
nav_order: 2
has_children: true
---

# Day 16
## Eviction and the working set, or how a tiny cache serves most of your reads 🧊

Today's one idea: your cache is smaller than your data, always, so it has to throw things out. Which things it throws out is the whole game. And here is the happy surprise you will measure today: because real traffic is lopsided, a few keys very hot and a long cold tail, a cache that holds a tiny fraction of your keys already serves most of your reads. That is why Redis can be small next to the database it protects. The flip side is just as important. If your traffic has no hot set, a cache barely helps at all, and no eviction policy can save it.

Yesterday you bolted a cache in front of the database and watched reads get fast. Today you ask the question that decides your Redis bill: when the cache is full, what do you keep?

---

## Before you start ⏪

You need Day 15 fresh: cache-aside, a read checks the cache first, and on a miss it fetches from the database and stores the value. Today we keep that exact pattern and add the one thing Day 15 ignored, a size limit. Once the cache is full, every new key you store costs you an old one.

You also want the Zipf idea from the back of your mind, and we will build it from scratch anyway. If you can read a dictionary and a for loop in Python, you can do today's lab. The only data structure that matters is `collections.OrderedDict`, and it does almost all the work for you.

---

## Words you will meet today 📖

Eviction is what a full cache does to make room: it picks one resident entry and throws it out so a new one can go in. A cache that never evicts is just a slow copy of your whole database.

An eviction policy is the rule for choosing the victim. The common ones are LRU (least recently used), LFU (least frequently used), FIFO (first in, first out) and random. Today you build and race three of them.

LRU, least recently used, evicts the entry that has gone longest without being touched. The bet is simple: if you have not needed it for a while, you probably will not need it soon. It is the default in most caches because it is cheap and it is usually right.

FIFO, first in, first out, evicts whatever was inserted longest ago, no matter how often it has been read since. It is LRU without the memory of reads, and today you will see exactly what that costs.

The working set is the set of keys that are actually being used in a given window of time. Not the keys that exist, the keys that get read. For most systems the working set is a small slice of the whole keyspace, and the entire art of caching is holding the working set in fast memory.

The hit rate is the fraction of reads the cache answers itself. The miss rate is the rest, the reads that fall through to the database. The miss rate is the number that bites, and most people watch the wrong one.

A Zipf distribution is the lopsided popularity curve you see everywhere: the most popular key gets roughly twice the traffic of the second, three times the third, and so on. A handful of keys dominate, and a very long tail of keys are each touched almost never. Web pages, search terms, products, videos, all of them are roughly Zipf.

The knee is the bend in the hit-rate-versus-size curve. Under Zipf, hit rate climbs steeply as the cache grows to cover the hot set, then flattens hard once the hot set is captured. Past the knee, every extra megabyte of Redis buys you less and less.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Redis key eviction](https://redis.io/docs/latest/develop/reference/eviction/), the official docs. The canonical reference for what a real cache throws out: the `maxmemory` limit, the `allkeys-lru` and `allkeys-lfu` policies, and the lovely detail that Redis does not even do true LRU. It samples a handful of keys and evicts the oldest of those, because perfect LRU costs too much memory. Today's Part 1, running in production.
- [Cache replacement policies](https://en.wikipedia.org/wiki/Cache_replacement_policies) on Wikipedia. A clean tour of exactly the policies in today's lab, LRU, FIFO, LFU and random, with the trade-offs laid side by side. Read the LRU and FIFO sections closely, because Part 3 is a race between those two.
- [AWS Builders' Library, caching challenges and strategies](https://aws.amazon.com/builders-library/caching-challenges-and-strategies/). The backbone of the week, written by people who run caches at Amazon's scale. For today, the parts on hit rate, the working set and sizing a cache.

Watch:
- [Caching in distributed systems, a friendly introduction](https://www.youtube.com/watch?v=zw7VwIlkPPc) by Gaurav Sen, about 11 minutes. A gentle tour of why we cache and how the replacement policies differ. Good to watch before the lab.
- After the lab, [Key eviction strategies in Redis](https://www.youtube.com/watch?v=EkaTFT9ox-I) by Arpit Bhayani (Asli Engineering), about 20 minutes. He implements eviction by hand and then walks Redis's real, approximate LRU. This is today's Part 1 and Part 3 taken all the way into a production engine.

### Why a cache has to throw things out (12 min)

Start with the obvious thing people skip. A cache is fast because it lives in memory, and memory is small and expensive. Your database holds a terabyte on cheap disk. Your Redis holds a few gigabytes of expensive RAM. So the cache can never hold everything, which means the moment it fills up, storing a new key requires deleting an old one. That deletion is eviction, and the rule that picks the victim is the eviction policy.

Here is the mental picture I keep. Your database is the big kitchen pantry at the back of the house, everything you own is in there, but it is a walk away. Your cache is the small fridge on the counter, right at arm's reach, and it holds maybe twenty things. You cannot fit the pantry in the fridge. So the only question that matters is: of everything you own, which twenty things do you keep at arm's reach? If you keep the milk, the eggs and the butter you reach for every morning, the fridge saves you a hundred pantry trips a day. If you fill it with the fancy olive oil you use twice a year, the fridge is useless and you are still walking to the pantry every morning.

That is the working set. Not what you own, what you actually reach for in a given stretch of time. The whole job of a cache is to hold the working set, and the whole job of an eviction policy is to figure out what the working set is without being told.

### LRU in a dozen lines (14 min)

LRU is the default policy because it is both cheap to implement and usually right. The rule: when you must evict, throw out the entry that has gone longest without being touched. The bet is that recent use predicts future use, which for most workloads is true.

The clever part is that Python hands you LRU almost for free. `collections.OrderedDict` remembers the order keys were inserted, and it lets you cheaply move a key to the back and pop a key from the front. So an LRU cache is just an OrderedDict where:

- a read of a key moves that key to the back, marking it most recently used, with `self.data.move_to_end(key)`,
- and when the cache is over capacity, you evict the key at the front, the least recently used, with `self.data.popitem(last=False)`.

That is the entire mechanism. A read is a vote to keep. Eviction always takes from the front, which, because every read moved its key to the back, is always the key nobody has touched in the longest time. You will write exactly those two lines in the lab, and Part 1 checks they evict the right key with a tiny four-move trace: put A, put B, read A, put C. Because the read kept A warm, the key that should fall out is B, not A.

Now compare FIFO, first in, first out. FIFO is LRU with the memory removed. It evicts whatever was inserted longest ago and it does not care how often you have read it since. In OrderedDict terms, FIFO also pops the front, but it never calls `move_to_end`, so a read changes nothing. That one missing line is the whole difference, and in Part 3 you will watch it cost about five points of hit rate. FIFO keeps throwing out keys you are still using, just because they are old.

### The knee, and why the miss rate is the number that bites (16 min)

Here is the part worth slowing down for. Caching works as well as it does because real traffic is lopsided. Under a Zipf distribution, the most popular key might be a thousand times hotter than a key in the tail. So a small set of keys is a large share of the reads, which means a cache that holds only that small set already answers a large share of the reads. In the lab you will sweep the cache size and watch the hit rate curve climb steeply and then flatten. That bend is the knee, and it is the single most useful shape in caching.

The numbers you will measure, on a keyspace of ten thousand keys under a realistic Zipf skew: a cache holding just one percent of the keys serves about fifty-three percent of the reads. One percent of the keys, over half the traffic. Grow the cache to twenty percent of the keys and you reach about eighty-five percent, better, but notice that the last big jump cost you twenty times the memory of the first. That is the knee in action. The first sliver of cache is pure gold, and past the hot set you are paying more and more for less and less.

Then you will run the same sweep on a uniform workload, where every key is equally likely, and the curve is a boring straight diagonal. A ten percent cache gets a ten percent hit rate, a twenty percent cache gets twenty percent, and that is all you can ever get. There is no hot set to capture, so the cache can only win on the fraction of keys it happens to be holding when a request arrives. This is the honest warning under all the caching hype: a cache helps in proportion to how skewed your traffic is. No skew, no benefit, no policy can conjure one.

And now the number almost everyone watches wrong. People track the hit rate and feel good when it is ninety percent. But your database does not feel the hit rate, it feels the miss rate, and the miss rate is what lands on it. Say you serve ten thousand reads a second at a ninety percent hit rate. One thousand misses a second reach the database. Now the hit rate slips to eighty percent, a drop that sounds small. The miss rate just went from ten percent to twenty percent, so two thousand misses a second now reach the database. A ten point drop in hit rate doubled the load on your database. This is why a Big Billion Day or Diwali sale takes systems down: the extra traffic and the colder cache push the hit rate down a few points, the miss rate doubles, and the database that was comfortable yesterday is on fire today. Watch the miss rate. It is the one with its hand on the database's throat.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-16-drills.md`](../notes/day-16-drills.md).

D1. A cache fronts a database and takes 10,000 reads per second at a 90 percent hit rate. How many reads per second reach the database? Now the hit rate slips to 80 percent. How many reach it now, and by what factor did the database load change? What does that tell you about which number to watch?

D2. A Zipf workload where 1 percent of the keys serve about half the reads. You size a cache to hold exactly that 1 percent. Roughly what hit rate do you expect? If you double the cache to 2 percent of the keys, why does the hit rate not double, and why will you never quite reach 100 percent?

D3. An LRU and a FIFO cache, both capacity 3. The access order is: put A, put B, put C, read A, put D. Which key does LRU evict on the put D? Which key does FIFO evict? Explain in one line why they differ.

D4. A reporting job does a one-pass scan: it reads 1,000,000 distinct keys, each exactly once, in order, through an LRU cache that holds 10,000. What is the hit rate on the scan? What happens to the hot set that was resident before the scan started? What do real databases do to stop this?

D5. A workload where every key is equally likely, no hot set at all, and you size a cache at 10 percent of the keyspace. What hit rate can you expect, and would you add the cache?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-16-eviction/eviction.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-16-eviction/eviction.py).

It is in three parts. Part 1 builds an LRU cache on top of OrderedDict and checks it evicts the right key. Part 2 runs a Zipf workload and a uniform workload through the cache at seven sizes, from 0.1 percent of the keyspace up to 20 percent, and draws the two hit-rate curves as ASCII bars so you can see the knee with your own eyes. Part 3 holds the size fixed at 1 percent and races LRU against FIFO and random on the same Zipf trace.

Standard library only, pure in memory, no files and no network, fully deterministic, and it runs in about a second.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The knee. Zipf reads, a cache that holds just 1 percent of the keys. What hit rate, as a percent? (A few hot keys dominate, so this is far above 1 percent.)
- P2. The contrast. The same 1 percent cache, but a uniform workload where every key is equally likely. What hit rate now?
- P3. Covering the working set. Zipf reads, a cache grown to 20 percent of the keys. What hit rate?
- P4. Policy. At the 1 percent cache on the Zipf workload, by how many percentage points does LRU beat FIFO?

P1 against P2 is the one to feel before you run it. Same cache, same size, two workloads. Write down both numbers and sit with how far apart they are.

### Fill in the TODOs

1. TODO 1 is the read bump in `get`: on a hit, move the key to the most-recently-used end. This one line is what makes LRU an LRU and not a FIFO.
2. TODO 2 is the eviction in `_evict`: when over capacity, drop the least-recently-used key, which sits at the front of the OrderedDict.
3. TODO 3 is the hit rate: hits as a percentage of all lookups. The metric the whole lab turns on.
4. TODO 4 is the headline of Part 3: how many percentage points LRU beats FIFO by.

```bash
cd labs/day-16-eviction
python3 eviction.py
```

### What you're going to discover

Part 1 is a sanity check, but do not skip past it. The four-move trace, put A, put B, read A, put C, is the whole policy in miniature. If your read bump is missing, C evicts A instead of B, and the test fails loudly. That is TODO 1 earning its place.

Part 2 is the day. The Zipf curve shoots up and flattens: a 1 percent cache already serves about 53 percent of the reads, and going all the way to 20 percent only gets you to about 85 percent. The uniform curve, right underneath it, is a near-straight diagonal where the hit rate just equals the cache fraction. Put the two ASCII charts side by side and the lesson is impossible to miss. The cache is not magic. It is a bet on skew, and Zipf is a very skewed bet.

Part 3 is the policy race. At a fixed 1 percent size on the Zipf trace, LRU comes out around 52.7 percent, FIFO around 47.4 percent, and random around 47.3 percent. LRU wins by about five points because it treats a read as a vote to keep, so the hot set stays resident. FIFO and random land together, a little behind, because neither one looks at how often a key is read. They evict hot keys on schedule and then pay to fetch them back.

### Traps ⚠️

- The hit rate depends on the skew. The lab uses a Zipf exponent of 1.1, which is realistic, but if you crank it up the knee gets sharper and if you flatten it the knee softens. Do not read the exact 52.7 as a law of nature. The shape of the curve is the lesson, not the third digit.
- Under this independent-reference workload, FIFO and random come out almost the same, and LRU's win is about five points, not fifty. That is honest. LRU's real advantage grows when traffic has bursts and temporal locality, which this clean workload deliberately does not have. Trust the direction, LRU on top, and know the gap widens in the messy real world.
- LRU is not always the hero. A one-pass scan (drill D4) is its worst enemy: the scan touches a million keys once each, hits nothing, and flushes your entire hot set on the way through. This is why MySQL's InnoDB uses a midpoint-insertion LRU and Postgres uses a clock sweep, both built to survive a scan. Recent does not always mean valuable.

### Deliverable

[`labs/day-16-eviction/RESULTS.md`](../labs/day-16-eviction/RESULTS.md) has a skeleton. Paste the output, especially the two ASCII curves, and write one line: how small a cache captured most of the Zipf reads, and why the uniform workload told such a different story.

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise: "I ran the same reads through a cache at 1 percent of the keyspace. On realistic Zipf traffic it served 53 percent of the reads. On uniform traffic it served 1 percent. The cache is a bet on skew." The two ASCII curves, the steep Zipf climb next to the flat uniform diagonal, are the screenshot. The miss-rate doubling (90 to 80 percent hit rate doubles database load) is the line that makes people stop scrolling.

Example posts are on the [Day 16 posts](../shares/day-16-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the hit rate a 1 percent cache gave you on Zipf versus uniform, and one thing you still cannot explain.

Day 17 is the thundering herd, also called a cache stampede. Today you learned that a few hot keys carry most of your traffic. Tomorrow you find out what happens when one of those very hot keys expires at a busy moment and ten thousand requests all miss at the same instant and stampede the database together. Think IRCTC at 10 AM when tatkal booking opens. 🚆 You will reproduce the stampede and then fix it two ways.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. At a 90 percent hit rate, 10 percent of 10,000 reads per second miss, so 1,000 reads per second reach the database. At an 80 percent hit rate, 20 percent miss, so 2,000 reads per second reach it. The database load doubled, from a hit-rate drop that sounded like only ten percent. The lesson: watch the miss rate, not the hit rate. Near the top of the curve a small slip in hit rate is a large jump in misses, because the misses are a small number and doubling a small number is easy. Going from 99 to 98 percent also doubles the database load. This is exactly the mechanism behind sale-day outages.

D2. About 50 percent, because by assumption that 1 percent of keys is half the reads, and a cache that holds them answers those reads. Doubling the cache to 2 percent does not double the hit rate, because the second 1 percent of keys is far colder than the first, each of those keys is requested much less often, so they add far fewer hits. That is the knee: the first slice of cache captures the hot set, and everything after it is scraping the long cold tail. You never reach 100 percent because the tail is enormous and each tail key is requested too rarely to still be resident when it comes back, so it misses almost every time.

D3. Start with the cache full after put A, put B, put C. The read of A is where they split. LRU counts the read and moves A to most recently used, so its least-recently-used key is now B, and put D evicts B. FIFO ignores the read entirely, its order is still the insertion order A, B, C, so put D evicts A, the first one in. They differ because FIFO evicts by age alone and throws out the key you literally just used, while LRU remembers the read and keeps A. That single difference is the five-point gap you measured in Part 3.

D4. The hit rate on the scan is zero, because every one of the million keys is seen for the first time, so every access is a miss. Worse, as the scan streams through, it keeps inserting scan keys that will never be read again, and each insertion evicts something, so by the end your entire hot set has been pushed out and replaced by cold scan keys you will never touch again. After the scan the cache is useless until the hot set gets re-fetched and re-warmed. This is cache pollution. Real databases defend against it: MySQL's InnoDB inserts new pages at the midpoint of its LRU list rather than the head, so a one-pass scan cannot reach the hot end and evict the truly hot pages. Postgres uses a clock-sweep buffer policy that resists a single scan. Many caches add scan-resistant policies such as segmented LRU or ARC, which require a key to be seen more than once before it is treated as hot. The deep point: LRU assumes recent means valuable, and a scan is a flood of recent-but-worthless keys that breaks the assumption.

D5. About 10 percent, because with no hot set the only reads you catch are the ones that happen to ask for a key currently resident, and you are holding 10 percent of the keys, so roughly 10 percent of reads hit. You almost certainly would not add the cache. You would be paying for the memory, the operational complexity, and the invalidation problem (a second copy of the truth that can go stale) to shave 10 percent off the database reads, and that 10 percent scales with how much memory you buy, so there is no cheap win hiding anywhere. A cache earns its keep only when the traffic is skewed enough that a small cache captures a large share. For a genuinely uniform workload, such as random point lookups by UUID with no popular key, measure first and expect the cache to buy you almost nothing.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-16-eviction/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-16-eviction/solution.py).

TODO 1, the read bump that makes LRU an LRU, inside `get` on a hit:

```python
self.data.move_to_end(key)
```

TODO 2, the eviction, inside `_evict`, dropping the least-recently-used key at the front:

```python
self.data.popitem(last=False)
```

TODO 3, the hit rate as a percent of all lookups:

```python
return 100.0 * self.hits / total
```

TODO 4, the headline of Part 3, how many points LRU beats FIFO by:

```python
gap = lru_rate - fifo_rate
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, keyspace of 10,000 keys, 200,000 reads, Zipf exponent 1.1.

```
==============================================================================
Part 1: build the LRU cache, and check it evicts the RIGHT key.
==============================================================================
  put A, put B, read A, put C   (capacity is 2)
  after the read, A is most-recently-used and B is least-recently-used
  so putting C should evict B. resident keys now: ['A', 'C']
  PASS: B was evicted, A survived because the read kept it warm.

==============================================================================
Part 2: the hit-rate-vs-size curve. Zipf vs uniform, same cache.
==============================================================================
  ZIPF reads (a few keys are very hot): hit rate as the cache grows
     0.1% of keys |#########                               |  22.8%
     0.5% of keys |##################                      |  44.2%
       1% of keys |#####################                   |  52.7%
       2% of keys |########################                |  60.7%
       5% of keys |############################            |  70.7%
      10% of keys |###############################         |  77.8%
      20% of keys |##################################      |  84.5%

  UNIFORM reads (every key equally likely): same cache, same sizes
     0.1% of keys |                                        |   0.1%
     0.5% of keys |                                        |   0.5%
       1% of keys |                                        |   1.0%
       2% of keys |#                                       |   2.0%
       5% of keys |##                                      |   5.0%
      10% of keys |####                                    |  10.1%
      20% of keys |########                                |  20.0%

  The Zipf curve shoots up then flattens: that bend is the KNEE. A
  cache of 1 percent of the keys already serves about half the reads,
  because a handful of hot keys ARE half the reads. The uniform curve
  is a near-straight diagonal: with no hot set, hit rate can only track
  the fraction of keys you can afford to hold. Same cache, same sizes,
  wildly different payoff, decided entirely by the shape of the demand.

==============================================================================
Part 3: policy matters. Same Zipf load, same size (1%), 3 policies.
==============================================================================
    LRU     |#####################                   |  52.7%
    FIFO    |###################                     |  47.4%
    random  |###################                     |  47.3%

  LRU beats FIFO by 5.3 points on the very same workload and size.
  FIFO and random land together, a little behind, because neither looks
  at how often a key is read. They evict a hot key on schedule and then
  pay to fetch it again. LRU notices the re-reads and keeps the hot set
  resident, so it spends its scarce slots on the keys that earn them.

==============================================================================
Scoreboard
==============================================================================
  P1 Zipf hit @ 1% cache         you =  50.0   actual =    52.7 %       close enough
  P2 uniform hit @ 1% cache      you =   1.0   actual =     1.0 %       close enough
  P3 Zipf hit @ 20% cache        you =  85.0   actual =    84.5 %       close enough
  P4 LRU - FIFO (points)         you =   5.0   actual =     5.3 pts       close enough

==============================================================================
The number to carry
==============================================================================
  A cache holding just 1% of the keys served 53% of the Zipf
  reads. The same size on a uniform workload served only 1%. Growing
  the cache to 20% of the keys got Zipf to 85%, so most of the
  win came from the first slice: that is the knee. And at a fixed size,
  LRU beat FIFO by 5 points just by treating a read as a vote to keep.
  This is why Redis is small next to the database it fronts, and why the
  question is never 'cache everything', it is 'cache the hot set'.

Now write labs/day-16-eviction/RESULTS.md.
```

Part 1 is the mechanism check. The four-move trace is LRU in miniature: because the read of A moved it to the most-recently-used end, the key that falls out when C arrives is B, not A. If your read bump were missing, this is where it would blow up, and that is the point of running it first.

Part 2 is the whole day in two little charts. The Zipf curve climbs fast and flattens: a cache of 1 percent of the keys already serves 52.7 percent of the reads, and even at 20 percent of the keys you only reach 84.5 percent. The uniform curve underneath is a straight diagonal where the hit rate simply equals the cache fraction, 10 percent cache for 10 percent hits. Same cache, same sizes, utterly different payoff, and the only thing that changed is whether the traffic had a hot set. That is the argument for caching and the warning about it, in one screenshot.

Part 3 is why the policy you pick matters. At a fixed 1 percent size, LRU scored 52.7 percent, FIFO 47.4 percent, random 47.3 percent. LRU's five-point lead comes from one idea: a read is a vote to keep, so hot keys keep getting bumped to safety and the hot set stays resident. FIFO and random ignore reads, so they evict hot keys by age or by luck and then pay to fetch them again. Under this clean workload five points is the honest gap, and it widens once real traffic adds bursts and locality.

The one line to carry out of today: a cache is a bet that your traffic is skewed, Zipf makes that a very good bet, and the number that decides whether your database survives is the miss rate, not the hit rate.

</details>
