---
title: "Day 49 drills"
parent: "Day 49: designing a multi-tenant SaaS"
grand_parent: "Week 7: production"
nav_order: 2
---

# Day 49 drills

Written on paper first. The multi-tenant SaaS, broken into its decisions.

D1 (isolation spectrum: silo vs pool vs bridge, and who you put on each):

D2 (cross-tenant leak: how a missing tenant_id filter breaches data, and the structural fix):

D3 (noisy neighbour: two mechanisms to contain one greedy tenant, and what you cap it at):

D4 (3am operability: the property that answers "everyone or one tenant", and why per-tenant SLOs):

D5 (cost and tiering: finding the expensive tenant, and the signal to move it to a silo):
