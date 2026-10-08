---
title: "Day 50 framework sheet"
parent: "Day 50: the framework"
grand_parent: "Week 8: putting it all together"
nav_order: 1
---

# The one-page framework sheet

Copy this into your fork and make it yours. Replace the questions and defaults with your own words. The goal is a single page you can glance at mid-interview and instantly know where you are and what comes next. Use it for every mock this week.

## The clock

| Step | Minutes | Output |
|---|---|---|
| 1. Requirements | 5 | functional + non-functional |
| 2. Scale estimate | 5 | reads/s, writes/s, storage/year |
| 3. API and entities | 5 | endpoints + core objects |
| 4. High-level design | 10 to 15 | boxes and arrows, read + write path |
| 5. Deep dives | 10 to 15 | the 1 to 2 hard parts, solved |
| 6. Bottlenecks and failure | 5 | what breaks, detection, degrade |

## Step 1, requirements. The questions I always ask:

- What are the two or three things a user must be able to do?
- How many users, and is it read heavy or write heavy?
- Latency target? Strong or eventual consistency?
- How available does it need to be, and how durable is the data?
- (your own)

## Step 2, scale estimate. My formula:

- writes/s = daily writes / 86,400, then times about 3 for peak
- reads/s = writes/s times the read:write ratio
- storage/year = daily new rows times row size times 365
- (write the numbers down, do not keep them in your head)

## Step 3, API and entities. My defaults:

- a POST for the write, a GET for the read, keep it to a handful
- name the 2 to 3 core entities and their key fields
- decide early what is metadata (in the database) vs blob (in object storage)

## Step 4, high-level design. The boxes I reach for:

- client, load balancer, stateless service (Day 6)
- database (sharded? Day 13), cache (Day 15), queue (Day 22)
- draw the write path and the read path as separate arrows

## Step 5, deep dives. Driven by step 1's non-functional list:

- high write rate -> sharding, the log (week 4)
- hot key / celebrity -> replication, local cache (Day 18)
- consistency -> quorums, the CAP choice (week 5)
- (pick where the hard part actually is, do not deep-dive the easy bit)

## Step 6, bottlenecks and failure. Always touch:

- the single point of failure, and the blast radius
- the p99 tail, not the average (Day 1, Day 4)
- how it is detected (Day 43) and how it degrades (Day 27)
- the rough monthly cost, and the one biggest line item (Day 48)

## My honest weak spot

The step I rush or skip under pressure is: ________________. The fix is: ________________.
