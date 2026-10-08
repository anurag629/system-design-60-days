---
title: "Day 38: vector search and embeddings"
parent: "Week 6: AI systems"
nav_order: 3
has_children: true
---

# Day 38
## Finding the needle by meaning, and the one dial that makes it fast 🔎

Today's one idea: a vector search engine does not look for a word, it looks for a meaning, and it cannot afford to look at everything. So it cheats, on purpose. It clusters the data, looks inside only the few clusters nearest your query, and accepts that it will miss a neighbour now and then. That miss is not a bug. It is a dial you turn, recall on one side, speed on the other, and knowing where to set that dial is most of what running a vector database is.

Yesterday you saw the GPU generate tokens and the KV cache make batching pay. Today we step one box to the left in the diagram, to the thing that feeds the model its context: the retriever. And here is the happy surprise. A vector index is just an index, the same idea as the B-tree on Day 10, only the question changed. A B-tree indexes "which rows sort near this key". A vector index indexes "which rows mean near this query". Same job, find the few that matter without scanning the whole table, a new kind of "near".

---

## Before you start ⏪

You need two things from earlier weeks fresh in your head. First, Day 10, what an index is for: it exists so you do not scan the whole table on every query, you jump to the small part that matters. Keep that sentence close, because today is the same sentence with "sort near" swapped for "mean near". Second, the caching weeks (week 3). A cache trades a hit rate for speed, you accept that some lookups miss so that most are fast. A vector index makes the very same bargain, it trades recall for speed, and today you measure the exact shape of that trade. Day 2's comfort with plain Python is all the code you need.

---

## Words you will meet today 📖

An embedding is a list of numbers (a vector) that a model produces for a piece of text, an image, or audio, chosen so that things with similar meaning get vectors pointing in a similar direction. A real embedding has 384 to 3072 numbers in it. Ours in the lab have 32, so the thing runs on your laptop in seconds.

A vector is just that list of numbers, a point in high-dimensional space. "High-dimensional" only means the list is long, 32 or 768 numbers instead of the 2 or 3 you can draw.

Cosine similarity is how we measure "point in a similar direction". It is the angle between two vectors, 1.0 for identical direction, 0 for unrelated, negative for opposite. If you scale every vector to length 1 first (we do), cosine similarity is simply the dot product, the sum of the elementwise products. That is the whole metric.

Nearest neighbour search is the task: given a query vector, find the k stored vectors most similar to it. Top-k, by cosine.

Brute force (or flat) search answers that exactly, by scoring the query against every stored vector. Correct, and linear in the number of vectors, which is the problem.

Approximate nearest neighbour, ANN, is the family of tricks that find most of the true neighbours without scoring everything. Faster, and sometimes wrong, by design.

Recall@k is the score that keeps ANN honest. Of the true top-k neighbours, what fraction did the approximate search actually return? If the real top-10 and your returned 10 share 9, recall@10 is 0.9.

IVF, the inverted file index, is the ANN scheme you build today. Cluster the vectors into cells once, then at query time score only the vectors in the cells nearest the query.

nprobe is the IVF dial. How many cells to open and search per query. Probe 1, fast and lossy. Probe all of them, you are back to brute force.

HNSW, hierarchical navigable small world, is the other common ANN scheme, a graph you walk instead of cells you open. Its dial is called efSearch. You will not build it today, but you should know the name, because pgvector and most vector databases offer both IVF and HNSW.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these:
- [pgvector README](https://github.com/pgvector/pgvector), the least hyped and most honest intro to vector search, and the week's core resource. Read how it stores vectors and especially its two index types, `ivfflat` (with `lists` and `probes`) and `hnsw`. Those `probes` are the exact dial you build today, sitting in a real Postgres extension.
- [Vector indexes](https://www.pinecone.io/learn/series/faiss/vector-indexes/) on Pinecone's learn site. Walks Flat, IVF and HNSW side by side and shows the recall-versus-speed trade with real numbers. This is today's lab in prose.
- [Vector search explained](https://weaviate.io/blog/vector-search-explained) on the Weaviate blog. A gentle on-ramp to ANN and HNSW, with good pictures of why a graph walk finds neighbours fast.
- [The Illustrated Word2vec](https://jalammar.github.io/illustrated-word2vec/) by Jay Alammar, if the word "embedding" still feels like hand-waving. The clearest picture anywhere of how meaning becomes a direction in space.

Watch, after the lab:
- [What is a Vector Database?](https://www.youtube.com/watch?v=gl1r1XV0SLw) by IBM Technology, Martin Keen, about 8 minutes. A tight overview that names embeddings, IVF, HNSW and how this all feeds RAG, which is tomorrow.

### What an embedding actually is (14 min)

Picture a huge library, but a magic one. The rule is that two books end up on nearby shelves whenever they are about similar things, no matter the title or the author. A thriller set in Mumbai and a thriller set in Delhi sit almost touching. A cookbook sits far away in another aisle. Nobody filed them by alphabet or by subject code. They were placed by meaning.

An embedding model is the librarian. You hand it a sentence and it hands back a position, written as a list of numbers. The list is long, 768 numbers for a common model, because meaning has many independent flavours and one or two numbers cannot hold them. That long list is the vector, and the position it describes is a point in 768-dimensional space. You cannot picture 768 dimensions and you do not need to. Everything we do works the same in 768 as it does in 2, it just has more numbers in the sum.

"Similar meaning" becomes a concrete, measurable thing: two vectors that point in nearly the same direction. We measure direction with cosine similarity, the cosine of the angle between them, 1.0 when they point the same way and 0 when they are unrelated. A neat trick makes this cheap. If you first scale every vector to length 1, so they all sit on the surface of a unit sphere, then the cosine is just the dot product, multiply the two lists elementwise and add it up. That is why the core line of today's lab is a one-line dot product. On the unit sphere, the most similar vector is simply the one with the largest dot.

So search by meaning is now a precise question with a boring name: nearest neighbour search. Given the query's point, find the k stored points closest to it on the sphere. The whole rest of the day is about doing that without checking every point, which is exactly the problem Day 10 solved for "sort near" and we now solve again for "mean near".

### Why exact search hits a wall (12 min)

The obvious way to find the nearest neighbours is to score the query against every stored vector and keep the top k. This is brute force, also called flat search, and it has one wonderful property and one fatal one. Wonderful: it is exact. It looked at everything, so it cannot miss, recall is 100 percent by definition. Fatal: its cost is linear in the number of vectors, every query, forever.

Put real numbers on it, because the numbers are the reason the whole industry exists. Say you have 10 million vectors of dimension 768. One similarity is about 768 multiply-adds. One query against all 10 million is about 7.7 billion multiply-adds. Even on hardware that chews through a billion of those a second, that is several seconds for a single query, and you have not even batched other users yet. Double the corpus and you double every query's cost. This does not scale, in the plainest sense of the word: the work per request grows with the size of the data.

And remember Day 4, tail latency. Tomorrow's RAG query does not make one vector search, it may make several, and an agent (Day 40) makes many. When one user request fans out into twenty retrievals, a slow retriever does not add, it multiplies, and the p99 you fought so hard for in week 1 falls apart. So we cannot afford exact search at scale, for the same reason we could not afford a full table scan on Day 10. We need an index, a structure built once so that each query touches a small slice of the data instead of all of it.

### ANN: trade a little recall for a lot of speed (14 min)

Here is the move that makes vector databases possible, and it is a genuinely different bargain from anything in weeks 1 to 5. We give up on being exact. We build an index that finds most of the true neighbours most of the time, and in exchange it goes many times faster. The family of such indexes is called approximate nearest neighbour search, ANN.

There are two main shapes, and you should know both names.

The one you build today is IVF, the inverted file index, and it is pure Day 13 thinking. Cluster all the vectors into cells once, up front, with k-means, each cell owning a patch of the space with a centroid at its middle. That is the build. Then a search is cheap: find the cell whose centroid is nearest the query, and score only the vectors in that one cell. If you split 5,000 vectors into 40 cells, one cell holds about 125 vectors, so you compare 125 instead of 5,000, plus a quick scan of the 40 centroids to pick the cell. Tens of times less work.

The other shape is HNSW, a navigable small-world graph. Instead of cells, every vector is a node wired to a few of its nearest neighbours, with a few long-range links on upper layers acting as express lanes. A search drops in at the top, greedily hops toward the query, and descends layer by layer. It is usually the fastest at high recall and it is what most managed vector databases reach for. You are not building it today, but when you read "hnsw" in the pgvector README, that is this.

Both need a way to keep score, and that score is recall@k. Of the query's true top-k neighbours (the ones brute force would have found), what fraction did the index actually return? Returned 9 of the true 10, recall@10 is 0.9. This is the number that tells you how much the approximation cost you, and it is the number you will watch move in the lab.

### The recall-versus-speed dial is the whole product (10 min)

Now the punchline, and it is the reason today exists. Both IVF and HNSW come with a knob. In IVF it is nprobe, how many cells you open instead of just the nearest one. Open one cell and you are fast but you miss any true neighbour that happened to land in the cell next door, right across a boundary. Open more cells and you catch those stragglers, recall climbs toward 100 percent, and your latency climbs too, because you are scoring more vectors. Open all the cells and you are doing brute force again, with a centroid scan bolted on for your trouble. In HNSW the knob is efSearch, and it behaves the same way: bigger means higher recall and higher latency.

That single knob is the entire personality of a vector database. There is no setting that is simply correct. There is only the point on the curve you chose: "90 percent recall at a tenth of the cost" for a product that can tolerate the odd missed result, or "99.9 percent recall, pay for it" for one that cannot. This is the same shape as a cache hit rate from week 3. You tolerate imperfect answers because most answers come back fast, and you tune the ratio to the product. When someone says vector search "is approximate" as if confessing a flaw, they have it backwards. Approximate is the feature. It is the dial that lets the thing run at all.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-38-drills.md`](../notes/day-38-drills.md).

D1. You have 10,000,000 vectors of dimension 768, and one cosine similarity is about 768 multiply-adds. Roughly how many multiply-adds does one brute-force query cost? If a core manages about 1 billion of those per second, how long is one query, and why does this force an index as the corpus grows?

D2. An IVF index splits N vectors into C roughly equal cells and probes nprobe of them. About how many vectors does one query score (ignore the centroid scan), and what is the rough speedup over brute force? Plug in N = 1,000,000, C = 1,000, nprobe = 10.

D3. For one query the true top-10 neighbours are a known set. Your ANN returns 10 ids, and 8 of them are in that true set. What is recall@10? If the product needs recall@10 of at least 0.95, is this good enough, and name the one knob you would turn first.

D4. In IVF with nprobe = 1, explain in one or two sentences why a genuinely nearest neighbour can be missed even though the index is working correctly. Which queries are most at risk of this, and how exactly does raising nprobe fix it, and what does the fix cost?

D5. A common embedding has 1,536 numbers, each a 4-byte float. How many bytes is one vector? For 10,000,000 vectors, how much memory just to hold the raw vectors, no index overhead? Given week 6 is all about the memory wall, name one thing a vector database does to shrink that number.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-38-vector-search/vector_search.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-38-vector-search/vector_search.py).

It is in three parts. Part 1 does exact brute-force search over 5,000 vectors and measures its latency and its (perfect) recall. Part 2 builds an IVF index, clusters the vectors into 40 cells with a tiny k-means, probes the single nearest cell, and measures recall and speed against Part 1's ground truth. Part 3 turns the nprobe dial from 1 up to all 40 cells and prints recall and latency at every step, so you watch the trade with your own eyes.

Standard library only, no numpy, no model, no API, no network. The vectors are made up but they have real cluster structure, so the neighbours mean something. It is deterministic (seeded) and runs in about 7 seconds, cleaning up nothing because it writes nothing.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. Brute-force search scores the query against every vector and keeps the real top k. What is its recall@k, as a percent?
- P2. The IVF index probing just one cell. What fraction of each query's true top-k does it find, as a percent?
- P3. That same one-cell IVF search, how many times faster than brute force?
- P4. Turn the dial up. Probing 8 cells instead of 1, what is recall@k now, as a percent?

P2 is the one to feel in your gut. Write a number. It is high, but it is not 100, and the gap between your guess and 100 is the whole lesson.

### Fill in the TODOs

1. TODO 1 is `similarity`, the metric everything rests on, the one-line dot product that is cosine on the unit sphere.
2. TODO 2 is `recall_at_k`, the overlap between what you found and the truth, divided by how many true neighbours there were. This is how you keep the approximation honest.
3. TODO 3 is `nearest_centroid`, which cell a vector belongs to, the argmax over centroids. This is the IVF build, and the first step of every IVF search.
4. TODO 4 is `cells_to_probe`, the dial itself, rank the cells by closeness to the query and take the nearest nprobe of them.

```bash
cd labs/day-38-vector-search
python3 vector_search.py
```

### What you're going to discover

Part 1 is the baseline and the wall. Exact search got 100 percent recall, because it looked at all 5,000 vectors, and that is exactly why it is slow, about 6 ms per query on the reference machine for a tiny 5,000-vector toy. Picture that number at 10 million.

Part 2 is the trick working. Probing one cell scored about 163 vectors instead of 5,000 and came back roughly 25 times faster, and it still found about 87 percent of the true neighbours. You gave up 13 percent of recall and bought a 25x speedup. On the reference run that is the headline trade, and it is a good trade for a lot of products.

Part 3 is the dial, and it is the thing to stare at. As nprobe climbs, recall climbs toward 100 and latency climbs right back toward brute force. On the reference machine recall went 87, 99, 100 by the time you probed three cells, while the per-query time went from a quarter of a millisecond up and up until, at nprobe equal to all 40 cells, you were simply doing brute force again. The sharp lesson hiding in the flat part of the table: once recall has maxed out, probing more buys you nothing but latency. Over-probing is a real and common misconfiguration.

### Traps ⚠️

- Recall here saturates fast, around three cells, because the toy data clusters very cleanly. Real embeddings are messier and the climb is more gradual, so do not read "three cells is always enough" into it. Read the shape: recall rises and plateaus, latency rises without stopping.
- The k-means build takes a second or two and is a one-time cost, paid once up front, not per query. That is the deal with every index, including the B-tree, you pay at build time to save at query time. Do not fold it into the per-query latency.
- Cell sizes come out lumpy, maybe 28 vectors in one and 225 in another. That is k-means on clustered data, not a bug, and it is why real systems care about how evenly an index balances its cells.
- The speedup is a ratio of two timings on the same machine, so the exact number wobbles run to run. Trust the shape, roughly 25x at one cell falling toward 1x at full probe, not the third digit.

### Deliverable

[`labs/day-38-vector-search/RESULTS.md`](../labs/day-38-vector-search/RESULTS.md) has a skeleton. Paste the output, and write one line: at one cell the IVF search hit what recall and what speedup, and what happened to both as you turned nprobe up?

---

## Block 4: write (30 min) 📣

Your angle today is the dial. "I built a tiny vector search engine. Exact search was 100 percent correct and slow. My approximate index found 87 percent of the right answers 25 times faster, and a single knob let me buy that recall back whenever I wanted it. That knob is the whole product." The nprobe table, recall climbing while latency climbs, is the screenshot.

Example posts are on the [Day 38 posts](../shares/day-38-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the recall and speedup you measured at nprobe = 1, and one thing you still cannot explain.

Day 39 is RAG, and today was the engine room of it. Retrieval-augmented generation is cache-aside with a vector search in the middle, you fetch the few most relevant chunks and stuff them into the prompt. Everything you learned today about recall becomes tomorrow's most common failure mode: if the retriever misses, the model answers confidently from nothing. Today you learned to find things by meaning, and to choose how hard to look. Tomorrow you wire that into a real answer.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. One query is about 10,000,000 times 768, roughly 7.7 billion multiply-adds. At a billion per second that is about 7.7 seconds for a single query, on one core, unoptimised. Real systems do far better with SIMD and tuned math libraries, but the shape does not change: the work is linear in the number of vectors, so every time the corpus grows the per-query cost grows with it. That is precisely the full-table-scan problem from Day 10, and it is why you build an index instead of scanning everything on every request.

D2. A query scores about nprobe times (N / C) vectors, because it opens nprobe cells of average size N / C. With N = 1,000,000, C = 1,000, nprobe = 10, that is 10 times 1,000, so about 10,000 vectors scored instead of 1,000,000. The rough speedup is C / nprobe, here 1,000 / 10 = 100x (a little less once you count the 1,000-centroid scan to pick the cells). The two knobs pull against each other: more cells (bigger C) means smaller cells and more speedup but a bigger centroid scan, more probes (bigger nprobe) means higher recall and less speedup.

D3. Recall@10 is 8 / 10 = 0.8, so 80 percent. That is below the 0.95 target, not good enough. The first knob to turn is nprobe (in IVF) or efSearch (in HNSW): probe more cells or widen the graph search so more of the true neighbours get scored. You will pay for it in latency, which is the trade the whole day is about.

D4. With nprobe = 1 you only ever open the single cell whose centroid is nearest the query, but a query sitting near the boundary between two cells can easily have some of its true nearest neighbours living just across that boundary, in the cell you did not open. So you miss them, even though the index did exactly what it was told. The queries most at risk are the ones near cell boundaries (in k-means terms, near a Voronoi edge). Raising nprobe opens the next-nearest cells too, so those across-the-border neighbours get scored and recall rises. The cost is latency, because every extra cell is more vectors to score.

D5. One vector is 1,536 times 4 bytes, so 6,144 bytes, about 6 KB. Ten million of them is about 61,440,000,000 bytes, roughly 61 GB, just for the raw vectors, before any index structure. That is a lot of expensive RAM (week 6 is the memory wall again), which is why vector databases lean on quantization, storing each number in 1 byte (int8) or even packing many dimensions into a few bits with product quantization, trading a little accuracy for a big cut in memory. It is the same recall-versus-resources bargain, pointed at RAM instead of time.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-38-vector-search/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-38-vector-search/solution.py).

TODO 1, the metric, a one-line dot product (cosine on the unit sphere):

```python
return sum(x * y for x, y in zip(a, b))
```

TODO 2, recall@k, the overlap with the truth over the size of the truth:

```python
return len(set(found_ids) & set(true_ids)) / len(true_ids)
```

TODO 3, the IVF build, the index of the most similar centroid:

```python
return max(range(len(centroids)), key=lambda j: similarity(vec, centroids[j]))
```

TODO 4, the dial, the nprobe cells whose centroids are closest to the query:

```python
order = sorted(range(len(centroids)),
               key=lambda j: similarity(query, centroids[j]), reverse=True)
return order[:nprobe]
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 5,000 vectors of dimension 32, 200 queries.

```
==============================================================================
Part 1: brute force. Exact, 100 percent recall, and linear in N
==============================================================================
  5,000 vectors, dimension 32, retrieving top 10 for 200 queries.
  every query is scored against all 5,000 vectors.
    latency: 6.30 ms/query   (1260 ms for all 200)
    vectors scored per query: 5,000
    recall@10: 100.0%   (it looked at everything, so it cannot miss)

  This is the ground truth every other search is measured against.
  It is also the wall: double the vectors and you double the work,
  every single query. That linear cost is why we reach for an index.

==============================================================================
Part 2: IVF. Cluster once, then search only the query's own cell
==============================================================================
  built 40 cells with k-means in 1540 ms (one-time, up front).
    cell sizes: 28 to 225 vectors (ideal would be 125).

  search probing nprobe=1 cell:
    latency: 0.255 ms/query   (24.7x faster than brute force)
    vectors scored per query: ~163 (vs 5,000 for brute, plus 40 centroids)
    recall@10: 86.6%

  Much faster, because it scores about 163 vectors instead of all
  5,000. The cost is the 13 percent it missed: a true neighbour that
  landed in a neighbouring cell is simply never seen. That miss is not
  a bug. It is the trade you chose by probing one cell.

==============================================================================
Part 3: the dial. Probe more cells, buy back recall, pay in latency
==============================================================================
  Same index, same queries. The only knob we turn is nprobe, the
  number of cells the search looks inside (out of 40).

   nprobe  scored/query   recall@10   ms/query   vs brute
        1          163       86.6%     0.257     24.5x
        2          275       99.3%     0.395     16.0x
        3          405       99.9%     0.559     11.3x
        5          664      100.0%     0.854      7.4x
        8         1035      100.0%     1.364      4.6x
       12         1534      100.0%     1.968      3.2x
       16         2041      100.0%     2.569      2.5x
       25         3163      100.0%     4.155      1.5x
       40         5000      100.0%     6.521      1.0x  <- brute force, basically

  Recall climbs toward 100 percent as you probe more cells, and the
  latency climbs right back toward brute force. Here the recall maxes
  out after only a few cells, because the data clusters cleanly. What
  keeps rising is the latency: probe more than you need and you pay
  brute-force prices for recall you already had. At nprobe = C you ARE
  brute force again, just with the centroid scan bolted on top. A vector
  database hands you this dial and lets you pick where to sit on it.

==============================================================================
Scoreboard
==============================================================================
  P1 brute-force recall              you =  100.0   actual =   100.0 %       close enough
  P2 IVF nprobe=1 recall             you =   88.0   actual =    86.6 %       close enough
  P3 IVF nprobe=1 speedup            you =   25.0   actual =    24.7 x       close enough
  P4 IVF nprobe=8 recall             you =  100.0   actual =   100.0 %       close enough

==============================================================================
The number to carry
==============================================================================
  Brute force was exact, 100% recall, by scoring all 5,000 vectors on
  every query. The IVF index probing one cell hit 87% recall at
  25x the speed, because it scored a small slice of the vectors
  instead of all of them. Turn the dial to nprobe=8 and recall came back
  to 100%. That knob, recall versus latency, is the whole game of a
  vector database. 'Approximate' is not a compromise you tolerate, it
  is the setting you get to choose.
```

Part 1 is the baseline and the wall in one. Exact search scored all 5,000 vectors on every query, so its recall is 100 percent and it cannot be anything else. The price of that certainty is the 6.3 ms per query, on a tiny toy, and that price grows linearly with the corpus. This is the full-table-scan problem from Day 10 in a new costume.

Part 2 is the bargain. Clustering into 40 cells cost a one-time 1.5 seconds, and after that a search that opened only the single nearest cell scored about 163 vectors instead of 5,000, came back about 25 times faster, and still recovered 86.6 percent of the true neighbours. The 13 percent it missed are neighbours that happened to sit in a cell the search did not open. That is the cost you agreed to by probing one cell.

Part 3 is the dial, and the whole point of the day. As nprobe rose from 1 to 40, recall climbed to 100 percent fast (by three cells here, because the toy data is cleanly clustered) while latency climbed the whole way back up to the brute-force number. The flat tail is its own warning: from nprobe 5 onward recall was already pinned at 100, so every extra cell was pure wasted latency. At nprobe = 40 you are simply doing brute force with an extra centroid scan. There is no single right setting. There is only the point on this curve your product can live with.

The one line to carry out of today: exact search is 100 percent recall and linear cost, an approximate index trades a slice of recall for a large multiple of speed, and the dial between them (nprobe for IVF, efSearch for HNSW) is not a flaw to apologise for, it is the control surface of every vector database you will ever run.

</details>

