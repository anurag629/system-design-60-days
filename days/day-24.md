---
title: "Day 24: Kafka, partitions and consumer groups"
parent: "Week 4: async, queues and the log"
nav_order: 3
has_children: true
---

# Day 24
## Kafka's real design: partitions for speed, and order only inside a lane 🚚

Today's one idea: a Kafka topic is not one log, it is a bundle of independent logs called partitions, and almost everything people find confusing about Kafka is really a confusion about partitions. Partitions are how you go fast (many consumers working at once). The partition count is a hard ceiling on how fast you can go. And the famous "Kafka keeps messages in order" is only true inside a single partition, never across the whole topic. Once you see that one rule, partition = hash(key) % P, the parallelism and the ordering both fall straight out of it.

Yesterday you built a single append-only log and a consumer that remembered its own offset. Today you cut that log into P lanes and let a team of consumers share them, and you measure the exact point where adding more consumers stops helping.

---

## Before you start ⏪

Bring Day 23 with you. You need the log in your head: append-only, every record gets an offset, and a consumer tracks its own position so it can replay. A partition is exactly that log. A topic is just several of them side by side. Day 22's queue intuition helps too, because a consumer group is how Kafka turns one topic into a shared work queue without losing the replay you got yesterday.

A little Python with threads is enough for the lab. If you did Day 17 (the stampede) you have already seen the pattern we use: start a bunch of threads together and measure wall-clock time.

---

## Words you will meet today 📖

A partition is one append-only log. A Kafka topic is split into P partitions, and each one is an independent ordered sequence of records with its own offsets. The partition, not the topic, is the real unit of storage and parallelism.

A key is the field on a record that decides its partition. The producer computes partition = hash(key) % P, so the key, and nothing else, picks the lane. Give two records the same key and they always land in the same partition.

A partitioner is the little function that does that hashing. The default hashes the key. If a record has no key at all, the partitioner just spreads records round robin, and you lose any per-key ordering because there is no key to order by.

A consumer group is a set of consumers that share the work of a topic. The group gets every record exactly once between its members, and the rule is strict: each partition is read by exactly one consumer in the group. Two different groups each get their own full copy of the topic.

A rebalance is what happens when a consumer joins or leaves the group. Kafka reassigns partitions so each live consumer again owns a fair share. Useful, but it pauses consumption for a moment, which is one reason you do not want a huge partition count churning constantly.

The ordering guarantee is the single promise: records are delivered in order within a partition, and there is no ordering promise across partitions. Everything sensible you do with keys is about lining up the thing you need ordered with a single partition.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Kafka docs, topics and partitions](https://kafka.apache.org/documentation/#intro_topics). Straight from the source. Short, and it says plainly that a topic is a partitioned log and that order is per partition. Read the "Topics and Logs" idea first.
- [Partitioning](https://developer.confluent.io/courses/apache-kafka/partitions/) from Confluent's Apache Kafka course. The clearest short explanation of how the key picks the partition and why that gives you per-key order.
- [Consumers and consumer groups](https://developer.confluent.io/courses/apache-kafka/consumers/) from the same course. How a group shares partitions, and why one partition goes to exactly one consumer.

Watch, after the lab:
- [What is Apache Kafka?](https://www.youtube.com/watch?v=06iRM1Ghr1k) by Confluent, about 12 minutes. A clean overview that puts topics, partitions and consumers in one picture.
- Optional and longer: [Apache Kafka Crash Course](https://www.youtube.com/watch?v=R873BlNVUB4) by Hussein Nasser. Jump to the partitions and consumer-group sections (roughly 15 minutes of it) for the best plain-English take on why a partition goes to one consumer.

### A topic is the log, cut into lanes (14 min)

Yesterday's log was one lane. Everything appended to the end, every record got the next offset, and a consumer walked it in order. Simple, and it has one problem: one lane means one consumer at a time can make progress through it in order, so your throughput is capped at whatever a single consumer can chew.

Kafka's fix is almost rude in its simplicity. Take the log and cut it into P separate lanes, called partitions. Each lane is still exactly the append-only log from Day 23, with its own offsets counting from zero. A topic named "orders" with 8 partitions is really 8 independent little logs, orders-0 through orders-7. There is no global offset across the topic. Offset 5 in partition 3 has nothing to do with offset 5 in partition 6.

Why bother? Because now 8 consumers can each own one lane and work at the same time, and your throughput is 8 times a single consumer instead of 1. Partitions are the unit of parallelism. That phrase is worth memorising, because it is the answer to a surprising number of Kafka questions. How do I make Kafka faster? More partitions. Why did adding consumers stop helping? You ran out of partitions. How much can one topic scale? About as far as you are willing to add partitions.

The picture to hold: the topic is a label, the partition is the real thing. Storage is per partition, ordering is per partition, parallelism is per partition.

### The key is the whole trick (12 min)

So which lane does a record go in? The producer decides, with one line:

    partition = hash(key) % number_of_partitions

That is the entire partitioning rule, and it is doing two jobs at once.

The first job is spreading load. Different keys hash to different numbers, so they scatter across all the partitions roughly evenly. That is the parallelism: a million different users' events fan out across your 8 lanes, and 8 consumers share the work.

The second job is quieter and more important. The same key always hashes to the same number, so every record with that key lands in the same partition, every single time. And a partition keeps its records in order. Put those together and you get the one guarantee people actually need: all the records for one key stay in order, even though the topic as a whole is a jumble of lanes.

This is why you key your records by the thing you need ordered. If you are publishing order events, created then paid then shipped, you use the order_id as the key. Now all three events for order number 4517 land in the same partition, in the order you sent them, and the consumer reading that partition sees created, paid, shipped, never shipped before paid. Meanwhile order 4518's events are off in some other lane, being processed in parallel, and you do not care how the two orders interleave globally because no human ever needed orders 4517 and 4518 to be in a strict global sequence.

Think of a busy sweet shop during Diwali with several billing counters. To keep one customer's items billed in the right order, you always send that customer to the same counter. Different customers go to different counters, so billing runs in parallel. If someone later asks "in what exact order were all the items in the whole shop billed today?", there is no clean answer, because the counters ran on their own clocks. That is per-key order with no global order, which is precisely Kafka.

One trap lives here, and the drills hit it. The rule is hash(key) % P. The moment you change P, by adding partitions, the same key can hash to a different lane. Old records for a key stay where they were, new ones may go somewhere else, and per-key order across that change is broken. Picking the partition count is a decision you live with.

### Consumer groups: dividing the lanes (12 min)

A consumer group is how a team of consumers shares a topic. You give them all the same group name, and Kafka hands out the partitions so that each partition is owned by exactly one consumer in the group. Nobody shares a partition. That exclusivity is the whole design.

Picture the delivery partners for a food app across a city. The city is carved into pin-code zones, and each zone is handled by exactly one partner, so two partners never turn up for the same parcel. Add more partners and the city clears faster, but only up to a point. Once every zone has its own partner, the next partner you hire just stands at the hub with nothing to do. To actually go faster you have to carve the city into more zones.

Partitions are the zones. Consumers are the partners. So throughput climbs as you add consumers, right up to the moment you have one consumer per partition, and then it goes flat. Extra consumers beyond the partition count are assigned nothing and sit idle. This is the single most useful operational fact about Kafka: you cannot have more useful consumers in a group than you have partitions. If your consumers are falling behind and you are already at one-per-partition, adding consumers will not help. You add partitions.

Two more things worth knowing. When a consumer dies or a new one joins, the group rebalances, reassigning partitions so the live consumers again split them fairly. And if you point a second, separate consumer group at the same topic, it gets its own complete copy of every record, read at its own pace, with its own offsets. That is the clever bit: within one group Kafka behaves like a work queue (each record handled once, by one member), and across groups it behaves like pub/sub (every group sees everything). One log, both patterns, decided entirely by which group name you use.

### The ordering guarantee, stated correctly (8 min)

Here is the sentence to carry out of today, because interviews and outages both turn on it. Kafka guarantees order within a partition, and makes no ordering promise across partitions.

People misremember this as "Kafka keeps messages in order," full stop, and then they are baffled when a consumer sees events out of sequence. What actually happened is that the events went to different partitions, each partition was read by a different consumer at a different speed, and the order the application saw was decided by whichever consumer happened to be quicker. Within each partition everything was perfectly ordered. Across partitions there was never any promise to break.

You get to choose where you sit on this. Key everything the same and you force it all into one partition, which gives you strict global order and also a single lane, which means no parallelism and the throughput of exactly one consumer. Spread keys across many partitions and you get all the parallelism, with order preserved only per key. There is no setting that gives you both global order and parallelism, because they are the same dial pointed in opposite directions. The lab makes you watch this happen.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-24-drills.md`](../notes/day-24-drills.md). About 8 minutes each.

D1. A topic has 12 partitions and the key is user_id. One busy user sends 1,000 messages. How many partitions do that user's messages land on, and why does that keep them in order? If you later grow the topic to 24 partitions, what happens to that user's ordering?

D2. A topic has 6 partitions and a consumer group has 4 consumers. How are the partitions shared out? What is the most consumers that can do useful work here? If you run 10 consumers in the group, how many sit idle, and what do you change to go past 6?

D3. You must process each order's events (created, paid, shipped) strictly in that order, on an 8-partition topic. What do you pick as the key, and why does that give you the guarantee? Can you also guarantee a single global order across all orders, and what would it cost?

D4. You need to process 60,000 messages per second, and one consumer handles about 5,000 per second. What is the minimum partition count, and how much headroom would you leave? Give two concrete reasons not to just set the partition count to 1,000.

D5. Two separate consumer groups, A with 3 consumers and B with 1, both subscribe to the same 6-partition topic. Does group B receive every message? Do the two groups slow each other down? What does this tell you about Kafka being a queue and a pub/sub log at the same time?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-24-partitions/partitions.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-24-partitions/partitions.py).

It is in three parts. Part 1 is the partitioner: it spreads many keys across 8 partitions and shows that one key, sent fifty times, always lands in a single partition. Part 2 is the consumer group: it runs the same workload with 1, 2, 4, 8 and 16 consumers and measures the throughput, so you watch it climb to the partition count and then go flat with half the consumers idle. Part 3 is ordering: it proves that records are in order within a partition, scrambled across two partitions, and still in order per key.

Standard library only, pure threads, nothing written to disk, and it runs in well under 40 seconds.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. You send the same key through the producer 50 times. How many different partitions do those 50 records land in?
- P2. With 8 partitions, you grow the group from 1 consumer to 8 (consumers equal partitions). How many times higher is the throughput at 8 than at 1?
- P3. Now push the group to 16 consumers. A partition goes to exactly one consumer. How many of the 16 end up with no partition and sit idle?
- P4. A key's records all share one partition, and a partition is read in order. Across the whole stream, how many times does a single key's records come out in the wrong order?

P2 is the one to feel in your gut first. Write a number. Most people say something vague like "faster"; the point of the lab is to see it land almost exactly on the partition count.

### Fill in the TODOs

1. TODO 1 is the partitioner itself, partition = hash(key) % P. This single line is the whole day. It is what pins a key to a lane.
2. TODO 2 is the group assignment, partition p to consumer p % C, a dict that gives each partition to exactly one consumer. This is what makes extra consumers idle.
3. TODO 3 is the throughput, records divided by the slowest consumer's time. The headline of Part 2.
4. TODO 4 is the out-of-order counter, used three ways in Part 3 to check order within a partition, across partitions, and per key.

```bash
cd labs/day-24-partitions
python3 partitions.py
```

### What you're going to discover

Part 1 is the quiet one. Many different keys spread almost evenly across all 8 partitions, which is your parallelism. But the one hot key, sent fifty times, lands in exactly one partition every time. Same rule, two effects: spread for strangers, a fixed home for each individual key.

Part 2 is the headline. Throughput roughly doubles each time you double consumers, 1 then 2 then 4, and hits about 8 times at 8 consumers, one per partition. Then you add 8 more consumers and nothing happens. Throughput stays flat and 8 consumers own no partition at all. You are looking at the hard ceiling: you cannot have more useful consumers than partitions.

Part 3 is the guarantee, measured. Each partition on its own is perfectly ordered, zero records out of place. Interleave two partitions the way two independent consumers really would, and the global order is scrambled. But check any single key and it is back to zero out of order, because that key lives in one partition. That contrast, ordered per key and not globally, is the exact thing Kafka promises and the exact thing people get wrong.

### Traps ⚠️

- The throughput speedup will not be a perfect 8.00. Thread scheduling and timer resolution mean you will see something like 7.8 to 8.1. That is the lesson, not noise: it rides the partition count. Trust the shape, not the third decimal.
- Part 2 deliberately gives every partition an equal load so the scaling is clean. Real topics have skew, one partition hotter than the rest, and then your group is only as fast as the consumer stuck with the fattest partition. That is a real problem (it is the Day 18 hot key wearing a Kafka shirt), and it is why key choice matters so much.
- The partitioner uses a stable hash (crc32), not Python's built-in hash(), on purpose. Python randomises string hashing per process, so built-in hash() would send the same key to different partitions on different runs. A real partitioner must be stable, which is the same reason your answer to D1 matters.

### Deliverable

[`labs/day-24-partitions/RESULTS.md`](../labs/day-24-partitions/RESULTS.md) has a skeleton. Paste the output, and write two lines: how many times faster the group got at one consumer per partition (and what happened past that), and the one-sentence ordering guarantee in your own words.

---

## Block 4: write (30 min) 📣

Your angle today is the correction: "Everyone says Kafka keeps messages in order. I measured it, and that is only true inside one partition. Here is the one rule, partition = hash(key) % P, that gives you both parallelism and per-key order, and why you can never have both global order and speed." The consumer-group table, doubling to the partition count then flat, is the screenshot.

Example posts are on the [Day 24 posts](../shares/day-24-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the throughput speedup you measured at one consumer per partition, and one thing you still cannot explain.

Day 25 is delivery semantics: at-least-once, at-most-once, and why exactly-once is more marketing than physics. Today you learned how Kafka spreads work and what it keeps in order. Tomorrow you crash a consumer mid-job, watch the duplicates appear, and fix them the way real systems do, with idempotency keys, the same idea that stops your UPI retry from charging you twice.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. With the key set to user_id, that user's 1,000 messages all hash to the same number, so they land on exactly one of the 12 partitions. Because a partition is an ordered append-only log read by one consumer, those 1,000 messages stay in the order they were sent. That is the per-key ordering guarantee. Now grow the topic to 24 partitions: the partitioner computes hash(user_id) % 24, which is a different lane from hash(user_id) % 12. The messages already written stay in the old partition, but new messages for that user may go to a new one, and the ordering across the change is gone. This is why you treat partition count as close to permanent, and why people who need to grow it often create a new topic and migrate rather than repartition a live one.

D2. Kafka hands the 6 partitions to the 4 consumers so each partition has exactly one owner: two consumers get 2 partitions each and two get 1 each (a 2, 2, 1, 1 split). The most consumers that can do useful work is 6, one per partition. If you run 10 consumers in the group, 6 own a partition and 4 sit idle, owning nothing, because a partition is never shared between two consumers in a group. To use more than 6 consumers you must first increase the partition count. The partition count is the ceiling on group parallelism, full stop.

D3. Use the order_id as the key. Then every event for a given order, created, paid and shipped, hashes to the same partition and is read in order by the one consumer that owns that partition, so you can never see shipped before paid for that order. You get strict per-order ordering while different orders still spread across all 8 partitions and process in parallel. Can you also guarantee a single global order across all orders? Only by forcing every record into one partition (for example a constant key), which serialises the whole topic into a single lane. That gives global order but kills parallelism: your throughput drops to one consumer's worth, no matter how many you run. Global order and parallelism are the same dial pointed opposite ways.

D4. One consumer does about 5,000 per second and you need 60,000, so you need at least 60,000 / 5,000 = 12 partitions to have 12 consumers working at once, and you would leave headroom, say 16 to 24, for spikes, for uneven partition load, and so you can add a consumer or two without immediately hitting the ceiling. But do not just set it to 1,000. First, every partition is real overhead: open file handles and memory on the brokers, more end-to-end latency, and slower, more disruptive rebalances when a consumer joins or leaves, so thousands of partitions for a workload that needs twelve is pure cost. Second, more partitions means more, smaller batches and more metadata to manage, which can actually lower throughput and raise latency. You size partitions to the throughput you need with sensible headroom, not to the largest number you can type.

D5. Yes, group B receives every message. Separate consumer groups each get their own complete copy of the topic, with their own offsets, read at their own pace, so B's single consumer reads all 6 partitions and sees every record, while A's 3 consumers split the 6 partitions among themselves (2 each) and share the work. The groups do not slow each other down in the logical sense: each tracks its own position and Kafka serves them independently (they do share broker resources, but neither consumes the other's records). This is the two-faced nature of a Kafka topic. Within one group it is a work queue, each record handled once by one member. Across groups it is pub/sub, every group sees the whole stream. The same log gives you both, and which one you get is decided purely by whether consumers share a group name.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-24-partitions/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-24-partitions/solution.py).

TODO 1, the partitioner, the whole day in one line. Same key in, same partition out:

```python
return hash_key(key) % num_partitions
```

TODO 2, the group assignment. Every partition to exactly one consumer, round robin, which is what leaves extra consumers idle:

```python
return {p: p % num_consumers for p in range(num_partitions)}
```

TODO 3, the throughput. Records over the slowest consumer's wall time, because a group finishes when its last consumer finishes:

```python
return total_records / wall_seconds
```

TODO 4, the out-of-order counter. Every place a later record has a smaller production sequence number than the one before it:

```python
return sum(1 for a, b in zip(seqs, seqs[1:]) if b < a)
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 8 partitions.

```
==============================================================================
Part 1: partitioning. hash(key) % P decides where a record goes.
==============================================================================
  240 different keys spread across the 8 partitions:
    partition:  p0  p1  p2  p3  p4  p5  p6  p7
    records:    31  29  30  30  30  30  31  29
    partitions that got at least one key: 8 of 8

    key cart-9     -> partition p6
    key order-7    -> partition p2
    key user-42    -> partition p3
    key payment-3  -> partition p2

  the one key 'user-42', sent 50 times, landed in 1 partition(s)
  Different keys fan out across every partition, which is the
  parallelism. But one key is pinned to one partition, which is what
  lets that key's records stay in order. Both come from the same rule.

==============================================================================
Part 2: consumer groups. Add consumers, but only up to the partition count.
==============================================================================
  8 partitions, 100 records each, 800 records total, 8 ms of work per record.

    consumers   wall(s)   records/s   speedup   idle
        1         7.55         106     1.00x     0
        2         3.82         209     1.98x     0
        4         1.91         419     3.96x     0
        8         0.96         833     7.86x     0   <- C = P
       16         0.96         832     7.85x     8

  throughput climbs almost linearly to C = P = 8 (7.9x), then stops.
  at C = 16 it is still about 7.9x, no better, and 8 consumers
  own nothing at all. A partition goes to exactly one consumer, so the
  partition count is the hard ceiling on useful parallelism. Want more
  consumers to help? You have to add partitions first.

==============================================================================
Part 3: ordering. Inside a partition yes, across partitions no.
==============================================================================
  partition p1, production seq order: [2, 3, 7, 8, 12, 13, 17, 18, 22, 23, 27, 28, 32, 33, 37, 38]
  partition p0, production seq order: [4, 9, 14, 19, 24, 29, 34, 39]
    each partition on its own is in order, out-of-order count: 0

  now two consumers read p1 and p0 together at different speeds.
  the order the app actually sees: [4, 2, 9, 14, 3, 19, 24, 7, 29, 34, 8, 39, 12, 13, 17, 18, 22, 23, 27, 28, 32, 33, 37, 38]
    out-of-order count across the two partitions: 5  (not 0)

  per-key check: every key's own records, across the whole stream,
    out-of-order count: 0
  So global order is gone the moment you use more than one partition.
  But a key lives in one partition and a partition is read in order,
  so that key's records are still perfectly ordered. That, and only
  that, is what Kafka promises you.

==============================================================================
Scoreboard
==============================================================================
  P1 same key -> partitions          you =   1.0   actual =     1.0        close enough
  P2 speedup at C = P                you =   8.0   actual =     7.9 x       close enough
  P3 idle consumers at C = 2P        you =   8.0   actual =     8.0        close enough
  P4 per-key order violations        you =   0.0   actual =     0.0        close enough

==============================================================================
The number to carry
==============================================================================
  Partitions are the unit of parallelism: 8 of them, and throughput
  rose about 7.9x going from 1 consumer to 8, then went flat
  (7.9x at 16 consumers, with 8 sitting idle). You cannot
  have more useful consumers than partitions. And ordering is the
  guarantee people get wrong: within a partition it held (0 out of
  order), across partitions it broke (5 out of order), but every
  key's own records stayed in order (0), because a key maps to one
  partition. Parallelism and per-key order from the one hashing rule.
```

Part 1 is the rule doing its two jobs. The 240 distinct keys land almost evenly across all 8 partitions, roughly 30 each, which is the parallelism you cash in during Part 2. But the single key user-42, sent 50 times, lands in partition 3 all 50 times. Spread for the crowd, a fixed home for the individual, both from one hash.

Part 2 is the ceiling. One consumer gets 106 records a second. Double to two consumers and it nearly doubles to 209, then 419 at four, then 833 at eight, which is the full 8 times, because now each of the 8 consumers owns one of the 8 partitions. Add eight more consumers and nothing moves: 832 a second, basically identical, and 8 consumers own no partition and do nothing. That flat line is the single most practical fact about Kafka throughput. The partition count is the ceiling, and consumers past it are dead weight.

Part 3 is the guarantee, measured three ways. Each partition read on its own is perfectly ordered, 0 out of place. The moment two consumers read two partitions at their own speeds, the order the application sees is scrambled, 5 inversions in this run, and in general there is simply no promise there. But every individual key, checked across the whole stream, comes back 0 out of order, because that key sits in one partition and a partition is read in sequence. Per key yes, globally no. That is the whole of Kafka's ordering promise, and now you have watched it hold and break in the same run.

The one line to carry: a Kafka topic is a bundle of logs, parallelism is capped at the number of them, and order lives inside one of them, so you choose your key to line up the thing you need ordered with a single partition.

</details>
