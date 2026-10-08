---
title: "Day 51 drills"
parent: "Day 51: mock, a URL shortener"
grand_parent: "Week 8: putting it all together"
nav_order: 2
---

# Day 51 drills

Paper first. Warm-up before the timed run, so your deep dive is sharp.

D1 (scale: 100M new URLs a day, 100 reads each, peak = 3x average: writes/s, reads/s, storage over 5 years):

D2 (the short code: hash vs counter-in-base62 vs key generation service, and your pick for 100M/day across many servers, with the reason):

D3 (the read path: click to redirect, exactly where the cache sits and the hit rate you expect):

D4 (301 vs 302, how it interacts with counting clicks, and what carries the count without slowing the redirect):

D5 (the code generator dies: what happens to writes, what happens to reads, and why reads do not care):
