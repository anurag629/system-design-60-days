---
title: "Day 14 drills"
parent: "Day 14: designing a storage layer"
grand_parent: "Week 2: storage"
nav_order: 2
---

# Day 14 drills

Written on paper first, with numbers. The storage layer for a messaging app, broken into its decisions.

D1 (scale: messages/sec, data per day and year, one machine or many):

D2 (engine: B-tree or LSM for an append-only message firehose, and why):

D3 (hot query "last 50 in this chat": partition by, order by, offset or keyset):

D4 (shard key and the hot partition: the 50M-member broadcast channel):

D5 (replication: the one read that cannot be served stale, and how):
