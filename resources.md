# Free resources, mapped to the 60 days

A warning before the list. Watching system design videos feels like learning and
mostly isn't. You will nod along to a 40-minute video on Kafka and be unable to
explain what a partition is a week later. The labs are the learning. These are
here to explain a number you already measured, or to give you vocabulary for a
thing you already built.

Rule of thumb: **no more than one video per day, and only after the lab.**

---

## The five I'd actually keep

If you use nothing else on this page, use these.

**Martin Kleppmann's distributed systems lectures** (YouTube, 8 lectures, ~1 hr each)
Cambridge undergraduate course, taught by the man who wrote DDIA. Free lecture
notes PDF alongside. This is the single best free resource in the field and it is
not close. Save it for weeks 4-5, it will be over your head before then.

**CMU 15-445, Intro to Database Systems** (Andy Pavlo, YouTube, full semester)
Recorded every year, all lectures public. Pavlo is funny and completely
uncompromising about detail. The first six lectures, on storage and buffer pools
and B-trees, are exactly week 2. Watch those six. You do not need the whole
course, though you may want it by the end.

**The AWS Builders' Library** (aws.amazon.com/builders-library, free, written)
Short essays by AWS principal engineers on things they actually run: timeouts,
retries, jitter, load shedding, health checks. No marketing. This is what
production thinking reads like, and almost nothing else free is at this level.
Start with "Timeouts, retries, and backoff with jitter."

**Use The Index, Luke!** (use-the-index-luke.com, free, written)
A whole free book about database indexes and nothing else. Yesterday's lab
showed you an index made a lookup 14,000x faster for 5% more disk. This explains
why, and when it won't. Week 2.

**The Google SRE book** (sre.google/books, free online)
Read chapters 3, 4, and 6: risk, service level objectives, monitoring. Week 7 is
built out of these. The rest is Google-specific and you can skip it.

---

## YouTube, by usefulness

I've ordered these by how much you'd actually learn per hour, which is not the
same as how popular they are.

**Deep, worth your time**

- **Hussein Nasser** — backend engineering, TCP, HTTP, database internals. Long,
  rambling, occasionally repeats himself, and genuinely teaches you things. His
  videos on TCP and connection pooling pair perfectly with what you measured on
  Day 1.
- **Arpit Bhayani** — database internals and system design, deeply technical.
  Indian audience, so a lot of it is aimed at the interview market, but the
  internals content is real.
- **Jordan Has No Life** — works through DDIA chapter by chapter and reads actual
  papers. Low production value, high signal. The opposite of ByteByteGo.
- **MIT 6.5840 (formerly 6.824), Distributed Systems** — Robert Morris's lectures,
  public on YouTube. Graduate level. Save for week 5. If Raft is confusing after
  reading the paper, this is where it clicks.

**Fine, but shallow**

- **ByteByteGo** — Alex Xu's channel. Beautiful animation, correct, and about two
  inches deep. Good for putting a name to a pattern. Bad for understanding it.
  Watch it *after* you've built the thing, as a summary.
- **Gaurav Sen** — the classic system design interview channel. Solid on the
  interview format. Treats a lot of choices as settled that aren't.
- **Tech Dummies (Narendra L)** — similar territory, some good case-study videos.

**For the interview specifically, later**

- **Hello Interview** (hellointerview.com and their YouTube) — free written
  breakdowns of common designs, and they're unusually honest about what an
  interviewer is actually listening for. Best free interview prep I know of.
  Week 8.
- **Exponent** — free mock interview recordings. Useful for watching how someone
  structures 45 minutes under pressure. The content is generic.

---

## Written, free

**Fundamentals**
- *High Performance Browser Networking*, Ilya Grigorik — hpbn.co, free full text.
  Chapters 1-4 are week 1. Chapter 11-13 for HTTP/2 and HTTP/3.
- *Distributed Systems for Fun and Profit*, Mikito Takada — book.mixu.net/distsys.
  Short, free, and the gentlest correct introduction to consistency models.
- **Colin Scott's interactive latency page** — you used this on Day 1.

**Databases**
- **Andy Pavlo's blog and the CMU database group's "what goes around comes
  around" reading list** — opinionated history of the field.
- **Postgres docs on EXPLAIN and on WAL** — dry, authoritative, short.
- **pgexercises.com** — free SQL practice with a real dataset. Do this if your
  SQL is rusty, because week 2 assumes you can write a JOIN without thinking.

**Distributed systems**
- **Jepsen** (jepsen.io/analyses) — Kyle Kingsbury breaks real databases and
  writes up exactly how they violated the guarantees they advertised. Both
  hilarious and the fastest way to understand why consistency models matter.
- **raft.github.io** and **thesecretlivesofdata.com/raft** — Raft, visualized,
  step by step. Do the visualization before you read the paper.
- **Papers We Love** (github.com/papers-we-love) — the papers, organized.

**Production and scale**
- **Marc Brooker's blog** (brooker.co.za/blog) — AWS principal engineer writing
  about queueing, timeouts, and capacity. Short posts, very high density.
- **Dan Luu's blog** (danluu.com) — performance, latency, and a lot of "everyone
  believes X, here is the data showing X is false."
- **Engineering blogs**: Netflix, Uber, Discord, Cloudflare, Figma. Discord's
  post on storing trillions of messages and Cloudflare's outage postmortems are
  both worth more than most textbooks.
- **highscalability.com** — old, patchy, but the architecture writeups are a
  goldmine if you dig.

**AI systems (week 6)**
- **The vLLM paper** ("Efficient Memory Management for Large Language Model
  Serving with PagedAttention") — this is the one paper that makes LLM inference
  make sense. It is genuinely a virtual-memory paper in disguise.
- **Anthropic and OpenAI docs on prompt caching and batching** — read the pricing
  and the constraints, not the tutorials. The constraints are the design.
- **pgvector's README** — the least hyped, most practical intro to vector search.

---

## The papers, in the order they'll make sense

Save all of these for week 5 and later. Reading them early is discouraging and
teaches you nothing.

1. **Raft** ("In Search of an Understandable Consensus Algorithm") — deliberately
   written to be readable, and it is.
2. **Amazon Dynamo** (2007) — consistent hashing, quorums, eventual consistency.
   Old and still the clearest statement of the tradeoff.
3. **Google MapReduce** (2004) — short, historically important, easy.
4. **Google Bigtable** (2006) — LSM trees in production.
5. **Kafka** ("a Distributed Messaging System for Log Processing") — the log as a
   primitive.
6. **Google Spanner** (2012) — what you can do if you own atomic clocks. Read
   last. It reframes everything before it.

---

## Practice, not consumption

- **Build the thing.** The labs in this repo are the practice. Nothing on this
  page substitutes.
- **Read one outage postmortem a week.** Cloudflare, GitHub, and AWS publish real
  ones. Ask yourself, before reading the fix, what you would have done.
- **Redesign something you use.** Not Twitter. Something you actually use and
  understand the requirements for, where you'd notice if the design were wrong.
- **hellointerview.com** for timed practice, week 8 only.

---

## What to skip

Grokking the System Design Interview, and the entire genre it spawned. It teaches
you to produce a plausible-sounding answer to a memorized question. That works
until someone asks a follow-up. You are doing this the slow way on purpose.

And skip any video titled "System Design Interview: Design Uber in 30 minutes"
until week 8. You'll pattern-match on the answer instead of learning the method,
and the pattern won't transfer.
