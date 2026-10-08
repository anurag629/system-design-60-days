---
title: "Day 21 design template"
parent: "Day 21: designing a news feed"
grand_parent: "Week 3: caching and the CDN"
nav_order: 1
---

# Day 21: design a news feed

Fill this in against the clock, 45 minutes for a first full pass, before you open the Solutions on the day page. Then improve it with the readings and mark what you added.

## 1. Requirements

Functional:

Non-functional (read vs write skew, speed, the celebrity case):

## 2. Scale estimate

Posts per second (average and peak):

Feed reads per second:

Fan-out-on-write cost (posts x average followers):

## 3. The core decision: push, pull, or hybrid

Push (fan-out on write), and where it breaks:

Pull (fan-out on read), and where it breaks:

Your choice, and the follower threshold where it flips:

## 4. Write path

What happens when a normal user posts:

What happens when a celebrity posts:

## 5. Read path

Where the precomputed part comes from, where the celebrity part comes from, how post ids become posts:

## 6. The feed cache

What it holds, how big, where it lives, and why far fewer feeds than users (Day 16):

## 7. Celebrity and failure

The celebrity post read by millions (Days 17, 18), and what protects the database:

What happens when the feed cache goes cold:

## Reflection

Which week 3 day the feed leaned on hardest, and where I had to guess:
