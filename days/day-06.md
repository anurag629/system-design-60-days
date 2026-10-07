---
title: "Day 6: more than one server"
parent: "Week 1: ground truth"
nav_order: 6
has_children: true
---

# Day 6, Sunday 2026-09-27
## More than one server, and killing one while it serves traffic 🔀

Today's one idea: putting a load balancer in front of a few servers is the easy part. The real work is what happens when one of those servers dies at 2 am. Whether your users even notice comes down to two things: does the balancer find out the server is dead, and does it try somebody else. Today you build the whole thing and kill a server on purpose to watch both.

This is the day week 1 stops being about one machine. Everything from here on, storage, caching, queues, all of it, assumes many machines and the certainty that some of them are broken right now.

---

## Before you start ⏪

Day 4's queue lesson is the backbone of today. "Don't send work to the server that can't keep up" is going to come back as a load balancing algorithm. If Day 4's cliff is fuzzy, skim your own `day-04-queues/RESULTS.md` for two minutes first.

The lab runs three real web servers and a real balancer on your laptop, all at once. Nothing is simulated. It needs no installs and no internet.

---

## Words you will meet today 📖

A load balancer is one server that sits in front of many others and spreads incoming requests across them. Clients talk to one address. Behind it, any number of servers share the work.

A backend, also called an upstream, is one of the servers behind the balancer, the ones actually doing the work.

Stateless means a server keeps nothing important in its own memory between requests. Every request carries, or looks up, whatever it needs. This is what lets any backend handle any request, which is the whole reason load balancing works. A server that remembers your shopping cart in its own RAM is stateful, and it breaks the moment a second server appears.

A health check is the balancer periodically asking each backend "are you alive?", usually by hitting a cheap endpoint like `/health`. An active health check means the balancer probes on a timer. A passive one means the balancer notices failures on real traffic. Today's lab uses active checks.

Round robin is the simplest way to pick a backend: go round the list in order, one each, over and over.

Least connections picks the backend currently handling the fewest requests. It steers around a server that is bogged down, which round robin cannot do.

L4 versus L7: a layer 4 balancer routes by IP and port without looking inside the request, which is fast and dumb. A layer 7 balancer reads the HTTP request and can route on the path, the headers, the cookie, which is slower and smart. Today's balancer is L7, because it reads the request and proxies it.

Connection draining, or graceful shutdown, is letting a server finish its in-flight requests before you take it out, instead of cutting them off mid-sentence.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Load balancing, visually](https://samwho.dev/load-balancing/) by Sam Rose. An interactive essay where you watch round robin, least connections and the rest handle traffic in real time. The best thing on the internet for this, and it is the whole lab before you build it.
- [Implementing health checks](https://aws.amazon.com/builders-library/implementing-health-checks/) from the AWS Builders' Library. The subtle one: how a health check that is too clever can take down your whole fleet at once.
- [The Twelve-Factor App: processes](https://12factor.net/processes). Short. Why your app servers must be stateless, said plainly.

Watch, after the lab:
- [Layer 4 vs Layer 7 load balancer](https://www.youtube.com/watch?v=O_DfHBPYLTA) by IT k Funde, 12 minutes. The one distinction the lab does not cover, explained well.
- Optional: [Load balancing algorithms explained](https://www.youtube.com/watch?v=F-LgiRxMsB0) by AK Coding, 10 minutes, if you want the algorithms spelled out beyond the samwho essay.

### One address in front, many servers behind (10 min)

A single server has a ceiling. From Day 4 you know it is not even 100% of capacity, it is more like 70% before latency starts climbing the wall. So you add more servers. But clients cannot be expected to know about five servers and pick between them. They want one address. The load balancer is that one address. It takes each request and hands it to one of the backends.

For this to work, any backend has to be able to handle any request. That is what stateless means, and it is not a nice-to-have, it is the whole foundation. The moment a server stashes something in its own memory that the next request needs, say your login session or your cart, you are in trouble, because the balancer might send your next request to a different server that has never heard of you. The fix is to keep that state somewhere shared that all servers can reach, a database or a Redis, which is exactly what weeks 2 and 3 are about. Keep the app servers dumb and identical, and you can add, remove or lose one without anybody noticing.

### How the balancer picks a backend (10 min)

The simplest rule is round robin: first request to server 1, next to server 2, next to server 3, then back to server 1. Even, predictable, and fine when every request costs about the same and every server is equally healthy.

It falls apart the moment one server is slower than the others, say it is doing a garbage collection pause or it is an older machine. Round robin keeps calmly sending it one request in three, and those requests pile up behind the slow work, exactly the Day 4 queue filling up. The server gets slower, the queue gets longer, and round robin does not care.

Least connections fixes this. The balancer counts how many requests each backend is currently handling and sends the next one to whoever has the fewest. A bogged-down server is holding lots of in-flight requests, so it stops receiving new ones until it catches up. This is Day 4's "one shared line beats many separate lines" wearing a load balancer costume. The lab's Part 3 makes a slow server and shows you round robin and least connections handling it side by side. The gap is bigger than you would guess.

### The part that actually matters: failure (10 min)

Here is the thing nobody teaches properly. A balancer spreading load across healthy servers is easy. What earns its keep is the day a server dies.

When a backend crashes, the balancer does not magically know. If it keeps round-robining, one request in three (with three servers) gets routed into a dead socket and fails. And it keeps failing, forever, because nothing told the balancer to stop. That is the default, and it is grim.

The first fix is the active health check. The balancer probes every backend every so often, say every 200 milliseconds, and the instant a backend stops answering, it is pulled out of the rotation. Now the failures only last from the crash until the next probe notices, the error window. Shorten the probe interval and the window shrinks, but you pay for it: more probe traffic, and under load a slow-but-alive server can fail a probe and get yanked out when you needed it. The AWS reading is all about that trap.

The second fix is retry. If a request to a backend fails, the balancer quietly tries a different one before giving up on the user. Combined with health checks, this takes the user-visible errors during a crash down to almost nothing. There is one rule, straight from Day 5: only retry requests that are safe to retry. Retrying a read is free. Retrying "charge the card" without an idempotency key charges twice. And one caution, which week 7 returns to: if every client retries hard at the same moment, the retries themselves become a flood that finishes off a struggling fleet. Retry with care.

The lab runs the same crash three times: no health check, health check, and health check with retry. Same crash, three completely different days for your users.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-06-drills.md`](../notes/day-06-drills.md). Day 4's `latency = work / (1 - utilization)` comes back in D5.

D1. You run four app servers behind a balancer, each able to handle 100 requests per second. Peak traffic is 300 per second. One server dies. Can the other three carry the peak? What does Day 4 say about how it feels at that load? Now peak is 350 per second and one dies. What happens?

D2. You set the health check interval to 30 seconds to keep probe load low. A server crashes 1 second after a check passed. Roughly how long does the balancer keep feeding it traffic? With four servers, about what fraction of all requests fail during that window? What does shrinking the interval cost you?

D3. Your app keeps each user's shopping cart in the memory of whichever server took their first request. You add a load balancer and a second server. What breaks, and why? Give two different fixes, and say which one survives a server dying.

D4. Three backends. One hits a two-second garbage collection pause. Describe what round robin does with the requests aimed at it during those two seconds. Describe what least connections does instead. Which do you want for an API where some requests are much heavier than others?

D5. Ten servers behind a balancer, each running at 70% busy. One dies and its share spreads evenly over the other nine. What is their new utilization? Using Day 4's formula, how much worse does average latency get? Now redo it assuming they were at 90% busy when one died. What happens, and what is the lesson about how hot you should run?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-06-load-balancer/load_balancer_lab.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-06-load-balancer/load_balancer_lab.py).

It starts three real HTTP servers and a real load balancer on your machine, drives them with 20 concurrent clients, and does three things. Part 1 shows the balancer spreading load evenly. Part 2 kills a backend 1.5 seconds into the run, three times over, with no health check, then a health check, then a health check plus retry, and measures how many requests fail each way. Part 3 makes one backend slow and races round robin against least connections.

Standard library only. The lab runs a self-check first and tells you exactly which TODO is missing, so it can never hang on you. About 30 seconds to run, most of it real time while load flows.

### Predict first

Fill in `PREDICTIONS` at the top of the file. Three backends, so each normally gets a third of the traffic.

- P1. With no health check, after you kill one of the three backends, what percentage of requests fail?
- P2. With a health check every 200 ms, how many milliseconds do errors last after the crash before they stop?
- P3. With health check plus retry, roughly how many user-visible errors in total?
- P4. With one backend 6x slower, how many times more requests does least connections complete than round robin?

P1 is reasoning, not guessing: three servers, one dead, nothing noticing. P2 is almost given once you know the probe interval. P4 is the one people underestimate.

### Fill in the TODOs

1. TODO 1 is round robin: step to the next backend and wrap around.
2. TODO 2 is least connections: pick the backend with the fewest requests in flight.
3. TODO 3 is the health probe: return True only if `/health` answers 200.
4. TODO 4 is the self-healing line: drop a backend from the pool when its probe fails, add it back when it recovers.

```bash
cd labs/day-06-load-balancer
python3 load_balancer_lab.py
```

### What you're going to discover

Part 1 is calm: three backends, a third of the traffic each. Good, that is the balancer doing its basic job.

Part 2 is the lesson. With no health check, about a third of all requests fail after the crash and they never stop, because the balancer keeps serving a corpse. Turn on health checks and the failures stop within about one probe interval, a couple of hundred milliseconds. Add retry and the user-visible errors drop to single digits or zero, because a failed request silently lands on a healthy backend. Same crash, every time. Only the balancer's smarts changed.

Part 3 is the Day 4 callback. The slow backend drags round robin down, because a third of the traffic queues behind it. Least connections completes meaningfully more requests, often more than one and a half times as many, by sending the slow server less.

### Traps ⚠️

- This lab uses real threads and real sockets, so the numbers wobble between runs. The shape is rock solid, the third decimal is not. Run it twice.
- The error window depends on the probe interval, which is 200 ms here. If your machine is busy, a probe can be slow and the window a bit wider. That is honest, not a bug.
- If the lab says a TODO is missing, it means the self-check caught an unfilled one before running. Fill it and rerun. It will not hang.
- Part 2's "no health check" window prints "never stopped" on purpose. The errors genuinely run to the end of the test, because nothing ever removes the dead backend.

### Deliverable

[`labs/day-06-load-balancer/RESULTS.md`](../labs/day-06-load-balancer/RESULTS.md) has a skeleton. Paste the output and write one line answering the real question: for the same crash, how many requests failed with nothing, and how many with health checks plus retry?

---

## Block 4: write (30 min) 📣

Your angle today is the crash: "I ran three servers behind a load balancer and killed one mid-traffic. With no health check, a third of requests failed and never recovered. With health checks and retry, almost none did. Same crash." The three-row table from Part 2 is the whole post. The least connections throughput result from Part 3 makes a good second one.

Example posts, written with the reference run's numbers, are on the [Day 6 posts](../shares/day-06-posts.md) page. Swap in your numbers and write them in your voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Add a Day 6 entry to your progress log with these three things:

1. What you completed, and what you skipped.
2. Your Part 2 numbers: failed requests with nothing, versus with health checks and retry.
3. One thing you still can't explain.

Then compare your work with the solutions below. Day 7 is the end of week 1: no new material, you design a URL shortener from scratch and we hold it up against what you could have drawn on day 2.

---

## Solutions 🔑

Open these only after you've done the day. Reading answers first feels like learning and isn't.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Four servers at 100 each is 400 capacity. Peak is 300. One dies, leaving 300 capacity for 300 of traffic, so it fits, but it fits at 100% busy, and Day 4 says 100% busy is a wall: the queue grows without bound and latency goes through the roof. So "yes, technically, and your users have a terrible time." At 350 peak, three servers give 300 against 350 arriving, which is over capacity: the queue grows forever and requests start timing out and failing. The lesson is to plan for N minus 1, enough servers that losing one still leaves comfortable headroom, not a server running flat out.

D2. Worst case the crash happens right after a check, so the balancer keeps feeding it for almost the full 30 seconds until the next probe. With four servers it is sending a quarter of all traffic into the dead one, so about 25% of requests fail for roughly 30 seconds. Shrinking the interval shrinks that window, which is why the lab uses 200 ms, but shorter intervals mean more probe traffic hitting every server, and under load a healthy-but-slow server can miss a probe and get pulled out exactly when you need it. The AWS reading is about that failure mode.

D3. With the cart in one server's memory, the second request can land on the other server, which has never seen the cart, so the cart looks empty or lost. Fix one: sticky sessions, where the balancer always routes a given user to the same server. It works until that server dies, and then the cart is gone, so it does not survive failure. Fix two: move the cart out of the server into a shared store like Redis or the database, so any server can serve any request. That one survives a server dying, which is why "make the app servers stateless" is the rule.

D4. Round robin keeps sending the slow server one request in three through the whole two-second pause, and they stack up in its queue behind the stuck work, so those users wait the full pause plus their queue time. Least connections sees the slow server's in-flight count climbing and stops sending it new work until it recovers, so almost all traffic flows to the two healthy servers. For an API with uneven request costs, you want least connections (or least response time), because round robin is blind to how loaded each server actually is.

D5. Ten servers at 70% means 7.0 server-loads of work. One dies, the 7.0 spreads over nine, so each is at 7.0 / 9 = 77.8% busy. Day 4's factor goes from 1 / (1 - 0.70) = 3.33x to 1 / (1 - 0.778) = 4.5x, so average latency gets about 35% worse. Survivable. Now at 90%: that is 9.0 server-loads over nine survivors, which is 100% each, and 1 / (1 - 1.0) is infinite: the survivors cannot absorb the load and the whole thing melts, one death cascading into total failure. The lesson is that the hotter you run, the less slack you have to absorb a failure. Running at 60 to 70% is not waste, it is the room that lets you lose a server and live.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-06-load-balancer/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-06-load-balancer/solution.py).

TODO 1, round robin:

```python
state["rr"] = (state["rr"] + 1) % len(healthy)
return healthy[state["rr"]]
```

TODO 2, least connections. The whole idea is in the key function:

```python
return min(healthy, key=lambda b: inflight[b.name])
```

TODO 3, the health probe:

```python
try:
    c = http.client.HTTPConnection("127.0.0.1", backend.port, timeout=0.2)
    c.request("GET", "/health")
    r = c.getresponse()
    ok = r.status == 200
    r.read(); c.close()
    return ok
except Exception:
    return False
```

TODO 4, the self-healing line, inside the health sweep:

```python
if ok and b not in self.healthy:
    self.healthy.append(b)
if not ok and b in self.healthy:
    self.healthy.remove(b)
```

That second `if` is the entire difference between the "never stopped" row and the "170 ms" row in Part 2. One line decides whether your balancer serves a corpse.

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. Real threads and sockets, so your numbers will wobble. The shape will not.

```
Part 1: three healthy backends, round robin
  backend-0:   689 requests  (33.3%)
  backend-1:   689 requests  (33.3%)
  backend-2:   688 requests  (33.3%)

Part 2: kill one of three backends 1.5 s in
  config                               errors  fail% after   error window
  no health check, no retry              1724        33.2%  never stopped
  health check every 200 ms                99         3.0%         149 ms
  health check + retry                      9         0.3%         123 ms

Part 3: one backend is 6x slower
  algorithm           completed   p99 ms  sent to slow
  round robin              1972       68           657
  least-connections        3157       69           272

Scoreboard
  P1 fail% after kill, no health   actual =     33.2 %
  P2 error window with health      actual =    149 ms
  P3 user errors with retry        actual =      9
  P4 leastconn / rr throughput     actual =      1.6 x
```

Part 1 is the sanity check: a third each. If yours is lopsided, your round robin is wrong.

Part 2 is the day. Read the three rows top to bottom. With no health check, a third of everything fails from the crash to the end of the test, because the balancer never finds out. Turn on the probe and errors stop 149 ms after the crash, which is about one 200 ms interval, exactly as predicted. Add retry and 9 requests out of several thousand failed, a rounding error, because the failed ones quietly retried onto a live backend. The crash was identical all three times. The only thing that changed was whether the balancer noticed and whether it tried again.

Part 3 is Day 4 again. Round robin finished 1,972 requests and shoved 657 of them at the slow backend, where they queued. Least connections finished 3,157, over 1.6x more, and sent the slow one only 272, because it could see the slow backend hoarding in-flight requests and routed around it. Same three servers, same slow one. The smarter rule did 60% more work.

The number I keep from today: same crash, 1,724 failed requests versus 9. The failure was never the question. Noticing it and retrying was.

</details>
