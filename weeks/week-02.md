# Week 2: storage, or where does the data actually sit? 💾

Days 8 to 14, Tue 2026-09-29 to Mon 2026-10-05.

Last week you learned how fast a computer is. This week you learn where your data lives and what it costs to put it there and get it back. Every "should we use Postgres or Mongo or Cassandra" argument you have ever heard is really an argument about the stuff in this week. Most people have that argument without knowing any of it. You will not.

Here is the honest truth. A database is not magic. It is a very clever program that writes your rows onto a disk in a particular shape, keeps a few extra copies of some columns so it can find things fast, and does a lot of careful bookkeeping so that a power cut does not corrupt everything. That is basically it. Once you can picture the shape of the bytes on disk, half of system design stops being scary.

We live inside Kleppmann's *Designing Data-Intensive Applications*, chapters 2, 3, 5 and 6, this whole week. Buy it if you have not. It is the one book worth the money.

## What you will be able to do by the end of the week

Someone says "our reads got slow after we hit 50 million rows." You can list five possible causes in order of likelihood, and you can say which EXPLAIN output would confirm each one. You know why adding an index sped up your read but slowed down your writes. You can explain to a non-technical PM why "just make it consistent AND always available" is not a thing you can promise.

## The days 🗓️

Day 8: how a row actually sits on disk. Pages, heap files, and why a database reads 8 kilobytes even when you asked for 8 bytes. Row stores vs column stores, and when each one wins. Lab: crack open a real SQLite file and read the page header with your own code.

Day 9: the two great families, B-tree vs LSM-tree. Postgres and MySQL are B-trees. Cassandra, RocksDB and friends are LSM-trees. One is built for reads, one for writes, and knowing which is which is a genuine interview filter. Lab: measure write amplification on both.

Day 10: indexes, properly this time. Composite indexes, covering indexes, and the very annoying day you learn your database decided to ignore the index you lovingly created. Lab: EXPLAIN ANALYZE experiments until the query planner stops surprising you.

Day 11: transactions and isolation levels. Dirty reads, non-repeatable reads, phantom reads, and MVCC, which is how Postgres lets a hundred people read and write at once without holding hands. Lab: open two connections and reproduce each anomaly with your bare hands.

Day 12: replication. One leader, many followers, and the small lie in the middle called replication lag. This is why you sometimes post a comment, refresh, and it is gone for two seconds. Lab: simulate lag and watch a stale read happen.

Day 13: partitioning, also called sharding. Splitting one big table across many machines, hash vs range, and the classic disaster of the hot shard. Think one Kohli century sending all the traffic to one server. Lab: shard a dataset, create a hot shard on purpose, then fix it.

Day 14: first real storage design. You design the database layer for something like Twitter or a URL shortener, on paper, timed. Then we compare it against what you would have drawn on day 8 and you see how much moved.

## Core resources for the week 📚

Read:
- Kleppmann, *DDIA*, chapters 2, 3, 5, 6. This is the spine of the week.
- [Use The Index, Luke!](https://use-the-index-luke.com/), the free index book, for days 8 to 10.
- [Postgres docs: EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html), dry but the source of truth.

Watch:
- [CMU 15-445 Intro to Database Systems](https://www.youtube.com/@CMUDatabaseGroup), Andy Pavlo. The first six lectures are exactly this week. He is funny and he does not cut corners.

## What trips people up this week ⚠️

They memorise "SQL is for structured data, NoSQL is for scale" and stop thinking. That sentence is almost meaningless. The real question is always about your access pattern: how you read, how you write, what you need to be consistent, and how big it gets. A well-sharded Postgres runs half the internet. A badly-modelled Mongo falls over at 100 GB. The database name on the box tells you very little. The data model and the access pattern tell you everything.
