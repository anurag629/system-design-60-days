---
title: "Day 28: designing a notification system"
parent: "Week 4: async, queues and the log"
nav_order: 7
has_children: true
---

# Day 28
## Designing a notification system, where every week-4 idea has to show up at once 🔔

Today's one idea: a notification system is the place all of week 4 collides. An event has to become a push, an email and an SMS, for maybe millions of users, without losing any, without sending duplicates, without one slow provider blocking the others, and without falling over when someone broadcasts to everyone. Every one of those requirements is a day you just did. Today you assemble them.

This is the week 4 finale, a design day. No coding lab. You design a notification service on paper, against the clock, then measure how differently you think about async work than you did on Day 22.

---

## Before you start ⏪

Bring all of week 4. Day 22 (async and the bounded queue), Day 23 (the log and replay), Day 24 (partitions and consumer groups), Day 25 (at-least-once and idempotency), Day 26 (the outbox), Day 27 (backpressure and shedding). Today every one of them is load-bearing, which is the point of the day.

---

## Words you will meet today 📖

Fan-out, here, is one event becoming many pieces of work: one "order shipped" event becomes a push to the phone, an email, and an SMS, each for a specific user, and a broadcast event becomes one message per recipient.

A channel is one delivery route: push (APNs for Apple, FCM for Android), email (through a provider like SendGrid), SMS (through a provider like Twilio). Each has its own provider, its own rate limit, and its own failure modes.

A provider is the external service that actually delivers on a channel. You do not control it, it rate-limits you, and it goes down sometimes, which shapes the whole design.

A dead-letter queue (DLQ) is where a message goes after it has failed its retries, so it is set aside for inspection instead of blocking the queue or being lost.

Channel isolation means each channel has its own queue and workers, so a slow or dead provider on one channel cannot back up or stall the others.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Design a notification fan-out service: push, email, SMS at scale](https://dev.to/gabrielanhaia/design-a-notification-fan-out-service-push-email-sms-at-scale-5a0d). The exact problem, with per-channel queues, retries, idempotency and backpressure all named. This is today's design, written out.
- [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) from the AWS Builders' Library. How retries actually work in production, and how a naive retry storm makes an outage worse.
- [Kafka's design](https://kafka.apache.org/documentation/#design), the official doc. The log, partitions and consumer groups from days 23 and 24, from the source, since a real notification system usually rides on exactly this.

Watch, after you have done your own design:
- [Notification service system design](https://www.youtube.com/watch?v=CUwt9_l0DOg) by codeKarle, about 20 minutes. A clean walkthrough of the queues, channels and scale.

### The shape: one event, many channels, all async (15 min)

Start with the access pattern, as always. Something happens in the product: an order ships, someone likes your post, a payment fails. That event needs to reach a user, maybe on several channels, maybe for millions of users at once. The triggering service cannot do this inline. It would be absurd for the "place order" request to wait while an email is sent through a third party. So the first move, Day 22, is async: the triggering service publishes an event and returns immediately.

From there the event flows into a notification service that decides, per user, which channels to use (respecting preferences and do-not-disturb) and fans the event out into per-channel work. The crucial decision, and it is Day 27 wearing a product hat, is channel isolation: push, email and SMS each get their own queue and their own pool of workers. Why? Because the providers fail independently. If SendGrid has a bad hour, you want the email queue to back up quietly while push and SMS sail through, not one shared queue where a slow email jams everything behind it.

Each channel's workers pull from their queue and call the provider. Providers rate-limit you (APNs and Twilio both do), so the workers respect that rate, and the queue in front of them is the buffer that absorbs a spike, exactly Day 27's bounded-queue-plus-backpressure. A message that keeps failing after its retries goes to a dead-letter queue rather than blocking the line or vanishing.

### Why every reliability guard here is a week-4 day (10 min)

The hard part of a notification system is not sending one notification. It is sending millions without losing any and without sending any twice, and every guard that makes that true is a day you did this week.

Do not lose the notification. The event that triggers it must not be lost if the triggering service crashes right after committing its business change. That is the Day 26 dual-write problem, and the fix is the outbox: write the business row and the notification event in one transaction, and let a relay publish it. The "order shipped" email cannot go missing because the publish failed.

Do not send it twice. Delivery is at-least-once (Day 25): a worker might send an email, crash before recording success, and on restart send it again. The user does not want two "your order shipped" emails. The fix is an idempotency key, deterministic per notification and channel, claimed before the provider call, so a redelivery is a no-op. Exactly-once delivery is still a myth; at-least-once plus idempotency is the real thing.

Do not fall over under a spike. A broadcast to fifty million users drops fifty million jobs into the queues at once. You do not try to send them in one second. The queue buffers (Day 22), the workers drain at the provider's rate (Day 27), and because a broadcast is not real-time, that is completely fine. The queue turned a thundering spike into a steady drain.

And if you ever want to add a new channel, say WhatsApp, later: the event log (Day 23) means you can add a new consumer group that replays history or starts fresh, without touching the producers. The whole thing is built on the log.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Write your answers into [`notes/day-28-drills.md`](../notes/day-28-drills.md). About 8 minutes each.

D1. Estimate the scale. 100 million users, each getting on average 5 notifications a day across channels. Notifications per second, average and peak at 3x? Now a marketing broadcast goes to all 100 million at once: how many jobs land in the queues instantly, and roughly how long to drain them at the peak rate? What does that tell you about whether a broadcast is real-time?

D2. A worker sends an email through the provider, then crashes before it can record success, so the message is redelivered and sent again. The user gets two emails. What is the fix, what exactly is the idempotency key made of, and at which step do you check it?

D3. "Order shipped" must update the orders table and send a notification. If you commit the order and then publish the notification event as two steps, what breaks on a crash in between, and which week-4 pattern fixes it?

D4. SendGrid (email) has a slow hour. Why must email, push and SMS each have their own queue and workers, and what happens to the email backlog during that hour? Where do messages that keep failing end up?

D5. APNs rate-limits you to 20,000 pushes per second, and a broadcast just queued 10 million. What do you do: drop them, or something else? Which week-4 idea is this, and why is a notification backlog usually throttled rather than shed?

---

## Block 3: build (100 min) 🔧

Today you build a design, not code. The template is [`labs/day-28-notifications/DESIGN.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-28-notifications/DESIGN.md). Copy it into your fork and fill it in.

Do it against the clock, 45 minutes for a first full pass: requirements, scale estimate, the async event flow, per-channel fan-out and isolation, the reliability guards (outbox, idempotency, retries and DLQ), and the broadcast and failure cases. Do not open the Solutions or the readings until your 45 minutes are up.

Then improve it with the readings open, marking what you added in a different colour. That delta is week 4 landing.

### What a strong design has

A weak one draws "service to queue to worker" and stops. A strong one isolates channels so one provider's bad hour stays local, names the outbox for not losing the event and the idempotency key for not sending twice, treats provider rate limits as backpressure the queue absorbs, and has a specific answer for the broadcast to everyone. Aim for that.

### Deliverable

Your filled-in `DESIGN.md`, and one honest paragraph: which week-4 day did the design lean on hardest, and where did you have to guess?

---

## Block 4: write (30 min) 📣

Your angle is the synthesis: "I designed a notification system, and every single reliability decision was one idea from this week: the outbox so I never lose a notification, the idempotency key so I never send two, per-channel queues so one dead provider stays contained, and backpressure so a broadcast to millions drains instead of exploding." Pick the two that surprised you most.

Example posts are on the [Day 28 posts](../shares/day-28-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it, and look back 📝

Log the three: what you completed, your notifications-per-second estimate, and one thing you still cannot explain.

Then the week 4 retrospective. Think back to Day 22, when async was just "put a job on a queue." Write down the three things you now know about moving work off the request path that you did not a week ago. That gap is week 4.

Week 5 is the hard one: distributed systems for real. CAP, quorums, consensus and Raft, logical clocks, and the classic papers. Everything so far mostly assumed machines that work. Next week we admit they do not, and we build the ideas that keep promises anyway. Budget the frustration; it is normal.

---

## Solutions 🔑

Open these only after your own 45-minute design pass.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. 100 million times 5 is 500 million notifications a day, about 5,000 per second average, roughly 15,000 at a 3x peak. A broadcast to all 100 million drops 100 million jobs into the queues the instant it fires. At 15,000 per second that is about 1.8 hours to drain, and the honest conclusion is that a broadcast is NOT real-time: you accept it fast into the queue and let it drain at whatever rate the providers allow. Trying to send 100 million in one second is neither possible nor necessary.

D2. The fix is an idempotency key. Make it deterministic from the notification and the channel, for example notification_id plus user_id plus channel, so the same logical notification always produces the same key. Check it right before the provider call: claim the key (a database insert with a unique constraint, or a set-if-not-exists in a dedup store), and if it is already claimed, skip the send. You check at the send step because the provider call is the non-idempotent side effect, the thing you must never do twice.

D3. If you commit the order and then publish the notification event separately, a crash in between leaves the order shipped in the database but no event published, so the "order shipped" notification is silently lost forever. This is the Day 26 dual-write problem. The fix is the outbox: write the order row and an outbox row in the same transaction, so they commit together or not at all, and a relay reads the outbox and publishes, retrying until it succeeds.

D4. Each channel has its own queue and workers so that a slow or dead provider stays contained. If email, push and SMS shared one queue, a SendGrid outage would fill that queue with stuck email jobs and starve push and SMS behind them. With isolation, the email queue backs up quietly during the bad hour while push and SMS keep flowing at full speed, and when SendGrid recovers the email workers drain the backlog. Messages that keep failing after their retries go to a dead-letter queue, set aside for inspection rather than blocking the queue or being lost.

D5. You do not drop them, you throttle: the push workers send at APNs's 20,000 per second, and the queue holds the other 9.98 million and feeds them in at that rate. This is Day 27 backpressure, with the provider's rate limit as the constraint. A notification backlog is throttled rather than shed because, unlike a live user request that is worthless if it waits, a notification is still useful a minute late, so delaying it is almost always better than dropping it. You shed only when the backlog is so hopeless that late delivery would be worse than none, which for most notifications it is not.

</details>

<details markdown="1">
<summary>A worked reference design</summary>

One good answer, not the only one. Yours will differ; what matters is that every reliability choice is a week-4 idea.

Requirements. Functional: turn a product event into deliveries across push, email and SMS, honouring each user's channel preferences and quiet hours, and support both per-user notifications and broadcasts. Non-functional: do not lose a notification, do not send duplicates, keep one failing provider from affecting the others, and survive a broadcast to everyone.

Scale, from D1: about 5,000 notifications per second average, 15,000 peak, and broadcasts that queue tens of millions at once and drain over time, not instantly.

The async flow, from Day 22: the triggering service publishes an event and returns. It never calls a provider inline.

Not losing the event, from Day 26: the triggering service writes its business change and the notification event in one transaction (the outbox), and a relay publishes to the event log. The event is on the log or it is not; there is no in-between.

The event log and fan-out, from Days 23 and 24: events live on a partitioned log (partition by user id, so one user's notifications stay ordered and the load spreads). The notification service consumes the log, applies preferences, and fans each event out into per-channel queues.

Channel isolation, from Day 27: push, email and SMS each have their own queue and worker pool. A provider's bad hour backs up only its own queue.

Not sending twice, from Day 25: delivery is at-least-once, so each send is guarded by an idempotency key (notification plus user plus channel), claimed before the provider call. Retries use exponential backoff with jitter, and messages that exhaust their retries go to a dead-letter queue.

Backpressure, from Day 27: workers send at each provider's rate limit, and the queue is the buffer. A broadcast is accepted fast and drained at provider rate, because it is not real-time.

The sentence that makes this sound senior: "every reliability guard here is a week-4 idea: the outbox so an event is never lost, the idempotency key so it is never sent twice, per-channel queues so one dead provider stays local, and the queue as backpressure so a broadcast drains instead of exploding."

</details>

<details markdown="1">
<summary>Week 4 in one page</summary>

Seven days, one idea underneath: take the slow, spiky, or must-not-be-lost work off the request path and hand it to a queue and a log.

Day 22, async and the queue. The caller drops the job and returns in microseconds instead of waiting the whole job. A bounded queue absorbs a burst and, when full, pushes back.

Day 23, the log. Append-only, offsets owned by the reader, and replay: a new consumer can re-read all of history, which a queue cannot do. This is what Kafka is built on.

Day 24, partitions and consumer groups. Partitions give parallelism, capped at the partition count; order holds within a partition and per key, not globally.

Day 25, delivery. At-least-once means duplicates; exactly-once delivery is a myth; an idempotency key gives you exactly-once effect, which is what a retried payment needs.

Day 26, the outbox. Writing to the database and publishing to a queue as two steps drifts apart on a crash; one transaction plus a relay fixes it, and the consumer still needs idempotency.

Day 27, backpressure. Producers outrun consumers; an unbounded queue defers the outage and worsens it; a bounded queue either blocks the producer or sheds the excess fast.

Day 28, today. All six, assembled into a notification system, where losing nothing, duplicating nothing, and surviving a broadcast are each one of this week's days.

If your design used the outbox, the idempotency key, channel isolation and backpressure, and had an answer for the broadcast, you did not learn six queue tricks this week. You learned how to move work off the critical path and still keep every promise. Week 5 asks what happens when the machines themselves stop keeping promises.

</details>
