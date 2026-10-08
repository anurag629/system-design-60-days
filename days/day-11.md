---
title: "Day 11: transactions and isolation"
parent: "Week 2: storage"
nav_order: 4
has_children: true
---

# Day 11
## Transactions, and why a bank balance goes wrong the moment two people touch it 💸

Today's one idea: reading a value, changing it in your code, and writing it back is three steps, not one. The instant two threads do those three steps at the same time, they step on each other and money silently disappears. A transaction is the thing that glues the three steps into one indivisible step so that cannot happen. In the lab you will watch 84% of a balance vanish, then get it all back by changing one line.

Yesterday and the day before were about how fast storage is and how it is shaped. Today is about correctness under concurrency, which is a different kind of scary. A slow query annoys you. A lost update lies to you.

---

## Before you start ⏪

You need Day 2's comfort with SQLite and basic Python, and that is about it. Today uses Python threads, but you do not need to know threading deeply. A thread is just a second worker running your code at the same time as the first. That is the whole point: two workers, one balance, and what goes wrong when they do not take turns.

If the words atomic, lock or commit are fuzzy, do not worry. We build them up from zero below.

---

## Words you will meet today 📖

A transaction is a group of reads and writes that the database treats as one unit. Either all of it happens, or none of it does, and while it runs the database keeps other transactions from seeing it half done. BEGIN starts one, COMMIT makes it permanent, ROLLBACK throws it away.

A read-modify-write is the pattern at the heart of today: read a value, change it in your application code, write it back. Innocent looking, and the source of most concurrency bugs.

A lost update is when two read-modify-writes overlap and one silently overwrites the other. Both read 100, both write 101, and one of the two increments is simply gone. The database never complained.

Atomic means all-or-nothing and indivisible. No other transaction can see a state in the middle. `UPDATE accounts SET balance = balance + 1` is atomic. The read-then-write version in your code is not.

A lock is how a database makes others wait. A write lock on a row means "I am changing this, everyone else queue up." Holding a lock across your whole read-modify-write is one way to make it safe.

Isolation is the I in ACID. It is the promise about how much one running transaction can see of another running transaction. There are levels, from weak and fast to strict and slow, and today you learn the whole ladder.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [DDIA chapter 7](https://dataintensive.net/), transactions. This is the chapter the whole day is built on. Read the opening on what a transaction is, the section on weak isolation levels, and the part called "preventing lost updates". Kleppmann names the exact bug you reproduce in the lab.
- [PostgreSQL docs: transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html). The authoritative table of which isolation level allows which anomaly. Note the honest footnote: Postgres only really has three distinct levels, and its "repeatable read" is actually snapshot isolation. Real databases bend the textbook.
- [SQLite isolation](https://www.sqlite.org/isolation.html). Short, and it is the engine your lab runs on. It explains why a reader inside a transaction sees a frozen snapshot, which is the exact behaviour of the Part 3 demo.

Watch, after the lab:
- [Transactions, ACID, and isolation levels](https://www.youtube.com/watch?v=AiYvR8yBMaU) by Ben Dicken, about an hour. A calm, careful walk through DDIA chapter 7. Long, but it is the best single explainer of everything today. Skip to the isolation levels part if you are short on time.
- [You won't forget how Postgres works after this](https://www.youtube.com/watch?v=q9jixKv4h2I) by Hussein Nasser, about 27 minutes. How a real engine actually runs a hundred transactions at once using MVCC, keeping multiple versions of a row so readers never block writers. This is the machinery under the isolation levels.

### Three steps that should have been one (20 min)

Picture an IRCTC tatkal window the second it opens. One seat is left. Two people hit book at the same instant. Both their requests read "1 seat available", both decide "yes, book it", both write "0 seats, booked". Two bookings, one seat. Someone is standing in the aisle tonight.

That is a lost update, and it is the same shape as a bank balance, a like counter, a stock quantity, a retry counter. The pattern is always:

```
read the current value
change it in your code
write the new value back
```

On one worker this is perfectly fine. The trouble starts with two. Say the balance is 400. Worker A reads 400. Before A writes 401, worker B also reads 400. A writes 401. B writes 401. Two deposits happened. The balance went up by one. One deposit vanished, and nobody got an error. The money is just wrong now.

Here is the part that makes it genuinely dangerous. It is invisible when you test. You run it once, by yourself, and it works. It passes code review. It ships. Then one busy evening, when enough requests land on the same row at the same time, the numbers quietly drift. No crash, no log line, no stack trace. Just a balance that does not add up and a very confused on-call engineer. Wrong data is a worse bug than a crash, because a crash at least tells you.

Why does it happen? Because the read and the write are two separate trips to the database with a gap in between, and in that gap anyone can change the value under you. The value you are about to write is based on a number that is already stale.

### The fix is a transaction (15 min)

There are two honest fixes, and they are the same idea wearing two outfits.

Fix one, do the whole thing in a single statement and let the database compute the new value:

```sql
UPDATE accounts SET balance = balance + 1 WHERE id = 1
```

This reads and writes inside one statement that the engine runs atomically. It takes the lock, reads the current value, adds one, writes it, and only then lets go. There is no gap for another worker to sneak into. This is the "one line different" fix, and it is the right default whenever you can express the change as arithmetic on the existing value.

Fix two, for when there is logic in the middle that SQL cannot do alone (check the balance is enough, then debit two different accounts), wrap the read-modify-write in a real transaction that grabs the write lock up front:

```sql
BEGIN IMMEDIATE;
  SELECT balance FROM accounts WHERE id = 1;   -- read
  -- ... your check and logic in code ...
  UPDATE accounts SET balance = ? WHERE id = 1; -- write
COMMIT;
```

BEGIN IMMEDIATE is the important word. It takes the write lock the moment the transaction starts, so from the first read to the final commit, no other writer can touch the row. The three steps are now one indivisible step. (If you used a plain BEGIN that only takes a read lock, two transactions could both read, then both try to upgrade to a write, and deadlock. IMMEDIATE avoids that by claiming the lock early. Keep that in your pocket, it is a real interview answer.)

Both fixes give exactly the right answer. In the lab you will see the naive version lose about 13,000 updates and both fixes lose exactly zero.

### The four anomalies and the isolation ladder (15 min)

The lost update is one member of a small family of things that can go wrong when transactions overlap. The classic four, worst to least nasty:

- Dirty read: you read another transaction's uncommitted change, and then it rolls back. You acted on a number that never officially existed.
- Non-repeatable read: you read a row twice inside one transaction and get two different values, because someone committed a change in between.
- Phantom read: you run the same WHERE clause twice and new rows appear the second time, because someone inserted rows that match.
- Lost update: the one from today. Two read-modify-writes clobber each other.

Isolation levels are the dial that decides which of these the database will let through. Weaker is faster and lets more slip. Stricter is slower and forbids more. The textbook ladder:

| anomaly | read uncommitted | read committed | repeatable read | serializable |
|---|---|---|---|---|
| dirty read | can happen | safe | safe | safe |
| non-repeatable read | can happen | can happen | safe | safe |
| phantom read | can happen | can happen | can happen | safe |
| lost update | can happen | can happen | safe | safe |

Serializable is the top of the ladder. It promises the result will be exactly as if every transaction ran one after another, alone, with nobody else around. It forbids all four anomalies. It is also the costliest, because to deliver that promise the database must either make conflicting transactions wait in line (locking) or let them run and abort the losers to retry (optimistic). You pay in throughput and in retries. You felt this in the lab: the BEGIN IMMEDIATE version was correct but about 14 times slower than the one-line fix, because every worker had to wait its turn for the lock.

Most real systems do not run at serializable. Postgres defaults to read committed, and its "repeatable read" is really snapshot isolation (each transaction sees a frozen photo of the database from when it began, which is how a hundred people read and write at once without holding hands). The practical skill is knowing which anomalies your default level still allows, and reaching for a stronger level or an explicit lock on the specific operations where correctness actually matters, like money.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-11-drills.md`](../notes/day-11-drills.md).

D1. Two sessions both read a balance of 100, both add 10 in their code, both write the result back. What is the final balance? What should it be? How much was lost, and in one sentence, why?

D2. Name the anomaly for each: you read a row twice in one transaction and get two different values; you read data that then gets rolled back; the same WHERE returns new rows the second time; two read-modify-writes clobber each other.

D3. Under READ COMMITTED, which of the four anomalies (dirty read, non-repeatable read, phantom, lost update) can still happen? Under SERIALIZABLE, which can happen?

D4. You want to deduct 100 from a balance. Compare `UPDATE accounts SET balance = balance - 100 WHERE id = 1` against reading the balance into your code and then updating. Which is safe under concurrency and why? Give one case where a single statement is not enough and you still need an explicit BEGIN...COMMIT.

D5. Serializable is the safest level. Name two costs you pay for it, and one mechanism a database uses to provide it. Tie your answer to the slowdown you measured in the lab.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-11-transactions/transactions.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-11-transactions/transactions.py).

It opens one shared SQLite file with a single account, then points 8 threads at that one balance. Part 1 runs the naive read-modify-write and watches the money vanish. Part 2 runs two fixes and watches the loss go to exactly zero. Part 3 prints the anomaly ladder and shows a real non-repeatable read happening in front of you, then shows a snapshot read making it disappear.

Standard library only, about 5 seconds to run.

### Predict first

Fill in `PREDICTIONS` at the top. Eight threads each add 1 to the balance 2,000 times, so the correct final balance is 16,000.

- P1. In the naive version (read, add 1 in code, write back), what does the balance actually end at?
- P2. So how many increments are lost, which is 16,000 minus P1?
- P3. With the one-line atomic fix, how many are lost?
- P4. With the same read-modify-write wrapped in BEGIN IMMEDIATE, how many are lost?

P3 and P4 are easy to guess once you understand the idea. The point is to commit to "zero" out loud before you see it. P1 is the one to feel: guess how bad it gets before you look.

### Fill in the TODOs

1. TODO 1 is the naive read-modify-write: SELECT the balance into Python, a tiny pause, then UPDATE to balance plus one. This is the bug, written on purpose.
2. TODO 2 is the one-line fix: `UPDATE accounts SET balance = balance + 1`.
3. TODO 3 is the same read-modify-write as TODO 1, but wrapped in `BEGIN IMMEDIATE ... COMMIT`.
4. TODO 4 is the lost-updates count: the correct total minus the actual final balance.

```bash
cd labs/day-11-transactions
python3 transactions.py
```

### What you're going to discover

Part 1 is the gut punch. On the reference machine, 8 threads doing 16,000 increments between them left the balance at about 2,561. Roughly 13,400 increments, 84% of them, were lost. No error was raised. The database did exactly what you told it: a pile of separate reads and writes that trampled each other.

Part 2 is the relief. Change the one line to `balance = balance + 1` and the balance lands on 16,000, dead on, zero lost. Wrap the naive version in BEGIN IMMEDIATE and it is also exactly 16,000. Same 8 threads, same 16,000 operations. The only thing that changed is that the read and the write became one indivisible step.

Part 2 also sneaks in the cost of safety: the BEGIN IMMEDIATE version was correct but about 14 times slower than the one-line fix, because every thread had to wait for the lock. That slowdown is not a bug, it is what strict isolation costs.

### Traps ⚠️

- If your naive version does not lose much, your two statements are probably ending up inside one automatic transaction. The lab opens connections with `isolation_level=None` (autocommit) on purpose, so each statement commits on its own and the gap between read and write is real. Keep that.
- Do not reach for a plain `BEGIN` in TODO 3. Two threads that both take a read lock and then both try to upgrade to a write lock will deadlock, and SQLite will raise "database is locked". `BEGIN IMMEDIATE` takes the write lock up front and sidesteps the whole problem.
- The exact lost number wobbles run to run, because it depends on timing. That is fine and honest. What never wobbles is that the naive version loses a lot and both fixes lose zero.

### Deliverable

[`labs/day-11-transactions/RESULTS.md`](../labs/day-11-transactions/RESULTS.md) has a skeleton. Paste the output, and write one line: in the naive version, how many updates were lost, and why did they vanish?

---

## Block 4: write (30 min) 📣

Your angle today is the invisible bug: "I corrupted a bank balance on purpose with 8 threads, watched 84% of the money vanish with no error at all, then fixed it by changing one line." The scoreboard, thousands lost then exactly zero, is a great screenshot.

Example posts are on the [Day 11 posts](../shares/day-11-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the number of lost updates you measured in the naive version, and one thing you still cannot explain.

Day 12 is replication: one leader, many followers, and the small lie in the middle called replication lag. Today you saw what it costs to keep one copy of the data correct under concurrency. Tomorrow you keep several copies, on several machines, and meet the new problem that a follower can be a few seconds behind the leader, which is why you sometimes post a comment, refresh, and it is gone for two seconds.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Final balance 110, correct balance 120, lost 10. Both sessions read the same 100, both computed 110, both wrote 110, so one of the two +10 increments was overwritten. The read and the write were separate steps with a gap in between, and in that gap the other session read the same stale 100.

D2. Read a row twice and get two values: non-repeatable read. Read data that then rolls back: dirty read. Same WHERE returns new rows: phantom read. Two read-modify-writes clobber each other: lost update.

D3. Under READ COMMITTED, dirty reads are prevented, but non-repeatable reads, phantoms, and lost updates can all still happen. Under SERIALIZABLE, none of the four can happen, because the result is guaranteed to match some one-at-a-time ordering of the transactions.

D4. `UPDATE accounts SET balance = balance - 100 WHERE id = 1` is safe, because the read and the write are one atomic statement and the engine holds the lock across both. Reading the balance into your code and then updating is not safe: another writer can change the balance in the gap, and you overwrite them. You still need an explicit BEGIN...COMMIT when the operation spans more than one statement or row and must be all-or-nothing, for example moving money between two accounts (debit one, credit the other) where both must happen together or neither, and where you also want to check the first account has enough before you touch the second.

D5. Two costs: lower throughput, because conflicting transactions must effectively run one at a time instead of in parallel; and, on optimistic implementations, wasted work and retries, because transactions that conflict are aborted and must run again. One mechanism: strict two-phase locking (hold locks until commit so conflicting transactions wait), or serializable snapshot isolation (let them run optimistically and abort the ones that would have conflicted). In the lab, the BEGIN IMMEDIATE version was correct but about 14x slower than the one-line fix, because every thread waited its turn for the write lock. That wait is exactly what you pay for strong isolation.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-11-transactions/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-11-transactions/solution.py).

TODO 1, the naive read-modify-write (the bug):

```python
bal = conn.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
time.sleep(THINK)  # the gap another thread sneaks into
conn.execute("UPDATE accounts SET balance = ? WHERE id = 1", (bal + 1,))
```

TODO 2, the one-line atomic fix:

```python
conn.execute("UPDATE accounts SET balance = balance + 1 WHERE id = 1")
```

TODO 3, the same read-modify-write wrapped in a transaction:

```python
conn.execute("BEGIN IMMEDIATE")
bal = conn.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0]
time.sleep(THINK)
conn.execute("UPDATE accounts SET balance = ? WHERE id = 1", (bal + 1,))
conn.execute("COMMIT")
```

TODO 4, the lost-updates count:

```python
return expected - final
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, 8 threads, 2,000 increments each.

```
==============================================================================
Part 1: the naive read-modify-write. Watch the money vanish.
==============================================================================
  8 threads x 2,000 increments each, starting from 0
  correct final balance:  16,000
  actual final balance:   2,561
  lost updates:           13,439  (84.0% of the money, gone)
  (took 1.43s)

==============================================================================
Part 2: the fix is a transaction. Same threads, same work, zero lost.
==============================================================================
  Fix A, one line different: UPDATE accounts SET balance = balance + 1
    final balance:  16,000   lost: 0   (0.18s)
  Fix B, the SAME read-modify-write wrapped in BEGIN IMMEDIATE ... COMMIT:
    final balance:  16,000   lost: 0   (2.51s)
    It ran about 14x the one-line fix, because every thread now
    waits its turn for the lock.

==============================================================================
Part 3: the isolation anomalies, and the one you can watch happen.
==============================================================================
    anomaly              read uncommitted  read committed  repeatable read  serializable
    dirty read           can happen        safe            safe             safe
    non-repeatable read  can happen        can happen      safe             safe
    phantom read         can happen        can happen      can happen       safe
    lost update          can happen        can happen      safe             safe

  Live demo, a reader in autocommit (read-committed style):
    read balance -> 1000,  a writer commits 1500,  read again -> 1500
    the same query gave two answers in a row. That is a non-repeatable read.
  Same thing, but the reader is inside one transaction (snapshot):
    read -> 1000,  a writer commits 1500,  read again -> 1000,  after commit -> 1500
    inside the transaction the value held steady. The anomaly is gone.

==============================================================================
Scoreboard
==============================================================================
  P1 naive final balance       you =  2,200.0   actual =   2,561.0        close enough
  P2 naive lost updates        you = 13,800.0   actual =  13,439.0        close enough
  P3 atomic fix lost           you =      0.0   actual =       0.0        spot on
  P4 transaction fix lost      you =      0.0   actual =       0.0        spot on

==============================================================================
The number to carry
==============================================================================
  Naive read-modify-write:  13,439 lost updates. Corrupted money.
  Atomic UPDATE + 1:        0 lost. Correct.
  BEGIN IMMEDIATE wrap:     0 lost. Correct.
```

Part 1: the balance should have hit 16,000 and instead landed at 2,561. About 13,400 increments were overwritten by other threads, and not one error was raised. This is the whole lesson in one number. Correctness under concurrency is not free and not automatic.

Part 2: the one-line atomic fix and the BEGIN IMMEDIATE wrap both land on exactly 16,000. The only change was making the read and the write one indivisible step. Notice Fix B was about 14x slower: that is the cost of holding a lock across the whole operation so everyone takes turns.

Part 3: the live demo shows a non-repeatable read for real. The same SELECT returns 1000, then 1500, because a writer committed in between and the reader was in autocommit. Put the reader inside a single transaction and it sees a frozen 1000 throughout, then the new 1500 only after it commits. That frozen snapshot is how a database gives you repeatable reads without blocking the writer, and it is the machinery behind every isolation level above read committed.

</details>
