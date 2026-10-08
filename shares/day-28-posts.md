---
title: "Day 28 posts"
parent: "Day 28: designing a notification system"
grand_parent: "Week 4: async, queues and the log"
nav_order: 3
---

# Day 28 posts: LinkedIn and X

The angle is synthesis: a notification system is where every reliability idea from the week has to show up at once. Swap in your own voice.

## LinkedIn

Day 28 of 60 days of system design, end of week 4. I designed a notification system, and the striking thing is that every single reliability decision was one idea from this week.

The shape is simple: a product event (order shipped, someone liked your post) is published, and the triggering service returns immediately. It never waits on an email provider. From there the event fans out into per-channel work: push, email and SMS, each with its own queue and workers.

That isolation is the first real decision. Providers fail independently, so if the email provider has a bad hour, you want the email queue to back up quietly while push and SMS sail through. One shared queue would let stuck emails starve everything behind them.

Then the hard part, which is not sending one notification but sending millions without losing any and without sending any twice. Every guard was a day:

- Do not lose it: the outbox. Write the business change and the notification event in one transaction, so a crash cannot leave the order shipped with no notification.
- Do not duplicate it: an idempotency key (notification + user + channel), claimed before the provider call. Delivery is at-least-once, so a redelivered message becomes a no-op.
- Survive a broadcast: a message to 50 million users drops 50 million jobs in the queue at once. You do not send them in a second. The queue buffers, the workers drain at the provider's rate limit, and because a broadcast is not real-time, that is fine.

A week ago async was just "put a job on a queue." Now I can see that at scale, async is a set of promises, and keeping them is the whole job.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #learninginpublic

## X thread

**1/**

Day 28, end of week 4 of 60 days of system design. I designed a notification system, and every reliability decision was one idea from this week.

**2/**

Shape: a product event is published and the triggering service returns instantly. It never waits on an email provider. The event fans out into per-channel work: push, email, SMS, each with its own queue.

**3/**

Isolation first. Providers fail independently, so email, push and SMS get separate queues. A bad hour at the email provider backs up the email queue only; push and SMS keep flowing. One shared queue would starve everything behind the stuck emails.

**4/**

The hard part is millions without loss or duplicates:

- outbox: write the change + the event in one transaction, never lose a notification
- idempotency key (notif + user + channel): at-least-once delivery, so a redelivery is a no-op, never two emails

**5/**

Broadcast to 50M: 50M jobs hit the queue at once. You do not send them in a second. The queue buffers, workers drain at the provider's rate limit, and a broadcast is not real-time, so that is fine.

Week 4 done. Async at scale is a set of promises, and keeping them is the job.

Code: github.com/anurag629/system-design-60-days
