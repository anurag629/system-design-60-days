---
title: "Day 45: rate limiting"
parent: "Week 7: production"
nav_order: 3
has_children: true
---

# Day 45
## Token bucket, leaky bucket, and the trap hiding inside the counter you would write first 🚦

Today's one idea: a rate limiter is the bouncer at the front door of your API. Its whole job is to say "yes, come in" to some requests and a fast "no, 429, try later" to the rest, so that a flood never reaches the thing behind it. There are a handful of ways to decide that yes or no, and they are not interchangeable. One of them, the one almost everyone writes first, quietly lets twice your limit through at exactly the wrong moment. Today you measure that hole on your own machine, and you learn which algorithm to reach for when a burst is friendly and which when the thing behind you is fragile.

This is the IRCTC tatkal problem in its purest form. Ten in the morning, booking opens, and every phone in the country hits the same endpoint in the same second. The limiter is the difference between an orderly queue and a pile-up that takes the whole booking system down with it.

---

## Before you start ⏪

One thing to get straight up front, because it trips people. On Day 27 you built backpressure and load shedding: that was work already inside your system, a bounded queue pushing back on a producer you control. Today is different. This is the limiter at the edge, facing the open internet, deciding which incoming requests even get to start. Same spirit, a fast no beats a slow collapse, but a different place and a different tool. Day 27 was the kitchen telling the waiters to slow down. Today is the bouncer at the door counting people in.

You need Day 4's queue intuition (a fast "no" protects you where an unbounded "yes" kills you) and a comfort with thinking in requests per second. The Day 2 level of Python is plenty for the lab.

---

## Words you will meet today 📖

A rate limiter is a component that caps how many requests a client (a user, an API key, an IP) may make in a given time, and rejects or delays the rest. It lives at the edge, usually in the API gateway.

A token bucket holds up to a fixed number of tokens (the capacity) and refills at a steady rate. Each request takes one token or is rejected. It allows a burst up to the bucket size, then settles to the refill rate. This is the most common API rate limiter.

A leaky bucket is a queue that drains at a constant rate. Requests join the bucket and leave at a fixed pace, so the output is a smooth stream with no bursts. If the bucket overflows, the excess is dropped.

A fixed-window counter counts requests in a clock-aligned window (per minute, per hour) and resets the count when the clock ticks into the next window. Cheap, and the source of today's trap.

A sliding-window counter counts requests in the trailing window ending now, not in a clock-aligned box, so there is no boundary to game.

HTTP 429 is "Too Many Requests", the status a limiter returns when it says no. A good 429 carries a Retry-After header telling the client how long to wait before trying again.

The burst allowance is how much a client can exceed the steady rate for a short moment. In a token bucket it is exactly the capacity.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these, Stripe first:
- [Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters) by Stripe. The clearest practical tour of the token bucket and the four common limiters, from a team that runs them on real payment traffic. If you read one thing, read this.
- [How we built rate limiting capable of scaling to millions of domains](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/) by Cloudflare. This is the sliding-window story: why the fixed window leaks at the boundary and how a trailing-window count fixes it without storing every timestamp.
- [Fixing retries with token buckets and circuit breakers](https://brooker.co.za/blog/2022/02/28/retries.html) by Marc Brooker. Short and dense. The token bucket turned inward, used to cap retries so a struggling dependency does not get a retry storm on top of its bad day.
- [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/) from the AWS Builders' Library. The grown-up version of saying no: reject early, reject cheaply, and protect the work already in flight. This is where rate limiting meets Day 27.

Watch, after the lab:
- [Five Rate Limiting Algorithms](https://www.youtube.com/watch?v=mQCJJqUfn9Y) by Hello Byte, about 17 minutes. Walks fixed window, sliding window, token bucket and leaky bucket with clear diagrams. Exactly today's material.
- Optional, for the interview framing: [Design a Rate Limiter](https://www.youtube.com/watch?v=VzW41m4USGs) by Jordan has no life, about 27 minutes. The distributed version, where the limiter has to work across many servers.

### The bouncer at the door, and why a fast no is the whole point (12 min)

Picture the limiter as one small piece of code that sits before everything expensive. A request arrives, the limiter checks "is this client within its allowance right now", and either waves it through to your real handlers or returns 429 immediately. That is all. But where it sits is the whole value. It is in front of the database, in front of the auth service, in front of the LLM that costs you money per token. So when a client misbehaves, or a bug in their app starts hammering you, or tatkal opens and a million people arrive at once, the limiter absorbs it with a cheap rejection instead of letting it turn into a pile of slow, expensive work that knocks your backend over.

Notice the word cheap. The reject path has to be the fast path. A limiter that does a database lookup, authenticates the user, and renders half a response before deciding to reject is worse than useless under a flood: it becomes the overloaded component itself. This is the same lesson as Day 27's load shedding, pointed at the front door. Say no early, say no cheaply, and spend your resources on the requests you are actually going to serve.

And say no politely. A 429 with a Retry-After header tells a well-behaved client exactly how long to back off. Without it, the client cannot tell a rejection from a timeout, so it retries blindly, usually at once, and often all the clients retry in the same instant because they all failed in the same instant. That is a retry storm, and it is how a brief blip becomes a sustained outage. The limiter's job is not just to block, it is to shape the client's behaviour on the way out.

### The token bucket, and why a little burst is a feature (14 min)

The token bucket is the one you will reach for most, so understand it in your bones. Picture a bucket that holds up to C tokens. A tap drips new tokens in at R per second, and the bucket never overflows past C. Every request must take one token to proceed; if the bucket is empty, the request is rejected. That is the entire algorithm, and two numbers define its personality.

The refill rate R is the sustained throughput. A client hammering you forever can only go as fast as the tap refills, because every request it makes has to wait for a token to drip. So in the long run, the token bucket meters every client down to R, no matter how hard they push.

The capacity C is the burst allowance. If a client has been quiet for a while, the bucket fills up to C, and then it can spend all C tokens in one instant: a burst of C requests straight through. This is not a bug, it is the point. Real traffic is bursty. A user opens your app and it fires twelve requests to paint the screen. A nightly job wakes up and syncs a batch. You want to allow those friendly bursts, up to a sensible ceiling, and only clamp down on sustained abuse. The token bucket does exactly that: burst up to C, then settle to R.

In the lab you will fire 50 requests at a bucket that holds 20, all in the same instant, and watch exactly 20 get through. A full bucket is the most you can ever spend at once. Then you will offer a sustained 30 requests per second at a bucket that refills at 10, and watch the long-run accept rate settle right onto 10 per second. Burst capped, then metered. Those two numbers, C and R, are the whole design.

### The fixed-window trap, and the sliding window that fixes it (12 min)

Now the one almost everyone writes first, and the reason today exists. The fixed-window counter is dead simple: keep a count per clock-aligned window, "100 requests this minute", and reset the count to zero when the minute ticks over. It is one integer and one comparison. It is also quietly broken at the edges.

Here is the trap. The limit is 100 per minute. A client sends 100 requests in the last second of 11:59, filling that minute's window. The clock ticks to 12:00, the counter resets to zero, and the client immediately sends 100 more. Two hundred requests in about two seconds, through a limiter that promised a hundred a minute. For that one second straddling the boundary, your backend sees double the load you sized it for. Nobody broke the rules. The rules had a seam, and the client sat right on it.

The fix is to stop counting in clock-aligned boxes and start counting the trailing window. A sliding-window limiter asks "how many requests has this client made in the last 60 seconds, measured from right now", not "how many this calendar minute". There is no boundary to sit on, because the window moves with the request. The exact version keeps the timestamps of recent requests and drops the ones that have aged out; the clever production version (the Cloudflare post) approximates it by weighting the current and previous fixed windows, so it keeps the cheapness and loses the seam. In the lab you will send the same boundary-straddling stream through both and watch the fixed window pass 200 while the sliding window holds the line at 100.

### Leaky bucket versus token bucket: burst or smooth (12 min)

The last choice. The token bucket and the leaky bucket sound similar and are often confused, but they shape traffic in opposite ways, and the difference is entirely in the output.

A token bucket, as you saw, lets bursts through. When tokens are available, requests pass the instant they arrive, so a burst in becomes a burst out. The backend feels the shape of the incoming traffic, just capped.

A leaky bucket does the opposite. Think of a real bucket with a small hole in the bottom. Requests pour in at whatever ragged pace they arrive, but they leak out of the hole at a strictly constant rate. The output is a smooth, even stream no matter how bursty the input was. If requests arrive faster than the hole can drain, they wait in the bucket, and if the bucket is full, they overflow and are dropped.

So which do you want? Reach for the token bucket when a burst is fine and you mostly care about the sustained rate: ordinary API traffic, where letting a user's app fire its opening dozen requests is good behaviour, not abuse. Reach for the leaky bucket when the thing behind you is fragile and must never see a spike: a legacy database that tips over above some writes per second, a third-party API with a hard concurrency cap, a payment processor that charges you for bursts. The leaky bucket guarantees the downstream never sees more than the drain rate, and it pays for that guarantee in queueing delay. In the lab you will feed the same bursty input to both and watch the token bucket spike at every burst while the leaky bucket drips a flat line, with the delay showing up as the honest cost.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Then copy your answers into [`notes/day-45-drills.md`](../notes/day-45-drills.md). About 8 minutes each.

D1. A token bucket refills at 100 tokens per second with a capacity of 500, and starts full. What is the largest burst it can pass in one instant? What steady rate does it allow a client that hammers it forever? And in one line each, what does the capacity control and what does the refill rate control?

D2. A fixed-window limiter allows 60 requests per 60-second window. If a client times it right, what is the most it can get through in a single 60-second stretch of wall-clock time, and why? What is the one change a sliding-window counter makes to stop that?

D3. You feed the same bursty input into a token bucket and a leaky bucket. Which one lets a burst reach the backend, and which smooths the output to a constant rate? What does the smoothing one pay for that? And which would you put in front of a fragile legacy database that falls over above 50 writes per second?

D4. A client is over its limit. Why does returning 429 with a Retry-After header beat both silently dropping the request and letting it through? What does a well-behaved client do with Retry-After? And why is a limiter that does its expensive work before rejecting self-defeating under load?

D5. You run a per-process, in-memory token bucket on each of 10 load-balanced servers, each set to 100 requests per second. Roughly what global limit does a client actually hit, and why? What is the usual fix, and what new failure mode does that fix introduce?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-45-rate-limiting/rate_limiting.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-45-rate-limiting/rate_limiting.py).

It is in three parts, all pure simulation on a virtual clock, so nothing sleeps and the whole thing runs in well under a second. Part 1 builds a token bucket, fires an instant burst at it, then a sustained overload, and watches it cap the burst and settle to the refill rate. Part 2 builds a fixed-window counter and a sliding-window counter and sends the same boundary-straddling stream through both. Part 3 feeds the same bursty input to a token bucket and a leaky bucket and compares the shape of the output.

Standard library only, deterministic (the one random stream is seeded), no threads, no files to clean up.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. A token bucket refills at 10/s, capacity 20, starts full. An instant burst of 50 requests all arrive at the same moment. How many get in?
- P2. The same bucket, now a sustained overload of about 30 requests per second for a full minute (three times the refill rate). What is the long-run accept rate in requests per second?
- P3. A fixed-window counter, limit 100 per 60-second window. A client sends 100 just before the boundary and 100 just after. How many are accepted across the boundary in total?
- P4. The exact same stream through a sliding-window counter that counts the trailing 60 seconds. How many now?
- P5. A leaky bucket draining at 10/s, fed a bursty input. What is its output rate in requests per second?
- P6. The token bucket fed that same bursty input. What is the most it lets out in any single one-second window?

P3 and P4 are the pair to feel in your gut before you run. Write down two numbers. The gap between them is the whole trap.

### Fill in the TODOs

1. TODO 1 is the token bucket itself: drip new tokens in (capped at the capacity), then take one if you can. The refill-then-take that is the entire algorithm.
2. TODO 2 is the fixed window's integer boundary, `int(now // window)`. The one line that makes the trap possible, because it resets the counter on the clock.
3. TODO 3 is the sliding window's eviction test: is this past request older than the trailing window, so it no longer counts? The one line that closes the trap.
4. TODO 4 is the leaky bucket's emit schedule: a request leaves no sooner than now and no sooner than the previous drip plus one interval. The line that forces a constant output rate.

```bash
cd labs/day-45-rate-limiting
python3 rate_limiting.py
```

### What you're going to discover

Part 1 is the token bucket behaving exactly as advertised. The instant burst of 50 gets capped at 20, the bucket size, because a full bucket is all you can spend at once. Then the sustained 3x overload settles to an accept rate right around 10 per second, the refill rate, because once the opening burst is spent, every further request has to wait for a token to drip. Burst allowance, then steady meter. Two numbers, C and R, doing their two jobs.

Part 2 is the trap sprung and then fixed. The fixed window passes 200 requests across the boundary, a clean 2x the stated limit, because the counter reset on the clock tick and the client sat right on the seam. The sliding window, given the identical stream, holds the line at 100, because the second batch still sees the first batch inside its trailing 60 seconds and rejects the excess. Same traffic, one honest limiter and one with a hole.

Part 3 is the two buckets shaping the same storm differently. The token bucket's output spikes to 20 at every input burst and sits at zero in between: bursty in, bursty out, just capped. The leaky bucket's output is a flat 10 per second, every second, no matter how clumpy the input was, and the cost shows up as queueing delay (the last request in a burst waits several seconds) and some overflow drops. Smooth output, paid for in latency.

### Traps ⚠️

- The token bucket starts full on purpose, so the very first burst is allowed. That is realistic (a fresh client has its full allowance) and it is why the instant burst accepts exactly the capacity. If you start it empty you will measure a different, more confusing number.
- The leaky bucket's per-second output bins can look like they wobble by one at the edges. That is pure floating-point drift from adding 0.1 many times, not a real wobble. The lab measures the true rate from the spacing of emissions, which comes out exactly 10 per second. Trust the spacing, not the bin edges.
- The fixed-window 2x is the clean, worst-case number from a client timing the boundary perfectly. Real clients rarely hit it dead on, so in production you see bursts somewhere between 1x and 2x. The point is that the ceiling is 2x, not that every minute doubles.
- Do not confuse this with Day 27. That was an internal queue pushing back on your own producer. This is an edge limiter rejecting outside requests. If you catch yourself reaching for a bounded `queue.Queue`, you are solving the wrong day.

### Deliverable

[`labs/day-45-rate-limiting/RESULTS.md`](../labs/day-45-rate-limiting/RESULTS.md) has a skeleton. Paste the output, and write one line: how many did the fixed window let through at the boundary versus the sliding window, and would you put a token bucket or a leaky bucket in front of a database that falls over above 50 writes per second, and why?

---

## Block 4: write (30 min) 📣

Your angle today is the hidden bug: "I wrote the rate limiter almost everyone writes first, the fixed-window counter, and measured a client pushing 200 requests through a 100-per-minute limit by sitting on the window boundary. One line, counting the trailing window instead of the clock, closes the hole." The fixed-versus-sliding scoreboard, 200 against 100, is the screenshot. Then the one-liner that sticks: token bucket allows friendly bursts, leaky bucket smooths output for a fragile downstream.

Example posts are on the [Day 45 posts](../shares/day-45-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the fixed-window boundary number you measured (how far above the limit it went), and one thing you still cannot explain.

Day 46 is the noisy neighbour: one greedy tenant degrading everyone else on shared infrastructure, and the per-tenant quotas and fairness that stop it. Today you learned to limit a single client at the door. Tomorrow you learn to keep one loud client from eating the share meant for everyone else inside the house.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Largest instant burst is 500, the capacity, because a full bucket is the most tokens you can spend at once. The steady rate for a client hammering forever is 100 per second, the refill rate, because once the bucket is drained every further request has to wait for a token to drip in. The capacity controls the burst allowance, how far above the steady rate a quiet client may briefly surge. The refill rate controls the sustained throughput, the long-run ceiling no client can beat. Tank size and tap speed, and they are independent knobs.

D2. The most a well-timed client gets through in a 60-second wall-clock stretch is 120, which is 2x the limit. Send 60 in the last moment of one window and 60 in the first moment of the next; both land inside a single trailing minute that straddles the boundary. It happens because the fixed window resets its counter on the clock tick regardless of recent history, so a trailing-minute view can contain two full windows' worth of traffic. The sliding-window fix is to count requests in the trailing 60 seconds ending now (drop any timestamp older than now minus 60) instead of resetting a counter on the clock boundary. There is no fixed seam to sit on because the window moves with each request.

D3. The token bucket lets a burst reach the backend: when it has tokens saved up, requests pass the instant they arrive, so a burst in is a burst out. The leaky bucket smooths the output to a constant rate, because requests leave through a fixed-rate hole regardless of how they arrived. The smoothing one pays in queueing delay (requests wait their turn in the bucket) and in dropped requests when the bucket overflows. For a fragile legacy database that falls over above 50 writes per second, use a leaky bucket draining at or below 50 per second, because it guarantees the database never sees more than the drain rate even under a spike. A token bucket would let a saved-up burst through and tip the database over, which is exactly what you are trying to prevent.

D4. A 429 with Retry-After beats a silent drop because a dropped request is indistinguishable from a slow one, so the client retries blindly and usually immediately, piling more load on; the header tells it precisely how long to wait. It beats letting the request through because letting it through defeats the limiter and overloads the backend you were protecting. A well-behaved client reads Retry-After and backs off for that long, ideally with a little jitter so that many clients that failed together do not all retry in the same instant. A limiter that does expensive work (database lookups, auth, rendering) before rejecting is self-defeating under load because the reject path is the hot path during a flood, and if rejecting is expensive the limiter itself becomes the overloaded component. Say no cheaply and early, or you have not really said no.

D5. A client actually hits roughly 1000 requests per second, about 10x the intended 100, because each server keeps its own in-memory bucket and knows nothing about the other nine, while the load balancer spreads the client's traffic across all ten. Ten independent 100-per-second buckets add up to 1000. The usual fix is a shared counter in a central store such as Redis that every server reads and updates, so the limit is enforced globally rather than per process. The new failure mode is that the central store is now a hot dependency on every request's critical path: it can become a bottleneck or a single point of failure, and when it is slow or down you must choose between fail-open (let traffic through and lose the limit) and fail-closed (reject and lose availability). Teams often soften this with local buckets reconciled periodically against the shared store, trading a little exactness for not round-tripping to Redis on every single request.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-45-rate-limiting/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-45-rate-limiting/solution.py).

TODO 1, the token bucket: drip new tokens in, capped at the capacity, then take one if there is a whole token to take.

```python
tokens = min(capacity, tokens + elapsed * rate)
if tokens >= 1.0:
    return tokens - 1.0, True
return tokens, False
```

TODO 2, the fixed window's integer boundary, the one line that makes the trap possible:

```python
return int(now // window)
```

TODO 3, the sliding window's eviction test, the one line that closes the trap:

```python
return timestamp <= now - window
```

TODO 4, the leaky bucket's emit schedule, which forces a constant output rate:

```python
return max(now, next_emit)
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3.

```
==============================================================================
Part 1: the token bucket. Allow a burst up to the bucket size, then
        settle to the refill rate.
==============================================================================
  bucket: 10 tokens/s refill, capacity 20, starts full.

  instant burst of 50 requests at the same moment:
    accepted 20, rejected 30
  The burst is capped at the bucket size (20). A full bucket is
  the most you can ever spend at once. That is the burst allowance.

  sustained overload: 1809 requests offered over 60s (30.1/s, 3.0x the rate):
    accepted 619, long-run accept rate = 10.3/s
    steady-state rate after warm-up = 10.0/s
  Offer three times as much and you still get through at the refill
  rate (10/s). The bucket caps the burst, then meters the rest.

==============================================================================
Part 2: the fixed-window trap. N per minute, reset on the minute, lets
        a client push 2N across the boundary.
==============================================================================
  limit 100 per 60s window. A client sends 100 just before
  the boundary (t~59) and 100 just after (t~60).

  fixed window:   accepted 200 across the boundary (2x the limit)
                  most in any trailing 60s = 200
  Both batches pass: the first fills window 0, then the counter resets
  on the boundary and the second fills window 1. 200 requests in about
  two seconds, through a limiter that promised 100 a minute.

  sliding window: accepted 100 across the boundary (1x the limit)
                  most in any trailing 60s = 100
  The second batch still sees the first batch inside its trailing
  60s, so the counter is already full and the excess is rejected.
  Counting the trailing window instead of a fixed box closes the trap.

==============================================================================
Part 3: leaky bucket vs token bucket. Same bursty input, very different
        output.
==============================================================================
  input: 200 requests in 5 bursts of 40, at t = 0, 3, 6, 9, 12.

  token bucket output per second (bin -> count):
    0:20 1:0 2:0 3:20 4:0 5:0 6:20 7:0 8:0 9:20 10:0 11:0 12:20 13:0 14:0 15:0 16:0 17:0 18:0 19:0
    peak second = 20 (a burst of up to the bucket size gets out)
    accepted 100 of 200, rejected on the spot.

  leaky bucket output per second (bin -> count):
    0:10 1:10 2:10 3:10 4:10 5:10 6:10 7:10 8:10 9:10 10:10 11:10 12:10 13:10 14:10 15:10 16:1 17:0 18:0 19:0
    steady output rate = 10.0/s (the constant leak rate, 10/s)
    emitted 161 of 200, overflowed 39, worst wait 4.0s.

  The token bucket lets bursts straight out: spikes at each input
  burst, nothing in between. The leaky bucket holds them and drips a
  flat stream, paying for it in queueing delay. Use leaky to shield a
  fragile downstream, token when friendly bursts are fine.

==============================================================================
Scoreboard
==============================================================================
  P1 token burst accepted            you =   20.0   actual =    20.0        close enough
  P2 token sustained rate            you =   10.0   actual =    10.3 /s       close enough
  P3 fixed-window boundary           you =  200.0   actual =   200.0        close enough
  P4 sliding-window boundary         you =  100.0   actual =   100.0        close enough
  P5 leaky output rate               you =   10.0   actual =    10.0 /s       close enough
  P6 token peak output               you =   20.0   actual =    20.0        close enough

==============================================================================
The number to carry
==============================================================================
  The fixed window let 200 requests through a '100 per minute'
  limit across one boundary, about 2x, because it resets on the clock.
  The sliding window held the same stream to 100. The token bucket
  caps a burst at the bucket size (20) and then meters at the refill
  rate; the leaky bucket emits a flat 10/s no matter the input.
  Same job, 'who gets in', three different shapes of yes and no.
```

Part 1 is the token bucket showing its two numbers at work. Fifty requests arrive in the same instant and exactly 20 get in, because the bucket holds 20 and no time has passed for it to refill: a full bucket is your whole burst allowance and no more. Then a sustained flood of three times the refill rate settles to an accept rate of about 10 per second, which is the refill rate, because after the opening burst drains, every request waits on a dripping token. Capacity sets the burst, refill rate sets the long-run throughput, and they are independent.

Part 2 is the trap and the fix side by side. The fixed window let 200 through at the boundary, a clean 2x, purely because it resets the counter when the clock ticks and the client sat on the seam. The sliding window, given the identical stream, held the line at 100, because the second batch still falls inside the trailing 60 seconds that contains the first, so the counter is already full. One line of difference, counting the trailing window instead of the clock box, and the hole is gone.

Part 3 is the two buckets shaping the same storm. The token bucket's output is spiky, 20 at each input burst and nothing in between, because it passes bursts straight through up to the cap. The leaky bucket's output is a flat 10 per second for every active second, no matter how clumpy the input, because it drains through a fixed-rate hole. The smoothing is not free: 39 requests overflowed and the worst-case wait was 4 seconds. That latency is the price of protecting a fragile downstream, and it is exactly why you choose a token bucket when bursts are fine and a leaky bucket when they are not.

The one line to carry out of today: a rate limiter is a choice, not a default. Fixed versus sliding window decides whether the boundary is honest, and token versus leaky bucket decides whether you allow bursts or smooth them away. Pick on purpose, because the easy default has a 2x hole in it.

</details>
