---
title: "Day 46 posts"
parent: "Day 46: multi-tenancy and isolation"
grand_parent: "Week 7: production"
nav_order: 3
---

# Day 46 posts: LinkedIn and X

The scoreboard makes a good screenshot: a well-behaved tenant served 20/tick, then 3.4/tick under a neighbour's flood, then 20/tick again once a quota goes in, with the greedy tenant pinned at 20. Swap in your own numbers and voice.

## LinkedIn

Day 46 of 60 days of system design. Today was the noisy neighbour, and I measured how much one greedy customer can steal from everyone else on a shared system.

The setup: one shared resource that serves 120 requests per tick, split across 6 tenants. An even share is 20 each. When everyone behaves, demand equals capacity and nobody is starved.

Then one tenant floods the pool with 600 requests per tick instead of 20. A shared queue serves whoever fills it, so service goes roughly in proportion to how much each tenant asks for. Here is what a well-behaved tenant, which changed nothing, got:

    behaving, shared quietly:   20 / tick
    one neighbour floods:      3.4 / tick

Its throughput fell by over 80 percent. It did nothing wrong. The greedy tenant alone ate 103 of the 120, about 86 percent of a resource it was entitled to one sixth of. That is the noisy neighbour, and in a real system it is one customer taking down the experience for all the others.

The fix is isolation. I put a token bucket (the same rate limiter from Day 45) in front of each tenant at its fair share of 20 per tick. Re-run the exact same flood:

    well-behaved tenant:  back to 20 / tick
    greedy tenant:        capped at 20 / tick (the other 580 rejected at the door)

The flood is turned away before it reaches the shared pool, so the pool is never overloaded and the quiet tenants are whole again.

The honest footnote: a hard quota is simple but wastes a tenant's unused share. Fair-share scheduling (max-min, what weighted fair queuing approximates) hands idle capacity to whoever is hungry while still guaranteeing everyone their share. Most real systems run both.

And there is a spectrum. Shared everything is cheapest with the worst isolation. Shared with per-tenant quotas is the usual middle. Dedicated resources per tenant give the best isolation and the biggest bill, because idle capacity in one box cannot help another. That cost is tomorrow's problem.

Isolation is not a feature you bolt on later. It is the line between one bad tenant and all of your tenants sharing the pain.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #multitenancy #saas #learninginpublic

## X thread

**1/**

One greedy customer can quietly starve all your others on a shared system. I measured it today.

Shared pool, 120 req/tick, 6 tenants, fair share 20 each.

A well-behaved tenant, when one neighbour floods:

behaving:  20/tick
flood on:  3.4/tick

Day 46 of 60 days of system design.

**2/**

This is the noisy neighbour.

A shared queue serves whoever fills it, so capacity goes roughly in proportion to demand. Flood with 600/tick and you get the lion's share.

The greedy tenant ate 103 of the 120, about 86% of a pool it was owed one sixth of.

**3/**

The quiet tenant changed nothing. Its throughput dropped over 80% and its extra requests pile up and time out. One customer, everyone else's problem.

**4/**

The fix: isolation.

Put a token bucket (Day 45's rate limiter) in front of each tenant at its fair share of 20/tick. Re-run the same flood:

quiet tenant: back to 20/tick
greedy:       capped at 20/tick, other 580 rejected at the door

**5/**

Footnote: a hard quota wastes a tenant's unused share.

Fair-share scheduling (max-min, what weighted fair queuing chases) lends idle capacity to the hungry while still guaranteeing everyone their share. Real systems run both.

**6/**

The spectrum:

shared, no limits: cheap, zero isolation
shared + quota:    the usual middle
dedicated/tenant:  best isolation, biggest bill (idle capacity can't be shared)

Isolation is the line between one bad tenant and all your tenants in pain.

Code: github.com/anurag629/system-design-60-days
