---
title: "Day 42 posts"
parent: "Day 42: designing a production AI chat system"
grand_parent: "Week 6: AI systems"
nav_order: 3
---

# Day 42 posts: LinkedIn and X

The angle is the reframe: in a real AI product, the model is the smallest box. Swap in your own voice.

## LinkedIn

Day 42 of 60 days of system design, end of week 6, AI systems. I designed a production RAG chat product today, and the thing that stuck with me is that the model was the smallest box in the diagram.

The product is two pipelines meeting at a vector index. Offline, you chunk documents, embed them, and load them into the index with permission metadata. Online, a question flows through a gateway (auth, token-based rate limits), a session store, a query rewrite, a semantic cache, hybrid retrieval filtered by the user's permissions, a reranker, prompt assembly, and only then the model, which streams the answer back and falls back to a backup if the provider is down.

Count the boxes. One of them is the LLM. The rest is retrieval, caching, batching, rate limiting and fallback, which is to say the five weeks of systems I did before this one.

Two things decide everything, and neither is the model's intelligence:

Retrieval decides quality. The smartest model cannot answer from a chunk you failed to retrieve. So groundedness is a chunking and retrieval problem, and if the answer is wrong, the first suspect is retrieval, not the model. Permissions have to be filtered at retrieval too, because once a document is in the prompt, telling the model to keep it secret is not a security control.

Cost decides whether you can ship. At a million users asking ten questions a day, you are looking at tens of billions of tokens a day and a seven-figure monthly bill, dominated by the output tokens that get generated one at a time. The levers are all from this week: a semantic cache, prompt caching, token-based limits, routing simple questions to a smaller model, and continuous batching to keep the GPU full.

AI serving is not a separate discipline. It is distributed systems with a GPU in the middle, and the GPU is the part you control least.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #ai #llm #learninginpublic

## X thread

**1/**

Day 42, end of week 6 (AI systems) of 60 days of system design. I designed a production RAG chat product, and the model was the SMALLEST box in the diagram.

**2/**

Two pipelines meet at a vector index.

Offline: chunk docs, embed, load into the index with permission metadata.
Online: gateway (auth, token limits) → session → query rewrite → semantic cache → hybrid retrieval (permission-filtered) → rerank → prompt → model (stream + fallback).

**3/**

Retrieval decides quality. The smartest model can't answer from a chunk you didn't retrieve. Wrong answer? Suspect retrieval, not the model.

And filter permissions AT retrieval. Once a doc is in the prompt, "please keep this secret" is not a security control.

**4/**

Cost decides whether you ship. 1M users x 10 questions/day ≈ tens of billions of tokens/day, a 7-figure monthly bill, dominated by output tokens (generated one at a time).

Levers, all from this week: semantic cache, prompt caching, token-based limits, smaller-model routing, continuous batching.

**5/**

The lesson of the whole week: AI serving is not a new discipline. It is distributed systems with a GPU in the middle, and the GPU is the part you control least.

Week 6 done. The five weeks before it were the real prep.

Code: github.com/anurag629/system-design-60-days
