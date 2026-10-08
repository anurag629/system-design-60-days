---
title: "Day 59: review and gaps"
parent: "Week 8: putting it all together"
nav_order: 10
has_children: true
---

# Day 59
## Review and gaps, spend the day on what is still shaky 🔍

Today's one idea: after 58 days you know exactly where your weak spots are, so today you spend your time there and nowhere else. No new material. You rate yourself honestly across all eight weeks, find the three topics that are still shaky, and drill those. Revising what you already know feels nice and teaches nothing. Revising what you cannot quite explain is the whole game.

The most valuable line in your daily log has been "one thing I can't explain yet." Today you collect those and close them.

---

## Before you start ⏪

Your daily logs, if you kept them, especially the "can't explain yet" lines. Your `RESULTS.md` files from the labs. Your fork. Everything you have made is revision material, and it is better than any book because the numbers in it are yours.

---

## Words you will meet today 📖

Spaced repetition is revisiting something just as you are about to forget it, which is when revising it sticks hardest. Your "can't explain yet" notes from weeks ago are perfect spaced-repetition targets: enough time has passed that closing them now locks them in.

A gap is a topic you cannot explain cleanly out loud to an imaginary beginner. Recognising what you cannot explain, as opposed to what you vaguely recognise, is the honesty this day runs on.

Active recall is testing yourself (answer the question from memory) rather than rereading (letting your eyes slide over familiar words and feeling falsely confident). Rereading feels productive and mostly is not; recall is where learning happens.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Today the reading is your own work and a question bank:
- Your own `RESULTS.md` files and daily logs. Reread the numbers you measured. This is the single best revision resource you have, because you produced it.
- [System design problem breakdowns](https://www.hellointerview.com/learn/system-design/problem-breakdowns/overview) from Hello Interview, used as a self-test. Pick three problems you have not drilled, and for each, try to run the six-step shape in your head in two minutes. Where you stall is a gap.

No video today. Today is active recall, not passive watching.

### Test yourself, do not reread 🧠

The trap of a revision day is rereading. You open a day page, the words look familiar, you nod, you feel ready, and you have learned nothing, because recognising is not knowing. So do the opposite: close the page and try to explain the thing out loud, to an imaginary beginner, from memory. Explain what a B-tree is and why it hates random writes. Explain why p99 matters more than the average. Explain fan-out on write versus read. Where your explanation stumbles, where you reach for a word and it is not there, that is a real gap, and that is where today's time goes.

This is why the Write block has been in every single day. Explaining a thing to strangers is the fastest way to find the hole, and you have been doing it for 58 days. Today you do it one more time, deliberately, on your weakest topics.

### The eight weeks, as a recall test 📚

Use the one-line-per-week map in the Solutions as an answer key, not a study sheet. First, from memory, write the single most important idea from each of the eight weeks. Then check against the map. The weeks where you blanked or waffled are your three topics for today. Be honest, because the imaginary beginner you are explaining to does not accept hand-waving, and neither does an interviewer.

---

## Block 2: drill (40 min) ✍️

Paper first, into [`notes/day-59-drills.md`](../notes/day-59-drills.md). This is the self-assessment that drives the whole day.

D1. The map, from memory. Write the single most important idea from each of the eight weeks, before looking at the answer key. One line each.

D2. The honest grid. Rate yourself 1 to 5 on each week (1, could not explain it; 5, could teach it). Be harsh. A 3 is "I sort of get it," which means it is a gap.

D3. The three. From the grid, pick your three lowest. These are today's targets. Write them down.

D4. The specific question. For each of the three, write the exact question you cannot answer cleanly. Not "caching," but "why does a cache stampede happen and what are the two fixes."

D5. The plan. For each of the three, write how you will close it in the next hour: rerun which lab, reread which day, re-explain to whom.

---

## Block 3: build (100 min) 🔧

Close your three gaps. Open [`labs/day-59-review-gaps/REVIEW.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-59-review-gaps/REVIEW.md), copy it, and fill in the self-assessment grid. Then spend the rest of the block on your three weakest topics, and for each one do the active thing, not the passive one: rerun the lab and re-read its numbers, then close the page and explain the idea out loud from memory until it is clean. If a lab is the fastest way to make it concrete again, rerun it. If re-reading one day page unblocks you, do that, then immediately test yourself without it.

The measure of success today is not time spent. It is that three things you could not explain this morning, you can explain cleanly tonight.

### What a good review day produces

A filled-in honest grid. Three gaps named as specific questions. And three clean explanations you could not give this morning, written in your own words, each a few sentences. If you can now explain all three to a beginner without reaching for notes, the day worked.

### Deliverable

Your filled-in `REVIEW.md` with the grid, and your three previously-shaky topics explained in your own words.

---

## Block 4: write (30 min) 📣

Your angle is the honesty of knowing your gaps. "On day 59 I did the least glamorous and most useful thing: I rated myself honestly across all eight weeks, found the three topics I still could not explain, and closed them. Revising what you already know is comfortable and useless. Revising what you can't quite say is the whole point." Share one gap you closed today and the clean explanation you can now give.

Example posts are on the [Day 59 posts](../shares/day-59-posts.md) page.

---

## End of day: log it 📝

Log the three: the three gaps you closed, the one that was most stubborn, and the single topic across all eight weeks you now feel strongest on.

Tomorrow is day 60. You present your capstone to yourself out loud as if to an interviewer, write a proper retrospective on the whole journey, and make a plan for what comes next. The finish.

---

## Solutions 🔑

Open after you have written your own map from memory.

<details markdown="1">
<summary>The eight weeks in one line each (the answer key)</summary>

Use this to grade your own map, not to study. If you could write these from memory, you know the course.

Week 1, ground truth. Know the real numbers (memory is nanoseconds, disk is microseconds, network is milliseconds), estimate before you design, and watch the tail (p99), because the average lies.

Week 2, storage. A row lives on a page; B-trees suit reads and random writes hurt them, LSM trees suit writes; indexes are a tradeoff; transactions and isolation levels decide what "correct" means; replication brings lag; sharding brings the hot shard.

Week 3, caching and the CDN. Cache-aside is the default pattern; eviction follows the working set; the thundering herd and the hot key are the two classic failures; the CDN is a cache near the user, and invalidation is the hard part.

Week 4, async, queues and the log. A queue decouples producer from consumer and absorbs bursts; the log is the primitive underneath; delivery is at-least-once plus idempotency; the outbox fixes dual-write; backpressure beats falling over.

Week 5, distributed systems. The network is unreliable and clocks lie; CAP is a real choice under partition and PACELC adds the latency tradeoff; quorums and consensus (Raft) give agreement; logical clocks order events without trusting time.

Week 6, AI systems. Inference is memory-bound and counted in tokens; the KV cache and continuous batching drive serving; vector search powers retrieval; most RAG failures are retrieval failures; agents explode the token bill; serving needs caching, limiting and fallback.

Week 7, production. Observability (logs, metrics, traces, alert on p99); SLOs and error budgets; rate limiting (token bucket, the fixed-window trap); multi-tenancy and the noisy neighbour; security boundaries (authn vs authz, IDOR); cost and capacity (size for 70 percent).

Week 8, synthesis. A design interview is a six-step performance; the hinge decision is where the signal is; and a real system is designed, built, broken under load, and written up with numbers, not hope.

</details>

<details markdown="1">
<summary>The ten ideas that carry the whole course</summary>

If everything else faded, these are the ten that would still make you dangerous.

1. Measure before you guess. The gap between your prediction and the number is the lesson.
2. Know the latency numbers cold. Memory, disk, network differ by orders of magnitude.
3. Watch p99, not the average. The tail is where real pain lives.
4. Reads and writes want different things. Design the two paths separately.
5. Cache the hot path, and respect the thundering herd and the hot key.
6. Decouple with a queue; make consumers idempotent.
7. In distributed systems the network fails and clocks lie; pick your CAP tradeoff on purpose.
8. For AI, the model is a slow expensive called service, and tokens are the budget.
9. Production is the other 80 percent: observability, SLOs, limits, cost.
10. Design before code, break your own thing before the world does, and back every claim with a number.

</details>
