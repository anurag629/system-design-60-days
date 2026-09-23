---
title: Home
nav_order: 1
permalink: /
---

# System design in 60 days
{: .fs-9 }

Four hours a day, from the first latency number to a full capstone design. Build small, broken, real systems, break them harder, then measure what happened.
{: .fs-6 .fw-300 }

<div class="today-card" markdown="1">
**Today, Wed 2026-09-23: [Day 2, estimation vs reality](days/day-02.md)**

Predict six numbers about a million-row database, then measure all six. Start with the reading block, and keep the laptop closed until your predictions are on paper.
</div>

[Start today's day](days/day-02.md){: .btn .btn-primary .mr-2 }
[See the progress log](progress.md){: .btn }

---

## The eight weeks

| Week | Days | Dates | Topic |
|---|---|---|---|
| [Week 1](weeks/week-01.md) | 1 to 7 | Jul 10, then Sep 23 to Sep 28 | Ground truth: latency, estimation, networking, APIs |
| [Week 2](weeks/week-02.md) | 8 to 14 | Sep 29 to Oct 5 | Storage: B-trees, LSM trees, indexes, transactions, replication |
| [Week 3](weeks/week-03.md) | 15 to 21 | Oct 6 to Oct 12 | Caching and the CDN |
| [Week 4](weeks/week-04.md) | 22 to 28 | Oct 13 to Oct 19 | Async: queues, logs, idempotency, backpressure |
| [Week 5](weeks/week-05.md) | 29 to 35 | Oct 20 to Oct 26 | Distributed systems and the papers |
| [Week 6](weeks/week-06.md) | 36 to 42 | Oct 27 to Nov 2 | AI systems: inference, RAG, agents, token economics |
| [Week 7](weeks/week-07.md) | 43 to 49 | Nov 3 to Nov 9 | Production: observability, SLOs, rate limits, cost |
| [Week 8](weeks/week-08.md) | 50 to 60 | Nov 10 to Nov 20 | Synthesis, mock designs, capstone |

Day pages show up in the sidebar under their week as they get written. Each day is built from the previous evening's report, so they're written one at a time.

## Days so far

| Day | Date | Topic | Lab results |
|---|---|---|---|
| [Day 1](days/day-01.md) | Fri Jul 10 | How slow is slow? | [Results](labs/day-01-latency/RESULTS.md) |
| [Day 2](days/day-02.md) | Wed Sep 23 | Estimation vs reality | [Results](labs/day-02-estimation/RESULTS.md) |

## The daily loop

| Block | Time | What |
|---|---|---|
| Read | 50 min | The day's reading, plus the explainer on the day page |
| Drill | 40 min | Back of the envelope math, or a timed design question, on paper |
| Build | 100 min | The lab. Code that runs, numbers you can point at |
| Write | 30 min | One LinkedIn post and one Twitter thread, drafted in `shares/` |

At the end of each day, report back three things: what you completed, the number that surprised you in the lab, and one thing you couldn't explain. The next day is built from that report.

## Getting around

The sidebar on the left has every week, with its days nested inside. Each day holds its own lab results and drafts. Every page in the main track has previous and next buttons at the bottom, so you can read straight through. The search box at the top covers every page.

Lab code lives in the [GitHub repo](https://github.com/anurag629/system-design-60-days). Clone it, since the labs run on your own machine.
