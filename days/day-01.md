# Day 1 — Friday 2026-07-10
## How slow is slow?

**Today's one idea:** a computer is a stack of storage tiers, and each tier down is roughly 100 times slower than the one above it. Almost every performance decision in system design is you noticing that some data is on the wrong tier.

Nothing today assumes prior knowledge. If a term is new, it's explained.

---

## Block 1 — Read (50 min)

### Today's links (all free)

**Core, do these:**
- Interactive latency table, set the year to 2026: https://colin-scott.github.io/personal_website/research/interactive_latency.html
- Jeff Dean's original "Latency Numbers Every Programmer Should Know": https://gist.github.com/jboner/2841832
- DDIA, chapter 1. Book site with free chapter 1 preview: https://dataintensive.net/

**If a term today was new:**
- *High Performance Browser Networking*, ch. 1 (free, full text): https://hpbn.co/primer-on-latency-and-bandwidth/
- The classic "what happens when you type a URL" walkthrough (you'll build on this Day 3): https://github.com/alex/what-happens-when

**One video, only after the lab, optional:**
- Hussein Nasser on latency and the network stack: https://www.youtube.com/@hnasr

Full curated list, mapped to every week: [resources.md](../resources.md).

### First, the mental model (read this part slowly, 10 min)

When your program needs a piece of data, it can live in one of a few places. From fastest to slowest:

**CPU cache.** A tiny amount of memory physically on the processor. Around 1 nanosecond to reach. A nanosecond is a billionth of a second. Light travels about one foot in a nanosecond. Your CPU cache holds maybe a few megabytes.

**RAM, also called main memory.** Around 100 nanoseconds. So a hundred times slower than cache. Your laptop probably has 16 to 64 gigabytes. When people say "in memory," this is what they mean. When your program is running, its variables live here.

**SSD, the disk.** Around 16 *micro*seconds for a small random read. A microsecond is a millionth of a second, so a thousand nanoseconds. That makes an SSD read roughly 150 times slower than RAM. Your laptop has maybe 500 gigabytes to 2 terabytes of it. The important property is that data here survives a reboot.

**The network.** Sending a request to a server in the same building and getting an answer back takes around 500 microseconds. To a server on another continent, about 150 *milli*seconds. A millisecond is a thousandth of a second. That cross-continent trip is roughly a million times slower than reaching into RAM.

Now look at those four tiers again and notice the pattern. Each step down buys you more space and costs you about two orders of magnitude of speed. That trade is the reason caches exist, the reason databases have indexes, the reason CDNs exist, and the reason people put servers in many countries. All of it is the same move: *this data is on a slow tier and it's being read a lot, so let's keep a copy on a faster tier.*

### Some units, because they trip everyone up

| Unit | Fraction of a second | Written |
|---|---|---|
| second | 1 | s |
| millisecond | 1/1,000 | ms |
| microsecond | 1/1,000,000 | µs or us |
| nanosecond | 1/1,000,000,000 | ns |

So: 1 ms = 1,000 µs = 1,000,000 ns. Say that out loud once. You will be converting between these constantly and it should be reflexive, not something you work out.

### Now the canonical table (10 min)

Open https://colin-scott.github.io/personal_website/research/interactive_latency.html and drag the year slider to 2026. This is a famous list originally written by Jeff Dean at Google. Play with the slider from 1990 to 2026 and watch which bars shrink and which barely move.

Here it is, roughly, for 2026:

```
L1 cache reference                        1 ns
Main memory (RAM) reference             100 ns
Read 1 MB sequentially from RAM       3,000 ns  =    3 µs
Read 4 KB randomly from an SSD       16,000 ns  =   16 µs
Read 1 MB sequentially from an SSD   50,000 ns  =   50 µs
Round trip inside one datacenter    500,000 ns  =  500 µs
Round trip California to Europe                 =  150 ms
```

**The single most important observation:** network round trips barely improved over thirty years, while CPU and memory got much faster. Physics doesn't care about your budget. The speed of light through fiber is fixed. This is why "just put it in another region" is so often the wrong answer, and it's why you'll hear experienced engineers obsess over *how many* network round trips a request makes rather than how fast each one is.

### Then read (30 min)

Kleppmann, *Designing Data-Intensive Applications*, chapter 1 ([book site with free ch.1 preview](https://dataintensive.net/)). If you don't have the book yet, the free preview covers exactly what you need for today.

You are reading for exactly one section: the part about **percentiles**. Don't worry about the rest yet, it'll make more sense in week 2.

The idea, in case the book's version is dense: if you measure how long a thousand requests took and sort them, the **median** (also called p50) is the middle one. Half your users had a better experience, half worse. The **p99** is the 990th one, so only 1% of requests were slower than that.

Averages lie. If 99 requests take 10ms and one takes 10 seconds, the average is about 110ms, which describes *nobody's* actual experience. The p99 tells you about your unhappiest customers, and those are usually the ones with the most data, meaning your most valuable ones.

**Hold this question while you read:** if a single web page makes 10 calls to a backend service, and that service has a p99 of 100ms, what fraction of page loads will contain at least one slow call? Try to reason it out. The answer is at the bottom and it surprises almost everyone.

---

## Block 2 — Drill (40 min)

Paper and pen. No laptop, no calculator. The point is to get comfortable being approximately right, fast.

### Two shortcuts you should memorize right now

**Seconds in a day = 86,400.** Round it to **100,000**. You will never regret this. It makes the division trivial and you're within 15%, which is well inside "right answer" territory for estimation.

**Powers of ten.** Thousand is 10³ and we call it K. Million is 10⁶, M. Billion is 10⁹, B. For bytes: kilobyte KB, megabyte MB (10⁶), gigabyte GB (10⁹), terabyte TB (10¹²), petabyte PB (10¹⁵).

### Worked example, so you see the shape of it

*A photo app has 100 million daily active users. Each opens the app 10 times a day. Each open makes 1 request to the feed service. What's the average requests per second?*

100M users × 10 opens = 1 billion requests per day.

1 billion / 100,000 seconds = 10,000 requests per second.

Done. Notice what I did: I never wrote 86,400. I never used a calculator. I turned 10⁹ / 10⁵ into 10⁴. **That's the whole technique.** Count the zeros.

Now: is 10,000 requests per second a lot? For a single modest server doing simple work, yes, that's near the edge. For a fleet of twenty, it's nothing. You now know roughly what shape of system you're building, and you got there in fifteen seconds.

### Your turn. Five minutes each, write the answer down before checking.

**D1.** A messaging app has 500 million daily active users. Each sends 40 messages per day. What is the average number of messages written per second?

**D2.** Traffic isn't flat, it peaks in the evening. Assume peak is 3 times the average. What's the peak write rate for D1?

**D3.** Each message is about 200 bytes of text plus metadata. How much new data does the app store per day? Per year? (Give it in GB or TB, whichever is more natural.)

**D4.** You want to keep the last 30 days of messages in RAM so reads are fast. Using your answer from D3, how many gigabytes is that? A large cloud machine has 512 GB of RAM. How many machines do you need, ignoring redundancy?

**D5.** A user in Mumbai loads a page. The server is in Virginia, and the round trip between them is about 250ms. The server itself takes 200ms to build the response. The page then makes 3 more requests, one after another, each needing a fresh round trip. Roughly how long until the page is done? What's the single biggest thing you'd change?

Write your answers in `notes/day-01-drills.md` first. Then check the bottom of this file. The gap between what you guessed and what's true is the actual lesson, and it disappears if you peek.

---

## Block 3 — Build (100 min)

You're going to measure the storage hierarchy on your own machine. Python, because we're measuring things that take microseconds and milliseconds, and Python's overhead of ~50ns per operation doesn't meaningfully pollute those. (It *would* pollute a CPU cache measurement, which is exactly why we're skipping that tier today. Honesty about what your tools can and can't measure is part of the craft.)

I've put a starter file at `labs/day-01-latency/measure.py` with the fiddly parts already written. Your job is the four `TODO` blocks.

### What you're measuring

1. **RAM random read.** Jump to random positions in a 200 MB array, read 8 bytes. Expect something in the low hundreds of nanoseconds per read.
2. **SSD random read.** Jump to random positions in a 1 GB file on disk, read 4 KB. Expect tens of microseconds. There's a trick here: the operating system caches recently-read file data in RAM (the "page cache"), so a naive second read measures RAM and you'd never know. The starter file disables that caching for you and explains how in a comment. Read the comment.
3. **Localhost network round trip.** Ping an HTTP server running on your own machine. No real network involved, so this measures the cost of the operating system's networking machinery, not distance. Expect tens to low hundreds of microseconds.
4. **Real network round trip.** Ping a server far away. Use `https://www.google.com` and something deliberately distant. Expect tens to hundreds of milliseconds.

### The deliverable

`labs/day-01-latency/RESULTS.md`, containing a table with three columns:

| What | Canonical value | My measurement | Ratio to RAM |
|---|---|---|---|

And below it, two paragraphs:
- **The ratios.** How many RAM reads fit in one SSD read? How many SSD reads fit in one cross-country round trip? These ratios are what you'll actually carry with you. Write them out as sentences: "One trip to Europe costs as much as ___ SSD reads."
- **The surprise.** One measurement that didn't match the canonical table. State what you expected, what you got, and your best guess at why. You don't need to be right. You need to have a theory.

### Mistakes you will probably make, in the order you'll make them

**Not warming up.** The first time you run anything, Python is still importing, the file isn't open yet, the network connection isn't established. Always throw away the first 10 iterations before you start timing. The starter file does this, but understand *why*.

**Timing one operation.** A single measurement of something that takes 100 nanoseconds is meaningless, because your clock isn't that precise and your OS might interrupt you mid-measurement. Time 100,000 operations and divide. The starter file does this too.

**Reporting the average.** You just read about percentiles. Don't average your samples. Report p50 and p99, and notice how far apart they are, especially for the network. That gap *is* the lesson from this morning's reading, showing up in your own data within hours of learning it. That's a good feeling. Chase it.

**Measuring the page cache and calling it disk.** If your SSD number comes out around 100 nanoseconds, you did not measure your SSD. You measured RAM. Go read the comment in the starter file again.

### If you finish early

Run the network measurement 500 times and plot a histogram of the results. You'll see a tight cluster and then a long, ugly tail stretching to the right. That shape has a name, and it's the reason p99 exists. Screenshot it. It's your social post.

---

## Block 4 — Write (30 min)

Thirty minutes. Draft, light edit, publish. Do not spend an hour making it perfect. Nobody is grading you and the compounding comes from consistency.

The instinct will be to apologize for being a beginner. Don't, but also don't pretend to be further along than you are. "I measured this today and here's what surprised me" is interesting to read. "Here are 5 things every engineer must know about latency" from someone on day 1 is not, and people can smell it.

### LinkedIn post

Your angle: **you measured it instead of memorizing it.**

Rough shape, rewrite it in your own words:

> I'm starting 60 days of system design, 4 hours a day. Day 1.
>
> Everyone shares Jeff Dean's latency numbers. I've seen that table a hundred times and never once checked whether it was true on my own machine.
>
> Today I measured it.
>
> [your table, 4 rows]
>
> What I didn't expect: [your surprise]. I thought [X]. I got [Y]. My theory is [Z], and I'm not sure I'm right.
>
> The number I keep thinking about: one network round trip from India to Virginia costs about as much as [N] reads from RAM.
>
> That reframes a lot. "Should we cache this?" isn't a matter of taste. It's a comparison between two numbers. If you don't know the numbers, you're just guessing with confidence.
>
> Day 1 of 60. Learning in public, mistakes included.
>
> #systemdesign #softwareengineering #learninginpublic

If you did the histogram stretch goal, attach it. A real chart from your own machine will outperform any amount of writing.

### Twitter / X thread, 5 tweets

1. The number, stated flat, no preamble. *"One network round trip from Mumbai to Virginia costs as much as roughly 2 million reads from RAM. I measured it today rather than trusting the table."*
2. What you built and why. One sentence.
3. Your table, as an image.
4. The surprise, and your theory for it. Say "I think" if you're not sure. Uncertainty reads as honest.
5. The consequence: one design decision this changes for you. Then the 60-day frame.

**Voice rules.** No 🧵 emoji. No "Let that sink in." No "Here's what I learned 👇". Just say the thing. Every tweet should contain a number.

---

## End-of-day report

Send me three things:

1. **What you completed, and what you skipped.** Skipping is fine and expected. Lying about it wastes both our time, because I build tomorrow from this.
2. **The number that surprised you.** From the lab.
3. **One thing you still can't explain to yourself.** This is the most valuable of the three. It tells me where to aim tomorrow.

---

## Drill answers

Only open this after you've written your own. Seriously.

<details>
<summary>Click to expand</summary>

**D1.** 500M × 40 = 20 billion messages/day. 20 × 10⁹ / 10⁵ seconds = **200,000 messages per second.**

**D2.** 3 × 200,000 = **600,000 writes per second at peak.** Sanity check: a single well-tuned Postgres instance handles somewhere in the low tens of thousands of simple writes per second. So this system needs somewhere on the order of 50 to 100 database shards. You just discovered why WhatsApp is not one Postgres box, and you did it with two lines of arithmetic.

**D3.** 20 × 10⁹ messages × 200 bytes = 4 × 10¹² bytes = **4 TB per day.** Per year: × 365 ≈ **1,460 TB, so about 1.5 petabytes.**

**D4.** 30 days × 4 TB = 120 TB. At 512 GB per machine: 120,000 GB / 512 GB ≈ **235 machines.** And that's before replication, which typically triples it. Now you understand, concretely, why keeping everything in RAM is a fantasy and why systems tier their storage: recent messages hot in RAM, older ones on SSD, ancient ones in cheap object storage. Nobody designed that because it was elegant. They did it because of this arithmetic.

**D5.** Round trip 250ms + server 200ms = 450ms for the first response. Then 3 more sequential requests at 250ms each (assume they're fast on the server) = 750ms. Total ≈ **1.2 seconds.**

The biggest change is **not** "make the server faster." Cutting the server's 200ms in half saves you 100ms out of 1,200. The biggest change is **removing round trips.** Combine those 3 follow-up requests into 1, and you save 500ms instantly. Or put a copy of the content geographically closer to Mumbai, which cuts every 250ms trip to maybe 30ms.

This is the lesson that makes today worth it. Beginners optimize the code. The round trips were 1,000ms of the 1,200ms, and no amount of code optimization touches them.

**And the percentile question from the reading:** if one call has a 1% chance of being slow, the chance that a page making 10 independent calls has *at least one* slow call is 1 − (0.99)¹⁰ ≈ **9.6%.**

So a service everyone describes as "p99 = 100ms, we're fine" produces a slow experience for nearly one in ten page loads. This is why large companies obsess over p99.9 and p99.99 on internal services. The tail doesn't stay in the tail. Fan-out drags it into the middle.

</details>
