---
title: "Day 7: your first real design"
parent: "Week 1: ground truth"
nav_order: 7
has_children: true
---

# Day 7
## Your first real design: a URL shortener, and how far you have come 🧩

Today's one idea: you already have every piece you need to design a real system. Today you put them together into one whole, on paper, the way you would in an interview or a design review. No new theory. Just assembly, and a look back at how differently you think now compared to a week ago.

This is the week 1 finale. Six days ago "design a URL shortener" would have been a scary open question. Today it is a set of decisions you can reason about with numbers. That shift is the whole point of the week.

---

## Before you start ⏪

No new tools. You will reach back for all six days: latency intuition from Day 1, estimation from Day 2, the request path from Day 3, the queue and the cliff from Day 4, API and pagination from Day 5, load balancing and failure from Day 6. Keep them handy. If any one is fuzzy, that is useful to notice today, because a design pulls on all of them at once.

There is no coding lab today. The deliverable is a written design, done against the clock, like the real thing.

---

## Words you will meet today 📖

Functional requirements are what the system must do. For a URL shortener: take a long URL and give back a short one, and send anyone who visits the short one to the long one.

Non-functional requirements are how well it must do it: how fast, how available, how much scale. These are where the interesting engineering lives, and where your week 1 numbers come in.

High-level design is the boxes-and-arrows picture: clients, load balancer, app servers, cache, database. The first thing you draw.

A deep dive is picking one hard part of that picture and working out the details, like exactly how the short code gets generated.

A bottleneck is the part that gives out first as traffic grows. Naming it, and saying what you would do about it, is the single most senior-sounding thing you can do in a design.

A short code is the bit after the slash, the "abc1234" in a short link. The scheme you pick to generate it is the heart of this design.

Base62 is counting in digits plus lowercase plus uppercase letters, 62 symbols. It is how you turn a boring incrementing number into a short, URL-safe code.

A 301 is a permanent redirect, which browsers cache, so repeat visits skip your server. A 302 is a temporary redirect, which comes back to you every time. That one choice decides whether you can count clicks.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [The delivery framework](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery) from Hello Interview. How to actually run a 45-minute design: the order to do things in so your brain is free to think. Read this first.
- [Bit.ly design breakdown](https://www.hellointerview.com/learn/system-design/problem-breakdowns/bitly) from Hello Interview. The exact problem you are doing today, worked by people who interview for a living. Skim it before you try, read it properly after.
- [Design Pastebin / Bit.ly](https://github.com/donnemartin/system-design-primer/blob/master/solutions/system_design/pastebin/README.md) from the System Design Primer. A second worked take, with back of the envelope numbers laid out.

Watch, after you have done your own design:
- [Design a URL shortening service like TinyURL](https://www.youtube.com/watch?v=C7_--hAhiaM) by Concept and Coding, about 30 minutes. A full walkthrough. Watching it before you try robs you of the practice, so do yours first.
- Shorter option: [Tiny URL system design](https://www.youtube.com/watch?v=Cg3XIqs_-4c) by TechPrep, 9 minutes.

### The framework, in the order you use it (15 min)

Every good design interview runs in roughly the same order, and knowing the order is what frees you to think about the actual problem instead of panicking about what comes next.

First, requirements. Ask what it must do (functional) and how well (non-functional). Do not skip this to look fast. A minute spent here saves you from designing the wrong thing for forty.

Second, estimate the scale. This is Day 2, and it is where you win or lose. The numbers you get here decide every choice after: whether one database is enough, whether you need a cache, how long your codes must be. Say the numbers out loud.

Third, the API. This is Day 5. A couple of endpoints, the methods, what goes in and what comes back. It forces you to be concrete.

Fourth, the high-level design. Draw the boxes: client, load balancer (Day 6), app servers, cache (coming in week 3), database (week 2). Show the write path and the read path separately, because for this system they look very different.

Fifth, the deep dive. Pick the hard part and go deep. For a URL shortener that is always the short code: how do you generate it so it is short, unique, and fast to make.

Last, bottlenecks and failure. What gives out first, what you would do about it, what happens when a piece dies (Day 6). This is the part most people skip and the part that marks you as someone who has run things in production.

### Why a URL shortener is a read-heavy problem (10 min)

Here is the insight that shapes the whole design, and you can only see it because you did Day 2. People create a short link once and then it gets clicked many, many times. The reads dwarf the writes, often by a hundred to one or more.

That one fact decides almost everything. The write path can be simple, because writes are rare. The read path, the redirect, has to be fast and cheap, because it happens constantly, and it is the thing a user actually waits on. So you cache hot links aggressively (week 3), you keep the redirect to as few round trips as possible (Day 3), and you make sure losing one server does not take redirects down (Day 6). A design that treats reads and writes the same here is a design that has not done the estimation.

---

## Block 2: drill (40 min) ✍️

Paper first. These are the design, broken into its hardest decisions. Write real answers, with numbers, into [`notes/day-07-drills.md`](../notes/day-07-drills.md). Spend about 8 minutes each.

D1. Estimate the scale. Assume 100 million new short URLs are created per month, and reads outnumber writes 100 to 1. What is the write rate per second, and the peak? The read rate, and the peak? Over 5 years, how many URLs are stored, and roughly how many terabytes?

D2. How long must the short code be? Using your 5-year count from D1, and base62 codes, how many characters do you need so you never run out? Show the arithmetic (how big is 62 to the power 6, and 62 to the power 7).

D3. Design the API. Give the endpoint to create a short URL and the endpoint to use one (the redirect). Method, path, what the client sends, what comes back, and the status code. For the redirect, 301 or 302, and what does that choice cost or buy you?

D4. Pick a short-code generation scheme. Compare three: an incrementing counter encoded to base62, a hash of the long URL, and a random code. For each, say how it handles uniqueness and what its weakness is. Which would you ship, and why?

D5. Name the bottleneck. At the read rate from D1, where does the simplest design (app servers plus one database) give out first? What one thing do you add to fix it, and roughly what read rate does the database see afterwards if that thing has a 90 percent hit rate?

---

## Block 3: build (100 min) 🔧

Today you build a design, not code. The template is [`labs/day-07-url-shortener/DESIGN.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-07-url-shortener/DESIGN.md). Copy it into your fork and fill it in.

Do it against the clock. Give yourself 45 minutes for a first full pass, start to finish, the way an interview runs: requirements, estimate, API, high-level design, deep dive on the short code, then bottlenecks and failure. Do not look at the Solutions section or the worked breakdowns until your 45 minutes are up. The whole value is in producing it yourself, badly, and then seeing what you missed.

Then take the rest of the block to go back over it with the readings open and improve it. Mark in a different colour what you added on the second pass. That delta is your actual learning for the week.

If you want to make it real (optional, and genuinely fun): the write path and read path of a URL shortener are small enough to build in an evening with the tools you already have, Python's `http.server` and `sqlite3`, base62 for the codes, and a dict as a stand-in cache. You have the pieces from days 2, 5 and 6. Treat it as a stretch, not a requirement.

### What a strong design has that a weak one does not

A weak design jumps straight to boxes. A strong one estimates first, and lets the numbers choose the boxes. A weak one treats reads and writes the same. A strong one notices this is read-heavy and designs the two paths differently. A weak one says "use a database." A strong one says which part is the bottleneck, at what number, and what it would add. Aim for the second kind.

### Deliverable

Your filled-in `DESIGN.md`, plus one honest paragraph at the bottom: what did your second pass add that your first pass missed? That paragraph is more useful than the design itself.

---

## Block 4: write (30 min) 📣

Your angle today is the before and after: "A week ago, 'design a URL shortener' would have frozen me. Here is the design I can now reason about, and the one number that drives all of it." Share your estimate, your short-code decision, and the bottleneck you named. A hand-drawn boxes-and-arrows photo makes a strong image.

Example posts are on the [Day 7 posts](../shares/day-07-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it, and look back 📝

Log the usual three: what you completed, your scale estimate and short-code choice, and one thing you still cannot explain.

Then the week 1 retrospective, which is the real point of today. Think back to Day 2, when you first turned "500 million users" into servers. If someone had asked you to design a URL shortener that day, what would you have drawn? Write down, in a few lines, the three biggest things your Day 7 design has that your Day 2 self would have missed. That gap is week 1.

Week 2 starts storage: how a database actually puts a row on a disk, why an index speeds up reads and slows down writes, and the two great families, B-trees and LSM trees. The URL shortener's database, which you waved at today, is about to stop being a black box.

---

## Solutions 🔑

Open these only after your 45-minute design pass. Reading the answer first is the one way to waste this day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. 100 million writes per month is 100,000,000 / (30 × 100,000 seconds) which is about 33 per second, call it 40. Peak at 3x is roughly 120 per second. Reads at 100 to 1 are about 4,000 per second, peak roughly 12,000. Storage: 100 million per month × 12 × 5 years is 6 billion URLs. At about 500 bytes each (short code, long URL, a little metadata) that is 3 terabytes, call it 9 with replication. The writes are tiny. The reads are the system. Three terabytes fits on one good machine, so this does not need heavy sharding for storage, it needs a plan for the read traffic.

D2. You need codes for 6 billion URLs and some headroom. 62 to the power 6 is about 56 billion, which already covers 6 billion, but it is tight and gets tighter as you grow. 62 to the power 7 is about 3.5 trillion, which is comfortable for decades. So 7 characters. Short enough to type, huge enough to never collide.

D3. Create: `POST /urls` with the long URL in the body, returns 201 and the short code (or full short URL). Use: `GET /{code}` returns a redirect to the long URL. For the redirect, 302 (temporary) means every click comes back to your server, so you can count clicks and change the target later, at the cost of serving every redirect yourself. 301 (permanent) lets the browser cache the redirect, which spares your servers but means you never see repeat clicks and can never change the target. If analytics matter, and for a link shortener they usually are the product, use 302.

D4. Counter plus base62: keep a global counter, hand each new URL the next number, encode it to base62. Unique for free, and short. Weakness: the codes are sequential and guessable (code 1001 is right after 1000), which leaks how many links exist and lets people walk your links, and the single counter is a write bottleneck unless you hand out ranges to each server. Hash of the long URL: take a hash, keep the first 7 base62 characters. Weakness: collisions, two URLs hashing to the same code, so you still need a uniqueness check and a retry, and identical long URLs map to the same code (sometimes good, sometimes a privacy leak). Random code: generate 7 random base62 characters, check it is free, retry on the rare clash. Weakness: a uniqueness check on every write, though at 56 billion free codes the clash rate is tiny. What to ship: random, or counter-with-ranges if you want the shortest possible codes. Random is simplest to reason about and not guessable, and the uniqueness check is cheap because writes are rare.

D5. The bottleneck is the database on reads. At 4,000 reads per second and peaks past 10,000, a single database doing a lookup per redirect is working hard and is a single point of failure. The fix is a cache in front of it (week 3), holding the hot links, since a small fraction of links get most of the clicks. At a 90 percent hit rate, the database sees 10 percent of 4,000, which is 400 reads per second, which is nothing. That one box turns the hard part of the system into an easy one. This is the Day 2 cache-hit-rate lesson and the Day 1 "reads from memory beat reads from disk" lesson, meeting in a real design.

</details>

<details markdown="1">
<summary>A worked reference design</summary>

This is one good answer, not the only one. Yours will differ, and that is fine. What matters is that the numbers drive the choices.

Requirements. Functional: create a short URL from a long one, and redirect a short URL to its long one. Maybe: custom aliases, expiry, click analytics. Non-functional: redirects must be fast (tens of milliseconds) and highly available (a dead redirect is a dead link everywhere it was shared), the system is very read-heavy, and short codes must be unique and hard to guess.

Scale, from D1: about 40 writes per second, about 4,000 reads per second, peaks a few times that, 6 billion URLs and roughly 3 terabytes over 5 years.

API, from D3: `POST /urls` to create, `GET /{code}` to redirect with a 302 so clicks can be counted.

Data model: a table keyed by the short code, holding the long URL, a created timestamp, and a click count. The code is the primary key, so the redirect is a single primary-key lookup, the fast index seek you measured on Day 5, not a scan.

Short code, from D4: 7 random base62 characters, checked for uniqueness on write. Writes are rare, so the check is cheap, and random codes are not walkable.

High-level design. Write path: client to load balancer to a stateless app server (Day 6), which generates a code, checks it is free, writes the row, returns it. Read path: client to load balancer to app server, which checks a cache first and only falls back to the database on a miss, then returns a 302. The two paths share almost nothing, because writes are rare and reads are everything.

The bottleneck and the fix, from D5: the database on reads. Put a cache (week 3) in front, holding hot links. At a 90 percent hit rate the database drops to a few hundred reads per second. For storage, 3 terabytes fits on one machine with replicas for safety, so you shard for durability and read-replicas rather than because the data is too big.

Failure, from Day 6: app servers are stateless, so losing one is a non-event behind the load balancer with health checks. The database has replicas, and a read replica can serve redirects if the primary is busy. The cache going down is the scary case, because the database suddenly takes the full 4,000 reads per second, so you size the database to survive a cold cache, or warm the cache carefully on restart. That last sentence, about surviving a lost cache, is the one that makes an interviewer sit up.

</details>

<details markdown="1">
<summary>Week 1 in one page</summary>

Seven days, one thread running through all of them: measure before you guess, and let the numbers choose the design.

Day 1, the storage hierarchy. Each tier is about 100x slower than the one above, and a network round trip is a million memory reads. Every "should we cache this" is a comparison of two of these numbers.

Day 2, estimation. Users times actions, divided by 100,000 seconds. Enough to decide whether one machine is enough, which is the only question estimation needs to answer.

Day 3, the request path. DNS, TCP, TLS, then the request, and the round trips dominate, so you count them rather than optimising the code between them.

Day 4, the queue and the cliff. A server does not slow down gradually, it falls off a wall near 100 percent busy, so you run at 60 to 70 percent and a slow dependency takes down everything that calls it.

Day 5, the API and pagination. A clean contract, and keyset over offset, because offset re-reads everything it skips. Index seeks beat scans by a thousand times.

Day 6, more than one server. A load balancer is easy, surviving a dead server is the job, and that comes down to noticing fast (health checks) and trying again (retry).

Day 7, today. All six, assembled into a design, with the numbers in front.

If your Day 7 design estimated first, split the read and write paths, named the bottleneck with a number, and had an answer for a lost cache and a dead server, you did not learn facts this week. You built judgement. That is the thing that lasts.

</details>
