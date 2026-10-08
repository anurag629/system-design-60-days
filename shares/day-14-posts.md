---
title: "Day 14 posts"
parent: "Day 14: designing a storage layer"
grand_parent: "Week 2: storage"
nav_order: 3
---

# Day 14 posts: LinkedIn and X

The angle is synthesis: one week of storage tools, applied to one real system. Swap in your own voice.

## LinkedIn

Day 14 of 60 days of system design, end of week 2. Today I designed the storage layer for a messaging app, and every single decision was a day from this week, answered with a number instead of a preference.

Scale first: 2 billion users, 50 messages each a day, is about 1 million messages a second, 3 million at peak, 11 petabytes a year. That one estimate ends the "can one database do this" question before you name any technology.

Engine: LSM, not a B-tree. Messages are written once and appended, never updated, at millions a second. On Day 9 I measured a B-tree take 11 times longer on random writes than sequential. You cannot pay that tax at this write rate. An LSM's append path does not care.

The hot query, "load the last 50 messages in this chat," wants the data partitioned by chat and ordered by time, read with keyset pagination, never offset (Day 5). Shard by chat id so that query hits one shard.

Then the trap: the 50-million-member broadcast channel. Shard by chat id alone and that one chat melts one machine, the celebrity key from Day 13. The fix is to bucket on time too, so one busy chat spreads across many shards. This is exactly how Discord stores trillions of messages.

And the one read I refuse to serve from a lagging replica: the message you just sent. Everything else, scrolling old history, can come from a replica that is a few seconds behind. That one cannot, or the app looks broken (Day 12).

A week ago a database was a black box. Now it is a set of choices with numbers behind them.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #databases #learninginpublic

## X thread

**1/**

Day 14, end of week 2 of 60 days of system design. I designed the storage layer for a messaging app, and every decision was a day from this week, with a number behind it.

**2/**

Scale: 2B users x 50 messages = ~1M messages/sec, 3M at peak, ~11 PB a year.

That estimate alone ends the "one database?" question. This is sharded from day one.

**3/**

Engine: LSM, not B-tree. Messages are append-only at millions/sec. Day 9 I measured a B-tree 11x slower on random writes. You cannot pay that here. An LSM append does not care about order.

**4/**

Hot query "last 50 in this chat": partition by chat, order by time, page with keyset not offset (Day 5). Shard by chat id so it hits one shard.

Trap: a 50M-member channel melts that one shard (Day 13). Fix: bucket by time too, spread it. Exactly what Discord does.

**5/**

The one read I will not serve from a lagging replica: the message you just sent. Scrolling old history can lag a few seconds, nobody notices. Your own just-sent message cannot (Day 12).

Week 2 done. A database went from black box to a set of choices with numbers.

Code: github.com/anurag629/system-design-60-days
