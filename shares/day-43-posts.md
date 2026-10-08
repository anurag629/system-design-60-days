---
title: "Day 43 posts"
parent: "Day 43: observability"
grand_parent: "Week 7: production"
nav_order: 3
---

# Day 43 posts: LinkedIn and X

The screenshot that carries this day is Part 1: the mean sitting at a calm 77 ms right next to a p99 of 1588 ms, about 21 times higher, on the exact same stream. Swap in your own numbers and voice.

## LinkedIn

Day 43 of 60 days of system design. Week 7 is production, the unglamorous plumbing that separates a diagram from a system you can actually run. Today was observability, and I measured the single most dangerous number on a dashboard.

I generated a stream of 20,000 requests and computed the RED metrics on it: Rate, Errors, Duration. The Duration is where it got interesting.

    mean   77 ms   <- the number on the calm dashboard
    p50    36 ms   <- half of requests faster than this
    p99  1588 ms   <- 1 request in 100 is slower than this

The mean is 77 ms. The median is 36 ms. If that is all your dashboard shows, the service looks perfectly healthy. But one request in a hundred is waiting over a second and a half, and the average is designed to hide exactly that. The p99 was about 21 times the mean. This is why you alert on the p99, never on the mean.

Then logs. I wrote the same requests two ways: once as structured records with real fields, and once as a blob of prose. The on-call question was "errors for tenant acme slower than one second." Against structured logs that is one line and it returned 52 records, exactly. Against the text blob, a grep for acme plus "failed" returned 105 lines, because text has no idea what "slower than one second" means. The latency is three digits buried in a sentence, not a field you can compare. You structure the log once at write time, or you parse it forever at read time.

Then a trace. One slow request, fanned out to three services. The metric told me it took 494 ms, which is useful for an alert and useless for a fix. The trace broke it into spans and showed the search service span alone was 412 ms, 83% of the whole request. Auth and render were noise. That is the thing metrics can never do: point at the one box that ate the time.

Metrics find the fire. Logs tell you who got burned. Traces point at the match. You need all three at 3am.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #observability #sre #learninginpublic

## X thread

**1/**

Today I measured the most dangerous number on any dashboard: the average.

Same stream of 20,000 requests.

mean   77 ms
p50    36 ms
p99  1588 ms

The mean looks healthy. The p99 is on fire. Day 43 of 60 days of system design.

**2/**

The mean is 77 ms and the median is 36 ms, so the dashboard says "all good."

But the p99 is 1588 ms, about 21x the mean. One user in a hundred is waiting over a second and a half.

An average is the one summary guaranteed to hide your unhappiest customers. Alert on p99.

**3/**

This is the RED method: Rate, Errors, Duration.

Rate = requests/sec. Errors = failure %. Duration = the latency distribution, as percentiles, NOT a single mean.

Errors here were 2%, and half of them lived in that slow tail. The mean hid those too.

**4/**

Logs next. Same events, two ways.

On-call question: "errors for tenant acme slower than 1s."

structured fields:  one filter -> 52 records, exact
text blob + grep:   "acme" + "failed" -> 105 lines, wrong

Text has no idea what "> 1s" means. Latency is not a field, it is digits in a sentence.

**5/**

Structure the log once at write time, or parse it forever at read time.

Fields turn a wall of text into a database you can ask questions of. "p99 latency by endpoint" is trivial with fields and nearly impossible without them.

**6/**

Then a trace. One slow request, fanned out to 3 services.

The metric said: 494 ms. True, and useless.

The trace said: search-service = 412 ms = 83% of the request. Auth and render were noise.

Only the trace points at the ONE box that ate the time.

**7/**

Three signals, one system:

metrics find the fire
logs tell you who got burned
traces point at the match

You need all three on call at 3am.

Code: github.com/anurag629/system-design-60-days
