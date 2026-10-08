---
title: "Day 58: capstone writeup"
parent: "Week 8: putting it all together"
nav_order: 9
has_children: true
---

# Day 58
## Capstone writeup, the architecture doc that outlasts the code 📄

Today's one idea: you turn four days of design, building and breaking into one clean architecture document, the kind you would be proud to hand a staff engineer. The design, the decisions and their tradeoffs, the numbers you measured on Day 57, the failure modes, and the cost. The code you wrote will be rewritten or thrown away. The ability to explain a system clearly, in writing, backed by numbers, is the thing that compounds for the rest of your career.

The code was the easy part. Explaining it so someone else trusts it is the real skill.

---

## Before you start ⏪

Your design doc (Day 55), your running slice (Day 56), and your load-test numbers (Day 57) are all in front of you. The writeup stitches them together. Bring Day 43 and 44 (how you would observe and set an SLO for this), Day 48 (the cost), and the failure thinking from week 5 and 7.

---

## Words you will meet today 📖

An architecture decision record (ADR) is a short note capturing one decision: what you chose, what you rejected, and why. A handful of ADRs is worth more than pages of prose, because they tell the reader not just what the system is but why it is not something else.

A failure mode is a specific way the system breaks: "the database primary dies," "the cache goes cold," "one tenant floods the queue." A good doc lists them and says, for each, how you detect it and how the system degrades.

A non-goal is something you deliberately did not do. Stating non-goals is how you stop a reader asking "but why didn't you handle X," because you already told them X was out of scope and why.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read, for how to write it well:
- [Design docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/) by Malte Ubl, again, now with your own system in mind. Notice how much of a good doc is tradeoffs and non-goals, not diagrams.
- [Architecture decision records](https://github.com/joelparkerhenderson/architecture-decision-record) by Joel Parker Henderson. Skim the templates. You will write two or three ADRs for your capstone's hardest decisions.
- [arc42](https://arc42.org/overview), once more, as a checklist of sections. Take the ones that fit, ignore the rest.

No video today. Writing is the work. Put the mocks and talks away and write.

### What a staff engineer looks for 🔍

A staff engineer reading your doc is not checking whether the diagram is pretty. They are checking three things. Do you know why you made each choice, or did you copy a pattern? Can you state what you did not do and why, or did you try to do everything and finish nothing? And are your claims backed by numbers or by hope? That last one is where your Day 57 load test turns an ordinary doc into a credible one. "Writes peak at about 4,200 per second and the bottleneck is the single database writer" is a sentence hope cannot fake. You measured it.

So the doc leads with a one-paragraph summary, states the requirements and the non-goals, describes the design in words and one diagram, records the two or three hard decisions as ADRs (chosen, rejected, why), and then, crucially, reports the measured results from Day 57 with the knee and the bottleneck named. Then the failure modes, each with detection and degradation, and finally the cost, a rough monthly bill with the dominant line item (Day 48). Short is good. A tight four pages beats a vague twenty.

### Write it for the reader who was not there 📝

The test of the doc is whether someone who never saw you build it could read it, understand what the system does, trust that it works at the scale you claim, and know where its edges are. Write for that person. Explain the acronyms. Say the numbers. Admit the weaknesses, because a doc that lists its own failure modes is far more trustworthy than one that pretends there are none. The honesty is the credibility.

---

## Block 2: drill (40 min) ✍️

Paper first, into [`notes/day-58-drills.md`](../notes/day-58-drills.md). Outline before you write.

D1. The summary. Write the one-paragraph summary of your capstone that a stranger could understand. If it takes more than a paragraph, your scope was too big.

D2. Non-goals. List three things your system deliberately does not do, and one line each on why that was the right call.

D3. The ADRs. Name the two or three decisions worth recording. For each, write the alternative you rejected and the reason in one line.

D4. The numbers. Which measurements from Day 57 go in the doc? Write the knee, the peak throughput, and the named bottleneck as you would state them to a skeptic.

D5. Failure modes. List three ways your system breaks, and for each, one line on how you detect it and how it degrades.

---

## Block 3: build (100 min) 🔧

Write the architecture doc. The template is [`labs/day-58-capstone-writeup/ARCHITECTURE.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-58-capstone-writeup/ARCHITECTURE.md). Copy it into your fork and fill every section with the real substance of your capstone. Use your actual Day 57 numbers. Write your real ADRs. List your real failure modes.

Keep it tight. Cut any sentence that is not a claim, a reason, or a number. When you are done, read it once as if you are the staff engineer: is every claim either obvious or backed? Is every "why" answered? Could a stranger trust this system from the doc alone?

### What a finished doc has

A summary a stranger understands. Requirements and explicit non-goals. A design section with one clear diagram in words. Two or three ADRs with rejected alternatives. The measured Day 57 results with the knee and bottleneck named. Failure modes with detection and degradation. A rough cost with the dominant line item. Four to six pages, no padding.

### Deliverable

Your filled-in `ARCHITECTURE.md`. This plus your running slice and your load-test numbers is your capstone. Be proud of it; it is evidence you can design, build, measure and explain a real system.

---

## Block 4: write (30 min) 📣

Your angle is that the writeup is the real deliverable. "I finished my capstone architecture doc. The code took a day; explaining it so a staff engineer would trust it took longer and taught me more. The move that makes a doc credible: every claim is backed by a number I measured, not hope." Share your summary paragraph and your headline number.

Example posts are on the [Day 58 posts](../shares/day-58-posts.md) page.

---

## End of day: log it 📝

Log the three: the hardest section to write honestly, the decision you are proudest of recording, and the weakness your doc now admits out loud.

Two days left. Tomorrow is review and gaps: an honest look across all eight weeks at what is still shaky, and a day of targeted revision. Then day 60, the finish.

---

## Solutions 🔑

Open after your own writeup.

<details markdown="1">
<summary>A worked architecture doc (abridged, the URL shortener slice)</summary>

Summary. A URL shortener service: create a short code for a long URL, redirect on visit, count clicks asynchronously. Built as a single HTTP node with SQLite and an in-memory read cache. This doc covers the create-and-resolve slice and its measured limits.

Requirements. Create a short link, resolve and redirect, expose metrics. Read heavy (links are read far more than written). Durable (a saved link must survive a restart).

Non-goals. No user accounts (out of scope for the slice; auth is orthogonal). No custom aliases (a separate uniqueness-checked write path, not needed to prove the design). No distributed deployment (single node, measured honestly, with sharding named as the real-scale path).

Design. Client to HTTP service. Writes insert a row and cache the mapping. Reads check the in-memory cache first and fall through to SQLite on a miss. Click counting would go via a queue so the redirect never waits (designed, not built in the slice).

ADR 1, short code generation. Chosen: auto-increment id encoded base62. Rejected: hashing the URL (needs collision handling) and a key generation service (more machinery than a single-node slice warrants). Why: simplest thing that is collision-free; the tradeoff is sequential, guessable codes, acceptable for a demo, not for private links.

ADR 2, read cache. Chosen: in-process LRU cache in front of SQLite. Rejected: an external cache like Redis (unnecessary for one node). Why: makes repeated reads bypass the database entirely; the tradeoff is the cache is per-process and lost on restart, which is fine because it is just a read accelerator over a durable store.

Measured results (Day 57, one laptop). Read-heavy peak about 12,700 req/s, knee at 8 concurrent workers. Write-heavy peak about 4,200 req/s, flattening earlier. The bottleneck is the single database writer: every write serialises through one lock, so write throughput is roughly a third of read throughput and does not improve with more concurrency, it only grows the queue and p99 (under 3ms at the knee to nearly 12ms at 32 workers).

Failure modes. Process dies: in-flight requests fail, the durable store is intact, restart recovers all data (cache rebuilds cold). Database locked under write storm: writes queue and p99 climbs; detect via the p99 metric and the writes counter, degrade by shedding or queueing writes. Cache cold after restart: a burst of misses hits the database (a small thundering herd, Day 17); detect via cache hit rate, mitigate by warming popular keys.

Cost (if real). Dominated by read bandwidth and the cache tier, not storage, because the workload is 100-to-1 reads. At real scale the single node is replaced by a sharded store behind a balancer with a distributed cache, and the dominant line item becomes egress, not compute (Day 48).

What is next. Turn on WAL and batch commits to lift the write ceiling; shard by code and add a distributed cache for real scale; build the async click-counting path.

</details>
