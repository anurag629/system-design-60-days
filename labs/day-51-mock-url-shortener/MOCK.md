---
title: "Day 51 mock brief"
parent: "Day 51: mock, a URL shortener"
grand_parent: "Week 8: putting it all together"
nav_order: 1
---

# Mock 1: design a URL shortener

Copy this into your fork. Set a 45-minute timer. Run all six steps out loud, writing as you talk. Do not pause to look things up. When it rings, stop and grade yourself with the rubric at the bottom.

## The brief

Design a service like Bitly. A user submits a long URL and gets a short one back. Anyone who visits the short URL is redirected to the long one. Assume you may be asked for custom aliases, link expiry, and click analytics, so leave room for them.

## 1. Requirements (5 min)

Functional:

Non-functional (and which one drives the design):

## 2. Scale estimate (5 min)

Writes/s (peak):

Reads/s (peak):

Storage over 5 years:

## 3. API and core entities (5 min)

Endpoints:

Entities:

## 4. High-level design (10 to 15 min)

The write path (create a short link):

The read path (resolve and redirect):

## 5. Deep dives (10 to 15 min)

The hinge decision I am going deep on (the short code, or the read scale):

My answer and the tradeoff:

## 6. Bottlenecks and failure (5 min)

Single point of failure and blast radius:

What breaks under load, how it is detected, how it degrades:

## Self-grade (score each out of 2)

- [ ] Requirements: functional vs non-functional, named "read heavy"
- [ ] Scale: real numbers that changed a decision
- [ ] API and entities: clean and minimal
- [ ] High-level: read path and write path separated
- [ ] Deep dive: a real hinge decision, reasoned
- [ ] Failure and cost: reads survive a write-path failure

Total out of 12: ______  The step I drill again: ______
