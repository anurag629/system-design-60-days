---
title: "Day 39 posts"
parent: "Day 39: RAG, and why it mostly fails at retrieval"
grand_parent: "Week 6: AI systems"
nav_order: 3
---

# Day 39 posts: LinkedIn and X

The scoreboard is the screenshot: recall at a good chunk size versus the two broken extremes, and the crash when the query uses synonyms. Swap in your own numbers and voice.

## LinkedIn

Day 39 of 60 days of system design. Today I built a tiny RAG system in pure Python and then broke it on purpose, and it changed how I think about "the LLM got it wrong."

Here is the thing nobody shows in a RAG demo. The generator is downstream. Before the model writes a single word, a retriever has already picked which chunks of your documents it gets to read. If the right chunk is not in that shortlist, no model on earth can answer. So I stopped measuring the model and measured retrieval.

I used a small corpus, chunked it, built plain TF-IDF vectors, and asked 10 questions with a known answer sitting in the text. The metric is recall@k: did the chunk holding the answer make the retrieved shortlist?

At a sensible chunk size, recall was 100 percent. Then I changed only the chunk size.

    too large (200 words):  20%
    good   (28 words):     100%
    too small (6 words):    60%

Too large, and the answer is one sentence drowned in a wall of unrelated text, so the chunk's similarity score sinks below the relevance threshold and the retriever throws it away. Too small, and the answer is split across several chunks, so no single one is similar enough to surface. Recall peaks in the middle. Chunk size is a real tuning knob, not a default you accept.

Then I kept the good chunk size and only reworded the questions with synonyms the documents never used: "swift" for "fast," "beast" for "animal," "dwells" for "lives."

    matched wording:  100%
    synonym wording:    0%

Zero. TF-IDF matches words, not meaning, and a word the corpus has never seen has nothing to match. This is the exact gap that semantic embeddings close, and why a reranker usually sits on top.

The lesson I am taking: RAG is a retrieval problem wearing a generation costume. "RAG is bad" is almost always "retrieval is bad."

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #rag #llm #learninginpublic

## X thread

**1/**

I built a tiny RAG system in pure Python today and broke it on purpose. The result killed a belief I had about LLMs.

Day 39 of 60 days of system design.

**2/**

RAG demos always show the model. But the model is downstream. A retriever decides which chunks of your docs it even gets to read. If the answer chunk is not in that shortlist, no model can save you.

So I stopped testing the model and tested retrieval.

**3/**

Setup: small corpus, chunk it, plain TF-IDF vectors, 10 questions with a known answer in the text. Metric = recall@k: did the chunk holding the answer make the shortlist?

Good chunk size: 100%. Then I changed ONLY the chunk size:

too large: 20%
good:     100%
too small: 60%

**4/**

Too large: the answer is one sentence lost in a wall of text, so the chunk's similarity drops below the relevance cutoff and gets discarded.

Too small: the answer is split across chunks, so no single one is similar enough to surface.

Recall peaks in the middle. Chunk size is a knob.

**5/**

Then I kept the good size and only swapped in synonyms the docs never use. "swift" for "fast," "beast" for "animal."

matched: 100%
synonym:   0%

Zero. TF-IDF matches words, not meaning. A word the corpus never saw has nothing to match.

**6/**

That is the gap semantic embeddings close, and why rerankers exist.

The takeaway: RAG is a retrieval problem wearing a generation costume. "RAG is bad" is almost always "retrieval is bad."

Code: github.com/anurag629/system-design-60-days
