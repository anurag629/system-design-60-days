---
title: "Day 2: estimation vs reality"
parent: "Week 1: ground truth"
nav_order: 2
has_children: true
---

# Day 2, Wednesday 2026-09-23
## Estimation, and the moment reality disagrees with you 📏

Today's one idea: an estimate you never check is just a guess wearing a nice shirt. You will estimate six things on paper, then measure all six, and the gap between the two will teach you more than either number alone.

Day 1 was about how fast a computer is. Today is about how much stuff costs: bytes on disk, writes per second, and the price of making a write survive a power cut. Every design from here on is built out of those three.

---

## Welcome back, quick recap first ☕ (5 min)

It has been a while since Day 1, so here is what you measured on this laptop. You need two of these numbers today, so keep them handy.

| What | Your number |
|---|---|
| RAM random read | 177 ns |
| SSD random 4 KB read | 84.7 µs |
| Localhost round trip | 19.5 µs |
| Round trip to Mumbai | 54.2 ms |

And the lesson that came with them: the page cache (the copy of recently used file data the operating system keeps in RAM) lied to you. Your first SSD number was 1.83 µs because you were really reading RAM. Hold on to that suspicion. Today a different layer tries the same trick.

---

## Words you will meet today 📖

Read this once now. Come back to it when the lab uses one of these words.

A transaction is a group of database changes that either all happen or none happen. Think of a UPI payment: money leaves your account and arrives in your friend's, or neither thing happens. There is no version where it leaves and never arrives.

Commit is the moment a transaction becomes final. After the database says "committed," it promises the change is permanent.

Durability is the part of that promise that says "even if the power goes out one millisecond later." That's the D in ACID, which you will meet properly in week 2.

fsync() is the system call (a request from a program to the operating system) that says "take everything I wrote to this file and put it physically on the disk, and do not return until it is really there." Without it, your writes sit in RAM for a while, and a power cut eats them. A database has to call fsync on every commit to keep its durability promise. That's slow, and today you find out how slow.

A write-ahead log (WAL) is a file the database appends to before it changes the real data. If it crashes halfway, it reads the log on restart and finishes or undoes the work. Appending to the end of one file is the cheapest kind of write a disk can do, which is why nearly every serious database works this way.

An index is a separate, sorted structure that lets the database jump to matching rows instead of checking every row. It works like the index at the back of a textbook. Without it the database does a full table scan: it reads all million rows and checks each one, like looking for one name by reading the entire phone book.

Extrapolation means measuring a small sample and multiplying up. You time 10,000 of something and multiply by 100 to estimate a million. It's a legitimate tool as long as you say out loud that you used it.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Google's back of the envelope pro-tip](https://highscalability.com/google-pro-tip-use-back-of-the-envelope-calculations-to-choo/). Short, and it's where this whole habit comes from.
- The pricing pages for [AWS S3](https://aws.amazon.com/s3/pricing/) and [AWS RDS for Postgres](https://aws.amazon.com/rds/postgresql/pricing/). Find two numbers and write them down: the price of storing 1 GB for a month on S3 Standard, and the price of 1 GB-month of RDS gp3 storage. Most engineers can't quote either one. That makes their designs impossible to argue with, and not in the good way.
- [Use The Index, Luke! chapter 1](https://use-the-index-luke.com/sql/anatomy), on how an index is actually laid out. Read it before the lab so the index section makes sense while you're in it.

Watch these two, after the lab:
- [Back of the envelope estimation](https://www.youtube.com/watch?v=WZjSFNPS9Lo), about 30 minutes. Your predictions are already on paper by then, so watch someone else size a system and notice where your instinct goes a different way.
- [Write-ahead logs, the secret to fast databases](https://www.youtube.com/watch?v=s3hKYMOpp3E) by Ben Dicken, 11 minutes. This is the payoff of today's lab in pictures: why one batched commit beats a thousand small ones.

### Powers of two, and why storage estimates go wrong (10 min)

You already know powers of ten. Storage is sold in powers of ten and allocated in powers of two, and this confuses everyone at least once.

| Power | Name | Approx | Exact |
|---|---|---|---|
| 2¹⁰ | kilo | 1 thousand | 1,024 |
| 2²⁰ | mega | 1 million | 1,048,576 |
| 2³⁰ | giga | 1 billion | 1,073,741,824 |
| 2⁴⁰ | tera | 1 trillion | 1,099,511,627,776 |

For estimation, 2¹⁰ ≈ 10³ and you move on. The 2.4% error grows to about 10% by terabytes, and you won't care. What you should care about is a much bigger gap, and it's what today's lab is about: a row of data does not take up the number of bytes its fields add up to. Not even close. You'll find out why by measuring.

### The nines (10 min)

Availability (the fraction of time a service is up and working) is quoted in "nines." Learn to convert instantly, because interviewers ask, and because it changes how you read an SLA (the uptime a provider promises you in writing).

| Availability | Downtime per year | Per month | Per day |
|---|---|---|---|
| 99% (two nines) | 3.65 days | 7.2 hours | 14.4 min |
| 99.9% (three nines) | 8.77 hours | 43.8 min | 1.44 min |
| 99.99% (four nines) | 52.6 min | 4.4 min | 8.6 s |
| 99.999% (five nines) | 5.26 min | 26 s | 0.86 s |

The row to remember: three nines still means 43 minutes of downtime a month. That's a full IPL powerplay plus the strategic timeout, every month, with your app down.

Now the part that bites. Say your service calls five other services, each promising three nines, and you need all five to answer. Your ceiling is 0.999⁵ = 99.5%, which is 3.6 hours a month. Dependencies multiply. Every part you add lowers your availability, never raises it.

That's the same compounding you met on Day 1, when tail latency got worse as you called more servers. Same math, different quantity. Notice that, na?

### Think about this while you read (20 min)

On Day 1 you estimated a messaging app creates about 4 TB of new messages per day. Using the two prices you just looked up, what does one year of that cost on S3? What would it cost on RDS? The ratio between those two numbers is the whole reason tiered storage exists: hot data (read often) goes on expensive fast storage, and cold data (rarely read) goes on cheap slow storage. P10 in the drill makes you do this properly.

---

## Block 2: drill (40 min) ✍️

Paper first, no laptop. Then copy your answers into [`notes/day-02-estimates.md`](../notes/day-02-estimates.md) (the template is already there) and into the prediction table in [`progress.md`](../progress.md).

The first six are the ones today's lab checks. Do not skip this, and do not peek at the lab output first. The whole exercise depends on you committing to a number before you find out. Estimating after you've seen the answer is like doing a DRS review after watching the replay. Not allowed.

### Predict these six, then the lab measures them

You're going to create a SQLite table with 1,000,000 rows:

```sql
CREATE TABLE messages (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER,
    body       TEXT,      -- exactly 200 characters
    created_at INTEGER    -- unix timestamp
);
```

SQLite is a full database that lives in a single file and ships inside Python. There's no server, and nothing to install.

P1. How many megabytes will the database file be? The naive answer is 1M × (8 + 8 + 200 + 8) = 1M × 224 bytes ≈ 214 MB. Is the real file bigger or smaller than that, and by how much?

P2. You insert all 1M rows inside one single transaction. How many seconds does it take?

P3. You insert the same rows with one transaction per row, so the database has to fsync after every single row. How many rows per second can it manage? Here's a hint. Day 1 measured a 4 KB SSD read at 84.7 µs. A durable write has to wait for the drive to confirm the data is truly stored, which is more work than a read. Start from that number and reason.

P4. How much bigger does the file get when you add an index on `user_id`? Give it as a percentage.

P5. You look up all messages for one `user_id` without an index, across 1M rows. How many milliseconds?

P6. The same lookup with the index. How many milliseconds? And what's the ratio between P5 and P6?

### And four for the interview muscle 💪

P7. A video platform gets 500 hours of new video every minute. Average 1 GB per hour after encoding. How many petabytes per year?

P8. You run a service on 20 machines. Each has a 99.9% chance of being up. You need at least one alive. What's your availability? Now you need all twenty alive. What is it now?

P9. A cache holds 100 GB and your average object is 4 KB. How many objects fit? If you get 200,000 reads per second and 90% of them hit the cache, how many reads per second reach the database?

P10. Day 1's messaging app: 4 TB/day. On S3 at about $0.023 per GB-month, what does storage cost in the twelfth month? Careful: the data piles up. You aren't paying for 4 TB in month twelve.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-02-estimation/estimate.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-02-estimation/estimate.py).

It works the same way as Day 1. The scaffolding is written and four TODOs are yours. It uses SQLite, which comes with Python, so there's nothing to pip install. Once the TODOs are in, it runs in under 30 seconds.

The script won't let you cheat. If the `PREDICTIONS` dictionary at the top is empty, it refuses to run. Once you fill it in, it prints your guess next to the real number and tells you how far off you were.

### What it measures

1. Bytes per row on disk. A 224-byte row does not take 224 bytes, and the reason is the most important fact about how databases store things. Week 2 is built on it.

2. Bulk insert speed, with one transaction wrapping all 1M rows.

3. Durable insert speed, with one transaction per row. The database calls fsync and waits for the SSD to confirm each write landed. This number will be dramatically, almost insultingly worse than #2. That gap is why every high-throughput system in the world batches its writes. Swiggy doesn't send one rider per dish when you order three.

4. The index, in two ways: what it costs in bytes and what it buys you in lookup time.

### Fill in the TODOs

1. Put your six predictions into `PREDICTIONS` at the top of the file. They should be the same numbers you wrote on paper.
2. TODO 1 times the bulk insert.
3. TODO 2 runs the one-commit-per-row loop under three durability settings.
4. TODO 3 times the lookup with no index.
5. TODO 4 times the same lookup with the index, keeping the best of five runs.

Each TODO is 3 to 10 lines, and the comment above it shows you the shape. Type it out yourself instead of copy-pasting the comment. Your fingers learn things your eyes skip.

Run it from inside the lab folder:

```bash
cd labs/day-02-estimation
python3 estimate.py
```

### What you're going to discover

I'll spoil the shape but not the numbers. The numbers are yours.

Your durable insert rate will come out as roughly `1 / (time for one fsync)`. If one fsync takes 1 ms, you get about 1,000 rows per second, no matter how fast your CPU is. Multiply that out for 1M rows and you'll see why the naive loop is unusable. It's also why every ORM tutorial that shows you `for row in rows: save(row)` is quietly teaching you to build something that falls over on Big Billion Days.

The index will make the lookup faster by some factor. Predict the factor before you see it. Then look at what the index cost you, in bytes and in how long it took to build. There's no free index. Week 2 is mostly about that trade.

### Traps ⚠️

- On a Mac, plain `fsync()` returns as soon as the SSD accepts the write into its own internal buffer, before it's actually stored. Apple has a stronger call, `F_FULLFSYNC`, for people who really mean it. The lab measures both, and the gap between them is today's version of Day 1's page cache lie. The long comment in `fresh_db()` explains it. Read that comment.
- SQLite's `synchronous` setting decides whether it calls fsync at all. The script sets it explicitly for every test, so you always know what you measured. If a number looks too good, check that first. Day 1 should have made you suspicious of any measurement that pleases you.
- The script deletes `messages.db` before each test. If you start experimenting on your own, delete it yourself (`rm -f messages.db*`), or you'll be timing inserts into a table that already has a million rows in it.
- Timing a million individual durable commits would take several minutes, so the script times 10,000 and multiplies, and it prints that it's doing so. That's extrapolation. It's fine. Just always say it.
- The indexed lookup is so fast that the timer is almost measuring nothing. That's why TODO 4 keeps the best of five runs. Don't over-read the third decimal place.

### Deliverable

[`labs/day-02-estimation/RESULTS.md`](../labs/day-02-estimation/RESULTS.md) has a skeleton waiting for you. Paste the scoreboard the script prints. Then write one sentence for each of the six predictions: were you high or low, by how much, and why do you now think that happened?

Being wrong is the point. On Day 1 you were 2x off on D3 and it carried straight into D4. That isn't failure. That's calibration. An estimator who is never surprised has stopped estimating and started reciting.

---

## Block 4: write (30 min) 📣

Your angle today is prediction versus reality. It's a strong one because almost nobody publishes their wrong guesses.

The hook writes itself once you have the numbers: "I predicted my database would insert N rows per second. It did M. Here's the thing I forgot about."

Drafts go in `shares/day-02-linkedin.md` and `shares/day-02-twitter.md`. Write them yourself today. On Day 1 I drafted the posts so you could see the shape. Today you have a real finding of your own, and it will read better in your voice than in mine.

Two rules. Lead with the number you got wrong, not the one you got right. And attach a screenshot of the scoreboard, because a table with a "30x too HIGH" column in it is the kind of thing people stop scrolling for.

---

## End-of-day report 📝

Send me these three:

1. Which of the six predictions were you closest on, and which one were you most wrong on?
2. The fsync number. Say it out loud to me, in microseconds per commit, for both the real fsync and the one that lies.
3. One thing you still can't explain.

Day 3 is what actually happens when you type a URL. We'll use `tcpdump` to watch the packets behind the round trips you measured on Day 1. I'll write it after your report, so if something today didn't land, Day 3 comes at it from a different side first.

---

## Drill answers 🔑

Open these only after writing yours. P1 through P6 aren't here on purpose, because the lab tells you those. That's the whole exercise.

<details markdown="1">
<summary>P7 through P10</summary>

P7. 500 hours/min × 60 × 24 = 720,000 hours of video per day. × 1 GB = 720 TB per day. × 365 ≈ 263 PB per year. That's roughly YouTube's order of magnitude, and it's why nobody stores video in a database.

P8. At least one alive: the only failure is all 20 down at the same moment, probability 0.001²⁰, which is effectively zero. Availability ≈ 100%. All twenty alive: 0.999²⁰ = 98.02%, which is about 7 days of downtime a year.

Same 20 machines. Same hardware. The difference between the best availability you can imagine and a genuinely bad one comes entirely from whether your design needs one of them or all of them. That one idea is most of what redundancy means.

P9. 100 GB / 4 KB = 10¹¹ / (4 × 10³) = 25 million objects. With a 90% hit rate, 10% of 200,000 = 20,000 reads per second reach the database.

Now the part people miss. If your hit rate drops from 90% to 80%, database load doesn't rise by 10%. It goes from 20,000 to 40,000 reads per second. It doubles. The database only ever sees the misses, and the miss rate just went from 10% to 20%. So a cache that gets slightly worse can take down the thing behind it. That's the shape of most cache-related outages, and it's week 3.

P10. The data piles up, so in month 12 you're storing about 12 months of it. 4 TB/day × 365 = 1,460 TB ≈ 1.46 PB by year end. 1,460,000 GB × $0.023 ≈ $33,600 for the twelfth month alone. Across the whole year you're storing about half that much on average, so the year costs somewhere around $200,000.

That's S3, the cheap tier. RDS gp3 storage is roughly 5x the price per GB (check the number you wrote down), so the same data would cost about a million dollars a year. And it won't fit anyway, because a single RDS Postgres instance tops out at 64 TB. Now you know why nothing keeps everything hot forever, and why "just put it all in Postgres" stops being an answer around the terabyte mark.

</details>
