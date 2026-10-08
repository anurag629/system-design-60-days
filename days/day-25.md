---
title: "Day 25: delivery semantics and idempotency"
parent: "Week 4: async, queues and the log"
nav_order: 4
has_children: true
---

# Day 25
## Exactly-once is mostly a lie, and idempotency keys give you the real thing 💸

Today's one idea: you cannot promise that a message is delivered exactly once across a network that drops packets and crashes workers. What you can promise is at-least-once delivery, where a message arrives one or more times, and then you make the processing idempotent so the extra arrivals do nothing. The combination behaves like exactly-once from the outside, and it is how a UPI payment that says "failed, tap again" does not charge you twice.

Yesterday you saw Kafka hand work to a consumer group and track offsets. The quiet question underneath was: what happens when a consumer takes a message, does the work, and then dies before it can say "done"? Today you answer it, and you measure the damage three different ways on your own machine.

---

## Before you start ⏪

You need the last three days in your head. A queue or log holds messages and hands them to a consumer (Day 22 and 23). A consumer reads, does some work, and tells the broker it is finished so the broker can move on (Day 24, where that "finished" marker was the committed offset). Today zooms all the way in on that one handshake: the consumer does the work, and separately it acks. The whole lesson lives in the gap between those two steps. Day 2's comfort with plain Python is enough for the lab. No external services, just the standard library.

---

## Words you will meet today 📖

An ack (acknowledgement) is the consumer telling the broker "I am done with this message, you can forget it". Until the broker hears an ack, it assumes the message might still need doing, and it will hand the message out again.

At-most-once delivery means the broker acks or moves on first and the consumer processes after. A crash in between loses the message for good. No duplicates, but silent loss.

At-least-once delivery means the consumer processes first and acks after. A crash in between means the broker never heard the ack, so it redelivers, and the work runs again. No loss, but duplicates.

Exactly-once delivery is the thing people wish for: every message takes effect once, no loss and no duplicate, with no extra work on your side. As a delivery guarantee across a network it is not achievable. As an effect it is, and that is the day.

A redelivery is the broker handing out a message again because it never got the ack. The consumer cannot tell a redelivery apart from a first delivery unless you give it a way to.

An idempotent operation is one you can run many times and the result is the same as running it once. "Set the balance to 500" is idempotent. "Add 500 to the balance" is not, and that difference is the whole problem.

An idempotency key is a unique id carried on the message so the consumer can recognise a redelivery and skip the work it already did. The key is how you turn a non-idempotent effect (a charge) into one that is safe to retry.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Message Delivery Semantics](https://kafka.apache.org/documentation/#semantics), the Kafka design docs. Short, primary-source, and it lays out at-most-once, at-least-once and exactly-once in plain terms, with the honest caveat about what exactly-once can and cannot mean. Start here.
- [Exactly-Once Semantics Are Possible: Here's How Kafka Does It](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/) on the Confluent blog. The nuance from the people who sell it. Read it for where the "possible" has fine print: inside a closed Kafka-to-Kafka loop with transactions, not for the side effects your consumer has on the outside world.
- [Implementing Stripe-like Idempotency Keys](https://brandur.org/idempotency-keys) by Brandur Leach. The best practical walk-through of how a payments API actually makes a retry safe, with the key, the stored result, and the transaction that ties them together. This is the pattern behind today's lab.

Optional, if you want the operator's view: [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) in the AWS Builders' Library.

Watch, after the lab:
- [How Kafka Actually Achieves Exactly-Once Semantics](https://www.youtube.com/watch?v=iRhDCIzhm4A) by Arpit Bhayani, about 18 minutes. Exactly today's topic, with the producer idempotence and transaction pieces drawn out carefully.
- [Designing Idempotent API Endpoints for Payments at Stripe](https://www.youtube.com/watch?v=J2IcD9FZvZU) by Arpit Bhayani, about 14 minutes. The request-side version of the lab: the key, the dedupe, and why the client mints the key.

### The three delivery semantics, and which failure each one buys (16 min)

Picture a consumer pulling one message off a queue. It has two jobs to do: the work (post a charge to a ledger, send an email, update a row) and the ack (tell the broker it is done). The entire theory of delivery semantics is just the question of which of these two you do first.

If you ack first and then do the work, you have chosen at-most-once. Think about what a crash does here. The broker has already been told the message is done, so it has forgotten the message. If your worker dies after the ack but before the work, the message is gone. Nobody will ever redeliver it, because as far as the broker is concerned it was handled. You never get a duplicate, and you sometimes get silent loss. That is a fine trade for a metrics ping or a "user is typing" event, where one missed item costs nothing. It is a terrible trade for a payment.

If you do the work first and then ack, you have chosen at-least-once. Now a crash after the work but before the ack means the broker never heard "done". So, correctly and stubbornly, it hands the message out again. Your worker comes back, processes the same message a second time, and finally acks. No message is ever lost. But the work ran twice. For a charge, that is a double deduction. For an email, a second copy in the inbox. This is the default in almost every real broker (SQS, RabbitMQ, Kafka consumers) because loss is usually scarier than duplication, and duplication is something you can defend against.

Exactly-once delivery is the wish that neither happens: the work runs once, no loss and no duplicate, and you do nothing special. Across a network with crashes, that is not a thing you can buy. The next section is why.

### Why exactly-once delivery is a lie: the two-step problem (14 min)

Here is the heart of it. The work and the ack are two separate operations in two separate systems. The work is a write to your database or a call to a payment gateway. The ack is a message to the broker. There is no single transaction that spans both, because they do not share a transaction manager. One is in Postgres, the other is in Kafka or SQS. They cannot commit together.

So whatever order you pick, there is a moment in between, and a crash can land exactly in that moment. Process-then-ack can crash after the charge posts but before the ack is sent, and the redelivery charges again. Ack-then-process can crash after the ack but before the charge posts, and the charge never happens. You are not choosing whether to have a gap. The gap is always there. You are only choosing which side of it to be wrong on: duplicate, or loss.

That is why "exactly-once delivery" cannot be promised. To deliver exactly once, the broker would need to know, with certainty, whether the work finished, and the only signal it has is the ack, which can itself be lost on the way back. The broker genuinely cannot tell "the consumer did the work and the ack got lost" apart from "the consumer never did the work". Faced with that ambiguity, it must either assume done (risk loss) or assume not-done (risk duplicate). There is no third option.

So the honest systems do not sell you exactly-once delivery. They give you at-least-once delivery, which guarantees no loss, and then they hand you the responsibility for the duplicates. Which brings us to the fix.

### Idempotency keys: exactly-once effect on top of at-least-once (12 min)

If duplicates are unavoidable, make them harmless. That is the whole idea. Give every message a unique id, an idempotency key, that is stable across retries. Before the consumer does the work, it checks whether it has already applied that id. If it has, the message is a redelivery, so it skips the work and just acks. If it has not, it does the work and records the id. A redelivered message now changes nothing. The delivery is still at-least-once. The effect is exactly-once.

Two details decide whether this actually works. The first is who makes the key and when. The client has to mint it once, before the first attempt, and reuse the same key on every retry of that same intent. If the key is a fresh random value on each try, or a server timestamp, then the retry looks like a brand-new request and you are back to double charging. This is why your UPI app generates a transaction reference the moment you tap Pay, and sends the same one when you tap again after a "failed" screen.

The second detail is where the "I have already applied this id" record lives. It has to be written in the same atomic commit as the effect. If you charge the card and record the key in one transaction, a crash does both or neither, and a redelivery safely sees the key and stops. If you record the key separately from the effect, you have just recreated the two-step problem one level down, and a crash in the new gap either double-applies or skips forever. In the lab the store is in memory and the effect is in memory, so they move together for free. In production they must share a transaction, and when the effect and the record genuinely cannot be in one transaction (the effect is a DB write, the record is a publish to a queue), that is the dual-write problem, and its fix is the outbox pattern, which is tomorrow.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-25-drills.md`](../notes/day-25-drills.md).

D1. Name the three delivery semantics: at-most-once, at-least-once, exactly-once. For each, say whether it risks loss or duplicates, and which order of the two steps, process and ack, produces it.

D2. A consumer must do two things on a message: apply the effect and ack it. Explain in two or three sentences why you cannot make those one atomic step across a network, and what that means for the phrase "exactly-once delivery".

D3. You add an idempotency key per message so a redelivery is a no-op. Where must the "I have already applied this id" record live for the dedupe to survive the consumer crashing right after it applies the effect? What breaks if that record and the effect are written separately?

D4. A payment request is "charge this card 500 rupees for order 123". Who should generate the idempotency key and when, the client before the first attempt or the server on each request? Give one good key and one bad key, and say why the bad one fails to stop a double charge.

D5. A broker delivers 5000 messages, and 8 percent of deliveries crash after processing but before the ack, each losing its ack exactly once. How many total deliveries does the consumer handle, how many duplicate effects land without an idempotency key, and how many effects are actually applied with one?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-25-delivery/idempotency.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-25-delivery/idempotency.py).

It is in three parts. A toy broker hands 1000 payments to a single consumer over a real queue. A deterministic sprinkling of deliveries crash after the work but before the ack, so the broker redelivers them. Part 1 processes then acks with no dedupe and counts the duplicate charges. Part 2 keeps the exact same crashes and redeliveries but adds an idempotency key per message and shows the duplicates drop to zero. Part 3 flips to ack-first and shows the other failure, lost charges, so you feel why neither order is "exactly-once" and why idempotency is the real fix.

Standard library only, queue plus threading, no files to clean up, and it runs in well under a second.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. At-least-once, no idempotency. 1000 payments, each a 100-rupee charge, about 10 percent of deliveries crash after the charge but before the ack. How many duplicate charges end up in the ledger?
- P2. Same messages, same crashes, same redeliveries, but each message carries a unique id and the consumer skips any id it has already applied. How many duplicate charges now?
- P3. Flip to ack-before-processing (at-most-once). A crash after the ack now loses the message. How many charges are lost (never posted at all)?
- P4. Back to at-least-once. Counting the first delivery plus every redelivery, how many total deliveries did the consumer handle for 1000 messages?

P1 and P2 are the pair to feel in your gut. Write both down. The point of the day is that P1 is a real, ugly number and P2 is exactly zero, for the same crashes.

### Fill in the TODOs

1. TODO 1 is the at-least-once charge decision: process on every delivery. This is the one line that makes a redelivery charge the card a second time.
2. TODO 2 is the idempotency-key check: have we already applied this id? One lookup turns N charges into 1.
3. TODO 3 is the at-most-once loss: because we acked first, a crash takes the message and the broker never brings it back.
4. TODO 4 is the headline number: how many charges landed beyond the one-per-message that was correct.

```bash
cd labs/day-25-delivery
python3 idempotency.py
```

### What you're going to discover

Part 1 is the ugly truth. The same 1000 payments, a handful of crashes, and the ledger comes out over 100,000 because 107 charges were posted twice. Nothing was lost. The system did its job, stubbornly, and that is exactly why you got duplicates. At-least-once means duplicates are not an edge case, they are Tuesday.

Part 2 is the relief, and the surprise is how little changed. The broker redelivered just as often, 1107 total deliveries either way. The only difference is one lookup against a set of ids before charging. That single check takes the ledger to exactly 100,000. Delivery stayed at-least-once; the effect became exactly-once.

Part 3 is the honesty. Ack first and the duplicates vanish, but now 97 charges are silently lost and the ledger is under 100,000. Put the three side by side and the lesson is undeniable: process-first duplicates, ack-first loses, and you cannot have neither by reordering. You get there with at-least-once plus Part 2's key.

### Traps ⚠️

- The duplicate count is deterministic here on purpose (a seeded crash plan), so you get the same 107 every run and can reason about it. A real queue's duplicates are random in count and timing. Do not read the exact 107 as a law; read the fact that it is clearly above zero as the law.
- The idempotency set in the lab lives in memory and survives the simulated crash, because the "crash" is just a lost ack, not a wiped process. In production the dedupe record must be durable and must commit with the effect. If you store it separately, you have moved the bug, not fixed it. That is Day 26.
- Part 3 loses messages quietly. That is the scary part of at-most-once: there is no error, no retry, no trace. The ledger is just wrong and nothing shouts. Duplicates at least announce themselves.

### Deliverable

[`labs/day-25-delivery/RESULTS.md`](../labs/day-25-delivery/RESULTS.md) has a skeleton. Paste the output, and write one line: how many duplicate charges without the key, how many with it, and why the same crashes produced such different ledgers.

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise: "I charged a fake card 1000 times and crashed the worker on purpose. Process-then-ack gave me 107 duplicate charges. Ack-first lost 97. One idempotency key took the duplicates to exactly zero, same crashes. That is why exactly-once delivery is a myth and exactly-once effect is not." The three-way scoreboard is the screenshot.

Example posts are on the [Day 25 posts](../shares/day-25-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the duplicate count you measured without the key versus with it, and one thing you still cannot explain.

Day 26 is the outbox pattern and the dual-write problem: what goes wrong when the effect lives in your database and the message lives in a queue, and you try to write to both. Today you saw that the idempotency record must commit with the effect. Tomorrow you handle the case where it cannot, which is the single most common way real systems lose or duplicate data.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. At-most-once: ack first, then process. A crash in the gap loses the message and it is never redelivered. Risk is loss, never duplicates. Fine for metrics or presence pings. At-least-once: process first, then ack. A crash in the gap means the broker never heard the ack, so it redelivers and the work runs again. Risk is duplicates, never loss. This is the default in SQS, RabbitMQ and Kafka consumers. Exactly-once: the message takes effect once, no loss and no duplicate, with no work on your side. As a delivery guarantee across a network it is not achievable; as an effect it is, via at-least-once plus idempotency.

D2. The effect (a DB write, a card charge) and the ack (a message to the broker) live in two different systems that do not share a transaction, so there is no single commit that covers both. Whatever order you pick, a crash can land between them: process-then-ack can die after the effect but before the ack and get redelivered, ack-then-process can die after the ack but before the effect and lose it. The gap is always there, so "exactly-once delivery" would require closing a window you cannot close over an unreliable network. The honest framing is at-least-once delivery plus idempotent processing.

D3. The dedupe record must be written in the same atomic commit as the effect. If "applied id 123" and "balance += 500" commit together, a crash does both or neither, and a redelivery sees the id and safely skips. If they are written separately, you recreate the two-step problem one level down: apply the effect and crash before recording the id (redelivery double-applies), or record the id and crash before the effect (the real work is skipped forever). When the effect and the record cannot share a transaction, that is the dual-write problem and the fix is the outbox pattern (Day 26).

D4. The client generates the key once, before the first attempt, and sends the same key on every retry of that intent. A good key is a stable id tied to the intent: a client-minted UUID created when the user taps Pay, or something like "order-123-charge". A bad key is anything that changes per request, such as a fresh random value the server mints on each call, or a timestamp. If the key changes on the retry, the server sees a new request and charges again, which is the double charge you were trying to prevent. The key must be stable across retries and unique across distinct intents.

D5. 8 percent of 5000 is 400 deliveries that crash once, so 400 redeliveries. Total deliveries are 5000 + 400 = 5400. Without a key, process-then-ack applies the effect on every delivery, so duplicates are 400 and 5400 effects land where 5000 should. With a key, the 400 redeliveries are no-ops, so exactly 5000 effects are applied, the correct number, even though the broker still delivered 5400 times.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-25-delivery/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-25-delivery/solution.py).

TODO 1, at-least-once processes on every delivery, which is what makes a redelivery charge twice:

```python
should_charge = True
```

TODO 2, the idempotency-key check, one lookup that turns N charges into 1:

```python
already_applied = msg.id in seen
```

TODO 3, at-most-once loses a message because we acked before processing:

```python
lost = broker.crash_counts[msg.id] >= 1
```

TODO 4, the headline number, charges posted beyond the correct one-per-message:

```python
extra = applications - n_messages
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 1000 payments.

```
==============================================================================
Part 1: at-least-once. Process, then ack. A crash before the ack means
        the broker redelivers, and the charge is posted twice.
==============================================================================
  messages sent:                     1000
  deliveries handled (with retries): 1107
  charges posted to the ledger:      1107
  duplicate charges:                 107
  ledger balance:                    110,700  (correct is 100,000)
  overcharged by:                    10,700 rupees
  Every redelivery ran the charge again, because the handler posts the
  charge on every delivery. At-least-once delivery means duplicates are
  not an edge case, they are the normal case under crashes and retries.

==============================================================================
Part 2: idempotency keys. Same crashes, same redeliveries, but each id
        is applied at most once. The redelivered charge is a no-op.
==============================================================================
  messages sent:                     1000
  deliveries handled (with retries): 1107
  charges posted to the ledger:      1000
  duplicate charges:                 0
  ledger balance:                    100,000  (correct is 100,000)
  distinct ids remembered:           1000
  The broker still redelivered exactly as often as in Part 1. The only
  change is the consumer checked an id against a set before charging.
  Delivery is still at-least-once. The EFFECT is now exactly-once.

==============================================================================
Part 3: why exactly-once DELIVERY is a lie. Ack BEFORE processing, and
        a crash loses the message instead of duplicating it.
==============================================================================
  messages sent:                     1000
  deliveries handled (no retries):   1000
  charges posted to the ledger:      903
  lost charges (never posted):       97
  ledger balance:                    90,300  (correct is 100,000)
  undercharged by:                   9,700 rupees
  Acking first means a crash takes the message with it, and because the
  broker was told the message was done, it never comes back. That is
  at-most-once: no duplicates, but silent loss. Process-first gives
  duplicates; ack-first gives loss. You cannot ack and process as one
  atomic action across a network, so one of these two is always your
  reality. The honest answer is at-least-once plus Part 2's idempotency.

==============================================================================
Scoreboard
==============================================================================
  P1 at-least-once duplicates        you =   110   actual =    107        close enough
  P2 idempotent duplicates           you =     0   actual =      0        close enough
  P3 at-most-once lost               you =   100   actual =     97        close enough
  P4 at-least-once deliveries        you = 1,110   actual =  1,107        close enough

==============================================================================
The number to carry
==============================================================================
  Same 1000 payments, same crashes, same redeliveries.
  At-least-once, no key:   107 duplicate charges, ledger 110,700 (too high).
  At-least-once + idem key: 0 duplicates, ledger 100,000 (exactly right).
  At-most-once (ack first): 97 lost charges, ledger 90,300 (too low).
  Exactly-once delivery would mean zero duplicates AND zero loss with
  no dedupe logic. Nobody can promise that across a network. What you
  CAN have is at-least-once delivery and an idempotency key, which is
  how a UPI retry after a 'failed' screen does not charge you twice.
```

Part 1 is the day. One thousand payments, a handful of crashes placed after the charge but before the ack, and 107 of those charges got posted a second time when the broker redelivered. Nothing was lost. The ledger is 110,700 when it should be 100,000, an extra 10,700 rupees that never should have moved, and the system produced it by working correctly. That is the signature of at-least-once: it would rather charge you twice than risk charging you zero times.

Part 2 is the fix, and what I like about it is how small it is. The broker did the exact same thing, 1107 deliveries, same 107 redeliveries. The consumer just checked each message id against a set before charging and skipped the ids it had already seen. The ledger landed on 100,000 exactly. The delivery guarantee did not change at all. The effect became exactly-once because the duplicates were made into no-ops.

Part 3 is the honesty check. I acked before processing, and the duplicates disappeared, but now 97 charges were lost silently and the ledger came in under at 90,300. No error, no retry, nothing in a log. Set the three next to each other and there is no reordering that gives you neither duplicates nor loss, because the work and the ack cannot commit together. The one line to carry out of today: stop chasing exactly-once delivery, take at-least-once, and spend an idempotency key to make the retries harmless.

</details>
