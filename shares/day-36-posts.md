---
title: "Day 36 posts"
parent: "Day 36: how LLM inference actually works"
grand_parent: "Week 6: AI systems"
nav_order: 3
---

# Day 36 posts: LinkedIn and X

The scoreboard makes a good screenshot: one output token costs about 150 prompt tokens, and a batch-1 decode step does 1 FLOP per byte while the GPU can do 150. Swap in your own numbers and voice.

## LinkedIn

Day 36 of 60 days of system design. Week 6 is AI systems, and I started where everything else follows from: how an LLM actually serves one request. I built a small cost model, no GPU and no API, just the physics, and the numbers reframed how I think about the token bill.

An LLM answers in two phases. Prefill reads your whole prompt in one parallel pass, so all the input tokens share a single trip through the model. That pass is the time-to-first-token. Decode then writes the answer one token at a time, and here is the catch: every single output token is a full pass over the model, reading all 14 GB of weights again to produce one more word.

So I compared 500 tokens of input against 500 tokens of output on the same toy machine:

    500 prompt tokens  (one prefill pass):     23 ms
    500 output tokens  (500 decode passes):  3500 ms

Same token count. Output was 150 times slower. That is not a tuning problem, it is the shape of the thing: input is parallel, output is sequential.

Then the part that explains it. One decode step reads 14 GB of weights to do about 14 GFLOPs of maths. That is 1 FLOP for every byte it drags in, while the GPU can do 150 FLOPs in the time it reads one byte. The compute units sit idle 99 percent of the step, waiting on memory. LLM decode is memory-bound, not compute-bound, and no faster chip fixes a bottleneck that is about bandwidth.

The way out is batching. One 14 GB read can feed many requests at once, so you reuse the expensive part. In the model, going from batch 1 to batch 150 kept the step time flat but multiplied throughput 150 times. That is tomorrow's topic, and it is why the KV cache and continuous batching exist.

The practical takeaway for anyone shipping an AI feature: total latency is time-to-first-token plus (output tokens times time-per-token), a straight line in the length of the answer. If you want it faster and cheaper, cut the output before you touch anything else.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #llm #aiinfra #learninginpublic

## X thread

**1/**

Day 36 of 60 days of system design. I built a tiny cost model of how an LLM serves one request. No GPU, no API, just the physics. It changed how I read my token bill.

**2/**

An LLM answers in two phases.

Prefill: reads your whole prompt in ONE parallel pass. That is your time-to-first-token.

Decode: writes the answer one token at a time. Each output token is a full pass over the model.

**3/**

So 500 tokens of INPUT vs 500 tokens of OUTPUT, same machine:

prompt (1 prefill pass):   23 ms
output (500 passes):     3500 ms

150x slower for the same token count. Input is parallel, output is sequential.

**4/**

Why is one decode step so slow? It reads all 14 GB of weights to produce ONE token.

14 GFLOPs of maths, 14 GB moved = 1 FLOP per byte.
The GPU can do 150 FLOPs per byte.

The compute sits idle 99% of the step. Decode is MEMORY-bound.

**5/**

A faster chip does not fix a bandwidth problem. Batching does.

One 14 GB read can feed many requests at once. In the model, batch 1 to batch 150 kept step time flat and multiplied throughput 150x. That is the KV cache + continuous batching story (Day 37).

**6/**

The rule to carry:

total latency = TTFT + (output tokens x time-per-token)

A straight line in output length. Want it faster and cheaper? Trim the output first. Everything else is a rounding error next to that.

Code: github.com/anurag629/system-design-60-days
