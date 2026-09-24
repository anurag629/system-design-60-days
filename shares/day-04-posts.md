---
title: "Day 4 posts"
parent: "Day 4: latency, throughput and the queue"
grand_parent: "Week 1: ground truth"
nav_order: 3
---

# Day 4 posts: LinkedIn and X

Written with the reference run's numbers. Part 1 of the lab is a simulation, so your numbers should land close to these; swap in yours anyway. The numbers in square brackets are your predictions. Attach the part 1 table as a screenshot, or better, a photo of the curve you drew by hand.

## LinkedIn

Day 4 of 60 days of system design. I simulated one server with a queue in front of it at different levels of busy, and watched what happened to latency.

Each request needs 10 ms of work. The server can do 100 per second.

    50% busy    average latency     20 ms
    80% busy                        50 ms
    90% busy                        98 ms
    95% busy                       221 ms
    99% busy                     1,224 ms

From 90% to 99% busy is only 10% more traffic. Latency got 12 times worse.

Nothing broke. No code changed. The server just ran out of slack. Requests arrive at random, so they come in clumps, and the only thing that drains a clump is idle time. At 99% busy there's almost none left.

I predicted [your 99% guess] ms. I think most of us picture load and latency as a straight line. It's a wall.

The second result surprised me more. Same traffic at 90 requests per second, but two servers sharing one queue. I guessed [your two-server guess] ms, figuring twice the servers means half the latency. It was 12.5 ms. Eight times better, because each server is now only 45% busy, far from the wall.

Then I checked Little's Law with a real worker thread: requests inside the system = arrival rate × average latency. A thread peeking every 2 ms counted 7.00 requests in the system. The formula said 6.99.

This is why production systems are planned for 60 to 70% busy, and why a slow database can take down every service that calls it.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #performance #learninginpublic

## X thread

**1/**

One server, 10 ms of work per request. I simulated it at different load:

50% busy → 20 ms
90% busy → 98 ms
99% busy → 1,224 ms

90% to 99% is 10% more traffic and 12x the latency. Day 4 of 60 days of system design.

**2/**

Why? Random arrivals come in clumps. Only idle time drains a clump, and a server can't save up idle time for later.

The closer you get to 100% busy, the less idle time there is. The textbook formula: latency = work / (1 - utilization).

**3/**

My favourite result: same 90 req/s, two servers sharing one queue.

I guessed [your guess] ms. Actual: 12.5 ms.

Not half of 98. Eight times better. You're not buying speed. You're buying distance from the wall.

**4/**

Averages lie, too. At 90% busy the average was 98 ms and the p99 was 481 ms.

One request in a hundred took 5x the average. That's the one your users tweet about.

**5/**

Little's Law, checked with real threads: requests in system = arrival rate × latency.

Counted: 7.00. Formula: 6.99.

The one queueing formula worth memorising.

Code: github.com/anurag629/system-design-60-days
