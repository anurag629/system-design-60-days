---
title: "Day 50 posts"
parent: "Day 50: the framework"
grand_parent: "Week 8: putting it all together"
nav_order: 3
---

# Day 50 posts: LinkedIn and X

The angle is the reframe: a design interview is a performance with a shape, not a memory test. Swap in your own voice.

## LinkedIn

Day 50 of 60 days of system design. Start of the last week, and today there was no new theory, just a shape.

I used to freeze in design interviews. I would try to remember an answer I had watched on YouTube, and the moment the question was even slightly different, I was lost. Today I learned why. I was treating a performance like a memory test.

A 45-minute design interview has a fixed shape, six steps:

1. Requirements, 5 min. What does it do, and how well (scale, latency, consistency)? Ask, do not assume.
2. Scale estimate, 5 min. Back of the envelope. Reads per second, writes per second, storage per year.
3. API and entities, 5 min. The handful of endpoints and the main data objects.
4. High-level design, 10 to 15 min. Boxes and arrows, the read path and the write path.
5. Deep dives, 10 to 15 min. Pick the hard part and go deep. This is where seniority shows.
6. Bottlenecks and failure, 5 min. What breaks, how you see it, how you degrade.

The thing nobody told me: once the shape is muscle memory, your brain stops spending energy on "what comes next" and spends it on the actual problem. Like a batsman who has grooved the shot in the nets, so in the match the head stays still to read the ball.

The other half is not on the whiteboard. Drive the conversation. Narrate every box and what it costs. State tradeoffs as choices. Watch the clock, because the most common failure is spending 20 minutes on requirements and never reaching the deep dive where the real signal is.

Tomorrow I run the whole thing for real: mock 1, a URL shortener, against the clock.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #interviewprep #learninginpublic

## X thread

**1/**

Day 50 of 60 days of system design. Last week starts. No new theory today, just a shape.

I used to freeze in design interviews because I was treating a performance like a memory test.

**2/**

A 45-min design interview has six steps:

1. Requirements (5m)
2. Scale estimate (5m)
3. API + entities (5m)
4. High-level design (10-15m)
5. Deep dives (10-15m)
6. Bottlenecks + failure (5m)

**3/**

The unlock: once the shape is muscle memory, your brain stops burning energy on "what next" and spends it on the actual problem.

Groove the shot in the nets so in the match your head stays still.

**4/**

Half of it is not on the whiteboard: drive the conversation, narrate every box and its cost, state tradeoffs as choices, watch the clock.

Most common failure: 20 min on requirements, never reach the deep dive where the signal is.

**5/**

Tomorrow: mock 1, design a URL shortener, end to end and timed.

Code: github.com/anurag629/system-design-60-days
