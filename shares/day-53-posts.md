---
title: "Day 53 posts"
parent: "Day 53: mock, a rate limiter and a news feed"
grand_parent: "Week 8: putting it all together"
nav_order: 3
---

# Day 53 posts: LinkedIn and X

The angle is compression: fluency is reaching the one decision that matters faster, not knowing more. Swap in your own voice.

## LinkedIn

Day 53 of 60 days of system design. Mock 3 was different: two designs back to back, 20 minutes each, a rate limiter and a news feed.

Twenty minutes is not enough to design everything, and that is the point. The drill was selection: get to the one decision that actually matters, fast, and spend your time there instead of drawing a generic load balancer for ten minutes.

For a rate limiter, the whole game is the word distributed. One server with a token bucket in memory is trivial. But with ten gateways and a limit of 100 per minute, a user spread across all ten quietly gets 1,000, because no single gateway sees the whole picture. So the real question is where the count lives: central in Redis for an exact limit but a network hop every request, or local per gateway for speed but loose and unfair, or a hybrid that syncs. Name the three, pick, done. And never forget the polite answer: a 429 with Retry-After.

For a news feed, the whole game is one decision wearing a trench coat: fan-out on write or fan-out on read. Push each post into all your followers' feeds so reading is cheap, which breaks the moment someone with 100 million followers posts. Or assemble each feed on open, which is cheap to write and painfully slow to read. The senior answer is the hybrid: fan-out on write for normal users, fan-out on read for celebrities, and a single feed is your precomputed list with the few celebrities you follow merged in live.

The lesson: I did two designs in the time I used to need for half of one. Fluency is not more knowledge. It is knowing where the one real decision is and going straight there.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #interviewprep #learninginpublic

## X thread

**1/**

Day 53 of 60 days of system design. Mock 3: two designs, 20 min each. A rate limiter and a news feed.

20 min is not enough to design everything. That is the point. The skill is selection.

**2/**

Rate limiter, the whole game is "distributed."

One server: trivial token bucket. Ten gateways with a 100/min limit: a user spread across all ten gets 1,000, because no gateway sees the whole picture.

**3/**

So: where does the count live?

Central Redis = exact, but a hop per request.
Local per gateway = fast, but loose and unfair.
Hybrid = sync periodically.

Name all three, pick, return 429 + Retry-After.

**4/**

News feed, one decision wearing a trench coat: fan-out on write or on read.

Push to all followers (breaks at 100M followers) vs assemble on open (slow reads).

Senior answer: hybrid. Write-fan-out for normal users, read for celebrities.

**5/**

Did two designs in the time I used to need for half of one.

Fluency is not more knowledge. It is going straight to the one decision that matters.

Code: github.com/anurag629/system-design-60-days
