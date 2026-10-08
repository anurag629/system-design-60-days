---
title: "Day 43 drills"
parent: "Day 43: observability"
grand_parent: "Week 7: production"
nav_order: 2
---

# Day 43 drills

Written on paper first. Logs, metrics, traces, and why a mean hides the fire.

D1 (the mean lies, on purpose. 100 requests: 99 of them take 40 ms, and one takes 4,000 ms. Work out the mean, the p50 and the p99 by hand. Which of the three would a dashboard showing only "average latency" report, and what is it hiding? In one line, why is the average the single worst summary of a user's experience):

D2 (the RED method. Name the three RED signals for a request-driven service and say in a few words what each one tells you. For a service running at 500 req/s, 3% errors and a p99 of 1.4s while the mean is 60 ms, which signal pages you first and why? Which one would a "mean latency" alert have completely missed):

D3 (structured vs unstructured. You keep 10 million log lines a day. At 3am someone asks "every 5xx for tenant acme on /checkout slower than one second in the last hour." Why is that one line against structured logs and an ordeal against a blob of prose? Name the one field that, if nobody logged it, makes the question unanswerable after the fact, and say what that tells you about when logging decisions actually get made):

D4 (a trace across services. A request fans out to three downstream services called one after another: 20 ms, 430 ms and 35 ms, plus 15 ms of gateway work. What is the total latency, and what fraction of it is the slow span? A latency metric reports only that total number; what can the trace tell you that the metric cannot? Now suppose the three were called in parallel instead of in sequence: what is the total, and which span does the trace still finger):

D5 (RED, USE, and the tail under fan-out. RED is for requests; USE is utilisation, saturation and errors for a resource. Which method do you reach for to explain a slow endpoint, and which to explain why the database behind it is slow? Then the Day 1 question again: one backend has a p99 of 100 ms, meaning 1% of its calls are slow, and a page makes 10 independent calls to it. What fraction of page loads contain at least one slow call, and why does that make a dependency's p99 matter more than it first looks):
