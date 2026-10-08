---
title: "Day 42: designing a production AI chat system"
parent: "Week 6: AI systems"
nav_order: 7
has_children: true
---

# Day 42
## Designing a production AI chat system, where the model is one box and the engineering is everything around it 🤖

Today's one idea: the magic is the model, but the job you are hired for is everything around it. A production AI chat product is a retrieval system, a serving system, a cache, a rate limiter, a gateway and a cost model, with an LLM in the middle. Every one of those is a week-6 day, sitting on top of five weeks of ordinary distributed systems. Today you assemble them, and you will notice the model is the smallest part of the diagram.

This is the week 6 finale, a design day. You design a RAG-based AI chat product on paper, against the clock, and see that your five weeks of non-AI systems were the actual preparation.

---

## Before you start ⏪

Bring all of week 6. Day 36 (prefill vs decode, stream the output), Day 37 (the KV cache and continuous batching), Day 38 (vector search), Day 39 (RAG and retrieval quality), Day 40 (agent loops and token cost), Day 41 (semantic cache, token rate limiting, gateway fallback). And bring the earlier weeks, because the AI parts bolt onto a normal system: a cache (week 3), queues (week 4), stateless services behind a load balancer (Day 6), a sharded vector index (weeks 2 and 5).

---

## Words you will meet today 📖

RAG, retrieval-augmented generation, is answering from your own documents: retrieve the relevant chunks, put them in the prompt, and have the model answer from them with citations, instead of from its training alone.

Grounding is making the answer come from the retrieved context, not the model's memory, which is how you cut hallucination and cite sources.

The ingestion pipeline is the offline half: take documents, chunk them, embed them, and load them into the vector index, with incremental updates as documents change.

The query path is the online half: everything that happens between the user's question and the streamed answer.

A model gateway is the service in front of the LLMs that handles routing (which model), batching, streaming, retries, and fallback to a backup model.

Streaming is sending the answer token by token as it is generated, so the user sees words appear almost immediately (low time-to-first-token) instead of waiting for the whole response.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Building a chatbot with RAG, and why the architecture matters](https://dev.to/iniyarajan86/build-chatbot-with-rag-why-your-architecture-matters-354m). The ingestion-plus-query shape, chunking choices, hybrid retrieval, and the failure modes, laid out as an architecture.
- [The vLLM / PagedAttention paper](https://arxiv.org/abs/2309.06180). The serving half: the KV cache and continuous batching that make the GPU affordable. You simulated this on Day 37; here is the real thing.
- [Anthropic prompt caching docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching). The cost half: caching the stable prefix (system prompt plus retrieved context) so you do not pay to reprocess it every turn. Read the constraints.

Watch, after you have done your own design:
- [Design ChatGPT, a mock interview](https://www.youtube.com/watch?v=I9-PUPYZyiw) by Aced (formerly Exponent), about 35 minutes. A full worked design under interview conditions.
- Optional: [Design ChatGPT or an LLM, including RAG](https://www.youtube.com/watch?v=YLtOGnaczKg), about 32 minutes.

### Two pipelines: ingestion offline, query online (15 min)

A RAG chat product is two systems that meet at the vector index.

The ingestion pipeline runs offline, whenever documents change. It connects to the sources, chunks each document (the Day 39 knob, too big dilutes the answer, too small loses context), embeds each chunk into a vector, and upserts it into the vector index with metadata, crucially including who is allowed to see it. It must handle incremental updates and deletes, because a stale index gives stale answers, and a revoked document must leave the index promptly. This half is a queue and a pool of embedding workers (week 4), writing to a sharded vector store (Day 38, sharded like week 2).

The query path runs online, per question, and it is a pipeline of cheap steps guarding one expensive step (the model). Authenticate and rate-limit at the gateway (Day 41, per tenant). Load the session (stateless service plus a session store, Day 6 and week 3). Rewrite the question using conversation history. Check the semantic cache (Day 41), and if a similar question was answered before, return it without touching the model at all. Otherwise do hybrid retrieval, vector similarity plus keyword match, filtered by the user's permissions, then rerank and assemble a prompt (system instructions, retrieved chunks, the question). Send that to the model gateway, which batches (Day 37), streams the answer back token by token (Day 36), and falls back to a backup model if the primary is down (Day 41). Finally run output guardrails and log everything for evaluation.

Notice how little of that is the model. The model is one box near the end. The product is the pipeline around it.

### Why retrieval and cost dominate the design (10 min)

Two things decide whether this product is good and whether it is affordable, and neither is the model's intelligence.

Retrieval decides quality. The smartest model cannot answer from a chunk you failed to retrieve (Day 39). So groundedness is a retrieval problem: good chunking, hybrid retrieval so exact identifiers are not lost to fuzzy embeddings, reranking, and permission filtering at the retrieval layer, because the model cannot be trusted to hide content you handed it. If the answer is wrong, the first suspect is retrieval, not the model.

Cost decides whether you can ship it. LLM cost is per token, output tokens are the expensive sequential part (Day 36), and a naive design reprocesses the whole prompt every turn. So the levers are all week 6: a semantic cache to skip repeat questions entirely, prompt caching to stop repaying for the stable prefix, token-based rate limiting and per-tenant budgets so one user cannot burn the month, routing simple questions to a smaller model, and continuous batching so the GPU is never idle. Do the token math early, because for an AI product the cloud bill is the business model.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Write your answers into [`notes/day-42-drills.md`](../notes/day-42-drills.md). About 8 minutes each.

D1. Estimate the cost. 1 million users, 10 questions a day each, averaging 1,000 input tokens (prompt plus retrieved context) and 500 output tokens per question. Questions per second (and peak)? Tokens per day? At a blended 5 dollars per million tokens, roughly what is the monthly bill, and which tokens, input or output, are the expensive sequential part?

D2. Retrieval quality. Why is retrieval, not the model, the thing that decides whether answers are grounded? Give one chunking mistake that silently wrecks answers (Day 39), and say why hybrid retrieval (vector plus keyword) beats vector alone for a question containing an exact policy number.

D3. Serving. Give two reasons to stream the answer rather than return it whole (Day 36), and explain why continuous batching (Day 37) lets you serve more users on the same GPUs. When would you route a question to a smaller, cheaper model?

D4. Cost control. Name three levers from this week that cut the bill: what a semantic cache saves that an exact-match cache cannot, why rate limiting must be token-based not request-based, and what prompt caching avoids repaying for.

D5. Reliability and security. The primary model provider has an outage. What keeps the product answering (Day 41)? And where must permission filtering happen, at retrieval or in the prompt, and why can you not rely on telling the model to keep documents secret?

---

## Block 3: build (100 min) 🔧

Today you build a design, not code. The template is [`labs/day-42-ai-chat/DESIGN.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-42-ai-chat/DESIGN.md). Copy it into your fork and fill it in.

Do it against the clock, 45 minutes for a first full pass: requirements and the cost estimate, the ingestion pipeline, the query path end to end, the serving and cost levers, and the reliability and security cases. Do not open the Solutions or the readings until your 45 minutes are up.

Then improve it with the readings open, marking what you added. That delta is week 6 landing.

### What a strong design has

A weak one draws "user to LLM to answer." A strong one separates offline ingestion from the online query path, treats retrieval quality as the groundedness lever, does the token-cost math and names the cache, routing and batching levers that make it affordable, streams for time-to-first-token, filters permissions at retrieval, and has a fallback for a provider outage. In short, it treats the model as one component in a real system. Aim for that.

### Deliverable

Your filled-in `DESIGN.md`, and one honest paragraph: which earlier week did this AI system lean on most, and which part are you least sure about?

---

## Block 4: write (30 min) 📣

Your angle is the reframe: "I designed an AI chat product, and the model turned out to be the smallest box in the diagram. The real work was retrieval quality, the token-cost math, a semantic cache, continuous batching, and a fallback for when the provider goes down. AI serving is distributed systems with a GPU in the middle." Pick the two that surprised you.

Example posts are on the [Day 42 posts](../shares/day-42-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it, and look back 📝

Log the three: what you completed, your monthly-cost estimate and the one lever you would pull first to cut it, and one thing you still cannot explain.

Then the week 6 retrospective. Think back to the start of the week, when LLM serving felt like a separate, mysterious discipline. Write down the three AI-systems ideas that turned out to be ordinary systems ideas in disguise (batching, caching, tail latency), and the one genuinely new thing (the KV cache and the memory-bound GPU). That is week 6.

Week 7 is production: observability, SLOs, rate limiting, multi-tenancy, security and cost. The stuff that separates a design on a whiteboard from a system that survives being on call. You have built the systems; next week you learn to run them at 3am.

---

## Solutions 🔑

Open these only after your own 45-minute design pass.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. 1 million users times 10 questions is 10 million questions a day, about 100 per second, roughly 300 at a 3x peak. Tokens: 10 million times 1,500 (1,000 in plus 500 out) is 15 billion tokens a day. At 5 dollars per million tokens that is 15,000 times 5, about 75,000 dollars a day, roughly 2.25 million dollars a month. The output tokens (500 each, 5 billion a day) are the expensive sequential part (Day 36): they are generated one at a time, so they cost more per token in latency and often in price than the input, which is why trimming output length and caching are where the savings are. For an AI product, this estimate is the business model, not a footnote.

D2. Retrieval decides groundedness because the model can only answer from what you put in the prompt; if the right chunk was not retrieved, the model either says it does not know or, worse, makes something up. A chunking mistake that wrecks answers: chunks too large dilute the relevant sentence among irrelevant text so its similarity score drops and it is not retrieved; chunks too small split the answer across pieces so no single chunk carries it (Day 39). Hybrid retrieval beats vector alone for an exact policy number because embeddings match meaning, not exact strings, so "policy A-4471" fuzzily matches many similar codes; a keyword match nails the exact token, and combining the two catches both semantic and exact matches.

D3. Stream because time-to-first-token is what the user feels: words appearing in 300 ms reads as fast even if the full answer takes 8 seconds, whereas waiting 8 seconds for it all at once reads as broken (Day 36). And streaming lets the user start reading and cancel early if it is wrong. Continuous batching lets you serve more users on the same GPUs because a finished request's slot is immediately refilled instead of the whole batch waiting for the slowest request (Day 37), keeping the memory-bound GPU full. Route to a smaller model when the question is simple (a greeting, a classification, a short factual lookup), because a smaller model is cheaper and faster and the big model is wasted on it.

D4. A semantic cache saves the cost of repeat questions asked in different words: it keys by meaning (embedding similarity), so "how do I reset my password" and "I forgot my password, what now" hit the same cached answer, where an exact-match cache sees two different strings and misses both (Day 41). Rate limiting must be token-based because cost is per token: a request limit would let a few enormous requests blow the budget while blocking many tiny cheap ones, so you meter tokens per minute instead. Prompt caching avoids repaying to process the stable prefix (the system prompt and, often, the retrieved context) on every turn of a conversation, since that prefix does not change.

D5. A model gateway with fallback keeps the product answering during a provider outage: the gateway retries, and past a threshold routes to a secondary model (a different provider or a smaller self-hosted one), so the user still gets an answer, degraded rather than down (Day 41). Permission filtering must happen at RETRIEVAL, filtering documents by the user's access before they are ever put in the prompt, because once a chunk is in the context the model has seen it, and instructing the model to keep it secret is not a security control; a clever prompt can extract it. Security lives in retrieval, not in a polite request to the model.

</details>

<details markdown="1">
<summary>A worked reference design</summary>

One good answer, not the only one. Yours will differ; what matters is that the model is one box and the engineering around it is the design.

Requirements. Functional: a chat product that answers from a knowledge base with citations, remembers the conversation, and streams responses. Non-functional: low time-to-first-token, grounded answers (low hallucination), controlled cost, multi-tenant isolation, and survival of a provider outage.

Cost estimate, from D1: about 100 questions per second, 15 billion tokens a day, on the order of a couple of million dollars a month at this scale, dominated by output tokens. This number drives every later choice.

Ingestion pipeline (offline): connectors pull documents into a queue (week 4); workers chunk them at a tuned size (Day 39), embed each chunk (Day 38), and upsert into a sharded vector index with access metadata, handling incremental updates and deletes so the index stays fresh and revocations take effect.

Query path (online): client to an API gateway that authenticates and applies per-tenant token-based rate limits (Day 41); a stateless chat service with a session store (Day 6, week 3); query rewrite from history; a semantic cache check that short-circuits repeat questions (Day 41); hybrid retrieval (vector plus keyword) filtered by the user's permissions (Day 38, Day 39); rerank and assemble the prompt; the model gateway, which batches continuously (Day 37), streams tokens back (Day 36), uses prompt caching for the stable prefix, routes simple questions to a smaller model, and falls back to a backup model on failure (Day 41); output guardrails; and async logging and evaluation against a golden question set.

Reliability and security, from D5: fallback keeps it answering through an outage; permission filtering at retrieval keeps tenants isolated; grounding plus citations plus confidence checks control hallucination; per-tenant token budgets stop one customer burning the shared bill.

The sentence that makes this sound senior: "the model is one box near the end; the product is the retrieval quality in front of it, the batching and streaming around it, and the cache, limits and fallback that keep it affordable and up."

</details>

<details markdown="1">
<summary>Week 6 in one page</summary>

Seven days, one idea underneath: serving an LLM is distributed systems with an expensive, memory-bound GPU in the middle, so your first five weeks were the real preparation.

Day 36, inference. Prefill processes the prompt in parallel; decode generates output one token at a time, so latency is linear in output length and output tokens dominate cost. It is memory-bound, which is why batching matters.

Day 37, the KV cache and continuous batching. The cache makes decode cheap and caps batch size by memory; continuous batching keeps the GPU full, which is Day 4 and Day 6 pointed at a GPU, and it is the vLLM result.

Day 38, vector search. Approximate nearest neighbour trades a little recall for a lot of speed, and the recall-versus-speed dial is the whole behaviour of a vector database.

Day 39, RAG. It lives or dies on retrieval: chunking and vocabulary decide whether the right context reaches the model, so most "RAG is bad" is "retrieval is bad".

Day 40, agents. The context grows every step, so naive token cost balloons; trimming it brings the cost back to linear, and one request fanning into many calls brings back tail latency.

Day 41, serving. A semantic cache skips repeat questions, token-based limiting meters the real cost, and a gateway with fallback survives an outage.

Day 42, today. All of it assembled, with the model as the smallest box.

If your design treated the model as one component, did the token math, and leaned on batching, caching and fallback, you did not learn a mysterious new field this week. You learned that AI systems are the systems you already knew, aimed at a GPU. Week 7 is about keeping any of this alive in production.

</details>
