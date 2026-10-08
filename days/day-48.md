---
title: "Day 48: cost and capacity planning"
parent: "Week 7: production"
nav_order: 6
has_children: true
---

# Day 48
## Turning an architecture into a monthly bill before you build it 💸

Today's one idea: every box and arrow on your diagram has a price, and you can work out that price with a napkin and the four operations you learned in school. Capacity planning tells you how many servers a design needs. Cost planning turns that server count, plus the bytes you store and the bytes you ship out, into a number in dollars. Do this arithmetic early and an architecture debate stops being a matter of taste and becomes a matter of "this one is 27,000 a month and that one is 90,000, next question."

All week we have been building the plumbing that keeps a system alive. Today is the plumbing that keeps it affordable. It is the least glamorous page in the whole guide and quietly one of the most useful, because the fastest way to sound senior in a design review is to put a monthly figure next to your diagram while everyone else is still arguing about which database is cooler.

---

## Before you start ⏪

Bring Day 4. Little's Law (L = arrival rate times time in the system) is the whole engine of capacity planning, and the cliff (a server's latency explodes as it nears 100 percent busy) is why you never size a fleet for 100 percent. Bring Day 6, where you learned to plan for N minus 1, enough servers that losing one still leaves headroom. And bring Day 20, the CDN, because the single biggest lever on today's bill lives at the edge. If those three are fuzzy, skim them first. Everything today is them, read through a rate card.

---

## Words you will meet today 📖

Capacity planning is working out how much hardware a given load needs: how many servers, how much memory, how many connections. It is Little's Law pointed at a fleet.

Service time is the work one request costs on one worker, not counting any waiting. 20 ms of service time means a single worker slot can finish 50 of those requests a second.

A worker slot is one request-in-flight's worth of a server. A box with 8 vCPUs gives you roughly 8 slots, so it can have 8 requests actually being worked on at once.

Utilisation is how busy a slot is, from 0 to 100 percent. The target utilisation is the busy level you design for, and for reasons you proved on Day 4 it is around 70 percent, not 100.

Egress is data transfer out of your cloud, from your servers to the internet, to your users. Clouds charge for it per GB, they rarely charge for data coming in, and it is the line on the bill people forget exists.

A line item is one row on the bill: compute, storage, egress, and so on. The dominant line item is the biggest one, and it is the only row where big savings live.

Right-sizing is matching the instance to the actual load instead of the load you imagined, so you stop paying for idle vCPUs. A reserved instance or savings plan is a commitment (one or three years) that trades flexibility for a discount of roughly a third off compute.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [AWS Well-Architected, the Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html). The practitioner's checklist: right-sizing, demand-based supply, and the pricing models (on-demand, reserved, spot). Skim the design principles and the right-sizing section, this is the vocabulary a cloud bill is argued in.
- [The Cost of Cloud, a Trillion Dollar Paradox](https://a16z.com/the-cost-of-cloud-a-trillion-dollar-paradox/) by Sarah Wang and Martin Casado at a16z. The big-picture case that cloud cost is a first-class design and business concern, not a finance afterthought, with egress and lock-in as the usual villains. Opinionated and worth arguing with.
- [napkin-math](https://github.com/sirupsen/napkin-math) by Simon Eskildsen. A short, punchy repo of the numbers and the method for estimating a system's cost and capacity from first principles, before you build it. This is the muscle today's lab trains.

Watch, after the lab:
- [Stop Rate Limiting! Capacity Management Done Right](https://www.youtube.com/watch?v=m64SWl9bfvk) by Jon Moore at Strange Loop, about 42 minutes. We promised you this one back on Day 4, and here is the payoff: Little's Law and utilisation used to manage a real system's capacity. The best single talk on the idea.
- Optional, short: [AWS Data Transfer Costs Explained](https://www.youtube.com/watch?v=YpmUwaqKT9E) by Cloudperceptor, about 6 minutes. A quick visual tour of the egress line that is about to dominate your bill.

### Capacity is just Little's Law with a budget (15 min)

Here is the question capacity planning answers: my service peaks at some number of requests a second, each request costs some amount of work, so how many servers do I buy?

Start with Day 4. Little's Law says the number of requests inside your system at any instant is the arrival rate times how long each one stays. At peak that is your concurrency, the number of things being worked on at the same moment. If 8,000 requests a second arrive and each spends 20 ms being served, then L = 8,000 times 0.020, which is 160 requests in flight at any instant. That 160, not the 8,000, is what your hardware has to hold.

Now spread those 160 across servers. A modern box gives you several worker slots, say 8, one per vCPU. Naively you would need 160 divided by 8, which is 20 servers, and each slot would be 100 percent busy. But you learned on Day 4 what 100 percent busy does: latency falls off a cliff, because random bursts have no room to drain. So you deliberately leave slack. Size each slot for 70 percent busy, and you need 160 divided by 0.70, which is about 229 slots, which is 29 servers. The extra 9 servers over the naive 20 are not waste. They are the headroom the cliff demands. Then Day 6 adds one more: keep a spare so that when a server dies, the survivors still hold the peak without crossing 70 percent. Call it 30.

Notice the shape of this. The whole calculation is one multiplication (Little's Law), one division (the 70 percent target), and one addition (the spare). That is capacity planning. Everything fancier is a refinement of those three steps.

### Why a slow dependency is a capacity problem (10 min)

Here is the part that bites teams in production, and it is Little's Law again. Your traffic has not changed, but the database gets slow and each request now spends 30 ms in your system instead of 20. What happens to your fleet?

The concurrency rises in lockstep. L was 8,000 times 0.020, which is 160. Now it is 8,000 times 0.030, which is 240. Half as much time again per request means half as many servers again, at the exact same traffic. You went from needing 30 servers to needing 44. Nobody sent you more requests. A dependency just got slower, and your capacity requirement, and therefore your bill, grew by half.

This is why "the database is a bit slow today" is never just a latency story. By Little's Law it is a capacity story and a cost story wearing a latency costume. It is also why one slow dependency can take down a whole fleet: if you do not have the extra servers, the concurrency it demands has to queue somewhere, and queueing near 100 percent is the cliff. Day 4 told you this in the small. Today you see the bill it writes in the large.

### The monthly bill, and the line nobody checks (14 min)

A cloud bill, stripped down, has three lines that matter for most services.

Compute is your servers: the count, times the hourly rate, times the hours in a month (the industry uses 730, which is 24 times 365 divided by 12). Storage is the data you keep: GB times a per-GB-month rate. Egress is the data you ship out to users: GB times a per-GB rate. There are a dozen smaller lines (load balancers, logs, DNS, API calls), but these three carry most services.

Now the lesson, and it is the whole reason this day exists. Add up a real-ish design and one line is almost always much bigger than the others, and it is usually not the one people fight about. In today's lab the compute line is about 7,400 a month, storage is a mere 1,600, and egress is 18,000, two thirds of the entire bill. Yet which line do teams pour weeks into? Compute. They right-size instances and haggle over vCPUs, shaving a few percent off the middle line, while the biggest line sails past unexamined because there is no server to point at and egress does not show up in a CPU graph.

Think of a big Indian wedding budget. People argue for hours about the flowers and the lighting, the lines they can see and touch. The caterer, per plate times a thousand guests, is quietly most of the bill, and a 10 percent move there dwarfs anything you do to the flowers. Egress is the caterer. Find your dominant line before you optimise anything, or you will polish the flowers while the catering bankrupts you.

### One lever, aimed at the big line (11 min)

Once you know the dominant line, optimisation becomes obvious: pull the lever that moves it.

If egress dominates, the lever is a CDN, which is Day 20 wearing a finance hat. Put a CDN in front, and the static bytes (images, video, CSS, JS, most of what a content service ships) leave the edge instead of your origin. Three things happen to the bill. Origin-to-CDN transfer is free within the cloud, so you stop paying origin egress on cached objects entirely. CDN egress is tiered, so at high volume the per-GB rate is lower than your origin's. And the cache means the origin serves each object once and the CDN serves it to thousands, so the bytes you pay full freight on collapse (that is the 120-origin-hits-to-12 result from Day 20, now denominated in rupees). In the lab, a CDN takes about 22 percent off the entire bill.

Compare that with the lever teams reach for first. A reserved-instance commitment knocks about 35 percent off compute, which sounds huge, but 35 percent of the 27 percent compute line is under 10 percent of the bill. Same effort, less than half the money, because it is aimed at the smaller line. Both are worth doing. The order is the lesson: find the dominant line, pull its lever first, and only then go tidy the rest. A design you can cost is a design you can defend, and a design you can defend is most of the job.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-48-drills.md`](../notes/day-48-drills.md). These are all one multiplication, one division, one addition. The point is to make the arithmetic automatic, so it is instant in a design review.

D1. A service peaks at 12,000 requests a second, each request needs 15 ms of work on one worker slot, and your servers have 4 slots each. How many requests are in flight at peak (Little's Law)? Sizing for 70 percent busy, how many servers do you need for the load, and what is the final count once you add one spare for N minus 1?

D2. Same service, same 12,000 requests a second, 4 slots a server. The database slows down and each request now takes 25 ms instead of 15. Recompute the fleet at 70 percent plus one spare. Why does a slower request raise the server count at unchanged traffic, and what does Day 4's cliff say about the alternative, just letting the existing fleet run hotter?

D3. A design runs 40 servers at 0.50 dollars an hour (730 hours a month), stores 50 TB at 0.08 dollars per GB-month, and serves 80 TB a month of egress at 0.09 dollars per GB. Work out each line and the total. Which line dominates, and by how much? How is that different from the lab's design, and what does the difference tell you about picking a lever?

D4. Take the lab's design: a 27,046 dollar monthly bill, of which egress is 18,000 at 0.09 dollars per GB for 200 TB. You put a CDN in front, origin-to-CDN transfer is free, and CDN egress is 0.06 dollars per GB. If the CDN serves all 200 TB to users at the CDN rate, what is the new egress line, the new total, and the percent saved off the whole bill? And why does a CDN cut the bill even when its per-GB rate is not dramatically lower than the origin's?

D5. You run 10 servers, each handling 100 requests a second at 100 percent busy, so 1,000 a second of capacity. Peak traffic is 650 a second. What utilisation are you at during peak? One server dies, can the other nine hold the peak, and at what utilisation? A second server dies, now what? Finally, tie it to the 70 percent rule: why is "we are only at 65 percent, we have loads of headroom" a dangerous thing to say on its own?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-48-cost/cost_model.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-48-cost/cost_model.py).

It is a cost-and-capacity calculator for one realistic read-heavy web service, in three parts. Part 1 turns a peak request rate into a server count using Little's Law, sizes it for 70 percent with an N-minus-1 spare, shows how the count grows as requests get slower, and then runs a small seeded queue simulation that kills servers to prove the headroom was worth paying for. Part 2 builds the monthly bill, compute plus storage plus egress, and names the dominant line. Part 3 applies one lever, a CDN on the dominant line, and recomputes the saving, next to the compute lever teams usually pull instead.

Standard library only, no network, no files, and it runs in under a second. The one simulation uses a seeded RNG, so your numbers match the reference to the digit.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. Servers to carry a peak of 8,000 requests a second, each needing 20 ms of work, on 8-slot boxes, sized for 70 percent busy with one spare. How many?
- P2. The whole monthly bill, in dollars (compute plus storage plus egress).
- P3. The single biggest line item's share of that bill, as a percent.
- P4. The percent of the bill a CDN on the dominant line removes.

P3 is the one to sit with. Before you run anything, guess which of the three lines is biggest and by how much. Most people guess compute. Write down your number.

### Fill in the TODOs

1. TODO 1 is Little's Law: concurrency equals arrival rate times service time. This one line is the whole of capacity planning.
2. TODO 2 is the sizing: spread the concurrency across slots at the target utilisation, round up to whole servers, add the spares. The 70 percent and the plus-one live here.
3. TODO 3 is the egress line: bytes out times the per-GB rate. The simplest line on the bill, and usually the biggest.
4. TODO 4 is the lever's payoff: the saving as a percent of the original bill.

```bash
cd labs/day-48-cost
python3 cost_model.py
```

The file self-checks the four TODOs before it computes anything and tells you exactly which one is still blank, so you can never get stuck staring at a wrong number.

### What you're going to discover

Part 1 is the capacity arithmetic made concrete. The naive answer (size for 100 percent) is 20 servers, the honest answer (70 percent plus a spare) is 30, and the slower-request table shows the count marching up in step with service time: double the work per request, double the fleet. Then the simulation lands the point you cannot argue with. A fleet sized at 70 percent with a spare shrugs off three dead servers and never leaves the comfort zone, while a fleet run at 95 percent to save money climbs to 99 percent as servers die and, once genuinely over capacity, its latency runs away. Same traffic, two very different outcomes, decided months earlier on a spreadsheet.

Part 2 is the shape of a real bill. Egress is two thirds of it, compute a bit over a quarter, storage a rounding error. If you predicted compute would dominate, you are in good company, and you have just learned the most useful thing on this page.

Part 3 is the lever. The CDN takes about 22 percent off the whole bill, more than twice what a reserved-instance commitment on compute would, because it is aimed at the line that is actually big. That is the entire discipline in one comparison.

### Traps ⚠️

- The simulation's p99 sits near 4.6x even on an idle fleet. That is not queueing, it is the tail of the exponential service time itself (the 99th percentile of an exponential is about 4.6 times its mean). The queueing signal to watch is the mean climbing and the utilisation nearing 100, not the p99.
- With this many pooled servers the cliff is gentler than Day 4's single box. That is real, and it is Day 4's own result that sharing one queue beats splitting it. The reason you still leave 30 percent headroom is not steady-state latency, it is failures and bursts, which the simulation shows by killing servers.
- The rates in the file are realistic 2024-ish AWS list prices, stated at the top. They are not gospel. The method is the lesson, not the exact 0.09 per GB. Change the rates to your own cloud's and the shape of the answer holds.
- Do not read the CDN saving as "CDN per-GB is always cheaper." The win is a mix: free origin-to-CDN transfer, cheaper egress at volume, and cache offload. At tiny volumes the gap shrinks. Be honest about that in your write-up.

### Deliverable

[`labs/day-48-cost/RESULTS.md`](../labs/day-48-cost/RESULTS.md) has a skeleton. Paste the output, and write one line: which line dominated your bill, was it the one you predicted, and how much did the one lever save?

---

## Block 4: write (30 min) 📣

Your angle today is the reframe: "I turned an architecture into a monthly bill before writing a line of production code. The line everyone optimises (compute) was a quarter of it. The line nobody checks (egress) was two thirds. One CDN took 22 percent off the total." The bill breakdown is the screenshot.

Example posts are on the [Day 48 posts](../shares/day-48-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, your bill's dominant line and the saving from the one lever, and one thing you still cannot explain.

Day 49 closes the week and the course's teaching with a design day: a multi-tenant SaaS or an on-call-friendly system, timed, with observability, SLOs, rate limiting, isolation, security and cost all baked in from the first stroke. Today you learned to put a number on a design. Tomorrow you defend a whole design, with that number in your pocket.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Little's Law: L = 12,000 times 0.015, which is 180 requests in flight at peak. At 70 percent busy you need 180 divided by 0.70, which is about 257 slots, and at 4 slots a server that is 257 divided by 4, rounded up, which is 65 servers for the load. Add one spare for N minus 1 and the final count is 66. The multiply, divide, add pattern again: Little's Law, then the target, then the spare.

D2. L is now 12,000 times 0.025, which is 300 in flight, up from 180 purely because each request stays longer. At 70 percent that is 300 divided by 0.70, about 429 slots, which is 429 divided by 4 rounded up, 108 servers, plus one spare, 109. So a request that got 67 percent slower pushed the fleet from 66 to 109, about 65 percent more servers, at identical traffic. That is Little's Law: the hardware holds concurrency, and concurrency is rate times time, so stretching the time stretches the fleet. The alternative, letting the existing 66 servers (264 slots) absorb 300 in-flight requests, means running at 300 over 264, which is 114 percent, over capacity. Day 4's cliff says you cannot do that: past 100 percent the queue grows without bound and latency goes to infinity. You must add the servers or shed the load. There is no third option.

D3. Compute is 40 times 0.50 times 730, which is 14,600. Storage is 50,000 GB times 0.08, which is 4,000. Egress is 80,000 GB times 0.09, which is 7,200. Total is 25,800. Here compute dominates at 14,600 over 25,800, about 57 percent, with egress second at 28 percent. This is the opposite of the lab's design, where egress was two thirds. The lesson is that there is no universal villain: a compute-heavy service (lots of processing, modest bytes out) is dominated by compute, and a content-heavy service (lots of bytes out, light processing) is dominated by egress. Find your dominant line from your own numbers, then pick the lever that moves it. A CDN would do almost nothing here; reserved instances or right-sizing is the lever for this bill.

D4. New egress is 200,000 GB times 0.06, which is 12,000, down from 18,000. The compute and storage lines do not change, so the new total is 7,446 plus 1,600 plus 12,000, which is 21,046. The saving is 6,000, which is 6,000 over 27,046, about 22 percent of the whole bill. The CDN cuts the bill even without a dramatically lower rate for three reasons. Origin-to-CDN transfer is free within the cloud, so you stop paying origin egress on everything the CDN caches. CDN egress is priced in volume tiers, so at 200 TB the blended rate is genuinely lower. And the cache means the origin serves each object once while the CDN serves it to everyone, so the number of billable bytes at full price falls before the rate even enters it. That is Day 20's origin-hit collapse, now showing up as money.

D5. At peak you are at 650 over 1,000, which is 65 percent busy. One server dies, leaving nine at 100 each, so 900 capacity, and 650 over 900 is about 72 percent. Still holds, comfortably. A second dies: eight servers, 800 capacity, 650 over 800 is about 81 percent, still under 100 but now firmly in the region where Day 4 says latency is climbing fast (roughly 1 over 1 minus 0.81, about 5 times the work time). So it holds, but it does not feel good. The danger in "we are only at 65 percent, loads of headroom" is that 65 percent is the healthy-fleet number, and the real question is always headroom for what. One failure takes you to 72, two to 81, and a traffic spike landing on top of a failure can push you over the wall. Headroom only means something relative to the failures and bursts you actually planned for. That is why the rule is 70 percent plus N minus 1, not "whatever leaves us some room."

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-48-cost/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-48-cost/solution.py).

TODO 1, Little's Law, the whole of capacity planning in one line:

```python
return peak_rps * service_time_s
```

TODO 2, size the fleet: spread the concurrency across slots at the target utilisation, round up to whole servers, add the spares:

```python
slots = conc / target_util
return math.ceil(slots / cores_per_server) + redundancy
```

TODO 3, the egress line, the simplest and usually the biggest:

```python
return egress_gb * rate_per_gb
```

TODO 4, the lever's payoff, as a percent of the original bill:

```python
return (before - after) / before * 100.0
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. The simulation is seeded, so your numbers should match these.

```
==============================================================================
Part 1: capacity. Turn a request rate into a server count.
==============================================================================
  peak traffic:        8,000 requests/second
  work per request:    20 ms on one worker slot
  slots per server:    8

  Little's Law: requests in flight at peak = 8,000 x 0.020s = 160.
  So at any instant about 160 requests are being worked on. That
  concurrency, not the request rate, is what the fleet has to carry.

  Sizing the fleet:
    at 100% busy (no headroom):  20 servers   <- the cliff edge
    at 70% busy (Day 4 headroom): 29 servers   <- 45% more, to stay off the cliff
    plus 1 spare for N-1 (Day 6):  30 servers   <- lose one, still holds peak

  The 9 extra servers past the bare 100% figure are not waste.
  They are the room random bursts need so latency does not fall off
  Day 4's cliff, plus one spare so a dead instance is a shrug, not an
  incident. Running flat out to save money is how you pay for it later.

  If each request gets slower (say the database slows down), the
  concurrency rises in lockstep, and so does the server count:
    service time    in flight   servers (70% + spare)
    20 ms                 160                      30
    25 ms                 200                      37
    30 ms                 240                      44
    40 ms                 320                      59
  Double the work per request and you roughly double the fleet, at the
  same traffic. A slow dependency is a capacity problem wearing a
  latency costume, and the bill feels it directly.

  Does the headroom earn its keep? Simulate the peak hour and start
  killing servers. Latency is in multiples of the 20 ms service time.
    (healthy fleet = 30 servers at 70% + spare;  hot fleet = 22 servers at 95%, no spare)
    scenario                             util    mean     p99  note
    healthy, all 30 up                    66%    1.0x    4.6x  comfortable
    healthy, 1 down (29 up)               68%    1.0x    4.6x  comfortable
    healthy, 3 down (27 up)               74%    1.0x    4.6x  comfortable
    hot, all 22 up                        90%    1.0x    4.6x  hot, little margin
    hot, 1 down (21 up)                   94%    1.1x    4.7x  hot, little margin
    hot, 2 down (20 up)                   99%    1.9x    5.7x  at the wall, no margin
    hot, 3 down (19 up)                   99%   19.5x   38.8x  OVERLOAD, queue runs away
  With this many pooled servers the cliff is gentler than one lonely
  box (sharing a queue buys tolerance, the Day 4 result), so read the
  trend, not one row. The healthy fleet never leaves the comfort zone,
  even three servers down. The hot fleet looked cheaper on the
  spreadsheet, then climbed 90 to 94 to 99% as servers died, and once
  it was genuinely over capacity the mean latency ran away. That gap
  between the two tables is exactly what the 70% target buys you.

==============================================================================
Part 2: the monthly bill. Three lines, and one of them is most of it.
==============================================================================
  rates: compute $0.34/hr x 730 hrs, storage $0.08/GB, egress $0.09/GB

  line      how                                    per month    share
  compute   30 servers x $0.34/hr x 730h              $7,446      28%
  storage   20,000 GB x $0.08                         $1,600       6%
  egress    200,000 GB out x $0.09                   $18,000      67%
            TOTAL                                    $27,046     100%

  The dominant line is EGRESS at 67% of the bill.
  Notice the shape. Storage, the line everyone frets about, is the
  smallest. Compute is the one teams spend weeks right-sizing. And the
  real monster is egress, the bytes going out to users, which rarely
  gets a second look because there is no server to point at. Cost work
  that ignores the biggest line is theatre.

==============================================================================
Part 3: a lever. Aim it at the dominant line, not the comfortable one.
==============================================================================
  Lever: put a CDN in front (Day 20). The static bytes now leave the
  CDN edge, origin-to-CDN transfer is free, and edge egress is cheaper
  at volume, so the egress line reprices from $0.09 to $0.06 per GB.

    egress before:  $    18,000
    egress after:   $    12,000
    bill before:    $    27,046
    bill after:     $    21,046
    saved:          $     6,000   = 22.2% of the whole bill

  Now the lever teams usually reach for first, on the comfortable line:
    reserved instances, 35% off compute -> saves $2,606 = 9.6% of the bill

  The CDN saved 22.2% and the compute commit saved 9.6%, roughly 2.3x as
  much, for comparable effort. Both are worth doing. But the order
  matters: you get the big money by pulling the lever on the line that
  is actually big, and only egress was ever going to move this bill.

==============================================================================
Scoreboard
==============================================================================
  P1 servers at 70% + spare      you =      30.0   actual =       30.0        close enough
  P2 monthly bill                you =  25,000.0   actual =   27,046.0 $       close enough
  P3 dominant line share         you =      65.0   actual =       66.6 %       close enough
  P4 CDN saving                  you =      20.0   actual =       22.2 %       close enough

==============================================================================
The number to carry
==============================================================================
  8,000 rps at 20 ms each needs 30 servers once you size
  for 70% busy and keep one spare. That design costs $27,046 a month,
  and egress is 67% of it, not the compute everyone stares at.
  One CDN on that dominant line takes 22% off the bill. Capacity and
  cost are the same arithmetic read twice: Little's Law sets the server
  count, the server count plus the rate card sets the bill, and the
  biggest line is where the savings live. A design you cannot cost is
  a design you cannot defend.
```

Part 1 is capacity made concrete. The naive 100 percent sizing says 20 servers, the honest 70 percent plus a spare says 30, and the slower-request table shows the fleet growing in direct proportion to service time, which is Little's Law staring back at you. The simulation is the part that settles the argument. The 70 percent fleet rides out three dead servers without leaving the comfort zone, while the 95 percent fleet, cheaper by eight boxes, climbs to the wall on two failures and runs away on three. That is the value of headroom, measured, not asserted.

Part 2 is the bill's real shape, and it surprises almost everyone. Egress, the bytes out to users, is two thirds of the whole thing. Compute, the line teams obsess over, is a bit over a quarter. Storage, the line people fear, is six percent. If your instinct said compute would be biggest, you have just learned why so many cost-cutting efforts shave the wrong line.

Part 3 is the discipline in one comparison. The CDN, aimed at the dominant egress line, took 22 percent off the bill. The reserved-instance commitment, aimed at the smaller compute line, took under 10. Same effort, more than double the money, purely because one lever was pointed at the line that was actually big.

The one line to carry out of today: capacity and cost are the same arithmetic read twice. Little's Law sets the server count, the server count and the rate card set the bill, and the dominant line is the only place real savings live. Learn to put that number next to your diagram, and you will never again be the person in the review who designed something nobody can afford.

</details>
