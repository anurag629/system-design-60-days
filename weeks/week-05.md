# Week 5: distributed systems, the real deal 🌍

Days 29 to 35.

This is the hard week. I am telling you now so you do not panic on Wednesday when your brain hurts. Everybody's brain hurts this week. If it did not, the week would be lying to you.

Here is why it is hard. Everything you learned so far assumed one computer that mostly works. This week we admit the truth: real systems run on many computers connected by an unreliable network, the machines fail at random, the clocks disagree, and messages arrive late, twice, or never. And somehow, on top of that mess, we still have to promise users that their money is not lost and their message got through. The tools we build to keep that promise are some of the most beautiful ideas in computing.

You will read actual research papers this week. Do not be scared of the word "paper". The ones I picked are famous precisely because they are readable. Dynamo, Bigtable, Spanner and Raft are written by working engineers for working engineers, not for mathematicians.

## What you will be able to do by Sunday

You can state CAP correctly, which most people cannot, and explain why it is a choice you make per-operation and not a label you stick on a database. You can explain how a quorum works with R plus W greater than N. You can describe, in your own words, how Raft picks a leader and keeps everyone's log in agreement. You understand why Google built atomic clocks into their data centres, and why that is both brilliant and slightly insane.

## The days 🗓️

Day 29: failure and time. The eight fallacies of distributed computing, partial failure, and why "just check if the other server is alive" is a genuinely hard question. Lab: simulate clock skew between two nodes and watch it cause a bug.

Day 30: CAP for real, and its grown-up cousin PACELC. The famous "pick two" is a cartoon. The truth is more interesting and more useful. Reading-heavy day. Lab: partition a toy two-node store and feel the tradeoff.

Day 31: replication and quorums, Dynamo style. How Amazon's cart stayed available through failures by letting copies disagree and healing later. R plus W greater than N, read repair, and eventual consistency. Lab: a quorum read and write simulator.

Day 32: consensus and Raft. How a group of machines agrees on a single value even when some of them crash. Leader election and log replication, step by step. Lab: walk through the Raft states, using the visualisation, and reason about a split vote.

Day 33: logical clocks. Since real clocks lie, we invent logical ones. Lamport timestamps and vector clocks, and how they capture "this happened before that" without trusting any wall clock. Lab: implement vector clocks and detect two events that were truly concurrent.

Day 34: paper day. Read Dynamo, skim Bigtable and Spanner, and write a one-page summary of each in plain language. This is the day the whole week clicks into place.

Day 35: distributed design. You design a distributed key-value store, or the sync engine behind something like Google Docs, timed, then a retro.

## Core resources for the week 📚

Read the papers, in this order:
- [Raft: in search of an understandable consensus algorithm](https://raft.github.io/raft.pdf). Written to be read.
- [Amazon Dynamo](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf), 2007. The clearest statement of the availability tradeoff.
- [Google Bigtable](https://research.google/pubs/pub27898/), 2006, and [Spanner](https://research.google/pubs/pub39966/), 2012. Read Spanner last, it reframes everything.

Watch, when a paper does not click:
- [Martin Kleppmann's distributed systems lectures](https://www.youtube.com/playlist?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdiB), the best free lectures in the field.
- [The Secret Lives of Data: Raft](https://thesecretlivesofdata.com/raft/), Raft as an animation. Do this before the Raft paper.

## What trips people up this week ⚠️

Two things. First, they treat "eventually consistent" as a bug or a cop-out. It is often the correct, deliberate choice, and half the internet runs on it happily. Second, they try to sprinkle Raft and consensus onto problems that do not need agreement at all. Consensus is expensive. Most of your system should avoid needing it. The skill is knowing the small core that genuinely requires everyone to agree, and keeping it as small as possible. When it is not landing, slow down and message me. We re-approach, we do not push through.
