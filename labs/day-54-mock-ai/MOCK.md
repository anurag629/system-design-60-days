---
title: "Day 54 mock brief"
parent: "Day 54: mock, an AI system"
grand_parent: "Week 8: putting it all together"
nav_order: 1
---

# Mock 4: design a production AI system

Copy this into your fork. 45-minute timer. Out loud. Frame the model as a called service in the first two minutes, then design the system around it. Do not spend time on how transformers work.

## The brief

Pick one:
- A RAG product: a user asks questions in natural language and gets answers grounded in a company's documents, with sources.
- A general AI chat product: a ChatGPT-style assistant with conversation history.

Either way the model is a third-party service you call: tokens in, tokens out, billed per token, slow and rate-limited.

## 1. Requirements (5 min)

Functional:

Non-functional (name TTFT, grounded answers, cost per query, per-user budget):

## 2. Scale estimate (5 min)

Queries/s (peak):

Tokens per query (in and out), and the cost driver:

## 3. API and core entities (5 min)

Endpoint (streaming):

Entities (Chunk/embedding for RAG, trimmed Conversation):

## 4. High-level design (10 to 15 min)

Ingestion (offline, if RAG):

Query path (retrieve, build prompt, call model, stream back):

Where the cache and rate limiter sit:

## 5. Deep dives (10 to 15 min)

The hinge (retrieval quality, or serving latency/throughput, or cost):

My answer and the tradeoff:

## 6. Bottlenecks and failure (5 min)

The model API times out or is overloaded: timeout, retry, fallback?

The cost number that decides if the product is viable:

## Self-grade (score each out of 2)

- [ ] Requirements: grounded answers, TTFT, cost per query
- [ ] Framing: model as a called, expensive, rate-limited service
- [ ] Serving: streaming for TTFT, batching for GPU throughput
- [ ] Retrieval (if RAG): serious, admitted naive top-k is not enough
- [ ] Cost: concrete levers, why conversations grow costly
- [ ] Failure: timeouts, fallback, per-user budget

Total out of 12: ______  The AI concern I drill before a real interview: ______
