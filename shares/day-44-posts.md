---
title: "Day 44 posts"
parent: "Day 44: SLOs and error budgets"
grand_parent: "Week 7: production"
nav_order: 3
---

# Day 44 posts: LinkedIn and X

The scoreboard makes the point in one screenshot: a 99.9% SLO is a budget of about 2,000 failed requests, or 43.8 minutes, for the whole month, and one three-hour incident burned 8x the daily rate. Swap in your own numbers and voice.

## LinkedIn

Day 44 of 60 days of system design. Today I stopped treating "uptime" as a vibe and turned it into a number I can spend.

An SLO of 99.9% sounds like "basically always up". It is not. Over one month it allows you exactly this much failure:

    99.9% SLO, 2,000,000 requests/month
    budget = 2,000 failed requests
           = 43.8 minutes of downtime

That is the error budget. It is just (1 minus the SLO) times the total. And the moment you write it as a number, three things change.

First, you can see how fast you are spending it. I simulated a month with one three-hour incident. A quiet day burned 0.6x the sustainable rate. The incident day burned 8x. At that pace the whole month's budget is gone in under four days. One bad afternoon, a quarter of the month's budget, and the number says so before anyone argues about it.

Second, you can see why 100% is the wrong goal. Each extra nine costs 10x the room of the one before: 99% gives you 438 minutes a month, 99.9% gives 43.8, 99.99% gives 4.4. And 100% gives you zero, which means you can never ship a risky change, never have an incident, never patch under load. It is infinitely expensive and it buys you a system too scared to move.

Third, and this one hurt: dependencies multiply. My service needs all 5 of its dependencies, each promising 99.9%. The ceiling is 0.999 to the 5th, about 99.5%, which is 3.6 hours of downtime a month before I have written a single bug of my own. You do not get to pick a number better than your dependencies allow, unless you make some of them optional.

The error budget is not a stick to beat the team with. It is permission to spend failure on purpose, on deploys and experiments and real life. 100% uptime is the goal of a team that has never shipped anything.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #sre #reliability #learninginpublic

## X thread

**1/**

"We need 100% uptime."

No, you do not, and today I measured why. Day 44 of 60 days of system design: SLOs and error budgets.

**2/**

A 99.9% SLO is not "always up". It is a budget.

Over one month of 2,000,000 requests:

budget = (1 - 0.999) x 2,000,000
       = 2,000 failed requests
       = 43.8 minutes of downtime

That is all the failure you are allowed. For the whole month.

**3/**

Writing it as a number lets you watch how fast you spend it. The burn rate.

I simulated a month with one 3-hour incident:

quiet day:     0.6x the sustainable rate
incident day:  8x

At 8x, the whole month's budget is gone in under 4 days. One afternoon ate ~25% of it.

**4/**

This is why 100% is the wrong goal. Each nine costs 10x the room of the last:

99%     = 438 min/month
99.9%   = 43.8 min
99.99%  = 4.4 min
100%    = 0 min

0 minutes means you can never ship a risky change or have a bad day. Infinitely expensive.

**5/**

And the part that stung: dependencies multiply.

My service needs all 5 dependencies, each at 99.9%.

ceiling = 0.999^5 = 99.5%
        = 3.6 hours of downtime a month

Before my own bugs. You cannot be more available than everything you wait on.

**6/**

So the error budget is not a stick. It is permission to spend failure on purpose: deploys, experiments, maintenance, real life.

Pick a number you can defend. Then spend the budget.

Code: github.com/anurag629/system-design-60-days
