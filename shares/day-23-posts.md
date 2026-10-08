---
title: "Day 23 posts"
parent: "Day 23: the log as a primitive"
grand_parent: "Week 4: async, queues and the log"
nav_order: 3
---

# Day 23 posts: LinkedIn and X

The good screenshot today is Part 3: two consumers on one log at different offsets, and a brand new consumer replaying all 100,000 records from offset 0 while the first sits at the end. Swap in your own numbers and voice.

## LinkedIn

Day 23 of 60 days of system design. Today was the append-only log, the idea underneath Kafka and underneath every write-ahead log you have ever relied on. I built a tiny one to feel why it is such a big deal.

The log is almost embarrassingly simple. You only add to the end. Every record gets the next integer, its offset: 0, 1, 2, and so on. Nothing is ever edited in place. In the lab I appended 100,000 records and read the offsets straight back, 0 to 99,999, in order.

The first interesting bit is that the position is not stored on the log. It is stored by the reader. A consumer reads forward from its own offset, processes each record, and commits that offset somewhere durable. I crashed the consumer halfway, at offset 59,999, and threw the whole object away. On restart it read its last committed offset and carried on. Nothing was lost.

One detail decides everything here: it commits the offset AFTER doing the work, not before. So the crash landed in the gap between "processed" and "committed", and on restart it re-ran exactly that one record.

    total records processed: 100,001  (one ran twice)
    records missed:          0
    records duplicated:      1

That is at-least-once delivery, and it is a choice. Commit before the work instead and a crash would skip a record, which is at-most-once. You pick which failure you can live with: a duplicate you have to dedupe, or a gap you may never notice.

Then the part that made it click. I added a brand new, second consumer and started it at offset 0. It re-read the entire history, all 100,000 records, on its own cursor, while the first consumer sat untouched at offset 100,000. Two readers, one log, two positions.

A queue cannot do that. Once a message is taken off a queue it is gone, so a reader you add tomorrow sees nothing of the past. The log keeps everything, so you can bolt on a new consumer next month and let it reprocess all of history. That is how you backfill a new analytics table, or replay a day of events through a fixed bug, without asking anyone to resend anything.

Reads love this because the offset lives with the reader. That one design choice is most of what Kafka is.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #kafka #learninginpublic

## X thread

**1/**

Day 23 of 60 days of system design. The append-only log, the idea under Kafka and under every write-ahead log.

Built a tiny one. You only add to the end. Each record gets the next offset: 0, 1, 2, ...

Appended 100,000 records. Offsets came back 0 to 99,999, in order. Nothing edited in place.

**2/**

The trick: the position is not on the log. It is on the READER.

A consumer reads from its own offset, processes a record, commits that offset somewhere durable. Restart, and it resumes from the committed offset.

I crashed one at offset 59,999 and threw the object away. It came back and carried on. Nothing lost.

**3/**

One detail decides everything: it commits the offset AFTER the work, not before.

So the crash fell between "processed" and "committed", and on restart it re-ran that one record.

    processed: 100,001 (one twice)
    missed:    0
    duplicated: 1

That is at-least-once.

**4/**

Flip the order (commit before processing) and a crash SKIPS a record instead. That is at-most-once.

You are choosing your failure: a duplicate to dedupe, or a gap you might never see. For a card charge vs a view counter, you would choose differently.

**5/**

Then the superpower. I added a second consumer and started it at offset 0.

It replayed all 100,000 records on its own cursor, while the first consumer sat untouched at 100,000.

Two readers, one log, two positions.

**6/**

A queue cannot do this. Take a message off a queue and it is gone; a reader you add tomorrow sees none of the past.

The log kept everything, so a new consumer can reprocess all of history. Backfills, replays through a fixed bug, no resends.

That is most of what Kafka is.

Code: github.com/anurag629/system-design-60-days
