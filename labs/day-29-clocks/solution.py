"""
Day 29 lab: failure, time, and the eight fallacies. The clock-skew bug, where
trusting the wall clock to order events across machines quietly eats your data.

This is the full working solution. The starter file is clock_skew.py.
Run it:      python3 solution.py

Standard library only, no network, no threads, no files. It is a DETERMINISTIC
simulation: one seeded stream of writes to a single key, replayed under different
clock conditions. Same numbers on every machine, every run.

The scenario. An active-active key-value store with two nodes, A and B. Clients
write to the same key, and each write is routed to whichever node is handy. Each
node stamps the write with ITS OWN wall clock and the nodes reconcile with
last-write-wins: when two writes to a key meet, keep the one with the larger
timestamp. This is exactly what Cassandra and DynamoDB LWW and old Riak do.

The bug. The two clocks do not agree. Node A's clock runs a little ahead of node
B's. So a write that truly happened LATER, on node B, can carry a SMALLER
timestamp than an older write on node A. Last-write-wins then keeps the older
write and silently throws away the newer one. No error. No log line. The newer
value just never existed, as far as the store is concerned.

The big ideas:
  - A newer write is silently lost whenever the older write sat on the faster
    clock and the clock lead was bigger than the gap between the two writes.
  - As skew grows, the share of newer writes lost climbs. For a fixed gap it is
    a clean cliff: zero loss while skew < gap, then loss the moment skew >= gap.
  - Tightening the clocks (NTP, a few ms) shrinks the loss a lot but never to a
    guaranteed zero, because a hot key gets near-simultaneous writes whose gap is
    smaller than even a few ms of skew.
  - The real fix is to stop ordering cross-machine events by the wall clock.
    Order them with a logical clock or a version vector (Day 33), which cannot be
    reordered by skew at all, or lean on a dedicated time service with bounded
    uncertainty (Google's Spanner TrueTime).
"""

import math
import sys
import random

PREDICTIONS = {
    # P1: node A's clock runs 200 ms ahead of node B's, writes to one hot key
    #     arrive on average 50 ms apart (Poisson). Under last-write-wins, what
    #     percent of the NEWER writes get silently discarded?
    "lww_loss_at_200ms_pct": 20,

    # P2: now fix the gap between writes at exactly 50 ms and grow the skew from
    #     0 upward. At what skew (ms) does the FIRST newer write start getting
    #     lost? (Below this, loss is exactly zero.)
    "loss_threshold_ms": 50,

    # P3: tighten the clocks to NTP quality, skew 2 ms. Same 50-ms-average write
    #     stream. What percent of newer writes are STILL lost now?
    "lww_loss_at_ntp_2ms_pct": 1,

    # P4: throw away the wall clock. Order the same writes by a logical version
    #     instead, at the same 200 ms of skew. What percent of newer writes are
    #     silently lost now?
    "logical_loss_pct": 0,
}

SEED = 42
N_WRITES = 20_000        # writes to one hot key in the main stream
MEAN_GAP_MS = 50.0       # Poisson arrivals, so gaps are exponential, mean 50 ms
MAIN_SWEEP = [0, 1, 2, 5, 10, 20, 50, 100, 200, 500]
HEADLINE_SKEW = 200      # the skew P1 and P4 ask about
FIXED_GAP_MS = 50.0      # the crisp-threshold demo uses a fixed inter-write gap
N_FIXED = 4_000
NTP_SWEEP = [0.5, 1, 2, 5, 10]
NTP_FOCUS = 2            # the skew P3 asks about


# ---------------------------------------------------------------------------
# The two clocks and the one resolution rule. This is the whole lab in 4 lines.
# ---------------------------------------------------------------------------

def stamp(true_time_ms, skew_ms):
    """TODO 1. The wall-clock timestamp a node puts on a write: the true time it
    happened PLUS this node's clock offset. This one line is the whole mistake,
    trusting a local clock to mean the same thing as every other node's clock.
    """
    return true_time_ms + skew_ms


def lww_lost(incoming_ts, stored_ts):
    """TODO 2. Last-write-wins keeps the larger timestamp. So the incoming (truly
    newer) write is SILENTLY LOST when its stamp is not strictly greater than the
    stored one. Ties go to the older write, which is its own little trap.
    """
    return incoming_ts <= stored_ts


def logical_stamp(stored_version):
    """TODO 3. The fix. Instead of reading a wall clock, a write observes the
    version it is replacing and writes the next one up. A counter that only ever
    goes forward, and never consults the time of day.
    """
    return stored_version + 1


def logical_lost(incoming_version, stored_version):
    """TODO 4. Same resolution rule as LWW, keep the larger value. The point of
    the day is that the RULE was never the problem: feed it wall-clock stamps and
    you lose data, feed it logical versions and you do not.
    """
    return incoming_version <= stored_version


# ---------------------------------------------------------------------------
# The seeded write stream and the measurements.
# ---------------------------------------------------------------------------

def make_stream(n, mean_gap, seed):
    """One key, n writes. Arrivals are a Poisson process, so the gaps between
    writes are exponential with the given mean. Each write lands on node A or B
    by a coin flip. Seeded, so the stream is identical on every run.
    """
    rng = random.Random(seed)
    writes = []
    t = 0.0
    for _ in range(n):
        t += rng.expovariate(1.0 / mean_gap)
        node = "A" if rng.random() < 0.5 else "B"
        writes.append((t, node))
    return writes


def make_fixed_stream(n, gap):
    """n writes at a fixed gap apart, strictly alternating A, B, A, B. Every B
    write immediately follows an A write, so every B write is a candidate for
    being lost. This makes the skew-vs-gap threshold a clean cliff.
    """
    writes = []
    t = 0.0
    for i in range(n):
        node = "A" if i % 2 == 0 else "B"
        writes.append((t, node))
        t += gap
    return writes


def lww_loss_pct(writes, skew):
    """Replay the stream under last-write-wins. Node A's clock is `skew` ms ahead
    of node B's. Walk the writes in true-time order (each one is genuinely newer
    than the one before). Count how often the newer write loses to the one it is
    trying to replace, purely because of the clock stamps.
    """
    prev_ts = None
    lost = 0
    total = 0
    for (t, node) in writes:
        s = skew if node == "A" else 0.0
        ts = stamp(t, s)
        if prev_ts is None:
            prev_ts = ts
            continue
        total += 1
        if lww_lost(ts, prev_ts):
            lost += 1
        prev_ts = ts           # the latest intent becomes what the next write updates
    return 100.0 * lost / total


def logical_loss_pct(writes):
    """Replay the same stream, but resolve by a logical version instead of the
    wall clock. Each write observes the stored version and writes the next one
    up, so the version always moves forward in true-time order. Skew is not even
    an input here, which is exactly the point.
    """
    stored_version = 0
    prev_version = None
    lost = 0
    total = 0
    for (t, node) in writes:
        v = logical_stamp(stored_version)
        if prev_version is None:
            prev_version = v
            stored_version = v
            continue
        total += 1
        if logical_lost(v, prev_version):
            lost += 1
        prev_version = v
        stored_version = v
    return 100.0 * lost / total


def find_threshold(fixed_writes, gap):
    """Smallest whole-millisecond skew at which any newer write is lost, for the
    fixed-gap stream. Below it, loss is exactly zero.
    """
    skew = 0
    while skew <= int(2 * gap) + 1:
        if lww_loss_pct(fixed_writes, skew) > 0:
            return skew
        skew += 1
    return None


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------

def part1(writes):
    print("=" * 78)
    print("Part 1: the clock-skew bug. A newer write, silently eaten by an older one")
    print("=" * 78)

    # The canonical single pair, spelled out.
    skew = 80.0
    a_true, b_true = 100.0, 140.0          # B truly happens 40 ms AFTER A
    a_ts = stamp(a_true, skew)             # node A clock is 80 ms ahead
    b_ts = stamp(b_true, 0.0)              # node B clock is on true time
    print("  One pair, by hand. Node A's clock is 80 ms ahead of node B's.")
    print(f"    write A: true time {a_true:.0f} ms on node A  ->  timestamp {a_ts:.0f}")
    print(f"    write B: true time {b_true:.0f} ms on node B  ->  timestamp {b_ts:.0f}")
    print(f"    B really happened {b_true - a_true:.0f} ms AFTER A, so B is the newer value.")
    if lww_lost(b_ts, a_ts):
        print(f"    but last-write-wins sees {b_ts:.0f} <= {a_ts:.0f}, keeps A, and drops B.")
    print("    the newer write is gone. No error, no log line. That is the bug.")
    print()

    # The sweep: how bad does it get as skew grows?
    print(f"  Now the real thing: {N_WRITES:,} writes to one key, gaps averaging")
    print(f"  {MEAN_GAP_MS:.0f} ms (Poisson), split across the two nodes. Node A's clock runs")
    print("  ahead by a growing skew. Percent of NEWER writes that LWW silently loses:")
    print()
    print("     skew (ms)     newer writes lost")
    loss_at_headline = None
    for skew in MAIN_SWEEP:
        pct = lww_loss_pct(writes, skew)
        bar = "#" * int(round(pct))
        print(f"     {skew:>6}        {pct:5.1f}%  {bar}")
        if skew == HEADLINE_SKEW:
            loss_at_headline = pct
    print()
    print("  Zero skew loses nothing. As the clock lead grows the loss climbs and")
    print("  then levels off: once A is reliably ahead, every write that crosses from")
    print("  the fast node to the slow one is at risk. One bad clock, a quarter of the")
    print("  updates to a hot key quietly vanishing.")

    # The crisp threshold: fixed gap, find the cliff.
    print()
    print(f"  The threshold, made crisp. Fix the gap between writes at exactly")
    print(f"  {FIXED_GAP_MS:.0f} ms and grow the skew. Loss is a cliff, not a ramp:")
    fixed = make_fixed_stream(N_FIXED, FIXED_GAP_MS)
    threshold = find_threshold(fixed, FIXED_GAP_MS)
    for skew in [0, 10, 30, 49, 50, 51, 80]:
        pct = lww_loss_pct(fixed, skew)
        print(f"     skew {skew:>3} ms   ->   {pct:5.1f}% lost")
    print(f"  Loss is exactly zero until skew reaches {threshold} ms, which is the gap")
    print(f"  between writes. Below the gap, skew cannot reorder two writes. At or above")
    print("  it, the older write's stamp overtakes the newer one and LWW keeps the wrong")
    print("  value. Skew only hurts you once it is larger than the time between writes.")
    return loss_at_headline, float(threshold)


def part2(writes):
    print("\n" + "=" * 78)
    print("Part 2: tighten the clocks (NTP). It shrinks the loss, it does not kill it")
    print("=" * 78)
    print("  NTP keeps machine clocks within a few milliseconds of each other. So the")
    print("  skew is tiny now, not 200 ms. Same write stream, small skews:")
    print()
    print("     skew (ms)     newer writes lost")
    loss_at_focus = None
    for skew in NTP_SWEEP:
        pct = lww_loss_pct(writes, skew)
        print(f"     {skew:>6}        {pct:5.2f}%")
        if abs(skew - NTP_FOCUS) < 1e-9:
            loss_at_focus = pct
    print()
    print("  Far better: at a couple of ms of skew the loss is a fraction of a percent,")
    print("  not a quarter. But look closely, it is not zero. A hot key gets bursts of")
    print("  nearly simultaneous writes, and any two writes closer together than the")
    print("  skew can still be reordered. Tightening the clocks pushes the problem into")
    print("  the corner of near-concurrent writes. It never promises to remove it,")
    print("  because you cannot promise skew is smaller than EVERY gap.")
    return loss_at_focus


def part3(writes):
    print("\n" + "=" * 78)
    print("Part 3: the real fix. Stop ordering cross-machine events by the wall clock")
    print("=" * 78)
    print("  The resolution rule was never the problem. Keeping the larger value is")
    print("  fine. The problem is what we fed it: a wall-clock stamp that means")
    print("  different things on different machines. So feed it something else.")
    print()
    pct = logical_loss_pct(writes)
    print(f"  Replay the SAME {N_WRITES:,} writes, at the same {HEADLINE_SKEW} ms of skew, but order")
    print("  them by a logical version (each write takes the next number up from the")
    print("  one it replaces) instead of a timestamp:")
    print(f"    newer writes silently lost = {pct:.1f}%")
    print()
    print("  Zero. A logical clock never reads the time of day, so no amount of skew can")
    print("  reorder two writes that truly follow one another. What used to be a silent")
    print("  loss becomes either a correct ordering (if the writes are causally related)")
    print("  or, for writes that really were concurrent, a conflict a version vector can")
    print("  DETECT and hand to the application, instead of a value that just disappears.")
    print("  That is Day 33: Lamport clocks and version vectors.")
    print()
    print("  Two other honest fixes:")
    print("    - A dedicated time service with BOUNDED uncertainty. Google's Spanner")
    print("      reads a clock that tells it 'the real time is within these bounds' and")
    print("      simply waits out the uncertainty before committing. It made the bound")
    print("      small with GPS and atomic clocks in every data centre, which is both")
    print("      brilliant and slightly mad.")
    print("    - Single-writer ordering: route all writes for a key through one leader,")
    print("      so there is one clock and one order, no cross-machine comparison at all.")
    print()
    print("  And the eight fallacies of distributed computing, the list everyone")
    print("  rediscovers the hard way: the network is reliable; latency is zero;")
    print("  bandwidth is infinite; the network is secure; topology never changes;")
    print("  there is one administrator; transport cost is zero; the network is")
    print("  homogeneous. Today's clock-skew bug is their close cousin: time is not")
    print("  global either. Assume none of these and you will not be surprised.")
    return pct


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>7.2f} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    if diff <= 3.0 or (predicted > 0 and 0.6 <= actual / predicted <= 1.7):
        note = "     close enough"
    elif actual > predicted:
        note = "   too LOW (reality is worse)"
    else:
        note = "   too HIGH (reality is kinder)"
    print(f"  {name:<34} you = {predicted:>6.2f}   actual = {actual:>7.2f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    writes = make_stream(N_WRITES, MEAN_GAP_MS, SEED)

    loss_200, threshold = part1(writes)
    loss_ntp = part2(writes)
    loss_logical = part3(writes)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 LWW loss at 200 ms skew", PREDICTIONS["lww_loss_at_200ms_pct"], loss_200, "%")
    verdict("P2 loss threshold vs gap", PREDICTIONS["loss_threshold_ms"], threshold, "ms")
    verdict("P3 LWW loss at 2 ms (NTP)", PREDICTIONS["lww_loss_at_ntp_2ms_pct"], loss_ntp, "%")
    verdict("P4 logical-clock loss", PREDICTIONS["logical_loss_pct"], loss_logical, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  A single node whose clock ran {HEADLINE_SKEW} ms ahead made last-write-wins")
    print(f"  silently drop {loss_200:.0f}% of the newer writes to a hot key. For a fixed gap")
    print(f"  the loss is zero only while the skew stays under that gap ({threshold:.0f} ms here);")
    print("  past it, the newer write loses. NTP shrank the loss to a fraction of a")
    print(f"  percent ({loss_ntp:.2f}% at 2 ms) but never to a guaranteed zero. Ordering by a")
    print(f"  logical version instead of the wall clock took it to {loss_logical:.0f}%. The lesson:")
    print("  never trust the wall clock to order events across machines.")
    print()


if __name__ == "__main__":
    main()
