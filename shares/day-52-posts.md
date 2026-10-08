---
title: "Day 52 posts"
parent: "Day 52: mock, a chat system"
grand_parent: "Week 8: putting it all together"
nav_order: 3
---

# Day 52 posts: LinkedIn and X

The angle is that chat inverts the request-response model, and that flip is where all the difficulty lives. Swap in your own voice.

## LinkedIn

Day 52 of 60 days of system design. Mock 2: design a chat system like WhatsApp, 45 minutes, timed.

Here is the thing that reframed it for me. Every system I have designed for 50 days has the same shape: the client asks, the server answers. A URL shortener, a feed, a key-value store, all request-response.

Chat breaks that. A message for you arrives while you are just sitting there with the app open, and the server has to push it to you without you asking. That one inversion is where every hard part comes from.

Because the server pushes, every online user holds a persistent connection to a gateway server. So now your gateways are stateful, they hold millions of live connections, which no stateless web service ever has to deal with. And you get a genuinely new problem: I am connected to gateway 7, my friend is on gateway 2000, so how does my message cross from one to the other? You need a routing layer, a map of which gateway each user is attached to right now.

Three more things the clock taught me:

Delivery is at-least-once plus a message id the client dedupes on, plus a per-conversation sequence number for ordering. That combination gives you "exactly once, in order" without magic.

Offline is not a special case you bolt on, it is half the design. If you are offline, nothing is pushed, your messages wait in durable storage, and your device syncs from your last-seen sequence when you reconnect.

Presence (online, last seen, typing) is secretly the most expensive feature, because it changes constantly and everyone watching you wants it live. The honest answer is to make it best-effort and slightly stale, because perfectly live presence at a billion users is not worth the cost.

The trap was feature soup: I wanted to design encryption and media upload. The interviewer wants to see you reason about delivery at scale. Protect the core.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #interviewprep #learninginpublic

## X thread

**1/**

Day 52 of 60 days of system design. Mock 2: design WhatsApp, 45 min, timed.

One reframe made the whole thing click.

**2/**

Every system for 50 days: client asks, server answers. Request-response.

Chat breaks it. A message arrives while you sit idle, and the server must push it to you. That inversion is where all the difficulty comes from.

**3/**

Because the server pushes, every user holds a persistent connection to a gateway. Your gateways are now stateful, holding millions of live sockets.

New problem: I'm on gateway 7, my friend on 2000. You need a routing layer mapping user to gateway.

**4/**

Delivery = at-least-once + a client-deduped message id + a per-conversation sequence number for order. That combo gives "exactly once, in order."

**5/**

Offline is half the design, not a bolt-on. Messages wait in durable storage, your device syncs from last-seen sequence on reconnect.

Presence is the secret monster: best-effort and slightly stale on purpose.

**6/**

The trap: feature soup (encryption, media). Protect the core: connection, routing, delivery, offline.

Code: github.com/anurag629/system-design-60-days
