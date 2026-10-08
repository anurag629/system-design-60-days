---
title: "Day 50: the framework"
parent: "Week 8: putting it all together"
nav_order: 1
has_children: true
---

# Day 50
## The framework, because a 45-minute design is a performance with a fixed shape 🎭

Today's one idea: a system design interview is not a memory test, it is a performance with a known structure, and once that structure is muscle memory your brain is free to actually think about the problem instead of panicking about what comes next. Same as a cricketer who has grooved the cover drive a thousand times in the nets, so in the match the shot just happens and the head stays still to read the ball.

This is week 8, the finish. No new theory. For the next five days you practise running the conversation, and today you learn the shape with zero pressure.

---

## Before you start ⏪

You already have every piece. The scale estimate is Day 2. The API is Day 5. Load balancing and the stateless service is Day 6. Storage and sharding are week 2. Caching is week 3. Queues are week 4. The failure talk is week 5 and week 7. Today just arranges them into an order you can run in your sleep.

---

## Words you will meet today 📖

Functional requirements are what the system does: the two or three core features. "A user can shorten a URL and anyone can visit the short link." Verbs the user cares about.

Non-functional requirements are how well it does them: scale, latency, consistency, availability, durability. These are the ones that actually shape the design, and the ones beginners skip.

Back of the envelope is a rough calculation done in your head or on paper to size the system: users, requests per second, storage per year. Not precise, just the right order of magnitude (Day 2).

A deep dive is the part of the interview where you pick one hard sub-problem and go deep: the hot key, the fan-out, the consistency choice. This is where you show you are senior and not reciting a blog post.

Driving the interview means you lead: you propose the next step, you state tradeoffs out loud, you manage the clock. The interviewer is a collaborator you are thinking with, not an examiner waiting for the magic word.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these two:
- [Delivery](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery) from Hello Interview. This is the single best free writeup of how to actually spend the 45 minutes. It is the backbone of today.
- [Core concepts](https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts) from Hello Interview, a quick refresher of the vocabulary you will reach for in every design.

Watch:
- [How to Crack Any System Design Interview](https://www.youtube.com/watch?v=o-k7h2G3Gco) by ByteByteGo, about 8 minutes. The shape, fast.
- [Design Reddit, a system design mock interview](https://www.youtube.com/watch?v=KYExYE_9nIY) by Exponent (now Aced), about 41 minutes. Watch a strong candidate run the whole 45 minutes. Do not watch for the answer, watch for the moves: how they clarify, when they estimate, how they narrate the tradeoffs, how they manage the clock.

### The six steps, and the clock 🕐

Here is the shape. Six steps, and the times are a budget, not a law, but if you are wildly over on one, you are stealing from another.

Step 1, requirements, about 5 minutes. Pin down the two or three functional requirements (what it does) and the non-functional ones (scale, latency, consistency, availability). Ask, do not assume. "How many users? Reads or writes heavy? Does it need to be strongly consistent, or is eventual fine?" The non-functional answers are what make the design yours instead of generic.

Step 2, scale estimate, about 5 minutes. Back of the envelope (Day 2). Daily active users, reads per second and writes per second at peak (remember peak is a few times the average), storage per year, bandwidth. You are not after precision, you are after the order of magnitude that tells you whether one database is fine or you need a hundred.

Step 3, API and core entities, about 5 minutes. The handful of endpoints (Day 5) and the main data objects. This is the contract between the client and your system, and writing it down stops you designing in the air.

Step 4, high-level design, about 10 to 15 minutes. Boxes and arrows, the happy path end to end. Client, load balancer, stateless service (Day 6), database, cache, queue. Draw the write path and the read path separately, because they usually want different things.

Step 5, deep dives, about 10 to 15 minutes. Pick the one or two hard parts and go deep, driven by the non-functional requirements from step 1. High write rate, so how do you shard? One celebrity, so how do you handle the hot key? This is the most important step and the one that separates a pass from a strong hire.

Step 6, bottlenecks and failure, about 5 minutes. What breaks, how you see it break (Day 43), how you degrade instead of dying (Day 27). Single points of failure, the p99 tail, the monthly bill. End on honesty, not on a claim that it scales infinitely.

### The part that is not on the whiteboard 🗣️

The structure is half of it. The other half is how you carry yourself. Drive: you say what you are doing next, you do not wait to be prompted. Narrate: every box you draw, say why it is there and what it costs, because an interviewer cannot read your mind and silence reads as "does not know." State tradeoffs out loud, always as a choice: "I will go with eventual consistency here to keep writes fast, and the cost is a reader might see stale data for a second, which for a feed is fine." Manage the clock: if you have spent 15 minutes on requirements you have already lost. And treat the interviewer as a teammate, lean on their hints, because a hint ignored is the fastest way to fail.

---

## Block 2: drill (40 min) ✍️

Paper first. Write your answers into [`notes/day-50-drills.md`](../notes/day-50-drills.md).

D1. Write the six steps from memory, with the time budget next to each. Do it again tomorrow until you never have to think about it.

D2. For each step, write the one sentence that says what its output is. For example, step 3's output is "a short list of endpoints and the two or three main entities."

D3. Take the prompt "design a pastebin" (store a blob of text, get a short link to read it back). Do only steps 1 and 2, requirements and the scale estimate, in 10 minutes. Assume 10 million new pastes a day, each read 10 times on average. What is the write rate, the read rate, and the storage per year?

D4. Name the single most common way candidates fail the time budget, and the rule that prevents it.

D5. The interviewer says "okay but what happens when that database falls over?" Which step is that, and what are the three things a good answer touches?

---

## Block 3: build (100 min) 🔧

Today you build a tool you will use for the rest of the week: your own one-page framework sheet. The starter is [`labs/day-50-framework/FRAMEWORK.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-50-framework/FRAMEWORK.md). Copy it into your fork and make it yours: the six steps, your time budget, and for each step the two or three questions you always ask and the things you always draw.

Then rehearse it once, out loud, against the prompt "design a pastebin," for the full 45 minutes, alone, talking to the wall. It will feel ridiculous. Do it anyway. The first time you run the shape should not be in a real interview, the same way you do not want the first time you fsync for real (Day 2) to be during an outage.

### What a good framework sheet has

Not an essay. A single page you could glance at and instantly know where you are. The six steps, the clock, and your personal defaults: the questions you ask in step 1, the formula you use in step 2, the boxes you reach for in step 4. Yours, in your words, so it is a trigger and not a script.

### Deliverable

Your filled-in `FRAMEWORK.md`, and one honest line: which of the six steps is the one you are most likely to rush or skip under pressure.

---

## Block 4: write (30 min) 📣

Your angle is the reframe: a design interview is not a memory test, it is a performance with a shape, and learning the shape is what lets you think. "I used to freeze in design interviews because I was trying to remember an answer. This week I learned the six-step shape, and suddenly my brain is free to actually reason about the problem."

Example posts are on the [Day 50 posts](../shares/day-50-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the step you are most likely to rush, and one move from the mock video you want to steal.

Tomorrow the real practice starts: mock 1, a URL shortener, end to end and against the clock. You designed one on Day 7, so you are not starting cold. Tomorrow you run the whole thing as a performance.

---

## Solutions 🔑

Open these only after your own drill pass.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. 1, requirements (5 min). 2, scale estimate (5 min). 3, API and core entities (5 min). 4, high-level design (10 to 15 min). 5, deep dives (10 to 15 min). 6, bottlenecks and failure (5 min).

D2. Step 1's output: two or three functional requirements and the non-functional ones (scale, latency, consistency, availability). Step 2's output: the order-of-magnitude numbers, reads per second, writes per second, storage per year. Step 3's output: a short list of endpoints and the two or three main entities. Step 4's output: a boxes-and-arrows diagram of the read path and the write path. Step 5's output: a deep solution to the one or two hard sub-problems. Step 6's output: the failure modes, how they are detected, and how the system degrades.

D3. Writes: 10 million pastes a day is 10,000,000 / 86,400, about 116 writes per second average, and at say 3 times peak about 350 writes per second. Reads: each paste read 10 times means 100 million reads a day, about 1,160 per second average, about 3,500 at peak. Storage: if a paste averages a few kilobytes, say 10 KB to be safe, 10 million a day is about 100 GB a day, about 36 TB a year. The lesson: it is read heavy (10 to 1), writes are small, and storage grows fast, so you will want a blob store and a cache, not one fat database doing everything.

D4. The most common failure is spending too long on requirements and the high-level design and never reaching the deep dives, so the interview ends before you got to show any depth. The rule: timebox hard, and when a step's budget is up, move on even if it is not perfect. You can always come back. Depth in step 5 is where the signal is, so protect its time.

D5. That is step 6, bottlenecks and failure. A good answer touches three things: detection (how do you even know it fell over, which is health checks and alerting on error rate, Day 43 and 44), failover (a replica is promoted, or the service degrades to read-only or serves stale cache, Day 12 and Day 27), and blast radius (is this a single point of failure, and what else goes down with it). Bonus points for naming the data-loss window if the primary died before replicating.

</details>

<details markdown="1">
<summary>A worked step 1 to 3 for "design a pastebin"</summary>

Requirements. Functional: a user can create a paste (a blob of text) and get a short URL back; anyone with the URL can read the paste; pastes can optionally expire. Non-functional: read heavy, highly available for reads, eventual consistency is fine (a paste appearing a second late is nobody's crisis), durable (a saved paste must not vanish).

Scale, from D3: about 350 writes per second and 3,500 reads per second at peak, roughly 36 TB a year of blobs. Read heavy by 10 to 1.

API and entities. Endpoints: POST /pastes with the text, returns an id and short URL; GET /pastes/{id} returns the text. Entities: a Paste (id, text or a pointer to the blob, created_at, expires_at). The text itself goes in a blob store, not the metadata row, because 10 KB blobs do not belong in your index. That one decision, metadata in the database and the blob in object storage, is the whole shape of the system, and you reached it in step 3.

</details>
