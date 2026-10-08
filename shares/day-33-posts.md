---
title: "Day 33 posts"
parent: "Day 33: logical clocks"
grand_parent: "Week 5: distributed systems"
nav_order: 3
---

# Day 33 posts: LinkedIn and X

The Part 3 scoreboard is your screenshot: vector clocks keep all 4 cart items, last-write-wins keeps 1 and silently drops 3. Swap in your own numbers and voice.

## LinkedIn

Day 33 of 60 days of system design. Today I learned how to order events across machines without trusting a single clock, and then watched a wall clock quietly eat three quarters of a shopping cart.

The setup: on an earlier day I saw that clocks on different servers drift and jump, so comparing two timestamps from two machines is basically a guess. Today was the fix. You stop asking "what time did this happen?" and start asking "did this happen before that?". And it turns out you can answer that perfectly by counting, no clock needed.

First, Lamport timestamps. Each process keeps one integer, bumps it on every event, and on receiving a message jumps to max(mine, yours) + 1. This gives a lovely guarantee: if a really happened before b, then Lamport(a) < Lamport(b). I ran a little three-process simulation and that held on all 31 ordered pairs.

But here is the catch I did not expect. The guarantee only runs one way. Lamport(a) < Lamport(b) does NOT mean a happened before b. In my run, Lamport slapped a confident "came first" on 11 pairs of events that never influenced each other. They were concurrent, and Lamport simply could not see it.

Then, vector clocks. Instead of one integer, each process carries a whole vector, one slot per process. Now you can compare any two events and get the truth: before, after, or genuinely concurrent (neither vector dominates). My simulation classified all 45 pairs correctly and found 14 that were truly concurrent, the exact ones Lamport had papered over.

Why care? A pair of concurrent writes to the same key is a conflict. I replayed four writes to one cart. Vector clocks spotted the 2 concurrent conflicts, kept both versions, and the cart reconciled to all 4 items. Last-write-wins, trusting a skewed wall clock, kept the single write with the biggest timestamp and silently dropped 3 items. No error. No log line. Your milk is just gone.

Count causality, do not trust clocks. That is the whole lesson, and I got to watch it happen on my own laptop.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #learninginpublic

## X thread

**1/**

Day 33 of 60 days of system design.

I ordered events across 3 machines without using a single clock, then watched a wall clock silently delete 3 items from a shopping cart.

Logical clocks. Here is the whole thing.

**2/**

First idea: stop asking "what time did this happen?" Ask "did this happen BEFORE that?"

You can answer that by counting. No clock needed.

Lamport timestamp: each process keeps one integer, bumps it every event, and on receiving a message jumps to max(mine, yours) + 1.

**3/**

The payoff: if a really happened before b, then Lamport(a) < Lamport(b).

In my 3-process sim that held on all 31 ordered pairs. Rock solid.

**4/**

The catch nobody warns you about:

it only works ONE way.

Lamport(a) < Lamport(b) does NOT mean a happened before b. In my run Lamport confidently ordered 11 pairs of events that never influenced each other. It cannot see concurrency.

**5/**

Fix: vector clocks. Each process carries a whole vector, one slot per process.

Compare two vectors:
- V ≤ W everywhere -> V before W
- neither dominates -> CONCURRENT

My sim classified all 45 pairs correctly. 14 were truly concurrent, the exact ones Lamport hid.

**6/**

Why it matters: two concurrent writes to one key = a conflict.

I replayed 4 writes to one cart.

Vector clocks: flagged 2 conflicts, kept both versions, cart = all 4 items.
Last-write-wins (wall clock): kept 1 item, silently dropped 3.

**7/**

Same writes. Same order. One approach keeps your data, the other loses it and never tells you.

Count causality. Do not trust clocks.

Code: github.com/anurag629/system-design-60-days
