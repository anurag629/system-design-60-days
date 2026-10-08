---
title: "Day 48 drills"
parent: "Day 48: cost and capacity planning"
grand_parent: "Week 7: production"
nav_order: 2
---

# Day 48 drills

Paper first, with the arithmetic shown. Capacity by Little's Law, then the bill, then the lever. Every one is a multiply, a divide, and an add.

D1 (12,000 rps, 15 ms per request, 4 slots a server: requests in flight at peak, servers for the load at 70% busy, and the final count with one N-minus-1 spare):

D2 (same service, the database slows each request from 15 ms to 25 ms: recompute the fleet at 70% plus a spare, say why unchanged traffic needs more servers, and what Day 4's cliff says about just running the old fleet hotter instead):

D3 (40 servers at $0.50/hr for 730 hrs, 50 TB storage at $0.08/GB, 80 TB egress at $0.09/GB: each line, the total, the dominant line and its share, and how this differs from the lab's egress-dominated bill):

D4 (the lab's $27,046 bill with $18,000 egress at $0.09/GB for 200 TB: new egress line and new total if a CDN serves all 200 TB at $0.06/GB with free origin-to-CDN transfer, the percent saved, and why a CDN cuts the bill even without a much lower per-GB rate):

D5 (10 servers, 100 rps each at 100% busy, 650 rps peak: utilisation at peak, then after one server dies, then after two, and why "we are only at 65%, loads of headroom" is dangerous on its own):
