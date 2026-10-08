---
title: "Day 21 drills"
parent: "Day 21: designing a news feed"
grand_parent: "Week 3: caching and the CDN"
nav_order: 2
---

# Day 21 drills

Written on paper first, with numbers. The news feed, broken into its caching decisions.

D1 (scale: posts/sec, feed reads/sec, fan-out-on-write cost per day):

D2 (push vs pull on one post: 500 followers vs 10M, why push breaks for the celebrity):

D3 (hybrid read path: where the 199 normal posts come from vs the 1 celebrity):

D4 (feed cache memory: 100M x 800 ids x 8 bytes, does it fit, which Day 16 idea shrinks it):

D5 (celebrity posts, 10M refresh at once: which two week 3 problems, and the three protections):
