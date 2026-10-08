---
title: "Day 53: mock, a rate limiter and a news feed"
parent: "Week 8: putting it all together"
nav_order: 4
has_children: true
---

# Day 53
## Mock 3, two smaller designs back to back, to build speed ⚡

Today's one idea: not every design needs the full 45 minutes, and part of being fluent is knowing how to compress the shape into 20 minutes without dropping the important parts. So today is two mini-mocks, a rate limiter and a news feed, 20 minutes each, back to back. You have built both already (Day 45 and Day 21), so the drill is speed and selection, not learning.

Doing two in one sitting teaches you something one long mock cannot: how fast you can get to the real decision when you are not allowed to dawdle.

---

## Before you start ⏪

Framework sheet on the desk. Reread Day 45 (rate limiting: token bucket, leaky bucket, the fixed-window trap) and Day 21 (the news feed: fan-out on write versus read, the celebrity problem). Two timers, or one you reset. Be strict: 20 minutes each, no spillover.

---

## Words you will meet today 📖

A token bucket is a rate-limit algorithm: a bucket refills with tokens at a fixed rate, each request spends one, and an empty bucket means "rejected." It allows short bursts (a full bucket) while capping the long-run rate (Day 45).

The 429 is the HTTP status for "Too Many Requests," usually sent with a Retry-After header telling the client how long to wait. The polite "no" that protects your system.

Fan-out on write means when you post, your post is pushed into all your followers' feeds immediately. Fan-out on read means feeds are assembled when each follower opens the app. The choice is the whole news-feed design (Day 21).

A precomputed feed is a follower's feed stored ready to serve, filled by fan-out on write, so opening the app is a cheap read instead of an expensive gather-and-rank.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read, lightly, one for each mock:
- [Design a distributed rate limiter](https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-rate-limiter) from Hello Interview. The key twist is "distributed": many gateways sharing one limit.
- [Design Facebook's news feed](https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-news-feed) from Hello Interview. Fan-out, ranking, the celebrity.

Watch, after your runs:
- [System design mock interview: design Instagram](https://www.youtube.com/watch?v=VJpfO6KdyWE) by Exponent (now Aced), about 31 minutes. Instagram's feed is the same problem as the news feed, with photos on top.

### Rate limiter: the whole game is "distributed" 🚦

A rate limiter on one server is easy: a token bucket in memory (Day 45). The interview question is almost always distributed, and that one word is the deep dive. You have ten gateway servers and a limit of "100 requests per minute per user." If each gateway keeps its own local bucket, a user spread across all ten effectively gets 1,000, because no gateway sees the whole picture. So you need shared state.

The options, and their tradeoffs: a central store (Redis) holding each user's counter, which every gateway reads and writes, giving an exact global limit at the cost of a network hop on every request and a dependency on Redis being up. Or local buckets that each enforce a fraction of the limit (10 per gateway), simple and fast but loose and unfair if traffic is lopsided. Or a hybrid: local buckets that periodically sync with the central store, trading a little accuracy for a lot less load. State the three, pick based on how exact the limit must be, and do not forget the response: a 429 with Retry-After, and the limiter sits at the gateway so bad traffic dies before it reaches your services.

### News feed: fan-out is the only question that matters 📰

The news feed is one decision wearing a trench coat: fan-out on write or fan-out on read. On write, when you post, you push the post id into every follower's precomputed feed, so opening the app is a dirt-cheap read of a ready-made list. Brilliant until someone with 100 million followers posts, and that one write becomes 100 million (Day 18, the celebrity problem). On read, you store nothing ahead of time and assemble each feed when the user opens the app by gathering recent posts from everyone they follow, which is cheap to write and expensive and slow to read.

The real answer is the hybrid, and saying it is what sounds senior. Fan-out on write for normal users (most people have a manageable follower count), and fan-out on read for the celebrities (do not push their post to 100 million feeds, instead merge their recent posts in at read time for the people who follow them). So a follower's feed is mostly precomputed, with the handful of celebrities they follow mixed in live. That hybrid is the design.

---

## Block 2: drill (40 min) ✍️

Paper first, into [`notes/day-53-drills.md`](../notes/day-53-drills.md). Two mocks, so the drills split.

D1 (rate limiter). Ten gateways, a limit of 100 per minute per user. Why does a local-only bucket on each gateway break the limit, and what are the two fixes and their costs?

D2 (rate limiter). Which algorithm would you reach for and why (token bucket, leaky bucket, sliding window), and what exactly do you return to a rejected client?

D3 (news feed). Explain fan-out on write and fan-out on read in one sentence each, and the cost that kills each one at the extremes.

D4 (news feed). The hybrid. Who gets fan-out on write, who gets fan-out on read, and how is a single follower's feed assembled from both?

D5 (both). Each of these has a classic "it falls over" moment: the rate limiter's central store goes down, and a celebrity posts. What do you do in each case?

---

## Block 3: build (100 min) 🔧

Two timed runs, 20 minutes each, with a short break between. Open [`labs/day-53-mock-ratelimiter-feed/MOCK.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-53-mock-ratelimiter-feed/MOCK.md), which has both briefs. Run the rate limiter first, stop at 20, breathe, then run the news feed.

In 20 minutes you cannot do everything, so this is a selection drill: spend your first two minutes on requirements and scale, then go almost straight to the one decision that matters (distributed state for the limiter, fan-out for the feed). Skipping to the hinge decision fast, on purpose, is the skill.

Then grade both against the rubric.

### What a strong run looks like

For each, you reach the hinge decision inside the first 8 minutes and spend the rest reasoning about it. You do not waste a 20-minute mock drawing a generic load balancer and database for ten minutes. Speed comes from knowing where the one real decision is and going there.

### Deliverable

Both filled-in briefs, both rubric scores, and one line: which of the two you ran cleaner, and why.

---

## Block 4: write (30 min) 📣

Your angle is compression. "I did two system designs in the time I used to need for half of one. Fluency is not knowing more, it is getting to the one decision that matters faster." Share the hinge decision from whichever mock you ran cleaner.

Example posts are on the [Day 53 posts](../shares/day-53-posts.md) page.

---

## End of day: log it 📝

Log the three: both rubric scores, which design you ran cleaner, and the one you want to rerun.

Tomorrow, the last mock, and the one most relevant to interviews right now: design an AI system, a production RAG or chat product. Week 6 meets everything else.

---

## Solutions 🔑

Open after your own runs.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. A local bucket on each gateway only sees the traffic that gateway handles. With a load balancer spreading one user across all ten gateways, the user can spend up to 100 on each, so the real limit becomes 1,000, not 100. Fix one: a central store (Redis) holds the per-user counter and every gateway increments it, giving an exact global limit at the cost of a network round trip per request and a hard dependency on Redis. Fix two: give each gateway a local share (10 per minute) so no central call is needed, cheap and fast but unfair and loose when traffic is uneven. The hybrid syncs local counters to the center periodically, trading exactness for load.

D2. Token bucket, usually, because it allows a natural short burst (a user who was quiet can briefly spend a full bucket) while capping the sustained rate, which matches how real clients behave. Leaky bucket if you need a strictly smooth outflow. Avoid a naive fixed window because of the Day 45 boundary trap, where a client can fire a full window's worth at the end of one window and the start of the next, getting 2x through; a sliding window fixes that. To a rejected client you return HTTP 429 Too Many Requests with a Retry-After header saying when to try again, and ideally headers showing the limit and remaining quota.

D3. Fan-out on write: when you post, the post is pushed immediately into every follower's precomputed feed, so reading the feed is cheap, but a celebrity's single post becomes millions of writes. Fan-out on read: nothing is precomputed, and each feed is assembled on open by gathering recent posts from everyone the user follows, so writing is cheap but reading is slow and expensive, especially for someone who follows thousands.

D4. Hybrid. Normal users (ordinary follower counts) get fan-out on write: their posts are pushed into followers' precomputed feeds. Celebrities (huge follower counts) get fan-out on read: their posts are not pushed to millions, instead stored once and merged in at read time. A single follower opening the app reads their mostly-precomputed feed and then merges in recent posts from the few celebrities they follow, blending the two. Most of the feed is cheap and ready; the expensive celebrities are handled lazily.

D5. Rate limiter central store down: you must fail open or fail closed, and you decide which on purpose. Fail open (allow requests when the limiter cannot check) keeps the product working but drops protection; fail closed (reject when you cannot verify) protects the backend but hurts users. Most pick fail open for a limiter with a short fallback to local buckets, so you degrade to loose limiting rather than no service. Celebrity posts: do not fan out on write; switch that user to fan-out on read so their post is merged in lazily instead of triggering millions of writes (Day 18).

</details>

<details markdown="1">
<summary>Worked reference, the rate limiter</summary>

Requirements. Functional: limit each user (or API key, or IP) to N requests per window, reject the rest politely. Non-functional: low added latency, works across many gateways, the limit should be close to exact, highly available (the limiter must not take the whole site down).

Design. The limiter is middleware at the API gateway, so rejected traffic dies before reaching your services. A central Redis holds a per-user token bucket (or a counter with a sliding window). Each request does an atomic check-and-decrement in Redis; if there is a token, allow and decrement, else return 429 with Retry-After. To cut the per-request Redis cost at high scale, gateways keep a small local cache of each user's remaining quota and sync periodically, accepting slight overshoot. If Redis is down, fail open to local-only buckets so the site stays up with looser limiting.

The senior sentence: "the limiter lives at the gateway, state is central in Redis for an exact global limit with local buffering to cut the hop, I return 429 with Retry-After, and I fail open to local buckets if the store dies so the limiter can never take down the service it protects."

</details>

<details markdown="1">
<summary>Worked reference, the news feed</summary>

Requirements. Functional: a user follows others, posts, and sees a feed of recent posts from people they follow, newest or ranked first. Non-functional: feed open must be fast (it is the most common action), read heavy, eventual consistency is fine (a post appearing a few seconds late is okay).

Design. Hybrid fan-out. On post by a normal user, push the post id into each follower's precomputed feed (a per-user list in a fast store), so opening the app is one cheap read. Celebrities are exempted from write fan-out; their posts are stored once and merged in at read time. Ranking is applied at read time on the small, already-gathered candidate set. Media lives in a blob store and CDN (week 3), not in the feed itself, which holds ids.

The senior sentence: "fan-out on write for the many so the feed open is a cheap read, fan-out on read for the celebrities so one post is not a hundred million writes, and a follower's feed is their precomputed list with the handful of celebrities they follow merged in live."

</details>

<details markdown="1">
<summary>The self-grade rubric (apply to each mock)</summary>

Score each out of 2.

- Requirements and scale in the first ~4 minutes, not ten?
- Did you name the one hinge decision (distributed state, or fan-out)?
- Did you reach that decision inside 8 minutes?
- Did you reason through the tradeoff rather than assert an answer?
- Did you cover the "it falls over" case (store down, celebrity)?

8 to 10, fast and clean. 5 to 7, you got there but dawdled early. Below 5, you spent too long on the generic setup, which is the exact habit a two-mock day is meant to break.

</details>
