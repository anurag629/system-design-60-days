# Week 7: production, or what happens after you ship 🛠️

Days 43 to 49.

Anyone can draw boxes and arrows. This week is about the difference between a design and a system that actually runs at 3 AM when something breaks and you are on call. This is the week that separates the people who "know system design" from the people companies actually pay well.

Think of it this way. In week 8 you will do mock interviews, and the candidates who stand out are not the ones who name the most technologies. They are the ones who, after drawing the happy path, calmly say "now, how do we know it is working, what happens when this piece fails, what stops one customer from hogging everything, and what does this cost per month?" That calm is what this week builds.

None of this is glamorous. There are no clever algorithms here. It is observability, error budgets, rate limiting, isolation, security basics, and cost. It is the plumbing. But a house is mostly plumbing you never see, and you notice immediately when it is missing.

## What you will be able to do by Sunday

You can instrument a service so that when it misbehaves you can actually see why, using logs, metrics and traces. You can define an SLO and compute an error budget, and explain why 100% uptime is the wrong goal. You can implement a token bucket rate limiter, the exact thing standing between IRCTC and total collapse every tatkal morning. You can look at a design and estimate the monthly cloud bill, which turns architecture debates from opinion into arithmetic.

## The days 🗓️

Day 43: observability. Logs, metrics and traces, and the difference between them. The RED method for requests and the USE method for resources. Lab: instrument a small service and expose real metrics you can watch move.

Day 44: SLOs and error budgets. What "three nines" costs you in real downtime, and why chasing 100% makes your system slower and your team miserable. Lab: compute an SLO and an error budget from a stream of request data.

Day 45: rate limiting and load shedding. Token bucket, leaky bucket, and gracefully saying "no" before you fall over. This is the IRCTC tatkal problem in its purest form. 🚆 Lab: implement token bucket and leaky bucket and watch them protect a service under a flood.

Day 46: multi-tenancy and isolation. The noisy neighbour problem, where one greedy customer degrades everyone else, and the quotas and fairness that stop it. Lab: simulate a noisy neighbour, then add per-tenant quotas.

Day 47: security boundaries, the parts that touch design. Authentication vs authorisation, where secrets live, and signing requests so they cannot be forged. Not a full security course, just what every design must get right. Lab: sign and verify a request with HMAC, and see how a tampered request gets caught.

Day 48: cost and capacity planning. Reading a cloud bill, right-sizing, and the arithmetic that tells you whether your design is affordable before you build it. Lab: build a small cost model for a real-ish system.

Day 49: production design. You design a multi-tenant SaaS or an on-call-friendly system, timed, with observability and cost baked in from the start, then a retro.

## Core resources for the week 📚

Read:
- [Google SRE book](https://sre.google/books/): the chapters on [embracing risk](https://sre.google/sre-book/embracing-risk/), [SLOs](https://sre.google/sre-book/service-level-objectives/), and [monitoring](https://sre.google/sre-book/monitoring-distributed-systems/).
- [AWS Builders' Library](https://aws.amazon.com/builders-library/): the essays on load shedding, timeouts and health checks.
- [Marc Brooker's blog](https://brooker.co.za/blog/) on rate limiting and capacity, short and dense.

Watch:
- Any solid conference talk on load shedding or rate limiting in practice. One, after the lab.

## What trips people up this week ⚠️

They design for the happy path and treat failure handling as something to add later. In production there is no later. The interesting question is never "how does this work when everything is fine", it is "how does this behave when a dependency is slow, a disk fills up, a customer sends ten times the normal traffic, or a deploy goes wrong". Design the failure behaviour on purpose, from the start, and say it out loud. That habit alone will make you look two levels more senior than you are.
