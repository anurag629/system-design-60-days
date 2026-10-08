---
title: "Day 45 drills"
parent: "Day 45: rate limiting"
grand_parent: "Week 7: production"
nav_order: 2
---

# Day 45 drills

Written on paper first. Token bucket maths, the fixed-window boundary, leaky vs token, 429 behaviour, and where the limiter lives.

D1 (a token bucket refills at 100 tokens/s with a capacity of 500, and starts full: the largest burst it can pass in one instant, the steady rate it allows a client hammering it forever, and what the capacity and the refill rate each control):

D2 (a fixed-window limiter allows 60 requests per 60-second window: the most a single client can get through in any 60-second stretch of wall-clock time if they time it right, why that happens, and the one-line change a sliding-window counter makes to stop it):

D3 (same bursty input into a token bucket and a leaky bucket: which one lets a burst reach the backend and which one smooths the output to a constant rate, the cost the smoothing one pays, and which you would put in front of a fragile legacy database that falls over above 50 writes/s):

D4 (a client is over its limit: why returning 429 with a Retry-After header beats both silently dropping the request and letting it through, what a well-behaved client does with Retry-After, and why a limiter that does its slow work before rejecting is self-defeating under load):

D5 (where the limiter lives: why a per-process in-memory token bucket behind 10 load-balanced servers actually enforces roughly 10x the intended global limit, the usual fix, and the new failure mode that fix introduces):
