---
title: "Day 54 posts"
parent: "Day 54: mock, an AI system"
grand_parent: "Week 8: putting it all together"
nav_order: 3
---

# Day 54 posts: LinkedIn and X

The angle is that designing an AI product is barely about the model. Swap in your own voice.

## LinkedIn

Day 54 of 60 days of system design. Last mock, and the one most relevant to interviews right now: design a production AI system.

The biggest mistake people make, and I nearly made it too, is spending the whole time on the model. How attention works, how it was trained, which architecture. None of that is the question.

The model is a slow, expensive, rate-limited service you call. Tokens in, tokens out, billed per token. The moment you frame it like that, as just another costly hot dependency, the design becomes familiar: you wrap it with the same machinery as anything else, a cache in front, a rate limiter, a fallback, a queue, and tight cost accounting.

Four things that actually matter:

Time to first token beats total time. In a streaming chat, a reply that starts in 300ms and streams for 8 seconds feels fast. One that shows nothing for 8 seconds feels broken. So you stream, and you optimise for the first token.

GPUs are scarce, so you batch requests to keep them busy and queue when demand exceeds capacity, instead of piling on unlimited work and falling over.

For RAG, the model is only as right as the context you feed it. Most RAG failures are retrieval failures: wrong chunks in, confident nonsense out. So retrieval quality is the real work, and naive top-k similarity is not enough, you add reranking and hybrid search.

Cost is the true scaling limit. A long conversation resends the whole history every turn, so cost grows with the square of the conversation. The levers: a semantic cache for repeated questions, trimming history instead of resending it, and routing easy queries to a small cheap model.

The sentence that sounds senior: "the token bill is the real constraint here, so I would cache semantically and route simple queries to a smaller model." Say that and the interviewer knows you have actually built one.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #ai #llm #interviewprep #learninginpublic

## X thread

**1/**

Day 54 of 60 days of system design. Last mock: design a production AI system.

Biggest mistake, and I nearly made it: spending the time on the model. How attention works, how it trained. None of that is the question.

**2/**

The model is a slow, expensive, rate-limited service you call. Tokens in, tokens out.

Frame it as just another costly hot dependency and the design gets familiar: cache, rate limiter, fallback, queue, cost accounting.

**3/**

Time to first token beats total time. A reply that starts in 300ms and streams feels fast. One silent for 8s feels broken.

So you stream and optimise the first token.

**4/**

GPUs are scarce: batch requests to keep them busy, queue when demand exceeds capacity. Don't pile on unlimited work.

RAG: the model is only as right as the context. Most RAG failures are retrieval failures. Add reranking and hybrid search.

**5/**

Cost is the real scaling limit. A long chat resends the whole history each turn, so cost grows with the square of the conversation.

Levers: semantic cache, trim history, route easy queries to a small model.

**6/**

Mocks done. Tomorrow the capstone begins: pick one system, design it, build a slice, break it under load, write it up.

Code: github.com/anurag629/system-design-60-days
