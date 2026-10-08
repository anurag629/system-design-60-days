---
title: "Day 22 drills"
parent: "Day 22: sync vs async, and why queues exist"
grand_parent: "Week 4: async, queues and the log"
nav_order: 2
---

# Day 22 drills

Written on paper first. Sync vs async, queue depth, Little's Law, and backpressure.

D1 (a request does four slow side effects inline: charge card 120 ms, notify restaurant 80 ms, find a rider 200 ms, send SMS 60 ms; user-visible latency synchronously, vs enqueue-and-return with one serial worker; what changed and what did not):

D2 (latency vs throughput: making the caller async did not make the work faster; define both, say why a queue plus one worker slashes caller latency but not throughput, when adding workers raises throughput, and what sets the ceiling):

D3 (queue depth: arrivals lambda = 100/sec, one worker serves mu = 50/sec, what happens to depth over time; then lambda = 30/sec, mu = 50/sec, is it stable, and why does an unbounded queue hide the lambda > mu problem; Little's Law L = lambda x W for intuition):

D4 (a bounded queue of maxsize M is full and a producer calls put(): the three things the queue can do, a real system for each, and what the producer should do in each case):

D5 (async plus a queue is not free: two concrete costs it adds, and one kind of operation where the synchronous answer is the right one):
