---
title: "Day 24 posts"
parent: "Day 24: Kafka, partitions and consumer groups"
grand_parent: "Week 4: async, queues and the log"
nav_order: 3
---

# Day 24 posts: LinkedIn and X

The consumer-group table makes a clean screenshot: throughput roughly doubling as you double consumers, right up to the partition count, then a dead flat line with half the consumers idle. Swap in your own numbers and voice.

## LinkedIn

Day 24 of 60 days of system design. Today I measured the two things about Kafka that people get wrong in interviews all the time, on my own laptop, with pure Python.

First, partitions are the unit of parallelism, and the partition count is a hard ceiling. I built a topic with 8 partitions and threw a consumer group at it, growing the group from 1 consumer to 16:

    consumers   records/s   speedup   idle
        1           106      1.00x      0
        2           209      1.98x      0
        4           419      3.96x      0
        8           833      7.86x      0   <- consumers == partitions
       16           832      7.85x      8

Throughput almost doubles every time you double consumers, right up to 8. Then it stops dead. At 16 consumers, 8 of them own no partition and just sit there. A partition is read by exactly one consumer in a group, so once you have one consumer per partition, extra consumers do nothing. If you want more parallelism, you add partitions, not consumers.

Second, the ordering guarantee. People say "Kafka keeps messages in order." That is only half true, and the half they skip is the important one. I produced an ordered stream and checked three things:

- within a single partition: 0 messages out of order
- across two partitions read together: out of order, scrambled
- for any single key: 0 messages out of order

Kafka guarantees order inside one partition, never across partitions. The trick is that a message's key decides its partition (partition = hash(key) % number_of_partitions), so every message with the same key lands in the same partition and stays ordered. That is why you key order events by order_id: all the events for one order keep their sequence, even though the topic as a whole does not.

So the whole design falls out of one hashing rule. Same key, same partition, which buys you per-key order. Different keys, different partitions, which buys you parallelism. You just cannot have both global order and parallelism at the same time, and now I have seen exactly why.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #kafka #distributedsystems #learninginpublic

## X thread

**1/**

Two things about Kafka that people get wrong in interviews, both measured on my laptop today. Day 24 of 60 days of system design.

**2/**

Partitions are the unit of parallelism, and they are a hard ceiling.

8 partitions, consumer group growing from 1 to 16 consumers:

    1  consumer  -> 1.00x
    2  consumers -> 1.98x
    4  consumers -> 3.96x
    8  consumers -> 7.86x
    16 consumers -> 7.85x, and 8 of them idle

**3/**

Double the consumers, roughly double the throughput, up to 8. Then flat.

A partition is read by exactly ONE consumer in a group. Once you have one consumer per partition, extra consumers own nothing. More parallelism means more partitions, not more consumers.

**4/**

The ordering guarantee everyone half-remembers.

"Kafka keeps messages in order" is only true INSIDE one partition.

My stream, checked three ways:
- within a partition: 0 out of order
- across two partitions: scrambled
- per key: 0 out of order

**5/**

Why does per-key order survive?

partition = hash(key) % num_partitions

Same key always hashes to the same partition, and a partition is read in order. So every event for one key stays ordered, even though the topic as a whole does not.

**6/**

That is why you key order events by order_id. created, paid, shipped all land in one partition, in sequence.

The whole thing is one rule:
same key -> same partition -> per-key order.
different keys -> different partitions -> parallelism.

You cannot have global order AND parallelism. Pick.

Code: github.com/anurag629/system-design-60-days
