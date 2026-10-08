---
title: "Day 16 posts"
parent: "Day 16: eviction and the working set"
grand_parent: "Week 3: caching and the CDN"
nav_order: 3
---

# Day 16 posts: LinkedIn and X

The two ASCII curves make the screenshot: the Zipf one shoots up and flattens (the knee), the uniform one is a straight diagonal. Swap in your own numbers and voice.

## LinkedIn

Day 16 of 60 days of system design. Today I measured the one fact that decides how big your Redis needs to be, and it is not the size of your data.

A cache is smaller than the data behind it, so it has to throw things out. I built a plain LRU cache (about a dozen lines on top of Python's OrderedDict: a read bumps the key to the back, and when you are full you drop the key at the front) and then I ran two different read workloads through it at seven cache sizes.

Workload one was Zipf: a few keys very hot, a long cold tail, which is what real traffic actually looks like. Workload two was uniform: every key equally likely.

    cache = 1% of the keys
      Zipf workload:     52.7% hit rate
      uniform workload:   1.0% hit rate

Same cache, same size. The difference is entirely the shape of the demand. Under Zipf, 1% of the keys are most of the reads, so a cache holding just that 1% already serves half the traffic. Grow it to 20% of the keys and you reach about 84%, but most of the win came from that first sliver. That bend is the knee, and it is why Redis can be tiny next to the database it fronts.

Under uniform traffic there is no hot set to capture, so the hit rate just tracks the fraction of keys you can afford to hold. A 10% cache gets you a 10% hit rate. Caching barely helps at all.

Then I held the size fixed and swapped the eviction policy:

    LRU:     52.7%
    FIFO:    47.4%
    random:  47.3%

LRU wins by about 5 points, because it treats a read as a vote to keep, so the hot set stays resident. FIFO and random evict by age or by luck, so they keep throwing hot keys out and paying to fetch them again.

The number I am carrying: the miss rate, not the hit rate, is what hits your database. Going from a 90% to an 80% hit rate does not add 10% load, it doubles it. That one line explains a lot of sale-day outages.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #caching #redis #learninginpublic

## X thread

**1/**

Day 16 of 60 days of system design.

I ran the same reads through an LRU cache at a 1% cache size, two ways:

Zipf traffic (a few hot keys):  52.7% hit rate
uniform traffic (no hot set):    1.0% hit rate

Same cache. The workload shape is everything.

**2/**

A cache is smaller than your data, so it evicts. LRU is tiny on top of an OrderedDict:

- a read moves the key to the back (most recently used)
- when full, drop the key at the front (least recently used)

That is the whole thing.

**3/**

Sweep the cache size on Zipf traffic and the hit-rate curve has a KNEE:

 1% of keys -> 53%
 5% of keys -> 71%
20% of keys -> 84%

Most of the win is in the first slice, because a few hot keys ARE most of the reads. This is why Redis is small next to its database.

**4/**

Uniform traffic has no hot set, so the same sweep is a straight diagonal: a 10% cache gets a 10% hit rate. If your lookups have no hot key (think random UUIDs), a cache barely helps. Measure the shape before you pay for Redis.

**5/**

Hold the size fixed, change the policy:

LRU:    52.7%
FIFO:   47.4%
random: 47.3%

LRU wins because a read is a vote to keep, so the hot set stays resident. FIFO evicts by age and keeps tossing hot keys out.

**6/**

The number to carry: it is the MISS rate that hits your database.

90% -> 80% hit rate is not 10% more load. The miss rate doubled, so the database load doubled. That is the sale-day outage in one line.

Code: github.com/anurag629/system-design-60-days
