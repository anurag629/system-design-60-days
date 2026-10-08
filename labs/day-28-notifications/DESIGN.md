---
title: "Day 28 design template"
parent: "Day 28: designing a notification system"
grand_parent: "Week 4: async, queues and the log"
nav_order: 1
---

# Day 28: design a notification system

Fill this in against the clock, 45 minutes for a first full pass, before you open the Solutions on the day page. Then improve it with the readings and mark what you added.

## 1. Requirements

Functional (channels, preferences, per-user and broadcast):

Non-functional (no loss, no duplicates, provider isolation, survive a broadcast):

## 2. Scale estimate

Notifications per second (average and peak):

A broadcast to everyone: jobs queued at once, and time to drain:

Is a broadcast real-time? Why:

## 3. The async flow

What the triggering service does (and does not do) inline:

## 4. Fan-out and channel isolation

How one event becomes per-channel work:

Why each channel gets its own queue and workers:

## 5. Reliability guards (name the week-4 day for each)

Not losing the event:

Not sending it twice:

Retries and what happens after they are exhausted:

## 6. Backpressure and the broadcast

Provider rate limits and how the queue absorbs them:

What you do with 10 million queued pushes against a rate-limited provider:

## Reflection

Which week-4 day the design leaned on hardest, and where I had to guess:
