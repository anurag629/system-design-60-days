---
title: "Day 49: designing a multi-tenant SaaS"
parent: "Week 7: production"
nav_order: 7
has_children: true
---

# Day 49
## Designing a multi-tenant SaaS, where every tenant shares the system but must never feel it 🏢

Today's one idea: a multi-tenant SaaS is one system pretending to be a separate one for each customer. The whole design is about sharing resources for cost while guaranteeing that no tenant can see another's data, slow another down, or spend another's budget. Every guarantee is a week-7 day: isolation (Day 46), authorization (Day 47), quotas and rate limits (Day 45), per-tenant observability and SLOs (Days 43 and 44), and the cost of it all (Day 48).

This is the week 7 finale, a design day. You design a B2B SaaS on paper, against the clock, with the production concerns baked in from the start rather than bolted on when it is already on fire.

---

## Before you start ⏪

Bring all of week 7. Day 43 (observability, now with a tenant dimension), Day 44 (SLOs and error budgets, now per tenant), Day 45 (rate limiting, now per tenant), Day 46 (the noisy neighbour, which is the central villain of multi-tenancy), Day 47 (authorization, where a missing tenant check is a cross-tenant data leak), Day 48 (cost, which is the entire reason you share resources at all). And earlier weeks: sharding (week 2), caching (week 3), stateless services behind a balancer (Day 6).

---

## Words you will meet today 📖

A tenant is one customer organisation: a company, a team, an account, with its own users and its own data, sharing your system with every other tenant.

Tenant isolation is the promise that one tenant cannot access, affect, or even notice another: not their data (security), not their performance (the noisy neighbour), not their costs.

The pool model shares resources across all tenants (one database, one app fleet), separated by a tenant id. Cheapest, but isolation is your job to enforce in software.

The silo model gives a tenant dedicated resources (its own database, maybe its own fleet). Strong isolation, high cost, usually reserved for big or compliance-bound tenants.

The bridge model is the middle: shared infrastructure with a per-tenant boundary inside it, such as a schema per tenant in a shared database.

Tenant context is the tenant id carried on every request, the thing every query, quota, metric and authorization check keys off.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [SaaS Lens: tenant isolation](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html) from the AWS Well-Architected SaaS Lens. The canonical treatment of silo, pool and bridge and how to isolate tenants properly.
- [Avoiding overload by putting the smaller service in control](https://aws.amazon.com/builders-library/avoiding-overload-in-distributed-systems-by-putting-the-smaller-service-in-control/) from the AWS Builders' Library. The noisy-neighbour and overload problem (Days 45 and 46) from people who run it.
- [SLOs](https://sre.google/sre-book/service-level-objectives/) from the Google SRE book, re-read with a tenant lens: in a SaaS, you often owe each tenant an SLO, and the error budget is per tenant.

Watch, after you have done your own design:
- [Multi-tenancy isn't about databases](https://www.youtube.com/watch?v=4_pxeE1Xv3Q) by CodeOpinion, about 12 minutes. The right framing: isolation is a system concern, not a schema trick.
- Optional, deeper: [AWS re:Invent, SaaS tenant isolation patterns](https://www.youtube.com/watch?v=fuDZq-EspNA), about 52 minutes.

### Share for cost, isolate for trust (15 min)

Multi-tenancy exists for one reason: cost (Day 48). Giving every customer their own dedicated stack is simple and perfectly isolated, and it is also ruinously expensive, because a tiny tenant that uses almost nothing still pays for a whole database instance. So you share. The entire discipline of multi-tenancy is sharing resources to save money without letting the sharing leak.

There are three leaks to prevent, and they map to three week-7 days. The first is data: tenant A must never see tenant B's rows. This is authorization (Day 47) at every data access, and the nightmare is a single query that forgot its tenant filter and now returns everyone's data. The second is performance: tenant A running a monstrous report must not slow tenant B to a crawl. This is the noisy neighbour (Day 46), fixed with per-tenant quotas, rate limits (Day 45) and fair scheduling. The third is cost: one tenant must not quietly run up a bill the others subsidise, which needs per-tenant cost attribution (Day 48).

The practical answer is almost never pure silo or pure pool. It is tiered: pool by default, so most tenants share cheaply with quotas keeping them in line, and silo the few that need it, the giant enterprise, the tenant with a compliance requirement that demands physical separation. The follower count from the feed design has a cousin here: most tenants are small and share happily, a few are huge and get their own everything.

### Run it like you are on call at 3am (10 min)

The other half of production is operability, and multi-tenancy raises the stakes. When the pager goes off with "the app is slow", your first question is the one that only tenant-aware observability can answer: is it everyone, or is it one tenant? Without a tenant dimension on your metrics and logs (Day 43), you cannot tell, and you will waste the outage guessing. With it, you see instantly that tenant 4471 is hammering one endpoint, and you throttle them instead of scaling the whole fleet.

So every signal carries the tenant id. Metrics are sliced by tenant, so you can see one tenant's error rate and latency. Logs are structured with a tenant field (Day 43), so you can filter to one customer's requests. SLOs and error budgets are tracked per tenant (Day 44), because you owe each customer a number, and a healthy fleet average can hide one tenant whose budget is on fire. This is what separates a SaaS you can operate from one that owns you.

---

## Block 2: drill (40 min) ✍️

Paper first. Write your answers into [`notes/day-49-drills.md`](../notes/day-49-drills.md). About 8 minutes each.

D1. The isolation spectrum. Describe silo, pool and bridge, and the cost-versus-isolation tradeoff of each. Which would you put a free-tier tenant on, and which would you put a large enterprise customer with a data-residency compliance requirement on, and why?

D2. The cross-tenant leak. In the pool model every tenant's rows live in one table separated by tenant_id. Describe how a single query that forgets its tenant_id filter becomes a cross-tenant data breach (this is Day 47's IDOR at scale). Then give a structural fix that does not rely on every developer remembering to add the filter.

D3. The noisy neighbour. One tenant kicks off a huge export that saturates the shared worker pool, and every other tenant's requests slow to a crawl (Day 46). What two mechanisms contain this so the well-behaved tenants keep their performance, and what do you cap the greedy tenant at?

D4. Operability at 3am. The pager says the app is slow. What single property of your metrics and logs lets you answer "is it everyone or one tenant" in seconds (Day 43), and why does a per-tenant SLO and error budget (Day 44) catch problems a fleet-wide average hides?

D5. Cost and tiering. Pooling saves money, but how do you find out which tenant is actually expensive, so a cheap plan is not subsidising a heavy user (Day 48)? And what signals tell you a tenant has grown big enough to deserve its own silo?

---

## Block 3: build (100 min) 🔧

Today you build a design, not code. The template is [`labs/day-49-saas/DESIGN.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-49-saas/DESIGN.md). Copy it into your fork and fill it in.

Do it against the clock, 45 minutes for a first full pass: requirements, the isolation model (and tiering), how data isolation is enforced, how the noisy neighbour is contained, per-tenant observability and SLOs, and cost and attribution. Do not open the Solutions or the readings until your 45 minutes are up.

Then improve it with the readings open, marking what you added. That delta is week 7 landing.

### What a strong design has

A weak one says "add a tenant_id column." A strong one picks an isolation model and tiers it, enforces the tenant filter structurally so a forgetful query cannot leak data, contains the noisy neighbour with quotas and fair scheduling, puts a tenant dimension on every metric and log so it is operable at 3am, tracks per-tenant SLOs, and can attribute cost per tenant. Aim for that.

### Deliverable

Your filled-in `DESIGN.md`, and one honest paragraph: which week-7 day is the one you would least want to get wrong in production, and why.

---

## Block 4: write (30 min) 📣

Your angle is the realisation that multi-tenancy is a trust problem, not a schema problem: "I designed a multi-tenant SaaS, and almost none of it was about the database. It was about making sure one tenant can never see another's data, slow another down, or spend another's budget, and about being able to tell at 3am whether it is everyone or just one customer." Pick the two that landed hardest.

Example posts are on the [Day 49 posts](../shares/day-49-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it, and look back 📝

Log the three: what you completed, the isolation model you chose and why, and one thing you still cannot explain.

Then the week 7 retrospective. Think back to the start of the week. Write down the three production concerns you now treat as part of the design rather than afterthoughts (observability, SLOs, isolation, rate limiting, cost, pick three), and the one you would still forget under pressure. Naming it is how you stop forgetting it.

Week 8 is the finish: no new theory, just synthesis. A couple of days on how to run a design interview cleanly, then timed mock designs, then a capstone you build, break and write up. Seven weeks of measuring and building have quietly turned into judgement. Next week you prove it.

---

## Solutions 🔑

Open these only after your own 45-minute design pass.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Silo gives each tenant dedicated resources (its own database, maybe its own fleet): the strongest isolation, the simplest mental model, and the highest cost, since even a tiny tenant pays for a whole stack. Pool shares one set of resources across all tenants, separated by tenant_id: the cheapest, but isolation is entirely your software's job to enforce. Bridge is the middle, shared infrastructure with a per-tenant boundary inside, such as a schema per tenant. A free-tier tenant goes on the pool: it uses almost nothing, and paying for a silo per free user would bankrupt you. A large enterprise with a data-residency compliance requirement goes on a silo: it can afford it, and "your data is in its own database in its own region" is often a contractual requirement, not a preference. Most SaaS tier this: pool for the many, silo for the few.

D2. In the pool model, every tenant's rows share a table and are separated only by a tenant_id column, so correctness depends on every single query including "WHERE tenant_id = :me". A query that forgets it (a new endpoint, a reporting join, an admin tool) returns rows across all tenants, which is a cross-tenant data breach, the Day 47 IDOR at the scale of your whole customer base. The structural fix is to not rely on developers remembering: enforce the tenant scope below the application code, for example with row-level security in the database (the database itself refuses to return rows outside the current tenant), or a data-access layer that automatically injects the tenant filter on every query, or in the silo/bridge model physical separation so a cross-tenant query is impossible by construction. The rule: make the safe thing automatic, because "remember to add the filter" fails the one time it matters.

D3. Per-tenant quotas or rate limits (Day 45) cap how much of the shared capacity any one tenant can consume, so the greedy tenant is throttled at its own limit rather than eating everyone's share. Fair scheduling (Day 46), serving tenants round-robin rather than first-come-first-served, ensures the flood of one tenant's jobs does not starve the others waiting behind them. You cap the greedy tenant at its fair share (or its plan's quota), so its big export runs slowly within its own budget while every other tenant keeps full performance. Isolation of performance, not just data.

D4. The single property is a tenant dimension on every metric and log (Day 43): metrics sliced by tenant and logs carrying a structured tenant field, so you can ask "show me latency and error rate for each tenant" and instantly see whether the slowness is fleet-wide or one customer. Without it you are blind to the one-tenant case and will waste the outage scaling the wrong thing. A per-tenant SLO and error budget (Day 44) catches what an average hides: the fleet can be at a healthy 99.95 percent while one tenant is at 98 percent and furious, because their pain is averaged away across everyone else. Per-tenant budgets make one suffering tenant visible instead of drowned in the mean (the Day 1 and Day 4 tail lesson, applied to customers).

D5. You find the expensive tenant with per-tenant cost attribution (Day 48): tag resource usage (compute time, storage, egress, requests) with the tenant id and sum it per tenant, so you can see that tenant 4471 on the cheap plan is using 40 percent of the cluster. Without attribution, pooling hides who is costing what, and your cheapest plan silently subsidises your heaviest user. A tenant deserves its own silo when its usage is large enough that dedicated resources are cheaper or safer than its share of the pool, when it is causing noisy-neighbour problems that quotas cannot fully tame, or when a compliance or performance guarantee in its contract requires physical separation. The trigger is a number (its cost or load share), not a feeling.

</details>

<details markdown="1">
<summary>A worked reference design</summary>

One good answer. Yours will differ; what matters is that isolation, operability and cost are designed in, not added later.

Requirements. Functional: a B2B SaaS where many customer organisations (tenants), each with users and data, use one system. Non-functional: strict data isolation between tenants, performance isolation (no noisy neighbour), per-tenant SLOs, operability (debuggable per tenant at 3am), and cost efficiency.

Isolation model: tiered. Pool by default (shared database and app fleet, separated by tenant_id) for the many small tenants, because it is the only affordable option at scale. Silo (dedicated database, possibly dedicated region) for large or compliance-bound tenants. This is the follower-count pattern again: most are small and share, a few are huge and get their own.

Data isolation, from D2: enforce the tenant scope below the application, with database row-level security or a data-access layer that injects the tenant filter automatically, so a forgotten filter cannot leak data. Tenant context (the tenant id) rides every request from the gateway inward.

Performance isolation, from D3: per-tenant rate limits (Day 45) and quotas at the gateway, and fair scheduling across tenants in the shared worker pools (Day 46), so one tenant's flood is capped at its own share and the rest are untouched.

Operability, from D4: every metric is sliced by tenant and every log carries a tenant field (Day 43); SLOs and error budgets are tracked per tenant (Day 44), so one unhappy tenant is visible instead of averaged away.

Cost, from D5: per-tenant cost attribution (Day 48) tags usage by tenant, so you know who is expensive, can price plans honestly, and can decide by a number when a tenant should move to a silo.

The sentence that makes this sound senior: "pool for cost with the tenant filter enforced in the database not the code, quotas and fair scheduling so no tenant is a noisy neighbour, a tenant dimension on every signal so I can tell at 3am if it is one customer or all, and cost attribution so the cheap plan is not subsidising the heavy user."

</details>

<details markdown="1">
<summary>Week 7 in one page</summary>

Seven days of the unglamorous plumbing that separates a diagram from a system you can run.

Day 43, observability. Logs, metrics and traces. Alert on p99 not the mean, because the average hides the tail; structured logs are queryable; a trace finds the one slow span in a fan-out.

Day 44, SLOs and error budgets. Reliability as a number you can spend. 100 percent is the wrong goal; the error budget is what lets you ship, and dependencies multiply downward.

Day 45, rate limiting. Token bucket for friendly bursts, leaky bucket for a steady drain, and the fixed-window trap that lets 2x through at the boundary. The polite "no" that protects you.

Day 46, multi-tenancy and isolation. The noisy neighbour starves everyone through a shared resource; quotas and fair scheduling contain one greedy tenant.

Day 47, security boundaries. Authentication is who you are, authorization is whether you may do this, and a valid token is not permission. Sign requests, block replays, check ownership to stop IDOR.

Day 48, cost and capacity. Size for about 70 percent, turn the architecture into a monthly bill, find the dominant line item, and pull one lever to cut it.

Day 49, today. A multi-tenant SaaS with all of it designed in.

If you now reach for observability, SLOs, quotas, authorization and a cost estimate as part of the design rather than as a later cleanup, you learned the real lesson of week 7: the happy path is the easy 20 percent, and production is the other 80. Week 8 is where you put all eight weeks together.

</details>
