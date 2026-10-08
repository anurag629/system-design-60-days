---
title: "Day 52 mock brief"
parent: "Day 52: mock, a chat system"
grand_parent: "Week 8: putting it all together"
nav_order: 1
---

# Mock 2: design a chat system like WhatsApp

Copy this into your fork. 45-minute timer. Out loud. Lead with the connection model. Stop when it rings and grade yourself.

## The brief

Design a messaging app like WhatsApp. One-to-one and group chats, delivery receipts (sent, delivered, read), presence, and offline delivery. Assume a billion registered users. You may be nudged toward media, encryption, or huge groups, so leave room, but protect the core: connection, routing, delivery, offline.

## 1. Requirements (5 min)

Functional:

Non-functional (name exactly-once, ordered-per-conversation, scale):

## 2. Scale estimate (5 min)

Sends/s (peak):

Concurrent open connections:

Storage per day:

## 3. API and core entities (5 min)

Events over the connection:

Entities (model the message and the per-conversation sequence):

## 4. High-level design (10 to 15 min)

The connection and routing layer (how A on gateway 7 reaches B on gateway 2000):

The send path (online recipient):

The offline path (recipient disconnected, then reconnects):

## 5. Deep dives (10 to 15 min)

The hinge I am going deep on (delivery and ordering, or group fan-out, or presence):

My answer and the tradeoff:

## 6. Bottlenecks and failure (5 min)

A gateway dies with its connections: what happens, and how is no message lost?

What gets shed first under load?

## Self-grade (score each out of 2)

- [ ] Requirements: exactly-once, ordered-per-conversation, billion-user scale
- [ ] Scale: sends/s and connection count
- [ ] API and entities: message + per-conversation sequence
- [ ] High-level: persistent connections + routing layer, not stateless web
- [ ] Deep dive: offline sync or fan-out done properly
- [ ] Failure and cost: gateway death and reconnect, presence best-effort

Total out of 12: ______  The concept I drill again: ______
