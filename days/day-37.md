---
title: "Day 37: the KV cache and continuous batching"
parent: "Week 6: AI systems"
nav_order: 2
has_children: true
---

# Day 37
## The KV cache, and the queueing trick that keeps a GPU from burning money 🧠

Today's one idea: serving an LLM comes down to two numbers, and the model's cleverness is neither of them. One, how much GPU memory each request eats, because the model caches a key and value for every past token so it never recomputes the conversation. Two, how well you keep the GPU full when requests finish at wildly different times. The famous vLLM paper is really about these two. Strip the AI vocabulary away and you are left with a memory-budget problem and a queueing problem, both of which you already solved earlier in this course. Today you measure them and watch continuous batching beat static batching by 5x, on the same hardware, for the same work.

Yesterday you saw that generation happens one token at a time, and that decode is memory-bound. Today you see exactly what is sitting in that memory, why it caps your batch, and the scheduling trick that stops the expensive box from sitting idle.

---

## Before you start ⏪

You need Day 36 fresh: prefill processes the whole prompt in one pass, then decode generates one token at a time, and decode is the slow, memory-bound part. Today is about the memory decode uses and how many decodes you can run side by side.

And pull Day 4 back up in your head, because today leans on it hard. Day 4 was tail latency, utilisation, and the chaiwala with one line versus two separate ones. Every bit of that returns, except the server is now a GPU that costs more per hour than the chaiwala makes in a year. The lab is pure Python, standard library only, no model and no GPU. It simulates the mechanics so you feel them.

---

## Words you will meet today 📖

The KV cache is the memory the model keeps so it does not recompute the past. During decode, each new token must attend to every previous token, which needs their key and value tensors. Rather than recompute those every step, the model stores them once and reuses them. Fast, but it grows with every token and lives in scarce GPU memory.

Decode is the one-token-at-a-time phase from Day 36. Each decode step reads the whole KV cache, does a little maths, and appends one token's key and value to the cache.

Static batching groups a fixed set of requests, runs them together, and does not free any slot until the slowest request in the group finishes. Simple, and it wastes the GPU whenever output lengths differ.

Continuous batching, also called in-flight batching or iteration-level scheduling, refills a slot the instant its request finishes, pulling the next waiting request from a shared queue. The GPU stays full. This is the vLLM headline.

Head-of-line blocking is when a quick item is stuck behind a slow one in the same line. You met it on Day 4 with queues and on Day 6 with load balancers. Static batching is head-of-line blocking wearing a GPU costume.

PagedAttention is vLLM's memory trick: store the KV cache in fixed-size blocks that can sit at scattered addresses, like an operating system's pages, instead of one big contiguous reservation per request. It is what makes the slots cheap to allocate and free, so continuous batching is practical. You will not implement it today, but you should know the name and the idea.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these, in this order:
- [Efficient Memory Management for LLM Serving with PagedAttention](https://arxiv.org/abs/2309.06180), the vLLM paper. The one paper that makes inference serving click. Read the intro and section 3 on the memory problem; the KV cache waste they describe is exactly today's Part 1.
- [vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention](https://blog.vllm.ai/2023/06/20/vllm.html), the project's own blog post. The gentle on-ramp to the same idea, with pictures, if the paper is heavy going.
- [Achieve 23x LLM inference throughput and reduce p50 latency](https://www.anyscale.com/blog/continuous-batching-llm-inference) by Anyscale. This is the continuous-batching result in plain language, with the static-versus-continuous diagrams that today's Part 2 turns into numbers.
- [PagedAttention](https://huggingface.co/docs/text-generation-inference/en/conceptual/paged_attention) in the Hugging Face TGI docs. Short and practical, for the memory-layout side.

Watch, after the lab:
- [Efficient LLM Serving with vLLM](https://www.youtube.com/watch?v=oObhZfVdcpI), a Ray and AI21 meetup talk, about 23 minutes. PagedAttention, continuous batching, and KV cache management from the serving-engineering angle.
- Optional, for the KV cache itself: [KV Cache Explained](https://www.youtube.com/watch?v=hafEw3bEu8E) by Ready Tensor, about 12 minutes, walking prefill, decode, and the cache.

### Why the model keeps a KV cache (12 min)

Think about how decode works. To generate token number 501, the model has to let that position attend to all 500 tokens before it. Attention needs a key and a value for each of those earlier tokens. Those keys and values are not cheap to compute, they come out of big matrix multiplies against the model weights. If the model recomputed them from scratch at every single step, generating a long answer would be quadratic misery: step 2 redoes 1 token, step 500 redoes 499, and it piles up.

So the model does the obvious thing. It computes each token's key and value once, when that token first appears, and stores them. Next step, it only computes the key and value for the one new token and reads the rest from storage. That store is the KV cache. It turns an O(n squared) recompute into O(n) with a running cache, which is the only reason decode is fast enough to be a product.

Here is the catch, and it is the whole day. That cache has to live in GPU memory, right next to the weights, because the GPU touches it on every single step. And it grows by one token's worth every step, for every request you are serving at once. A dabbawala remembers which tiffin goes to which office so he does not re-sort the whole stack at every building. Wonderful, until the day he is carrying four hundred tiffins and runs out of arms. The KV cache is the model's memory of the conversation, and memory, it turns out, is exactly what runs out first.

### Memory is the ceiling, not compute (14 min)

Let us put a number on it. Take a 7B-class model served in fp16. Its KV cache, per token, is two tensors (one key, one value), across every layer, across every attention head, each head holding head_dim numbers at two bytes each:

    2 (K and V) x 32 layers x 32 heads x 128 dim x 2 bytes = 512 KiB per token

Half a megabyte, for one token. Now a single request is not one token, it is the whole conversation. A 2000-token chat is already a gigabyte of KV cache. The GPU has, say, 80 GiB. The weights eat about 16 of that, so you have 64 GiB of budget left for all the KV caches of all the requests you are running at once. Divide:

    64 GiB budget / 1 GiB per 2048-token request = 64 requests at once

And watch what happens as conversations get longer, because that is the part people miss:

    2,048-token chats:    64 requests fit
    4,096-token chats:    32 requests fit
    8,192-token chats:    16 requests fit
    16,384-token chats:    8 requests fit

Every time the context doubles, the batch halves. And here is the thing that surprises people coming from a normal-software background: the compute per token barely moves across those rows. A longer context does not make each step meaningfully more arithmetic. What it does is eat memory, and memory is what caps the batch. That is what "decode is memory-bound, not compute-bound" means in practice, and it is why your long-context feature is expensive to serve and not merely slow. The batch size is a memory decision before it is anything else. This is Part 1 of the lab, and it is pure arithmetic you can do on paper.

### Static batching and the slowest passenger (12 min)

So you can fit, say, 16 requests at once. How do you run them? The naive way, and the way the first generation of serving systems worked, is static batching. Gather up to 16 requests, run them together step by step, and when they are all done, gather the next 16.

The problem is that requests do not finish together. One user asked for a yes or no, another asked for a 600-word essay. Under static batching, the short request generates its answer in 20 steps and then its slot just sits there, occupied but idle, because the batch does not release any slot until the longest request in it is done. So fifteen finished requests wait, holding their seats, while one long request grinds on for another five hundred steps. The GPU is doing a sixteenth of the work it could be doing, and you are paying for all of it.

This is head-of-line blocking, and you have measured it twice already. Day 4 was the chaiwala: two separate lines means someone gets stuck behind the person ordering fifteen cutting chais while the other counter stands idle. Day 6 was the load balancer sending a request to a busy backend while another sat free. Same shape every time. One slow item in a shared fate blocks all the quick ones behind it. Static batching is a bus that will not leave the stop until its slowest passenger has finished their journey, which is a strange and wasteful way to run a bus.

### Continuous batching: refill the seat the moment it empties (12 min)

The fix is almost insultingly simple to state, and that is what makes it a great idea. Do not wait for the whole batch. The instant a request finishes and frees its slot, pull the next waiting request off the queue and drop it into that slot, on the very next step. The batch is never a fixed group that lives and dies together, it is a set of slots that are continuously refilled. That is continuous batching, also called iteration-level scheduling, because the scheduler makes a decision every iteration instead of once per batch.

Now the short requests stream through. A 20-token answer finishes, its slot immediately takes a fresh request, and the GPU stays full of useful work instead of full of finished requests politely waiting. The long essay still takes its five hundred steps, but it no longer freezes fifteen other slots while it does. In the lab you will see this take the GPU from 14 percent busy to the 70s, and throughput up by 5x, for the identical workload.

This is Day 4's other lesson, the one next to tail latency: a single shared queue beats many separate lines, because no teller stands idle while customers wait in the wrong line. Continuous batching is one shared queue feeding every slot on the GPU. The piece that makes it practical is PagedAttention, which stops each request from reserving one big contiguous block of memory up front (sized for the longest answer it might produce, almost all of which is wasted). Instead the cache is paged into small blocks, allocated as the answer grows and freed the instant the request ends, so a freed slot is genuinely cheap to hand to the next request. Memory trick underneath, queueing win on top. That is the paper.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers where asked. Then copy your answers into [`notes/day-37-drills.md`](../notes/day-37-drills.md). About 8 minutes each.

D1. KV cache size. A model costs 512 KiB of KV cache per token. A request has a 2000-token prompt and generates 500 tokens. How much KV cache does it hold at the end, and how many such requests fit in a 64 GiB budget?

D2. Memory-bound, not compute-bound. Why does doubling the sequence length roughly halve how many requests you can run at once, while the compute per token barely changes? What does that make the real ceiling during decode?

D3. Static batching, head-of-line blocking. A static batch of 8 requests: seven need 20 output tokens, one needs 500. How many decode steps does the batch take? How many slot-steps are wasted sitting idle, and what is the GPU utilisation? Which earlier day is this?

D4. Continuous batching. Same 8 slots, but now a deep queue of waiting requests and continuous batching. Why does almost all the idle time from D3 vanish? Name the single operation that is the whole trick, and the Day 6 idea it is.

D5. Prefix sharing. A thousand requests all begin with the same long system prompt. How can the KV cache avoid recomputing and re-storing that prefix a thousand times, which week-3 idea is that, and when does it stop helping?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-37-batching/batching.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-37-batching/batching.py).

It is in three parts. Part 1 is the KV cache: it computes, for a 7B-class model on an 80 GiB GPU, how many requests fit in memory as the sequence length grows, and shows the batch halving as the context doubles. Part 2 simulates a workload of 200 requests with varied output lengths and measures throughput and GPU utilisation under static batching versus continuous batching. Part 3 ties both back to Day 2, Day 4 and Day 6.

Standard library only. No model, no API, no network, no numpy. One "step" is one decode pass in which every active request emits one token. The workload is seeded, so your numbers match the reference to the digit, and the whole thing runs in well under a second.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. GPU has 64 GiB left for the KV cache after the weights, and each token costs 0.5 MiB. At a sequence length of 2048 tokens, how many requests fit at once?
- P2. Same budget, but now each conversation is 8192 tokens, four times longer. How many fit now?
- P3. On a 200-request workload with varied output lengths, how many times higher is continuous batching's throughput than static batching's? Guess the multiple. Most people say 2. It is bigger.
- P4. On that same workload, what percent of the GPU's slot-time does static batching actually spend doing useful work?

P3 is the one to feel in your gut first. Write a number down.

### Fill in the TODOs

1. TODO 1 is the KV-cache ceiling: the memory budget divided by one request's footprint. This one line is the whole of Part 1, memory caps the batch.
2. TODO 2 is static batching's cost: a batch lasts as long as its longest request. Head-of-line blocking in one `max()`.
3. TODO 3 is the continuous-batching trick: the instant a slot frees, admit the next waiting request. The difference between static and continuous is this single line.
4. TODO 4 is the headline: the throughput multiple, static steps over continuous steps, for the same work.

```bash
cd labs/day-37-batching
python3 batching.py
```

### What you're going to discover

Part 1 is the memory wall. The same model, the same GPU, and the only thing that changes down the table is how long the conversations are. At 2048 tokens you fit 64 requests; at 8192 you fit 16. Four times the context, a quarter of the batch. Nothing about the compute changed. This is why "memory-bound" is not a slogan, it is the thing setting your batch size.

Part 2 is the queueing result. With output lengths that vary, static batching runs the GPU at about 14 percent useful slot-time, because short requests finish and then sit idle behind the one long request in their batch. Continuous batching refills those freed slots immediately and runs at around 72 percent, for 5x the throughput. Same requests, same 16 slots, same hardware. The control case in the lab, where every request is the same length, comes out as a near tie, which proves the win comes entirely from variance, not from batching alone.

Part 3 says the quiet part out loud. None of this was new. It was Day 4's "keep the expensive server busy," Day 4 and Day 6's "one shared queue beats separate lines," and Day 2's "batch the work." The GPU just made the stakes enormous.

### Traps ⚠️

- Continuous batching comes out around 72 percent in the lab, not 100, and that is honest, not a bug. We drain a fixed batch of 200 requests, so at the very end the queue empties and the last few long requests finish with slots to spare. On a real server that keeps receiving requests, that tail never happens and utilisation sits near 100. The comparison that matters is 14 versus 72.
- The win is from variance in output length, not from continuous batching being magic. Re-read the control case: equal-length requests give a 1.0x tie. If your real traffic genuinely had uniform output lengths, static batching would be fine. It never does.
- Part 1 is deliberately 1024-based (KiB, MiB, GiB as powers of 1024) so the batch numbers come out as clean halvings. If you redo the arithmetic with 1000-based units you will be a few percent off and that is fine, the lesson is the halving, not the third digit.

### Deliverable

[`labs/day-37-batching/RESULTS.md`](../labs/day-37-batching/RESULTS.md) has a skeleton. Paste the output, and write one line: continuous batching gave how many times the throughput of static, and what single change bought it?

---

## Block 4: write (30 min) 📣

Your angle today is the reveal: "I finally understood the vLLM paper, and the surprise is that it is not an AI trick. It is a queueing trick aimed at a GPU. Memory caps the batch, and continuous batching keeps that batch full, for 5x the throughput on the same hardware." The scoreboard, static 14 percent busy versus continuous 72 percent, is the screenshot.

Example posts are on the [Day 37 posts](../shares/day-37-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the throughput multiple you measured for continuous over static, and one thing you still cannot explain.

Day 38 is vector search and embeddings: the index for "things that mean similar," the way a B-tree was the index for "things that sort near," and the recall-versus-latency dial you get to turn. Today you learned why the GPU's memory is the bottleneck and how to keep it busy. Tomorrow you start on the retrieval half of an AI product.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The request holds 2000 + 500 = 2500 tokens at the end, and each token is 512 KiB, so its KV cache is 2500 x 512 KiB = 1,250 MiB, about 1.22 GiB. In a 64 GiB budget (which is 65,536 MiB) you fit 65,536 / 1,250 = 52.4, so 52 such requests at once. Note that it is the total token count, prompt plus generated, that costs memory: a long prompt is just as expensive to hold as a long answer, which is why long system prompts are not free.

D2. The KV cache is 512 KiB per token, so a request's memory footprint is linear in its token count: double the sequence length and you double the memory per request, which halves how many fit in a fixed budget. The compute per decode step, by contrast, is dominated by multiplying the current state against the model weights, and that barely grows with how many tokens came before. So lengthening the context buys you a big memory bill and almost no extra compute. The real ceiling during decode is therefore GPU memory, not FLOPs, which is the whole meaning of "memory-bound."

D3. The batch takes as long as its slowest member, so 500 steps. Useful work is 7 x 20 + 1 x 500 = 640 token-steps. The slots available over those 500 steps are 500 x 8 = 4,000 slot-steps, so utilisation is 640 / 4,000 = 16 percent, and 4,000 - 640 = 3,360 slot-steps are wasted sitting idle. This is head-of-line blocking from Day 4: the seven short requests finish in 20 steps and then hold their seats, idle, for 480 more steps because the batch will not free a slot until the 500-token request is done.

D4. With continuous batching, the seven short requests finish at step 20 and their slots are refilled from the deep queue on the very next step, so the GPU goes back to 8 active requests instead of 1. The idle slot-steps vanish because no slot waits for its batch-mates; it waits only for its own request. The single operation that is the whole trick is "when a slot frees, admit the next waiting request immediately" (the lab's `admit_count`, which tops the active set back up to the limit every step). That is Day 6's one-shared-queue idea: a free teller serves the next person in the single line rather than standing idle because its original group has not all finished.

D5. If a thousand requests share the same long system prompt, the model can compute the key and value tensors for that prefix once and let all thousand requests point at the same cached blocks (prefix sharing, built on PagedAttention's block table, and exposed to you as prompt caching). You neither recompute the prefix a thousand times nor store it a thousand times. That is caching from week 3: compute an expensive result once, reuse it many times, keyed here by the shared prefix. It stops helping the moment the requests diverge: once each request starts generating its own unique continuation, those tokens are unique and must be computed and stored per request. Prefix sharing wins big when a large fixed prefix (a long system prompt, few-shot examples, a shared document) is reused across many calls, and does nothing for the unique tail of each one.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-37-batching/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-37-batching/solution.py).

TODO 1, the KV-cache ceiling, the whole of Part 1. The memory budget divided by one request's footprint:

```python
return budget_bytes // (seq_len * kv_bytes_per_token)
```

TODO 2, static batching's cost, head-of-line blocking in one line. A batch lasts as long as its longest request:

```python
return max(batch_lengths)
```

TODO 3, the continuous-batching trick, the single line that separates it from static. Fill every free slot from the waiting queue, this step:

```python
return min(max_batch - active_count, waiting)
```

TODO 4, the headline. Same work, fewer steps means proportionally more throughput:

```python
return static_steps / continuous_steps
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. Pure simulation, so your numbers match to the digit.

```
==============================================================================
Part 1: the KV cache. GPU MEMORY caps the batch, not compute
==============================================================================
  Model: 32 layers, 32 kv-heads, head_dim 128, fp16.
  Every token of every request keeps a key AND a value tensor cached
  so the model never recomputes the past. That costs, per token:
    2 (K,V) x 32 layers x 32 heads x 128 dim x 2 bytes = 512 KiB/token
  GPU has 80 GiB; weights and overhead take 16 GiB,
  leaving 64 GiB of KV-cache budget.

    seq length    KV per request   requests that fit
           512           256 MiB                 256
         1,024           512 MiB                 128
         2,048          1.00 GiB                  64
         4,096          2.00 GiB                  32
         8,192          4.00 GiB                  16
        16,384          8.00 GiB                   8
        32,768         16.00 GiB                   4

  The compute per token barely moves with sequence length, but the KV
  cache grows linearly with it, so the number of requests you can hold
  at once HALVES every time the conversation doubles in length. A chat
  that grows from 2k to 8k tokens drops your batch from 64 to 16.
  That is why 'memory-bound, not compute-bound' is the first fact of
  LLM serving, and why long contexts are expensive to serve, not just
  slow. The batch size is a memory decision.

==============================================================================
Part 2: static vs continuous batching. Same work, very different bill
==============================================================================
  Workload: 200 requests, all waiting at t=0 (a busy server).
    182 short (8-40 tokens) and 18 long (400-700 tokens).
    13,280 output tokens in total, longest request 661 tokens.
    16 slots fit in memory (the Part 1 ceiling).

  Control, every request exactly 100 tokens (no variance):
    static 1,300 steps, continuous 1,300 steps  ->  1.00x. Basically a tie.
    With no variance there is no slow request to block the others, so
    refilling slots buys you almost nothing. Variance is the enemy.

  Real workload, varied lengths (at 20 ms per decode step):
                     steps   wall time     req/sec    GPU busy
    static           5,797     115.9 s         1.7       14.3%
    continuous       1,148      23.0 s         8.7       72.3%

  Continuous batching has 5.0x the throughput for the SAME requests
  on the SAME hardware. Static ran the GPU at only 14% useful
  slot-time; continuous kept it at 72%.

  Why? In static batching a group of 16 cannot free ANY slot until its
  longest request is done. With a long request in almost every batch,
  15 short requests finish early and then sit idle for hundreds of
  steps, holding slots they are not using. Continuous batching hands a
  freed slot to the next waiting request on the very next step, so the
  short requests stream through instead of waiting. That is the whole
  vLLM throughput result, and it is head-of-line blocking from Day 4:
  one short request should never be stuck behind one long one.

  (Continuous is 72%, not 100%, only because we drain a FIXED
   batch: at the very end the queue empties and the last few long
   requests finish with slots to spare. On a real server that keeps
   receiving requests, that tail never happens and utilisation sits
   near 100%. The honest comparison is still 14% vs 72% here.)

==============================================================================
Part 3: you have seen this before. It is distributed systems, on a GPU
==============================================================================
  Nothing today was new. It was three old lessons aimed at the GPU:

  Day 4, keep the expensive server busy. The GPU is the costliest box
    in the building. An idle slot is money on fire. Continuous batching
    exists to keep utilisation high, exactly the point of the
    utilisation chapter, just with a four-figure-an-hour server.

  Day 4 and Day 6, one shared queue beats separate lines. Static
    batching is 16 people forced to leave the bank together, so the
    whole counter waits on the one person opening a fixed deposit.
    Continuous batching is one shared queue feeding every teller: the
    moment a teller is free, the next person steps up. Same tellers,
    far more customers served per hour. The GPU's KV-cache slots are
    the tellers.

  Day 2 and Day 6, batching itself. Doing many requests in one pass
    beats one at a time, the same reason one batched commit beats a
    thousand fsyncs. The GPU only earns its keep when the batch is full.

  So the AI serving stack is your week 1-to-5 brain with a GPU in the
  middle. The KV cache is a memory-budget problem. Continuous batching
  is a queueing problem. Your token bill is a utilisation problem. The
  model is the magic; the engineering is everything around it.

==============================================================================
Scoreboard
==============================================================================
  P1 requests that fit at 2048       you =   64.0   actual =    64.0 reqs       close enough
  P2 requests that fit at 8192       you =   16.0   actual =    16.0 reqs       close enough
  P3 continuous throughput mult      you =    6.0   actual =     5.0 x       close enough
  P4 static GPU utilisation          you =   15.0   actual =    14.3 %       close enough

==============================================================================
The number to carry
==============================================================================
  At 2048 tokens, 64 requests fit in the KV-cache budget; at 8192 only
  16. Memory, not compute, sets the batch, and long contexts shrink it.
  Then continuous batching served the same 200 requests 5.0x faster than
  static, because static left the GPU 14% busy while short requests
  sat trapped behind long ones. The KV cache is a memory-budget
  problem and batching is a queueing problem. You solved both in
  weeks 1 to 6; the GPU just raised the stakes.
```

Part 1 is the memory wall drawn out in full. Read the table top to bottom: the model and the GPU never change, only the conversation length does, and the batch you can fit falls from 256 requests at 512 tokens to 4 requests at 32k. Every doubling of the context halves the batch, because the KV cache is linear in token count and it is competing for the same 64 GiB. The compute per token is roughly flat across that whole table. That gap, memory growing while compute stays put, is the precise meaning of "decode is memory-bound," and it is why a long-context feature costs you batch size, which is to say money.

Part 2 is the queueing result, and the control case is the proof. When every request is exactly 100 tokens, static and continuous tie at 1.00x, because with no variance there is no slow request to trap the others behind. Introduce realistic variance, a mix of short answers and long essays, and static batching collapses to 14 percent utilisation: almost every batch of 16 holds a long request, so fifteen short requests finish and sit idle for hundreds of steps holding slots they are not using. Continuous batching refills each freed slot on the next step and runs the same work in a fifth of the time. The 5x is not a model improvement. It is a scheduler that refuses to let a short request wait behind a long one.

Part 3 is the point of the whole week in one screen. The KV cache is a memory-budget problem you could have reasoned about in week 2. Continuous batching is the single-shared-queue result from Day 4 and the load-balancing instinct from Day 6. Batching itself is Day 2. Bring your distributed-systems brain to the GPU and the famous paper reads like a tidy application of things you already know, which is exactly how to read the rest of this week.

</details>
