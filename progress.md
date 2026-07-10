# Progress log

Format: one entry per day. Fill it in at the end of the Write block.

---

## Day 1 — 2026-07-10 — Latency numbers ✅

- [x] Read: DDIA ch. 1 + interactive latency table
- [x] Drill: D1-D5 answered before checking
- [x] Build: `labs/day-01-latency/RESULTS.md`
- [ ] Write: LinkedIn post + Twitter thread (drafts in `shares/`, post tomorrow AM)

**Drill score:** D1 ✅ D2 ✅ D3 ✗ (2 TB, actual 4 TB — dropped a factor of 2)
D4 ✗ (120 machines, actual 235 — but arithmetic was right, the bad D3 propagated)
D5 partial (1.8 s was a fair reading of an ambiguous question; missed the second half)

**Measured:**

| What | Canonical | Mine |
|---|---|---|
| RAM random read | 100 ns | 177 ns |
| SSD random 4 KB | 16 µs | 84.7 µs |
| Localhost RTT | — | 19.5 µs |
| RTT Mumbai | — | 54.2 ms |
| RTT São Paulo | — | 417.9 ms |

**Surprising number:** localhost round trip (19.5 µs) is **4.3x faster than an
SSD read** (84.7 µs). The textbook hierarchy says the network sits below the
disk. On this machine it doesn't. "Network is slow" really means "distance is
slow," and loopback has no distance.

**Runner-up:** localhost had the worst tail of anything measured, p99/p50 = 3.03x,
worse than São Paulo's 1.50x. Not the network. The scheduler.

**Can't explain yet:** why my RAM read is 177 ns against a canonical 100 ns.
Current theory is TLB misses (200 MB is 51,200 pages, the TLB holds ~2-3k
entries, so random access misses almost every time and the CPU walks the page
table). Unverified.

**Bugs found in the lab:**
1. CDNs made "distance to Melbourne" measure the distance to a cache down the road
2. DNS was being timed inside the TCP connect loop
3. SSD benchmark measured the page cache: reported 1.83 µs, real answer 84.7 µs

**Shipped:** github.com/anurag629/system-design-60-days

---

## Day 2 — 2026-07-11 — Estimation vs reality

- [ ] Read: powers of two, the nines, Alex Xu ch. 2, S3 + RDS pricing pages
- [ ] Drill: P1-P6 predictions written down **before** running the lab; P7-P10
- [ ] Build: `labs/day-02-estimation/RESULTS.md`
- [ ] Write: both posts, in your own words this time

**Predictions (fill in before running):**

| | Predicted | Actual | Off by |
|---|---|---|---|
| P1 db size (MB) | | | |
| P2 bulk insert (s) | | | |
| P3 durable rows/sec | | | |
| P4 index size (%) | | | |
| P5 scan (ms) | | | |
| P6 indexed lookup (ms) | | | |

**Most wrong on:**

**The fsync number:**

**Can't explain yet:**

---
