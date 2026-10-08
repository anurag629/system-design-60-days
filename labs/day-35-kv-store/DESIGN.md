---
title: "Day 35 design template"
parent: "Day 35: designing a distributed key-value store"
grand_parent: "Week 5: distributed systems"
nav_order: 1
---

# Day 35: design a distributed key-value store

Fill this in against the clock, 45 minutes for a first full pass, before you open the Solutions or the Dynamo paper. Then improve it with the readings and mark what you added.

## 1. Requirements and consistency stance

Functional (the API):

Non-functional (availability, scale, failure, consistency):

AP or CP, and why for this workload:

## 2. Key placement

How a key maps to nodes, and the resharding cost when a node is added (Day 13):

## 3. Replication and quorums

N, W, R and what each setting trades (Day 31):

The default you pick and why:

## 4. Conflicts

How concurrent writes to one key are detected and resolved (Days 29, 33):

## 5. Failure handling

Staying writable when owner nodes are down (sloppy quorum, hinted handoff):

Repairing drifted replicas, and tracking membership:

## 6. When CP instead

A product where you would refuse writes during a partition, and why (Day 30):

## Reflection

Which week-5 day the store leaned on hardest, and what I am least sure about:
