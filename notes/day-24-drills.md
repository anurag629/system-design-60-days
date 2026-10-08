---
title: "Day 24 drills"
parent: "Day 24: Kafka, partitions and consumer groups"
grand_parent: "Week 4: async, queues and the log"
nav_order: 2
---

# Day 24 drills

Paper first. Partitioning by key, consumer groups, and the one ordering guarantee Kafka actually gives.

D1 (a topic has 12 partitions and the key is user_id; one busy user sends 1,000 messages: how many partitions do that user's messages land on, why does that keep them in order, and what happens to that ordering if you later grow the topic to 24 partitions):

D2 (a topic has 6 partitions and a consumer group has 4 consumers: how are partitions shared out, what is the most consumers that can do useful work, how many sit idle if you run 10, and what do you change to go past 6):

D3 (you must process order events (created, paid, shipped) for each order strictly in that order, on an 8-partition topic: what do you pick as the key and why does that give you the guarantee, and can you also guarantee a single global order across all orders, at what cost):

D4 (you need 60,000 messages/sec and one consumer handles about 5,000/sec: the minimum partition count, how much headroom you would leave, and two concrete reasons not to just set partitions to 1,000):

D5 (two separate consumer groups, A with 3 consumers and B with 1, both subscribe to the same 6-partition topic: does group B receive every message, do the groups slow each other down, and what does this say about Kafka being a queue and a pub/sub log at once):
