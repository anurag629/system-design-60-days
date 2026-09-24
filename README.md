# System design in 60 days

A free, hands-on system design course. 60 days, 4 hours a day, about 240 hours in total. Reading, drills, a lab with starter code, full solutions, and example posts for every day.

Read it as a site: https://anurag629.github.io/system-design-60-days/

## The bet

Most people "learn system design" by watching videos about designing Twitter, then freeze in an interview because they memorized an answer instead of a method. This course is built the other way around: you build small, broken, real systems, break them harder, then measure what happened. Theory shows up when you need it to explain a number you just saw.

The AI-era part isn't a bolt-on week at the end. Serving models, RAG retrieval, agent orchestration, and token economics are just distributed systems with unusual cost curves and unusually bad tail latency. Weeks 1-5 earn you the vocabulary. Week 6 spends it.

## Daily loop (4 hours)

| Block | Time | What |
|---|---|---|
| Read | 50 min | Assigned chapter or paper. Notes go in `notes/`. |
| Drill | 40 min | Back-of-envelope math, or a design question with a timer. |
| Build | 100 min | The lab. Code that runs. Numbers you can point at. |
| Write | 30 min | One LinkedIn post + one Twitter thread. Draft in `shares/`. |

The Write block is not optional and not vanity. Explaining a thing you half-understand to strangers is the fastest way to find the hole in your understanding. Ship it even when it's ugly.

## Following along

1. Fork this repo and clone your fork. Labs run on your own machine, Python standard library only.
2. Each day, work through the day page on the site in order. Write your predictions down before running any lab.
3. Fill in the TODOs in the lab's starter file. Stuck? Each lab folder has a `solution.py`, and each day page ends with a Solutions section: drill answers, the TODO code, and a reference run with every number explained.
4. Write your posts. Each day has example posts written with the reference run's numbers.
5. Keep a progress log: what you finished, the number that surprised you, and one thing you can't explain yet.

## The eight weeks

Week 1 is ground truth. Latency numbers, back of the envelope estimation, HTTP/TCP/TLS, DNS, API design, load balancing. You end the week able to estimate any system's shape in 5 minutes on a napkin.

Week 2 is storage. B-trees vs LSM trees, indexes, transactions and isolation levels, replication, partitioning, the actual cost of a JOIN. Postgres under load, with real EXPLAIN plans.

Week 3 is caching and the CDN. Cache invalidation, thundering herds, hot keys, Redis internals, CDN behavior, cache coherence. This is where most production systems actually fall over.

Week 4 is async. Queues, log-structured streaming, Kafka's design, exactly-once as a lie, idempotency keys, outbox pattern, backpressure. You build a pipeline that survives you killing workers at random.

Week 5 is distributed systems, properly. CAP as it actually reads, consensus and Raft, logical clocks, quorums, failure detection, the papers (Dynamo, Bigtable, Spanner). Hardest week. Budget the frustration.

Week 6 is AI systems. LLM inference serving, KV cache and batching, vector search, RAG architecture, agent orchestration, semantic caching, token-based rate limiting, model gateways and fallback. Everything you learned so far, aimed at a GPU.

Week 7 is production. Observability, SLOs and error budgets, rate limiting, multi-tenancy, security boundaries, cost modeling, capacity planning. The stuff that separates a design from a system.

Week 8 is synthesis. Timed mock designs, one full capstone, and a written architecture doc you'd be happy to hand a staff engineer.

## The stack you'll build on

Postgres (Neon or local), Redis (Upstash or local), Node/TypeScript or Python, Docker, k6 for load testing, and a Vercel or Railway deploy target. Everything has a free tier. Nothing here requires a cloud bill.

## Files

- `days/`: one page per day, with reading, drills, the lab brief, and solutions
- `weeks/`: the overview for each week
- `labs/`: one folder per lab, with a starter file (TODOs), `solution.py`, and a `RESULTS.md` template
- `notes/`: drill answer templates
- `shares/`: example LinkedIn and X posts for each day
- `progress.md`: the author's own progress log
