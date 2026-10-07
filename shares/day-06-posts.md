---
title: "Day 6 posts"
parent: "Day 6: more than one server"
grand_parent: "Week 1: ground truth"
nav_order: 3
---

# Day 6 posts: LinkedIn and X

Written with the reference run's numbers. These wobble between runs because the lab is real threads and sockets, so swap in your own. Attach the Part 2 three-row table as a screenshot.

## LinkedIn

Day 6 of 60 days of system design. I ran three real web servers behind a real load balancer, pointed 20 concurrent clients at it, and then killed one server 1.5 seconds in. On purpose. Three times.

Same crash each time. The only thing I changed was how smart the balancer was.

    no health check, no retry       1,724 requests failed, and they never stopped
    health check every 200 ms          99 failed, errors stopped after ~150 ms
    health check + retry                9 failed

With no health check the balancer never finds out the server is dead, so it keeps sending one in three requests into a corpse, forever. A health check pulls the dead server out about one probe-interval after it dies, so the errors stop. Retry sends a failed request to a healthy server before the user ever sees an error.

The failure was never the interesting part. Servers die. Whether anyone notices comes down to two questions: does the balancer find out, and does it try someone else.

Then I made one server 6x slower and raced two algorithms. Round robin kept calmly sending it a third of all traffic, where it queued up. Least connections watched the slow server hoard requests and routed around it. Least connections finished 1.6x more work on the exact same hardware.

That is yesterday's queue lesson again: do not shove work at the server that cannot keep up.

Code is public, three servers and a balancer in about 200 lines of standard-library Python: github.com/anurag629/system-design-60-days

#systemdesign #reliability #learninginpublic

## X thread

**1/**

I put 3 real servers behind a real load balancer and killed one mid-traffic. Same crash, three setups:

no health check: 1,724 requests failed, forever
health check: 99 failed, stopped in ~150 ms
health check + retry: 9 failed

Day 6 of 60 days of system design.

**2/**

With no health check the balancer never learns the server is dead. It keeps routing 1 in 3 requests into a dead socket until the end of time.

A health check is just the balancer asking "you alive?" on a timer and pulling out whoever stops answering.

**3/**

Retry is the second half. A failed request quietly gets sent to a different, healthy server before the user sees anything.

One rule from Day 5: only retry what is safe to retry. Retrying a read is free. Retrying "charge the card" without an idempotency key charges twice.

**4/**

Then I made one backend 6x slower and raced the algorithms.

round robin:       1,972 requests done
least connections: 3,157 requests done

Round robin keeps feeding the slow server a third of traffic. Least connections routes around it. 1.6x more work, same hardware.

**5/**

The whole day in one line: servers dying is not the problem, it is a certainty.

The job of the thing in front of them is to notice fast and try someone else. 1,724 failures vs 9, same crash.

Code: github.com/anurag629/system-design-60-days
