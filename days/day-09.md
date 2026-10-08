---
title: "Day 9: B-trees and LSM trees"
parent: "Week 2: storage"
nav_order: 2
has_children: true
---

# Day 9
## The two families of storage engine, and why one of them hates random writes 🌳

Today's one idea: there are really only two ways a database keeps a big pile of records on disk. One keeps everything sorted and edits it in place (a B-tree, like SQLite, Postgres and MySQL). The other never edits in place, it just appends and tidies up later (an LSM tree, like RocksDB, Cassandra and LevelDB). The first is wonderful at reads and miserable at random writes. The second is the other way round. Once you see why, half the "which database should I use" questions answer themselves.

Yesterday you saw that everything lives in pages. Today you see the two ways to arrange those pages over time, and you measure, on your own laptop, the one gap that decides which engine a system picks.

---

## Before you start ⏪

You need Day 8 fresh in your head: a database file is a stack of fixed-size pages, and the engine reads and writes a whole page at a time, never half of one. Everything today is about what happens to those pages when you insert rows in a nice order versus a nasty one. Day 2's comfort with SQLite is enough Python for the lab.

---

## Words you will meet today 📖

A B-tree (really a B+ tree in most databases) is a shallow, wide, sorted tree of pages. The keys stay in sorted order, and a lookup walks from the root down to a leaf in three or four hops. This is the default index structure in almost every relational database.

A page split is what a B-tree does when the leaf page a new row belongs on is already full. It cuts the page in two, moves half the rows to a fresh page, and updates the parent. Cheap when it is rare, painful when it is constant.

An LSM tree, log-structured merge tree, never updates a page in place. New writes go into an in-memory table, and when that fills it is flushed to disk as a sorted run. Reads merge across runs, and a background job compacts runs together.

A memtable is the LSM's in-memory buffer, the place every write lands first. Fast, sorted, and backed by a write-ahead log so a crash does not lose it.

A sorted run, or SSTable, is one immutable sorted file the LSM flushed from a memtable. The store is a memtable plus a growing stack of these.

Compaction is the LSM's background tidying: merge several sorted runs into fewer, drop overwritten and deleted keys. It is the rent you pay for cheap writes.

Read amplification is the LSM's cost: one logical read may have to check the memtable plus several runs, so it touches more places than a B-tree's single path.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [DDIA chapter 3](https://dataintensive.net/), storage and retrieval. The spine of this week. Today, the "SSTables and LSM-trees" section and the "B-trees" section that follows it, then Kleppmann's own side-by-side comparison at the end. If you read one thing, read this.
- [Log Structured Merge Trees](https://www.benstopford.com/2015/02/14/log-structured-merge-trees/) by Ben Stopford. The clearest short explanation of why appending and merging beats update-in-place for writes. A little old, still the best on-ramp.
- [What is an LSM Tree?](https://www.helius.dev/blog/lsm-tree-explained) on the Helius blog. Modern, visual, and it walks the memtable, SSTables, bloom filters and compaction with real RocksDB commands.

Watch, after the lab:
- [The Secret Sauce Behind NoSQL: LSM Tree](https://www.youtube.com/watch?v=I6jB0nM9SKU) by ByteByteGo, about 7 minutes. Tight, well drawn, exactly the write side of today.
- Optional, for the B-tree and page side: [How Do Databases Store Tables on Disk?](https://www.youtube.com/watch?v=DbxddGtHl70) by Hussein Nasser, about 19 minutes. Bridges yesterday's pages into today's trees.

### Two ways to keep a sorted pile of records (16 min)

Imagine you run the attendance register for a huge college, and the rule is that the register must always be in sorted order by roll number. You have two ways to work.

The first way: whenever a student arrives, you find their exact place in the register and write them in right there. The register is always perfectly sorted, so finding anyone later is instant, you just binary-search to their page. This is the B-tree. Keep everything sorted, edit in place, pay a little on every write so that every read is cheap. SQLite, Postgres, MySQL and basically every relational database index work this way.

The second way: when a student arrives, you scribble their name on whatever notepad is in your hand, in arrival order, no sorting at all. When the notepad fills, you sort that one notepad and file it on a shelf. Reads are now harder, because a name could be on the current notepad or on any shelved one, so you check several places. But writing is trivially fast and you never reshuffle anything. This is the LSM tree. Append now, sort small batches, merge later. RocksDB, Cassandra, LevelDB, ScyllaDB and most write-heavy stores work this way.

That is the whole fork in the road. Neither is cleverer. They make opposite bets about whether reads or writes are the thing you cannot afford to make slow.

### Why a B-tree hates random writes (12 min)

Here is the part you will measure today, and it is the one that surprises people. A B-tree is not equally happy with all writes. It loves keys that arrive in order and struggles with keys that arrive shuffled.

Think back to the register. If students happen to arrive already sorted by roll number, you are always writing onto the last page, and that page stays open on your desk. Easy. This is an auto-increment integer primary key: every new row has a bigger key than the last, so it always belongs on the rightmost leaf of the tree, which is sitting hot in the cache. Almost no page splits, almost no scattered writes.

Now let students arrive in random order. A roll number from the middle of the alphabet forces you to open a page deep in the register, and if that page is full you split it, shove half the rows onto a new page, and fix the parent. The next student is somewhere else entirely, so you put the first page away and open another. You are thrashing: every write touches a different cold page, and your desk (the cache) is too small to hold them all. This is a random UUID primary key, and it is why "just use a UUID for the id" quietly wrecks insert throughput on a large table. The data is identical. Only the order changed, and the order is everything.

This connects straight to Day 8. The engine writes whole pages. Sequential keys keep rewriting the same one hot page. Random keys dirty a fresh scattered page every time, and once the tree is bigger than the cache, each of those pages is a separate trip to disk. In the lab you insert the same 300,000 rows both ways and watch random come out many times slower.

### The LSM bargain: cheap writes, pricier reads (12 min)

The LSM sidesteps the whole problem by refusing to update in place. A write appends to the memtable and to a write-ahead log, and returns. It does not go looking for the right page, it does not split anything, it does not care one bit what the key is or what order the keys arrive in. That is why its write path is flat: sequential or shuffled, it is the same cheap append. In the lab you will see the random and sequential write times come out within a whisker of each other, while the B-tree's differ by a factor of ten or more.

When the memtable fills, the LSM sorts it once and flushes it to disk as an immutable sorted run. Sorting one small batch in memory is cheap, and writing the run out is one long sequential write, never the scattered page writes the B-tree pays. The writes that reach the disk are append-friendly, which is exactly what both spinning disks and SSDs prefer.

So what is the catch? Reads. The newest value for a key might be in the memtable, or in the most recent run, or in an older one. So a point read checks the memtable first, then each run from newest to oldest, until it finds the key. That is several lookups where a B-tree does one. A read for a key that is not there is the worst case: it has to check every single place before giving up. Real LSM engines soften this two ways. A bloom filter sits in front of each run and answers "definitely not here" cheaply, so most runs get skipped without a disk read. And compaction keeps merging runs into fewer, bigger ones so the stack never grows without bound. The lab measures the raw read tax first, so you feel why those two tricks exist.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-09-drills.md`](../notes/day-09-drills.md).

D1. You insert 1,000,000 rows into a B-tree table with 50,000 leaf pages, and your page cache holds 5,000 of them (10 percent). With random keys, what fraction of inserts land on a page that is not in the cache? With an auto-increment key, why does the whole job stay on essentially one hot page?

D2. An LSM flushes a sorted run every 64 MB, and you write 2 GB before any compaction runs. How many sorted runs are on disk? To read a key that is not in the memtable, how many runs might a naive LSM have to check in the worst case?

D3. A B-tree with 8 KB pages changes one 100-byte row. At minimum, how many bytes must it write to disk to do that, and what does that say about its write amplification? How is the LSM's write amplification different in shape, even though it is not zero?

D4. Classify each workload as B-tree-friendly or LSM-friendly, and say why in a few words: a banking ledger with heavy point reads and in-place updates; an append-only event log taking 500,000 writes per second; a time-series metrics store; the users table of a normal web app with balanced reads and writes.

D5. An LSM has 8 sorted runs, each with a bloom filter at a 1 percent false-positive rate. For a key that is absent, roughly how many runs does the lookup actually read from disk on average? What problem does that solve, and what does it cost you?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-09-btree-lsm/storage_engines.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-09-btree-lsm/storage_engines.py).

It is in three parts. Part 1 inserts 300,000 rows into a SQLite B-tree twice, once with sequential keys and once with random keys, and times both. Part 2 builds a tiny LSM writer, a memtable that appends and flushes sorted runs, and times it on sequential versus random keys. Part 3 reads keys back out of the LSM and counts how many places each read has to touch.

Standard library only, sqlite3 is the B-tree, and it runs in a few seconds and cleans up every file it makes.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. Inserting 300,000 rows with random primary keys versus sequential ones, into the same B-tree. How many times slower is random?
- P2. The LSM write path is a plain append. Writing the same rows in random order versus sequential order, what is the time ratio random over sequential? (1.0 means order does not matter at all.)
- P3. The LSM flushes a sorted run every 70,000 writes. For 300,000 writes, how many sorted runs land on disk?
- P4. To answer a point read, the LSM checks the memtable plus every run. For a key that is absent, how many places must it touch?

P1 is the one to feel in your gut before you run it. Write down a number. Most people guess 2 or 3, and the real answer is bigger.

### Fill in the TODOs

1. TODO 1 is the B-tree INSERT statement, the write whose cost you are measuring.
2. TODO 2 is the slowdown factor, random time over sequential time. The headline of Part 1.
3. TODO 3 is the flush: sort the memtable into a run before writing it. This one line is the whole LSM idea, append unsorted, sort in small batches.
4. TODO 4 is the read tax: how many places a point read must check, the number of runs plus the memtable.

```bash
cd labs/day-09-btree-lsm
python3 storage_engines.py
```

### What you're going to discover

Part 1 is the shock. The same 300,000 rows, the same keys, the same payload. The only difference is the order the keys arrive in, and random comes out around 11 times slower than sequential on the reference machine. That is the B-tree splitting pages and writing scattered pages that spill out of the cache on every commit, while the sequential run keeps rewriting one hot rightmost page.

Part 2 is the relief. The LSM's append write path comes out almost exactly the same for sequential and random, a ratio near 1.0, because appending never looks at the key. The only place order shows up at all is the background sort at flush time, and even that writes its run out in one sequential pass.

Part 3 is the honest bill. Reading one key back, the LSM had to check the memtable plus all four runs, five places for a key that is not there, where a B-tree walks a single root-to-leaf path. That is the read amplification that bloom filters and compaction exist to fight.

### Traps ⚠️

- If your B-tree slowdown is only a little above 1, your machine may be caching the whole file. The lab pins SQLite's cache to 8 MB on purpose, and commits in batches, so the random writes actually have to leave the cache. Do not raise the cache size and then wonder where the gap went.
- The LSM write ratio will wobble a bit run to run, maybe 0.9 to 1.2. That is still "flat". The point is it is near 1 while the B-tree is near 11. Trust the contrast, not the third decimal.
- The background sort for random keys really is slower than for sorted keys (that is just how sorting works). That is fine. It is off the write path, and it does not touch the disk in a scattered way. Do not mistake it for the B-tree's problem.

### Deliverable

[`labs/day-09-btree-lsm/RESULTS.md`](../labs/day-09-btree-lsm/RESULTS.md) has a skeleton. Paste the output, and write one line: random B-tree inserts were how many times slower than sequential, and why did the LSM not care about order?

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise: "I inserted the same 300,000 rows into a database twice, changing only the order of the keys, and random was 11 times slower. That one gap is why RocksDB and Cassandra exist." The scoreboard, B-tree 11x versus LSM flat, is the screenshot.

Example posts are on the [Day 9 posts](../shares/day-09-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the B-tree random-versus-sequential slowdown you measured, and one thing you still cannot explain.

Day 10 is indexes for real: how the B-tree you met today becomes the index that makes a WHERE clause fast, and why the wrong index makes writes slower for no reason. Today you learned the two shapes a storage engine can take. Tomorrow you put one of them to work.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. With random keys, inserts are spread uniformly across the 50,000 leaf pages, and only 5,000 are cached, so about 90 percent of inserts land on a page that has to be fetched from disk. With an auto-increment key, every new row has the largest key so far, so it always belongs on the rightmost leaf. That one page stays hot in the cache and is rewritten again and again, with a split only when it fills. Same data, wildly different cache behaviour, purely because of key order. This is the lab's Part 1 in miniature.

D2. 2 GB divided by 64 MB is 32 sorted runs on disk. A read for a key not in the memtable might, in the naive case, have to check all 32 runs, newest to oldest, before it finds the key or concludes it is absent. That is the read amplification compaction and bloom filters are there to control.

D3. To change one 100-byte row, the B-tree must write the whole 8 KB page that row lives on, so at least 8,192 bytes hit the disk to change 100 bytes of data, roughly 80x write amplification on that page (and more once you count the write-ahead log). The LSM's amplification is not zero either, but it is a different shape: the write itself is a cheap ~100-byte append, and the extra bytes are paid later, in bulk, when compaction rewrites that row a few times as it merges down the levels. The key difference is that the LSM's extra writes are sequential and deferred, while the B-tree's are random and immediate.

D4. Banking ledger, heavy point reads and in-place updates: B-tree, you want fast lookups and clean read-modify-write on single rows. Append-only event log at 500,000 writes per second: LSM, this is exactly what an append-and-merge engine is built for. Time-series metrics store: LSM, ingestion is write-dominated and mostly append. Normal users table with balanced reads and writes: B-tree, the relational default, good reads and perfectly fine writes at that scale. The rule of thumb: if writes dominate and arrive fast, lean LSM, otherwise a B-tree is the comfortable default.

D5. With a 1 percent false-positive rate, each run's bloom filter correctly says "not here" 99 percent of the time for an absent key, and only falsely sends you to disk 1 percent of the time. Across 8 runs that is about 8 times 0.01, roughly 0.08 runs actually read from disk, so on average the lookup touches almost no runs at all. That solves the read-amplification problem, a missing-key read goes from "check all 8 runs" to "check almost none". The cost is the memory for the filters and a small, tunable false-positive chance.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-09-btree-lsm/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-09-btree-lsm/solution.py).

TODO 1, the B-tree insert whose cost you are measuring:

```python
insert_sql = "INSERT INTO t (k, v) VALUES (?, ?)"
```

TODO 2, the slowdown factor, the headline of Part 1:

```python
slowdown = rand_ms / seq_ms
```

TODO 3, the flush, which is the entire LSM idea in one line, append unsorted, then sort a small batch before writing it:

```python
run = sorted(memtable)
```

TODO 4, the read tax, every run plus the one memtable:

```python
read_places = len(loaded) + 1
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 300,000 rows.

```
==============================================================================
Part 1: the B-tree. Insert 300,000 rows, sequential vs random keys.
==============================================================================
  sequential keys (1, 2, 3, ...):     152.7 ms
  random keys (shuffled):            1694.0 ms
  random inserts are 11.1x slower, for the SAME rows
  Sequential keys keep extending the rightmost leaf of the tree, so
  the same few pages stay hot. Random keys land all over the tree,
  splitting pages and dirtying scattered pages that get written out
  on every commit. This is the B-tree's weakness.

==============================================================================
Part 2: the LSM. The write path is append-only, so order is free.
==============================================================================
  write path (append to memtable + WAL):
    sequential keys:      66.7 ms
    random keys:          72.7 ms
    ratio random / sequential = 1.09x  (1.0 = order does not matter)
  background flush (sort each run before writing it):
    sequential keys:      46.8 ms
    random keys:         138.8 ms
  sorted runs written to disk: 4  (70,000 rows each)
  Appending does not look at the key, so the write path is flat. The
  only order cost is sorting a run at flush time, and even that writes
  the run out sequentially, never the scattered page writes Part 1 paid.

==============================================================================
Part 3: the LSM read tax. One read touches many sorted places.
==============================================================================
  the store right now: 1 memtable + 4 sorted runs
  a present key is found after touching 3.33 places on average
  an absent key must touch all 5 places before giving up
  a B-tree answers the same read by walking ONE root-to-leaf path
  That is read amplification. Real LSMs cut it with a bloom filter per
  run (skip runs that cannot hold the key) and by compacting many runs
  into fewer. It is the price paid for the cheap, order-free writes.

==============================================================================
Scoreboard
==============================================================================
  P1 B-tree random slowdown    you =   10.0   actual =     11.1 x       close enough
  P2 LSM write ratio r/s       you =    1.0   actual =      1.1 x       close enough
  P3 LSM sorted runs           you =    4.0   actual =      4.0        close enough
  P4 LSM read places (miss)    you =    5.0   actual =      5.0        close enough

==============================================================================
The number to carry
==============================================================================
  Same 300,000 rows, same keys, only the order changed. The B-tree
  took 11.1x longer on random keys than sequential. The LSM write
  path did not care: random vs sequential came out 1.09x, basically
  flat. That gap is the whole reason write-heavy systems (logs, events,
  time series, messaging) reach for an LSM engine and not a B-tree.
  The LSM pays it back on reads: 5 places to check instead of 1.
```

Part 1 is the day. The two inserts hold identical rows, identical keys, identical payload. The sequential run finished in about 150 ms, the random run took about 1.7 seconds, 11 times longer. Nothing about the data changed, only the order it arrived in, and that alone is the difference between keeping one hot page on your desk and thrashing scattered cold pages out of an 8 MB cache on every commit. This is why a random UUID primary key on a large, busy table is a quiet performance bug.

Part 2 is the contrast. The LSM's append write path came out 67 ms sequential and 73 ms random, a ratio of 1.09, flat for all practical purposes. Appending to a memtable does not inspect the key, so key order simply cannot affect it. The one place order shows up is the background flush, where sorting the random batch took longer than sorting the already-ordered one, 139 ms versus 47 ms. That is real, but it is off the write path and it still writes each run to disk in one sequential pass.

Part 3 is the bill the LSM pays. With four runs on disk plus the memtable, a present key was found after touching about 3.3 places on average, and an absent key had to touch all 5 before giving up, where a B-tree answers either in a single root-to-leaf walk. That is read amplification, and it is exactly why production LSMs put a bloom filter in front of every run and keep compacting runs together. You measured the raw cost here so the fixes make sense tomorrow.

The one line to carry out of today: writes love an append-only LSM because order does not matter, reads love a sorted-in-place B-tree because there is only one place to look, and almost every real storage engine is one of these two bets.

</details>
