---
title: "Day 45 posts"
parent: "Day 45: rate limiting"
grand_parent: "Week 7: production"
nav_order: 3
---

# Day 45 posts: LinkedIn and X

The scoreboard makes a good screenshot: the fixed window let 200 through a "100 per minute" limit, the sliding window held it to 100, the token bucket capped a burst at 20, the leaky bucket emitted a flat 10/s. Swap in your own numbers and voice.

## LinkedIn

Day 45 of 60 days of system design. Today I built the thing that stands at the front door of every API and decides who gets in: the rate limiter. And I found the bug that lives inside the most common one people write.

The naive version is a fixed-window counter. "100 requests per minute, reset on the minute." Looks fine. Here is what I measured when a client times it on purpose:

    fixed window:   accepted 200 across the boundary (2x the limit)
    sliding window: accepted 100 across the boundary (1x the limit)

Send 100 requests at 11:59:59, then 100 more at 12:00:00. The counter resets on the minute, so both batches pass. That is 200 requests in about two seconds, through a limiter that promised 100 a minute. For one second your backend takes double the load it was sized for. A sliding-window counter looks at the trailing 60 seconds instead of a fixed box, sees the first batch is still in the window, and rejects the excess. One line of difference, and the hole closes.

Then I compared the two bucket algorithms on the same bursty traffic.

    token bucket: lets a burst of 20 straight through, then meters at 10/s
    leaky bucket: emits a flat 10/s no matter how the input arrives

A token bucket holds up to N tokens and spends one per request, so it allows a friendly burst up to the bucket size and then settles to the refill rate. A leaky bucket queues requests and drains them at a constant rate, so the output is a smooth stream with no bursts, at the cost of queueing delay. Token bucket when a burst is fine. Leaky bucket when the thing behind you is fragile and must never see a spike.

This is the IRCTC tatkal problem in its purest form. Ten in the morning, the whole country hits the same endpoint in the same second, and the limiter is what stands between an orderly queue and a pile-up.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #ratelimiting #learninginpublic

## X thread

**1/**

Day 45 of 60 days of system design.

I wrote a "100 requests per minute" rate limiter, the fixed-window kind almost everyone writes first. Then I timed a client to beat it:

    accepted 200 across the boundary

2x the limit. Here is why.

**2/**

A fixed window resets the counter on the minute.

So a client sends 100 at 11:59:59 and 100 more at 12:00:00. Window 1 fills, the clock ticks, window 2 resets, window 2 fills. 200 requests in ~2 seconds, through a limiter that promised 100/min.

For one second your backend eats double.

**3/**

The fix is a sliding window: count the trailing 60 seconds, not a fixed box.

    sliding window: accepted 100

Now the second batch still sees the first batch inside its trailing minute, so the counter is already full and the excess gets a 429. Same stream, half the damage.

**4/**

Then the two bucket algorithms, same bursty input:

token bucket: a burst of 20 gets straight out, then a steady 10/s
leaky bucket: a flat 10/s, always, no bursts

**5/**

Token bucket holds N tokens, spends one per request. It allows a burst up to the bucket size, then settles to the refill rate. Bursts are fine.

Leaky bucket queues and drains at a constant rate. Output is smooth, the cost is queueing delay. Use it to shield a fragile downstream.

**6/**

So the limiter is not one thing. It is a choice:

- fixed vs sliding window: is the boundary honest?
- token vs leaky bucket: do you allow bursts or smooth them?

Same job, "who gets in", different shapes of yes and no. This is the IRCTC tatkal problem.

Code: github.com/anurag629/system-design-60-days
