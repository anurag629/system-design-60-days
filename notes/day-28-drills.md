---
title: "Day 28 drills"
parent: "Day 28: designing a notification system"
grand_parent: "Week 4: async, queues and the log"
nav_order: 2
---

# Day 28 drills

Written on paper first, with numbers. The notification system, broken into its decisions.

D1 (scale: notifications/sec, a broadcast to 100M, drain time, is it real-time):

D2 (duplicate email on retry: the fix, what the idempotency key is made of, where you check it):

D3 ("order shipped" dual write: what breaks on a crash, which week-4 pattern fixes it):

D4 (SendGrid slow hour: why per-channel queues, what happens to the backlog, where failures end up):

D5 (APNs rate limit vs 10M queued pushes: throttle or shed, which day, why notifications are throttled):
