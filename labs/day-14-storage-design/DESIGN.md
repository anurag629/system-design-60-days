---
title: "Day 14 design template"
parent: "Day 14: designing a storage layer"
grand_parent: "Week 2: storage"
nav_order: 1
---

# Day 14: design the storage layer for a messaging app

Fill this in against the clock, 45 minutes for a first full pass, before you open the Solutions on the day page or the Discord write-up. Then improve it with the readings and mark what you added.

## 1. Access pattern

What gets written, how often, append or in-place update:

What gets read, by what key, how often:

## 2. Scale estimate

Messages per second (average and peak):

New data per day, and per year:

What that scale tells you (one machine or many):

## 3. Engine

B-tree or LSM, and the Day 9 reason:

Row store, column store, or both (and where analytics goes):

## 4. Data model and the hot query

The one hot query, and the partition + ordering that serves it:

Offset or keyset paging, and why:

## 5. Shard key and hot partition

Shard key:

Where the hot partition comes from, and how you spread it:

## 6. Replication and consistency

How reads scale and survive a node dying:

The one read that cannot be stale, and how you handle it:

## Reflection

Which week 2 day I leaned on hardest, and the choice I was least sure about:
