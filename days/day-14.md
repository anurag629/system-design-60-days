---
title: "Day 14: designing a storage layer"
parent: "Week 2: storage"
nav_order: 7
has_children: true
---

# Day 14
## Designing the storage layer for a billion messages, and how far week 2 took you 🗄️

Today's one idea: week 2 handed you a toolkit, row store versus column store, B-tree versus LSM, indexes, transactions, replication, sharding. Today you pick, for one real write-heavy system, and you justify every choice with a number instead of a vibe. That is the whole jump from "I know what an LSM is" to "I know when to reach for one."

This is the week 2 finale, a design day like Day 7. No coding lab. You design the data layer for a messaging app, on paper, against the clock, then hold it up against what you would have drawn before this week.

---

## Before you start ⏪

Bring all of week 2. Day 8 (pages, row vs column), Day 9 (B-tree vs LSM), Day 10 (indexes), Day 11 (transactions), Day 12 (replication and lag), Day 13 (sharding and the hot shard). Today pulls on every one of them at once, which is exactly the point. If one is fuzzy, today will show you which.

---

## Words you will meet today 📖

The access pattern is how the data is actually read and written: what you look up, by what key, how often, and whether writes are appends or updates. Every storage choice flows from this, so it is the first thing you pin down.

A write-heavy system takes far more writes than reads, or writes that must be very cheap. Messaging is the classic case: a message is written once, appended, almost never updated.

A shard key, or partition key, is the field you split the data by across machines. Choosing it well is most of the design, because it decides both how evenly load spreads and how cheap your common query is.

A hot partition is one shard that gets a wildly disproportionate share of traffic, usually from one popular key, a celebrity or a giant group. It melts one machine while the rest sit idle, and it is the recurring villain of week 2.

A read replica is a follower copy that serves reads so the leader can focus on writes. It scales reads, at the cost of replication lag (Day 12).

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [How Discord stores trillions of messages](https://discord.com/blog/how-discord-stores-trillions-of-messages). The real thing: a messaging store at enormous scale, on an LSM engine, sharded by channel and time bucket to beat the hot partition. Today's design, built by a real company, with the war stories.
- [WhatsApp design breakdown](https://www.hellointerview.com/learn/system-design/problem-breakdowns/whatsapp) from Hello Interview. The same problem worked by interviewers, with the data-layer decisions called out.
- [DDIA chapter 3](https://dataintensive.net/), one more pass. You have the vocabulary now, so the engine-choice section reads completely differently than it did on Day 8.

Watch, after you have done your own design:
- [Design a chat application like WhatsApp](https://www.youtube.com/watch?v=a8KUKOh3YXk) by Concept and Coding, about 50 minutes. A full worked design. Long, so do yours first, then watch and compare.

### The method: let the access pattern choose the storage (15 min)

Every storage design starts with one question, and it is not "SQL or NoSQL." It is: what is the access pattern? Pin down what gets written, how often, whether writes are appends or in-place edits, what gets read, by what key, and how often. Write that down first. Everything else is a consequence of it.

Then the choices fall out, each one a week 2 idea:

Engine, from Day 9. Are writes an append-mostly firehose, or a mix of reads and in-place updates? Append-heavy at huge volume leans LSM. Balanced, update-in-place, point-read-heavy leans B-tree. Messaging is append-mostly and enormous, so it leans LSM, which is exactly what Cassandra, ScyllaDB and friends are.

Row versus column, from Day 8. Does the app fetch whole records (row store) or scan one field across millions of rows for a dashboard (column store)? Usually both exist: a row or LSM store for the app, a column store the data is copied into for analytics.

The index and the query, from Days 5 and 10. What is the one hot query, and what index or partition makes it a seek instead of a scan? For messaging it is "give me the last fifty messages in this chat," which wants the data partitioned by chat and ordered by time, read with keyset pagination, never offset.

The shard key, from Day 13. What do you split by so the hot query stays on one shard and load spreads evenly? And where is the hot partition going to come from? For messaging, shard by chat, and the hot partition is the giant group or broadcast channel, which you tame by also bucketing on time so one chat's history spreads across shards. That is the Discord story exactly.

Replication, from Day 12. How do you scale reads and survive a machine dying, and where does replication lag bite? Reading old chat history tolerates lag fine. Reading the message you just sent does not, so that one read wants read-your-writes.

Notice that every decision is a week 2 day, and every one is answered with the access pattern plus a number, not a preference.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Write your answers into [`notes/day-14-drills.md`](../notes/day-14-drills.md). About 8 minutes each.

D1. Estimate the scale. Assume 2 billion users sending 50 messages a day each. Messages per second, average and peak at 3x? At about 300 bytes a message, how much new data per day, and per year? What does that scale alone tell you about one database versus many?

D2. Pick the engine. Messages are written once, appended, essentially never updated, at the peak rate from D1. B-tree or LSM, and why? Tie your answer to the Day 9 measurement.

D3. The hot query is "load the last 50 messages of this chat." What do you partition by, what do you order by, and do you page through older messages with offset or keyset? Why (Day 5 and Day 10)?

D4. Choose a shard key and name the hot partition. If you shard by chat id, what happens to a broadcast channel with 50 million members, and how do you spread that one chat's load across shards (Day 13)?

D5. Replication. You run read replicas to scale reads (Day 12). Reading week-old history from a replica is fine even if it lags. Which single read is not fine to serve stale, and how do you handle just that one?

---

## Block 3: build (100 min) 🔧

Today you build a design, not code. The template is [`labs/day-14-storage-design/DESIGN.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-14-storage-design/DESIGN.md). Copy it into your fork and fill it in.

Do it against the clock. Give yourself 45 minutes for a first full pass: access pattern, scale estimate, engine choice, the data model and the hot query's index, the shard key and the hot partition, then replication and consistency. Do not open the Solutions or the Discord write-up until your 45 minutes are up. The value is in producing it yourself first.

Then spend the rest of the block improving it with the readings open, marking in a different colour what you added. That delta is week 2 landing.

### What a strong storage design has

A weak one names technologies ("use Cassandra"). A strong one starts from the access pattern and lets it choose the technology, estimates the scale before deciding one machine will not do, names the one hot query and the index that serves it, picks a shard key and says where the hot partition will come from and how it is tamed, and knows which single read cannot tolerate replication lag. Aim for that.

### Deliverable

Your filled-in `DESIGN.md`, and one honest paragraph: which week 2 day did you lean on hardest, and which choice were you least sure about?

---

## Block 4: write (30 min) 📣

Your angle is the synthesis: "I designed the storage layer for a messaging app using one week of tools. Here is why messages go in an LSM store, sharded by chat and time, and the one read I refuse to serve from a replica." The engine choice and the hot-partition fix make the strongest points.

Example posts are on the [Day 14 posts](../shares/day-14-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it, and look back 📝

Log the three: what you completed, your engine choice and the number behind it, and one thing you still cannot explain.

Then the week 2 retrospective. Think back to Day 8, when a database file was still a black box. Write down the three storage decisions you can now make with a number that you could not have made a week ago. That gap is week 2.

Week 3 is caching and the CDN: the fastest read is the one you never send to the database at all. You spent a week making the database fast. Next week you learn when to skip it entirely, and how a cache that fails badly takes the healthy database down with it.

---

## Solutions 🔑

Open these only after your own 45-minute design pass.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. 2 billion users times 50 messages is 100 billion messages a day. Over 100,000 seconds that is about 1 million messages per second average, roughly 3 million at a 3x peak. At 300 bytes each, that is 30 TB of new data per day, about 11 petabytes a year. The scale alone settles it: no single machine holds 11 PB a year or takes 3 million writes a second, so this is sharded across many machines from day one. Estimation decided the shape before any technology was named.

D2. LSM. Messages are the textbook append-only, write-heavy, never-updated workload, and at 3 million writes a second you cannot afford the B-tree's random-write tax you measured on Day 9. An LSM's append path does not care about key order and turns those writes into cheap sequential flushes. The read cost an LSM pays is acceptable here because the hot read is a small, well-targeted range (one chat's recent messages), not a random point lookup across everything.

D3. Partition by chat id, order by time (or a time-ordered message id) within the chat, and page with keyset, not offset. Keyset because "load 50 older messages before the ones I am showing" is exactly `WHERE chat_id = ? AND id < :oldest_seen ORDER BY id DESC LIMIT 50`, an index seek that stays fast no matter how deep the history goes, while offset would re-scan the whole chat every page (Day 5) and would also show duplicates as new messages arrive.

D4. Shard by chat id so one chat's messages live together and the hot query hits one shard. The hot partition is the giant broadcast channel: 50 million members all reading and writing one chat id lands on one shard and melts it, exactly the Day 13 celebrity key. The fix is to not let one chat be one partition: bucket on time too, so the partition key is (chat id, time bucket), and a busy chat's history spreads across many shards instead of piling onto one. This is precisely how Discord stores trillions of messages.

D5. The one read that cannot be stale is the message you just sent: send it, your screen refreshes, and it must be there, or the app looks broken. That is a read-your-writes requirement (Day 12). Serve that one read from the leader, or from a replica known to have caught up to your write, or simply let the sending client show its own message from local state. Every other read, scrolling old history, can come from a lagging replica without anyone noticing.

</details>

<details markdown="1">
<summary>A worked reference design</summary>

One good answer, not the only one. Yours will differ; what matters is that the access pattern and the numbers drive it.

Access pattern. Writes: a message appended to a chat, write-once, never updated, at a few million per second peak. Reads: load the most recent messages of a chat on open, then page backwards through older ones; far fewer reads than the fan-out suggests because clients cache what they have seen. This is append-heavy and range-read, almost never a random point update.

Scale, from D1: about 1 million writes per second average, 3 million peak, 30 TB a day, 11 PB a year. Sharded from the start.

Engine, from D2: an LSM store (Cassandra or ScyllaDB shape), because the workload is an append firehose and the Day 9 random-write tax rules a B-tree out at this write rate.

Data model and the hot query, from D3: messages keyed by (chat id, time bucket) as the partition and message id as the clustering order, so "last 50 in this chat" is a single-partition range read served by keyset pagination, and scrolling back is more keyset reads, never offset.

Shard key and hot partition, from D4: shard by chat id, bucketed by time so no single chat is a single unbounded partition. The broadcast channel is the hot partition, and the time bucket spreads its load; truly enormous fan-out channels get special handling (treat a broadcast as a feed, not a chat).

Replication and consistency, from D5: asynchronous replicas scale the history reads and survive a node dying. The only read pinned to a fresh copy is your own just-sent message, handled with read-your-writes (serve it from the leader or from local client state). Everything else tolerates lag.

Analytics, from Day 8: none of the above serves the "messages per country per day" dashboard well, because that scans one field across everything. Copy the data into a column store for analytics and keep it off the live messaging path.

The sentence that makes this design sound senior: "messages go in an LSM store sharded by chat and time, because the workload is an append firehose with a hot partition problem, and the only read I will not serve from a lagging replica is the one you just sent."

</details>

<details markdown="1">
<summary>Week 2 in one page</summary>

Seven days, one question underneath all of them: what is the access pattern, and what does the data cost to store and reach?

Day 8, pages. A database file is a stack of fixed-size pages, and it reads a whole page to get one row. Row stores keep a record together; column stores keep a field together. Opposite jobs.

Day 9, B-tree vs LSM. B-trees sort and update in place, great for reads, terrible at random writes. LSMs append and merge, great for writes, pricier on reads. Almost every engine is one of these two bets.

Day 10, indexes. The right index turns a scan into a seek. The wrong query, a non-leftmost composite filter or a function wrapped around a column, makes the engine ignore a perfectly good index.

Day 11, transactions. Read-modify-write without a transaction loses updates and corrupts money. Atomicity makes the read and the write one indivisible step.

Day 12, replication. Followers lag, so a read straight after a write can show the old value. You route around the staleness only where it matters.

Day 13, sharding. Split by a key chosen so the hot query stays on one shard and load spreads. Modulo sharding makes resharding move everything; consistent hashing moves a fraction. Neither saves you from the celebrity key.

Day 14, today. All six, chosen for one real system, each justified with a number.

If your design started from the access pattern, chose the engine from the write pattern, named the hot partition before it bit you, and knew which one read could not be stale, you did not learn six storage facts this week. You learned how to choose. Week 3 is about when to not touch the database at all.

</details>
