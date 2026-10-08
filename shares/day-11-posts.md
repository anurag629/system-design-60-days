---
title: "Day 11 posts"
parent: "Day 11: transactions and isolation"
grand_parent: "Week 2: storage"
nav_order: 3
---

# Day 11 posts: LinkedIn and X

The scoreboard (thousands of lost updates, then exactly zero) makes a good screenshot. Swap in your own numbers and voice.

## LinkedIn

Day 11 of 60 days of system design. Today I corrupted a bank balance on purpose, then fixed it by changing one line.

The setup: one account starting at 0, and 8 threads each adding 1 to it, 2,000 times. If nothing goes wrong the balance should end at 16,000. Simple counter.

The naive way, the way everyone writes it the first time:

    read the balance into a variable
    add 1
    write the new value back

Run that with 8 threads and the balance ended at about 2,500. Roughly 13,500 increments just vanished. 84% of the money, gone.

Here is why. The read and the write are two separate steps. Thread A reads 400. Before it writes 401, thread B also reads 400. Both write 401. Two increments happened, the balance went up by one. That is a lost update, and at scale almost every increment loses its race.

The fix is a transaction, and it is genuinely one line:

    UPDATE accounts SET balance = balance + 1 WHERE id = 1

Now the read and the write happen inside one statement that the database runs atomically, holding the lock the whole time. Final balance: exactly 16,000. Zero lost. Same 8 threads, same 16,000 operations, one line different.

The thing I will not forget: the bug was invisible on a single thread. It only showed up under concurrency, and it showed up as wrong data, not a crash. No error, no stack trace, just money that is quietly incorrect. That is the scariest kind of bug, and it is exactly what transactions and isolation levels exist to prevent.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #databases #learninginpublic

## X thread

**1/**

Today I corrupted a bank balance on purpose.

8 threads, each adds 1 to a balance 2,000 times. Should end at 16,000.

It ended at ~2,500. About 13,500 increments vanished. 84% of the money, gone. No error, no crash. Just wrong.

Day 11 of 60 days of system design.

**2/**

The bug is the way everyone writes it first:

    read balance into a variable
    add 1
    write it back

Thread A reads 400. Thread B reads 400 before A writes. Both write 401. Two increments, balance moved by one.

That is a lost update.

**3/**

The fix is one line:

    UPDATE accounts SET balance = balance + 1

Read and write now happen inside one atomic statement, lock held the whole time. No gap for another thread to slip into.

Final balance: 16,000. Zero lost.

**4/**

Same idea works for anything with a check in the middle (move money between two accounts, decrement stock): wrap it in BEGIN IMMEDIATE ... COMMIT so the read and the write are one indivisible unit.

It was correct, but about 14x slower, because threads wait their turn. That is the price of isolation.

**5/**

The lesson that stuck: this bug is invisible on one thread. It only appears under concurrency, and it appears as quietly wrong data, not a crash.

That is the whole reason transactions and isolation levels exist.

Code: github.com/anurag629/system-design-60-days
