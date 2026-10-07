---
title: "Day 7 posts"
parent: "Day 7: your first real design"
grand_parent: "Week 1: ground truth"
nav_order: 3
---

# Day 7 posts: LinkedIn and X

The angle today is before and after. A hand-drawn boxes-and-arrows photo of your design makes a strong image. Swap in your own numbers and voice.

## LinkedIn

Day 7 of 60 days of system design, and the end of week 1. Today I designed a URL shortener from scratch, on paper, against the clock.

A week ago that question would have frozen me. I would have drawn some boxes and said "use a database" and hoped. Today it is a set of decisions I can reason about with numbers.

The number that drives the whole thing: this is read-heavy, about 100 reads for every write. People make a short link once and it gets clicked thousands of times. Once you see that, the design falls out of it.

- Writes are rare (about 40 a second), so the write path can be simple.
- Reads are everything (about 4,000 a second, peaks past 10,000), so the redirect has to be a single fast lookup, cached hard.
- 7 random base62 characters give 3.5 trillion codes, enough for decades, and not guessable.
- The bottleneck is the database on reads. A cache in front at a 90 percent hit rate drops it from 4,000 reads a second to 400. The hard part of the system becomes easy with one box.

The thing I could not have said a week ago: what happens when the cache dies. The database suddenly takes the full read load, so you size it to survive a cold cache. Naming that is the difference between a diagram and a system.

Week 1 taught me one habit above all: estimate first, and let the numbers choose the design.

Code and notes are public: github.com/anurag629/system-design-60-days

#systemdesign #learninginpublic

## X thread

**1/**

Day 7, end of week 1 of 60 days of system design. I designed a URL shortener from scratch, on paper, timed.

A week ago this would have frozen me. Today it is just a set of decisions with numbers behind them.

**2/**

The one number that drives everything: it is read-heavy, ~100 reads per write.

A link is made once and clicked thousands of times. So the write path stays simple and the read path, the redirect, is where all the engineering goes.

**3/**

Short code: 7 random base62 characters.

62^7 is ~3.5 trillion codes. Enough for decades, short enough to type, and random so nobody can walk your links. Writes are rare, so checking a new code is unique is cheap.

**4/**

Bottleneck: the database on reads, ~4,000/s with peaks past 10,000.

Fix: a cache in front. At a 90% hit rate the database sees 400/s instead of 4,000. One box turns the hard part easy. That is the Day 1 and Day 2 lessons in a real design.

**5/**

The part I could not have said a week ago: what happens when the cache dies.

The database takes the full load at once, so you size it to survive a cold cache. That sentence is the difference between a diagram and a system.

Week 1 done. Estimate first, let the numbers choose the design.

Code: github.com/anurag629/system-design-60-days
