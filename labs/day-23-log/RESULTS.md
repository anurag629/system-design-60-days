---
title: "Day 23 lab results"
parent: "Day 23: the log as a primitive"
grand_parent: "Week 4: async, queues and the log"
nav_order: 1
---

# Day 23 results: the log, offsets, and replay

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (last offset after appending N records):
- P2 (duplicates after a crash between process and commit):
- P3 (records missed after that crash):
- P4 (records the new consumer replayed from offset 0):

## The offset is the whole trick

The consumer crashed and resumed with nothing lost. In your own words, where was the committed offset kept, and why did resuming from it skip nothing:

## At-least-once, in my own words

The restart re-ran one record. Why does committing the offset after the work (not before) turn a crash into a duplicate rather than a gap, and which one would you rather debug:

## The replay superpower

A brand new consumer re-read all N records while the first sat at the end. Why can a log do this when a queue cannot:

## The number that matters

Two consumers on one log at different offsets (___ and ___), and a fresh consumer replayed all ___ records from offset 0. What does that let you build that a queue would not:

## Can't explain yet
