---
title: "Day 10 drills"
parent: "Day 10: indexes in depth"
grand_parent: "Week 2: storage"
nav_order: 2
---

# Day 10 drills

Written on paper first. Composite indexes, covering indexes, column order, and the days the planner ignores your index.

D1 (leftmost prefix). Index on (country, city, created_at). For each query, say whether the index is used and how much of it: (1) WHERE country = 'IN'; (2) WHERE country = 'IN' AND city = 'Pune'; (3) WHERE city = 'Pune'; (4) WHERE country = 'IN' AND created_at > ?; (5) WHERE city = 'Pune' AND created_at > ?:

D2 (covering). Query: SELECT status FROM orders WHERE user_id = ?. You have an index on (user_id). What does the plan do after the index search, what one change makes it covering, and what will the plan say then?

D3 (defeated index). You have an index on email. Why does WHERE lower(email) = 'x@y.com' not use it? Give one fix, and name one more way a WHERE clause silently kills an index:

D4 (an index is not free). A table takes 10,000 inserts a second. What does each extra index cost on every insert, and give two reasons you would NOT add an index even though it speeds one read:

D5 (column order). You run WHERE user_id = ? AND created_at > ? ORDER BY created_at a lot. Which composite index, (user_id, created_at) or (created_at, user_id), and why does putting the equality column before the range column matter?
