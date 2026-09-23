# Week 6: AI systems, the fun one 🤖

Days 36 to 42, Tue 2026-10-27 to Mon 2026-11-02.

This is the week you came for, and here is the good news: you are ready for it now in a way you were not five weeks ago. Because serving an AI model is not some alien new discipline. It is distributed systems with a very expensive, very hungry component in the middle called a GPU. Everything you learned about latency, batching, caching, queues and tail latency now points straight at that GPU.

Let me say the thing people miss. An LLM is slow and costly in a specific, understandable way, and once you see the shape of it, the whole architecture around it makes sense. The model generates one token at a time, each token needs the whole model and all the previous tokens, and the GPU's memory is the real bottleneck, not its compute. That single fact explains the KV cache, continuous batching, why long prompts cost more, and why your token bill looks the way it does.

The rest is familiar friends in new clothes. Vector search is just an index for "things that mean similar", the way a B-tree is an index for "things that sort near". RAG is cache-aside plus retrieval. Agents are a request that fans out into many requests, so tail latency is back to bite you. Semantic caching is caching where the key is a meaning instead of an exact string.

## What you will be able to do by the end of the week

You can explain prefill versus decode and why the first token is slow but the rest stream fast. You can say what the KV cache is and why continuous batching was such a big deal. You can design a RAG system and name its three most common failure modes before you build it. You can do the token-cost maths for an AI feature and tell a PM roughly what it will cost per user per month, which is a superpower almost nobody has.

## The days 🗓️

Day 36: how LLM inference actually works. Tokens, prefill vs decode, and why it is memory-bound not compute-bound. Lab: hit a real model API and measure tokens per second, and how latency grows with output length.

Day 37: the KV cache and continuous batching, the vLLM insight. This is a virtual-memory paper wearing an AI hat, and it is genuinely clever. Lab: measure throughput with and without batching and see the difference for yourself.

Day 38: vector search and embeddings. Approximate nearest neighbour, HNSW, and the recall-versus-latency dial you get to turn. Lab: build a tiny vector index and measure how recall trades off against speed.

Day 39: RAG architecture. Chunking, retrieval, reranking, and the failure modes that make RAG demos great and RAG products frustrating. Lab: build a minimal RAG, break it on purpose, and measure retrieval quality.

Day 40: agents and orchestration. Tool calls, the reasoning loop, context window management, and cost that balloons because one user request becomes twenty model calls. Lab: a small agent loop, with the token cost of every step printed so you feel it.

Day 41: serving concerns. Semantic caching, token-based rate limiting, model gateways, and fallback when your primary model is down or slow. Lab: a semantic cache plus a token bucket in front of an LLM endpoint.

Day 42: AI system design. You design a production AI chat product or a RAG system at real scale, timed, then a retro.

## Core resources for the week 📚

Read:
- [Efficient Memory Management for LLM Serving with PagedAttention](https://arxiv.org/abs/2309.06180), the vLLM paper. The one paper that makes inference click.
- [Anthropic prompt caching docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching). Read the constraints, because the constraints are the design.
- [pgvector README](https://github.com/pgvector/pgvector), the least hyped and most practical intro to vector search.

Watch:
- Talks from the vLLM and Ray teams on inference serving, and any solid walkthrough of RAG failure modes. Pick one, after the lab.

## What trips people up this week ⚠️

They design the AI part and forget it is still a system. The model is one box in a diagram that also needs a queue in front of it for spikes, a cache for repeated questions, a rate limiter so one user cannot burn your whole budget, a fallback for when the provider has an outage, and a plan for when a request takes 30 seconds. The magic is in the model. The engineering, the part they are actually hiring you for, is in everything around it. Bring your week 1 to 5 brain into this week and you will run circles around people who only know the AI buzzwords.
