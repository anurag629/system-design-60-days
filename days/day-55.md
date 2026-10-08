---
title: "Day 55: capstone kickoff"
parent: "Week 8: putting it all together"
nav_order: 6
has_children: true
---

# Day 55
## Capstone kickoff, where you design before you write a line of code 🏗️

Today's one idea: the capstone is the whole course in one project. You pick one system you genuinely care about, and over four days you design it, build one real slice, break that slice under load, and write it up. Today is design, on paper, before any code, because the thing that separates engineers who ship from engineers who flail is that the first group writes down what they are building and why before they build it.

No mocks today. This is your own thing now.

---

## Before you start ⏪

Everything. This is the point where the whole course is on the table. The scale estimate (Day 2), the API (Day 5), storage and sharding (week 2), caching (week 3), queues (week 4), the failure thinking (week 5 and 7). Pick a system where you will actually use some of this, not a toy that needs none of it.

---

## Words you will meet today 📖

A design document (or architecture doc) is a short written description of what you are building, why, and the tradeoffs you chose, written before the code so that you (and anyone reviewing) can argue about the decisions while they are still cheap to change. Day 58 polishes it; today you draft it.

A vertical slice is one feature built all the way through every layer, end to end, rather than one whole layer (all the database, then all the API). You build a thin slice that actually works instead of a broad foundation that does nothing yet.

Scope is what you are and are not building. The single most useful thing a design doc does is say "not this, not now," so you build one real thing instead of ten half things.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these two. This is a writing day, so the reading is about how to write a design, not a new system topic:
- [Design docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/) by Malte Ubl. The best short piece on why you write the document before the code, and what goes in it. Read the whole thing.
- [arc42 overview](https://arc42.org/overview). A clean, reusable template for an architecture document. You do not need all of it; skim it for the sections that fit your capstone.

There is no video today on purpose. A writing day is for writing, not watching. If you want one thing in your ears while you think, re-listen to any mock from this week and notice how the strong candidate's spoken design is basically a design doc said out loud.

### Pick something you care about, and small enough to build 🎯

The capstone fails in one of two ways: you pick something so big you never finish, or so trivial it teaches you nothing. The sweet spot is a system with one genuinely interesting slice you can build in a day with the standard library, and then load test. Here is a menu, all buildable as a small HTTP service:

A URL shortener with click analytics (the write path, the cache, async counting). A rate-limiter service (the distributed-counter decision made real). A simple job queue with workers and retries (week 4 in miniature). A key-value store with a write-ahead log and a read cache (week 2 and 3). A small feed service with fan-out (week 3). A document-search service with keyword retrieval (a RAG retrieval slice without the model). A metrics ingestion endpoint that aggregates counters (week 7). Pick one, or bring your own, as long as it has a slice worth measuring.

The rule: choose the slice where a number will surprise you. The whole course has been about predicting a number and measuring the gap. Your capstone slice should be one where you can predict throughput or latency, build it, load test it on Day 57, and find out you were wrong in an interesting way.

### Write the design before the code 📝

Today you produce a design document, not code. It is short: requirements and scope, a scale estimate, the API, a high-level diagram in words, the one slice you will build, and the two or three decisions you are making with their tradeoffs. Writing it first does three things. It forces you to decide scope ("I am building the write path and the cache, not auth, not a UI"). It surfaces the hard decisions while they are still just words. And it gives you something to check reality against on Day 57, when the load test tells you whether your design held.

The discipline here is the real lesson of the capstone. Anyone can start typing. Writing down what you will build, and what you will not, before you build it, is the habit that makes the difference at work, long after any interview.

---

## Block 2: drill (40 min) ✍️

Paper first, into [`notes/day-55-drills.md`](../notes/day-55-drills.md).

D1. Pick your system. Write one sentence on what it does and one on why you care about it. If you cannot say why you care, pick a different one.

D2. Scope. Write three things you ARE building and three you are explicitly NOT building (not now). Be ruthless; the not-list is more important than the list.

D3. The interesting slice. Which one feature will you build end to end, and what number about it do you predict (throughput, or p99 latency, or cache hit rate)? Write the prediction down now, so Day 57 can prove you wrong.

D4. Scale. Rough back-of-envelope for your system at a plausible real scale: reads/s, writes/s, storage. Does any number change your design?

D5. The two hard decisions. Name the two decisions in your design that have real tradeoffs (not "which language"), and state the tradeoff for each.

---

## Block 3: build (100 min) 🔧

Write the design doc. The starter is [`labs/day-55-capstone-kickoff/REQUIREMENTS.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-55-capstone-kickoff/REQUIREMENTS.md). Copy it into your fork and fill it in properly. This is the document you will build against for the next three days, so make it real: not a wishlist, a plan.

Resist the urge to open an editor and start coding. You will build tomorrow. Today's output is words, because a slice built from a clear design in one focused day beats a mess coded from a vague idea over three.

### What a strong design doc has

A one-paragraph summary a stranger could understand. A scope section with a real not-list. A scale estimate with numbers. A clear statement of the one slice you will build and the number you predict for it. And two or three decisions written as choices with tradeoffs, so on Day 58 you can say whether they held.

### Deliverable

Your filled-in `REQUIREMENTS.md`, and the one predicted number you are most curious to test on Day 57.

---

## Block 4: write (30 min) 📣

Your angle is the discipline. "I am starting my capstone, and the first day has no code. I am writing the design first, on purpose, because writing down what I will build and what I will not is the habit that actually ships things." Share your system and the one slice you are going to break under load.

Example posts are on the [Day 55 posts](../shares/day-55-posts.md) page.

---

## End of day: log it 📝

Log the three: the system you chose, the one slice you will build, and the number you predicted for it.

Tomorrow you build the slice. One real feature, all the way through, measurable. There is a working reference service in the lab folder so you are never staring at a blank file.

---

## Solutions 🔑

Open after your own design pass.

<details markdown="1">
<summary>A worked design doc (URL shortener with analytics)</summary>

This is one filled-in example so you can see the shape. Yours should be your system.

Summary. A URL shortener service: POST a long URL, get a short code; GET the short code, redirect to the long URL; count clicks asynchronously. The interesting slice is the write-and-redirect path with a read cache and async click counting.

Scope. Building: create a short link, resolve and redirect, an in-memory read cache, a metrics endpoint. Not building (not now): user accounts, custom aliases, a UI, link expiry, distributed deployment. One box, one database, one cache.

The interesting slice. The create-and-resolve path. Prediction: with a read cache in front, reads will be limited by the HTTP server, not the database, and will hit several thousand per second on my laptop, while writes will be a few times slower because they serialise through the single database writer. I predict reads at roughly 10,000/s and writes at roughly 3,000/s, and I predict the write path is the bottleneck.

Scale (if this were real). 100 million new links a day (about 3,500 writes/s peak), read 100x (about 350,000 reads/s peak), tens of TB over years. At real scale I would shard the store and put a distributed cache in front, but the slice I build is one node, measured honestly.

Two hard decisions. One, short code generation: an auto-increment id encoded base62, chosen for simplicity in the slice, with the tradeoff that codes are sequential and guessable (fine for a demo, not for private links). Two, click counting: asynchronous via a queue, chosen so the redirect never waits, with the tradeoff of eventual-consistency on the count (a click may take a moment to show). 

The number I most want to test: the write-path throughput, because I suspect the single database writer is a harder ceiling than I expect.

</details>
