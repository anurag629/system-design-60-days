---
title: "Day 54: mock, an AI system"
parent: "Week 8: putting it all together"
nav_order: 5
has_children: true
---

# Day 54
## Mock 4, a production AI system, where the model is the easy part 🤖

Today's one idea: designing an AI product is not designing a model. The model is an opaque box you call. The whole design is the system around it: getting the first token back fast, feeding it the right context through retrieval, rationing scarce and expensive GPU time, and stopping the token bill from eating the company. This is exactly the kind of question showing up in real interviews now, and most candidates fumble it because they talk about the model instead of the system.

Mock 4, the last one. Week 6 meets everything else you have learned.

---

## Before you start ⏪

Framework sheet on the desk. Reread week 6, especially Day 42 (you designed a production AI chat system there), Day 39 (RAG and why it fails at retrieval), Day 40 (agents and the token bill), and Day 41 (serving: caching, limiting, fallback). This mock is week 6 under the clock.

---

## Words you will meet today 📖

A token is the unit an LLM reads and writes, roughly a word-piece. You are billed per token, in and out, and latency scales with how many tokens come out. Everything about cost and speed is counted in tokens (Day 36).

Time to first token (TTFT) is how long until the first word appears. In a streaming chat UI this matters far more than total time, because a reply that starts in 300ms and streams feels fast even if it takes 8 seconds to finish.

RAG (retrieval-augmented generation) is fetching relevant documents and stuffing them into the prompt so the model answers from your data instead of its memory. The quality of the answer is mostly the quality of the retrieval (Day 39).

A semantic cache returns a stored answer when a new question means the same thing as an earlier one, even if the words differ, by comparing embeddings. It can cut cost sharply on repetitive traffic (Day 41).

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read, lightly, for the shape:
- [Design ChatGPT](https://www.hellointerview.com/learn/system-design/problem-breakdowns/chatgpt) from Hello Interview. It treats the model as a called service and puts all the design in the serving system around it, which is exactly the right framing.
- Your own [Day 42 design](../days/day-42.md). You already built this; reuse it.

Watch, after your own run:
- [Design ChatGPT, a system design mock interview with an eBay engineering manager](https://www.youtube.com/watch?v=I9-PUPYZyiw) by Exponent (now Aced), about 35 minutes. A real run at exactly this question.

### The model is a called service, the design is everything else 🧩

The single biggest mistake is spending the interview on the model. You are not training it, you are not inspecting its weights, you call it like any other backend dependency: you send tokens in, you get tokens out, you pay per token, and it is slow and scarce. Once you frame it as "an expensive, slow, rate-limited third-party service" (week 7's language), the design becomes familiar. You wrap it with the same machinery as any other hot, costly dependency: a cache in front, a rate limiter, a fallback, a queue for the slow path, and tight cost accounting.

Two numbers drive the serving design. First, TTFT. Users forgive a long total response if words start appearing fast, so you stream tokens as they generate and you optimise for first-token latency, not total latency. Second, GPU scarcity. A GPU can only do so much at once, so you batch requests together (Day 37, continuous batching) to keep it busy, and you queue when demand exceeds capacity rather than falling over. Those two, stream for perceived speed and batch for throughput, are the heart of serving.

### Retrieval and cost are where it actually fails 💸

If the product is RAG (answer from our docs), the deep dive is retrieval, because the model can only be as right as the context you hand it. Day 39's lesson stands: most RAG failures are retrieval failures, the model got the wrong or no relevant chunks and then confidently made something up. So you design the retrieval pipeline seriously: chunking, embeddings, a vector index (Day 38), and the honest acknowledgement that naive top-k similarity misses things, so you add reranking or hybrid keyword-plus-vector search. Garbage retrieved is garbage generated.

Cost is the other place it dies, and it is where you sound senior. Every token in and out is money, long conversations resend the whole history every turn so cost grows with the square of the conversation, and agents (Day 40) multiply calls until the bill explodes. So you attack cost deliberately: a semantic cache for repeated questions (Day 41), trimming or summarising conversation history instead of resending all of it, routing easy requests to a smaller cheaper model and only hard ones to the big model, and a hard per-user token budget (week 7's rate limiting and cost attribution). An interviewer who hears "I would route simple queries to a small model and cache semantically, because the token bill is the real scaling limit here" knows you have actually run one of these.

---

## Block 2: drill (40 min) ✍️

Paper first, into [`notes/day-54-drills.md`](../notes/day-54-drills.md). Warm-up before the timed run.

D1. The framing. Why is "design an AI chat product" mostly not about the model, and what familiar thing (from week 7) is the model most like?

D2. Latency. What is TTFT, why does it matter more than total response time in a chat UI, and what technique makes a long answer feel fast?

D3. GPU scarcity. A GPU serves limited concurrent work. What do you do to keep it busy (Day 37), and what do you do when demand exceeds capacity instead of crashing?

D4. RAG. Why are most RAG failures actually retrieval failures (Day 39), and name two things you would do to make retrieval better than naive top-k similarity.

D5. Cost. Give three concrete levers to cut the token bill (Day 40, Day 41), and explain why a long conversation gets more expensive every single turn.

---

## Block 3: build (100 min) 🔧

The timed run. Open [`labs/day-54-mock-ai/MOCK.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-54-mock-ai/MOCK.md), copy it, 45-minute timer, out loud. Pick either a RAG product (answer questions over a company's documents) or a general AI chat product; the brief covers both. Lead by framing the model as a called service, then design the serving system around it.

Then grade yourself. The classic failure here is the one from the readings: spending ten minutes on how transformers work, which is not the question. Protect your time for serving, retrieval, and cost.

### What a strong run looks like

You frame the model as an expensive, slow, rate-limited dependency in the first two minutes. You design streaming and batching for latency and throughput. If it is RAG, you take retrieval quality seriously and admit naive similarity is not enough. And you have a real cost section with concrete levers, because cost is the thing that actually limits these systems in production.

### Deliverable

Your filled-in `MOCK.md`, your rubric score, and one line: the AI-specific concern you would most want to drill before a real interview.

---

## Block 4: write (30 min) 📣

Your angle is the reframe that cuts through the hype: "Designing an AI product is barely about the model. The model is a slow, expensive service you call. The actual engineering is retrieval quality, streaming for speed, batching for throughput, and a token bill that grows with the square of the conversation." Share the lever that surprised you most.

Example posts are on the [Day 54 posts](../shares/day-54-posts.md) page.

---

## End of day: log it 📝

Log the three: your rubric score, whether you framed the model as a called service from the start, and the AI concept you still want to drill.

Tomorrow the mocks are done and the capstone begins. You pick one system you genuinely care about, and over four days you design it, build a real slice, break it under load, and write it up. This is where the whole course lands.

---

## Solutions 🔑

Open after your own timed run.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Because you do not build or train the model, you call it. The design is the serving system wrapped around a called dependency: the API in front, the retrieval that feeds it context, the cache, the rate limiter, the queue, the fallback, and the cost accounting. The model is most like an expensive, slow, rate-limited third-party service (week 7's framing), and once you treat it that way, the whole design becomes a familiar "wrap a costly hot dependency" problem rather than anything exotic.

D2. TTFT is time to first token, how long until the first word of the reply appears. In a streaming chat UI it matters more than total time because a reply that starts in a few hundred milliseconds and then streams feels fast and responsive, even if the full answer takes several seconds, whereas a reply that shows nothing for 8 seconds and then dumps everything feels broken. The technique: stream tokens to the client as they are generated rather than waiting for the whole response, so you optimise and measure first-token latency.

D3. A GPU can only process so many tokens concurrently, so to keep it busy you batch multiple requests together, and specifically continuous batching (Day 37), where new requests slot into the batch as others finish rather than waiting for a fixed batch to complete. When demand exceeds capacity you queue and apply backpressure (Day 27) rather than overloading the GPU, and you may shed or degrade the lowest-priority requests. You never just pile unlimited concurrent work onto a fixed GPU; you batch to the sweet spot and queue the rest.

D4. Because the model answers from whatever context you give it, so if retrieval returns the wrong chunks, irrelevant chunks, or nothing useful, the model fills the gap by confidently inventing an answer (Day 39). The generation step is rarely the problem; the retrieval step usually is. Two improvements over naive top-k vector similarity: add a reranking step that reorders the top candidates with a more precise (and more expensive) model so the best chunks actually reach the prompt, and use hybrid retrieval that combines keyword search with vector similarity so exact terms and names are not lost to fuzzy embeddings. Better chunking and metadata filtering also help.

D5. Three levers: a semantic cache that returns a stored answer for a question that means the same as an earlier one (Day 41), cutting repeated work to near zero on common questions; trimming or summarising the conversation history instead of resending the entire transcript every turn; and model routing, sending easy requests to a small cheap model and reserving the big expensive model for hard ones. A long conversation gets more expensive every turn because the whole history is resent as input on each new message, so input tokens grow with the length of the conversation, and the total cost over a conversation grows roughly with the square of its length (Day 40). That is why trimming history is not a nicety but a core cost control.

</details>

<details markdown="1">
<summary>A worked reference design (RAG product)</summary>

Requirements. Functional: a user asks a question in natural language and gets an answer grounded in the company's documents, with sources, streamed back. Non-functional: low TTFT, answers grounded (minimal hallucination), controllable cost per query, graceful under load, and a hard per-user budget.

Scale. Say 1 million queries a day, about 12 per second average and maybe 40 at peak, each query retrieving a handful of chunks and generating a few hundred tokens. The expensive resource is GPU time and the model API bill, not storage.

API and entities. POST /chat {conversation_id, message} streaming the answer and a list of source chunks. Entities: Document, Chunk (text, embedding, source metadata), Conversation (trimmed history).

High-level design. Ingestion (offline): documents are chunked, embedded (Day 38), and written to a vector index. Query path: embed the question, retrieve top candidates from the vector index, rerank them, build a prompt with the best chunks and the trimmed conversation history, call the model, and stream tokens back with citations. A semantic cache sits in front to short-circuit repeated questions. A rate limiter and per-user token budget guard cost and capacity.

Deep dives. Retrieval quality (Day 39): hybrid keyword-plus-vector search and a reranker, because naive top-k misses things and retrieval quality is answer quality. Serving (Day 37, 41): stream for TTFT, batch on the GPU for throughput, queue under overload. Cost (Day 40): semantic cache, history trimming, and model routing (small model for easy queries).

Failure and cost. The model API is a third-party dependency, so you need timeouts, retries with backoff, and a fallback (a cheaper model, or a graceful "I could not answer" rather than a hang, Day 41). Cost is dominated by model tokens, so the cache hit rate and the small-model routing fraction are the two numbers that decide whether the product is viable.

The senior sentence: "the model is a slow expensive called service, so I stream for first-token latency, batch on the GPU for throughput, take retrieval quality seriously because that is where RAG actually fails, and attack cost with a semantic cache, history trimming and model routing, because the token bill is the real scaling limit."

</details>

<details markdown="1">
<summary>The self-grade rubric</summary>

Score each out of 2.

- Requirements: named grounded answers, TTFT, and cost per query as goals?
- Framing: treated the model as a called, expensive, rate-limited service, not a thing to explain?
- Serving: streaming for TTFT and batching for GPU throughput?
- Retrieval (if RAG): took it seriously and admitted naive similarity is not enough?
- Cost: concrete levers (cache, trimming, routing) and why conversations grow costly?
- Failure: timeouts, fallback, per-user budget?

10 to 12, you clearly have run one of these in your head before. 6 to 9, solid but you probably drifted toward the model. Below 6, reframe the model as a called service and rerun.

</details>
