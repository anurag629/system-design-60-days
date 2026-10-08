---
title: "Day 39: RAG, and why it mostly fails at retrieval"
parent: "Week 6: AI systems"
nav_order: 4
has_children: true
---

# Day 39
## RAG, and why it mostly fails at retrieval 🔎

Today's one idea: a RAG system has two halves, retrieval and generation, and almost everything that goes wrong lives in the first half. The model is downstream. Before it writes a single word, a retriever has already decided which chunks of your documents it gets to read, and if the right chunk is not in that pile, the smartest model on earth cannot answer. So when people say "RAG is bad," what they almost always mean is "our retrieval is bad." Today you build a tiny RAG retriever, measure how often it actually finds the answer, and then break it two ways that every real system breaks.

Yesterday (Day 38) you built a vector index and watched recall trade off against speed. Today you put retrieval to work inside RAG and find out that the chunk you feed the model matters more than the model.

---

## Before you start ⏪

You want Day 38 fresh: a vector index stores embeddings and finds nearest neighbours, and recall is "did the right thing come back." Today's lab uses the simplest possible vectors, TF-IDF, so you can see every moving part in pure Python, but the shape is identical to a real embedding retriever. Keep the week 6 framing in mind too: RAG is really cache-aside plus retrieval, the same pattern you met in week 3, except the "cache" is your document store and the lookup is fuzzy.

If the words embedding, cosine similarity and recall are comfortable, you are ready. If they are not, skim Day 38 first.

---

## Words you will meet today 📖

Retrieval-augmented generation, RAG, is the pattern where you fetch relevant text from your own documents and paste it into the prompt, so the model answers from your data instead of only its training. Two steps: retrieve, then generate.

A chunk is one piece of a document after you split it up. You retrieve chunks, not whole documents, because a whole document is too big to rank well and too big to stuff into a prompt.

Chunking is the act of splitting documents into chunks, and the chunk size is a tuning knob that quietly decides how well retrieval works.

TF-IDF (term frequency times inverse document frequency) is a plain, old way to turn text into a vector: count the words, then weight each by how rare it is across the corpus, so common words fade and distinctive words count. It matches words, not meaning.

Recall@k is today's scoreboard: over a set of test questions with known answers, how often did the chunk holding the answer land in the top k that retrieval returned. If it did not, generation was doomed before it began.

A relevance threshold is the minimum similarity score a chunk must clear to be handed over at all. Below it, a match is treated as noise and dropped. Real vector search does this, not a blind top k.

Reranking is a second, slower pass that re-scores the shortlist by reading the query and each chunk together, to fix the order the first cheap pass got roughly right.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Chunking strategies for LLM applications](https://www.pinecone.io/learn/chunking-strategies/) from Pinecone. The practical heart of today. Why chunk size is a real decision, what fixed-size, sentence and semantic chunking trade, and how it shows up in retrieval quality.
- [Introducing contextual retrieval](https://www.anthropic.com/news/contextual-retrieval) from Anthropic. A clear, honest look at why naive chunk-and-embed retrieval misses, and how embeddings, a keyword pass (BM25) and reranking stack up to fix it. This is today's Part 3 with the real tools.
- [Seven failure points when engineering a RAG system](https://arxiv.org/abs/2401.05856), a short paper that catalogues where RAG breaks in production. Notice how many of the seven are retrieval problems, not model problems.

Watch, after the lab:
- [What is retrieval-augmented generation?](https://www.youtube.com/watch?v=T-D1OfcDW1M) by IBM Technology, about 7 minutes. Marina Danilevsky gives the cleanest short explanation of the retrieve-then-generate loop and why grounding matters.
- Optional, and directly about today's Part 2: [The 5 levels of text splitting for retrieval](https://www.youtube.com/watch?v=8OJC21T2SL4) by Greg Kamradt, about an hour. A deep, visual tour of chunking, from naive fixed-size up to semantic splitting. Dip in rather than watching it all.

### RAG in one breath, and where it actually breaks (12 min)

A RAG system does something very simple. A question comes in. You turn it into a vector, search your document store for the chunks whose vectors are closest, take the top few, paste them into the prompt above the question, and ask the model to answer using that text. That is the whole pattern. Retrieve, then generate.

Here is the part that took me a while to accept. The clever, expensive, much-discussed half is generation, and it is almost never where RAG fails. The model is only as good as the text you handed it. If retrieval surfaces the wrong chunks, the model has three options, all bad: it guesses from its training and maybe hallucinates, it answers from the irrelevant text you gave it, or if it is well behaved it says it does not know. None of those is the right answer, and none of them is the model's fault. The evidence simply was not in the room.

So the honest way to debug RAG is to stop staring at prompts and measure retrieval on its own. That is what recall@k does. Take a set of questions whose answers you know live in specific chunks, run retrieval, and count how often the right chunk comes back in the top k. That single number is a ceiling on your whole system. If retrieval recall is 60 percent, then 40 percent of your questions are unanswerable no matter what you do to the model, the prompt or the temperature. Today's lab makes you feel that ceiling, and the two ordinary mistakes that push it down.

### Chunk size, the knob everyone sets once and forgets (14 min)

The first mistake is chunking. You have to split documents before you can retrieve pieces of them, and almost everyone picks a chunk size on day one, moves on, and never revisits it. It turns out to be one of the highest-leverage numbers in the system, and getting it wrong quietly wrecks recall at both ends.

Think about what a chunk has to be. It has to be small enough that it is mostly about one thing, so its vector points in a clear direction, and big enough that a whole answer fits inside it with a little context around it. Those two pulls fight, and the sweet spot is in the middle.

Chop too small, say a handful of words per chunk, and a single answer gets split across three or four chunks. Now no chunk contains the whole answer. The chunk with the most of it carries maybe one or two of the words your question is asking about, so its similarity is weak, and it sinks underneath hundreds of other little scraps that happen to share a common word. Even if you did retrieve that fragment, it is missing the context the model needs to use it. The answer is in your corpus, split into pieces too small to find.

Chop too large, say a few hundred words per chunk, and the opposite happens. The answer is one sentence sitting in a wall of unrelated text. When you build the chunk's vector, those few matching words get averaged over everything else in the chunk, so the chunk's similarity to the question drops. In a real system with a relevance threshold, the right chunk now scores so low that the retriever discards it as noise, even though the answer is literally inside it. The answer is in your corpus, buried too deep to surface.

Plot recall against chunk size and you get an inverted U. Low at tiny sizes, low at huge sizes, a plateau of good retrieval in between. In the lab you will watch recall climb from 60 percent at tiny chunks up to 100 percent in the middle and back down to 20 percent at huge chunks, on the same corpus and the same questions, changing nothing but the chunk size. After that you will never set a chunk size by reflex again.

### The vocabulary wall, and why TF-IDF cannot climb it (12 min)

The second mistake is subtler, and it is really a limitation, not a mistake. TF-IDF matches words. If the question and the document use the same words, it works beautifully. If they use different words for the same thing, it goes blind.

Picture a help centre. The document says "to terminate your plan, open billing settings." The user types "how do I cancel my subscription." A human sees those are the same request. A keyword retriever sees almost no shared words, scores the chunk near zero, and never retrieves it. In the lab you will take questions that retrieve perfectly, reword them with synonyms the corpus never uses (swift for fast, beast for animal, dwells for lives) and watch recall fall straight to zero. Same questions, same answers sitting right there in the text, and retrieval cannot find them, because a word the corpus has never seen has nothing to match against.

This is exactly the gap that semantic embeddings close (Day 38). A good embedding puts "cancel subscription" and "terminate plan" near each other in vector space because they mean the same thing, not because they share letters. That is why real RAG uses dense embeddings rather than pure keyword matching, and often both together: a keyword pass is precise when the words do match, and an embedding pass rescues the cases where they do not. On top of that sits a reranker, a slower model that reads the question and each shortlisted chunk together and reorders them, buying precision at the very top of the list where it matters most. Our toy uses TF-IDF on purpose, so you feel the wall that embeddings were invented to get over.

### It is still a system (8 min)

One last thing, because this is week 6 and the whole point of the week is that AI serving is distributed systems with a GPU in the middle. Retrieval is the fast, cheap half of RAG, often a few milliseconds. The LLM call behind it is the slow, metered half. So the same tools you built all course still apply here. A cache in front catches repeated or near-repeated questions so you do not pay the model twice for the same answer (week 3, and semantic caching is Day 41). A queue absorbs spikes so a traffic burst does not melt your model endpoint (week 4). And tail latency comes back to bite the moment one request fans out into several, a retrieval plus a rerank plus a generation, because your p99 is set by the slowest step in the chain (Day 4). RAG is not a magic box. It is a pipeline, and you already know how to reason about pipelines.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers where asked. Then copy your answers into [`notes/day-39-drills.md`](../notes/day-39-drills.md). About 8 minutes each.

D1. The ceiling. A RAG pipeline retrieves the chunk holding the answer only 60 percent of the time. On the other 40 percent, what is the best the generator can possibly do, and what does that say about "most RAG problems are retrieval problems"?

D2. The chunk-size knob. An answer sentence is about 15 words. You chunk at 5, 40, and 400 words. For each, say what happens to the answer and to the similarity of the chunk that holds it, and why recall peaks in the middle rather than rising with size.

D3. Why idf matters, and why large chunks blur. Over 100 chunks, term A is in 2 and term B is in 90. Compute idf = log(N / df) for both and say which discriminates better. Then re-chunk to just 5 chunks where almost every word is in almost every chunk; what happens to idf, and how does that explain a too-large chunk losing its edge?

D4. The vocabulary wall. The user asks "how do I cancel my subscription," the doc says "to terminate your plan, open billing settings," and the retriever is pure TF-IDF. Will it find the chunk? Explain words versus meaning, name the Day 38 fix, and say what a reranker adds.

D5. The threshold trade, and bringing weeks 1 to 5 back. You raise the relevance threshold. What happens to precision and to recall? Then, given that retrieval is milliseconds but the LLM call is slow and metered, name two things from earlier weeks you would put around this endpoint and what each buys you.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-39-rag/rag.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-39-rag/rag.py).

It is a RAG retriever in pure Python, no model, no API, no network, no numpy. The generation step is stubbed, because the lesson is retrieval. It has three parts. Part 1 builds the retriever (chunk, TF-IDF vectors, cosine similarity, keep the top few above a relevance threshold) and measures recall@3 over 10 questions whose answers live in the corpus. Part 2 sweeps the chunk size and shows recall rising then falling. Part 3 keeps the good chunk size but rewords the questions with synonyms and watches recall collapse.

It is deterministic (no randomness at all) and runs in well under a second.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. At a sensible chunk size, over 10 matched questions, what recall@3 do you expect (percent)?
- P2. Re-chunk far too large, so the answer is diluted. Recall@3 now?
- P3. Re-chunk far too small, so the answer is split. Recall@3 now?
- P4. Keep the good size but ask with synonyms the corpus never uses. Recall@3 now?

P4 is the one to feel in your gut first. The answer is sitting right there in the text. Write down how often you think a keyword retriever still finds it.

### Fill in the TODOs

Four numbered lines, the whole retrieval pipeline.

1. TODO 1 is the term count, turning a chunk or a query into a bag of word counts. The start of every vector.
2. TODO 2 is the idf weight, log(n_chunks / doc_freq), the one line that makes rare words count and common words fade.
3. TODO 3 is cosine similarity, the dot product over the two lengths, how a query is compared to a chunk by direction rather than by raw overlap.
4. TODO 4 is the measurement, whether the gold chunk made the retrieved shortlist. This is recall, one membership test.

```bash
cd labs/day-39-rag
python3 rag.py
```

The file refuses to run until you fill in `PREDICTIONS`, and stops cleanly telling you which TODO to fill if one is still blank. If you get stuck, `solution.py` in the same folder is the full working version.

### What you're going to discover

Part 1 is the baseline. With sensible chunks, retrieval finds the answer chunk in the top 3 every time, 100 percent. Good. Retrieval works when you treat it with respect.

Part 2 is the knob. Nothing changes except chunk size, and recall traces a clean arch: around 60 percent when chunks are tiny, 100 percent across a healthy middle band, and down to 20 percent when chunks are huge. The too-small end is the answer split into unfindable fragments. The too-large end is the answer diluted until its chunk scores below the relevance threshold and gets thrown away. Same corpus, same questions, wildly different recall, purely from one number.

Part 3 is the wall. Keep the good chunk size, reword the same 10 questions with synonyms, and recall drops to zero. The answers never moved. TF-IDF just cannot match a word it has never seen. That is the single clearest argument for semantic embeddings you will ever get to run yourself.

### Traps ⚠️

- Do not read the too-large result as "the retriever could not find it." It found it, the chunk was often still rank 1, but its similarity had dropped below the relevance threshold, so a real system discards it as a weak match. The threshold is the point. Dilution lowers the score, and the score is what gets you kept or dropped.
- Recall is coarse with 10 questions, it moves in steps of 10 percent. That is fine. You are after the shape of the curve and the size of the gaps, not a third decimal place.
- The synonym queries still share a word or two with the corpus by accident (like "ocean" or "river"), so a couple do not fall all the way to nothing on their own. The aggregate still lands at zero, because a word or two is not enough to clear the threshold. Trust the aggregate.

### Deliverable

[`labs/day-39-rag/RESULTS.md`](../labs/day-39-rag/RESULTS.md) has a skeleton. Paste your output, and write one line: at a good chunk size retrieval found the answer how often, and what did it fall to when you broke the chunk size and when you used synonyms?

---

## Block 4: write (30 min) 📣

Your angle today is the reframe: "I built a RAG system and broke it on purpose, and it changed how I read 'the LLM got it wrong.' The model is downstream. If retrieval does not surface the right chunk, nothing the model does can fix it, and I watched recall fall from 100 percent to 20 percent just by changing the chunk size, and to zero by changing a few words to synonyms." The scoreboard is the screenshot.

Example posts are on the [Day 39 posts](../shares/day-39-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the recall numbers you measured at a good chunk size versus the two broken extremes, and one thing you still cannot explain.

Day 40 is agents: a single user request that fans out into many model calls, a reasoning loop, tools, and a token bill that balloons because one question becomes twenty. Today you saw that one request hides a retrieval step. Tomorrow you watch one request become a whole tree of them, and tail latency and cost come straight back from weeks 1 and 4.

---

## Solutions 🔑

Open these only after you have done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. On the 40 percent of questions where the answer chunk is not retrieved, the generator's ceiling is basically zero correct answers. The evidence is not in the context, so a well-behaved model says it does not know, and a less careful one hallucinates or answers from whatever irrelevant text it was handed. You cannot generate your way to an answer that is not in the room. That is the whole point: retrieval recall is a hard ceiling on end-to-end accuracy, so improving the model does nothing for those 40 percent while improving retrieval does. Most RAG failures are retrieval failures wearing a generation mask.

D2. At 5 words per chunk, the 15-word answer is split across about three chunks, so no chunk holds the whole thing; the best chunk carries a third of the query's words, its similarity is weak, and it is probably missed (and useless without context even if retrieved). At 40 words, the answer sits whole in one chunk with a little surrounding context, all the query's words co-occur, similarity is high, and it is retrieved. At 400 words, the answer is one sentence among roughly 27, its matching words are averaged over the whole chunk, similarity drops toward or below the threshold, and it can be discarded. Recall peaks in the middle because you need the answer whole, which rules out too small, and concentrated, which rules out too large.

D3. idf_A = log(100 / 2) = log(50) which is about 3.9; idf_B = log(100 / 90) = log(1.11) which is about 0.1. Term A, the rare one, gets roughly 40 times the weight, because a rare word tells you a lot about which chunk you are in and a near-universal word tells you almost nothing. Now re-chunk to 5 chunks where almost every word appears in almost every chunk: df approaches N, so idf = log(5 / 5) = log(1) = 0, and every term's weight collapses toward zero. The chunk vectors become nearly identical and undiscriminating, which is exactly why a too-large chunking loses its ability to tell one chunk from another: there is no rarity left to separate them.

D4. Pure TF-IDF will almost certainly miss. "cancel" and "subscription" share no tokens with "terminate," "plan" and "billing," so the keyword overlap is near zero, the similarity is low, and the chunk is never retrieved. It is a words-versus-meaning problem: the request is identical in meaning but disjoint in vocabulary. The Day 38 fix is semantic embeddings, dense vectors that place "cancel subscription" and "terminate plan" close together because they mean the same thing, so the match survives the vocabulary gap. A reranker adds a second, slower pass that reads the query and each shortlisted chunk together and reorders them, raising precision at the top of the list where the model actually reads.

D5. Raising the threshold raises precision, because only strong matches survive, so there is less irrelevant text in the context, and it lowers recall, because borderline-but-correct chunks now get dropped, so you miss more answers. It is the standard precision-versus-recall dial, and you set it by how much you fear a wrong answer versus a missed one. Around the endpoint, from earlier weeks: a cache for repeated or near-repeated questions (week 3) so you do not pay the slow model twice for the same query, and a queue in front (week 4) to absorb spikes and smooth bursty traffic onto the metered model. A fair third answer is tail latency (Day 4): once a request fans out into retrieve plus rerank plus generate, your p99 is set by the slowest step, so you budget for it.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-39-rag/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-39-rag/solution.py).

TODO 1, the term count, the start of every vector:

```python
return Counter(tokens)
```

TODO 2, the idf weight, the line that makes rare words count:

```python
return math.log(n_chunks / doc_freq)
```

TODO 3, cosine similarity, comparing by direction not raw overlap:

```python
return dot(vec_a, vec_b) / (norm_a * norm_b)
```

TODO 4, the measurement, did the answer chunk make the shortlist:

```python
return gold_index in shortlist
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, fully deterministic (no randomness, so your numbers will match).

```
==============================================================================
Part 1: a tiny RAG retriever, and how often it finds the answer chunk
==============================================================================
  corpus: 57 short documents, 2346 words total.
  chunk size: 28 words  ->  84 chunks on the shelf.
  test set: 10 questions, each with a known answer sentence.
  retrieval: TF-IDF vectors, cosine similarity, keep the top 3 chunks
             whose score clears the relevance threshold tau = 0.3.

  recall@3 with sensibly sized chunks = 100%
  Read that as: in that share of the questions, the chunk that actually
  holds the answer survived into the top 3 we would hand to the model.
  When it does not, the smartest LLM alive still answers from wrong text.

  A couple of retrievals, so you can see it working:
    q: 'which animal comes out at night to eat grass near th'
       gold ranked #1 at cosine 0.59; top hit "...it comes out at night to eat grass on the land near the wa..."
    q: 'which animal sleeps through the cold winter in a den'
       gold ranked #1 at cosine 0.43; top hit "...whatever food it can find at night the brown bear is a lar..."

==============================================================================
Part 2: break it with chunk size. Too small splits the answer, too
        large dilutes it, and recall peaks in the middle
==============================================================================
  Same corpus, same 10 questions, same top 3 above tau. Only
  the chunk size changes. Watch recall climb then fall: an inverted U.

    chunk size   chunks    recall@3
             3      782         70%  ##############
             6      391         60%  ############
            12      196         90%  ##################
            20      118        100%  ####################
            28       84        100%  ####################
            40       59        100%  ####################
            60       40         90%  ##################
            90       27         60%  ############
           140       17         20%  ####
           200       12         20%  ####

  too small (6 words):  recall@3 = 60%
    The answer sentence is cut across several tiny chunks, so the one
    that holds the most of it carries only a word or two of the query.
    Its similarity is weak and it sinks below the other scraps, or below
    tau, so the retriever never hands it over.
  too large (200 words): recall@3 = 20%
    Now the answer is one sentence buried in a wall of unrelated text. Its
    few matching words are averaged over the whole chunk, the cosine of
    the right chunk drops below tau, and the retriever discards it as
    noise even though the answer is sitting right there inside it.
  best in the sweep: 20 words at 100%. Chunk size is a
  knob you tune, not a default you ignore.

==============================================================================
Part 3: break it with vocabulary. TF-IDF matches words, not meaning
==============================================================================
  Good chunk size (28 words), the same 10 questions, but
  reworded with synonyms the documents never use: 'swift' for 'fast',
  'beast' for 'animal', 'dwells' for 'lives', and so on.

  recall@3, matched wording:  100%
  recall@3, synonym wording:  0%

  Why it falls off a cliff: a query word the corpus never saw is not in
  the vocabulary, so it has no idf weight and contributes nothing to the
  score. Look at how many query words even survive to be matched:

   question    matched hits vocab    synonym hits vocab
          1                   7/7                   2/8
          2                   6/6                   3/7
          3                   6/6                   0/7
          4                   6/6                   1/7
          5                   7/7                   1/7
          6                   8/8                   0/7
          7                   7/7                   0/7
          8                   6/7                   0/7
          9                   6/6                   0/8
         10                   8/8                  2/10

  Same questions, same answers sitting right there in the corpus. Only
  the words changed, and retrieval went blind. This is the exact gap
  semantic embeddings (Day 38) close: they put 'swift' and 'fast' near
  each other in vector space, so meaning matches even when words do not.
  A reranker on top then reorders the shortlist by a deeper read.

==============================================================================
Scoreboard
==============================================================================
  P1 good chunk recall@3             you =  100   actual =    100 %       close enough
  P2 too-large recall@3              you =   20   actual =     20 %       close enough
  P3 too-small recall@3              you =   60   actual =     60 %       close enough
  P4 synonym recall@3                you =    0   actual =      0 %       close enough

==============================================================================
The number to carry
==============================================================================
  At a sensible chunk size, retrieval found the answer chunk 100% of the
  time. Chunk too large and it fell to 20%; too small, 60%. Keep the
  good size but ask with synonyms and it crashed to 0%, because
  TF-IDF matches words, not meaning. Every one of those failures happens
  BEFORE the model sees anything. That is why RAG is a retrieval problem
  wearing a generation costume, and why 'the LLM got it wrong' is usually
  'we handed it the wrong three chunks'.
```

Part 1 is the baseline, and it is deliberately boring: treated with a sensible chunk size, retrieval found the answer chunk in the top 3 every single time. This is the state most demos show you, and it is real. Retrieval works when the pieces are the right size and the words line up.

Part 2 is the knob nobody touches. The same 57 documents, the same 10 questions, the same top 3, and recall traces an arch purely as the chunk size changes: 60 percent when chunks are tiny, a plateau at 100 percent through the middle, and 20 percent when chunks are huge. The two failures have opposite shapes. Too small splits a single answer across several chunks so none of them is similar enough to surface. Too large buries the answer in so much unrelated text that its chunk scores below the relevance threshold and gets thrown away as noise, even though the answer is sitting right inside it. The healthy band in the middle is where a chunk is about one thing and still holds a whole answer.

Part 3 is the wall. Keep the good chunk size, reword the same questions with synonyms the corpus never uses, and recall goes from 100 percent to zero. The answers did not move. TF-IDF simply has no way to match a word it has never seen, because that word carries no weight in the vocabulary. This is the cleanest possible motivation for Day 38's embeddings: you need vectors that encode meaning, so "swift" lands near "fast" even though they share no letters, and a reranker on top to tidy the final order.

The one line to carry out of today: RAG is a retrieval problem wearing a generation costume. When it is wrong, look at the chunks you fed the model before you blame the model.

</details>
