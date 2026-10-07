---
title: "Day 6 drills"
parent: "Day 6: more than one server"
grand_parent: "Week 1: ground truth"
nav_order: 2
---

# Day 6 drills

Written on paper first. Load balancing, health checks and statelessness. D5 brings back Day 4's latency = work / (1 - utilization).

D1 (4 servers at 100 req/s, peak 300 then 350, one dies):

D2 (30 s health check interval, crash just after a check: window and fail fraction):

D3 (cart in server memory, add a second server: what breaks, two fixes):

D4 (3 backends, one hits a 2 s GC pause: round robin vs least connections):

D5 (10 servers at 70%, one dies: new utilization and latency; then at 90%):
