---
title: "Day 58 architecture doc"
parent: "Day 58: capstone writeup"
grand_parent: "Week 8: putting it all together"
nav_order: 1
---

# Architecture doc template

Copy this into your fork and fill every section with the real substance of your capstone. Use your actual Day 57 numbers. Keep it to four to six pages. Cut any sentence that is not a claim, a reason, or a number.

## Summary

One paragraph a stranger could understand: what the system does and what this doc covers.

## Requirements

Functional:

Non-functional (and which one drives the design):

## Non-goals

Three things this system deliberately does NOT do, one line each on why:
-
-
-

## Design

In words, the read path and the write path, and one simple diagram (ASCII is fine). Where the store, cache, and queue sit.

## Decisions (ADRs)

### ADR 1: <the decision>
- Chosen:
- Rejected:
- Why (and the tradeoff you accepted):

### ADR 2: <the decision>
- Chosen:
- Rejected:
- Why (and the tradeoff you accepted):

### ADR 3 (optional):

## Measured results (from Day 57)

State these as you would to a skeptic:
- Peak throughput (read, and write if different):
- The knee (at what load throughput flattens):
- The named bottleneck (the resource, not a guess):
- p99 at the knee, and past it:

## Failure modes

For each: what breaks, how you detect it, how it degrades.
- Failure 1:
- Failure 2:
- Failure 3:

## Cost (if this were real)

Rough monthly shape and the dominant line item (Day 48):

## What is next

The one or two changes that would most move the ceiling, and the real-scale path:
