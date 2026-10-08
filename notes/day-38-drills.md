---
title: "Day 38 drills"
parent: "Day 38: vector search and embeddings"
grand_parent: "Week 6: AI systems"
nav_order: 2
---

# Day 38 drills

Written on paper first. Embeddings, exact versus approximate search, recall@k, and the nprobe dial.

D1 (10,000,000 vectors of dimension 768, one similarity about 768 multiply-adds: roughly how many multiply-adds per brute-force query, how long at 1 billion/sec on one core, and why this forces an index as the corpus grows):

D2 (IVF with N vectors in C equal cells, probing nprobe of them: about how many vectors scored per query and the rough speedup over brute force, worked for N=1,000,000, C=1,000, nprobe=10):

D3 (true top-10 known, ANN returns 10 ids of which 8 are in the true set: recall@10, whether it clears a 0.95 target, and the first knob you would turn):

D4 (IVF with nprobe=1: why a genuinely nearest neighbour can be missed even though the index is correct, which queries are most at risk, and how raising nprobe fixes it and at what cost):

D5 (embedding of 1,536 four-byte floats: bytes per vector, memory to hold 10,000,000 of them raw, and one thing a vector database does to shrink that number):
