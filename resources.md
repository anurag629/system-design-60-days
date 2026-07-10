# Free resources, mapped to the 60 days

Every link here has been checked and resolves. A warning before the list, though.

Watching system design videos feels like learning and mostly isn't. You will nod
along to a 40-minute video on Kafka and be unable to explain what a partition is a
week later. The labs are the learning. These are here to explain a number you
already measured, or to give you vocabulary for a thing you already built.

Rule of thumb: **no more than one video per day, and only after the lab.**

Each day file (`days/day-NN.md`) has a "Today's links" block with just the two or
three things you need that day. This page is the full map.

---

## The five I'd actually keep

If you use nothing else on this page, use these.

- **[Martin Kleppmann's distributed systems lectures](https://www.youtube.com/playlist?list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdiB)**
  (8 lectures, ~1 hr each). Cambridge course by the man who wrote DDIA. Free
  [lecture notes PDF](https://www.cl.cam.ac.uk/teaching/2122/ConcDisSys/dist-sys-notes.pdf).
  The best free resource in the field, not close. Save it for weeks 4-5.
- **[CMU 15-445, Intro to Database Systems](https://15445.courses.cs.cmu.edu/)**
  (Andy Pavlo, [full course on YouTube](https://www.youtube.com/@CMUDatabaseGroup)).
  The first six lectures, on storage and buffer pools and B-trees, are exactly
  week 2. Pavlo is funny and uncompromising about detail.
- **[The AWS Builders' Library](https://aws.amazon.com/builders-library/)** (free,
  written). Short essays by AWS principal engineers on things they actually run:
  timeouts, retries, jitter, load shedding. Start with
  ["Timeouts, retries, and backoff with jitter"](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/).
- **[Use The Index, Luke!](https://use-the-index-luke.com/)** (free book about
  database indexes and nothing else). Tomorrow's lab shows an index make a lookup
  14,000x faster for 5% more disk. This explains why, and when it won't.
- **[The Google SRE book](https://sre.google/books/)** (free online). Read
  [risk](https://sre.google/sre-book/embracing-risk/),
  [SLOs](https://sre.google/sre-book/service-level-objectives/), and
  [monitoring](https://sre.google/sre-book/monitoring-distributed-systems/).
  Week 7 is built from these.

---

## YouTube, by usefulness

Ordered by how much you'd actually learn per hour, which is not the same as how
popular they are.

**Deep, worth your time**

- **[Hussein Nasser](https://www.youtube.com/@hnasr)** — backend engineering, TCP,
  HTTP, database internals. Long and rambling, and genuinely teaches. His TCP and
  connection-pooling videos pair perfectly with what you measured on Day 1.
- **[Arpit Bhayani](https://www.youtube.com/@AsliEngineering)** — database
  internals and system design, deeply technical.
- **[Jordan Has No Life](https://www.youtube.com/@jordanhasnolife5163)** — works
  through DDIA chapter by chapter and reads actual papers. Low production value,
  high signal. The opposite of ByteByteGo.
- **[MIT 6.5840, Distributed Systems](https://pdos.csail.mit.edu/6.824/)** (Robert
  Morris, [lectures on YouTube](https://www.youtube.com/@6.824)). Graduate level.
  Save for week 5. If Raft is confusing after the paper, this is where it clicks.

**Fine, but shallow**

- **[ByteByteGo](https://www.youtube.com/@ByteByteGo)** — Alex Xu's channel.
  Beautiful animation, correct, two inches deep. Watch it *after* you've built the
  thing, as a summary.
- **[Gaurav Sen](https://www.youtube.com/@gkcs)** — the classic interview channel.
  Solid on the format. Treats a lot of choices as settled that aren't.

**For the interview specifically, week 8 only**

- **[Hello Interview](https://www.hellointerview.com/)** — free written breakdowns
  of common designs, unusually honest about what an interviewer is listening for.
  Best free interview prep I know of.
- **[Exponent](https://www.tryexponent.com/)** — free mock interview recordings.
  Useful for watching someone structure 45 minutes under pressure.

---

## Written, free

**Fundamentals**
- [*High Performance Browser Networking*](https://hpbn.co/), Ilya Grigorik — free
  full text. [Ch. 1, latency and bandwidth](https://hpbn.co/primer-on-latency-and-bandwidth/)
  is week 1.
- [*Distributed Systems for Fun and Profit*](https://book.mixu.net/distsys/),
  Mikito Takada — short, free, the gentlest correct intro to consistency models.
- [Colin Scott's interactive latency page](https://colin-scott.github.io/personal_website/research/interactive_latency.html)
  — you used this on Day 1.
- [Jeff Dean's latency numbers](https://gist.github.com/jboner/2841832) — the gist.
- [The System Design Primer](https://github.com/donnemartin/system-design-primer)
  — the most-starred free system design resource. Good index, shallow depth. Use
  it as a glossary, not a course.

**Databases**
- [Postgres docs: EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
  — dry, authoritative, short. Week 2.
- [Use The Index, Luke! — Anatomy of an index](https://use-the-index-luke.com/sql/anatomy)
  — start here.
- [pgexercises](https://pgexercises.com/) — free SQL practice on a real dataset.
  Do this if your SQL is rusty; week 2 assumes you can write a JOIN.

**Distributed systems**
- [Jepsen](https://jepsen.io/analyses) — Kyle Kingsbury breaks real databases and
  documents exactly how they violated their advertised guarantees. Hilarious, and
  the fastest way to understand why consistency models matter.
- [raft.github.io](https://raft.github.io/) and
  [The Secret Lives of Data: Raft](https://thesecretlivesofdata.com/raft/) — Raft,
  visualized step by step. Do the visualization before the paper.
- [Papers We Love](https://github.com/papers-we-love/papers-we-love) — the papers,
  organized.

**Production and scale**
- [Marc Brooker's blog](https://brooker.co.za/blog/) — AWS principal engineer on
  queueing, timeouts, and capacity. Short, very high density.
- [Dan Luu's blog](https://danluu.com/) — performance and latency, and a lot of
  "everyone believes X, here's the data showing X is false."
- [High Scalability](https://highscalability.com/) — old and patchy, but the
  architecture writeups are a goldmine. The
  [back-of-the-envelope piece](https://highscalability.com/google-pro-tip-use-back-of-the-envelope-calculations-to-choo/)
  is your Day 2 reading.
- Engineering blogs worth a weekly read: Netflix, Uber, Discord, Cloudflare,
  Figma. Discord's "trillions of messages" post and Cloudflare's outage
  postmortems beat most textbooks.

**AI systems (week 6)**
- [vLLM / PagedAttention paper](https://arxiv.org/abs/2309.06180) — the one paper
  that makes LLM inference make sense. It's a virtual-memory paper in disguise.
- [Anthropic prompt caching docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
  — read the constraints, not the tutorial. The constraints are the design.
- [pgvector](https://github.com/pgvector/pgvector) — the least hyped, most
  practical intro to vector search.

---

## The papers, in the order they'll make sense

Save all of these for week 5 and later. Reading them early is discouraging.

1. [**Raft**](https://raft.github.io/raft.pdf) — deliberately written to be
   readable, and it is.
2. [**Amazon Dynamo**](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
   (2007) — consistent hashing, quorums, eventual consistency.
3. [**Google MapReduce**](https://research.google/pubs/pub62/) (2004) — short,
   historically important, easy.
4. [**Google Bigtable**](https://research.google/pubs/pub27898/) (2006) — LSM
   trees in production.
5. [**Kafka**](https://notes.stephenholiday.com/Kafka.pdf) — the log as a
   primitive.
6. [**Google Spanner**](https://research.google/pubs/pub39966/) (2012) — what you
   can do if you own atomic clocks. Read last; it reframes everything before it.

---

## Practice, not consumption

- **Build the thing.** The labs in this repo are the practice. Nothing here
  substitutes.
- **Read one outage postmortem a week.** Cloudflare, GitHub, and AWS publish real
  ones. Before you read the fix, decide what you'd have done.
- **Redesign something you actually use** and understand the requirements for,
  where you'd notice if the design were wrong. Not Twitter.
- **[Hello Interview](https://www.hellointerview.com/)** for timed practice, week 8
  only.

---

## What to skip

Grokking the System Design Interview, and the genre it spawned. It teaches you to
produce a plausible-sounding answer to a memorized question. That works until
someone asks a follow-up. You're doing this the slow way on purpose.

And skip any video titled "System Design Interview: Design Uber in 30 minutes"
until week 8. You'll pattern-match on the answer instead of learning the method,
and the pattern won't transfer.
