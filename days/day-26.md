---
title: "Day 26: the outbox pattern"
parent: "Week 4: async, queues and the log"
nav_order: 5
has_children: true
---

# Day 26
## The dual write, and why your database and your queue drift apart 📨

Today's one idea: the moment you write the same fact to two places that do not share a transaction, your database and your queue, you have a gap. One write succeeds, the other does not, and now the two systems disagree about what happened. The order is saved but the email never goes out. The fix is not a smarter retry or a bigger timeout. The fix is to stop doing two writes. You write the event into your own database, in the same transaction as the business row, and let a separate relay carry it to the queue later. That is the outbox pattern, and once you have seen the gap with your own eyes, you will spot this bug in half the systems you review.

All week you have been handing work to a queue and trusting it to happen later. Today is the uncomfortable question underneath that trust: how does the work actually get into the queue in the first place, and what happens if that step fails after you have already told the customer "done"?

---

## Before you start ⏪

You need two things from earlier in the week fresh in your head. Day 25 is the big one: at-least-once, at-most-once, and the idempotency key that stops a repeated message from charging you twice. Today ends exactly there, so if Day 25 is foggy, skim your own notes first. You also want the week 3 fan-out in mind, the one event that triggers a dozen downstream jobs, because that is what silently never happens when an event goes missing today.

Day 2's comfort with SQLite is all the Python you need. The lab is standard library only, sqlite3 as the database and a plain Python list as the queue, and it runs in about two seconds.

This is a teaching day with a sharp, measurable lab. Day 27 is backpressure, what happens when the consumer cannot keep up and the queue starts to grow. Today is about getting the event into the queue correctly in the first place. Tomorrow is about what happens when there are too many of them.

---

## Words you will meet today 📖

A dual write is when you write one logical change to two different systems in two separate steps, for example you INSERT an order into your database and then publish an "order placed" event to Kafka. Two writes, two systems, no shared transaction between them.

The dual-write problem is the inconsistency you get when one of those two writes succeeds and the other does not. The order is committed but the event is lost, or the event goes out for an order that was never saved. There is no happy ordering, as you will see.

An outbox, or outbox table, is an ordinary table in your own database where you record the events you intend to publish. The trick is that you write the outbox row in the same transaction as the business change, so the two can never disagree.

A relay, also called a message relay or dispatcher, is a separate process that reads unsent outbox rows, publishes each one to the real queue or broker, and marks it sent. It is the only thing that talks to the queue, and it can crash and restart safely.

At-least-once is a delivery guarantee: a message arrives one or more times, never zero. The outbox relay gives you exactly this, which is the honest best a relay can promise.

Change data capture, CDC, is a fancier relay that tails the database's write-ahead log instead of polling a table. Debezium is the well-known one. Same idea, different plumbing, and we will name it today without building it.

An idempotency key, from Day 25, is a stable identifier on each event that lets a consumer recognise a repeat and act on it only once. The outbox hands you duplicates, and this is what cleans them up.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [The Dual-Write Problem](https://www.confluent.io/blog/dual-write-problem/) on the Confluent blog. The clearest plain statement of the problem and why the obvious fixes (retry the publish, use a distributed transaction) do not actually save you. Start here.
- [Pattern: Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html) by Chris Richardson on microservices.io. The canonical write-up of the solution, with the relay and the two ways to build it (polling versus tailing the log). Short and precise.
- [Reliable Microservices Data Exchange With the Outbox Pattern](https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/) on the Debezium blog. A real, production-grade version where the relay tails the write-ahead log instead of polling. Read it for the shape, not the Java.

Watch, before or after the lab:
- [What is the Dual Write Problem?](https://www.youtube.com/watch?v=FpLXCBr7ucA) by Confluent, about 6 minutes. Sets up exactly what Part 1 reproduces.
- [What is the Transactional Outbox Pattern?](https://www.youtube.com/watch?v=5YLpjPmsPCA) by Confluent, about 5 minutes. The fix, which is Part 2. Same short course, so the two videos flow straight into each other.

### The dual write, and the gap nobody sees (14 min)

Picture the checkout for an online store. A customer taps "Place order". Your code does the obvious, honest thing:

1. INSERT the order row into the database, and commit. The order is now durable. The screen says "Order placed".
2. Publish an "order placed" event to the queue, so the email service, the inventory service and the week 3 fan-out can all do their part.

Two writes. The first goes to your database, the second goes to a completely separate system, your queue or broker. Nothing wraps the two together. And there is a gap between them, a few milliseconds where step one is done and step two has not happened yet. If the process is killed in that gap, a deploy, an out-of-memory kill, a crashed pod, the order is saved forever and the event is simply gone. Not delayed. Gone. Nothing will ever retry it, because nothing recorded that it was supposed to happen.

This is the IRCTC "paisa kat gaya, ticket nahi aaya" feeling, turned around. Your bank says the money left. IRCTC says there is no ticket. Two systems, each certain, each disagreeing with the other. The customer is caught in the middle. In our store, the database is certain the order exists, the queue has never heard of it, and the email, the stock decrement and the fan-out all silently never happen.

Now the part that trips people up. "Fine," you say, "I will just reverse the order. Publish the event first, then write the database." That does not fix it, it only moves the wound. Crash in the new gap and you have published an "order placed" event for an order that was never saved. Downstream sends a confirmation email for an order that does not exist, inventory is decremented for a sale that never happened. There is no ordering of two separate writes that is atomic. One of them is always first, and a crash right after it leaves the two systems disagreeing. That is the dual-write problem, and it is why no amount of reordering or retry logic on its own will save you.

### The outbox: make it one write (14 min)

Here is the move, and it is almost annoyingly simple once you see it. The reason the two writes can disagree is that they go to two systems. So do not write to two systems. Write both facts to one system, the one you already trust to be transactional, your database.

Alongside your orders table, you add an outbox table. When an order comes in, you open one transaction and you do two INSERTs inside it: the order row, and an outbox row holding the event you want to publish. Then you commit once. Because both rows are in the same local transaction, the database guarantees they land together or not at all. There is no gap. There is no state where the order exists but the intention to publish was never recorded. A crash before the commit loses both (and the customer sees a clean failure, which is correct). A crash after the commit keeps both. The disagreement is gone, because the two facts were never in two places.

But the event is still sitting in your database, not in the queue. Something has to carry it across. That something is the relay, a separate process that does nothing but loop: read the outbox rows that are not yet marked sent, publish each one to the real queue, and mark it sent. The relay is where the risky "talk to another system" step now lives, and the beauty is that the relay can crash as often as it likes. If it dies before publishing a row, the row is still unsent, so the next pass picks it up. If it dies after publishing but before marking sent, the row is still unsent, so the next pass publishes it again. Either way, nothing is lost. The worst the relay can do is send something twice, and that is a problem we already know how to handle.

So the outbox turns one scary distributed write into two safe local ones: an atomic commit you trust, and a retryable relay that cannot lose anything. That is the whole pattern. In the lab you run the same crashing workload against both designs and watch the lost count go from a few hundred to exactly zero.

### At-least-once, and why you still need the idempotency key (10 min)

Notice what the relay just promised, and read it carefully. It promised that every outbox row is eventually published at least once. It did not promise exactly once. It cannot. The relay publishes to the queue and then marks the row sent, and those are, once again, two separate writes to two separate systems. If it crashes between them, the event is already in the queue but the row still looks unsent, so next pass it goes out a second time. This is not a bug you can code away. It is the same wall Day 25 ran into: exactly-once delivery is mostly a comforting story, and at-least-once is the honest guarantee.

Which is exactly why the two ideas, the outbox and the idempotency key, are partners, not rivals. The outbox answers "did the event get out at all", and the answer is now always yes. The idempotency key answers "did it get out twice", and lets the consumer shrug off the repeat. Each event carries a stable key (the outbox row id works perfectly), the consumer remembers the keys it has already handled, and a duplicate is recognised and dropped. It is the UPI reflex: the payment says "failed", you tap again, and the backend sees the same reference and does not charge you twice. In the lab, the relay leaves a few hundred duplicate copies in the queue, and the idempotent consumer collapses them straight back to one action per order.

One more thing worth knowing, so you are not surprised in a real codebase. The relay I described polls the outbox table on a loop. That works and it is easy to reason about, but it adds query load and a little latency. The production-grade alternative is change data capture: a tool like Debezium tails the database's write-ahead log (the same WAL you met in week 2) and turns committed outbox rows into published events without ever running a SELECT. Same pattern, same guarantees, less polling. You do not need to build it to understand it, and today's lab deliberately builds the simple polling version so the mechanism is in your hands.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-26-drills.md`](../notes/day-26-drills.md).

D1. You write the order to the database and publish an event to the queue as two steps. Describe the two possible orderings, database first then publish, and publish first then database, and say exactly what inconsistency a crash in the gap leaves behind for each. Then say why no reordering ever makes the pair atomic.

D2. A service takes 2,000,000 orders a day, and the publish step fails independently 0.1 percent of the time with the naive dual write. How many orders a day end up committed with no event? How many over a 30-day month? And why does nobody notice for a long time?

D3. The outbox move: explain why writing the outbox row in the same transaction as the order removes the failure window. What is the single thing that must now succeed, and what does a crash before the commit versus after the commit leave behind?

D4. The relay publishes an event and then crashes before it marks the outbox row sent. What does the next relay pass do, and what does the consumer end up seeing? Why can a relay reading an outbox never promise exactly-once on its own?

D5. A teammate says "we have the outbox now, so we can drop the idempotency keys". Correct them: what does the outbox guarantee, and what does it not? Then name one difference between a polling relay and a log-tailing relay like Debezium.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-26-outbox/outbox.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-26-outbox/outbox.py).

It is in three parts. Part 1 places 5,000 orders with the naive dual write, commit the order then publish as a second step, with the publish crashing about 20 percent of the time, and counts the orders whose event was lost. Part 2 places the same 5,000 orders with an outbox, order row and outbox row in one transaction, then runs a relay that also crashes, and shows zero lost. Part 3 counts the duplicate events the relay produced and shows the idempotency key cleaning them up.

Standard library only, sqlite3 is the database and a plain list is the queue. It is single threaded and deterministic, so the numbers come out the same every run, and it deletes the database file it makes.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The naive dual write, 5,000 orders, publish crashing about 20 percent of the time after the commit. How many orders end up in the database with no event published?
- P2. The outbox, same 5,000 orders, same crash rate, but the event is in the same transaction and a relay retries. How many orders end up with no event at all?
- P3. The relay is at-least-once: it can publish and then crash before marking the row sent, so it republishes. How many duplicate copies land in the queue?
- P4. After a consumer dedupes on the idempotency key, how many distinct orders are delivered downstream exactly once?

P2 is the one to feel in your gut before you run it. Write a number. If you believe the outbox, it is a bold, round zero.

### Fill in the TODOs

1. TODO 1 is the naive publish, the second write of the dual write. The one line that silently does not happen when the process crashes after the commit.
2. TODO 2 is the outbox INSERT, written in the same transaction as the order so the two commit atomically. This single line is the whole pattern.
3. TODO 3 is the relay marking a row sent, and it must happen after the publish, never before. Get this order wrong and you have rebuilt the original bug.
4. TODO 4 is the idempotent consumer: act on each event the first time its key is seen, skip the repeats.

```bash
cd labs/day-26-outbox
python3 outbox.py
```

### What you're going to discover

Part 1 is the gut punch. 5,000 orders, all committed, all shown to the customer as placed, and a few hundred of them have no event at all. On the reference run it was 986 lost. Nothing errored. No exception, no retry, no log line. The database is confidently wrong, and it will stay wrong until a human notices the missing emails weeks later.

Part 2 is the relief, and it is a clean zero. The relay crashed on plenty of rows, exactly as often as Part 1's publish did, but a relay crash only ever leaves an outbox row unsent, never lost, so the next pass picks it up. Every single order ends up with its event in the queue. The database and the event stream agree on all 5,000.

Part 3 is the honest footnote. That retrying relay published some events more than once, 608 duplicate copies on the reference run. That is at-least-once in the flesh. The idempotent consumer, keyed on the event, collapses those 5,608 queue entries back to exactly 5,000 actions. Outbox stopped the loss, idempotency stopped the doubles.

### Traps ⚠️

- In Part 2, the order of the two relay steps is the entire lesson. Publish, then mark sent. If you mark sent first and then crash, you have lost the event, which is precisely the bug the outbox exists to kill. TODO 3 is written to make you do it in the safe order.
- The outbox row must go in the same transaction as the order, not in its own commit right after. Two commits is just the dual write again, wearing a table instead of a queue. One transaction, one commit, both rows.
- Do not be alarmed that the outbox did not give you exactly-once. It is not supposed to. At-least-once plus an idempotency key is the real-world shape of "exactly-once", and Part 3 is there so you feel why both halves are needed.
- The lab is deterministic on purpose (fixed seed, single thread), so your lost count and duplicate count will match the reference closely. If your Part 2 lost count is anything but zero, your TODO 2 or TODO 3 is in the wrong place.

### Deliverable

[`labs/day-26-outbox/RESULTS.md`](../labs/day-26-outbox/RESULTS.md) has a skeleton. Paste the output, and write one line: how many events did the naive dual write lose, how many did the outbox lose, and what did the idempotency key have to clean up afterwards?

---

## Block 4: write (30 min) 📣

Your angle today is the silent bug made visible: "I reproduced the most common bug in event-driven backends on my laptop. Save the order, then publish the event, two steps. Crash in between and 986 of my 5,000 orders were saved with their event lost forever, no error anywhere. The outbox pattern took that to zero." The scoreboard, 986 lost versus 0 lost, is the screenshot.

Example posts are on the [Day 26 posts](../shares/day-26-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the lost-event count you measured for the naive dual write versus the outbox, and one thing you still cannot explain.

Day 27 is backpressure. Today you made sure the event reliably gets into the queue. Tomorrow the consumer cannot keep up, the queue grows, memory fills, and you have to decide what to slow, drop or push back on. The event stream you just made trustworthy is about to get crowded.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Ordering one, database first then publish: you commit the order, then crash before publishing. The order exists, the event is lost, downstream never reacts (no email, no stock change, no fan-out). This is the silent, permanent inconsistency the lab's Part 1 counts. Ordering two, publish first then database: you publish the event, then crash before the commit. Now an "order placed" event exists for an order that was never saved, so downstream acts on a phantom, a confirmation email and a stock decrement for a sale that does not exist. Neither ordering is atomic because they are two writes to two systems with no shared transaction. One of them is always first, and a crash immediately after it leaves the two systems disagreeing. You cannot reorder your way out of it.

D2. 2,000,000 times 0.001 is 2,000 orders a day committed with no event. Over 30 days that is 60,000 orders. It stays invisible because nothing errors: the order committed fine, the customer saw "placed", and the only symptom is the absence of a downstream effect, an email that never arrived, stock that was never decremented. Absence is much harder to alert on than a failure, so these pile up quietly until a human stumbles on the pattern.

D3. Writing the outbox row in the same transaction as the order means the database commits both together or neither, atomically, so there is no longer a window where the order exists but the intention to publish does not. The single thing that must now succeed is one local transaction commit, which is exactly the kind of thing databases are built to make reliable. A crash before the commit leaves nothing (both rows roll back, the customer sees a clean failure, which is correct). A crash after the commit leaves both the order and its outbox row, so the event is guaranteed to be published eventually by the relay. The two writes to two systems have become one write to one system.

D4. The next relay pass finds the outbox row still marked unsent (the crash happened before the mark), so it publishes the event again and this time marks it sent. The consumer therefore sees that event twice. A relay can never be exactly-once on its own because publishing to the queue and marking the row sent are themselves two separate writes to two separate systems, the same dual-write shape, so a crash between them forces a choice: mark-sent-first risks losing the event, publish-first risks a duplicate. Choosing publish-first (the safe choice) is what makes it at-least-once.

D5. The teammate is half right and half dangerously wrong. The outbox guarantees that every event is published at least once, so nothing is lost, the database and the event stream never disagree about whether something happened. It does not guarantee exactly-once: the relay can republish after a crash, so duplicates are normal. The idempotency key is what lets the consumer drop those duplicates and act once. Keep both. As for the relay, a polling relay runs a SELECT on the outbox table on a loop, which is simple but adds query load and a little latency; a log-tailing relay like Debezium reads the database's write-ahead log directly and emits events as rows commit, with no polling query, at the cost of more moving parts to operate.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-26-outbox/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-26-outbox/solution.py).

TODO 1, the naive publish, the second write of the dual write:

```python
queue.append(event_for(order_id))
```

TODO 2, the outbox INSERT in the same transaction as the order, which is the whole pattern in one line (the single `conn.commit()` just below it then covers both rows):

```python
conn.execute("INSERT INTO outbox (order_id, payload) VALUES (?, ?)",
             (order_id, event_for(order_id)))
```

TODO 3, the relay marking a row sent, after the publish, never before:

```python
conn.execute("UPDATE outbox SET sent = 1 WHERE id = ?", (row_id,))
```

TODO 4, the idempotent consumer, acting on each key only the first time it is seen:

```python
if ev not in seen:
    seen.add(ev)
    processed += 1
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 5,000 orders, a 20 percent crash rate.

```
==============================================================================
Part 1: the dual write. Order to the DB, event to the queue, SEPARATELY.
==============================================================================
  orders committed to the database:   5000
  events published to the queue:      4014
  orders with a LOST event:           986
  Every one of these orders is in the database, the customer was told
  it went through, but no event was ever published. The email never
  goes out, inventory is never decremented, the fan-out never fires.
  Nothing errored, nothing retries. It is a silent, permanent lie.

==============================================================================
Part 2: the outbox. One transaction for both, a relay that retries.
==============================================================================
  orders committed to the database:   5000
  outbox rows written (same txn):     5000
  relay passes until fully drained:   7
  outbox rows still unsent:           0
  distinct orders delivered:          5000
  orders with a LOST event:           0
  The relay crashed on plenty of rows, but a crash only ever leaves
  the outbox row unsent, never lost. The next pass picks it up. So the
  database and the event stream end up agreeing on every single order.

==============================================================================
Part 3: at-least-once. The relay can publish twice, so consumers dedupe.
==============================================================================
  events sitting in the queue:        5608
  of those, duplicate copies:         608
  naive consumer, work done:          5608  (over-counts!)
  idempotent consumer, work done:     5000
  The outbox guaranteed nothing was LOST, but it hands you duplicates.
  That is at-least-once, and it is the best a relay can promise. The
  idempotency key from Day 25 turns at-least-once into effectively
  exactly-once at the consumer: each order is acted on one time.

==============================================================================
Scoreboard
==============================================================================
  P1 naive lost events               you =  1,000   actual =     986        close enough
  P2 outbox lost events              you =      0   actual =       0        close enough
  P3 outbox duplicate events         you =    700   actual =     608        close enough
  P4 idempotent distinct delivered   you =  5,000   actual =   5,000        close enough

==============================================================================
The number to carry
==============================================================================
  Same 5,000 orders, same 20% crash rate, two designs.
  Dual write:  986 orders committed with their event LOST forever,
               silently. No error, no retry, just permanent drift.
  Outbox:      0 lost. The event rides the same transaction as the
               order, and the relay retries until it is delivered.
  The relay's price is at-least-once: 608 duplicate copies in the
  queue. The Day 25 idempotency key collapses them, so all 5,000
  orders are acted on exactly once. Outbox stops loss, idempotency
  stops doubles. You need both.
```

Part 1 is the day. The same 5,000 orders all committed cleanly, the customer was told each one went through, and 986 of them have no event in the queue at all. The publish step died in the gap after the commit, and because nothing recorded that the publish was owed, nothing retries it. That is the dual-write problem: not a crash you can see, but a silent drift between two systems that both think they are right.

Part 2 is the fix, and the number is zero. The relay crashed just as often as Part 1's publish did, but a relay crash can only leave an outbox row unsent, and an unsent row is simply picked up on the next pass. The event rode in the same transaction as the order, so the two could never be separated, and the relay guaranteed the event eventually reached the queue. Seven passes to fully drain, zero rows lost.

Part 3 is the catch you must respect. Making the relay never lose anything means letting it occasionally send the same thing twice, 608 duplicate copies here. A consumer that trusts the stream blindly would do 5,608 units of work, over-counting every duplicate as a second email or a repeated charge. The idempotent consumer, keyed on the event, does exactly 5,000. That is the shape of real exactly-once: at-least-once delivery plus idempotent consumers.

The one line to carry out of today: the outbox makes sure the event gets out at all, and the idempotency key makes sure acting on it twice does no harm. Neither one replaces the other, and a serious event-driven system runs both.

</details>
