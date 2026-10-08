---
title: "Day 56 posts"
parent: "Day 56: capstone build"
grand_parent: "Week 8: putting it all together"
nav_order: 3
---

# Day 56 posts: LinkedIn and X

The angle is the walking skeleton and the honesty of a real slice over a toy. Swap in your own voice.

## LinkedIn

Day 56 of 60 days of system design. Capstone build day. I made one slice of my system run, end to end.

Two ideas shaped the day.

First, the walking skeleton. Instead of building a perfect storage layer that does nothing for a week, you build the thinnest possible path that works all the way through: one request in, the real work happens, one response out. Then you flesh it out. Something alive and small beats something elegant and dead.

Second, the difference between a toy and a real slice. A toy stores things in a dictionary and forgets them when it stops. A real slice persists to an actual store, has a genuine read path and write path, and exposes a metrics endpoint so you can watch it work. It does not have to be big. Mine is a couple of hundred lines of pure standard library. But the request does the real work, the data really lands, and the numbers really move.

That honesty is the whole point, because tomorrow I load test it, and a load test on a slice that fakes its work measures nothing. If the write actually hits a database, the load test finds the real ceiling.

So before I stopped, I wrote down my prediction: where I think it will break, and at roughly what throughput. Tomorrow the load generator tells me how wrong I am. Same loop as every day of this course: predict, measure, learn from the gap.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #softwareengineering #buildinpublic

## X thread

**1/**

Day 56 of 60 days of system design. Capstone build day. One slice, running end to end.

Two ideas shaped it.

**2/**

The walking skeleton: build the thinnest path that works all the way through first, then flesh it out.

Something alive and small beats something elegant and dead.

**3/**

Toy vs real slice. A toy stores in a dict and forgets on restart. A real slice persists to an actual store, has a true read and write path, and exposes /metrics so you can watch it work.

Mine: ~200 lines, pure stdlib. But the work is real.

**4/**

That honesty matters because tomorrow I load test it. A load test on a slice that fakes its work measures nothing.

If the write really hits a database, the test finds the real ceiling.

**5/**

Wrote my prediction before stopping: where it breaks, at roughly what throughput.

Tomorrow the load generator tells me how wrong I am. Predict, measure, learn from the gap.

Code: github.com/anurag629/system-design-60-days
