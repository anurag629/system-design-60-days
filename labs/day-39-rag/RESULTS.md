---
title: "Day 39 lab results"
parent: "Day 39: RAG, and why it mostly fails at retrieval"
grand_parent: "Week 6: AI systems"
nav_order: 1
---

# Day 39 results: RAG lives or dies on retrieval

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (recall at a good chunk size):
- P2 (recall when chunks are too large):
- P3 (recall when chunks are too small):
- P4 (recall when the query uses synonyms):

## The chunk-size knob, in my own words

What was the recall at a sensible chunk size, and what did it fall to at the too-large and too-small ends? Why does each extreme hurt (dilution below the threshold at the top, split-and-starved fragments at the bottom):

## The vocabulary wall

Same questions, same answers sitting in the corpus, only the words changed. What did recall drop to, and why can TF-IDF not match a word it has never seen:

## The number that matters

At a good chunk size retrieval found the answer ___ of the time. Too large it fell to ___, too small to ___, and with synonyms to ___. Why does every one of those failures happen before the model sees anything:

## Can't explain yet
