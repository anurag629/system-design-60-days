---
title: "Day 46: multi-tenancy and isolation"
parent: "Week 7: production"
nav_order: 4
has_children: true
---

# Day 46
## Multi-tenancy and the noisy neighbour, where one greedy customer ruins it for everyone 🏘️

Today's one idea: when many customers share one system, they also share one fate, unless you build walls between them on purpose. One tenant with a bad deploy, a retry storm, or just a very big workload can eat the shared capacity and starve everyone else, and the starved tenants did nothing wrong. The fix is isolation: a per-tenant quota, fair scheduling, or in the extreme a dedicated box each. Today you make one greedy tenant collapse the throughput of five well-behaved ones on your own laptop, then you put a limiter in and watch the five come back.

This is week 7, the production plumbing. It is not a clever algorithm. It is the difference between a SaaS that quietly serves a thousand customers and one where customer number 847 runs a bad query and the other 999 all get paged.

---

## Before you start ⏪

Bring Day 45. The quota you add today is a token bucket, the exact rate limiter you built for rate limiting, now pointed at one tenant each instead of one global limit. Bring Day 27 too (backpressure and load shedding): the noisy neighbour is an overload problem, and saying no to the greedy tenant is load shedding aimed by tenant. And keep Day 48 in the corner of your eye, because the last part of today ends on cost, and cost is what decides how much isolation you can actually afford.

If "shared pool", "fair share" and "token bucket" are fresh, you are ready. The lab is a pure simulation, so Day 2's Python is plenty.

---

## Words you will meet today 📖

A tenant is one customer of a shared system: one company on your SaaS, one team on your internal platform, one account whose requests and data must stay logically separate from the others.

Multi-tenancy is many tenants sharing the same running system and its resources, instead of each getting their own copy. It is cheaper to run, and it is why almost every SaaS is built this way.

The noisy neighbour is the tenant whose workload spikes and eats the shared capacity, degrading everyone else. The name is the flatmate who plays loud music at 2 AM: they are not necessarily malicious, they are just using more than their share of a shared thing.

A quota, or per-tenant limit, is a cap on how much of the shared resource one tenant may use, enforced before its requests reach the shared pool. A token bucket per tenant is the usual way to do it.

Fair-share scheduling serves the shared resource so that every tenant gets at least its fair share whenever it wants, and spare capacity is handed to whoever is still hungry. Max-min fairness is the ideal; weighted fair queuing and round-robin are the practical approximations.

Work conserving describes a scheduler that never leaves the resource idle while anyone has work waiting. A hard quota is not work conserving (it can leave capacity unused); fair scheduling is.

The isolation spectrum runs from shared everything (one pool, no walls, cheapest, worst isolation), through shared with per-tenant quotas (the usual middle), to dedicated resources per tenant (a box each, best isolation, highest cost).

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Fairness in multi-tenant systems](https://aws.amazon.com/builders-library/fairness-in-multi-tenant-systems/), from the AWS Builders' Library. The best single piece on today: why admission control per tenant beats a global limit, how to pick a fair share, and the traps (a tenant gaming per-ID buckets, bursty-but-legitimate load). Read this one slowly.
- [Handling overload](https://sre.google/sre-book/handling-overload/), from the Google SRE book. The overload framing behind the noisy neighbour: per-customer limits, graceful degradation, and why a system must be able to say no before it falls over. Short and sharp.
- [Isolation, security, or noisy neighbor?](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/isolation-security-or-noisy-neighbor.html), from the AWS SaaS tenant isolation whitepaper. This is the isolation spectrum laid out as silo, pool and bridge models. Part 3 of the lab in prose.

Watch, after the lab:
- [Multi-tenancy architecture](https://www.youtube.com/watch?v=IhrBgoVIoT4) by Hussein Nasser, about 25 minutes. A calm walk through what multi-tenancy is, the pooled-versus-isolated trade-off, and where the noisy neighbour bites. The same voice from the storage week.
- Optional, for a quick overview first: [The Ultimate Guide to Multi-Tenancy in 5 minutes](https://www.youtube.com/watch?v=ZYuu8sWUQww) by ByteMonk, about 6 minutes. A tight tour of the isolation models if you want the shape before the detail.

### Why we share, and the bill it saves (12 min)

Start with why multi-tenancy exists at all, because the noisy neighbour is the price of a thing that is otherwise a very good idea.

Imagine you run a SaaS with a thousand customers. You could give each customer their own server, their own database, their own everything. Clean, fully isolated, and ruinously expensive, because most customers are idle most of the time. A customer who sends traffic for eight hours a day and sleeps the other sixteen is paying for a machine that sits dark two thirds of the time, and you are the one buying that machine. Multiply by a thousand and you have bought three times the hardware you actually need, because the peaks do not all line up.

So instead you pool them. One fleet of servers, one shared database tier, and all thousand customers ride on top. Now when customer A is busy and customer B is asleep, A quietly uses the capacity B is not touching. This is statistical multiplexing, the same reason an ISP can sell more bandwidth than it owns: not everyone peaks at once, so the shared pool sized for the aggregate is far smaller than a thousand private boxes. The bill drops, maybe by that factor of three, and that saving is the whole business case for building SaaS this way.

But you have also just tied a thousand fates together. The pool that lets A borrow B's idle capacity is the same pool that lets A eat B's needed capacity when A goes haywire. The flatmate who shares your kitchen is lovely until the night they cook for forty people and you cannot get to the stove. That is the deal you made when you pooled, and the rest of today is about getting the saving without the 2 AM paging.

### The noisy neighbour, and why the shared queue betrays you (14 min)

Here is the part you will measure. Picture one shared resource that can handle 120 requests per tick, shared by 6 tenants. An even split is 20 each. When every tenant asks for its 20, total demand is 120, exactly the capacity, and everyone is served in full. Lovely. The pool is doing its job.

Now one tenant floods. Not out of malice, usually: a retry loop after a failure, a batch job someone scheduled badly, a genuinely large customer who tripled overnight. It starts asking for 600 requests per tick instead of 20. Total demand is now 700 against a pool that can serve 120. Something has to give, and the cruel part is who it gives from.

A plain shared queue, first come first served, has no idea which tenant a request belongs to. It just serves the front of the line. And if the greedy tenant is putting 600 requests into that line for every 20 a quiet tenant puts in, then the line is mostly greedy requests, so the service the pool hands out ends up roughly proportional to how much each tenant demanded. The greedy tenant asked for 600 of the 700, so it gets about 600/700 of the capacity, around 103 of the 120. Each quiet tenant asked for 20 of the 700, so it gets about 20/700 of the capacity, around 3.4. That quiet tenant wanted 20, deserved 20, changed nothing about its own behaviour, and now gets 3.4. Over 80 percent of its requests are turned away, and the ones that are not sit in a growing queue and blow past the client's timeout. Its throughput collapsed and its latency exploded, because of someone else.

Notice the shape of the betrayal. The shared queue is not broken; it is behaving exactly as designed, serving requests in order. The design simply has no notion of fairness between tenants, so "serve the front of the line" quietly means "reward whoever shouts loudest". More shards or more servers do not save you either, because one greedy tenant scales its flood right along with you. The problem is not capacity. The problem is that nothing is counting per tenant.

### Three ways to build the wall (16 min)

The fix is to make the system tenant-aware, and there are three levels of it.

The first and most common is a per-tenant quota. You put a rate limiter, a token bucket from Day 45, in front of each tenant, refilling at that tenant's fair share of 20 per tick. Now the greedy tenant's flood hits its own bucket first: 20 requests find tokens and go through, the other 580 find the bucket empty and are rejected right there, a 429 at the door, before they ever reach the shared pool. The pool now sees 20 from the greedy tenant and 20 from each of the others, total 120, exactly capacity, no overload. Every quiet tenant is back to its full 20. The greedy tenant is held to exactly what it is owed. This is the IRCTC tatkal logic turned per customer: the counter will serve you your quota of tickets and not let you shove the whole queue aside, no matter how many times you refresh.

The quota is simple and predictable, but it has one honest flaw: it is not work conserving. Set every tenant's cap at 20, and if one tenant is idle, its 20 just evaporates. The pool runs under capacity while the greedy tenant, who could happily use that idle slice, is pinned at its cap. You protected the quiet tenants and wasted the slack.

So the second level is fair-share scheduling. Instead of a hard cap, you schedule the shared pool by max-min fairness: give every tenant its fair share first, then hand whatever is left to whoever is still hungry. Under the flood this looks the same, everyone gets 20. But when a tenant goes idle, its share is not wasted, it is lent to the greedy tenant, which soaks up the genuinely spare capacity. The pool stays full, yet an active quiet tenant can never be starved, because its fair share is guaranteed before any leftover is shared out. This is what weighted fair queuing and deficit round robin approximate in real routers and schedulers. The cost is that it is more complex to build than a flat cap, which is why most real systems run a quota for the hard ceiling and fair scheduling for the work-conserving middle, together.

The third level is to stop sharing. Give every tenant its own box of 20 per tick and nothing else. Now the greedy tenant is physically walled off: it cannot exceed its box no matter what, which is the strongest isolation you can buy. But it also cannot borrow a neighbour's idle box, so all the statistical-multiplexing saving you built multi-tenancy for is gone. You are back to provisioning and paying for everyone's peak at once. Best isolation, highest bill.

That is the isolation spectrum, and it is a dial, not a switch. Shared everything is cheapest and least safe. Dedicated per tenant is safest and dearest. Shared with quotas and fair scheduling is the pragmatic middle where most SaaS lives, and exactly where on that dial you sit is a money question. That is Day 48.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Then copy your answers into [`notes/day-46-drills.md`](../notes/day-46-drills.md). About 8 minutes each.

D1. A shared pool serves 120 req/tick across 6 tenants. Five ask for 20 each, the greedy one floods with 600. Under proportional service, how many req/tick does a quiet tenant get, what fraction of its demand is that, and how much does the greedy tenant get?

D2. You put a token bucket in front of every tenant at the fair share. What rate do you set, how many of the greedy tenant's 600 req/tick now reach the pool, and what does the quiet tenant's served rate become? Where do the rejected requests go?

D3. One quiet tenant goes idle and sends nothing. Under a hard quota at the fair share, how much of the 120-capacity pool is actually used and what is wasted? Under max-min fair scheduling, where does the idle tenant's share go, and which property is the fair scheduler buying you?

D4. Rank the three models, shared-everything, shared-with-quota, dedicated-per-tenant, by isolation and by cost. For the dedicated model, why can idle capacity in one tenant's box not help a busy neighbour, and what does that do to the bill as the tenant count grows?

D5. A metrics SaaS runs 1,000 tenants on one shared ingestion pipeline sized for the aggregate. One tenant 100x's its write rate after a bad deploy. Without isolation, what do the other 999 tenants experience? Name the first control you would add and say whether it sits at admission or in the scheduler, and name one per-tenant metric that would have caught it early.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-46-multitenancy/multitenancy.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-46-multitenancy/multitenancy.py).

It is a pure simulation, standard library only, and it runs in well under a second. A shared resource serves 120 requests per tick, 6 tenants share it. Part 1 floods the pool with one greedy tenant and measures what the quiet tenants lose. Part 2 adds a per-tenant token bucket (the quota) and then fair-share scheduling, and measures the quiet tenants coming back. Part 3 lays out the isolation spectrum and ties it to cost.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The flood, no isolation. A well-behaved tenant asks for its fair share of 20 per tick while the greedy tenant floods with 600. How many requests per tick does the well-behaved tenant actually get served?
- P2. Same flood, no isolation. How many per tick does the greedy tenant get served? (Capacity is 120, its fair share would be 20.)
- P3. Now a per-tenant quota at the fair share, same flood. What is the well-behaved tenant's served rate now?
- P4. Same quota run. What is the greedy tenant capped at?

P1 is the one to feel in your gut first. The quiet tenant wanted 20 and did nothing wrong. Write down what you think it actually gets while the neighbour floods. Most people guess "a bit less". It is a lot less.

### Fill in the TODOs

1. TODO 1 is the fair share, `capacity // n`. The yardstick everything else is measured against, and the rate you hand each tenant's limiter.
2. TODO 2 is proportional service, `capacity * demand / total_demand`. One line, and it is the whole noisy-neighbour effect: a shared pool with no accounting serves you in proportion to how loud you are.
3. TODO 3 is the token bucket's admit step, refill then let through as many as there are tokens. This is the quota that both caps the greedy tenant and protects the quiet ones.
4. TODO 4 is the dedicated model, `min(demand, capacity // n)`. You get your own box and not one request more, which is the best isolation and the most wasted slack.

```bash
cd labs/day-46-multitenancy
python3 multitenancy.py
```

### What you're going to discover

Part 1 is the gut punch. The baseline is calm: every tenant asks for 20, the pool serves 120, everyone is whole. Then one tenant floods with 600 and the well-behaved tenant drops to about 3.4 per tick, a fall of over 80 percent, while the greedy tenant alone eats about 103 of the 120. The sweep underneath shows it getting steadily worse the louder the neighbour gets. Nothing refused the flood, because nothing was counting per tenant.

Part 2 is the relief. Put a token bucket at the fair share in front of each tenant and re-run the identical flood. The quiet tenant snaps back to 20, the greedy tenant is pinned at 20, and its other 580 per tick are rejected at the door before they ever load the pool. Then the fair-scheduling twist: when a tenant goes idle, the hard quota wastes its share while max-min fair scheduling lends it to the greedy tenant, keeping the pool full without ever starving an active tenant. Two tools, one simple and one work conserving, usually run together.

Part 3 is the spectrum on one screen: shared with no limits (Part 1), shared with a quota (Part 2), and dedicated per tenant, scored by isolation and by cost. Dedicated walls the greedy tenant off completely but throws away the multiplexing saving, which is exactly the cost conversation for Day 48.

### Traps ⚠️

- The model serves the overloaded pool in proportion to demand. That is a fair model of a shared first-come-first-served queue under sustained overload, not a claim that every real queue is exactly proportional. The lesson is the direction and the size of the collapse, not the third decimal.
- The token bucket's burst is set equal to its rate here, so there is no saved-up burst and the steady-state admit is clean. In a real limiter you would allow a small burst, which smooths bursty-but-legitimate tenants. That is a knob, not a contradiction.
- The idle-tenant comparison is the subtle one. Both the quota and fair scheduling protect the quiet tenants under the flood. They differ only when there is genuine slack: the quota wastes it, fair scheduling lends it out. Do not conclude the quota is useless; it is the hard ceiling that fair scheduling alone does not give you.
- Dedicated shows the greedy tenant at 20 here only because its box is 20. The point is not the number, it is that it physically cannot exceed its box and cannot borrow anyone else's, so idle capacity is simply lost.

### Deliverable

[`labs/day-46-multitenancy/RESULTS.md`](../labs/day-46-multitenancy/RESULTS.md) has a skeleton. Paste the output, and write one line: how far did the well-behaved tenant's throughput fall under the flood, and how much of it did the quota give back?

---

## Block 4: write (30 min) 📣

Your angle today is the measured injustice: "I watched one greedy tenant on a shared system drop a well-behaved tenant's throughput by over 80 percent, from 20 requests per tick to 3.4, and the well-behaved tenant did nothing wrong. Then a per-tenant quota, the same rate limiter from yesterday, gave it all back and pinned the greedy one at its fair share." The scoreboard, 20 to 3.4 to 20, is the screenshot.

Example posts are on the [Day 46 posts](../shares/day-46-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, how far the well-behaved tenant's throughput fell under the flood and how much the quota restored, and one thing you still cannot explain.

Day 47 is security boundaries, the parts that touch design: authentication versus authorisation, where secrets live, and signing a request so it cannot be forged. Today you kept one tenant from stealing another's capacity. Tomorrow you keep one tenant from reading another's data, which is the harder wall and the one you really cannot get wrong.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Total demand is 5 times 20 plus 600, which is 700, against a pool of 120. Proportional service gives each tenant capacity times its share of demand. A quiet tenant: 120 times 20/700, about 3.4 req/tick, which is 3.4 out of the 20 it wanted, roughly 17 percent (so about 83 percent turned away). The greedy tenant: 120 times 600/700, about 102.9 req/tick, so one tenant eats around 86 percent of a pool it is entitled to one sixth of. That gap is the noisy neighbour.

D2. You set each bucket's rate to the fair share, 120/6 = 20 req/tick. The greedy tenant's bucket refills 20 tokens per tick, so 20 of its 600 requests find a token and reach the pool and the other 580 find the bucket empty and are rejected at the door (a 429), before they ever touch the shared pool. The quiet tenant asks for 20, has 20 tokens, so all 20 go through: it is back to its full 20 req/tick. The rejected requests do not queue in the pool, which is the point, the flood is shed at the tenant's own limiter so the shared resource never sees it.

D3. Capacity 120, one quiet tenant idle (0), four quiet tenants at 20, greedy flooding. Under a hard quota at the fair share, each tenant is capped at 20: the four active quiet tenants get 20 each (80), the greedy tenant is pinned at 20, and the idle tenant's 20 is simply unused. The pool serves 100 of its 120, so 20 is wasted. Under max-min fair scheduling, the idle tenant's share is handed to whoever is still hungry: the four quiet tenants still get their 20 each, and the greedy tenant soaks up the leftover, reaching 40, so the pool runs full at 120. The property the fair scheduler buys you is work conservation: it never leaves the resource idle while someone has work waiting, without ever starving a tenant below its fair share.

D4. Isolation, worst to best: shared-everything (no walls, Part 1 happens), shared-with-quota (the greedy tenant is capped, quiet tenants protected), dedicated-per-tenant (a physical box each, nothing can cross). Cost, cheapest to dearest, is the same order reversed: shared-everything is one pool, shared-with-quota adds only a cheap meter per tenant, dedicated needs a box per tenant. For dedicated, idle capacity in one box cannot help a busy neighbour because the boxes are separate resources with no shared queue to lend from, so you lose statistical multiplexing and must provision every tenant's peak at once. As the tenant count grows, the bill grows close to linearly with tenants rather than with aggregate load, which is why dedicated is reserved for the tenants who pay for it or legally require it.

D5. Without isolation, the one tenant's 100x write burst floods the shared ingestion pipeline, and the other 999 tenants see their ingestion throughput collapse and their write latency climb as the shared queue fills; some of their writes time out and are dropped, and they get paged for a problem they did not cause. The first control is a per-tenant admission limit (a token bucket or concurrency cap keyed by tenant), which sits at admission, before the shared pipeline, so the burst is shed at the door rather than loading the pipeline. The per-tenant metric that catches it early is per-tenant request or write rate (or per-tenant share of pipeline capacity), so a single tenant crossing its share lights up immediately instead of hiding inside a healthy-looking aggregate.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-46-multitenancy/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-46-multitenancy/solution.py).

TODO 1, the fair share, the yardstick and the limiter's rate:

```python
return capacity // n
```

TODO 2, proportional service, the entire noisy-neighbour effect in one line:

```python
return capacity * demand / total_demand
```

TODO 3, the token bucket's admit step, refill then let through what there are tokens for:

```python
self.tokens = min(self.tokens + self.rate, self.burst)
admitted = min(int(self.tokens), demand)
self.tokens -= admitted
return admitted
```

TODO 4, the dedicated model, your own box and not one request more:

```python
return min(demand, capacity // n)
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. The simulation is deterministic, so your numbers should match to the decimal.

```
==============================================================================
Part 1: the noisy neighbour. One shared pool, no limits, one bad actor.
==============================================================================
  The shared resource serves 120 requests per tick.
  6 tenants share it. An even split is 20 req/tick each (the fair share).

  Baseline, everyone well-behaved (20 req/tick each, 120 total):
    every tenant served 20.0/20  (demand = capacity, nobody is starved)

  Now the greedy tenant floods: it asks for 600/tick, the quiet ones
  still ask for 20. Total demand is 700 for a 120-req/tick pool.
    well-behaved tenant served:   3.4/tick  (wanted 20, 83% turned away)
    greedy tenant served:       102.9/tick  (it alone eats 86% of the pool)

  The quiet tenant did nothing wrong and its throughput fell off a cliff.
  A shared queue serves whoever fills it, so the flood crowds everyone
  else out. The requests that are turned away pile up and time out: that
  is the latency collapse behind the throughput number.

  Watch the quiet tenant sink as the neighbour gets louder:
     greedy demand  quiet served  greedy served
                20          20.0           20.0
                60          15.0           45.0
               120          10.9           65.5
               300           6.0           90.0
               600           3.4          102.9
              1200           1.8          110.8
  More flood from one tenant, less for each of the other five. No amount
  of flooding is refused, because nothing is counting per tenant.

==============================================================================
Part 2: contain the neighbour. A per-tenant quota, then fair scheduling.
==============================================================================
  Fix one: a token bucket in front of each tenant, refilling at the
  fair share (20 req/tick). Re-run the exact same flood.
    well-behaved tenant served:  20.0/tick  (back to its full share)
    greedy tenant served:        20.0/tick  (capped at its share)
    greedy requests rejected:     580/tick  (429 at the door, never hit the pool)
  The limiter turns the flood away before it reaches the shared pool, so
  the pool is no longer overloaded and the quiet tenants are whole again.
  The greedy tenant is held to exactly what it is entitled to.

  Fix two: fair-share (max-min) scheduling of the pool itself, no hard cap.
    well-behaved tenant served:  20.0/tick
    greedy tenant served:        20.0/tick
  Same protection under this flood. The difference shows when a tenant
  goes idle and leaves slack on the table:

    one quiet tenant idle (sends 0); greedy still flooding 600:
                            quiet active    greedy   pool used
      hard quota                    20.0      20.0        100/120
      fair scheduling               20.0      40.0        120/120
  The hard quota protects the quiet tenants but wastes the idle share
  (greedy stays pinned at its cap, pool runs under capacity). Fair
  scheduling hands that idle share to the greedy tenant instead, so the
  pool stays full, yet an active quiet tenant can never be starved. That
  is the real trade: a hard cap is simple, fair scheduling is work
  conserving. Most real systems run a quota AND fair scheduling together.

==============================================================================
Part 3: the isolation spectrum, cheapest to safest
==============================================================================
  The same flood (600/tick greedy, 20/tick quiet), three ways to share
  one 120-req/tick resource across 6 tenants:

  model                    quiet served greedy served   isolation     cost
  shared, no limits                 3.4         102.9        none      low
  shared + per-tenant quota         20.0          20.0        good   medium
  dedicated per tenant             20.0          20.0        best     high

  Shared, no limits: one pool, nothing counted per tenant. Cheapest to
    run, zero isolation, and Part 1 is what you get.
  Shared + quota: one pool, a cheap meter per tenant. The quiet tenants
    are protected and the pool is still shared, so idle capacity can be
    reused (with fair scheduling). This is the usual middle ground.
  Dedicated: give every tenant its own box of 20 req/tick. The greedy
    tenant is physically walled off, but so is all the slack: if a box
    is idle, no one else can use it, so you provision and pay for the
    peak of all 6 tenants at once. Strongest isolation, highest bill.

  The move from a shared pool (statistical multiplexing, one bill for the
  aggregate) to dedicated boxes (one bill per tenant, idle or not) is the
  isolation-versus-cost dial. Putting real money on that dial is Day 48.

==============================================================================
Scoreboard
==============================================================================
  P1 quiet served, no isolation      you =    3.4   actual =    3.4 /tick       close enough
  P2 greedy served, no isolation     you =  103.0   actual =  102.9 /tick       close enough
  P3 quiet served, with quota        you =   20.0   actual =   20.0 /tick       close enough
  P4 greedy served, with quota       you =   20.0   actual =   20.0 /tick       close enough

==============================================================================
The number to carry
==============================================================================
  Same shared resource, same flood, same quiet tenant wanting 20/tick.
  Shared with no limits: the quiet tenant got 3.4/tick while the
  greedy neighbour ate 103 of the 120. Add a per-tenant quota
  and the quiet tenant is back to 20/tick, the greedy one pinned at
  20. Isolation is not a feature you bolt on; it is the difference
  between one customer and all your other customers sharing the pain.
```

Part 1 is the day. Same pool, same six tenants. When everyone behaves, the pool serves 120 and all six get their 20. Change one thing, let one tenant flood with 600 instead of 20, and the well-behaved tenant drops from 20 to 3.4 per tick while the greedy one climbs to 103. Nothing about the quiet tenant changed. The shared queue simply serves whoever fills it, so loud wins and the quiet are starved. The sweep shows there is no threshold where this suddenly happens; it degrades smoothly the louder the neighbour gets.

Part 2 is the contrast. A token bucket at the fair share in front of each tenant turns the same flood away at the door: the greedy tenant's 580 extra requests per tick are rejected before the pool ever sees them, so the pool is no longer overloaded and the quiet tenant is back to a clean 20. The idle-tenant comparison is the nuance worth keeping: a hard cap protects everyone but wastes unused capacity, while max-min fair scheduling lends that unused capacity to whoever wants it without ever starving an active tenant. Simple ceiling plus work-conserving middle, run together.

Part 3 is the map. Shared with no limits is Part 1, cheap and unsafe. Shared with a quota is Part 2, the pragmatic middle. Dedicated per tenant walls everyone off perfectly and throws away the whole reason you pooled, so it costs the most. Where you sit on that dial is a money decision, which is exactly where Day 48 picks up.

The one line to carry out of today: when customers share a system they share a fate, and isolation (a per-tenant quota, fair scheduling, or a dedicated box) is how you stop one customer's bad day from becoming everyone's.

</details>
