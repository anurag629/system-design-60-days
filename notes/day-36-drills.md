---
title: "Day 36 drills"
parent: "Day 36: how LLM inference actually works"
grand_parent: "Week 6: AI systems"
nav_order: 2
---

# Day 36 drills

Paper first, with numbers. Use the lab's toy machine throughout: a 7B model in fp16 (14 GB of weights to read per pass, about 14 GFLOPs per token), on a GPU with 2 TB/s of memory bandwidth and 300 TFLOP/s of compute. Then copy your answers into this file. About 8 minutes each.

D1 (prefill and TTFT. Prefilling a 1,000-token prompt is one parallel pass: FLOPs are 1,000 tokens' worth, bytes read are the 14 GB of weights once. Work out the compute time and the memory time, say which wins, and give the TTFT):

D2 (decode and total latency. A decode step is memory-bound at about 7 ms (TPOT), and the TTFT from D1 is the start-up cost. Give the total latency for a 300-token reply, and what fraction of it is decode):

D3 (the memory wall. A batch-1 decode step reads 14 GB and does 14 GFLOPs. Compute its arithmetic intensity in FLOP/byte and the machine's balance point (compute / bandwidth). Is the step memory-bound or compute-bound, and by what factor do the compute units sit idle):

D4 (batching. One 14 GB weight read can serve a whole batch at once. Roughly what batch size makes the step compute-bound (hint: the balance point from D3), and what is the throughput in tokens per second at batch 1 versus batch 64? Why does batching lift throughput but not the latency of a single lonely request):

D5 (the token bill. Same 1,000-token prompt, two replies: 100 output tokens and 1,000 output tokens, with TPOT 7 ms and the TTFT from D1. Give the latency ratio. If output tokens are priced at 3x input tokens, give the cost ratio. In one line, why do you trim the output before anything else):
