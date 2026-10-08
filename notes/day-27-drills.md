---
title: "Day 27 drills"
parent: "Day 27: backpressure and load shedding"
grand_parent: "Week 4: async, queues and the log"
nav_order: 2
---

# Day 27 drills

Written on paper first. Little's Law from Day 4, queue depth, backpressure, and load shedding. Use `wait = depth / drain_rate` and `L = λ × W`. Nothing else is needed.

D1 (producer offers 500 jobs/sec, consumer drains 300/sec, unbounded queue: how many jobs are backed up after 10 minutes, how long does a job joining the back wait to be picked up, and what happens to that wait as time goes on):

D2 (consumer handles 200 jobs/sec and your SLA allows at most 300 ms of queueing delay: how big should you cap the queue, and what does capping it at 10,000 "to be safe" do to the worst-case wait):

D3 (a request handler puts a job on a bounded in-process queue that a worker pool drains; the queue fills and put() blocks: walk the chain of what blocks next, all the way to the user, and say when a blocked producer is worse than a dropped request):

D4 (requests arrive at 1,000/sec, the service handles 400/sec, you shed the excess with a 429 that costs about 1% of the work of serving one: how many 429s per second, how much capacity does shedding burn, and why does the fast "no" keep the system alive):

D5 (for each, pick block/backpressure or shed/429 and say why: an internal batch ETL reading from Kafka, a user-facing checkout API in a flash sale, a logging and metrics pipeline, a payment webhook receiver):
