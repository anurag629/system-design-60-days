---
title: "Day 12 drills"
parent: "Day 12: replication and lag"
grand_parent: "Week 2: storage"
nav_order: 2
---

# Day 12 drills

Written on paper first. Leader and follower, lag, and the stale read.

D1 (user posts a comment, write hits the leader, UI reads it back from a follower 50 ms behind: why is the comment missing, and the smallest fix that does not make the user wait):

D2 (leader takes 2,000 writes/sec, a follower applies 1,500/sec: what happens to the lag during a 10-second burst, and roughly how long to catch up after the burst stops):

D3 (leader in Mumbai, follower in Singapore, 60 ms round trip: async write latency vs synchronous write latency, and what happens to writes under each mode when the Singapore follower goes down):

D4 (async replication, the leader crashes with 200 ms of writes not yet sent, a follower is promoted: what happens to those writes, and what would sync replication change and cost):

D5 (for each read, say follower-is-fine, must-read-leader, or must-wait: your own just-posted comment; a stranger's comments from last week; your bank balance right after a transfer; a dashboard of yesterday's signups):
