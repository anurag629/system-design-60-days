---
title: "Day 37 drills"
parent: "Day 37: the KV cache and continuous batching"
grand_parent: "Week 6: AI systems"
nav_order: 2
---

# Day 37 drills

Paper first, with numbers where the drill asks for them. KV cache memory, batching, and the queue underneath it all. About 8 minutes each.

D1 (KV cache size. A model costs 512 KiB of KV cache per token. A request has a 2000-token prompt and generates 500 tokens. How much KV cache does it hold at the end, and how many such requests fit in a 64 GiB budget?):

D2 (memory-bound, not compute-bound. Why does doubling the sequence length roughly halve how many requests you can run at once, while the compute per token barely changes? What does that make the real ceiling during decode?):

D3 (static batching, head-of-line blocking. A static batch of 8 requests: seven need 20 output tokens, one needs 500. How many decode steps does the batch take? How many slot-steps are wasted sitting idle, and what is the GPU utilisation? Which earlier day is this?):

D4 (continuous batching. Same 8 slots, but now a deep queue of waiting requests and continuous batching. Why does almost all the idle time from D3 vanish? Name the single operation that is the whole trick, and the Day 6 idea it is):

D5 (prefix sharing. A thousand requests all begin with the same long system prompt. How can the KV cache avoid recomputing and re-storing that prefix a thousand times, which week-3 idea is that, and when does it stop helping?):
