---
title: "Day 42 design template"
parent: "Day 42: designing a production AI chat system"
grand_parent: "Week 6: AI systems"
nav_order: 1
---

# Day 42: design a production AI chat system (RAG)

Fill this in against the clock, 45 minutes for a first full pass, before you open the Solutions or the readings. Then improve it with the readings and mark what you added.

## 1. Requirements and cost estimate

Functional:

Non-functional (latency, groundedness, cost, multi-tenancy, outage survival):

Token-cost estimate (questions/sec, tokens/day, monthly bill, which tokens dominate):

## 2. Ingestion pipeline (offline)

Chunking, embedding, the vector index, incremental updates and permissions metadata:

## 3. Query path (online, end to end)

Gateway and rate limiting, session, query rewrite, semantic cache, hybrid retrieval + permission filter, rerank, prompt assembly, model gateway (batching, streaming, routing, fallback), guardrails, logging:

## 4. Serving and cost levers

Streaming and why, continuous batching, prompt caching, semantic cache, model routing, per-tenant token budgets:

## 5. Reliability and security

Provider outage handling (fallback):

Where permission filtering happens, and why not in the prompt:

Hallucination control:

## Reflection

Which earlier week this leaned on most, and what I am least sure about:
