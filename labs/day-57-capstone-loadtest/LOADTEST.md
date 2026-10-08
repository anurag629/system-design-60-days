---
title: "Day 57 load-test guide"
parent: "Day 57: capstone load test"
grand_parent: "Week 8: putting it all together"
nav_order: 1
---

# Load-test guide: find the knee

The load generator `loadgen.py` lives next to this file. Pure standard library, nothing to install.

## Run it against your service

```
# terminal 1: your Day 56 service (or the reference)
cd labs/day-56-capstone-build && python3 app.py

# terminal 2: push rising concurrency
cd labs/day-57-capstone-loadtest
python3 loadgen.py --url http://127.0.0.1:8080 --stages 1,2,4,8,16,32 --duration 3 --write-ratio 0.1
python3 loadgen.py --url http://127.0.0.1:8080 --stages 1,2,4,8,16,32 --duration 3 --write-ratio 0.9
```

- `--stages` is the worker counts it runs in turn.
- `--duration` is seconds per stage.
- `--write-ratio` is the fraction of requests that are writes (POST) vs reads (GET). Turn it up to hammer the write path, down for the read path.

It prints throughput, error rate, and p50/p95/p99 per stage, then names the peak.

## Predict first

Before you run, write down: peak throughput, the worker count where p99 crosses 100ms, and which resource gives out first. The gap between your guess and the output is the lesson.

## Read the result

- Throughput rises, then flattens. The flat line is your ceiling.
- The knee is where throughput flattens but p99 keeps climbing. That is your capacity and your bottleneck.
- Watch p99, not the average. The tail is where the pain lives.

## Then do real performance work

1. Form a hypothesis for the bottleneck (use the USE method and your `/metrics`).
2. Change one thing to try to raise the ceiling.
3. Re-run and see if the knee moved.
4. Record the before and after.

That measure, hypothesise, change one thing, measure again cycle is the whole job.

## Point it at anything

`loadgen.py` takes any `--url`, so it works against your own service, the reference, or any HTTP endpoint you control. Do not point it at services you do not own.
