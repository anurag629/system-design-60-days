---
title: "Day 37 posts"
parent: "Day 37: the KV cache and continuous batching"
grand_parent: "Week 6: AI systems"
nav_order: 3
---

# Day 37 posts: LinkedIn and X

The scoreboard is the screenshot: continuous batching at 5x the throughput of static, and the memory table where the batch halves every time the context doubles. Swap in your own numbers and voice.

## LinkedIn

Day 37 of 60 days of system design. Today I understood the vLLM paper, and the punchline is that it is not really an AI trick. It is a queueing trick, pointed at a GPU.

Two things decide your GPU bill when you serve an LLM, and the model's cleverness is neither of them.

First, memory, not compute, caps how many requests you can run at once. The model caches a key and value tensor for every past token so it never recomputes the history. That KV cache grows with the length of the conversation. I worked it out for a 7B-class model on an 80 GiB GPU:

    2,048-token chats:   64 requests fit at once
    8,192-token chats:   16 requests fit at once

The batch halves every time the context doubles. Long conversations are expensive to serve, not just slow, and the batch size is a memory decision before it is anything else.

Second, how you share that batch decides your throughput. I simulated 200 requests with varied output lengths, 16 slots, two ways:

    static batching:      14% GPU utilisation
    continuous batching:  72% GPU utilisation, 5x the throughput

Static batching runs a fixed group together and frees no slot until the slowest request in the group is done. So fifteen short requests finish and then sit idle for hundreds of steps, holding slots they are not using, stuck behind one long one. That is head-of-line blocking, the exact thing I measured back on Day 4 with a single shared queue beating separate lines.

Continuous batching hands a freed slot to the next waiting request on the very next step. The GPU stays full. One shared queue feeding every slot, instead of everyone forced to leave the counter together.

So the whole AI serving stack turned out to be my weeks 1 to 5 brain with a GPU in the middle. The KV cache is a memory-budget problem. Continuous batching is a queueing problem. The token bill is a utilisation problem.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #llm #inference #learninginpublic

## X thread

**1/**

Today I understood the vLLM paper. The surprise: it is not an AI trick. It is a queueing trick aimed at a GPU.

Day 37 of 60 days of system design.

**2/**

First fact of LLM serving: memory caps the batch, not compute.

The model caches a key/value tensor for every past token (the KV cache) so it never recomputes history. That cache grows with conversation length.

7B model, 80 GiB GPU:

2k chats: 64 fit
8k chats: 16 fit

**3/**

The batch halves every time the context doubles. Long conversations are expensive to serve, not just slow. Your batch size is a memory decision first.

**4/**

Second fact: how you share the batch decides throughput.

I ran 200 requests with varied output lengths, 16 slots, two ways.

static:      14% GPU busy
continuous:  72% GPU busy, 5x throughput

Same requests. Same hardware.

**5/**

Static batching frees no slot until the SLOWEST request in the group finishes. So 15 short requests finish early and sit idle, holding slots, stuck behind one long one.

That is head-of-line blocking. I measured it on Day 4 as "one shared line beats separate lines."

**6/**

Continuous batching hands a freed slot to the next waiting request on the very next step. The GPU stays full.

One shared queue feeding every slot, instead of everyone forced to leave the counter together.

**7/**

So the AI serving stack is just distributed systems with a GPU in the middle.

KV cache = a memory-budget problem.
Continuous batching = a queueing problem.
Token bill = a utilisation problem.

The model is the magic. The engineering is everything around it.

Code: github.com/anurag629/system-design-60-days
