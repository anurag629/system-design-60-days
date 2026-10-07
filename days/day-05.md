---
title: "Day 5: designing an API"
parent: "Week 1: ground truth"
nav_order: 5
has_children: true
---

# Day 5
## Designing an API, and why "page 5000" quietly disappeared from the web 📄

Today's one idea: the obvious way to paginate, `LIMIT 20 OFFSET 100000`, gets slower on every single page, because the database has to count past everything it skips. The fix is one line of SQL, and once you see it you will notice that infinite scroll everywhere already uses it.

An API is a contract. Other people's code, and your own app, depend on it behaving the same way tomorrow. So today is half about taste (what a clean endpoint looks like) and half about one measurement that decides whether your "load more" button stays fast at ten rows or ten million.

---

## Before you start ⏪

Day 2's SQLite skills are all you need. Same idea as that day: build a big table, then time two ways of reading from it. If you did Day 2, this will feel familiar and a bit faster.

---

## Words you will meet today 📖

An endpoint is one URL your API answers on, together with the method. `GET /orders/42` is an endpoint. `POST /orders` is a different one.

A resource is the thing an endpoint is about: an order, a user, a post. Good APIs are organised around resources (nouns), and use the HTTP method (the verb) to say what to do with them.

Pagination is handing back a long list a little at a time, one page per request, instead of all ten million rows at once.

Offset pagination says "skip the first N rows, give me the next 20." It is `LIMIT 20 OFFSET N`. Simple, and the default in almost every tutorial.

Keyset pagination, also called cursor or seek pagination, says "give me the 20 rows after the last id I saw." It is `WHERE id > :last_seen ... LIMIT 20`. No skipping.

A cursor is just the bookmark you carry between pages. For keyset pagination it is the id (or sort key) of the last row you saw.

Idempotent means doing it twice is the same as doing it once. `GET` is idempotent, reading a page changes nothing. Charging a card is not, unless you make it so.

An idempotency key is a unique id the client attaches to a write, so that if the request is retried after a timeout, the server recognises the repeat and does the work only once. This is how UPI does not charge you twice when the app says "failed" and you tap pay again. 💸

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [No Offset](https://use-the-index-luke.com/no-offset) by Markus Winand. One page, and it is the whole lab in words: why offset is slow and wrong, and what to do instead.
- [Stripe API: pagination](https://docs.stripe.com/api/pagination). A real, excellent API doing cursor pagination. Notice they never offer "jump to page 500."
- [Stripe API: idempotent requests](https://docs.stripe.com/api/idempotent_requests). The clearest short explanation of idempotency keys anywhere.

Watch these two, after the lab:
- [Pagination optimization: keyset vs offset](https://www.youtube.com/watch?v=XHQ8QhslXS0), 5 minutes. The lab's result, drawn out.
- [What is API idempotency and why is it important?](https://www.youtube.com/watch?v=I08syTslan8) by Be A Better Dev, 12 minutes. The retry story, with code.

### What a good endpoint looks like (15 min)

An API is a promise you make to other code. The whole craft is making that promise easy to use and hard to misuse. A few habits get you most of the way.

Organise around resources, which are nouns, and let the HTTP method be the verb. You do not need an endpoint called `/createOrder` and another called `/getOrder`. You need one resource, `orders`, and the method says the rest.

| You want to | Method and path | Success code |
|---|---|---|
| Create an order | `POST /orders` | 201 Created |
| Fetch order 42 | `GET /orders/42` | 200 OK (404 if missing) |
| List a user's orders | `GET /users/7/orders?limit=20` | 200 OK |
| Cancel order 42 | `POST /orders/42/cancel` | 200 OK |

Return honest status codes. 200 for a fine read, 201 when you made something, 400 when the caller sent nonsense, 401 and 403 for "who are you" and "not allowed", 404 for missing, 429 for "slow down", 500 when you broke. A caller writes very different code for a 400 than for a 500, so lying with your status codes makes everyone's day worse.

Make writes safe to retry. The network will time out on a request that actually succeeded, and the client will retry. If that retry charges the card again, you have a bug that only shows up on bad wifi, which is to say in production, at scale, blamed on you. The fix is the idempotency key from this morning's reading, and it is the same insight as Day 4's queues: the network delivers your message at least once, so make a repeat harmless.

Version from day one. Put `/v1/` in the path, or a version header. The day you need `/v2/` and did not plan for it is a bad day.

### Why offset pagination falls over (10 min)

Here is the trap, and almost everyone walks into it because the tutorials teach it.

You have a feed. Page 1 is `LIMIT 20 OFFSET 0`. Page 2 is `OFFSET 20`. Page 500 is `OFFSET 9980`. Looks harmless. But think about what the database does to serve page 500: it has no way to jump to row 9,980. It reads row 1, row 2, all the way to row 9,980, throws every one of them away, and only then starts collecting your 20. Page 50,000 reads a million rows to hand you twenty. The deeper the page, the slower it gets, forever.

Keyset pagination fixes it by remembering where you were. Instead of "skip 9,980 rows", you say "give me 20 rows where id is greater than the last id I saw." The database jumps straight there using the index it already has on id, the same index seek you measured on Day 2 that was 14,000 times faster than a scan. Every page costs the same, whether it is page 1 or page one million.

There is a second problem with offset, and it is worse than slow. It shows wrong results. On a newest-first feed, if three new posts arrive between you loading page 1 and page 2, offset page 2 shifts down by three and shows you three posts you already saw. Keyset does not care, because the cursor is anchored to a row, not to a position. The lab makes both of these happen in front of you.

This is why, if you watch closely, big sites let you scroll forever but never let you type "go to page 500" any more. Infinite scroll is cursor pagination wearing a nice coat. 🧥

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-05-drills.md`](../notes/day-05-drills.md).

D1. A feed shows 20 posts per page. A user scrolls to page 500. With offset pagination, how many rows does the database read to build that one page? With keyset pagination, how many? What is the ratio?

D2. A payment API. The client sends "charge ₹500", the network times out before the response comes back, so the client retries. What happens without an idempotency key? What happens with one? What makes a good key, and what makes a bad one?

D3. Design the four endpoints for a food delivery app: place an order, fetch one order, list a restaurant's orders for today, and mark an order delivered. Give the method, the path, and the success status code for each.

D4. A newest-first feed, 10 posts per page, offset pagination. Between a user loading page 1 and tapping for page 2, five new posts are published. How many posts does the user see twice? Now instead suppose five already-seen posts were deleted. How many posts does the user miss entirely?

D5. A client has to sync all 10 million rows of a table through your API, 20 rows per page, keyset pagination, and each request takes 50 ms (the network, not the database, is the slow part). How long does a full sync take? You change the page size to 200. How long now, and what did it cost you?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-05-pagination/pagination_lab.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-05-pagination/pagination_lab.py).

It builds a 2,000,000 row table once, then does three things. Part 1 fetches one page from different depths, both ways, and prints the query planner's reason for the difference. Part 2 pages through the whole table both ways and counts how many rows each approach makes the database touch. Part 3 reproduces the duplicate-rows bug on a tiny feed so you can see offset return wrong results, not just slow ones.

Standard library only. The first run spends a few seconds building the table, then the whole thing runs in under a minute.

### Predict first

Fill in `PREDICTIONS` at the top of the file. The table has 2,000,000 rows, a page is 20 rows.

- P1. Milliseconds to fetch the first page with offset (depth 0).
- P2. Milliseconds to fetch a deep page with offset, skipping 1,000,000 rows.
- P3. Milliseconds to fetch that same deep page with keyset.
- P4. How many times slower is the deep offset page than the deep keyset page?

P1 and P3 are almost a gift once you have read the morning's material. P2 is the one to sit with. P4 is where people are wildly off, usually guessing 2x or 10x. Write a number down anyway.

### Fill in the TODOs

1. TODO 1 is the offset query: `ORDER BY id LIMIT ? OFFSET ?`.
2. TODO 2 is the keyset query: `WHERE id > ? ORDER BY id LIMIT ?`. Notice there is no OFFSET at all.
3. TODO 3 advances the cursor in the keyset walk. Without it the loop asks for the same first page forever, so the lab stops you if you forget.
4. TODO 4 counts the rows the database had to touch for an offset page, which is `offset + len(rows)`. This produces the number that made my jaw drop.

```bash
cd labs/day-05-pagination
python3 pagination_lab.py
```

### What you're going to discover

The offset column climbs as you go deeper: fine near the top, then tens of milliseconds, then seconds. The keyset column does not move at all, from page one to page one million. The query planner line tells you why in two words: `SCAN` versus `SEARCH`.

Part 2 has the number I want you to carry. Walking the whole table by keyset touches two million rows, once each. Walking it by offset would touch about twenty billion rows, because it re-reads the start of the table on every page. Same data, same pages. One is a line, the other is a triangle.

Part 3 is the quiet one. Offset page 2 hands back three rows you already saw on page 1, after three new posts arrived. Keyset hands back the correct next page. Slow is annoying. Wrong is a bug report.

### Traps ⚠️

- The shallow pages are sub-millisecond, close to timer noise. The lab takes the fastest of several runs, so trust the deep rows and the ratio, not the third decimal of the top row.
- If part 2's keyset walk seems to hang, you forgot TODO 3 and the cursor never advances. The lab catches this and tells you.
- Keyset is easy when you sort by a unique column like id. When you sort by something with ties, say `created_at` where two rows share a timestamp, the cursor needs a tiebreaker (sort by `created_at, id` and carry both). The lab sticks to id to keep the lesson clean, but remember this the day you paginate by date.

### Deliverable

[`labs/day-05-pagination/RESULTS.md`](../labs/day-05-pagination/RESULTS.md) has a skeleton. Paste the output, and write one line on the Part 2 number: how many rows did offset touch to walk the table, and how does that compare to keyset?

---

## Block 4: write (30 min) 📣

Your angle today writes itself: "I fetched the same 20 rows from the top of a table and from a million rows deep. The deep one was 600 times slower, and the fix is one line of SQL." The query-planner `SCAN` versus `SEARCH` line makes a great screenshot. The duplicate-rows result from Part 3 is a strong second post, because most people have never seen offset be wrong, only slow.

Example posts, written with the reference run's numbers, are on the [Day 5 posts](../shares/day-05-posts.md) page. Swap in your numbers and put them in your own words. Drafts go in `shares/`.

---

## End of day: log it 📝

Add a Day 5 entry to your progress log with these three things:

1. What you completed, and what you skipped.
2. Your deep offset time, your keyset time, and the ratio.
3. One thing you still can't explain.

Then compare your work with the solutions below. Day 6 is more than one server: load balancers, health checks, and killing a server while it serves traffic.

---

## Solutions 🔑

Open these only after you've done the day. Reading answers first feels like learning and isn't.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Page 500 at 20 per page starts at offset (500 - 1) × 20 = 9,980. Offset reads 9,980 skipped rows plus 20 returned, so 10,000 rows for one page. Keyset reads 20. That is 500x more work for the same twenty rows, and it gets worse every page.

D2. Without a key, the server sees two separate "charge ₹500" requests and charges twice. With a key, the client sends the same unique id on both the first try and the retry. The server records that it already handled that key and returns the original result instead of charging again. A good key is generated by the client, unique to this one logical operation, and stable across retries of that same intent (a UUID made before the first attempt). A bad key is anything the server generates (too late, the retry gets a new one), anything reused across different operations (now two real charges collapse into one), or a timestamp that changes on retry.

D3. One clean answer:
- Place an order: `POST /orders`, returns 201.
- Fetch one order: `GET /orders/42`, returns 200, or 404 if it does not exist.
- A restaurant's orders for a given day: `GET /restaurants/9/orders?date=<the day>&limit=20`, returns 200.
- Mark delivered: `POST /orders/42/deliver`, or `PATCH /orders/42` with `{"status": "delivered"}`, returns 200.
The exact paths are a matter of taste. What is not a matter of taste: creating returns 201, missing returns 404, and the write endpoints should be safe to retry.

D4. Five new posts push everything down by five, so offset page 2 (which skips the first 10) now starts five rows earlier than it should, and five posts from the end of page 1 appear again. The user sees five posts twice. If five already-seen posts were deleted instead, page 2 shifts up by five and the user misses five posts entirely, never seeing them. Shift up, you skip. Shift down, you repeat. Keyset avoids both because it asks for rows after a specific id, not after a position.

D5. 10,000,000 / 20 = 500,000 requests. At 50 ms each, that is 25,000 seconds, about 6.9 hours. At 200 per page: 50,000 requests × 50 ms = 2,500 seconds, about 42 minutes, 10x faster because you paid the 50 ms network cost a tenth as often. The cost: each response is 10x bigger, uses more memory on both ends, takes a touch longer for the database to build, and if a request fails you re-fetch 200 rows instead of 20. Bigger pages trade more work per request for fewer requests. Past a point, usually a few hundred to a thousand rows, the response size starts to hurt more than the saved round trips help.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-05-pagination/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-05-pagination/solution.py).

TODO 1, the offset query:

```python
return conn.execute(
    "SELECT id, author_id, created_at FROM posts ORDER BY id LIMIT ? OFFSET ?",
    (PAGE, offset),
).fetchall()
```

TODO 2, the keyset query. The whole difference is here, and it is one `WHERE`:

```python
return conn.execute(
    "SELECT id, author_id, created_at FROM posts WHERE id > ? ORDER BY id LIMIT ?",
    (cursor, PAGE),
).fetchall()
```

TODO 3, advance the cursor to the last id you saw:

```python
cursor = rows[-1][0]
```

Forget this and the keyset walk asks for `id > 0` forever, which is page 1 on repeat. That is why the lab checks and stops you.

TODO 4, count what the database had to touch:

```python
rows_touched += off + len(rows)
```

`off` is the rows it reads and discards to honour the OFFSET, and `len(rows)` is what it returns. Summed over a full walk, this is the 20 billion.

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 2,000,000 rows. Your absolute times depend on your machine, but the shape and the ratios will match.

```
Part 1: fetch ONE page of 20 rows, from different depths
         depth   offset ms   keyset ms  offset / keyset
             0       0.008       0.008               1x
         1,000       0.011       0.008               1x
        10,000       0.039       0.008               5x
       100,000       0.335       0.008              42x
     1,000,000       5.6         0.009             620x
     1,999,980      11.2         0.009            1240x
    offset deep : SCAN posts
    keyset deep : SEARCH posts USING INTEGER PRIMARY KEY (rowid>?)

Part 2: page through the table in pages of 100
  keyset: walked all 2,000,000 rows in 20,000 pages, 0.32 s, touched 2,000,000 rows
  offset: walked the first 200,000 rows in 2,000 pages, 0.71 s, touched 200,100,000 rows
  To finish the whole table with offset would touch about 20 billion rows
  and take roughly 71 s, versus 0.32 s for keyset.

Part 3: offset does not just get slow, it shows wrong results
  OFFSET  page 1: [20, 19, 18, 17, 16]
          page 2: [18, 17, 16, 15, 14]
          shown twice: [18, 17, 16]
  KEYSET  page 1: [20, 19, 18, 17, 16]   (cursor = 16)
          page 2: [15, 14, 13, 12, 11]
          shown twice: nothing
```

The depth column is the whole story. At the top of the table the two are identical, both under 10 microseconds, because offset has nothing to skip. By a million rows deep, offset is around 600x slower, and at the end of the table it is past 1,000x. Keyset never moves off 9 microseconds, because `WHERE id > ?` is an index seek, exactly the Day 2 lesson: the database jumps to the right leaf of the B-tree instead of walking there.

The query planner says it plainly. `SCAN` means it reads every row it skips. `SEARCH ... USING INTEGER PRIMARY KEY` means it seeks straight to the row and stops. You could have predicted the whole table from those two words.

Part 2 is the number I keep. Keyset touches each row once, two million in total. Offset, walked to the end, would touch about twenty billion, because page N re-reads the N pages before it. That is the difference between a line and a triangle, between O(n) and O(n²), shown in rows instead of Big-O notation.

Part 3 is the part that turns "offset is slow" into "offset is wrong." Three posts arrived between page 1 and page 2, and offset handed back `[18, 17, 16]` a second time. On a real feed that is a user seeing the same three tweets twice and wondering if your app is broken. Keyset's cursor was pinned to id 16, so page 2 continued cleanly from 15. Slow you can sometimes live with. Wrong files a bug.

</details>
