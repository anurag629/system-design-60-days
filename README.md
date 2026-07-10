# System design in 60 days

Start: 2026-07-10 · End: 2026-09-07 · 4 hours/day · ~240 hours total

## The bet

Most people "learn system design" by watching videos about designing Twitter, then freeze in an interview because they memorized an answer instead of a method. This plan is built the other way around: you build small, broken, real systems, break them harder, then measure what happened. Theory shows up when you need it to explain a number you just saw.

The AI-era part isn't a bolt-on week at the end. Serving models, RAG retrieval, agent orchestration, and token economics are just distributed systems with unusual cost curves and unusually bad tail latency. Weeks 1-5 earn you the vocabulary. Week 6 spends it.

## Daily loop (4 hours)

| Block | Time | What |
|---|---|---|
| Read | 50 min | Assigned chapter or paper. Notes go in `notes/`. |
| Drill | 40 min | Back-of-envelope math, or a design question with a timer. |
| Build | 100 min | The lab. Code that runs. Numbers you can point at. |
| Write | 30 min | One LinkedIn post + one Twitter thread. Draft in `shares/`. |

The Write block is not optional and not vanity. Explaining a thing you half-understand to strangers is the fastest way to find the hole in your understanding. Ship it even when it's ugly.

## Reporting back

At the end of each day, tell me:
1. What you completed (and what you skipped)
2. The number that surprised you in the lab
3. One thing you couldn't explain to yourself

I adjust the next day based on that. If you're crushing it, I make it harder. If a concept didn't land, we re-approach from a different angle instead of moving on.

## The eight weeks

**Week 1 — Ground truth.** Latency numbers, back-of-envelope estimation, HTTP/TCP/TLS, DNS, API design, load balancing. You end the week able to estimate any system's shape in 5 minutes on a napkin.

**Week 2 — Storage.** B-trees vs LSM trees, indexes, transactions and isolation levels, replication, partitioning, the actual cost of a JOIN. Postgres under load, with real EXPLAIN plans.

**Week 3 — Caching and the CDN.** Cache invalidation, thundering herds, hot keys, Redis internals, CDN behavior, cache coherence. This is where most production systems actually fall over.

**Week 4 — Async.** Queues, log-structured streaming, Kafka's design, exactly-once as a lie, idempotency keys, outbox pattern, backpressure. You build a pipeline that survives you killing workers at random.

**Week 5 — Distributed systems, properly.** CAP as it actually reads, consensus and Raft, logical clocks, quorums, failure detection, the papers (Dynamo, Bigtable, Spanner). Hardest week. Budget the frustration.

**Week 6 — AI systems.** LLM inference serving, KV cache and batching, vector search, RAG architecture, agent orchestration, semantic caching, token-based rate limiting, model gateways and fallback. Everything you learned so far, aimed at a GPU.

**Week 7 — Production.** Observability, SLOs and error budgets, rate limiting, multi-tenancy, security boundaries, cost modeling, capacity planning. The stuff that separates a design from a system.

**Week 8 — Synthesis.** Timed mock designs, one full capstone, and a written architecture doc you'd be happy to hand a staff engineer.

## The stack you'll build on

Postgres (Neon or local), Redis (Upstash or local), Node/TypeScript or Python, Docker, k6 for load testing, and a Vercel or Railway deploy target. Everything has a free tier. Nothing here requires a cloud bill.

## Files

- `resources.md` — free resources, mapped to the weeks that need them
- `weeks/` — full detail for each week, written the Sunday before
- `days/` — the day's material and exercises
- `labs/` — your code
- `notes/` — your reading notes
- `shares/` — your LinkedIn and Twitter drafts
- `progress.md` — the log
