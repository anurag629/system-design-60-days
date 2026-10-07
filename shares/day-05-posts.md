---
title: "Day 5 posts"
parent: "Day 5: designing an API"
grand_parent: "Week 1: ground truth"
nav_order: 3
---

# Day 5 posts: LinkedIn and X

Written with the reference run's numbers. Swap in your own, and rewrite in your voice. Attach the Part 1 table as a screenshot, with the `SCAN` versus `SEARCH` lines visible.

## LinkedIn

Day 5 of 60 days of system design. I took the same 20 rows from the top of a 2,000,000 row table, and from a million rows deep, and timed both.

Top of the table: 0.008 ms. A million rows deep: 5.6 ms. Same twenty rows, 600 times slower.

The culprit is the pagination style almost every tutorial teaches:

    SELECT ... ORDER BY id LIMIT 20 OFFSET 1000000

To hand you page 50,000, the database reads the million rows it is skipping, throws them all away, and only then collects your twenty. The deeper the page, the more it throws away. The query planner said it in one word: SCAN.

The fix is one line. Instead of "skip a million rows", you say "give me the rows after the last id I saw":

    SELECT ... WHERE id > :last_id ORDER BY id LIMIT 20

Now the database seeks straight to the spot using the index. Every page costs the same, page 1 or page one million. The planner word changes to SEARCH, and my deep page went from 5.6 ms to 0.009 ms.

I walked the whole table both ways. Keyset touched 2 million rows, once each. Offset would have touched about 20 billion, because every page re-reads the ones before it.

And offset is not just slow, it is wrong. On a newest-first feed, when 3 new posts arrived between page 1 and page 2, offset showed me 3 posts I had already seen. Keyset did not, because its cursor is pinned to a row, not a position.

This is why infinite scroll never lets you "jump to page 5000" any more. It is cursor pagination in a nice coat.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #databases #learninginpublic

## X thread

**1/**

Same 20 rows from a 2,000,000 row table.

Top of the table: 0.008 ms
A million rows deep: 5.6 ms

600x slower for the exact same twenty rows. Day 5 of 60 days of system design.

**2/**

The cause is the pagination every tutorial teaches:

LIMIT 20 OFFSET 1000000

The database reads the million rows it skips, throws them away, then collects your 20. Deeper page, more waste. The query planner literally says: SCAN.

**3/**

The fix is one line. Remember the last id instead of counting from the start:

WHERE id > :last_id ORDER BY id LIMIT 20

Now it seeks with the index. Deep page went 5.6 ms → 0.009 ms. Planner says: SEARCH.

**4/**

Walked the whole table both ways.

keyset: touched 2,000,000 rows
offset: would touch ~20,000,000,000 rows

Every offset page re-reads the ones before it. A line vs a triangle.

**5/**

Offset is not only slow, it is wrong.

Newest-first feed. 3 new posts arrive between page 1 and page 2. Offset showed me 3 posts twice. Keyset did not, because the cursor points at a row, not a position.

This is why "jump to page 5000" quietly died.

Code: github.com/anurag629/system-design-60-days
