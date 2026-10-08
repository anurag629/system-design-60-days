---
title: Home
nav_order: 1
permalink: /
---

# System design in 60 days
{: .fs-9 }

A free, hands-on system design course. Sixty days of work, each day about four hours, done at whatever pace suits you, one a day or one a week. You build small, broken, real systems, break them harder, then measure what happened. Every day has reading, drills, a lab with starter code, full solutions, and example posts so you can learn in public.
{: .fs-6 .fw-300 }

[Start at Day 1](days/day-01.md){: .btn .btn-primary .mr-2 }
[Latest: Day 14](days/day-14.md){: .btn .mr-2 }
[Track your progress](tracker.md){: .btn .mr-2 }
[How to follow along](#how-to-follow-along){: .btn }

---

## Who this is for

Anyone who can write a little Python and wants to actually understand system design, not memorise answers to "design Twitter." No prior system design knowledge is assumed. Every term is explained the first time it shows up. The labs use only Python's standard library, so there's nothing to install, and they run on a laptop.

Most people learn system design by watching videos about designing big systems, then freeze in an interview because they memorised an answer instead of a method. This course works the other way round. You predict a number, measure it on your own machine, and the gap between the two is the lesson. Theory shows up when you need it to explain a number you just saw.

## The eight weeks

| Week | Days | Topic |
|---|---|---|
| [Week 1](weeks/week-01.md) | 1 to 7 | Ground truth: latency, estimation, networking, queues, APIs, load balancing |
| [Week 2](weeks/week-02.md) | 8 to 14 | Storage: B-trees, LSM trees, indexes, transactions, replication |
| [Week 3](weeks/week-03.md) | 15 to 21 | Caching and the CDN |
| [Week 4](weeks/week-04.md) | 22 to 28 | Async: queues, logs, idempotency, backpressure |
| [Week 5](weeks/week-05.md) | 29 to 35 | Distributed systems and the classic papers |
| [Week 6](weeks/week-06.md) | 36 to 42 | AI systems: inference serving, RAG, agents, token economics |
| [Week 7](weeks/week-07.md) | 43 to 49 | Production: observability, SLOs, rate limits, cost |
| [Week 8](weeks/week-08.md) | 50 to 60 | Synthesis, mock designs, capstone |

New days are published as they're written. Each one shows up in the sidebar under its week.

## Days so far

| Day | Topic | Lab | Posts |
|---|---|---|---|
| [Day 1](days/day-01.md) | How slow is slow? Measure the storage hierarchy | [Results](labs/day-01-latency/RESULTS.md) | [Posts](shares/day-01-posts.md) |
| [Day 2](days/day-02.md) | Estimation vs reality, a million-row database | [Template](labs/day-02-estimation/RESULTS.md) | [Posts](shares/day-02-posts.md) |
| [Day 3](days/day-03.md) | What happens when you type a URL, counted in round trips | [Template](labs/day-03-url/RESULTS.md) | [Posts](shares/day-03-posts.md) |
| [Day 4](days/day-04.md) | Latency, throughput and the queue | [Template](labs/day-04-queues/RESULTS.md) | [Posts](shares/day-04-posts.md) |
| [Day 5](days/day-05.md) | Designing an API: offset vs cursor pagination | [Template](labs/day-05-pagination/RESULTS.md) | [Posts](shares/day-05-posts.md) |
| [Day 6](days/day-06.md) | More than one server: load balancing and failure | [Template](labs/day-06-load-balancer/RESULTS.md) | [Posts](shares/day-06-posts.md) |
| [Day 7](days/day-07.md) | Your first real design: a URL shortener | [Design template](labs/day-07-url-shortener/DESIGN.md) | [Posts](shares/day-07-posts.md) |
| [Day 8](days/day-08.md) | How a row sits on disk: pages, row vs column stores | [Template](labs/day-08-pages/RESULTS.md) | [Posts](shares/day-08-posts.md) |
| [Day 9](days/day-09.md) | B-trees vs LSM trees: why one hates random writes | [Template](labs/day-09-btree-lsm/RESULTS.md) | [Posts](shares/day-09-posts.md) |
| [Day 10](days/day-10.md) | Indexes in depth: composite, covering, and ignored | [Template](labs/day-10-indexes/RESULTS.md) | [Posts](shares/day-10-posts.md) |
| [Day 11](days/day-11.md) | Transactions and the lost update | [Template](labs/day-11-transactions/RESULTS.md) | [Posts](shares/day-11-posts.md) |
| [Day 12](days/day-12.md) | Replication and lag | [Template](labs/day-12-replication/RESULTS.md) | [Posts](shares/day-12-posts.md) |
| [Day 13](days/day-13.md) | Partitioning and sharding: the hot shard | [Template](labs/day-13-sharding/RESULTS.md) | [Posts](shares/day-13-posts.md) |
| [Day 14](days/day-14.md) | Designing a storage layer for a messaging app | [Design template](labs/day-14-storage-design/DESIGN.md) | [Posts](shares/day-14-posts.md) |

## The loop for each day

Each day is four blocks, about four hours in total. Go at your own pace.

| Block | Time | What |
|---|---|---|
| Read | 50 min | The day's reading and videos, plus the explainer on the day page |
| Drill | 40 min | Back of the envelope math, or a timed design question, on paper |
| Build | 100 min | The lab. Predict first, fill in the TODOs, run it, explain the numbers |
| Write | 30 min | One LinkedIn post and one X thread about what you found |

The four blocks are the four boxes you tick on the [progress tracker](tracker.md). The Write block isn't optional and isn't vanity. Explaining a thing you half understand to strangers is the fastest way to find the hole in your understanding.

## How to follow along

1. Fork the [GitHub repo](https://github.com/anurag629/system-design-60-days) and clone your fork. The labs run on your own machine, because measuring your own machine is the point.
2. Each day, read the day page top to bottom and do the blocks in order. Write your predictions down before you run anything. Every lab refuses to run until you do.
3. Fill in the TODOs in the lab's starter file, run it, and fill in that lab's `RESULTS.md`. If you get stuck, each lab folder has a `solution.py`, and each day page ends with a Solutions section: drill answers, the TODO code, and a reference run with an explanation of every number.
4. Write your posts. The example posts for each day are written with the reference run's numbers. Use them for shape, then write your own with your numbers.
5. Tick off the blocks on the [progress tracker](tracker.md) as you go. It saves in your browser, on your device, so it remembers where you are between visits, and it resets with one button. Alongside it, keep a short reflective log in your fork, a few lines per day:

```markdown
## Day N: topic

The number that surprised me:

One thing I can't explain yet:
```

That last line is the most useful one. Take it into the next day's reading, ask someone, or go back to the lab until it makes sense.

## Getting around

The sidebar on the left has every week, with its days nested inside. Each day holds its lab results, drill notes and example posts. Every page in the main track has previous and next buttons at the bottom, so you can read straight through. The search box at the top covers every page.
