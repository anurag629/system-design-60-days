---
title: "Day 38 posts"
parent: "Day 38: vector search and embeddings"
grand_parent: "Week 6: AI systems"
nav_order: 3
---

# Day 38 posts: LinkedIn and X

The nprobe table makes the screenshot: recall climbing toward 100 percent in one column while latency climbs right beside it. Swap in your own numbers and voice.

## LinkedIn

Day 38 of 60 days of system design. Today I built a tiny vector search engine in pure Python and finally understood why everyone says vector search "is approximate", and why that is a feature and not an apology.

A vector search finds things by meaning. You turn text into a list of numbers (an embedding), and two things that mean something similar get lists that point in a similar direction. Search becomes: find the stored vectors closest to the query.

The honest way to do that is brute force. Score the query against every vector, keep the top 10. I did it over 5,000 vectors:

    recall: 100%  (it looked at everything, it cannot miss)
    cost:   it scored all 5,000 vectors, every query

Exact, and linear. Now imagine 10 million vectors instead of 5,000. Every query scores all of them. That wall is why vector databases exist.

So I built an approximate index (IVF): cluster the vectors into 40 cells once, then at query time only search the cell nearest the query.

    probe 1 cell:  86.6% recall, about 25x faster

I gave up 13 percent of the right answers and bought a 25x speedup, because I scored ~163 vectors instead of 5,000. A true neighbour that happened to land in the next cell over just gets missed.

Then the part that made it click. I turned the one knob, nprobe, the number of cells to search:

    1 cell:   86.6% recall
    2 cells:  99.3% recall
    3 cells:  99.9% recall
    all 40:   100%   (back to brute force)

Recall climbs toward 100 as you probe more, and latency climbs right back up with it. There is no "correct" setting. There is only the point on that curve your product can afford. 90 percent recall for a tenth of the cost, or near-exact for more.

That dial is the whole personality of a vector database. Postgres with pgvector hands it to you as `probes`. "Approximate" is not a compromise you tolerate, it is the setting you get to choose.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #ai #vectorsearch #learninginpublic

## X thread

**1/**

Built a tiny vector search engine in pure Python today and finally get why vector search "is approximate", and why that is a feature.

Day 38 of 60 days of system design.

**2/**

Search by meaning: turn text into a list of numbers (an embedding). Similar meaning, similar direction. Finding matches = finding the nearest vectors to your query.

**3/**

The exact way is brute force: score the query against every vector, keep the top 10.

5,000 vectors:
recall 100% (cannot miss, it saw everything)
cost: scored all 5,000, every query

Exact, and linear. Now picture 10 million.

**4/**

So you build an approximate index. IVF: cluster the vectors into 40 cells once, then only search the cell nearest the query.

probe 1 cell: 86.6% recall, ~25x faster

Scored ~163 vectors instead of 5,000. Missed the neighbours that fell in the next cell.

**5/**

Then the dial. nprobe = how many cells to search:

1 cell:  86.6%
2 cells: 99.3%
3 cells: 99.9%
all 40:  100% (= brute force again)

Recall climbs toward 100, latency climbs right back up with it.

**6/**

There is no correct setting. Only the point on the curve your product can afford: 90% recall cheap, or near-exact for more.

pgvector exposes this exact knob as `probes`.

"Approximate" is not a flaw you tolerate. It is the dial you get to turn.

Code: github.com/anurag629/system-design-60-days
