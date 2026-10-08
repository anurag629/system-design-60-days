---
title: "Day 20: the CDN and cache invalidation"
parent: "Week 3: caching and the CDN"
nav_order: 6
has_children: true
---

# Day 20
## The CDN, the 304, and serving stale on purpose 🌍

Today's one idea: a CDN is just a cache that lives close to your users, and the whole art of running one is deciding how long a copy may be trusted and what to do the moment it goes stale. You have three moves, and only three. Serve the copy because it is still fresh. Ask the origin "has this changed?" and let it answer cheaply with a 304. Or, the clever one, hand over a slightly old copy right now and quietly fetch a fresh one behind the user's back. Today you build all three on your own laptop and measure what each one costs.

All week the same trick has repeated at every layer. RAM caches disk, Redis caches the database. Today we go one hop further out, past your own servers, to the edge. And we meet the thing that makes caching genuinely hard: a copy can go stale, and deciding what to do about that is the part everyone gets wrong.

---

## Before you start ⏪

You need the shape of the week in your head. Day 15 gave you cache-aside and the idea that a cache is a second copy of the truth. Day 17 was the stampede, ten thousand requests missing the same key at the same instant. Today's part 3 is that same stampede wearing a CDN costume, so if day 17 is fresh you will see it coming. Day 2's comfort with running a Python script is all the setup you need. The lab uses only the standard library, real HTTP and real threads, nothing to install.

This is the last teaching day of the week. Day 21 is a design day where caching is the star, so today is where the CDN pieces click into place.

---

## Words you will meet today 📖

A CDN, content delivery network, is a fleet of caching servers spread around the world so that a user in Pune talks to a machine in Mumbai instead of one in Virginia. Each of those machines is an edge server, or a POP (point of presence). The thing behind all of them, the one source of truth, is the origin.

Fresh and stale are the two states of a cached copy. A copy is fresh while it is still inside its max-age, the number of seconds the origin said it may be trusted. Once that time passes, the copy is stale, which does not mean wrong, only that the cache is no longer sure.

Cache-Control is the HTTP response header where the origin writes the rules, most importantly max-age. It is the origin telling every cache downstream "you may reuse this for N seconds without asking me again."

An ETag is a short fingerprint of a response body, something like "9f3c2a-v1". If the body changes, the ETag changes. It is how a cache and an origin agree on whether two copies are the same without shipping the whole body.

A conditional request is a request that carries a condition, here If-None-Match with the ETag the cache already holds. It means "only send me the body if your version no longer matches mine."

A 304 Not Modified is the origin's reply to a conditional request when nothing has changed. No body, just headers. It is the cheap answer that makes revalidation worth doing.

Revalidation is the act of checking a stale copy with the origin. Blocking revalidation makes the request that found the copy stale wait for that check. Stale-while-revalidate does not: it serves the stale copy at once and refreshes in the background.

A purge, or invalidation, is you telling the CDN to forget a cached copy right now, before its max-age runs out. It is the emergency brake, and as you will see, it is less reliable than simply never caching the wrong thing in the first place.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these:
- [MDN: HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching). The clearest plain reference for Cache-Control, max-age, freshness and revalidation. If you read one thing, read this, slowly.
- [MDN: HTTP conditional requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Conditional_requests). The ETag, If-None-Match and 304 story, which is the heart of part 2.
- [Cache-Control for Civilians](https://csswizardry.com/2019/03/cache-control-for-civilians/) by Harry Roberts. A warm, practical walk through the directives you actually use, including why you fingerprint assets and cache them forever.

Watch, after the lab:
- [What Is A CDN? How Does It Work?](https://www.youtube.com/watch?v=RI9np1LWzqw) by ByteByteGo, about 4 minutes. Tight picture of the edge-and-origin shape.
- [HTTP Caching with E-Tags, Explained by Example](https://www.youtube.com/watch?v=TgZnpp5wJWU) by Hussein Nasser, about 17 minutes. He walks a real request and watches the 304 come back, which is exactly today's part 2.

### What a CDN actually is (10 min)

Picture the sweet shop near your house during Diwali week. The halwai could make every box of kaju katli to order, but at that volume nobody would ever get served. So he keeps trays out front, freshly made, and most customers take what is already on the tray. Only when a tray runs low does anyone go back to the kitchen. The tray is a cache. The kitchen is the origin.

A CDN is that tray, placed in dozens of cities. Your origin server might sit in one data centre, but the CDN keeps copies of your images, your CSS, your JSON, even whole pages, on edge servers close to where people actually are. A user's request hits the nearest edge, and most of the time the edge answers from its own copy without ever bothering your origin. Your origin stops being the thing every single request touches and becomes the thing the edges occasionally check with. That is the whole value, and in the lab you watch 120 requests collapse to 12 origin hits because of it.

The catch is the one we have circled all week. The tray out front might be yesterday's batch. How does the edge know when its copy is too old to trust? That is what the rest of today is about.

### Freshness: the clock the origin sets (12 min)

When the origin sends a response, it stamps it with a rule: Cache-Control: max-age=600, say, meaning "any cache may reuse this for 600 seconds." The edge stores the copy and starts a clock. While the clock is under 600 seconds, the copy is fresh, and the edge serves it with zero contact with the origin. This is the fast, cheap, happy path, and it is where a good CDN spends almost all of its time.

Here is the piece of arithmetic that matters, and it is drill one. Suppose a page is requested a thousand times a second and you cache it with max-age of ten seconds at a single shared edge. How often does the origin get hit? Not a thousand times a second. Once every ten seconds. The first request after each expiry refills the copy, and the other nine thousand nine hundred and ninety nine are served from the edge. Your origin load just fell by a factor of ten thousand, and all you did was promise to be at most ten seconds out of date.

That trade, a little staleness for an enormous drop in load, is the entire reason CDNs exist. The number you choose for max-age is you deciding, per resource, how stale is acceptable. A logo can be a year. A news homepage might be ten seconds. A stock ticker, zero. There is no universally right value, only the right value for how fast that particular thing actually changes.

### The conditional request, and why a 304 is a gift (14 min)

So the clock runs out and the copy is stale. The lazy thing would be to throw it away and download the whole body again. But think about it: most of the time nothing has actually changed. The logo is the same logo. Re-downloading 500 KB to discover it is byte-for-byte identical is a waste of everyone's time.

This is what the ETag is for. When the origin first sent the body, it attached a fingerprint, the ETag. Now, instead of a blind re-fetch, the edge sends a conditional request: GET the resource, If-None-Match: "9f3c2a-v1". It is asking "I already have the version tagged 9f3c2a, is that still current?" If it is, the origin replies 304 Not Modified, with no body at all, just headers. The edge sees the 304, resets its freshness clock, and keeps serving the copy it already had.

Be precise about what the 304 saves and what it does not, because that is drill two. It saves the body on the wire, the 500 KB you did not have to send. It saves the origin the work of regenerating that body. What it does not save is the round trip. The edge still had to travel to the origin, ask the question, and wait for the answer. On a CDN where the origin is in another continent, that round trip can be a hundred milliseconds or more, even for a tiny 304. So the real win of caching is never "cheap revalidation." It is that most requests never revalidate at all, because they land while the copy is still fresh. The 304 just makes the occasional check less painful than a full re-fetch. In the lab, a full 200 costs 60 ms and a 304 costs 30 ms, and you count how many of each you got.

### Stale-while-revalidate: serve the tray, fry the next batch (14 min)

Now the clever part, and the one that genuinely surprised me the first time I measured it.

Blocking revalidation has an ugly edge. The copy goes stale, and the very next request that arrives is the one that has to go and check with the origin. Everyone before it was served instantly from the edge in about a millisecond. This one unlucky person, who did nothing different, suddenly waits the full origin round trip while the edge revalidates. Their request was the one holding the short straw when the clock struck. In the lab you watch the worst request jump to 38 ms while the median stays at zero.

Stale-while-revalidate removes that unfairness. The rule, written as Cache-Control: max-age=60, stale-while-revalidate=600, says: for the first 60 seconds the copy is fresh, serve it. For the next 600 seconds it is stale but still serveable, so hand it over immediately AND kick off a background refresh. Nobody waits for the origin. The slightly old copy goes out at edge speed, and the fresh copy quietly arrives a moment later for the next person.

Back to the sweet shop. Blocking revalidation is the halwai locking the counter the instant a tray empties and making the next customer stand there while he fries a fresh batch. Stale-while-revalidate is him handing over the slightly-less-fresh piece from the back of the tray with a smile, and starting the next batch so the following customer is covered. Same kitchen, same work, but one customer is left standing and the other is not.

And this is where day 17 comes back. Imagine the copy is ferociously hot, a viral page taking ten thousand requests a second, and it expires. Under naive blocking revalidation, all ten thousand simultaneously find it stale and all ten thousand stampede the origin at once. That is the tatkal rush at ten in the morning, every booking hitting IRCTC in the same instant. Two things save you. Request coalescing lets only one request through to the origin and makes the rest wait for that single result, which protects the origin but still makes those requests wait. Stale-while-revalidate serves all ten thousand the old copy instantly and refreshes once in the background, which protects the origin AND keeps everyone fast. Real CDNs do both. The lab's part 3 shows the latency half of this: same origin load either way, wildly different experience for the user.

### Invalidation: the hard problem, and the honest way around it (6 min)

You shipped a broken stylesheet with max-age of one day. Every edge and every browser now holds it, happily, for the next twenty four hours. What do you do?

Option one is a purge: you tell the CDN to drop that copy everywhere, right now. It works, mostly, but purges take time to propagate across every POP, they are not always perfectly reliable at global scale, and crucially they do nothing for the copy already sitting in a user's browser. That browser was told one day, and it will wait one day.

Option two is the honest trick the whole industry uses: do not invalidate, rename. Serve the file from a fingerprinted URL like app.9f3c2a.css, where the fingerprint is a hash of the contents. When the file changes, its URL changes, so every cache treats it as a brand new thing and fetches it fresh at once. There is nothing stale to purge, because the old URL is simply never requested again. This is why the standard pattern is to fingerprint your static assets and cache them for a year as immutable, while serving your index.html with no-cache. The HTML is the one small thing that must always be current, and its only job is to point at the latest fingerprinted asset URLs. Long caching and instant deploys, at the same time, with no purge button in sight. That is drill four, and it is one of those ideas that quietly makes your whole deployment story simpler.

The old joke says the two hard problems in computing are cache invalidation and naming things. The fingerprint trick is lovely precisely because it turns the first hard problem into the second one.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-20-drills.md`](../notes/day-20-drills.md).

D1. A resource is requested 1,000 times a second. You put a CDN in front with Cache-Control max-age=10s. Treating one edge as a single shared cache, how many requests a second reach the origin? Now the CDN has 50 edge locations that do not share a cache. How many origin requests a second now, and what does that tell you about content on a big CDN?

D2. A 500 KB image with max-age=60 is requested again 5 minutes after it was stored, and the content has not changed. Compare a plain re-fetch against a conditional request with If-None-Match. What does the resulting 304 save you, in bytes and in origin work, and what does it not save?

D3. A response carries Cache-Control: max-age=60, stale-while-revalidate=600. For a request that arrives when the stored copy is 30s old, 120s old, and 700s old: in each case, is the copy served from the edge or does someone wait for the origin, and is a background refresh triggered?

D4. You shipped a broken app.css with max-age=86400 and users are stuck with it for a day. Compare two fixes: purge the file at the CDN, versus serve it from a new fingerprinted URL like app.9f3c2a.css. Which is more reliable and why? And why is the common rule "fingerprint static assets with a one year max-age, but serve index.html with no-cache"?

D5. One very hot page expires at the edge at the exact moment 10,000 requests a second are hitting it. Under blocking revalidation with no coalescing, what does the origin feel? Explain how request coalescing and stale-while-revalidate each prevent that, and which one keeps user latency flat.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-20-cdn/http_cache.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-20-cdn/http_cache.py).

It is a real origin server in its own thread, with real Cache-Control and ETag headers and real 304 responses, and a tiny edge cache in front of it that the client talks to. Standard library only, no files written to disk, and it runs in about 15 seconds.

It is in three parts. Part 1 sends the same 120 requests for 3 resources with no cache at all, so every one reaches the origin, and times it. Part 2 puts a TTL edge cache in front: it serves the stored copy while fresh, and when it goes stale it revalidates with a conditional request so the origin can answer 304. Part 3 takes one hot key and reads it over and over as it keeps expiring, once with blocking revalidation and once with stale-while-revalidate, and compares the user-facing latency.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The workload is 120 requests (3 resources, 4 rounds, 10 reads each). With no cache, how many reach the origin?
- P2. The same 120 requests behind a TTL edge cache (max-age 0.3s, rounds spaced so the copy goes stale once between each). How many reach the origin now?
- P3. During that TTL run, how many of the origin trips come back as a cheap 304?
- P4. The one request that triggers a blocking revalidation waits for the origin while everyone else is served from the edge in about a millisecond. About how many milliseconds does that one request wait?

P2 is the one to feel before you run it. Write a number. The gap between it and P1 is the whole reason the CDN industry exists.

### Fill in the TODOs

1. TODO 1 is the freshness check: a copy is fresh while less than max-age has passed since you stored it. This one line is the TTL.
2. TODO 2 is the conditional request header, If-None-Match with the ETag you already hold. This is what lets the origin answer 304.
3. TODO 3 is what you do on a 304: keep the body you already have and slide its freshness clock forward, so it counts as fresh again.
4. TODO 4 is the stale-while-revalidate decision: when the copy is past fresh but still inside the stale window, you are allowed to serve it now and refresh behind the scenes.

```bash
cd labs/day-20-cdn
python3 http_cache.py
```

The lab self-checks the four TODOs before it runs any load and tells you exactly which one is missing, so you can never get stuck watching it hang.

### What you're going to discover

Part 1 is the baseline. No copy is kept anywhere, so all 120 requests walk to the origin and each pays the full 60 ms of work. Average latency sits up near 65 ms. This is the world without a CDN.

Part 2 is the collapse. The same 120 requests, but now only 12 reach the origin, a tenfold cut, and 9 of those 12 are cheap 304s because nothing actually changed between rounds. Average latency drops from about 65 ms to about 4 ms, because the overwhelming majority of requests are served from the edge in a flash. You get to watch the conditional request do its job: a body only when the content truly changed, a 304 otherwise.

Part 3 is the one to sit with. Blocking revalidation and stale-while-revalidate hit the origin the same number of times, so stale-while-revalidate is not cheating anyone out of freshness. The difference is who waits. Under blocking, the worst request spikes to around 38 ms, the unlucky one that arrived the instant the copy expired. Under stale-while-revalidate, the worst request is about 1 ms, because nobody ever waits for the origin. Same work, same staleness budget, one design leaves a user standing at the counter and the other does not.

### Traps ⚠️

- If your part 2 origin hits are not 12, check that the between-round sleep is actually longer than max-age. The rounds are deliberately spaced to expire once between each. If a round takes longer than max-age on a very slow machine, you will see a few extra revalidations. The shape still holds: a dozen-ish origin hits against 120.
- The stale-while-revalidate worst case is a sub-millisecond number, so the blocking-over-swr ratio printed in part 3 bounces around a lot run to run, anywhere from fifteen to seventy. Do not chase that ratio. The number that is stable and that matters is the blocking spike itself, around 38 ms, against a flat sub-millisecond stale-while-revalidate line.
- A 304 is not free. It still costs a full round trip to the origin, 30 ms in the lab. If you expected revalidation to be nearly instant, that is the lesson: the cheap part is the body you did not send, not the trip you did not avoid.
- Both part 3 policies make the same number of origin trips. If you see stale-while-revalidate making far fewer, your background refresh is not firing. If you see it making far more, you are spawning a refresh on every stale read instead of coalescing to one.

### Deliverable

[`labs/day-20-cdn/RESULTS.md`](../labs/day-20-cdn/RESULTS.md) has a skeleton. Paste the output, and write one line: origin hits fell from how many to how many, and why did stale-while-revalidate keep the worst request flat when blocking did not?

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise: "I built a tiny CDN on my laptop. The same 120 requests went from 120 origin hits to 12, and stale-while-revalidate kept the worst request at 1 ms while blocking revalidation spiked to 38 ms. Same origin load, different victim." The scoreboard is the screenshot.

Example posts are on the [Day 20 posts](../shares/day-20-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the origin-hit drop you measured with the TTL cache, and one thing you still cannot explain.

Day 21 closes the week with a design, something like a news feed or a rate limiter where caching carries the load, timed and then retro'd. Everything from day 15 to today comes together there. Today you learned the outermost cache, the one closest to the user, and the three moves it can make when a copy goes stale.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. With one shared edge cache, the origin is hit once per max-age window, because the first request after each expiry refills the copy and the rest are served from the edge. That is one request every 10 seconds, about 0.1 a second, down from 1,000. With 50 POPs that do not share a cache, each POP independently refills once per window, so the origin sees 50 requests every 10 seconds, about 5 a second. Still tiny against 1,000, but 50 times more than a single cache. The lesson: origin load on a big CDN scales roughly with the number of POPs divided by max-age, not with user traffic. And content that is not hot enough to be re-requested within max-age at each POP will keep expiring before it is reused, so long-tail content has a much worse hit rate than you would guess. This is why CDNs add tiered or shield caching, a middle layer the POPs share.

D2. A plain re-fetch sends the full 500 KB body down the wire and makes the origin produce or read that body. A conditional request with If-None-Match sends the ETag, and since nothing changed the origin replies 304 Not Modified with headers only, a few hundred bytes. The 304 saves the 500 KB transfer and the origin's work of regenerating the body. It does not save the round trip: the edge still had to go to the origin and wait for the answer, and the origin still had to look up the current ETag to compare. So revalidation is cheaper than a re-fetch, but it is not cheaper than a fresh hit that never left the edge.

D3. At 30s old the copy is inside max-age, so it is fresh: served from the edge instantly, no origin contact, no refresh. At 120s old it is past max-age (60s) but inside max-age plus the stale window (60 + 600 = 660s), so it is stale but serveable: the edge hands over the old copy instantly and triggers a background refresh, and nobody waits. At 700s old it is past 660s, beyond the stale-while-revalidate window entirely, so the copy may no longer be served stale: this request must block and revalidate with the origin, so this one waits. After it completes, the copy is fresh again.

D4. A purge tells the CDN to drop the copy everywhere now, but it propagates across POPs with some delay, is not perfectly reliable at global scale, and does nothing for the copy already cached in users' browsers, which were told to keep it for a day. The fingerprinted URL is more reliable: app.9f3c2a.css is a different URL, so every cache, edge and browser alike, treats it as a brand new resource with no stored copy and fetches it fresh immediately, while the broken old URL is simply never requested again. The rule follows from this. Fingerprinted assets can never be wrong under their URL, because any change makes a new URL, so you cache them for a year as immutable. The index.html must always reflect the latest deploy, because its job is to point at the current asset URLs, so you serve it with no-cache. You get long caching and instant deploys together.

D5. Under blocking revalidation with no coalescing, the instant the copy expires all 10,000 in-flight requests find it stale and all 10,000 go to the origin at once. The origin, which the cache was supposed to protect, gets slammed with a stampede for a single key, the tatkal rush at ten in the morning. Request coalescing fixes the origin load: only one request is allowed through to revalidate and the other 9,999 wait for that single result, so the origin sees one request, but those waiters still wait for the round trip, so their latency spikes. Stale-while-revalidate fixes both: all 10,000 are served the stale copy instantly and a single background refresh runs, so the origin sees about one request and no user waits. Coalescing protects the origin; stale-while-revalidate protects the origin and keeps user latency flat. Real CDNs combine them.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-20-cdn/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-20-cdn/solution.py).

TODO 1, the freshness check that is the whole TTL:

```python
fresh = (now - stored_at) < max_age
```

TODO 2, the conditional request header that lets the origin answer 304:

```python
headers = {"If-None-Match": etag}
```

TODO 3, what you do on a 304, keep the body and slide the freshness clock forward:

```python
new_stored_at = now
```

TODO 4, the stale-while-revalidate decision, serveable-while-stale between max-age and the end of the stale window:

```python
ok = max_age <= age < (max_age + swr_window)
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 120 requests for 3 resources.

```
==============================================================================
Part 1: no cache. Every request walks all the way to the origin.
==============================================================================
  requests sent by the client:      120
  requests that reached the origin: 120  (every single one)
  average user latency:               65.7 ms
  No copy is kept anywhere, so the client pays the full origin cost
  on every read, even for the same three resources over and over.

==============================================================================
Part 2: a TTL edge cache. Serve the stored copy until it goes stale,
        then revalidate with a conditional request (If-None-Match).
==============================================================================
  requests sent by the client:      120
  requests that reached the origin: 12
    of those, full 200 responses:   3
    of those, cheap 304 responses:  9
  average user latency:                4.2 ms
  The first read of each resource is a miss and fetches the body. After
  that, reads inside a fresh window are served from the edge for free.
  When a burst finds the copy stale, the edge asks the origin 'changed?'
  and the origin replies 304, no body, so the refresh is cheap.

==============================================================================
Part 3: one hot key, read over and over as it keeps going stale.
        Blocking revalidation vs stale-while-revalidate.
==============================================================================
  policy                      median ms   worst ms  slow reqs  origin trips
  blocking revalidation             0.0       38.0          4             5
  stale-while-revalidate            0.0        0.8          0             4
  worst-case spike, blocking / swr: 46.1x
  Both policies hit the origin about the same number of times, so SWR is
  not cheating the origin. The difference is WHO waits. Under blocking,
  the one request that finds the copy stale is stuck paying the origin
  trip while everyone else is served from the edge. Under SWR, that
  request gets the slightly old copy instantly and the refresh happens
  behind it, so the worst user latency stays flat.

==============================================================================
Scoreboard
==============================================================================
  P1 origin hits, no cache         you =   120.0   actual =    120.0        close enough
  P2 origin hits, TTL cache        you =    12.0   actual =     12.0        close enough
  P3 cheap 304 revalidations       you =     9.0   actual =      9.0        close enough
  P4 blocking spike (ms)           you =    40.0   actual =     38.0 ms       close enough

==============================================================================
The number to carry
==============================================================================
  Same 120 requests for the same 3 resources. With no cache, 120 of
  them hit the origin. With a TTL edge cache, 12: a 10x cut, and
  9 of those were cheap 304s because nothing had changed.
  Average user latency fell from 66 ms to 4 ms.
  And stale-while-revalidate kept the worst request at 1 ms while
  blocking revalidation spiked to 38 ms: 46x worse for the
  one unlucky user who happened to arrive the moment the copy expired.
```

Part 2 is the headline. The same 120 requests for the same 3 resources, and the cache cut origin hits from 120 to 12, a tenfold drop, with no change to the workload at all. Of those 12 trips, only 3 were full downloads, the first read of each resource. The other 9 were revalidations that came back 304 because nothing had changed, so the origin sent headers and no body. Average user latency fell from about 66 ms to about 4 ms, because the overwhelming majority of reads never left the edge. That is a CDN in one measurement: most requests served locally, the occasional check made cheap by the conditional request.

Part 3 is the one worth sitting with. Both policies made the same handful of origin trips, so neither is skimping on freshness. What differs is who pays. Under blocking revalidation, four requests stalled, each one the unlucky arrival that found the copy stale and had to wait the full origin trip, and the worst sat at 38 ms while everyone else was served from the edge at effectively zero. Under stale-while-revalidate, zero requests stalled: the worst case was under a millisecond, because the slightly old copy went out instantly and the refresh happened in the background. The printed blocking-over-swr ratio is large and jumpy, because the stale-while-revalidate worst case is a sub-millisecond number, so trust the absolute figures, a flat sub-millisecond line against a 38 ms spike.

The one line to carry out of today: a CDN is a cache at the edge, max-age decides how long a copy is trusted, the conditional request makes the occasional recheck cheap, and serving stale on purpose is how you keep one unlucky user from paying the origin bill for everyone else.

</details>
