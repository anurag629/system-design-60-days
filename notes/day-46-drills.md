---
title: "Day 46 drills"
parent: "Day 46: multi-tenancy and isolation"
grand_parent: "Week 7: production"
nav_order: 2
---

# Day 46 drills

Written on paper first. The noisy neighbour, fair shares, quotas, and the cost of isolation. Numbers before prose.

D1 (a shared pool serves 120 req/tick across 6 tenants; five ask for 20 each, the greedy one floods with 600. Under proportional service, how many req/tick does a quiet tenant get, what fraction of its demand is that, and how much does the greedy tenant get):

D2 (you put a token bucket in front of every tenant at the fair share. What rate do you set, how many of the greedy tenant's 600 req/tick now reach the pool, and what does the quiet tenant's served rate become? Where do the rejected requests go):

D3 (one quiet tenant goes idle and sends nothing. Under a hard quota at the fair share, how much of the 120-capacity pool is actually used and what is wasted? Under max-min fair scheduling, where does the idle tenant's share go, and which property is the fair scheduler buying you):

D4 (rank the three models, shared-everything, shared-with-quota, dedicated-per-tenant, by isolation and by cost. For the dedicated model, why can idle capacity in one tenant's box not help a busy neighbour, and what does that do to the bill as the tenant count grows):

D5 (a metrics SaaS runs 1,000 tenants on one shared ingestion pipeline sized for the aggregate. One tenant 100x's its write rate after a bad deploy. Without isolation, what do the other 999 tenants experience? Name the first control you would add and say whether it sits at admission or in the scheduler, and name one per-tenant metric that would have caught it early):
