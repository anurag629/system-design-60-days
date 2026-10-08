---
title: "Day 49 design template"
parent: "Day 49: designing a multi-tenant SaaS"
grand_parent: "Week 7: production"
nav_order: 1
---

# Day 49: design a multi-tenant SaaS

Fill this in against the clock, 45 minutes for a first full pass, before you open the Solutions or the readings. Then improve it with the readings and mark what you added.

## 1. Requirements

Functional (tenants, users, data):

Non-functional (data isolation, performance isolation, per-tenant SLOs, operability, cost):

## 2. Isolation model

Silo, pool, or bridge, and your tiering (who goes where and why):

## 3. Data isolation

How a tenant's data is kept separate, and the structural fix so a forgotten tenant filter cannot leak (Day 47):

## 4. Performance isolation (the noisy neighbour)

How one greedy tenant is contained: quotas, rate limits, fair scheduling (Days 45, 46):

## 5. Operability

Tenant dimension on metrics and logs (Day 43); per-tenant SLOs and error budgets (Day 44); answering "everyone or one tenant" at 3am:

## 6. Cost and tiering

Per-tenant cost attribution (Day 48), and the signal that a tenant should move to a silo:

## Reflection

The week-7 day I would least want to get wrong in production, and why:
