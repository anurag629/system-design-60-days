---
title: "Day 51: mock, a URL shortener"
parent: "Week 8: putting it all together"
nav_order: 2
has_children: true
---

# Day 51
## Mock 1, a URL shortener, the whole shape against the clock ⏱️

Today's one idea: you run the full 45-minute shape, start to finish, on a problem you already understand, so the only new thing you are practising is the performance itself. You designed a URL shortener on Day 7. Today you do not learn it, you perform it, timed, out loud, and then you grade yourself honestly.

This is the classic opening question in real interviews, and it looks easy until you have to produce the whole thing in 45 minutes without rambling.

---

## Before you start ⏪

Yesterday's framework sheet ([`labs/day-50-framework/FRAMEWORK.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-50-framework/FRAMEWORK.md)) is on the desk next to you. Reread your Day 7 design. Have a timer. You want 45 clear minutes and nobody interrupting, because the whole point is to simulate the pressure.

---

## Words you will meet today 📖

The signal is what an interviewer is actually grading: not whether you got the one right answer, but whether you clarify, estimate, make choices with reasons, and go deep in the right place. A design has many right answers, and the signal is your reasoning.

A key generation service (KGS) is a small component whose only job is to hand out unique short codes, so your main service never has to coordinate to avoid collisions. One of the cleaner answers to "how do two servers make short codes without clashing."

A 301 is a permanent redirect (the browser caches it and may skip your server next time); a 302 is temporary (the browser comes back to you every time). The choice decides whether you can count clicks.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these two before your timed run, lightly, for the shape, not to memorise:
- [Design Bitly](https://www.hellointerview.com/learn/system-design/problem-breakdowns/bitly) from Hello Interview. A clean, honest, current walkthrough of exactly this question.
- [Design Pastebin](https://github.com/donnemartin/system-design-primer/blob/master/solutions/system_design/pastebin/README.md) from the System Design Primer. A close cousin (short link to a blob), with the estimates worked out longhand.

Watch, after your own timed run, not before:
- [System Design: URL Shortener like TinyURL, with a FAANG Senior Engineer](https://www.youtube.com/watch?v=tm-SWO9gUAU) by System Design Fight Club, about 54 minutes. Long, but it is the real thing, with the back and forth and the deep dives. Compare their moves to yours.

### The three decisions that carry this design 🎯

You do not need to read much today, because the point is to perform. But know the three hinge decisions, because the deep dive lives in them.

First, how you make the short code. Three options: hash the long URL and take the first few characters (simple, but collisions need handling), encode an auto-incrementing counter in base62 (no collisions, but the counter is a coordination point, and codes are guessable and sequential), or a key generation service that pre-generates a big pile of unique keys and hands them out (no collisions, no hot counter, a little more machinery). State the tradeoff, pick one, move on.

Second, it is wildly read heavy. A link is created once and visited thousands of times, so reads dominate by orders of magnitude. That single fact drives the whole design: cache the code-to-URL mapping hard (Day 15, Day 18), because almost every request is a read you have seen before.

Third, the redirect type decides analytics. A 301 permanent redirect lets the browser cache it, so your server may never see the second click, which is great for load and terrible for counting. A 302 sends every click back through you, which costs you the request but lets you count it. If the product sells click analytics, you are on 302, and the click counting goes through a queue (week 4) so it never slows the redirect.

---

## Block 2: drill (40 min) ✍️

Paper first, and this is your warm-up before the timed run. Write short answers into [`notes/day-51-drills.md`](../notes/day-51-drills.md). These are the sub-questions the interviewer will push on, so priming them now makes your deep dive sharp.

D1. Scale. 100 million new URLs a day, each read on average 100 times over its life. What are the writes per second and reads per second at peak (use 3 times average), and roughly how much storage over 5 years?

D2. The short code. Compare the three approaches (hash, counter in base62, key generation service). For a system making 100 million codes a day across many servers, which do you pick and why?

D3. The read path. A short link gets hammered. Walk the request from click to redirect, and say exactly where the cache sits and what your hit rate should look like.

D4. The redirect. 301 or 302, and how does that choice interact with counting clicks? If you need analytics without slowing the redirect, what carries the count?

D5. One failure. The component that generates codes dies. What happens to writes, what happens to reads, and how did you design so reads do not care?

---

## Block 3: build (100 min) 🔧

The timed run. Open [`labs/day-51-mock-url-shortener/MOCK.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-51-mock-url-shortener/MOCK.md), copy it into your fork, start a 45-minute timer, and run all six steps out loud as if an interviewer is in the room. Write as you talk. Do not pause the timer to look things up. When it rings, stop, even mid-sentence.

Then, and this is the real work, grade yourself against the rubric in the same file. Where did you ramble? Which step did you rush? Did you reach the deep dive, or did requirements eat your clock? Be brutal, because the mock is worthless if you are kind to yourself.

Then watch the video and steal two moves.

### What a strong run looks like

Requirements and scale in under 12 minutes combined. A clean API. A high-level diagram that separates the fat read path from the thin write path. A deep dive that actually picks one of the three hinge decisions and reasons through it. And a failure section that shows reads survive the write path dying. If you did that in 45 minutes, you are interview ready on this question.

### Deliverable

Your filled-in `MOCK.md`, your honest rubric score out of the six steps, and one line: the step you need to drill again.

---

## Block 4: write (30 min) 📣

Your angle is the gap between knowing a design and performing it. "I have 'known' the URL shortener for weeks. Today I ran it as a timed 45-minute mock and found out knowing and performing are completely different skills." Share the one thing that surprised you about doing it under the clock.

Example posts are on the [Day 51 posts](../shares/day-51-posts.md) page. Write yours in your own voice.

---

## End of day: log it 📝

Log the three: your rubric score, the step that ate too much clock, and the one deep-dive decision you can now explain cleanly.

Tomorrow, mock 2, a chat system like WhatsApp. Harder, because fan-out and delivery and presence are genuinely tricky, and the scale is a billion users.

---

## Solutions 🔑

Open these only after your own timed run.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Writes: 100,000,000 / 86,400 is about 1,160 per second average, times 3 for peak is about 3,500 writes per second. Reads: 100 times the writes is 10 billion reads a day, about 116,000 per second average, about 350,000 at peak. Storage: each row is maybe 500 bytes (short code, long URL, metadata), 100 million a day is about 50 GB a day, about 18 GB times 5 years... 50 GB a day times 365 times 5 is about 90 TB over 5 years. The headline: read heavy by 100 to 1, and storage grows to tens of terabytes, so you shard the store and cache the reads.

D2. Hash the URL: simple and stateless, but two URLs can collide on the same short code, so you need collision detection and a retry, which is a read before every write. Counter in base62: no collisions ever, codes are short, but the counter is a single coordination point and the codes are sequential and guessable (a problem if links are meant to be private). Key generation service: a service pre-generates millions of unique random keys into a table, marks them used as they are handed out, so each app server grabs a batch and serves from it with no per-write coordination and no collisions. For 100 million a day across many servers, the KGS is the clean answer: no hot counter, no collision retries, and you can hand out non-sequential keys. Say all three, pick the KGS, give the reason.

D3. Click comes in to the load balancer, hits a stateless app server. The server checks the cache (Redis) for the short code. On a hit, which is almost always, it returns the redirect immediately without touching the database. On a miss (a cold or rare link), it reads the database, fills the cache, and returns. Because the workload is 100 to 1 reads and links are visited repeatedly, your cache hit rate should be very high, well over 90 percent, so the database barely sees the read traffic. The cache sits right in front of the database on the read path.

D4. A 301 permanent redirect lets the browser and any proxy cache the mapping, so repeat clicks may never reach your server. Great for load, but you cannot count clicks you never see. A 302 temporary redirect routes every click through your server, so you can count, at the cost of serving every request. If the product needs analytics, use 302 and do not count synchronously: the redirect returns instantly, and a message goes onto a queue (week 4) where a consumer aggregates clicks offline. The redirect never waits for the counter.

D5. The code generator (counter or KGS) dies. Writes fail or degrade: you cannot mint new short links until it recovers, or you fail over to a standby batch of pre-generated keys (which is exactly why the KGS hands out batches, so each server has a local buffer to survive a brief outage). Reads do not care at all, because resolving an existing short code is a cache or database read that never touches the code generator. That separation, writes depend on the generator and reads do not, is the design win. An interviewer loves hearing "reads are unaffected because the read path shares nothing with the write path."

</details>

<details markdown="1">
<summary>A worked reference design</summary>

One good answer. Yours will differ, and that is fine.

Requirements. Functional: create a short URL from a long one, optionally with a custom alias and an expiry; redirect a short URL to its long one; optionally count clicks. Non-functional: extremely read heavy, very high availability for redirects (a dead redirect is a dead link everywhere), low latency on the redirect, eventual consistency is fine for click counts.

Scale, from D1: about 3,500 writes/s and 350,000 reads/s at peak, tens of TB over 5 years.

API. POST /urls {long_url, custom_alias?, expiry?} returns {short_url}. GET /{code} returns a 302 to the long URL. Entity: Url (code, long_url, created_at, expires_at, owner).

High-level design. Client to load balancer to a stateless redirect service. Reads: service checks Redis, on a miss reads the sharded database and backfills the cache, returns the redirect. Writes: a separate create service gets a key from the key generation service, writes the mapping to the database, warms the cache. Click counting: the redirect service drops an event on a queue, and an offline consumer aggregates counts, so the redirect never blocks.

Deep dive, the code. Key generation service: pre-generate billions of unique 7-character base62 keys (62^7 is about 3.5 trillion, plenty), store them in a keys table, and each app server leases a batch of a few thousand at a time. No collisions, no hot counter, and a server can keep minting during a brief KGS outage from its local batch. Custom aliases are a separate write that checks uniqueness directly.

Deep dive, the read scale. Shard the database by short code. Put Redis in front with a very high hit rate because links repeat. Popular links get cached everywhere (Day 18, the celebrity problem in miniature). The database is a safety net, not the hot path.

Failure and cost. The redirect service is stateless, so you run many behind the balancer and lose none to a single death. Cache down means a read storm onto the database (Day 17, the thundering herd), so you protect it with request coalescing and a database that can take the fallback load. Cost is dominated by the cache and the read bandwidth, not storage. The redirect path is a single point of failure for the whole product, so it gets the most replication and the tightest SLO (Day 44).

The sentence that sounds senior: "it is a 100-to-1 read system, so the design is really a cache design with a durable store behind it, the write path and read path share nothing so a code-generator outage never touches redirects, and click counting is async so analytics never slows a redirect."

</details>

<details markdown="1">
<summary>The self-grade rubric</summary>

Score each out of 2: 0 skipped or wrong, 1 touched it, 2 did it well.

- Requirements: did you separate functional from non-functional, and did you name "read heavy" as the driving fact?
- Scale: did you produce reads/s, writes/s and storage, and did the numbers change a decision?
- API and entities: a clean handful of endpoints and the core entity?
- High-level: did the diagram separate the read path from the write path?
- Deep dive: did you pick a real hinge decision (the code, or the read scale) and reason through the tradeoff?
- Failure and cost: did you show reads survive a write-path failure, and name the single point of failure?

10 to 12 is interview ready on this question. 6 to 9, you have the pieces but the clock or the depth needs work. Below 6, run it again tomorrow.

</details>
