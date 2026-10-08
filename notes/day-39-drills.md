---
title: "Day 39 drills"
parent: "Day 39: RAG, and why it mostly fails at retrieval"
grand_parent: "Week 6: AI systems"
nav_order: 2
---

# Day 39 drills

Paper first, with numbers where the drill asks for them. Then copy your answers into your fork. About 8 minutes each. The answers are on the Day 39 page, under Solutions.

D1 (the ceiling): a RAG pipeline retrieves the chunk that actually holds the answer only 60 percent of the time (recall@k = 60%). On the other 40 percent, the right chunk is not in the context handed to the model. What is the best the generator can possibly do on those 40 percent, and what does that say about the claim "most RAG problems are retrieval problems"?

D2 (the chunk-size knob): an answer sentence is about 15 words long. You chunk the same corpus three ways: 5 words per chunk, 40 words per chunk, and 400 words per chunk. For each, say what happens to the answer sentence and to the similarity score of the chunk that holds it, and which of the three you would expect to retrieve the answer. Why does recall peak in the middle rather than rising with size?

D3 (why idf matters, and why large chunks blur): you build TF-IDF over 100 chunks. Term A appears in 2 chunks, term B appears in 90. Using idf = log(N / df), compute both weights and say which term discriminates better. Now you re-chunk so coarsely that there are only 5 chunks and almost every word appears in almost every chunk. What happens to idf, and how does that explain a too-large chunk losing its ability to tell chunks apart?

D4 (the vocabulary wall): a user asks "how do I cancel my subscription," but the help doc says "to terminate your plan, open billing settings." A pure TF-IDF (keyword) retriever is used. Will it find the right chunk? Explain in terms of matching words versus matching meaning, then name the fix from Day 38 and say what a reranker adds on top of it.

D5 (the threshold trade, and bringing week 1 to 5 back): your retriever keeps only chunks whose similarity clears a relevance threshold. You raise the threshold. What happens to precision (how much of the retrieved text is relevant) and to recall (how often the answer survives)? Then: the retrieval step is milliseconds but the LLM call behind it is slow and metered per token. Name two things from earlier weeks you would put around this endpoint and what each buys you.
