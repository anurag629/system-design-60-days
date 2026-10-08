---
title: "Day 55 capstone design doc"
parent: "Day 55: capstone kickoff"
grand_parent: "Week 8: putting it all together"
nav_order: 1
---

# Capstone design doc

Copy this into your fork and fill it in before you write any code. This is the document you build against for the next three days. Keep it short and real.

## Summary

One paragraph a stranger could understand: what the system does and the one slice you will build.

## Scope

Building (three things):
-
-
-

NOT building, not now (three things, be ruthless):
-
-
-

## The interesting slice

The one feature I will build end to end:

The number I predict about it (throughput, p99 latency, or cache hit rate), written down now so Day 57 can prove me wrong:

## Scale estimate (if this were real)

Reads/s (peak):

Writes/s (peak):

Storage/year:

Does any number change the design? How:

## API (the slice)

Endpoints:

Core entities:

## High-level design (in words)

The write path:

The read path:

Where the cache / queue / store sit:

## The two or three hard decisions

Decision 1 (and its tradeoff):

Decision 2 (and its tradeoff):

Decision 3 (optional):

## Candidate systems, if you need a menu

All buildable as a small HTTP service with the standard library:
- URL shortener with click analytics
- a rate-limiter service (the distributed-counter decision, made real)
- a job queue with workers and retries
- a key-value store with a write-ahead log and a read cache
- a feed service with fan-out
- a document-search service with keyword retrieval (RAG retrieval, no model)
- a metrics ingestion endpoint that aggregates counters

Pick one where a measured number will surprise you.
