---
title: "Day 52: mock, a chat system"
parent: "Week 8: putting it all together"
nav_order: 3
has_children: true
---

# Day 52
## Mock 2, a chat system like WhatsApp, where the hard part is the connection 💬

Today's one idea: a chat system flips the usual web model on its head. Normally the client asks and the server answers. In chat, the server has to push a message to a client that did not ask, which means holding millions of long-lived connections open and knowing which server each user is attached to right now. That one fact, the server pushes, is where all the difficulty lives.

Mock 2. Harder than the URL shortener, because delivery, presence and fan-out are genuinely tricky, and the headline scale is a billion users.

---

## Before you start ⏪

Day 50's framework sheet on the desk. Reread Day 14, where you designed the storage layer for exactly this kind of messaging app (the heavy write volume, the per-conversation ordering). Bring Day 25 (delivery semantics and idempotency, because "delivered exactly once" is the whole receipt system) and week 4 (queues, for fan-out).

---

## Words you will meet today 📖

A persistent connection (usually a WebSocket) is a network pipe held open between client and server so either side can send at any time, instead of the client having to poll "any messages for me?" every few seconds. Chat lives or dies on these.

Fan-out is delivering one sent message to all its recipients. In a one-to-one chat that is one recipient. In a group of 500 it is 500 deliveries from a single send, and that multiplication is the scaling problem.

Presence is the "online", "last seen at", and "typing..." status. It sounds trivial and is secretly one of the most expensive features, because it changes constantly and everyone watching a contact wants the update live.

A delivery receipt is the single, double, and blue tick: sent (reached the server), delivered (reached the recipient's device), read (the recipient opened it). Each tick is a message flowing back the other way.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read, lightly, for the shape:
- [Design WhatsApp](https://www.hellointerview.com/learn/system-design/problem-breakdowns/whatsapp) from Hello Interview. Current and honest, with the connection model and delivery done properly.
- Your own [Day 14 design](../days/day-14.md) and its notes. You already worked out the storage side of this, so reuse it.

Watch, after your own timed run:
- [Design WhatsApp, a system design interview with an ex-Meta senior manager](https://www.youtube.com/watch?v=cr6p0n0N-VA) by Hello Interview, about 58 minutes. A full, strong run with the framework visible in the chapter markers. If you want a shorter one, [Design Facebook Messenger](https://www.youtube.com/watch?v=uzeJb7ZjoQ4) by Exponent (now Aced) is about 15 minutes.

### The connection is the system 🔌

In a URL shortener the server answers requests. In chat, the server must reach out to a user who is just sitting there with the app open. So every online user holds a persistent connection (a WebSocket) to one of your gateway servers. Now the hard question: user A sends to user B, but A is connected to gateway 7 and B is connected to gateway 2000. How does the message get from 7 to 2000?

The answer is a routing layer. Somewhere you keep a map of "which gateway is this user attached to right now," usually in a fast store like Redis. Gateway 7 receives A's message, looks up B, sees gateway 2000, and forwards it (often through an internal queue or a direct internal call). Gateway 2000 pushes it down B's open connection. If B is offline, there is no connection, so the message goes into durable storage (Day 14) and waits, and B's device pulls it on next connect. That split, push to the connected, store for the disconnected, is the heart of the design.

### Fan-out, receipts, and the secret cost of presence 👀

Delivery is more than "send once." WhatsApp promises each message arrives exactly once and in order per conversation, which is Day 25's at-least-once plus idempotency (a message id the client dedupes on) plus a per-conversation sequence number for ordering. Receipts are just messages going the other way: when B's device receives the message it sends back a "delivered", when B opens the chat it sends a "read", and those flow back to A the same way the original did.

Group chat is where fan-out bites. A send to a group of 500 is 500 deliveries. For small groups you fan out on write (push to all 500 immediately), which is fine. For a huge group it is the celebrity problem from Day 18 again, and you may fan out on read or cap group size. And presence is the quiet monster: if a million users each watch 50 contacts, a single person coming online can trigger a storm of updates. The honest senior answer is that presence is best-effort, updated lazily, and often deliberately coarse ("last seen" rather than live), because making it perfectly live and perfectly scaled at the same time is not worth it.

---

## Block 2: drill (40 min) ✍️

Paper first, into [`notes/day-52-drills.md`](../notes/day-52-drills.md). Warm-up before the timed run.

D1. The connection. Why can you not build chat on ordinary request-response? What does a persistent connection give you, and what new problem does it create that a stateless web service never has?

D2. The routing problem. A is on gateway 7, B is on gateway 2000. Describe how A's message reaches B, and what store holds the "user to gateway" map.

D3. Offline delivery and ordering. B is offline when A sends three messages. Where do they go, how does B get them on reconnect, and what guarantees they arrive in the right order and are not shown twice (Day 25)?

D4. Group fan-out. A message to a 500-person group. What does fan-out on write cost, when would you not do it, and how is this the Day 18 celebrity problem?

D5. Presence. Why is "online / last seen / typing" one of the most expensive features to do well, and what is the honest engineering answer to keeping it cheap?

---

## Block 3: build (100 min) 🔧

The timed run. Open [`labs/day-52-mock-chat/MOCK.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-52-mock-chat/MOCK.md), copy it, set a 45-minute timer, and run all six steps out loud. Lead with the connection model, because if you start by drawing a normal web service you will have to tear it up.

Then grade yourself against the rubric in the file. Chat has more moving parts than the URL shortener, so the common failure here is drowning in features (reactions, media, encryption) and never nailing the core: connection, routing, delivery, offline. Protect the core.

### What a strong run looks like

You establish the persistent-connection model in the first few minutes and never waver. You can explain how a message crosses gateways. You handle the offline case with durable storage and ordered sync. You treat presence as best-effort out loud. And you resist the temptation to design end-to-end encryption and media upload when the interviewer actually wants to see you reason about delivery at scale.

### Deliverable

Your filled-in `MOCK.md`, your rubric score, and one line: the chat-specific concept you most need to drill.

---

## Block 4: write (30 min) 📣

Your angle is the inversion: chat breaks the model you have used for every other system this course. "Every system I have designed for 50 days has the server answering requests. A chat system has the server pushing to a client that never asked, and that single flip is where all the hard parts come from." Pick the part that surprised you.

Example posts are on the [Day 52 posts](../shares/day-52-posts.md) page.

---

## End of day: log it 📝

Log the three: your rubric score, whether you held the connection model from the start, and the one chat concept you still fumble.

Tomorrow is a change of pace: mock 3 is two smaller designs back to back, a rate limiter and a news feed, to build speed.

---

## Solutions 🔑

Open after your own timed run.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Request-response means the client always initiates, so the server can only reply to a question. But in chat, a message for B arrives while B is idle, and the server must deliver it without B asking. Polling ("any messages?" every 2 seconds) works but is wasteful and laggy at a billion users. A persistent connection (WebSocket) stays open so the server can push the instant a message arrives. The new problem it creates: your gateway servers are now stateful. Each holds millions of live connections and must know which users it owns, which a stateless web service (Day 6) never has to worry about. State is the price of push.

D2. A connects to gateway 7, which registers "user A is on gateway 7" in a shared, fast routing store (Redis). A sends a message for B. Gateway 7 looks B up in the routing store, finds "B is on gateway 2000," and forwards the message to gateway 2000 (through an internal message bus or a direct internal call). Gateway 2000 pushes it down B's open socket. The routing store is the map of user to current gateway, and it updates every time someone connects, disconnects, or reconnects to a different gateway.

D3. B is offline, so there is no connection and no gateway owns B. The messages go into durable per-conversation storage (Day 14), tagged with a sequence number. When B reconnects, B's device says "my last seen sequence for this conversation was N," and the server streams everything after N in order. Ordering comes from the per-conversation sequence number, not wall-clock time (Day 33's lesson). Not-shown-twice comes from the client deduping on message id (Day 25's idempotency), so even if the server resends on a flaky reconnect, B sees each message once.

D4. Fan-out on write means when A sends to the 500-person group, you immediately write or push the message to all 500 recipients' inboxes or connections. The cost is 500 writes or pushes from one send, and for a very large or very active group that multiplies into a flood. You would not do it for huge broadcast-style groups, where you instead fan out on read (recipients pull the group's messages when they look) or cap the group size. It is the Day 18 celebrity problem exactly: one sender with a huge audience is a hot key, and the fix is the same, do not eagerly push to a million followers.

D5. Presence changes constantly (every connect, disconnect, and keystroke for "typing"), and it is many-to-many: each user watches many contacts, and each user is watched by many. So a single person coming online can require notifying everyone who has them open, and multiplied across a billion users the update rate dwarfs the actual message rate. The honest answer is to make it best-effort and cheap: update "last seen" lazily, debounce "typing", do not guarantee presence is perfectly live, and accept coarse or slightly stale status. Chasing perfectly live presence at full scale is a cost most products quietly decide not to pay.

</details>

<details markdown="1">
<summary>A worked reference design</summary>

Requirements. Functional: one-to-one and group messaging, delivery receipts (sent, delivered, read), presence, offline delivery, message history. Non-functional: a billion users, low delivery latency, messages exactly once and ordered per conversation, highly available, durable (a message must never be lost).

Scale. Say 500 million daily active, each sending 40 messages a day, so about 20 billion messages a day, roughly 230,000 sends per second average and perhaps 700,000 at peak, each fanning out to one or more recipients. Hundreds of millions of connections held open at once.

API and entities. Over the persistent connection: send(conversation_id, client_message_id, text), and server pushes message, delivered, read events. Entities: User, Conversation, Message (id, conversation_id, sender, seq, body, created_at), and a per-user, per-conversation last-read sequence.

High-level design. Clients hold WebSocket connections to a fleet of gateway servers. A routing store (Redis) maps user to current gateway. A send travels: client to its gateway, gateway looks up each recipient, forwards through an internal bus to the recipient's gateway, which pushes down the socket. Messages are also written to durable, sharded storage (Day 14, sharded by conversation) for history and offline sync. Offline recipients get nothing pushed; their device syncs from storage on reconnect using the last-read sequence.

Deep dives. Delivery and ordering: at-least-once delivery with a client-side dedupe on message id, and a per-conversation sequence number for order (Day 25, Day 33). Fan-out: on write for normal groups, capped or read-fan-out for very large ones (Day 18). Connection management: gateways are stateful and must be drained carefully on deploy, and a client reconnects and re-registers in the routing store on any drop.

Failure and cost. A gateway dies and takes its connections with it; clients detect the drop and reconnect to another gateway, re-registering. No message is lost because sends are persisted before acknowledgement. Presence is best-effort and the first thing to shed under load. Cost is dominated by holding hundreds of millions of connections and the fan-out bandwidth, not by storage.

The sentence that sounds senior: "the server has to push, so gateways are stateful and I need a routing layer to find a user's gateway; delivery is at-least-once with client dedupe and a per-conversation sequence for ordering; and presence is deliberately best-effort because making it live and scaled at once is not worth the cost."

</details>

<details markdown="1">
<summary>The self-grade rubric</summary>

Score each out of 2.

- Requirements: named exactly-once, ordered-per-conversation, and the billion-user scale?
- Scale: produced sends/s and the connection count, not just vague "lots"?
- API and entities: modelled the message and the per-conversation sequence?
- High-level: established persistent connections and a routing layer, not a stateless web service?
- Deep dive: handled offline delivery with ordered sync, or fan-out, properly?
- Failure and cost: gateway death and reconnect, and presence as best-effort?

10 to 12, strong. 6 to 9, the core is there but you probably wobbled on the connection model or drowned in features. Below 6, rerun it and lead with the connection.

</details>
