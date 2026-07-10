# Day 1 results — the storage hierarchy on my machine

Measured 2026-07-10. Apple Silicon laptop, macOS, Python 3, `measure.py`.

## The table

| What | Canonical (2026) | Measured (p50) | Measured (p99) | Ratio to my RAM |
|---|---|---|---|---|
| RAM random read | 100 ns | **177 ns** | — | 1x |
| SSD random 4 KB read | 16 µs | **84.7 µs** | 134 µs | 478x |
| Localhost TCP round trip | — | **19.5 µs** | 59.1 µs | 110x |
| RTT to Mumbai | — | **54.2 ms** | 73.0 ms | 306,069x |
| RTT to Dublin | — | **188.3 ms** | 229.9 ms | 1,063,499x |
| RTT to Sydney | — | **198.6 ms** | 285.0 ms | 1,121,960x |
| RTT to Virginia | — | **295.6 ms** | 312.2 ms | 1,669,751x |
| RTT to São Paulo | — | **417.9 ms** | 627.0 ms | 2,360,722x |

Network hosts are AWS regional endpoints, which answer from the region on the
label. Famous university sites do not; they sit behind CDNs and answer from a
cache down the road.

## The ratios, in English

- One SSD read costs as much as **478 reads from RAM**.
- One round trip to Mumbai costs as much as **306,000 reads from RAM**.
- One round trip to São Paulo costs as much as **2.36 million reads from RAM**.

That last one is the number I'll actually carry. In the time it takes to ask a
server in Brazil a single question, this laptop could have read a value out of
memory 2.36 million times. Every cache, every CDN, and every read replica ever
built exists because of that ratio.

## Surprise 1: my network is faster than my disk

This is the one that got me. The mental model I started the day with was a clean
hierarchy: RAM, then SSD, then network, each roughly 100x slower than the last.

My numbers say:

```
SSD random 4 KB read    84.7 µs
localhost TCP RTT       19.5 µs   <- 4.3x faster than the disk
```

A full TCP round trip through the kernel, with two context switches and a
scheduler wakeup, beat a single 4 KB read off the SSD by more than 4x.

**My theory:** the "network is slow" intuition is really "distance is slow."
Loopback has no distance. What's left is the operating system's networking code,
and that's just CPU work, so it lands in the tens of microseconds. The SSD, in
contrast, is a physical device sitting on a PCIe bus. I forced every read to
actually go there by disabling the page cache, and I did it one read at a time
with no parallelism, which is the worst possible way to use an NVMe drive. NVMe
gets its famous throughput from having dozens of requests in flight at once.
I gave it one.

**What this changes:** "read it from a Redis box across the datacenter" is not
automatically worse than "read it from local disk." A same-datacenter round trip
is around 500 µs, which is still ~6x my SSD read, so disk wins there. But the
gap is one order of magnitude, not three, and it collapses entirely if the disk
read is uncached and the network hop is short. The hierarchy is a guideline, not
a law, and the boundaries between tiers are much blurrier than the tidy table
suggests.

## Surprise 2: the worst tail latency was on localhost

| Measurement | p99 / p50 |
|---|---|
| localhost RTT | **3.03x** |
| SSD read | 1.59x |
| São Paulo RTT | 1.50x |
| Sydney RTT | 1.43x |
| Mumbai RTT | 1.35x |
| Virginia RTT | 1.06x |

A packet that never left the machine was three times less predictable than one
that crossed the Atlantic and came back.

**My theory:** it isn't the network, because there isn't one. It's the scheduler.
Every loopback round trip needs the OS to wake up the echo-server thread, and if
a core is busy the wakeup waits. Most of the time it's instant. Occasionally you
land behind a scheduling quantum and pay tens of microseconds.

Meanwhile Virginia's p99/p50 was 1.06x, almost perfectly consistent. Once a
packet is committed to a long fiber path, the variance of the routers along the
way is small compared to the 296 ms of distance it has to cover anyway. **Long
latencies can be more predictable than short ones.** Averages would have hidden
this completely. Percentiles are how I saw it.

## Surprise 3: nobody gets the speed of light

Light in fiber moves at about 200,000 km/s, roughly two thirds of its vacuum
speed. So a round trip has a hard physical floor of `distance / 100` in
milliseconds. Nothing gets under it. Ever.

| Region | Distance (approx) | Physics floor | Measured | Tax |
|---|---|---|---|---|
| Mumbai | 1,150 km | 12 ms | 54 ms | **4.7x** |
| Dublin | 6,800 km | 68 ms | 188 ms | **2.8x** |
| Sydney | 10,400 km | 104 ms | 199 ms | **1.9x** |
| Virginia | 12,000 km | 120 ms | 296 ms | **2.5x** |
| São Paulo | 14,200 km | 142 ms | 418 ms | **2.9x** |

Everything is 2 to 5x slower than physics requires. Fiber doesn't run in straight
lines, it follows railways and coastlines and old telegraph routes. Every router
along the way stops the packet, reads its header, and forwards it. The tax is the
sum of all of that.

Notice the tax *shrinks* with distance: Mumbai pays 4.7x, Sydney pays 1.9x. The
fixed overhead of the first and last mile, my home ISP, is a big fraction of a
short trip and a small fraction of a long one.

## Surprise 4: my RAM is 77% slower than the canonical number

177 ns measured against a canonical 100 ns.

**My theory: TLB misses.** The buffer is 200 MB, which is 51,200 pages of 4 KB
each. The TLB, the small cache that translates memory addresses, holds maybe
2,000 to 3,000 entries. I'm jumping to random pages, so nearly every access
misses the TLB and the CPU has to walk the page table to find out where the data
physically lives, which itself costs memory reads.

So 177 ns isn't "a RAM read." It's a TLB miss plus a page walk plus a RAM read.
Sequential access would be far faster because the prefetcher would see it coming.
**Random access is the expensive thing, not memory access.** Which is, I suspect,
the reason databases store rows in pages and read them in blocks instead of
chasing pointers around.

## Bugs I found in the lab code

1. The internet probe originally used `www.mit.edu` and `www.unimelb.edu.au`.
   Both sit behind CDNs, so I was measuring the distance to a nearby cache, not
   to Boston or Melbourne. Melbourne "answered" in 41 ms, which is physically
   impossible. Replaced with AWS regional endpoints.

2. `socket.create_connection((host, port))` resolves DNS on every call. The timed
   loop was measuring DNS lookup plus TCP handshake and reporting the sum as a
   round trip. Fixed by resolving once, up front.

3. The SSD benchmark disabled the page cache on the read handle but not the write
   handle. Since the file had just been written, its pages were already in RAM.
   Measured p50 was 1.83 µs, which is memory. Writing with `F_NOCACHE` and
   `fsync` moved it to 84.71 µs, which is the disk. **A 46x error, reported with
   no warning at all.** The sanity check was set at 1 µs, below the failure it
   was watching for, so it stayed quiet and made the wrong number look verified.

That third one is the real lesson of the day. Benchmarks don't crash. They return
a number you're pleased with.

## What I'd tell yesterday's me

Round trips dominate. Everything else is noise until you've counted them.

A page that makes 4 sequential calls to Virginia has spent 1.2 seconds before the
server has done a single useful thing, and making the server code twice as fast
would save nothing worth measuring. The fix is never "optimize the code." The fix
is "make fewer round trips" or "move the data closer."
