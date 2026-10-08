---
title: "Day 17 drills"
parent: "Day 17: the thundering herd"
grand_parent: "Week 3: caching and the CDN"
nav_order: 2
---

# Day 17 drills

Written on paper first. Stampedes, the per-key lock, early recomputation, TTL jitter, and the hit-rate arithmetic that hides underneath all of it.

D1 (a hot key gets 50,000 requests per second, and the recompute takes 200 ms. The key expires. Roughly how many requests pile onto the source in the gap before the first recompute refills the cache, and what is the general formula for the size of that herd?):

D2 (single flight pins the source to one call. The other requests from D1 still arrive during the recompute: what do they do, what latency do they see, and what is the danger if that one recompute hangs or fails?):

D3 (early recomputation refreshes the value before it expires. Why does that make the herd disappear instead of just shrink, and why is probabilistic early expiry, now - delta * beta * ln(random) >= expiry, better than every request refreshing at a fixed "expiry minus X"?):

D4 (your service boots and warms 10,000 cache keys at once, all with a flat 60 s TTL. What happens at the 60 s mark, and how does adding random jitter to each TTL fix it, and how much jitter is enough?):

D5 (a cache running at a 90% hit rate drops to an 80% hit rate under the same request volume. By how much does the load on the database behind it go up, and how is a stampede the most violent version of this same arithmetic?):
