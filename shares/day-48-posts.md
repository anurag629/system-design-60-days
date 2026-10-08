---
title: "Day 48 posts"
parent: "Day 48: cost and capacity planning"
grand_parent: "Week 7: production"
nav_order: 3
---

# Day 48 posts: LinkedIn and X

The bill breakdown is the screenshot: compute a quarter, storage a rounding error, egress two thirds. Swap in your own numbers and voice.

## LinkedIn

Day 48 of 60 days of system design. Today I did the least glamorous thing in the whole course and it might be the most useful: I turned an architecture into a monthly bill before building any of it.

The service: 8,000 requests a second at peak, 20 ms of work each. Little's Law (Day 4) says the servers hold concurrency, not request rate: 8,000 times 0.020 is 160 requests in flight at any instant. Spread that across 8-slot boxes at 70 percent busy, not 100 (the Day 4 cliff), add one spare so losing a server is a shrug (Day 6), and you get 30 servers.

Then the bill:

    compute   30 servers          $7,446   (28%)
    storage   20 TB                $1,600   (6%)
    egress    200 TB out          $18,000   (67%)
    TOTAL                         $27,046

I had predicted compute would be the biggest line. It is a quarter of the bill. Egress, the bytes going out to users, is two thirds, and it is the line nobody checks, because there is no server to point at and it never shows up in a CPU graph.

So I pulled one lever on the line that was actually big. A CDN in front (Day 20): static bytes leave the edge, origin-to-CDN transfer is free, edge egress is cheaper at volume. New bill: 21,046. That is 22 percent off the total from one change.

For comparison, the lever everyone reaches for first, a reserved-instance commitment, saves about 35 percent of the compute line, which is under 10 percent of the bill. Same effort, less than half the money, because it is aimed at the smaller line.

The lesson is embarrassingly simple: find your dominant line before you optimise anything. A design you can cost is a design you can defend.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #cloudcost #learninginpublic

## X thread

**1/**

Day 48 of 60 days of system design.

I turned an architecture into a monthly bill before building it. The line everyone optimises was a quarter of the cost. The line nobody checks was two thirds.

**2/**

Capacity first, via Little's Law (Day 4).

8,000 requests/sec, 20 ms each.
In flight at peak = 8,000 x 0.020 = 160.

Servers hold concurrency, not request rate. Spread 160 across 8-slot boxes at 70% busy (not 100, that's the cliff), add a spare for N-1.

= 30 servers.

**3/**

The bill:

compute  30 servers   $7,446   (28%)
storage  20 TB        $1,600   (6%)
egress   200 TB out  $18,000   (67%)
TOTAL               $27,046

I predicted compute would dominate. Wrong. Egress is two thirds. It never shows up in a CPU graph, so nobody looks at it.

**4/**

One lever, aimed at the big line: a CDN (Day 20).

Static bytes leave the edge, origin to CDN transfer is free, edge egress is cheaper at volume.

New bill: $21,046. That's 22% off the total from one change.

**5/**

The lever teams pull first, reserved instances, saves ~35% of the compute line = under 10% of the bill.

Same effort. Less than half the money. Because it's aimed at the smaller line.

**6/**

The whole discipline in one sentence:

Find your dominant line before you optimise anything.

Capacity and cost are the same arithmetic read twice. Little's Law sets the server count, the server count plus the rate card sets the bill, and the biggest line is where the savings live.

Code: github.com/anurag629/system-design-60-days
