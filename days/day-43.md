---
title: "Day 43: observability"
parent: "Week 7: production"
nav_order: 1
has_children: true
---

# Day 43
## Observability, or why a mean hides the fire 🔭

Today's one idea: when your system misbehaves at 3am, you cannot SSH into it and poke around with print statements. You get whatever you decided, in advance, to record. That recording comes in three shapes: logs, metrics and traces. Each answers a different question, and the single most expensive mistake people make is watching an average when they should be watching a percentile. An average is the one number guaranteed to hide your worst customers.

This is the first day of week 7, production. The clever algorithms are behind you. What is left is the plumbing that decides whether a design on a whiteboard survives contact with real traffic. Observability is where that plumbing starts, because you cannot fix what you cannot see.

---

## Before you start ⏪

Two earlier days do most of the heavy lifting today, so pull them back up. Day 1 taught you percentiles: the median is the middle request, the p99 is the 990th of a thousand, and averages lie when the data has a tail. Day 4 showed you where that tail comes from, the queue in front of a busy server, and ended on the line "averages hide this, your users feel the p99." Today you stop reading about the tail and start measuring it on a stream you generate yourself. Day 2's comfort with plain Python is all the code you need.

---

## Words you will meet today 📖

Observability is how well you can understand what a system is doing inside from the signals it emits outside. A system is observable when you can answer a new question about its behaviour without shipping new code to ask it.

Telemetry is the data the system emits for that purpose. It comes in three shapes, and people call them the three signals or the three pillars.

A log is one event, recorded as it happened: "request X from tenant acme failed after 1532 ms." One line, one moment.

A metric is many events rolled into a number over time: requests per second, error rate, the p99 latency this minute. You lose the individual events and keep the shape.

A trace follows one request as it travels across services, broken into spans. Each span is one timed unit of work (a database query, an API call) with a start, a duration, and a pointer to its parent.

Structured logging means writing each log as fields (tenant, status, latency_ms) instead of a sentence, so you can filter and aggregate it like a database instead of grepping prose.

The RED method is the three metrics every request-driven service should expose: Rate (requests per second), Errors (the failure rate), and Duration (the latency distribution, as percentiles). The USE method is its mirror for a resource: Utilisation, Saturation and Errors, for a disk, a CPU or a connection pool.

A percentile is the latency only a given fraction of requests exceed. The p50 is the median, the p99 is what your slowest 1 percent live beyond. You care about these, not the mean.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/), the Google SRE book chapter. The source of the "four golden signals" (latency, traffic, errors, saturation), and the clearest argument for why you watch distributions, not averages. If you read one thing today, read this.
- [The RED method: how to instrument your services](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/) by Tom Wilkie. Rate, Errors, Duration, the exact three you compute in Part 1 of the lab, and why those three cover almost every request-driven service.
- [The USE method](https://www.brendangregg.com/usemethod.html) by Brendan Gregg. The resource-side mirror: Utilisation, Saturation, Errors. Short, and it is the instinct you reach for once a trace points you at a slow box.

Watch, after the lab:
- [Observability crash course: logs, metrics, traces explained](https://www.youtube.com/watch?v=umm-MyCl3Q4) by System Design Lab, about 36 minutes. A thorough tour of the three signals and how they fit together.
- [Distributed tracing in microservices, the big picture](https://www.youtube.com/watch?v=WS-eL_mkfWU) by CodeSnippet by Chetan, about 17 minutes. Exactly the Part 3 idea: one request, a shared trace id, spans across services.

### Three signals, and the question each one answers (16 min)

Think about ordering food on Swiggy or Zomato. Your order is late. There are three completely different things you might want to know, and they map one to one onto the three signals.

First, "how bad is it, overall, right now?" The app tells you the average delivery time in your area is up today. That is a metric: many orders rolled into one number over time. It is cheap to keep, it is what you put on a dashboard, and it is what fires an alert. What it cannot tell you is why your order specifically is late.

Second, "what exactly happened to order number 48213?" You dig out the one record for that order: placed at 8:02, accepted by the restaurant at 8:05, failed payment retry at 8:07. That is a log: one event, with detail, about one thing that happened. Logs are where you go once a metric has told you something is wrong and you need the specifics.

Third, "which leg of the journey was slow?" The tracking screen shows the restaurant took 30 minutes, the rider waited 10, and the ride to you was 5. That is a trace: one order, broken into timed stages across different actors, so you can see which stage ate the time. Forty five minutes total tells you nothing actionable. "The restaurant took 30 of those 45" tells you exactly where to look.

That is the whole mental model. Metrics tell you something is wrong. Logs tell you what happened to a specific request. Traces tell you where, across many services, the time or the failure actually lived. You need all three, because each one is useless at the job of the other two. A metric cannot name the slow service. A log cannot show you the shape of ten million requests. A trace of one request cannot tell you the error rate.

### Why a mean hides the fire, and RED is the fix (18 min)

Here is the part that bites people in production, and it is the thing you will measure today.

Picture a class of 100 students. Ninety nine of them score 40 out of 100 on a test, and one scores 4000 (humour me, it is a generous teacher). The class average is about 80. That average describes nobody. No student scored anywhere near 80. It is the arithmetic blend of a struggling majority and one wild outlier, and it is a lie about both.

Latency works exactly the same way, except the outlier is the request that matters most. Most of your requests are fast. A few are horrible. The mean sits in a no man's land between them, looking calm, describing no real user. In the lab you generate 20,000 requests where 90 percent are quick, a middle band is slower, and 2 percent fall off a cliff. The mean comes out around 77 ms and the median around 36 ms. Both look perfectly healthy. The p99 comes out around 1588 ms. One request in a hundred is waiting over a second and a half while your dashboard shows 77 ms and everyone goes home happy.

This is why the RED method exists. For any request-driven service you watch three things. Rate is how many requests per second are arriving, your traffic. Errors is what fraction of them failed, because a service can be lightning fast and still be returning 500s to one user in twenty, and a latency number will never show you that. Duration is the latency, and the whole discipline is in that one word "distribution." You never report Duration as a mean. You report p50, p99, and often p99.9, because the gap between them is the actual story. If your p50 is 36 ms and your p99 is 1588 ms, that 44x spread is telling you that a small, specific slice of your traffic is on fire, and your job is to go find it. The mean would have told you nothing was wrong at all.

So the rule you carry out of today: alert on the p99, never the mean. The mean is not a summary of your system, it is a way of not looking at it.

### When only a trace will do (12 min)

Metrics and logs have a shared blind spot. A modern request does not live in one place. It arrives at a gateway, which calls an auth service, which calls a search service, which hits a database, which calls a cache, and so on. Your p99 metric can scream "requests are slow," and your logs can show you one slow request, but neither can tell you which of the eight services in the chain actually ate the time. For that you need a trace.

A trace works by giving one request a single trace id at the front door and carrying that id with it to every service it touches. Each service records a span: its own slice of work, with a start time, a duration, its own span id, and a pointer back to the span that called it. Those spans fly off to a collector independently, from different machines, and because they all share the one trace id the collector can stitch them back into a tree. Now you can see the whole request laid out as a timeline, and the slow span sticks out like a sore thumb.

In the lab's Part 3 you take one slow request, the kind that was sitting anonymously in the p99 tail of Part 1, and you break it open. The gateway reports 494 ms. Useless on its own. The trace shows the search service span alone was 412 ms, 83 percent of the whole request, while auth and render were noise. That is the number you cannot get any other way. And it hands you straight to the USE method: now that you know the search service is slow, you go look at the resource behind it. Is its CPU pinned (utilisation), is its request queue backed up (saturation), is it throwing errors? RED told you the request was slow. The trace told you where. USE tells you why the box is struggling. Same instinct, three altitudes.

---

## Block 2: drill (40 min) ✍️

Paper first, with the arithmetic done by hand. Then copy your answers into [`notes/day-43-drills.md`](../notes/day-43-drills.md). About 8 minutes each.

D1. The mean lies, on purpose. 100 requests: 99 of them take 40 ms, and one takes 4,000 ms. Work out the mean, the p50 and the p99 by hand. Which of the three would a dashboard showing only "average latency" report, and what is it hiding? In one line, why is the average the single worst summary of a user's experience?

D2. The RED method. Name the three RED signals for a request-driven service and say in a few words what each one tells you. For a service running at 500 req/s, 3% errors and a p99 of 1.4s while the mean is 60 ms, which signal pages you first and why? Which one would a "mean latency" alert have completely missed?

D3. Structured vs unstructured. You keep 10 million log lines a day. At 3am someone asks "every 5xx for tenant acme on /checkout slower than one second in the last hour." Why is that one line against structured logs and an ordeal against a blob of prose? Name the one field that, if nobody logged it, makes the question unanswerable after the fact, and say what that tells you about when logging decisions get made.

D4. A trace across services. A request fans out to three downstream services called one after another: 20 ms, 430 ms and 35 ms, plus 15 ms of gateway work. What is the total latency, and what fraction is the slow span? A latency metric reports only that total; what can the trace tell you that the metric cannot? Now suppose the three ran in parallel instead: what is the total, and which span does the trace still finger?

D5. RED, USE, and the tail under fan-out. RED is for requests; USE is utilisation, saturation and errors for a resource. Which do you reach for to explain a slow endpoint, and which to explain why the database behind it is slow? Then the Day 1 question again: one backend has a p99 of 100 ms (1% of its calls are slow), and a page makes 10 independent calls to it. What fraction of page loads contain at least one slow call, and why does that make a dependency's p99 matter more than it first looks?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-43-observability/observability.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-43-observability/observability.py).

It generates one stream of 20,000 requests and then looks at it three ways, because that is exactly what the three signals are: three lenses on the same traffic. Part 1 computes the RED metrics and puts the mean next to the p99. Part 2 writes the same requests as structured records and as a blob of prose, then asks one on-call question of each. Part 3 takes one slow request, fans it out across three services with a shared trace id, and finds the span that ate the time. Standard library only, deterministic off a fixed seed, and it runs in well under a second with nothing to clean up.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. The stream's mean latency, in milliseconds. This is the number a naive dashboard shows. Does it look healthy?
- P2. The same stream's p99 latency, in milliseconds. One request in a hundred is slower than this. Write a number down before you peek, because this is the one almost everyone guesses too low.
- P3. The structured query: how many records are for tenant acme, are errors, and are slower than 1000 ms?
- P4. The trace: the slowest single span, in milliseconds. The one the trace fingers.

P2 is the gut-check. Most people, looking at a mean of "about 70 ms," guess a p99 of maybe 150 or 200. Write down your honest guess and see how far off the tail really is.

### Fill in the TODOs

1. TODO 1 is `percentile`, by linear interpolation. This one function is the whole reason a dashboard can show the tail instead of burying it in a mean.
2. TODO 2 is `error_rate`, the E in RED: the fraction of requests with status 500 or more.
3. TODO 3 is `matches_query`, three fields ANDed together. It is trivial here and impossible against prose, which is the entire point of Part 2.
4. TODO 4 is `slowest_span`, the one line that turns "the request was slow" into "the search service was slow."

```bash
cd labs/day-43-observability
python3 observability.py
```

The file stops cleanly and tells you which TODO to fill in next, so work through them in order. Nothing below a blank TODO runs.

### What you're going to discover

Part 1 is the shock, and it is the same shape as Day 9's random-insert surprise. The mean (around 77 ms) and the median (around 36 ms) both look fine. The p99 is around 1588 ms, roughly 21 times the mean. Identical stream, and the two numbers tell opposite stories. One of them is a comforting lie.

Part 2 is the one that changes how you write code tomorrow. The structured query returns exactly 52 matching records in one line. The grep over prose returns 105 lines, because "acme plus failed" cannot express "slower than one second," since the latency is three digits buried in a sentence rather than a field you can compare. Getting the right answer from text means regexing the number back out of every line, which is just rebuilding the field you threw away at write time.

Part 3 is the fix for the blind spot. The metric says the request took 494 ms. The trace says the search service span was 412 of those 494 ms, 83 percent, while auth and render were noise. That is the thing neither a metric nor a single log line could ever have told you.

### Traps ⚠️

- Do not report Duration as a mean, ever, not even "just for a quick look." The quick look is exactly where the tail hides. Train the reflex now: latency is a distribution, and you quote p50 and p99.
- Structured does not mean JSON specifically. It means fields. Key-value, JSON, columns in a table, all fine. The point is that "latency" is a number you can compare, not a word in a sentence.
- A trace id is worthless if it stops at the first service. The whole value is in propagating the same id across every hop, so the spans can be stitched back together. Dropping it at a service boundary is the most common way teams end up with "traces" that only ever show one span.
- p99 is not p100. The lab also prints p99.9 and the max, and they are much larger than p99. There is always a worse tail further out. Pick the percentile that matches the promise you are making, do not chase the max.

### Deliverable

[`labs/day-43-observability/RESULTS.md`](../labs/day-43-observability/RESULTS.md) has a skeleton. Paste the output, and write one line: how many times bigger was your p99 than your mean, and which single span did the trace blame for the slow request?

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise, and it is a strong one for a feed: "I put a mean latency of 77 ms right next to the p99 of the exact same traffic, which was 1588 ms, about 21 times higher. The average said the service was healthy. One user in a hundred was waiting over a second and a half. This is why you never alert on the mean." The scoreboard, mean beside p99, is the screenshot.

Example posts are on the [Day 43 posts](../shares/day-43-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the gap you measured between your mean and your p99, and one thing you still cannot explain.

Day 44 is SLOs and error budgets: you take the percentiles you learned to measure today and turn them into a promise ("99.9 percent of requests under 300 ms"), then work out what that promise costs you in real downtime and why chasing 100 percent is a trap. Today you learned to see the system. Tomorrow you learn to make a promise about it, in numbers.

---

## Solutions 🔑

Open these only after you have done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The sum is 99 times 40 plus 4000, which is 3960 plus 4000, so 7960, and the mean is 79.6 ms. The p50 is the middle value, and 99 of the 100 values are 40, so the median is 40 ms. The p99 sits right at the boundary of that single slow request: by interpolation it comes out around 80 ms, and if you simply take the slowest 1 percent it is the 4000 ms request itself. A dashboard showing "average latency" reports 79.6 ms. That one number hides two facts at once: that the typical request is actually 40 ms (faster than it claims), and that one request in a hundred is 4000 ms (a hundred times worse than it claims). The average is the worst summary because it blends the happy majority and the suffering minority into a single number that describes neither of them. It is the class average that is "fine" while one student is failing and the rest are bored.

D2. Rate is requests per second, your traffic or demand. Errors is the fraction of requests that failed, usually the 5xx rate. Duration is the latency distribution, reported as percentiles (p50, p99), never as a mean. For the service given, Errors pages you first: 3 percent of 500 req/s is 15 requests failing every second, which is a live outage for those users right now. The p99 of 1.4s is the next thing to chase, a slow tail that real users are feeling. A "mean latency" alert set on 60 ms would have stayed green through both the 3 percent error rate and the 1.4s tail, which is exactly why you do not alert on the mean.

D3. Against structured logs it is one filter: status >= 500, tenant == "acme", endpoint == "/checkout", latency_ms > 1000, timestamp in the last hour. Every clause is a field comparison the store can index. Against prose you must regex each value out of every line before you can compare it, and the matching is fragile: a substring search for "acme" also catches "acme-staging," and "slower than one second" cannot be expressed as a substring at all, because the latency is digits inside a sentence rather than a number you can test. The one field that makes the question unanswerable after the fact if it was never logged is the tenant id (the latency is the other). If nobody attached the tenant to each line, no amount of grep can tell you afterwards which lines belonged to acme, because that information was never written down. The lesson: observability is a design decision made at write time, before the incident, not a clever query you invent during it. You log the fields you will need for questions you cannot yet predict.

D4. Sequential: 20 + 430 + 35 + 15 = 500 ms total, and the slow span is 430 / 500 = 86 percent of the request. The latency metric reports only "500 ms." The trace tells you the 430 ms lived in the second service specifically, not auth, not render, not the gateway, so you know exactly which box to go look at. In parallel, the total is the slowest branch plus the gateway work, max(20, 430, 35) + 15 = 445 ms. The trace still fingers the same 430 ms span, because even in parallel it is the one on the critical path: the request cannot finish until its slowest branch does. Parallelism changes the total, not the culprit.

D5. You reach for RED to explain the slow endpoint (the request's rate, errors and duration), and for USE to explain why the database behind it is slow (is its CPU utilised, is its connection pool or disk queue saturated, is it erroring). RED is the request's view, USE is the resource's view, and a trace is usually what hands you from one to the other. The fan-out tail: each call is slow 1 percent of the time, the 10 calls are independent, so the chance all 10 are fast is 0.99 to the power 10, about 0.904, and the chance at least one is slow is 1 minus that, about 9.6 percent. So nearly one page load in ten contains a slow call, even though each individual call is "only 1 percent slow." Fan-out multiplies the tail, which is why a dependency's p99 matters far more than it looks: the more calls a page makes, the more surely it inherits the tail of its slowest dependency.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-43-observability/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-43-observability/solution.py).

TODO 1, the percentile by linear interpolation, the function that lets you see the tail instead of hiding it in a mean:

```python
if not values:
    return 0.0
s = sorted(values)
k = (len(s) - 1) * (p / 100.0)
lo, hi = math.floor(k), math.ceil(k)
if lo == hi:
    return s[int(k)]
return s[lo] + (s[hi] - s[lo]) * (k - lo)
```

TODO 2, the E in RED, the error rate as a percent:

```python
errors = sum(1 for r in records if r.status >= 500)
return errors / len(records) * 100.0
```

TODO 3, the structured-log query, three fields ANDed together:

```python
return (rec.tenant == tenant
        and rec.status >= 500
        and rec.latency_ms > min_latency_ms)
```

TODO 4, the one line that turns "the request was slow" into "the search service was slow":

```python
return max(spans, key=lambda s: s.dur_ms)
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, seed 43, 20,000 requests.

```
==============================================================================
Part 1: metrics (RED). Rate, Errors, Duration. The mean looks calm;
        the p99 is on fire.
==============================================================================
  stream: 20,000 requests over 60s

  R  Rate          333.3 req/s
  E  Errors         2.10 %      (status >= 500)
  D  Duration:
       mean        77.0 ms   <- the number on the calm dashboard
       p50         36.1 ms   <- half your requests are faster than this
       p90         79.0 ms
       p99       1588.0 ms   <- 1 request in 100 is SLOWER than this
       p99.9     2136.2 ms
       max       2195.9 ms

  The mean is 77 ms and the median is 36 ms. If that is all your
  dashboard shows, the service looks healthy. But the p99 is 1588 ms,
  about 21x the mean. One user in a hundred is waiting over a
  second while the average says everything is fine.
  This is Day 1's percentiles and Day 4's queue tail, made concrete:
  the average is the one summary number that is guaranteed to hide
  your worst customers. You alert on the p99, never the mean.

==============================================================================
Part 2: logs. Structured fields you can query vs a blob you cannot.
==============================================================================
  The on-call question at 3am: errors for tenant "acme" with latency over 1000ms.

  Structured logs (records with real fields):
    [r for r in log if r.tenant=='acme' and r.status>=500 and r.latency_ms>1000]
    -> 52 matching records, exactly. Here are three:
       tenant=acme /checkout status=500 latency=1637ms
       tenant=acme /login status=500 latency=2171ms
       tenant=acme /login status=500 latency=1747ms

  Unstructured logs (the same events as prose):
       [  0.00] request from umbrella to /login served after 28ms
    grep 'acme' | grep 'failed'  ->  105 lines
    ...but that counts EVERY acme error, including the fast ones.
    It has no idea what '> 1000ms' means, because 'latency' is
    not a field here, it is three digits buried in a sentence. To get
    the real answer from text you must regex the number out of every
    line and compare it, which is just rebuilding the field you threw
    away at write time. Structure the log once, or parse it forever.

  And aggregation is free once you have fields. p99 latency by endpoint:
       /checkout   p99 =  1720.1 ms  (4,910 requests)
       /search     p99 =  1544.2 ms  (4,986 requests)
       /feed       p99 =  1441.0 ms  (4,979 requests)
       /login      p99 =  1587.2 ms  (5,125 requests)
  Try writing THAT over a blob of prose. Fields are what make a log a
  database you can ask questions of, instead of a wall of text.

==============================================================================
Part 3: traces. Metrics say the request was slow. The trace says why.
==============================================================================
  One request, trace id trc-4f447fdf. Metrics (Part 1) would
  record just one number for it: 494 ms, somewhere out in the p99
  tail. Useful for an alert, useless for a fix. Now the trace:

  span                         start      dur  % of req
  api-gateway.request             0ms    494ms      100%
    user-service.lookup           8ms     23ms        5%  #
    search-service.query         31ms    412ms       83%  #################################
    render-service.html         442ms     45ms        9%  ###

  Every span shares the one trace id (trc-4f447fdf) and points at
  its parent, so the collector can rebuild this tree from spans that
  arrived separately from three different services.

  The slowest span is search-service.query at 412 ms, which is
  83% of the whole 494 ms request. THAT is what a
  trace buys you. The metric knew the request was slow. Only the trace
  knows it was the search service, not auth, not render, not the
  gateway. This is RED per request; the USE method (utilisation,
  saturation, errors) is the same instinct pointed at the resource
  behind that slow span: is the DB's disk or CPU saturated?

==============================================================================
Scoreboard
==============================================================================
  P1 mean latency                you =    70.0   actual =     77.0 ms       close enough
  P2 p99 latency                 you =  1500.0   actual =   1588.0 ms       close enough
  P3 acme slow errors            you =    50.0   actual =     52.0        close enough
  P4 slowest span                you =   430.0   actual =    411.6 ms       close enough

==============================================================================
The number to carry
==============================================================================
  Same stream, one mean and one p99. The mean was 77 ms and looked
  healthy. The p99 was 1588 ms, about 21x higher, and that is the
  number your slowest users actually live in. A mean hides the fire;
  the percentile shows it. That is the whole case for metrics done right.
  And when one request was slow, the trace put 412 of its 494 ms
  on a single span, the search service. Metrics find the fire, logs
  tell you who was burned, traces point at the match. Three signals,
  one system, and you need all three on call at 3am.
```

Part 1 is the day. The same 20,000 requests, two summary numbers, opposite stories. The mean of 77 ms and the median of 36 ms both say the service is healthy. The p99 of 1588 ms says one request in a hundred is waiting over a second and a half. That 21x gap between the mean and the p99 is the whole reason the SRE world watches distributions and alerts on percentiles. An average is not a summary of your system, it is a way of not seeing it.

Part 2 is the habit that follows you into every service you write after today. The structured filter answered a precise question in one line and returned 52 records. The grep over prose returned 105, because text cannot do arithmetic: "slower than one second" is meaningless when the latency is three digits inside a sentence rather than a field. The fix is not a cleverer grep, it is to log fields at write time. You decide what you will be able to ask long before the incident that makes you want to ask it.

Part 3 is the blind spot closing. A metric reported the slow request as a single 494 ms number, true and useless. The trace broke it into spans sharing one id and showed that the search service alone was 412 ms, 83 percent of the request, while auth and render were nothing. That is the one question metrics and logs genuinely cannot answer, which service in the chain ate the time, and it is why distributed tracing exists. From there the USE method takes over: go look at whether that search service's CPU, queue or disk is saturated.

The one line to carry out of today: metrics find the fire, logs tell you who got burned, and traces point at the match. You alert on the p99, never the mean, and you need all three signals the night something breaks.

</details>
