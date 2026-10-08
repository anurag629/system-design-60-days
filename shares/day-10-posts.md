---
title: "Day 10 posts"
parent: "Day 10: indexes in depth"
grand_parent: "Week 2: storage"
nav_order: 3
---

# Day 10 posts: LinkedIn and X

The two "ignored index" plans make the best screenshots: a composite index that refuses a city-only filter, and an email index defeated by lower(). Swap in your own numbers and voice.

## LinkedIn

Day 10 of 60 days of system design. Today I learned that creating an index is the easy part. Getting the database to actually use it is the real skill.

I built a SQLite table of 2 million rows and ran five queries, printing the EXPLAIN QUERY PLAN and the timing for each. Three results stuck with me.

One, the obvious win. Add an index on the column you filter, and a full table SCAN turns into a SEARCH. The query went from reading all 2 million rows to touching about 20. Roughly 5,000x faster. This part everyone knows.

Two, the covering index. For SELECT SUM(amount) WHERE country = ?, a plain index on country still has to jump back to the table for every one of the ~100,000 matching rows to read amount. An index on (country, amount) holds both columns, so SQLite answers from the index alone and never touches the table. The plan literally says USING COVERING INDEX. About 13x faster, same query, just a wider index.

Three, the part that humbles you. I had two perfectly good indexes that the planner simply ignored.

    composite index on (country, city), filter on city alone: ignored, full SCAN, ~1,900x slower
    index on email, query WHERE lower(email) = ?:            ignored, full SCAN

The composite one is the leftmost-prefix rule. The index is sorted by country first, so if you do not constrain country, the cities are scattered all through it and the index is useless. The email one is subtler: the index is on email, not on lower(email), so the moment you wrap the column in a function, the planner cannot use it and scans every row calling lower() on each.

The lesson I am taking: an index is not a "make this column fast" button. It is a sorted copy of some columns, and the planner uses it only when your query matches the way it is sorted. Break that shape and you silently pay a full scan, with no error to warn you.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #databases #sql #learninginpublic

## X thread

**1/**

Creating a database index is easy. Getting the planner to actually use it is the real skill.

Today I ran 5 queries on a 2M-row table and printed the EXPLAIN QUERY PLAN for each. Two of my indexes got completely ignored.

Day 10 of 60 days of system design.

**2/**

The easy win first. Filter a column with no index: full SCAN of 2M rows. Add an index: a SEARCH that touches ~20 rows.

About 5,000x faster. SCAN to SEARCH. This is the part everyone already knows.

**3/**

Covering index. SELECT SUM(amount) WHERE country = ?

Plain index on country: searches the index, then jumps to the table 100,000 times to read amount.

Index on (country, amount): answers from the index alone. Plan says USING COVERING INDEX. ~13x faster.

**4/**

Now the humbling part. A composite index on (country, city).

Filter on country: used.
Filter on country AND city: used.
Filter on city alone: IGNORED. Full scan. ~1,900x slower.

The index is sorted by country first. Skip it and the cities are scattered everywhere. Leftmost-prefix rule.

**5/**

Second ignored index. I have an index on email.

WHERE email = ? : used, instant.
WHERE lower(email) = ? : ignored, full scan of 2M rows.

The index is on email, not on lower(email). Wrap a column in a function and the index dies. No error. Just slow.

**6/**

The takeaway: an index is not a "make this fast" button. It is a sorted copy of some columns.

The planner uses it only when your query matches that sort order. Break the shape and you quietly pay a full scan.

Read the plan. Always read the plan.

Code: github.com/anurag629/system-design-60-days
