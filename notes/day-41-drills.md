---
title: "Day 41 drills"
parent: "Day 41: serving concerns, caching, limiting and fallback"
grand_parent: "Week 6: AI systems"
nav_order: 2
---

# Day 41 drills

Written on paper first. Semantic caching, token-based limiting, gateway fallback, and the token-cost maths.

D1 (a semantic cache runs over 10,000 support queries in a day; 60% are paraphrases of the 200 most common questions, and you measure a 55% hit rate. At $0.01 per model call, what do you save versus no cache? Then: a too-low threshold (0.3) causes false hits, a too-high one (0.95) causes false misses. Which error is worse, and why):

D2 (your token budget is 1,000,000 tokens per minute; you set a request limiter at 10,000 requests per minute, assuming 100 tokens each. A new summarization feature sends 5,000-token requests. How many does the request limiter admit, how many tokens is that, and what multiple of the budget? How many would a token bucket have admitted):

D3 (the primary model fails 20% of attempts, independently. (a) success on one attempt, (b) success with up to 3 attempts, (c) during a full outage the primary fails 100% of the time: success with 3 retries and no fallback, (d) add a secondary that fails 5% per attempt, up to 3 tries: outage success with fallback):

D4 (describe the order a request should flow through a gateway that has a semantic cache, a primary model and a secondary model. Explain how the cache plus fallback together let you survive a primary provider outage, and name the main risk of leaning on the cache during that outage):

D5 (the PM maths: 100,000 users, 20 messages a day each, average request 800 input tokens and 200 output tokens, priced at $3 per million input and $15 per million output. Daily cost with no cache? With a semantic cache at a 40% hit rate? Roughly what is the monthly saving):
