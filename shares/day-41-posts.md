---
title: "Day 41 posts"
parent: "Day 41: serving concerns, caching, limiting and fallback"
grand_parent: "Week 6: AI systems"
nav_order: 3
---

# Day 41 posts: LinkedIn and X

The scoreboard is the screenshot: a semantic cache hitting 68% where an exact-match cache hits 7%, a request cap letting 20x the token budget through, and fallback turning a total outage from 0% served into basically 100%. Swap in your own numbers and voice.

## LinkedIn

Day 41 of 60 days of system design. Week 6 is AI systems, and the thing nobody warns you about is that most of the hard engineering is not the model at all. It is the three boring layers around it. I built all three today, in plain Python, and measured them.

1. Semantic cache. A normal cache keys by the exact string, so "how do I reset my password" and "steps to reset my password" look like two different requests and both hit the model. A semantic cache keys by meaning: embed the query, and if it is close enough to something you already answered, return the cached answer. On a support-chat workload that was mostly paraphrases:

    exact-match cache:   7% hit rate
    semantic cache:     68% hit rate

Same traffic. The exact cache caught only the word-for-word repeats. The semantic one cut model calls by more than half.

2. Token-based rate limiting. LLM cost is per token, not per request, so a requests-per-minute limit is the wrong meter. I gave a request cap and a token bucket the same budget, then sent a batch of big requests:

    token bucket:  held spend at the budget
    request cap:   spent 20x the budget

The request cap silently assumed every request was small. One feature that sends big requests and it blew the budget twentyfold.

3. Gateway with fallback. The primary model fails sometimes. Retries handle the odd blip fine. But when I simulated a full provider outage, retries were useless (three failures out of three, every time) and success dropped to 0%. Add a fallback to a second provider and success went back to basically 100%.

None of this is AI magic. It is caching (week 3), rate limiting and backpressure (week 4), and failover (week 5), pointed at a GPU. That is the whole lesson of this week.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #llm #learninginpublic

## X thread

**1/**

Day 41 of 60 days of system design.

The surprise of AI serving: the model is the easy part. The hard engineering is the three layers around it. Built all three in plain Python today and measured them.

**2/**

Semantic cache.

A normal cache keys by exact string, so "reset my password" and "steps to reset my password" both hit the model. A semantic cache keys by MEANING.

Same support workload:

exact-match cache:  7% hit
semantic cache:    68% hit

More than half the calls, gone.

**3/**

Token-based rate limiting.

LLM cost is per TOKEN, not per request. So a requests-per-minute limit meters the wrong thing.

Gave a request cap and a token bucket the same budget, sent big requests:

token bucket: held the budget
request cap:  spent 20x the budget

**4/**

The request cap quietly assumed every request was small (100 tokens). One feature that sends 2,000-token requests and it overspent 20x. The token bucket meters the token, which is what the invoice counts.

**5/**

Gateway with fallback.

Primary model fails sometimes. Retries fix the odd blip (three failures in a row is rare).

But in a full outage, retries are useless:

no fallback:  0% served
fallback:    ~100% served

Fallback is the insurance you are glad you paid.

**6/**

The whole week in one line: AI serving is distributed systems with a GPU in the middle.

Semantic cache = caching (week 3).
Token bucket = rate limiting (week 4).
Fallback = failover (week 5).

Nothing new. New target.

Code: github.com/anurag629/system-design-60-days
