---
title: "Day 9 posts"
parent: "Day 9: B-trees and LSM trees"
grand_parent: "Week 2: storage"
nav_order: 3
---

# Day 9 posts: LinkedIn and X

The scoreboard makes a good screenshot: random B-tree inserts many times slower than sequential, while the append-only writes stay flat. Swap in your own numbers and voice.

## LinkedIn

Day 9 of 60 days of system design. Today I finally understood why there are two completely different kinds of storage engine, by measuring the gap on my own laptop.

I inserted 300,000 rows into SQLite twice. Same rows, same keys, same payload. The only thing I changed was the order the keys arrived in.

    sequential keys (1, 2, 3, ...):   153 ms
    random keys (shuffled):          1694 ms

Random was about 11 times slower. For identical data. That is the B-tree's weakness. A B-tree keeps everything sorted and updates it in place, so sequential keys just keep extending the same rightmost leaf, while random keys land all over the tree, splitting pages and scattering writes across the file.

Then I wrote a tiny LSM engine, the thing behind RocksDB, Cassandra and LevelDB. It does not update in place. It appends every write to an in-memory table and flushes sorted runs to disk later. I wrote the same 300,000 rows, sequential and random:

    append write path, sequential:   67 ms
    append write path, random:        73 ms

Basically flat. Appending does not look at the key, so it simply does not care what order the writes arrive in. That is the whole reason write-heavy systems choose an LSM.

Nothing is free, though. To read one key, the LSM had to check the in-memory table plus every sorted run, 5 places in my run, where a B-tree walks a single path from root to leaf. That read tax is why real LSMs add bloom filters and background compaction.

Reads love a B-tree. Writes love an LSM. Now I know why, because I measured it.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #databases #learninginpublic

## X thread

**1/**

I inserted the SAME 300,000 rows into SQLite twice today. Same keys, same data. Only the order changed.

sequential keys:  153 ms
random keys:     1694 ms

11x slower, for identical rows. Day 9 of 60 days of system design.

**2/**

That is the B-tree's weakness (SQLite, Postgres, MySQL).

A B-tree keeps data sorted and updates in place. Sequential keys keep extending the same rightmost leaf. Random keys land all over the tree, splitting pages and scattering writes across the file.

**3/**

Then I wrote a tiny LSM engine (the RocksDB / Cassandra / LevelDB family). It never updates in place. It appends to an in-memory table and flushes sorted runs to disk later.

Same 300,000 rows:

append, sequential:  67 ms
append, random:      73 ms

Flat.

**4/**

Why flat? Appending does not look at the key. It does not care what order writes arrive in. That order-independence is the entire reason write-heavy systems (logs, events, time series, messaging) reach for an LSM.

**5/**

The catch: reads.

To find one key, the LSM checked the memtable plus every sorted run. 5 places in my run. A B-tree answers the same read by walking ONE path, root to leaf.

Real LSMs fight this with bloom filters and compaction.

**6/**

So:

B-tree: fast reads, hates random writes.
LSM: cheap order-free writes, pays it back on reads.

Not better or worse. Opposite bets. And I got to watch the 11x gap appear on my own machine.

Code: github.com/anurag629/system-design-60-days
