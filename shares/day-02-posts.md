---
title: "Day 2 posts"
parent: "Day 2: estimation vs reality"
grand_parent: "Week 1: ground truth"
nav_order: 3
---

# Day 2 posts: LinkedIn and X

Written with the reference run's numbers (Apple Silicon laptop, macOS). The numbers in square brackets are your guesses. Fill them in honestly, because the wrong guesses are what make this post work. Then replace the measured numbers with yours.

Lead with the number you got most wrong. Attach a screenshot of the scoreboard.

## LinkedIn

Day 2 of 60 days of system design. Today I wrote down six guesses about a SQLite table with a million rows, then measured all six.

The one I got most wrong: how many rows per second a database can insert if every row is its own transaction.

I guessed [your P3 guess]. The real number was 3,501 rows per second.

The same million rows inside one transaction went in at 820,273 rows per second. Same data, same laptop, same database. 234 times faster.

The difference is one system call. When a database commits, it calls fsync() and waits for the SSD to confirm the bytes are physically stored. One commit per row means one wait per row, 286 microseconds each. One commit for everything means one wait, total. Every "we batch writes and flush every 100 ms" design you've ever read about exists because of this gap.

The part that bothered me more: macOS has two kinds of fsync. The normal one returns when the drive has accepted the data into its own cache, not when it's actually stored. That version ran at 18,376 rows per second, 5x faster than the honest one. The benchmark gets better and the durability quietly disappears. Nothing warns you.

Two smaller surprises:
- A 224-byte row took 228 bytes on disk. A 16-byte row of two integers took 11. Adding up field sizes is wrong in both directions.
- An index on user_id added 4.8% to the file and made a lookup 14,637 times faster (51 ms down to 0.003 ms).

An estimate you never check is just a guess. Mine were off by up to [your worst miss]x, and I learned more from that than from any table I've memorised.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #databases #learninginpublic

## X thread

**1/**

I guessed my laptop's database could do [your guess] durable inserts per second.

It did 3,501.

The same rows in one transaction: 820,273 per second. 234x faster, same data. Day 2 of 60 days of system design.

**2/**

The whole gap is one system call. Every commit calls fsync() and waits for the SSD to say "it's really stored."

One commit per row = 286 µs of waiting per row.
One commit for a million rows = one wait.

This is why every serious write path batches.

**3/**

The uncomfortable bit. On macOS, plain fsync() returns when the drive has *accepted* the write, not stored it.

honest fsync:   3,501 rows/s
plain fsync:   18,376 rows/s
no fsync:      99,795 rows/s

Faster benchmark, weaker guarantee, zero warnings.

**4/**

Row size, the naive way: add up the fields.

224-byte row → 228 bytes on disk (bigger)
16-byte row → 11 bytes on disk (smaller)

Wrong in both directions. SQLite stores small integers in 1 byte, and every row carries a header.

**5/**

An index on user_id cost 4.8% more disk and made a lookup 14,637x faster. 51 ms to 0.003 ms.

Predict first, then measure. My worst guess was off by [your worst miss]x.

Code: github.com/anurag629/system-design-60-days
