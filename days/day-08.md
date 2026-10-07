---
title: "Day 8: how a row sits on disk"
parent: "Week 2: storage"
nav_order: 1
has_children: true
---

# Day 8
## How a row actually sits on disk, and why dashboards use a different database 💾

Today's one idea: a database file is nothing magical. It is a stack of fixed-size blocks called pages, usually 4 or 8 kilobytes each, and to read even one tiny row the database reads the whole page it lives on. Once you can see the bytes, the black box opens, and half of week 2 stops being scary.

Welcome to week 2. Last week was about speed and scale in the abstract. This week is about the thing that actually holds your data, and today we start at the very bottom: the layout of bytes on the disk.

---

## Before you start ⏪

You need Day 2's comfort with SQLite, and the index-seek idea from Day 5 (a lookup jumps to the right spot instead of scanning). Today you read a real database file's own header with Python, so a little comfort with bytes helps, but the lab walks you through it.

---

## Words you will meet today 📖

A page is the fixed-size block a database reads and writes in. SQLite defaults to 4 KB, Postgres to 8 KB. The database never reads half a page. It reads the whole thing, always.

A heap, or a table's data pages, is where the rows actually sit, packed into pages one after another.

A row store keeps all the columns of one row together in the same place on disk. Postgres, MySQL and SQLite are row stores. Fetching a whole record is cheap, because it is all in one spot.

A column store keeps each column apart, all the values of one column together. Redshift, Snowflake, ClickHouse and DuckDB are column stores. Scanning one column across millions of rows is cheap, because you read only that column.

OLTP is the day-to-day work of an app: fetch this user, add this order. Lots of small reads and writes of whole rows. Row stores are built for it.

OLAP is analytics: sum revenue by region over a year. Few columns, enormous number of rows. Column stores are built for it.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [The SQLite file format](https://www.sqlite.org/fileformat.html). You are going to parse this header yourself in the lab. Read "The database header" section; the 4 KB page and the magic string are right there.
- [DDIA chapter 3](https://dataintensive.net/), storage and retrieval. The spine of this whole week. Today, the opening on how data is laid out, and the row vs column section near the end.
- [CMU 15-445 notes on database storage](https://15445.courses.cs.cmu.edu/fall2023/notes/03-storage1.pdf). Andy Pavlo's lecture notes on pages and the slotted-page layout. Dense, excellent, free.

Watch, after the lab:
- [Column vs row oriented databases](https://www.youtube.com/watch?v=Vw1fCeD06YI) by Hussein Nasser, about 34 minutes. Thorough, and it is exactly the Part 3 result drawn out.
- Shorter option: [Row vs column oriented storage](https://www.youtube.com/watch?v=CNhi6KdMKj8) by BigData Thoughts, 17 minutes.

### The page is the unit of everything (15 min)

Here is the fact the whole week hangs on. A database does not read rows. It reads pages. A page is a fixed-size block, 4 KB in SQLite, 8 KB in Postgres, and it is the smallest thing the engine ever pulls off the disk. Ask for one 8-byte number from one row, and the database reads the entire 4 KB page that row sits on, because that is the only size it knows how to read.

This connects straight back to Day 1. The disk is slow per operation but reads in big sequential chunks well, so the database works in page-size chunks to make each slow disk trip count. It also explains the shape of everything on top. An index (Day 5, and tomorrow) is a tree of pages. A row that does not fit in a page needs special handling. A table twice as wide, with twice the bytes per row, has half as many rows per page, so a scan of it reads twice as many pages for the same number of rows. Row width is a performance decision, not just a schema one.

In the lab you open a real SQLite file and read its first 100 bytes with your own code. You will find the magic string, the page size, and the page count, and you will confirm that the file size is exactly page size times page count. No magic. A stack of pages.

### Why your app DB and your dashboard DB are different (10 min)

Now the day's big payoff. Say you have a table of a billion events, each row 500 bytes wide, and you want one number: the sum of one 8-byte column. In a row store, the sum has to read every row off the disk, all 500 bytes of each, just to reach the 8 bytes it cares about. That is 500 GB read to use 8 GB of it. In a column store, that one column lives apart, all its values together, so the sum reads 8 GB and nothing else. Same answer, a fraction of the work.

Flip it around for a different query. Fetch one user's whole profile: a row store has it all in one page, one read, done. A column store has that user's name in one place, email in another, age in another, so assembling one whole row means touching many columns. Now the row store wins.

That is the whole story. Row stores are fast at "give me this whole record," which is what apps do all day. Column stores are fast at "scan one field across everything," which is what analytics does. Neither is better. They are built for opposite jobs, and serious systems run both: a row store for the app, and a column store the data gets copied into for the dashboards. The lab measures the gap on your own machine, and it is large.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-08-drills.md`](../notes/day-08-drills.md).

D1. A table's rows are about 200 bytes each, and the database uses 8 KB pages. Roughly how many rows fit in one page? If you ask for a single 4-byte number from one row, how many bytes does the database actually read off the disk, at minimum?

D2. That table has 10 million rows at 200 bytes each. How many bytes is the table? How many 8 KB pages? If a full scan reads it sequentially at about 500 MB per second, how long does the scan take?

D3. A dashboard sums one 8-byte column over a billion-row table, where each full row is 500 bytes. How many bytes must a row store read? How many must a column store read? What is the ratio?

D4. Classify each query as row-store-friendly (OLTP) or column-store-friendly (OLAP): fetch one user's profile by id; total revenue per region for last year; add an item to a cart; count sign-ups per day for the last month.

D5. Postgres uses 8 KB pages. If it used 16 KB instead, what gets better and what gets worse, for a single-row lookup versus a big scan? State the tradeoff in one sentence.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-08-pages/page_lab.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-08-pages/page_lab.py).

It builds two SQLite files, then does three things. Part 1 opens one of them and reads the 100-byte header with your own code, proving the file is a stack of pages. Part 2 works out how many rows fit in a page. Part 3 builds a column store beside the row store and races them on summing a single column.

Standard library only, a few seconds to run.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The page size of a default SQLite file, in bytes.
- P2. How many ~180-byte rows fit in one 4096-byte page.
- P3. The row-store file size for 500,000 fat rows, in megabytes.
- P4. How many times smaller the column-only file is than the row store's.

P1 you can get from this morning's reading. P4 is the one to feel: predict it before you see it.

### Fill in the TODOs

1. TODO 1 parses the page size and page count out of the header bytes with `struct.unpack`. This is you reading the file format by hand.
2. TODO 2 is rows per page, page size over bytes per row.
3. TODO 3 is the `SUM(val)` query for each store, same aggregate, different table.
4. TODO 4 is the headline ratio, how many times bigger the row-store file is.

```bash
cd labs/day-08-pages
python3 page_lab.py
```

### What you're going to discover

Part 1 prints "SQLite format 3" straight out of the raw bytes, and the file size comes out exactly page size times page count. A database file really is just pages.

Part 3 is the day. Summing one column, the row store reads tens of megabytes, the column store reads a fraction of that, for the identical answer. On the reference machine the row-store file was about 16 times bigger and read about 16 times more. The time gap is smaller than the size gap, because the operating system caches both files in memory after the first run, so you are often timing a warm cache. The bytes-on-disk ratio is the honest number, the one that decides things when the data is too big to cache.

### Traps ⚠️

- If Part 1 says the file size does not match page size times page count, your `struct` parse is reading the wrong bytes. Page size is a 2-byte big-endian number at offset 16, page count a 4-byte big-endian number at offset 28.
- The scan times wobble with the OS cache. Run it twice. Trust the size ratio over the time ratio.

### Deliverable

[`labs/day-08-pages/RESULTS.md`](../labs/day-08-pages/RESULTS.md) has a skeleton. Paste the output, and write one line: to sum one column, how many bytes did each store read, and why so different?

---

## Block 4: write (30 min) 📣

Your angle today is opening the black box: "I read my database file's header with 20 lines of Python. It is literally a stack of 4 KB pages. Then I learned why the database behind an app and the one behind a dashboard are built the opposite way." The header bytes and the row-vs-column size ratio both make good screenshots.

Example posts are on the [Day 8 posts](../shares/day-08-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the row-store vs column-store ratio you measured, and one thing you still cannot explain.

Day 9 is the two great families of storage engines, B-trees and LSM trees, one built for reads and one for writes. Today you saw that everything lives in pages. Tomorrow you see the two ways to arrange those pages, and why your database is fast at exactly one of reading or writing.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. 8192 / 200 is about 40 rows per page. To read one 4-byte number, the database still reads the whole 8 KB page it sits on, so 8,192 bytes minimum for 4 bytes of data. The page is the unit, always.

D2. 10,000,000 × 200 bytes is 2 GB. At 8 KB per page that is 2,000,000,000 / 8,192, about 244,000 pages. A sequential scan at 500 MB/s reads 2 GB in about 4 seconds. Scans are bounded by bytes divided by bandwidth, which is why halving the row width roughly halves the scan.

D3. The row store reads every full row to reach one column: 1,000,000,000 × 500 bytes is 500 GB. The column store reads only the 8-byte column: 1,000,000,000 × 8 is 8 GB. The ratio is about 62x, and a real column store also compresses that column hard, often making it another several times smaller. This is why you do not run analytics on your app's row-store database.

D4. Fetch one user's profile: OLTP, row store, it is one whole record in one page. Revenue per region for a year: OLAP, column store, few columns over huge rows. Add an item to a cart: OLTP, row store, a small write of one row. Sign-ups per day for a month: OLAP, column store, an aggregate over many rows touching few columns.

D5. With 16 KB pages, a single-row lookup reads more bytes than it needs (wasteful, since it still wants one small row), but a big scan does fewer, larger sequential reads and the index tree is shallower, so fewer seeks. The one-sentence tradeoff: bigger pages help scans and hurt tiny point reads, so OLTP leans smaller and OLAP leans larger, and 8 KB is Postgres splitting the difference.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-08-pages/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-08-pages/solution.py).

TODO 1, parse the header:

```python
page_size = struct.unpack(">H", head[16:18])[0]
page_count = struct.unpack(">I", head[28:32])[0]
```

`>H` is a big-endian 2-byte unsigned number, `>I` a big-endian 4-byte one. The offsets 16 and 28 come straight from the SQLite file format spec you read this morning.

TODO 2, rows per page:

```python
rows_per_page = page_size / bytes_per_row
```

TODO 3, the same aggregate on each store:

```python
row_sql = "SELECT SUM(val) FROM events"
col_sql = "SELECT SUM(val) FROM events_val"
```

TODO 4, the size ratio:

```python
size_ratio = row_sz / col_sz
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 500,000 rows.

```
Part 1: read the database file's own header, byte by byte
  magic string:  b'SQLite format 3\x00'
  page size:     4096 bytes
  page count:    21,796
  file size:     89,276,416 bytes
  page_size x page_count = 89,276,416  (matches)

Part 2: how many rows fit in one page
  500,000 rows in 89,276,416 bytes = 178.6 bytes per row
  so about 22.9 rows fit in one 4096-byte page

Part 3: add up ONE column. Row store vs column store.
  row store:      89.3 MB on disk,  SUM(val) in   25.3 ms
  column store:    5.5 MB on disk,  SUM(val) in    9.1 ms
  the row-store file is 16.4x bigger, and the scan is 2.8x slower

Scoreboard
  P1 page size            actual =    4,096 bytes
  P2 rows per page        actual =     22.9
  P3 row-store size       actual =     89.3 MB
  P4 column store smaller actual =     16.4 x
```

Part 1 is the quiet thrill: "SQLite format 3" comes out of bytes 0 to 15 of the raw file, and the file size is exactly 4096 times 21,796. You proved, with your own code, that a database is a stack of pages.

Part 2: the fat row is about 179 bytes, so only 23 fit in a 4 KB page. Make the row twice as wide and you halve that, and every scan doubles.

Part 3: to sum one column across 500,000 rows, the row store read all four fat text columns of every row, 89 MB, because they share a page with the number it wanted. The column store kept that number apart, so it read 5.5 MB, about 16 times less. The scan was only 2.8x faster rather than 16x, because after the first run the OS held both files in memory, so this is a warm-cache time. The 16x is the bytes-off-disk number, and that is the one that matters once the data is bigger than memory. This is the whole reason a column store exists, measured on your laptop.

</details>
