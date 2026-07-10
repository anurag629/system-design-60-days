# Day 2 — Saturday 2026-07-11
## Estimation, and the moment reality disagrees with you

**Today's one idea:** an estimate you never check is a guess. You'll estimate six
things on paper, then measure all six, and the gap will teach you more than
either number alone.

Yesterday you learned how fast a computer is. Today you learn how much stuff
costs: bytes, writes, and durability. Tomorrow's designs get built out of those.

---

## Block 1 — Read (50 min)

### Today's links (all free)

**Core, do these:**
- "Google pro-tip: back-of-the-envelope calculations" — the origin of this whole habit, and short: https://highscalability.com/google-pro-tip-use-back-of-the-envelope-calculations-to-choo/
- The System Design Primer, "Back-of-the-envelope" + "Appendix" sections (free, the powers-of-two and latency tables live here): https://github.com/donnemartin/system-design-primer#back-of-the-envelope-calculations
- AWS S3 pricing, the real numbers you'll reason with: https://aws.amazon.com/s3/pricing/
- AWS RDS pricing, to see the gap vs S3: https://aws.amazon.com/rds/pricing/
- Google SRE book, "Service Level Objectives" (the nines, done properly): https://sre.google/sre-book/service-level-objectives/

**For the lab (indexes and the query planner):**
- Use The Index, Luke! ch. 1, "Anatomy of an index" (free book): https://use-the-index-luke.com/sql/anatomy
- SQLite EXPLAIN QUERY PLAN docs, so you can read what the lab prints: https://www.sqlite.org/eqp.html

**Rusty SQL? optional warmup for week 2:**
- pgexercises, free SQL practice on a real dataset: https://pgexercises.com/

**One video, only after the lab, optional:**
- Arpit Bhayani on database internals (his "Asli Engineering" channel): https://www.youtube.com/@AsliEngineering

Full curated list, mapped to every week: [resources.md](../resources.md).

### Powers of two, and why storage estimates go wrong (10 min)

You already know powers of ten. Storage is sold in powers of ten and allocated in
powers of two, and this trips people up constantly.

| Power | Name | Approx | Exact |
|---|---|---|---|
| 2¹⁰ | kilo | 1 thousand | 1,024 |
| 2²⁰ | mega | 1 million | 1,048,576 |
| 2³⁰ | giga | 1 billion | 1,073,741,824 |
| 2⁴⁰ | tera | 1 trillion | 1,099,511,627,776 |

For estimation, 2¹⁰ ≈ 10³ and you move on. The 2.4% error compounds to about 10%
by terabytes and you will not care. What you *should* care about is a different
gap entirely, which today's lab is about: **a row of data does not occupy the
number of bytes its fields add up to.** Not even close. Find out why by measuring.

### The nines (10 min)

Availability is quoted in nines. Learn to convert instantly, because you'll be
asked and because it reframes what an SLA actually promises.

| Availability | Downtime per year | Per month | Per day |
|---|---|---|---|
| 99% (two nines) | 3.65 days | 7.2 hours | 14.4 min |
| 99.9% (three nines) | 8.77 hours | 43.8 min | 1.44 min |
| 99.99% (four nines) | 52.6 min | 4.4 min | 8.6 s |
| 99.999% (five nines) | 5.26 min | 26 s | 0.86 s |

The one that matters: **three nines still means 43 minutes of downtime a month.**
If your service depends on five other services that each promise three nines, and
you need all five, your ceiling is 0.999⁵ = 99.5%, which is 3.6 hours a month.
Dependencies multiply. Availability only ever goes down as you add parts.

That's the same compounding you met yesterday when tail latency got worse with
fan-out. Same math, different quantity. Notice that.

### Read (30 min)

Alex Xu, *System Design Interview* Vol 1, chapter 2. It is short. If you don't
have the book, search for "back of the envelope estimation system design" and
read any two of the top results, they all cover the same ground.

Then, and this is the more useful half: go find the **pricing page** for AWS S3
and for AWS RDS. Look up the actual cost of storing a terabyte for a month, and
the cost of a database instance with 64 GB of RAM. Write both numbers down. Most
engineers cannot tell you either, and it makes their designs unfalsifiable.

**Hold this question while you read:** yesterday you estimated 4 TB of new
messages per day. What does storing one year of that actually cost, in dollars,
on S3? Now on RDS? The ratio between those two numbers is why tiered storage
exists.

---

## Block 2 — Drill (40 min)

Paper. No laptop. Then write your answers in `notes/day-02-estimates.md`.

The first six are the ones today's lab will check, so write them somewhere you
can find them. **Do not skip this. The whole point is that you commit to a number
before you find out.**

### Predict these six, then the lab will measure them

You're going to create a SQLite table with 1,000,000 rows:

```sql
CREATE TABLE messages (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER,
    body       TEXT,      -- exactly 200 characters
    created_at INTEGER    -- unix timestamp
);
```

**P1.** How many bytes on disk will the database file be? (The naive answer is
1M × ~216 bytes ≈ 216 MB. Is it more or less than that, and by how much?)

**P2.** Inserting all 1M rows inside a single transaction. How many seconds?

**P3.** Inserting all 1M rows with one transaction per row, so the database must
flush to disk after each one. How many rows per second? (Hint: you measured
something yesterday that tells you almost exactly what a single durable write to
this SSD costs. Use it.)

**P4.** How much bigger does the file get when you add an index on `user_id`?
Give it as a percentage.

**P5.** Looking up all messages for one `user_id` **without** an index, over 1M
rows. How many milliseconds?

**P6.** The same lookup **with** the index. How many milliseconds? What's the
ratio between P5 and P6?

### And four for the interview muscle

**P7.** A video platform stores 500 hours of new video every minute. Average
1 GB per hour after encoding. How many petabytes per year?

**P8.** You run a service on 20 machines. Each has a 99.9% chance of being up. You
need at least one alive. What's your availability? Now: you need *all twenty*
alive. What is it now?

**P9.** A cache holds 100 GB and your average object is 4 KB. How many objects fit?
If you get 200,000 reads per second and 90% hit the cache, how many reads per
second reach the database?

**P10.** Yesterday's messaging app: 4 TB/day. On S3 at roughly $0.023 per GB-month,
what does one year of accumulated data cost in the twelfth month? (Careful: the
data accumulates. It isn't 4 TB you're paying for.)

---

## Block 3 — Build (100 min)

**Lab: `labs/day-02-estimation/estimate.py`**

Same shape as yesterday. Scaffolding is written, four TODOs are yours. It uses
SQLite, which ships inside Python, so there is nothing to install and no server
to run.

The script will not let you cheat. It asks for your six predictions first, at the
top of the file, then prints your prediction next to the truth and computes how
far off you were.

### What it measures

1. **Bytes per row on disk.** You'll find out that a 216-byte row does not take
   216 bytes, and the reason is the single most important fact about how
   databases store things. Week 2 builds on it.

2. **Bulk insert speed**, one transaction wrapping all 1M rows.

3. **Durable insert speed**, one transaction per row, so the database calls
   `fsync()` and waits for the SSD to confirm the write physically landed. This
   number will be dramatically, almost insultingly worse than #2. That gap is why
   every high-throughput system on earth batches its writes.

4. **Index cost**, in both bytes and lookup time.

### Fill in the TODOs

Open the file. Fill in your six predictions at the top. Then the four TODOs, each
a few lines. The comments walk you through it.

### What you're going to discover

I'll spoil the shape but not the numbers, because the numbers are yours.

Your durable insert rate will be roughly `1 / (time for one fsync)`. Yesterday you
measured a 4 KB read at 84.7 µs. An fsync is more expensive than a read, because
the drive has to acknowledge the data is truly persistent, not just accepted.
Multiply out what that means for 1M rows and you'll understand why the naive loop
is unusable, and why every ORM tutorial that shows you `for row in rows: save(row)`
is teaching you to build something that falls over.

The index will make your lookup faster by some factor. Predict that factor before
you see it. Then look at what it cost you in bytes and in insert speed. **There is
no free index.** Week 2 is largely about that trade.

### Traps

- SQLite's default `synchronous` mode may not be what you think. The script sets
  it explicitly and prints what it set, so you always know what you measured.
  If a number looks too good, that's the first place to check. Yesterday should
  have made you suspicious of any measurement that pleases you.
- Delete `messages.db` between runs. The script does this for you, but if you
  start experimenting on your own, remember.
- Timing 1M individual `fsync` calls would take most of an hour. The script does
  20,000 and extrapolates, and tells you it's extrapolating. **Extrapolation is a
  legitimate estimation tool.** Say so out loud when you use one.

### Deliverable

`labs/day-02-estimation/RESULTS.md`. The script prints a prediction-vs-reality
table. Paste it. Then, for each of the six, write one sentence: were you high or
low, by how much, and why do you now think that is?

Being wrong is the point. Yesterday you were 2x off on D3 and it cascaded straight
into D4. That's not a failure, that's calibration. **An estimator who is never
surprised has stopped estimating and started reciting.**

---

## Block 4 — Write (30 min)

Your angle today is **prediction versus reality**, and it's a strong one because
almost nobody publishes their wrong guesses.

The hook writes itself once you have the numbers: "I predicted my database would
insert N rows per second. It did M. Here's the factor I forgot about."

Drafts go in `shares/day-02-linkedin.md` and `shares/day-02-twitter.md`. Write
them yourself today. Yesterday I drafted them for you so you'd see the shape.
Today you have a real finding of your own and it will read better in your voice
than in mine.

Two rules. Lead with the number you got wrong, not the one you got right. And
include the terminal output as an image, because a prediction-vs-reality table
with a visible "you were 340x off" column is the kind of thing people screenshot.

---

## End-of-day report

1. Which of the six predictions were you closest on, and which were you most
   wrong on?
2. The fsync number. Say it out loud to me.
3. One thing you still can't explain.

Tomorrow is Day 3, what actually happens when you type a URL, and we'll use
`tcpdump` to watch the packets from today's round trips.

---

## Drill answers

Open only after writing yours. P1 through P6 aren't here on purpose. **The lab
tells you those.** That's the whole exercise.

<details>
<summary>P7 through P10</summary>

**P7.** 500 hours/min × 60 × 24 = 720,000 hours of video per day. × 1 GB = 720 TB
per day. × 365 ≈ **263 PB per year.** This is roughly YouTube's order of
magnitude, and it's why nobody stores video on a database.

**P8.** *At least one alive:* the only failure is all 20 down at once, probability
0.001²⁰, which is effectively zero. Availability ≈ **100%**, or 20 nines. *All
twenty alive:* 0.999²⁰ = **98.02%**, which is about 7 days of downtime a year.

Same 20 machines. Same hardware. The difference between the best availability you
can imagine and a genuinely bad one is entirely in whether your design needs one
of them or all of them. **This single idea is most of what redundancy means.**

**P9.** 100 GB / 4 KB = 10⁸ / 4×10³ ≈ **25 million objects.** With a 90% hit rate,
10% of 200,000 = **20,000 reads per second hit the database.**

Now the part people miss: if your hit rate drops from 90% to 80%, database load
doesn't rise by 10%. It goes from 20,000 to 40,000 requests per second. It
**doubles.** Cache hit rate is a lever on the miss rate, and the miss rate is what
your database actually experiences. A cache that gets slightly worse can take down
the thing behind it. This is the shape of most cache-related outages, and it's
Week 3.

**P10.** The data accumulates, so in month 12 you're storing 12 months of it.
4 TB/day × 365 = 1,460 TB ≈ 1.46 PB by year end. That's 1,460,000 GB × $0.023 ≈
**$33,580 for the twelfth month alone.** Total across the year is roughly half
that per month on average, so around $200,000 for the year.

And that's S3, the cheap tier. On RDS storage at roughly 10x, you'd be looking at
millions. Now you know why nothing keeps everything hot forever, and why "just
store it all in Postgres" stops being an answer somewhere around the terabyte
mark.

</details>
