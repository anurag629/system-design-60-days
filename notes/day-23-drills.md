---
title: "Day 23 drills"
parent: "Day 23: the log as a primitive"
grand_parent: "Week 4: async, queues and the log"
nav_order: 2
---

# Day 23 drills

Paper first. Offsets, the consumer's position, delivery semantics, and replay.

D1 (a log holds 5,000,000 records at offsets 0..4,999,999 and you append one more: what offset does it get? Then you want to "delete" the record at offset 3,000,000: what does an append-only log do instead of editing in place, and does any earlier offset change?):

D2 (a consumer has committed offset 4,200,000 while the log head is at 5,000,000: what is its lag? It commits after processing each record and crashes right after processing offset 4,500,000 but before committing it: what offset does it resume from, and how many records does it re-read?):

D3 (you can commit the offset before processing a record or after: for each order, what does a crash in the gap cost, a duplicate or a loss? Which order is at-least-once and which is at-most-once? Pick the right order for charging a card, and for bumping a view counter, and say why):

D4 (your events go to a log with 30 days of retention; a brand new analytics job joins today and wants to rebuild from the last 30 days: what offset does it start at, and what happens to the existing consumer's position while it runs? Why could you not do this if the events had gone through a traditional queue?):

D5 (a queue drops a message once it is acknowledged; a log keeps records until a retention limit of time or size: name one thing keeping data after it is read buys you, and one real cost of keeping it, and say when you would set a deliberately short retention):
