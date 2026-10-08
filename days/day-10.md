---
title: "Day 10: indexes in depth"
parent: "Week 2: storage"
nav_order: 3
has_children: true
---

# Day 10
## Composite, covering, and the day the planner ignores your index 🗂️

Today's one idea: an index is just a sorted copy of one or more columns, kept beside your table. The planner uses it only when your WHERE clause matches the order it is sorted in. Match that shape and a query that scanned millions of rows now touches a handful. Break the shape, by skipping the leftmost column or wrapping it in a function, and the planner quietly ignores the index and scans everything, with no error to warn you.

Day 5 gave you the one-line version: an index is a lookup that jumps instead of scanning. Day 9 showed you the tree the index is actually made of. Today is the day you stop trusting "I added an index" and start reading the plan, because half the time the index you lovingly created is sitting there unused.

---

## Before you start ⏪

You need Day 5's index-seek idea and Day 9's picture of a B-tree. You should be comfortable running SQLite from Python, which you have done since Day 2. Today you will run EXPLAIN QUERY PLAN a lot, so if you have never seen it, do not worry, the lab prints it for you on every query and the whole point is to learn to read it.

---

## Words you will meet today 📖

A composite index, also called a compound or multi-column index, is an index on more than one column. It is sorted by the first column, then by the second within each value of the first, and so on. Think of a phone book sorted by last name, then first name.

The leftmost-prefix rule says a composite index on (a, b, c) can be used by a query that constrains a leading run of its columns: a alone, or a and b, or all three. It cannot be seeked for b alone, or c alone, or b and c without a.

A covering index is one that already contains every column the query asks for, so the database answers from the index and never opens the table. SQLite prints USING COVERING INDEX in the plan. Other databases call the same thing an index-only scan.

Selectivity is how few rows a value matches. A unique email is highly selective and perfect for an index. A boolean that splits the table in half is barely selective, and an index on it is often worse than a plain scan.

The query planner, or optimizer, is the part of the database that reads your query and decides how to run it: which index, if any, and whether to scan or seek. EXPLAIN QUERY PLAN shows you the decision it made.

A SCAN reads every row of a table or every entry of an index. A SEARCH jumps straight to the matching rows through an index. SCAN versus SEARCH is the first thing you read in any plan.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html). Short and practical. This is the exact command you print on every query in the lab, so learn to read SCAN, SEARCH, and USING COVERING INDEX from the horse's mouth.
- [Use The Index, Luke: concatenated keys](https://use-the-index-luke.com/sql/where-clause/the-equals-operator/concatenated-keys). The clearest explanation of composite indexes and the leftmost-prefix rule anywhere. Markus Winand's free book is the index bible.
- [Use The Index, Luke: index-only scan and the covering index](https://use-the-index-luke.com/sql/clustering/index-only-scan-covering-index). Exactly the Part 3 result of the lab, drawn out with care.

Watch, after the lab:
- [Database Indexing Explained (with PostgreSQL)](https://www.youtube.com/watch?v=-qNSXK7s7_w) by Hussein Nasser, about 18 minutes. A calm, practical walk through what an index is and how it changes a query.
- [How do indexes make databases read faster?](https://www.youtube.com/watch?v=3G293is403I) by Arpit Bhayani, about 23 minutes. He builds the B-tree intuition from the ground up, which makes the leftmost-prefix rule obvious instead of a thing to memorise.

### An index is a sorted copy, nothing more (12 min)

Here is the whole mental model, and it carries the entire day. An index is a second, smaller structure that sits beside your table. It holds a copy of one or more columns, kept in sorted order, plus a pointer back to the full row. That is it. A B-tree index on email is the list of every email, sorted, each with a little arrow to the row it came from.

Once you hold that picture, every rule today becomes obvious instead of magic. Why is a lookup fast? Because the values are sorted, so the database binary-searches instead of reading everything. Why does an index cost you on writes? Because every insert now has to slot a new entry into the sorted structure too, keeping it in order. Why does skipping the first column break a composite index? Hold that thought, it is the next section, and the phone book answers it.

The lab proves the base case first. One filter, no index: the planner SCANs all 2 million rows. Add an index on that column: it becomes a SEARCH that touches about 20. On the reference machine that was roughly 5,000 times faster, for the identical query. That part you already expected. The rest of the day is about the times it does not happen even though you added the index.

### The leftmost-prefix rule, or the phone book (12 min)

Picture a paper phone book, sorted by last name, then first name. That is exactly a composite index on (last_name, first_name).

Ask it for everyone named "Sharma" and it is instant: all the Sharmas sit together, you flip straight to them. Ask for "Sharma, Anurag" and it is still instant: within the Sharmas, the first names are sorted too. But now ask for everyone whose first name is "Anurag", with no last name. The book is useless. The Anurags are scattered across every single last name, one under Agarwal, one under Khan, one under Verma. You have to read the whole book. The sort order put last name first, so first name alone buys you nothing.

That is the leftmost-prefix rule, exactly. A composite index on (a, b) serves a query on a, or on a and b together, because those match the sort order from the left. It does nothing for a query on b alone, because b is only sorted inside each value of a. In the lab you build an index on (country, city) and watch the plan: filter on country, it SEARCHes; filter on country and city, it SEARCHes; filter on city alone, and the plan flips straight back to SCAN. Same index, sitting right there, ignored, because the query did not start from the left.

This is why column order in a composite index is a real design decision, not a formality. Put the column you always filter on first.

### The covering index, or printing the number next to the name (10 min)

Back to the phone book. Normally the index gives you the name and an arrow: "go to this house and ask for the phone number." Following that arrow, once per match, is the cost. If a query matches 100,000 rows, that is 100,000 little trips back to the table to fetch the one extra column you asked for.

Now imagine the phone book printed the number right there next to the name. You would never knock on a single door. That is a covering index: an index that already holds every column the query needs, so the database answers from the index alone and never touches the table. In SQLite the plan says USING COVERING INDEX.

In the lab you sum one column, amount, for a whole country. With a plain index on country, the planner SEARCHes the index for the country, then makes about 100,000 trips to the table to read each amount. With an index on (country, amount), amount is already sitting in the index, so there are zero trips. Same query, and on the reference machine it ran about 13 times faster. The cost was a slightly wider index. This is the trick behind a lot of "why is this one report so fast" moments in real systems.

### The two days the planner ignores your index (10 min)

You will hit this in production, so meet it here first. You add an index, you are sure it should help, and the query is still slow. You run EXPLAIN and the planner is doing a full scan. The index is right there. Why?

The first way you already saw: the leftmost-prefix miss. You filter on a column that is not at the front of the composite index, so it cannot be seeked.

The second way is the sneaky one: you wrapped the column in a function. An index on email is a sorted list of the email values as they are. The moment you write WHERE lower(email) = 'x', you are no longer asking about email, you are asking about lower(email), which is a different value the index knows nothing about. The sorted order does not help, so the planner scans every row and calls lower() on each one. In the lab this was the most dramatic result of the day, tens of thousands of times slower than the same lookup without the function. The fix in real databases is to index the expression itself (an expression or functional index on lower(email)) or to store a normalised column. The same trap bites with a leading-wildcard LIKE '%foo', with a type mismatch, and with an OR spread across two different columns.

The habit to build: when a query is slow, do not guess and do not add another index on a hunch. Run EXPLAIN, read whether it is a SCAN or a SEARCH, and fix the reason. The planner is not being difficult. It is telling you your query does not match the shape of your index.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-10-drills.md`](../notes/day-10-drills.md).

D1. Index on (country, city, created_at). For each query, say whether the index is used and how much of it: (1) WHERE country = 'IN'; (2) WHERE country = 'IN' AND city = 'Pune'; (3) WHERE city = 'Pune'; (4) WHERE country = 'IN' AND created_at > ?; (5) WHERE city = 'Pune' AND created_at > ?.

D2. A query runs SELECT status FROM orders WHERE user_id = ?, and you have an index on (user_id). What does the plan do after the index search? What one change makes it a covering index, and what will the plan say then?

D3. You have an index on email. Why does WHERE lower(email) = 'x@y.com' not use it? Give one fix, and name one more way a WHERE clause can silently kill an index.

D4. A table takes 10,000 inserts a second. What does each extra index cost on every insert? Give two reasons you would not add an index even though it speeds up one read.

D5. You often run WHERE user_id = ? AND created_at > ? ORDER BY created_at. Which composite index, (user_id, created_at) or (created_at, user_id), and why does putting the equality column before the range column matter?

Answers are in the Solutions section at the bottom. Try all five before you look.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-10-indexes/indexes.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-10-indexes/indexes.py).

It builds one SQLite table of 2 million rows, then runs four parts covering the five cases from this morning. For each query it prints the EXPLAIN QUERY PLAN line and the timing, so you watch the plan flip between SCAN and SEARCH with your own eyes. Standard library only, and it runs in a few seconds.

### Predict first

Fill in `PREDICTIONS` at the top. All four are ratios.

- P1. How many times faster is the SEARCH (single-column index) than the full SCAN (no index)?
- P2. How many times slower is the city-only query (index unusable, back to SCAN) than the country-and-city query (index used)?
- P3. How many times faster is the covering index than the non-covering one, for the same SUM?
- P4. How many times slower is WHERE lower(email) = ? (forced scan) than WHERE email = ? (index search)?

P3 is the one most people underestimate. P1 and P4 are large and will surprise you. Write your guesses down before you run anything.

### Fill in the TODOs

1. TODO 1 creates the single-column index on user_id, the one that turns the no-index SCAN into a SEARCH.
2. TODO 2 is the query that filters on city alone, the one the (country, city) index cannot serve. This is the leftmost-prefix rule showing up in the plan.
3. TODO 3 creates the covering index on (country, amount), so SUM(amount) is answered from the index alone.
4. TODO 4 is the query that defeats the email index by wrapping the column in lower().

```bash
cd labs/day-10-indexes
python3 indexes.py
```

### What you're going to discover

Part 1 is the base case, and it is dramatic: the same query goes from scanning 2 million rows to touching about 20, thousands of times faster, just by adding the index.

Part 2 is the leftmost prefix. Filter on country, SEARCH. Filter on country and city, SEARCH. Filter on city alone, and the plan says plain SCAN, even though both the city-only filter and the country-and-city filter return only a handful of rows. One can use the index and one cannot, purely because of column order.

Part 3 is the covering index. The plan prints USING COVERING INDEX, and the query runs several times faster than the plain index, because it skipped about 100,000 trips back to the table.

Part 4 is the humbling one. WHERE email = ? is instant. Wrap it in lower() and the same lookup scans every row, tens of thousands of times slower. The index exists. The function made it useless.

### Traps ⚠️

- The timing ratios are order of magnitude, not exact, and they wobble run to run. A point lookup is microseconds, near the timer's floor, so dividing a 30 ms scan by it gives a big, noisy number. Trust the plan (SCAN vs SEARCH), which is deterministic. The "close enough" band on the scoreboard is wide on purpose.
- The lab sums amount on purpose in Parts 2 and 4. If you select only columns that happen to be in the index, SQLite can scan the index itself as a covering scan and the plan wording changes to "SCAN ... USING COVERING INDEX", which muddies the lesson. Summing a column that is not in the index forces an honest plain SCAN.
- A real database (Postgres, MySQL) uses table statistics from ANALYZE to decide between an index and a scan, so for a low-selectivity filter it may rationally choose a scan even when an index exists. SQLite here is simpler, but the leftmost-prefix and function-wrapping rules hold everywhere.

### Deliverable

[`labs/day-10-indexes/RESULTS.md`](../labs/day-10-indexes/RESULTS.md) has a skeleton. Paste the output, and write one line for each of the two ignored indexes: why did a perfectly good index sit unused?

---

## Block 4: write (30 min) 📣

Your angle today is the humbling one, because it is the one people remember: "I created an index and the database flat out ignored it, twice." The two ignored-index plans make the best screenshots, the composite index refusing a city-only filter and the email index defeated by lower().

Example posts are on the [Day 10 posts](../shares/day-10-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the covering-index speedup you measured, and one thing you still cannot explain.

Day 11 is transactions and isolation levels. Today an index was a single sorted structure you either matched or did not. Tomorrow you open two connections at once and watch them step on each other, dirty reads, non-repeatable reads, phantoms, and the MVCC trick that lets a hundred people read and write without holding hands.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Index on (country, city, created_at). (1) country = 'IN': used, seeks on the first column. (2) country = 'IN' AND city = 'Pune': used, seeks on the first two columns, a two-column prefix. (3) city = 'Pune': not used for a seek, city is not the leftmost column, so it is a full scan. (4) country = 'IN' AND created_at > ?: the index seeks on country, but it cannot use created_at through the index because the middle column, city, is unconstrained, so created_at is applied as a filter after the country seek, not as an index range. (5) city = 'Pune' AND created_at > ?: not used, the leftmost column country is missing, so full scan. The pattern: the index works from the left and stops at the first gap.

D2. With an index on (user_id) only, the plan is a SEARCH on user_id, and then for every matching row it does a table lookup to read status, because status is not in the index. Change the index to (user_id, status). Now status is already in the index, the plan says USING COVERING INDEX, and there are no table lookups at all.

D3. The index on email stores email values in their original form, sorted by email. WHERE lower(email) = 'x@y.com' asks about a different value, lower(email), which the index does not hold, so the planner cannot seek and scans every row applying lower(). Fix: index the expression itself (an expression or functional index on lower(email)), or store a normalised lowercase column and index that. One more index-killer: a leading-wildcard LIKE '%foo', because the sort order starts from the front of the string; others are a type mismatch between the column and the literal, and an OR across two different columns.

D4. Every index is a second sorted structure that must be kept in order, so each insert, update, or delete of the indexed column now also writes into the index, another B-tree insert and occasionally a page split, on top of the table write. At 10,000 inserts a second, every extra index is 10,000 more small writes a second, plus the disk and the page-cache memory it occupies. Reasons not to add one: the column is low selectivity, for example a boolean matching half the table, where a scan is as cheap as the index; the table is write-heavy and the read it would speed is rare; the extra index bloats the working set so it no longer fits in cache and everything else slows down.

D5. Use (user_id, created_at): equality column first, range column second. The index is sorted by user_id, then by created_at within each user_id, so the seek to user_id = ? lands on a contiguous run of that user's rows already ordered by created_at. The range created_at > ? is then one continuous slice, and the ORDER BY created_at is free, no separate sort. With (created_at, user_id) the rows are ordered by created_at first, so a given user's rows are scattered all through the index and the user_id equality cannot be seeked. The rule is equality before range.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-10-indexes/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-10-indexes/solution.py).

TODO 1, the single-column index that turns a SCAN into a SEARCH:

```python
idx_user_sql = "CREATE INDEX idx_user ON events(user_id)"
```

TODO 2, the city-only query the composite index cannot serve. city is not the leftmost column of (country, city), so the plan flips back to a plain SCAN:

```python
city_only_sql = "SELECT SUM(amount) FROM events WHERE city = ?"
```

TODO 3, the covering index. It holds both country and amount, so SUM(amount) is answered from the index alone and the plan says USING COVERING INDEX:

```python
cover_sql = "CREATE INDEX idx_cover ON events(country, amount)"
```

TODO 4, the query that defeats the email index. The index is on email, not on lower(email), so wrapping the column forces a full scan:

```python
defeat_sql = "SELECT SUM(amount) FROM events WHERE lower(email) = ?"
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 2,000,000 rows.

```
==============================================================================
Part 1: no index (case a) vs a single-column index (case b)
==============================================================================
  Query: SELECT SUM(amount) FROM events WHERE user_id = 42424

  case a, NO index:
    EXPLAIN QUERY PLAN:  SCAN events
    [SCAN]  time:   33.997 ms

  case b, index on user_id:
    EXPLAIN QUERY PLAN:  SEARCH events USING INDEX idx_user (user_id=?)
    [SEARCH]  time:    0.007 ms

  the index turned a SCAN of 2,000,000 rows into a SEARCH of about 20.
  speedup: 4,916x faster.

==============================================================================
Part 2: composite index on (country, city), the leftmost-prefix rule
==============================================================================
  index: CREATE INDEX idx_cc ON events(country, city)
  (each query sums amount, which is NOT in the index, so the plan shows
   a plain SEARCH or SCAN instead of a covering one)

  filter on country only (the leftmost column):
    EXPLAIN QUERY PLAN:  SEARCH events USING INDEX idx_cc (country=?)
    [SEARCH]  time:   38.408 ms

  filter on country AND city (full prefix):
    EXPLAIN QUERY PLAN:  SEARCH events USING INDEX idx_cc (country=? AND city=?)
    [SEARCH]  time:    0.027 ms

  filter on city only (skips the leftmost column):
    EXPLAIN QUERY PLAN:  SCAN events
    [SCAN]  time:   51.284 ms

  country alone and country+city both SEARCH the index. city alone can
  not: the index is sorted by country first, so the cities are scattered
  all through it. The planner gives up and SCANs all 2,000,000 rows.
  both the city-only and the country+city filter match only a handful of
  rows, yet one scans everything. penalty: 1,905x slower.

==============================================================================
Part 3: covering index vs non-covering, for SUM(amount) WHERE country = ?
==============================================================================
  index: CREATE INDEX idx_country ON events(country)
  non-covering, must fetch amount from the table:
    EXPLAIN QUERY PLAN:  SEARCH events USING INDEX idx_country (country=?)
    [SEARCH]  time:   26.657 ms

  index: CREATE INDEX idx_cover ON events(country, amount)
  covering, amount is IN the index already:
    EXPLAIN QUERY PLAN:  SEARCH events USING COVERING INDEX idx_cover (country=?)
    [SEARCH]  time:    2.054 ms

  the covering index holds country AND amount, so SQLite never touches
  the table. Watch for USING COVERING INDEX in the plan above.
  the ~100,000 saved table lookups make it 13.0x faster.

==============================================================================
Part 4: the defeated index, wrapping the column in a function
==============================================================================
  index: CREATE INDEX idx_email ON events(email)
  (each query sums amount so the plan shows a plain SEARCH or SCAN)

  WHERE email = ? (uses the index):
    EXPLAIN QUERY PLAN:  SEARCH events USING INDEX idx_email (email=?)
    [SEARCH]  time:    0.005 ms

  WHERE lower(email) = ? (index defeated):
    EXPLAIN QUERY PLAN:  SCAN events
    [SCAN]  time:  110.362 ms

  the index is sorted by email, not by lower(email). SQLite can not use
  it, so it SCANs every row and calls lower() on each one.
  penalty: 23,441x slower for one small function wrapper.

==============================================================================
Scoreboard, predicted ratio vs actual
==============================================================================
  P1 single-index speedup      you =    5,000   actual =    4,915.7 x     close enough
  P2 leftmost-prefix penalty   you =    2,000   actual =    1,905.3 x     close enough
  P3 covering speedup          you =       10   actual =       13.0 x     close enough
  P4 function-defeat penalty   you =   20,000   actual =   23,441.3 x     close enough

==============================================================================
The numbers to carry
==============================================================================
  A single-column index turned a full scan into a point lookup, about
  4,916x faster. A covering index skipped ~100,000 table lookups to run
  13.0x faster than a plain one. And TWO perfectly good indexes got
  ignored: the composite index for a non-leftmost filter (1,905x slower),
  and the email index wrapped in lower() (23,441x slower). The index exists.
  The planner still SCANs. Shape your query to match the index, or the
  index you lovingly created does nothing.
```

The four numbers tell the story. P1, a single index turned a scan of 2 million rows into a point lookup, thousands of times faster, the result everyone expects. P3, the covering index ran about 13 times faster than the plain one, not because it searched any smarter but because it skipped roughly 100,000 trips back to the table. And the two humbling ones, P2 and P4: a composite index refused a city-only filter because city is not its leftmost column, and an email index was made useless by a single lower() wrapper. Both indexes existed. Both were ignored. That is the day: the plan, not your intention, decides whether the index does anything, so read the plan.

The exact ratios will differ on your machine and wobble run to run, because the fast queries are microseconds, near the timer's floor. The SCAN versus SEARCH plan is the stable, honest signal. That is the one to screenshot.

</details>
