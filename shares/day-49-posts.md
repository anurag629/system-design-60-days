---
title: "Day 49 posts"
parent: "Day 49: designing a multi-tenant SaaS"
grand_parent: "Week 7: production"
nav_order: 3
---

# Day 49 posts: LinkedIn and X

The angle is that multi-tenancy is a trust and operability problem, not a schema one. Swap in your own voice.

## LinkedIn

Day 49 of 60 days of system design, end of week 7, production. I designed a multi-tenant SaaS today, and almost none of it was about the database.

A multi-tenant system is one system pretending to be a separate one for each customer. You share resources to save money, and then you spend the whole design making sure the sharing never leaks. There are three leaks, and each was a day this week.

Data: tenant A must never see tenant B's rows. In a shared table that comes down to a tenant_id filter on every query, and the nightmare is the one query that forgets it and returns everyone's data. The fix is to stop relying on memory: enforce the tenant scope in the database (row-level security) or a data layer that injects it automatically, so the safe thing is the automatic thing.

Performance: one tenant running a giant report must not slow everyone else. That is the noisy neighbour, and quotas plus fair scheduling cap the greedy one at its own share while the rest stay fast.

Cost: one tenant must not quietly run up a bill the others subsidise, which needs per-tenant cost attribution so you actually know who is expensive.

And the part that makes it operable: every metric and log carries the tenant id. When the pager says "the app is slow" at 3am, the only question that matters is "everyone, or one tenant", and you can only answer it if your dashboards are sliced by tenant. A fleet average of 99.95 percent can hide one customer at 98 percent who is about to churn.

The lesson of the whole week: the happy path is the easy 20 percent. Observability, SLOs, isolation, rate limiting and cost are the other 80, and they are what separate a diagram from a system you can run.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #saas #reliability #learninginpublic

## X thread

**1/**

Day 49, end of week 7 (production) of 60 days of system design. I designed a multi-tenant SaaS, and almost none of it was about the database.

**2/**

Multi-tenancy is one system pretending to be separate for each customer. You share for cost, then spend the design making sure sharing never leaks. Three leaks, three days this week:

**3/**

Data: tenant A must never see B's rows. The nightmare is one query missing its tenant_id filter. Fix: enforce the scope in the database (row-level security) or a data layer that injects it, so the safe thing is automatic, not "remember to add WHERE".

**4/**

Performance: one tenant's giant report must not slow everyone. Noisy neighbour. Quotas + fair scheduling cap the greedy tenant at its share.

Cost: per-tenant attribution, so the cheap plan isn't subsidising a heavy user.

**5/**

And operability: every metric and log carries the tenant id. At 3am "the app is slow", the only question is "everyone or one tenant", and a 99.95% average hides the one customer at 98% about to churn.

The happy path is the easy 20%. Production is the other 80.

Code: github.com/anurag629/system-design-60-days
