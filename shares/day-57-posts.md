---
title: "Day 57 posts"
parent: "Day 57: capstone load test"
grand_parent: "Week 8: putting it all together"
nav_order: 3
---

# Day 57 posts: LinkedIn and X

The angle is finding the knee: break your own thing on purpose, measure where it falls over. Swap in your own voice and your own numbers.

## LinkedIn

Day 57 of 60 days of system design. The best day of the course: I pointed a load generator at the slice I built and broke it on purpose.

A load test tells its story in two lines. Throughput, which rises as you add clients then flattens, and latency, which barely moves then takes off. The place where throughput goes flat but latency keeps climbing has a name: the knee. Before the knee, more clients means more work done. After it, more clients just means everyone waits in a longer queue. The knee is your real capacity, and it is where your bottleneck lives.

My reference service told a clean story. Read-heavy, it peaked around 12,700 requests per second and the knee came at 8 concurrent workers. Write-heavy, it peaked around 4,200, about a third, and flattened even earlier. That gap is the whole lesson: every write serialises through one database lock, so throwing more concurrency at it does nothing except grow the queue and push p99 from under 3ms to nearly 12ms.

Then the real work, which is not running the test, it is what you do with the result. Form a hypothesis for the bottleneck (Brendan Gregg's USE method: for each resource check utilisation, saturation, errors). Change one thing. Measure again. Did the knee move? That cycle is performance engineering.

Two things I will not forget. First, you run production at about 70 percent of the knee, not at it, because the knee is already the edge of the cliff and you need headroom for spikes and failures. Second, watch p99, not the average, because a perfectly healthy average can hide a slowest 1 percent that is on fire.

Breaking your own thing in a quiet room beats having real users break it at 2am. Every time.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #performance #loadtesting #learninginpublic

## X thread

**1/**

Day 57 of 60 days of system design. Best day of the course: I pointed a load generator at the slice I built and broke it on purpose.

**2/**

A load test tells its story in two lines. Throughput rises then flattens. Latency barely moves then takes off.

Where throughput goes flat but latency climbs = the knee. That is your real capacity and your bottleneck.

**3/**

My service: read-heavy it peaked ~12,700 req/s, knee at 8 workers. Write-heavy ~4,200, a third, flattening earlier.

The gap is the lesson: every write serialises through one DB lock. More concurrency just grows the queue and pushes p99 from <3ms to ~12ms.

**4/**

The real work isn't running the test, it's what you do with it.

Hypothesis (USE method: utilisation, saturation, errors per resource) → change one thing → measure again → did the knee move? That's performance engineering.

**5/**

Two keepers:
- Run production at ~70% of the knee, not at it. The knee is the cliff edge.
- Watch p99, not the average. A healthy average hides a slowest 1% that's on fire.

Break your own thing before 2am does it for you.

Code: github.com/anurag629/system-design-60-days
