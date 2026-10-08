---
title: "Day 44: SLOs and error budgets"
parent: "Week 7: production"
nav_order: 2
has_children: true
---

# Day 44
## SLOs and error budgets, or how to turn "is it reliable?" into a number you can spend 🎯

Today's one idea: reliability is not a feeling, it is a budget. You pick a target, say 99.9 percent, and that target hands you a fixed allowance of failure for the month: a certain number of failed requests, a certain number of minutes of downtime. That allowance is the error budget, and once you can see it as a number, the hard questions get easy. Can we ship this risky change? Check the budget. Was that incident a big deal? Measure how much of the budget it burned. Should we chase 100 percent? No, because 100 percent means an allowance of zero, which is infinitely expensive and leaves you no room to ever move.

Yesterday you learned to see your service with logs, metrics and traces. You can now measure the availability and the latency. Today you give those measurements a target and a consequence, which is the step from "I can see it" to "I know whether it is good enough, and what to do when it is not".

---

## Before you start ⏪

You need Day 43 fresh: the RED method gave you request rate, errors and duration, which is exactly the raw material for an SLI. You also want Day 2 in mind, the nines table and the one line that said dependencies multiply (0.999 to the fifth is 99.5 percent). Today we take that table, which looked like interview trivia back in week 1, and turn it into the tool you actually use to run a service. The lab is pure Python, standard library, no network and no threads, a deterministic simulation of one month of traffic. Day 2's comfort with a loop and a count is plenty.

---

## Words you will meet today 📖

An SLI, service level indicator, is the thing you measure. It is a ratio from the user's point of view: good requests over total requests (availability), or the fraction of requests served under 300 ms (latency). It is a symptom the user feels, not a cause like CPU usage.

An SLO, service level objective, is the target you hold the SLI to. "99.9 percent of requests succeed, measured over 30 days." It is a line you draw for yourselves, inside the company.

An SLA, service level agreement, is the promise you make to the customer in a contract, usually with money attached if you miss it. You keep the SLA looser than the SLO on purpose, so your own alarm (the SLO) goes off well before you owe anyone a refund.

An error budget is the failure the SLO allows: (1 minus the SLO) times the total, over the window. A 99.9 percent SLO is a 0.1 percent budget. It is a quantity you spend, not a wall you must never touch.

A burn rate is how fast you are spending the budget. A burn rate of 1 spends the whole month's budget evenly across the month. A burn rate of 10 spends it ten times too fast, so the month's allowance is gone in three days.

Dependency multiplication is the rule that if your service needs several other services to all be up at once, their availabilities multiply, so your ceiling is always below the weakest thing you depend on.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three, and the fourth if burn rate grabs you:
- [Google SRE book, Embracing Risk](https://sre.google/sre-book/embracing-risk/). The argument of the whole day, from the people who invented the error budget. Why 100 percent is the wrong target, how the budget aligns the people who want to ship with the people who want stability, and why unreliability has an optimal, non-zero level. If you read one thing, read this.
- [Google SRE book, Service Level Objectives](https://sre.google/sre-book/service-level-objectives/). The vocabulary done properly: SLI, SLO and SLA, how to pick an indicator that reflects what users actually feel, and why the SLO should be tighter than the SLA.
- [Google SRE Workbook, Implementing SLOs](https://sre.google/workbook/implementing-slos/). The practical how-to, with the budget arithmetic worked out. This is the spine of today's lab.
- Optional, straight into Part 2: [Google SRE Workbook, Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/). Burn rate as the thing you alert on, so a fast burn pages you now and a slow burn just files a ticket.

Watch, after the lab:
- [SLIs, SLOs, SLAs, oh my! (class SRE implements DevOps)](https://www.youtube.com/watch?v=tEylFyxbDLE) by Google Cloud Tech, about 8 minutes. The three terms drawn out clearly, with the error budget idea front and centre. Watch this one.
- Optional: [The Art of SLOs](https://www.youtube.com/watch?v=E3ReKuJ8ewA), about 4 minutes. A short, sharp take on choosing a target that means something.

### What you measure, what you promise, what you pay (16 min)

Three letters that get mixed up constantly, so let me pin them down with one running example: a service that handles API requests.

The SLI is the measurement. You decide the single most honest number for "is this service doing its job", from the user's side. For most request-serving systems that is availability, the fraction of requests that succeeded, and often a latency SLI too, the fraction served fast enough. Notice what an SLI is not. It is not CPU, memory or disk. Those are Day 43's USE method, the causes you look at when something is wrong. The SLI is the symptom the user feels, the RED method, and that is the whole point: you hold yourself to what the customer experiences, not to how hard your machines are breathing. A server can be at 20 percent CPU and still be failing every request.

The SLO is the target. You take the SLI and draw a line: 99.9 percent of requests succeed, measured over a rolling 30 days. That is an internal number, a promise your team makes to itself. Picking it is a real decision, not a reflex to write the most nines you can. A good SLO sits just a little above what users would start to notice and complain about, and not a hair higher, because every extra nine is expensive and users cannot feel reliability they never lose.

The SLA is the contract. It is the promise with legal and financial teeth, the one in the customer agreement that says "if we drop below 99.5 percent this quarter, you get a credit". Here is the trick that catches people: your SLA should be looser than your SLO. If you promise customers 99.5 but hold yourselves to 99.9, then by the time you are at risk of breaking the contract, your own SLO alarm has been screaming for a while. The gap between the two is your safety margin. Promise less than you aim for.

### The error budget, and why 100 percent is the wrong goal (16 min)

Now the idea that makes this whole topic click. An SLO of 99.9 percent does not mean "try to never fail". It means you are allowed to fail 0.1 percent of the time. That 0.1 percent is a real, countable quantity, and it is called the error budget.

Think of it exactly like a prepaid data pack. You get a fixed amount for the month. You can blow the whole thing in two days streaming video, or you can pace it and have some left on the 30th. Either way, the amount is fixed and you can see how much is left. The error budget is the same. A 99.9 percent SLO over a month of two million requests gives you a budget of 2,000 failed requests, which is also about 43.8 minutes of downtime. That is your pack for the month. Deploys spend it, experiments spend it, a flaky dependency spends it, a bad config spends it. The question is never "did anything fail", it is "how much of the pack is left".

The burn rate is how fast the meter is running. If you are failing at exactly the rate the SLO allows, your burn rate is 1 and the pack lasts exactly the month. If a bad deploy pushes your error rate to ten times the allowed rate, your burn rate is 10 and, left alone, you would empty the whole month's pack in three days. This is what you alert on, and it is smarter than alerting on raw errors. A slow burn can wait for working hours. A fast burn, the whole month's budget draining in an afternoon, should wake someone up. In the lab you will watch a quiet day burn at 0.6x and a three-hour incident burn at 8x, and you will feel how a single bad afternoon eats a quarter of the month.

So why not just aim for 100 percent and never think about budgets? Two reasons, and they are the heart of the day. First, it is infinitely expensive. Each extra nine costs roughly ten times the effort of the one before, in redundancy, testing and on-call pain, for a slice of reliability the user usually cannot even perceive, because their own phone and wifi fail far more often than your fourth nine ever will. Second, and worse, 100 percent means a budget of zero. Zero budget means you can never ship a risky change, never run an experiment, never do maintenance under load, never have one bad day, without "failing". A team with a 100 percent target is a team that has learned to never move. The error budget flips that: as long as there is budget left, ship freely. When it runs out, slow down and spend on reliability. It turns the oldest fight in the building, developers want to ship and ops wants stability, into simple arithmetic that both sides can read off the same dashboard.

### Dependencies multiply (12 min)

Here is the humbling part, and it is a straight callback to Day 2. Your availability is not something you set on your own. It is capped by everything you depend on.

Say your service needs five other services to answer a request, and you need all five, every time. Each of them is run by a good team and promises three nines, 99.9 percent. What can you promise? Not 99.9. Your request succeeds only if all five are up at once, and independent probabilities multiply, so your ceiling is 0.999 times itself five times, 0.999 to the fifth, which is about 99.5 percent. That is roughly 3.6 hours of downtime a month, and you have not written a single bug of your own yet. Add more dependencies and it keeps falling. This is Day 4's fan-out seen from the reliability side: a caller that waits on many services is only as up as the product of all of them.

The lesson is not "dependencies are bad". It is that you must fight this on purpose, because it does not fix itself. Fewer hard dependencies on the critical path. Make dependencies optional where you can, so that when the recommendations service is down you still show the page without recommendations, degraded instead of dead. Cache aggressively (week 3) so you are not calling a dependency on every single request. Put timeouts and fallbacks on every call, because a dependency that is slow and still holding your thread is Day 4's queue filling up, which turns one slow dependency into your own outage. The services that hit high availability are not the ones with flawless dependencies. They are the ones that assume every dependency will fail and are built to shrug when it does.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. A month is 43,830 minutes (the average month, the figure behind Day 2's table). Then copy your answers into [`notes/day-44-drills.md`](../notes/day-44-drills.md).

D1. Nines and downtime. Over one month, how many minutes of downtime does each of 99.9 percent, 99.95 percent and 99.99 percent allow? Which row is "three nines", and how much does the step from 99.9 to 99.99 cost you in room?

D2. Budget in requests. A service serves 5,000,000 requests this month under a 99.95 percent SLO. How many failures are you allowed? If it logged 1,800 failures, what percent of the budget did it spend, how much is left, and are you meeting the SLO?

D3. Burn rate. The SLO is 99.9 percent. A one-hour incident serves 60,000 requests and fails 1,200 of them. What is the error rate during the incident, and the burn rate? If that rate were sustained, roughly how long until the whole month's budget is gone?

D4. Dependencies multiply. Your service needs all 4 of its dependencies. Three are at 99.9 percent and one legacy service is at 99 percent. What is your combined availability ceiling, which dependency dominates the loss, and what does the ceiling become if you make the legacy one optional with a fallback?

D5. Choosing the target. Product asks for "100 percent uptime" on an internal batch-reporting API. Give two concrete reasons 100 percent is the wrong goal, propose a defensible SLO, state the error budget it implies in minutes per month, and say what that leftover budget lets the team actually do.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-44-slos/slos.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-44-slos/slos.py).

It is a pure simulation, standard library only, and it runs in under a second. It walks one month of a service's request stream, minute by minute, with a normal background failure rate and one three-hour incident dropped on a single day. Part 1 counts the stream to get the SLI and holds it up against a 99.9 percent SLO. Part 2 computes the error budget in requests and in minutes, shows how much this month spent, and measures the burn rate on a quiet day versus the incident day. Part 3 takes five dependencies at 99.9 percent and watches the combined availability fall, both by the multiplication formula and by a Monte Carlo that agrees with it.

Everything is deterministic. The RNG is seeded, so your run matches the reference to the digit.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. A 99.9 percent SLO over one month. How many minutes of downtime does that allow? (Day 2 had this in a table. See if it stuck.)
- P2. The service handled 2,000,000 requests this month under a 99.9 percent SLO. How many of them are you allowed to fail?
- P3. A multi-hour incident lands on one day. That single day spent how many times the sustainable daily slice of the budget? (1x means exactly on budget for the day.)
- P4. Your service needs all 5 dependencies, each at 99.9 percent. What combined availability can you offer, before any bug of your own?

P1 and P4 are the two to feel in your gut. Most people guess 99.9 percent means "a few minutes a month" and are surprised it is closer to 44, and most people guess five good dependencies still leave them near 99.9, not 99.5.

### Fill in the TODOs

1. TODO 1 is the SLI: successes over total, `good / total`. The measurement.
2. TODO 2 is the budget in requests: `(1.0 - slo) * total`. The failures you are allowed. Everything grows from this line.
3. TODO 3 is the burn rate: the error rate you serve over the error rate the SLO allows, `error_rate / (1.0 - slo)`.
4. TODO 4 is the multiplication: the product of the dependency availabilities, the chance all are up at once.

```bash
cd labs/day-44-slos
python3 slos.py
```

### What you're going to discover

Part 1 is the gentle one. The month comes in at about 99.93 percent, which clears the 99.9 percent SLO, so the verdict is "meeting it". Good news, until you look at how little room that was.

Part 2 is where it lands. The budget is 2,000 failed requests, or 43.8 minutes, for the whole month. This month spent about 70 percent of it, and a single three-hour incident burned at 8x the sustainable rate, enough to empty the month's budget in under four days if it had kept up. Then the "each nine costs 10x" table: 99 percent gives you 438 minutes, 99.9 gives 43.8, 99.99 gives 4.4, and 100 percent gives zero. That zero is the argument against perfection, printed as a number.

Part 3 is the ceiling. Five dependencies at 99.9 percent land you at 99.5 percent, about 3.6 hours a month, before your own code runs. The measured Monte Carlo column sits right on the formula, because this is multiplication, not luck. Watching the number fall one dependency at a time is the moment Day 2's little rule stops being trivia.

### Traps ⚠️

- A month is not 30 days exactly. The lab uses 43,830 minutes, the average Gregorian month, so the numbers match Day 2's table (43.8 and 4.4). If you use a flat 30 days you get 43.2 and 4.3, close but not matching. Do not let the small gap confuse you.
- Burn rate is a rate, not a total. A burn rate of 8 does not mean the budget is 8 percent gone. It means that if the current error rate held, the month's budget would drain 8 times faster than it should. The incident was only three hours, so it did not actually empty the budget, it just told you how fast it would have.
- The measured dependency column wobbles by a hundredth of a percent run to run, because it is a Monte Carlo over 200,000 trials. Trust the match to the formula, not the fourth decimal.
- Meeting the SLO this month does not mean you are safe. We spent 70 percent of the budget with one incident. Two such incidents and we would have blown it. "Green" on the dashboard can still be one bad afternoon from red.

### Deliverable

[`labs/day-44-slos/RESULTS.md`](../labs/day-44-slos/RESULTS.md) has a skeleton. Paste the output, and write one line: a 99.9 percent SLO allows how many minutes a month, and what sentence would you say in a design review when someone asks for 100 percent uptime?

---

## Block 4: write (30 min) 📣

Your angle today is the reframe that makes reliability concrete: "I used to think 99.9 percent uptime meant 'basically always up'. Then I did the arithmetic. Over a month it allows 2,000 failed requests, about 43.8 minutes, and a single three-hour incident burned 8 times too fast. 100 percent is the wrong goal, it is infinitely expensive and leaves no room to ship. Reliability is a budget you spend, not a wall you defend." The budget table and the dependency drop are the screenshots.

Example posts are on the [Day 44 posts](../shares/day-44-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the error budget you computed in minutes and requests, and one thing you still cannot explain.

Day 45 is rate limiting and load shedding. Today you learned that failure is a budget you can afford to spend. Tomorrow you learn how to protect that budget when a flood of traffic arrives: how to say "no" to some requests gracefully so the rest keep working, which is the IRCTC tatkal problem in its purest form. The error budget tells you how much failure you can take. Rate limiting is one of the tools that keeps you from spending it all in one morning.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The budget in minutes is (1 minus the SLO) times 43,830. 99.9 percent gives 0.001 times 43,830, about 43.8 minutes. 99.95 percent gives 0.0005 times 43,830, about 21.9 minutes. 99.99 percent gives 0.0001 times 43,830, about 4.4 minutes. "Three nines" is 99.9 percent, 43.8 minutes. The step from 99.9 to 99.99 cuts your room by a factor of ten, from 43.8 minutes down to 4.4. One extra nine, ten times less slack. That factor of ten per nine is the whole reason you do not chase nines for free.

D2. The budget is (1 minus 0.9995) times 5,000,000, which is 0.0005 times 5,000,000, so 2,500 failures allowed. It logged 1,800, so it spent 1,800 of 2,500, which is 72 percent of the budget, leaving 700. The SLI is 1 minus 1,800 over 5,000,000, which is 99.964 percent, above the 99.95 percent SLO, so yes, meeting it, with 28 percent of the budget still in hand.

D3. The error rate during the incident is 1,200 over 60,000, which is 0.02, or 2 percent. The burn rate is that error rate over the allowed rate, 0.02 over (1 minus 0.999), which is 0.02 over 0.001, so 20x. If a 2 percent error rate were sustained, you would burn the month's budget 20 times too fast, so the whole month's allowance would be gone in about 30.44 over 20 days, roughly 1.5 days. A sustained 2 percent error rate empties a 99.9 percent monthly budget in a day and a half, which is exactly why a burn rate that high should page someone immediately, not wait for the morning.

D4. You need all four, so the availabilities multiply: 0.999 times 0.999 times 0.999 times 0.99. The three nines give 0.999 cubed, about 0.99700, and times 0.99 is about 0.98703, so roughly 98.70 percent. The 99 percent legacy service dominates the loss: on its own it drops you about 1 percent, while the three good dependencies together cost only about 0.3 percent. If you make the legacy one optional, with a fallback so the request still succeeds when it is down, it no longer gates your availability, and your ceiling jumps to 0.999 cubed, about 99.70 percent. Removing one hard dependency moved you from 98.70 to 99.70 percent, nearly a full point, more than all your other reliability work combined. That is the lever to reach for first.

D5. Two reasons 100 percent is wrong. First, it is infinitely expensive: each extra nine costs roughly ten times the engineering of the last, for reliability the user usually cannot perceive because their own network fails more often than your high nines ever will. Second, it leaves a budget of zero, so you can never ship a risky change, run an experiment, do maintenance under load, or absorb a dependency's bad day without "violating" the target, which trains the team to never move. A defensible SLO for an internal, non-latency-critical batch API might be 99.5 percent, or even 99 percent. At 99.5 percent the budget is (1 minus 0.995) times 43,830, about 219 minutes, roughly 3.6 hours a month. That leftover budget is permission: to deploy during the day, to let a dependency wobble, to run a scheduled maintenance window, all without anyone treating a normal, healthy level of failure as an emergency.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-44-slos/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-44-slos/solution.py).

TODO 1, the SLI, the measurement: successes over total.

```python
return good / total
```

TODO 2, the error budget in requests, the failures you are allowed. Everything grows from this one line.

```python
return (1.0 - slo) * total
```

TODO 3, the burn rate, the error rate you serve over the error rate the SLO permits.

```python
return error_rate / (1.0 - slo)
```

TODO 4, the dependency multiplication, the chance every dependency is up at once.

```python
product = 1.0
for a in avails:
    product *= a
return product
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, seeded, one simulated month of 2,000,000 requests.

```
==============================================================================
Part 1: the SLI vs the SLO. Measure what you shipped, hold it up to
        what you promised
==============================================================================
  one month of traffic: 2,000,000 requests, 1,395 of them failed.
  SLI (measured availability) = 99.930%
  SLO (the promise)           = 99.900%
  verdict: MEETING the SLO.

  Notice the SLI is a plain count: good requests over all requests,
  over a fixed window. The SLO is the line you drew in advance. Day 43
  gave you the metrics to compute this; today you give the number a
  target and a consequence. We are above the line this month, but look
  how little room 'above the line' actually is, next.

==============================================================================
Part 2: the error budget. The failures you are ALLOWED, and how fast
        you are spending them
==============================================================================
  The budget is (1 - SLO) times the window. Two ways to read it:
    in requests: (1 - 0.999) x 2,000,000 = 2,000 failures allowed
    in minutes:  (1 - 0.999) x 43,830 = 43.8 minutes of downtime a month

  This month you spent 1,395 of 2,000 failures (69.7% of the budget).
  Budget left: 605 failures. You are in the black.

  Burn rate = the error rate you are serving / the error rate the SLO
  allows. 1x spends the budget exactly over the month. Watch one day:

  day                 requests    failures    error rate   burn rate
  a quiet day           66,240          40        0.060%       0.60x
  the incident day      66,240         540        0.815%       8.15x

  The sustainable daily slice is 65.7 failures. The quiet day
  stayed well under it (burn rate below 1, the budget would outlast the
  month). The incident day burned 8.2x: at that pace the whole
  month's budget is gone in 3.7 days. One bad afternoon ate a
  real slice of the month, and that is exactly what the budget is for,
  to tell you so in a number instead of an argument.

  Why not just aim for 100 percent? Because each extra nine costs 10x
  the room of the one before, and 100 percent allows zero failures ever:
  SLO               budget / month     vs previous
  99.000                 438.3 min               -
  99.900                  43.8 min   10x less room
  99.990                   4.4 min   10x less room
  99.999                   0.4 min   10x less room
  100.000     0.0 min, which means you can never ship a risky change,
  never have an incident, never patch under load. Infinitely expensive,
  and it buys you a system too scared to move. The budget is permission
  to spend failure on purpose: on deploys, experiments, and real life.

==============================================================================
Part 3: dependencies multiply. Each one you must call lowers your
        ceiling, before you add a single bug of your own
==============================================================================
  Each dependency promises 99.9%. You need ALL of them to
  answer, so their availabilities multiply (Day 2's rule, Day 4's
  fan-out: a caller is only as up as every service it waits on).

    dependencies   combined (theory)    measured    downtime / month
               1             99.900%     99.894%              44 min
               2             99.800%     99.800%              88 min
               3             99.700%     99.672%             131 min
               4             99.601%     99.576%             175 min
               5             99.501%     99.516%             219 min
               6             99.401%     99.406%             262 min
               7             99.302%     99.306%             306 min

  With 5 dependencies at 99.9%, your ceiling is already
  99.50% = about 219 minutes (3.6 hours) of downtime a
  month, and you have not shipped one line of your own yet. The measured
  column (a Monte Carlo of whether all 5 are up) sits right on the
  theory, because this is multiplication, not luck. This is why you
  fight it on purpose: fewer hard dependencies, timeouts and fallbacks
  so a dependency being down degrades you instead of taking you down,
  and caches so you do not have to call it every time.

==============================================================================
Scoreboard
==============================================================================
  P1 budget minutes (99.9%)          you =   44.00   actual =    43.83 min       close enough
  P2 budget requests                 you = 2000.00   actual =  2000.00        close enough
  P3 incident-day burn rate          you =    8.00   actual =     8.15 x       close enough
  P4 combined avail, 5 deps          you =   99.50   actual =    99.50 %       close enough

==============================================================================
The number to carry
==============================================================================
  A 99.9% SLO is NOT 'basically always up'. It is a budget: 2,000
  failed requests, or 44 minutes of downtime, for the whole month.
  This month spent 1,395 of them, and one 3-hour incident burned
  8x the daily rate on its own. Stack 5 dependencies at 99.9%
  and your ceiling is already 99.5% before your own bugs. That is
  why 100% is the wrong goal: it is infinitely expensive and leaves no
  room to ship. Pick a number you can defend, then spend the budget on
  purpose.
```

Part 1 is the setup. The month measured 99.93 percent, which clears the 99.9 percent SLO, so the service is "meeting it". That sounds comfortable until Part 2 shows that "meeting it" meant spending 70 percent of a very small allowance.

Part 2 is the day. The budget is 2,000 failed requests, or 43.8 minutes, for the entire month, and that is all 99.9 percent ever buys you. The burn-rate rows are the lesson: a quiet day runs at 0.60x, comfortably under budget, while the three-hour incident runs at 8.15x, which would drain the month in under four days if it held. Then the nines table makes the case against perfection in one column: 438 minutes at two nines, 43.8 at three, 4.4 at four, and a flat zero at 100 percent. Zero budget is a system that can never move.

Part 3 is the ceiling you do not control. Five dependencies at 99.9 percent, all required, put you at 99.5 percent, about 3.6 hours of downtime a month, before your own code has a chance to fail. The measured Monte Carlo column tracks the formula to the hundredth, because this is multiplication and not chance. It is the same 0.999 to the fifth you met on Day 2, except now you can watch it fall one dependency at a time and feel why reducing hard dependencies is reliability work, not cleanup.

The one line to carry out of today: reliability is a budget, not a wall. 99.9 percent is 43.8 minutes a month, you spend it on deploys and incidents and bad afternoons, and the moment you ask for 100 percent you have asked for a budget of zero, which no team that ships anything can afford.

</details>
