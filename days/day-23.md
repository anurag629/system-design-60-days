---
title: "Day 23: the log as a primitive"
parent: "Week 4: async, queues and the log"
nav_order: 2
has_children: true
---

# Day 23
## The log, the simplest idea that half of distributed systems are quietly built on 🪵

Today's one idea: a log is just a sequence you only ever add to, with each record numbered 0, 1, 2, and so on. The one clever move is that the number, the offset, is remembered by the reader, not by the log. That tiny decision is what lets a crashed consumer resume with nothing lost, and lets you add a brand new consumer next month that re-reads all of history. It is also most of what Kafka actually is.

Yesterday you saw a queue decouple a fast producer from a slow consumer. A queue is a pipe: a message goes in, a message comes out, and once it is out it is gone. Today you meet the thing that looks almost the same from the outside but behaves completely differently, because it keeps everything.

---

## Before you start ⏪

You need Day 22 fresh: a producer drops work into something in the middle and walks away, and a consumer picks it up later. Today that something in the middle stops being a disposable pipe and becomes a durable, replayable record of everything that happened. And pull on a thread from week 2: the write-ahead log you met on Day 8 and Day 9 is this exact structure. A database appends every change to a log first, then updates its pages. You already trusted a log with your data. Today you see it as a building block in its own right.

---

## Words you will meet today 📖

A log, in this sense, is an append-only, ordered sequence of records. You only add to the end. You never edit or delete in the middle. It is the write-ahead log from week 2, promoted to a first-class thing you build on.

An offset is the position of a record in the log, a plain integer. The first record is at offset 0, the next at 1, and the numbers never get reused or reordered. An offset is a permanent address: offset 42 means the same record forever.

A record, or message, or event, is one entry in the log. It is immutable once written. If something changes, you append a new record saying so, you do not go back and edit the old one.

A producer appends records to the end of the log. A consumer reads them forward from some offset.

A committed offset is the position a consumer has saved somewhere durable, meaning "everything up to here is done, resume from here if I restart". This is the one piece of state that makes a consumer crash-safe.

Replay is starting a consumer at an old offset (often 0) so it re-reads records it, or someone, already processed. A log allows this because it kept the records. A queue cannot, because it threw them away.

Retention is how long the log keeps a record before deleting it, set by time or by total size. It is the dial between "replay anything, forever" and "do not drown in disk".

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Using logs to build a solid data infrastructure](https://martin.kleppmann.com/2015/05/27/logs-for-data-infrastructure.html) by Martin Kleppmann. The clearest essay on why the humble append-only log is the backbone, not a detail. If you read one thing today, read this. It also quietly sets up Day 26's dual-write problem.
- [It's okay to store data in Apache Kafka](https://www.confluent.io/blog/okay-store-data-apache-kafka/) from Confluent. Directly about the thing that surprises people: the log keeps records after they are read, on purpose, and that retention is exactly what makes replay possible.
- [Kafka topics and the commit log](https://developer.confluent.io/courses/apache-kafka/topics/) from Confluent's own course. Short and visual, and it shows the offset model you are about to build, in the real system you will meet properly on Day 24.

Watch, after the lab:
- [What is Apache Kafka?](https://www.youtube.com/watch?v=FKgi3n-FyNU) by Confluent, about 10 minutes. The log, offsets, producers and consumers, drawn simply. This is Day 23's idea wearing its production clothes.
- Optional, to tie it back to week 2: [Write-Ahead Logs, the secret to fast database queries](https://www.youtube.com/watch?v=s3hKYMOpp3E) by Ben Dicken, about 11 minutes. The same append-only log, living inside a database.

### A log is almost nothing, and that is the point (14 min)

Picture a bank passbook, the old paper kind. Every transaction gets written on the next free line. You do not erase line 12 when money moves again, you write a new line. The passbook is in strict time order, it only grows, and any line you point at today says the same thing it said last year. That is a log. It is honestly one of the simplest data structures there is: a list you only append to, where each entry has a number that never changes.

Here is the thing that takes a while to believe. That simplicity is not a limitation you tolerate, it is the whole source of the power. Because you never edit in place, an old reader and a new reader see the same history. Because records are numbered in order, a reader can say "I am at line 4,200,000" and that one number is its entire bookmark. Because nothing is ever removed on read, you can come back tomorrow and read it all again. A queue gives up every one of these to be a simple pipe. The log keeps them, and gets a superpower in exchange.

In the lab you build exactly this: `append(record)` adds to the end and hands back the offset it landed at, and that is the entire write side. You will append 100,000 records and read the offsets straight back, 0 to 99,999, in order. No edits, no reordering, no surprises.

### The offset belongs to the reader, not the log (12 min)

This is the sentence to tattoo on the inside of your eyelids. In a queue, the broker tracks what has been delivered; the message is the broker's problem until it is acknowledged, then it is gone. In a log, the log does not track who has read what at all. Each consumer remembers its own offset. The log just sits there being a numbered list, and ten different consumers can be at ten different positions in it at once, none of them aware of the others.

Why does this matter so much? Two reasons. First, it makes a crash cheap to recover from. A consumer processes record 4,500,000, saves "I am now at 4,500,001" to somewhere durable, and if it dies, the replacement reads that saved number and carries on. Nothing coordinates this, there is no broker handing out messages and waiting for acks. The consumer owns its own place. Second, it makes consumers independent and cheap to add. Because the offset is the reader's, a new reader just picks a starting offset and goes, without disturbing anyone else.

In the lab, the offset store is a tiny SQLite table, consumer name to next offset. That is the durable bookmark. You will crash a consumer halfway, throw the whole object away, and watch a fresh one read that bookmark back and resume as if nothing happened.

### At-least-once is one line, and it is a choice (12 min)

Now the subtle part, and it is subtle in a way that bites people in production. Your consumer does two things per record: it processes the record (the real work, like writing a row somewhere), and it commits its offset (saves the bookmark). The order of those two is a decision, and the decision is the whole of delivery semantics.

Commit the offset after you process. Then if you crash in the gap, after the work but before the bookmark is saved, the restart resumes from the old bookmark and does that one record again. You get a duplicate. Nothing is ever lost. This is at-least-once.

Commit the offset before you process. Then if you crash in the gap, the bookmark already moved past a record you had not finished, so the restart skips it. You get a gap. Nothing is ever done twice. This is at-most-once.

That is the entire fork. There is no third option where a crash costs you neither a duplicate nor a gap, not without extra machinery, and the "exactly-once" you will hear advertised is that extra machinery (which is Day 25). For now, feel the honest tradeoff: pick the failure you can live with. For a card charge you refuse to lose the record, so you commit after and accept that a retry might charge twice, then you make the charge idempotent so the duplicate is harmless. UPI does this every day: your payment "fails", you tap again, and you are not charged twice, because the retry is deduplicated. For a view counter, a lost tick or a double tick barely matters, so you pick whichever is simplest. In the lab you will commit after, crash in the gap, and measure the result: exactly one record processed twice, zero lost.

### Replay is the thing a queue simply cannot do (10 min)

Here is the move that makes the log feel like magic the first time. You have a consumer happily reading along, sitting near the end of the log. You add a second, brand new consumer and start it at offset 0. It re-reads the entire history, every record, on its own cursor, while the first consumer sits exactly where it was, untouched. Two readers, one log, two different positions.

Try to do that with a queue and you cannot, because the records a queue delivered are gone. A reader you add tomorrow sees only what arrives from tomorrow on. The past is unrecoverable. With a log, the past is right there, because retention kept it, so a new consumer just rewinds and reprocesses.

This is not a toy trick. It is how you backfill a brand new analytics table from the last 30 days of events, how you replay a day of orders through a bug you just fixed, and how you spin up a second version of a service and let it rebuild its own state from scratch while the old one keeps serving. All of it, without asking a single producer to resend anything, because the log never threw it away. In the lab, the new consumer replays all 100,000 records from offset 0 while the first stays pinned at the end, and the two never interfere.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-23-drills.md`](../notes/day-23-drills.md). About 8 minutes each.

D1. A log holds 5,000,000 records at offsets 0 to 4,999,999, and you append one more. What offset does it get? Now you want to "delete" the record at offset 3,000,000. What does an append-only log do instead of editing in place, and does any earlier offset change?

D2. A consumer has committed offset 4,200,000 while the log head is at 5,000,000. What is its lag? It commits after processing each record and crashes right after processing offset 4,500,000 but before committing it. What offset does it resume from, and how many records does it re-read?

D3. You can commit the offset before processing a record, or after. For each order, what does a crash in the gap cost, a duplicate or a loss? Which order is at-least-once and which is at-most-once? Pick the right order for charging a card, and for bumping a view counter, and say why.

D4. Your events go to a log with 30 days of retention, and a brand new analytics job joins today wanting to rebuild from the last 30 days. What offset does it start at, and what happens to the existing consumer's position while it runs? Why could you not do this if the events had gone through a traditional queue?

D5. A queue drops a message once it is acknowledged; a log keeps records until a retention limit of time or size. Name one thing that keeping data after it is read buys you, and one real cost of keeping it. When would you set a deliberately short retention?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-23-log/append_log.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-23-log/append_log.py).

It is in three parts. Part 1 builds the log and appends 100,000 records, showing the offsets come back 0 to 99,999. Part 2 runs a consumer that commits its offset to a durable SQLite store, crashes it mid-stream, and restarts it to show it resumes with nothing lost and exactly one duplicate. Part 3 adds a brand new consumer at offset 0 and watches it replay all of history while the first consumer sits at the end.

Standard library only, single threaded so the numbers are exact, and it cleans up the one SQLite file it makes.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. You append N records to an empty log. Offsets start at 0. What is the offset of the last record?
- P2. The consumer commits its offset after processing each record, then crashes in the gap between processing a record and committing it, then restarts. How many records get processed twice?
- P3. After that same crash and restart, how many of the N records were missed entirely?
- P4. A brand new second consumer starts at offset 0 while the first sits at the end. How many records does it re-read?

P2 and P3 are the pair to feel before you run them. Write both down. The point of the lab is that one of them is not zero and the other is, and which is which is the whole lesson.

### Fill in the TODOs

1. TODO 1 is the append: a new record's offset is simply how many records are already in the log. This one line is the entire write side of a log.
2. TODO 2 is the resume: on restart, read this consumer's committed offset from the durable store. This is the bookmark that makes a crash safe.
3. TODO 3 is the commit: store the next offset to read, and do it after the work. The ordering is what makes the whole thing at-least-once.
4. TODO 4 is the replay start: a brand new consumer that wants all of history begins at offset 0.

```bash
cd labs/day-23-log
python3 append_log.py
```

### What you're going to discover

Part 1 is calm and a little anticlimactic, which is the point. Offsets are handed out 0, 1, 2, and once written they never move. A log is not clever. It is a numbered list you only add to, and all the power comes later, from that plainness.

Part 2 is the one to sit with. You crash the consumer at offset 59,999, after it processed that record but before it committed the offset. On restart it resumes from its committed offset, re-reads that one in-flight record, and finishes. The tally: 100,001 records processed for 100,000 records, so exactly one ran twice and zero were lost. That is at-least-once, and it came straight out of committing after the work. Commit before instead and you would have seen the mirror image, a gap and no duplicate.

Part 3 is the payoff. A new consumer starts at 0 and replays every record while the first sits pinned at 100,000, and the two never touch each other's position. Two consumers, one log, two offsets. That independence is the thing you cannot buy from a queue at any price.

### Traps ⚠️

- Off-by-one on the committed offset is the classic. Commit the next offset to read (the processed offset plus one), not the offset you just processed, or every restart quietly re-reads one extra record, crash or no crash.
- Do not confuse the two numbers in Part 2. Zero missed is the safety property (the log lost nothing). One duplicate is the cost (at-least-once). They are different things, and swapping which one you expected means you have the semantics backwards.
- The "crash" in the lab is a thrown-away object, not a power cut, so the SQLite offset survives even with fsync off. That is deliberate, to keep it fast. Just know that real durability across a power loss is a stronger promise than this lab makes.
- In Part 3 the new consumer gets its own name, so it has its own row in the offset store. Give two consumers the same name and they fight over one bookmark, which is not replay, it is a mess.

### Deliverable

[`labs/day-23-log/RESULTS.md`](../labs/day-23-log/RESULTS.md) has a skeleton. Paste the output, and write two lines: after the crash, how many records were lost and how many ran twice, and why; and why a brand new consumer could replay all of history off this log when a queue would have had nothing to give it.

---

## Block 4: write (30 min) 📣

Your angle today is the reframe: "a log looks just like a queue from the outside, but it keeps everything, and that one difference is why you can crash a consumer and lose nothing, and add a new consumer next month that re-reads all of history. A queue can do neither." The Part 3 scoreboard, two consumers at different offsets on one log, is the screenshot.

Example posts are on the [Day 23 posts](../shares/day-23-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the duplicate-versus-missed result you measured in Part 2, and one thing you still cannot explain.

Day 24 is Kafka for real: partitions so the log can scale past one machine, consumer groups so a team of consumers can split the work, and the ordering guarantee that only holds inside one partition. Everything you built today, the append, the offset, the replay, is a single-machine version of exactly what Kafka does. Tomorrow you see what it costs to spread that log across many.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The new record gets offset 5,000,000, the next integer after the current last, which is just the current length of the log. To "delete" offset 3,000,000, an append-only log does not touch it. It appends a new record at the end (a tombstone, or a newer version of that key) which also gets the next free offset. Offset 3,000,000 and every earlier offset are unchanged, because the log only ever grows at the tail. A consumer replaying from 0 sees the original record and later sees the tombstone, and resolves the two to "deleted". This is why deletes in log-based systems are themselves just more appends.

D2. Lag is head minus committed, 5,000,000 minus 4,200,000, so 800,000 records behind. On the crash: it committed after processing each record, so after finishing offset 4,499,999 it had committed 4,500,000 (the next offset to read). It then processed 4,500,000 and died before committing, so the stored offset is still 4,500,000. It resumes from 4,500,000 and re-reads exactly 1 record, the one it had processed but not committed. Same shape as the lab, one duplicate on a crash, nothing lost.

D3. Commit before processing: a crash in the gap means the bookmark already moved past a record you had not finished, so the restart skips it. That is a loss, and it is at-most-once. Commit after processing: a crash in the gap means you re-do the record you had finished but not bookmarked. That is a duplicate, and it is at-least-once. For charging a card you must never silently lose a charge, so you commit after (at-least-once) and make the charge idempotent with a key, so the retry does not double-charge. For a view counter, a lost or doubled tick is harmless, so you pick whichever is simplest, usually at-least-once because it is the natural order, and you stop worrying about the rare double count.

D4. The new analytics job starts at the earliest offset the log still holds (the start of the 30 day window) and reads forward to the head, rebuilding as it goes. The existing consumer's position is completely unaffected, because offsets are per-consumer: the new job has its own bookmark and the old job keeps reading from its own, and neither notices the other. You could not do this with a traditional queue because a queue removes each message once it is acknowledged, so 30 days of past events are simply not there for a new reader to consume. The log kept them; the queue did not.

D5. Keeping data after it is read buys you replay: you can add a new consumer and reprocess history, replay through a fixed bug, rebuild a derived store, and inspect what actually happened for debugging and audit. The costs are real: storage grows with retention, and holding data longer is a privacy and compliance burden, because an immutable log is awkward under a right-to-erasure request (you lean on compaction or crypto-shredding). You set a deliberately short retention when the data is sensitive personal data, when it is only useful briefly (ephemeral metrics), or when storage cost dominates and nobody will ever replay it.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-23-log/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-23-log/solution.py).

TODO 1, the append. A new record's offset is how many records are already there, which is the entire write side of a log:

```python
offset = len(self._records)
```

TODO 2, the resume. On restart, read this consumer's committed offset back from the durable store:

```python
committed = self.store.committed(self.name)
```

TODO 3, the commit. Store the next offset to read, and the loop calls this only after the work is done, which is what makes it at-least-once:

```python
self.store.commit(self.name, offset + 1)
```

TODO 4, the replay start. A brand new consumer that wants all of history begins at the first record:

```python
start = 0
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 100,000 records.

```
==============================================================================
Part 1: append. The log only grows, and every record gets an offset.
==============================================================================
  records appended:                 100,000
  first three offsets handed back:  [0, 1, 2]
  last three offsets handed back:   [99997, 99998, 99999]
  the last record's offset:         99,999
  (appending 100,000 records took 19 ms, about 5,294,682/sec)
  Offsets start at 0 and climb by one. A record's offset is just its
  position in arrival order, and once written it never moves. Reading
  offset 0 tomorrow gives the same record it gave today.

==============================================================================
Part 2: a consumer that remembers its offset, crashes, and resumes.
==============================================================================
  crashed after processing offset:  59,999
  records processed before crash:   60,000
  committed offset the store kept:  59,999
  restarted consumer resumed from:  59,999
  records processed after restart:  40,001
  ----
  total records processed:          100,001  (= N + 1)
  records MISSED (processed 0x):    0
  records DUPLICATED (processed 2x):  1   at offset [59999]
  The crash landed in the gap between processing a record and
  committing its offset. On restart the consumer resumed from the last
  COMMITTED offset, so it re-did that one in-flight record. Nothing was
  lost, and exactly one record ran twice. Committing after the work
  (not before) buys at-least-once: a crash costs a duplicate, never a
  gap. Flip the order and you would get at-most-once instead. Day 25.

==============================================================================
Part 3: replay. Add a new consumer later, re-read the whole log.
==============================================================================
  log length (records still kept):  100,000
  consumer A (orders-writer) offset:  100,000
  consumer B (analytics-v2) starts:  0
  ----
  two consumers, one log, different positions: A at 100,000, B at 0
  records consumer B replayed:      100,000
  B read every offset 0..99,999 in order: True
  consumer A's offset after B ran:  100,000  (unchanged, independent)
  consumer B's offset now:          100,000
  The log kept every record, so a reader added long after the fact
  rebuilt all of history on its own cursor, while the first consumer
  sat untouched at the end. A queue cannot do this: once a message is
  taken it is gone, so a new reader sees nothing of the past. The log
  is a shared tape every consumer rewinds for itself.

==============================================================================
Scoreboard
==============================================================================
  P1 last offset after append        you =    99,999   actual =    99,999        spot on
  P2 duplicates after crash          you =         1   actual =         1        spot on
  P3 records missed after crash      you =         0   actual =         0        spot on
  P4 records replayed from 0         you =   100,000   actual =   100,000        spot on

==============================================================================
The number to carry
==============================================================================
  One append-only log of 100,000 records. The first consumer crashed
  mid-stream, resumed from its committed offset, and re-ran exactly
  1 record (0 lost): that is at-least-once, bought by committing
  the offset AFTER the work. Then a brand new consumer started at
  offset 0 and replayed all 100,000 records on its own cursor, while
  the first consumer sat untouched at the end. Two readers, one log,
  two positions. The offset lives with the reader, not the log, and
  that one design choice is what Kafka is built on. Day 24 next.
```

Part 1 is the quiet one. The offsets come back 0, 1, 2, up to 99,999, in order, and that is all a log's write side ever does. No edits, no reordering. The plainness is the feature, because it is what keeps old and new readers seeing the same history.

Part 2 is the heart of the day. The consumer processed 60,000 records (offsets 0 to 59,999), crashed right after offset 59,999 but before committing it, and the store kept 59,999 as the resume point. The restart picked up from 59,999, re-ran that one record, and finished. The books: 100,001 processed for 100,000 records, so zero lost and exactly one duplicate. That duplicate is not a bug, it is the definition of at-least-once, and it exists because the commit comes after the work. Had the commit come first, you would have measured one missing record and no duplicate, which is at-most-once. The log gives you a clean choice between the two, and no free lunch past them.

Part 3 is the superpower in one screen. A new consumer with its own name started at offset 0 and replayed all 100,000 records, while the first consumer stayed pinned at 100,000, its position untouched. Two readers at two offsets on one log, fully independent, because each one owns its bookmark. That is the exact shape of adding a new analytics job that backfills from history while production keeps running, and it is the one thing a queue can never give you, because a queue does not keep what it delivered.

The one line to carry out of today: the offset lives with the reader, not the log, so a crash costs at most a replayed record and a new reader can rewind the whole tape. That single decision is most of what Kafka is, and tomorrow you see what it takes to spread that log across many machines.

</details>
