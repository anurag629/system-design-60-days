# Week 1 — Ground truth

**Dates:** Fri 2026-07-10 → Thu 2026-07-16
**Level:** starting from zero. No prior system design assumed.

## What system design actually is

Before anything else, let's kill a myth. System design is not a body of trivia about Kafka and load balancers. It's the practice of answering one question over and over: **given what this thing has to do, and given what computers are actually capable of, what's the simplest arrangement of parts that works?**

That question has two halves. The second half, "what computers are actually capable of," is where beginners are weakest, and it's where we start. If you don't know that reading from memory is roughly a hundred times faster than reading from disk, you have no basis for deciding whether to add a cache. You'd just be repeating something you read.

So week 1 is about building an intuition for speed and size. Nothing more.

## What you should be able to do by Thursday night

Someone describes an app. Within five minutes, on paper, you can say roughly how many requests per second it gets, roughly how much data it stores per year, and roughly where it will get slow first. You'll be off by some amount, and that's fine. Being right within 10x is the entire skill. Most beginners are off by 1000x because they never try.

## Days

### Day 1 (Fri) — How slow is slow?
The storage hierarchy: CPU cache, RAM, SSD, network. Each tier is roughly 100x slower than the one above it. You'll measure this yourself with about 40 lines of Python.

### Day 2 (Sat) — Estimation on a napkin
Turning "500 million users" into "how many servers." Powers of ten, seconds in a day, bytes in a record. Lots of repetition until the arithmetic stops being scary.

### Day 3 (Sun) — What happens when you type a URL
DNS, TCP handshake, TLS, HTTP request, response. The classic interview question, but you'll actually watch it happen with real tools instead of reciting it.

### Day 4 (Mon) — Latency vs throughput, and the queue
Why a system at 90% capacity feels fine and a system at 99% capacity falls over. The single most useful mental model in all of performance work, and it's just a graph.

### Day 5 (Tue) — Designing an API
What a good endpoint looks like. Pagination, and why the obvious way to paginate breaks at scale. You'll build both ways and watch one of them die.

### Day 6 (Wed) — More than one server
Load balancers, health checks, what "stateless" means and why everyone insists on it. You'll run three copies of an app behind a load balancer and kill one while it's serving traffic.

### Day 7 (Thu) — Your first real design
No new material. You design a URL shortener from scratch, write it up, and then we compare it against what you would have written on Monday.

## Reading for the week

All free:
- The interactive latency table: colin-scott.github.io/personal_website/research/interactive_latency.html
- *High Performance Browser Networking* by Ilya Grigorik, free at hpbn.co. Chapters 1 and 2 only, and only in week 1.
- The "What happens when you type google.com" GitHub repo (search it, you'll find it immediately)

One paid book, and it's the only one I'll push you to buy this month:
- Martin Kleppmann, *Designing Data-Intensive Applications*. This week you read chapter 1 and nothing else. We live in this book during weeks 2 through 5. It is genuinely the best technical book of the last decade and it will still be useful to you in ten years.

## What beginners get wrong this week

Two things.

They memorize the latency numbers as facts to recite, instead of internalizing the ratios. Nobody will ever ask you "how many nanoseconds is an L1 cache reference." They will ask you "should this be cached," and you answer that by comparing two numbers.

And they think estimation requires precision. It doesn't. If your napkin math says "about 50,000 requests per second" and the truth is 30,000, you made the right decision anyway, because both numbers say the same thing: too much for one machine, and you need a cache. The estimate exists to pick a design, not to be correct.
