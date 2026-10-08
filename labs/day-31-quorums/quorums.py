"""
Day 31 lab: replication and quorums, Dynamo style. N replicas, write to W,
read from R, and the one inequality that decides whether a read is guaranteed
to see the latest completed write: R + W > N.

Run it:      python3 quorums.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only, no network, no threads, no files. Everything is a
deterministic simulation. A logical version clock advances one step per write,
so "newest" just means "highest version", and every random choice (which
replicas a write lands on, which replicas a read asks, which replicas are up)
comes from a seeded RNG, so the run is reproducible to the digit.

The big ideas:
  - A write lands on W replicas and carries a new, higher version. A read asks R
    replicas and keeps the newest version it saw. The read is fresh only if its
    R replicas overlap the W that took the latest write.
  - R + W > N forces that overlap. Any R replicas and any W replicas, drawn from
    the same N, must share at least one once R + W > N (pigeonhole). So a read is
    guaranteed to see the latest completed write. Strong, 100 percent of reads.
  - R + W <= N drops the guarantee. The read set and the write set can now be
    disjoint, and a measurable fraction of reads come back stale.
  - You tune W and R on the same N. W=1, R=N makes writes cheap and reads
    fragile. W=N, R=1 is the mirror. W = R = N/2 + 1 is the balanced middle that
    survives the most failures. Quorums stay available as long as W (or R) can
    still be gathered from the live replicas, and read-repair heals the laggards
    later.

If you get stuck, the full working version is solution.py in this folder.
"""

import random
import sys
from math import comb

PREDICTIONS = {
    # P1: strong quorum, N=5, W=3, R=3 (R+W = 6 > 5). Out of every 100 reads,
    #     how many see the LATEST completed write?
    "strong_sees_latest_pct": None,

    # P2: weak quorum, N=3, W=1, R=1 (R+W = 2 <= 3). What percent of reads come
    #     back STALE, i.e. miss the latest write?
    "weak_stale_n3_pct": None,

    # P3: weak quorum, N=5, W=2, R=2 (R+W = 4 <= 5). Percent of STALE reads.
    "weak_stale_n5_pct": None,

    # P4: balanced W = R = 3 on N=5, each replica independently down 10% of the
    #     time. What percent of operations (reads AND writes) can still be served?
    "balanced_availability_pct": None,
}

N_SMALL = 3          # the small cluster for the classic W=1, R=1 demo
N = 5                # the main cluster
TRIALS = 50_000      # trials per measurement; keeps the whole run a few seconds
DOWN_PROB = 0.10     # per-replica chance of being down at any instant (Part 3)
SEED = 31


# ---------------------------------------------------------------------------
# The four TODOs: the heart of a quorum. Each is one load-bearing line.
# ---------------------------------------------------------------------------

def choose_write_targets(rng, up, w):
    """TODO 1, the write side. Pick W replicas (from the ones that are up) to
    receive this write."""
    # TODO 1 ------------------------------------------------------------------
    # Dynamo's coordinator sends the write to the replicas and keeps the first W
    # that acknowledge. Model that as a random W of the live set `up`. `rng` is a
    # seeded random.Random, so use rng.sample (not the global random) to stay
    # reproducible:
    #     return rng.sample(up, w)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def newest_version(responders, versions):
    """TODO 2, the read side. R replicas answered; versions[i] is the version
    each one holds. A quorum read keeps the NEWEST version it saw."""
    # TODO 2 ------------------------------------------------------------------
    # `responders` is the list of replica indexes that answered this read.
    # `versions[i]` is the version replica i currently holds. Newest = highest
    # version among the responders:
    #     return max(versions[i] for i in responders)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def is_strong(n, w, r):
    """TODO 3, the whole trick in one line. A read set of R and a write set of W
    drawn from N replicas are guaranteed to overlap, so a read always sees the
    latest write, exactly when R + W is strictly greater than N."""
    # TODO 3 ------------------------------------------------------------------
    # This is the headline of the whole day. Strong (guaranteed overlap) exactly
    # when R + W is strictly greater than N:
    #     return (r + w) > n
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def can_serve(up_count, needed):
    """TODO 4, availability. An operation that needs `needed` replicas (W for a
    write, R for a read) can complete only if at least that many are up."""
    # TODO 4 ------------------------------------------------------------------
    # A write needs W replicas up, a read needs R. The operation can be served
    # only if the number of live replicas is at least what it needs:
    #     return up_count >= needed
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    rng = random.Random(0)
    if choose_write_targets(rng, [0, 1, 2], 2) is None:
        return 1
    if newest_version([0, 1], [5, 3, 0]) is None:
        return 2
    if is_strong(5, 3, 3) is None:
        return 3
    if can_serve(4, 3) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# The store: N replicas, each holding a (version, value).
# ---------------------------------------------------------------------------

class QuorumStore:
    """N replicas, each holding a (version, value). A logical clock gives each
    write a new, strictly higher version, so the newest write is simply the
    highest version anywhere. That clock is the simulated time in this lab: it
    advances one step per write, nothing runs in real seconds."""

    def __init__(self, n, rng):
        self.n = n
        self.rng = rng
        self.versions = [0] * n
        self.values = [None] * n
        self.clock = 0

    def write(self, value, w, up):
        """Coordinator writes a new version to W of the live replicas. Returns
        the version written, or None if W live replicas cannot be gathered."""
        if not can_serve(len(up), w):
            return None
        self.clock += 1
        v = self.clock
        for i in choose_write_targets(self.rng, up, w):
            self.versions[i] = v
            self.values[i] = value
        return v

    def read(self, r, up, repair=False):
        """Coordinator reads from R live replicas and keeps the newest version.
        Returns that version, or None if R live replicas cannot be gathered.
        With repair=True it pushes the newest version back onto any stale
        responder it saw (read-repair)."""
        if not can_serve(len(up), r):
            return None
        responders = self.rng.sample(up, r)
        newest = newest_version(responders, self.versions)
        if repair:
            source = max(responders, key=lambda i: self.versions[i])
            val = self.values[source]
            for i in responders:
                if self.versions[i] < newest:
                    self.versions[i] = newest
                    self.values[i] = val
        return newest


def measure_consistency(n, w, r, trials, seed):
    """Write a fresh version, then immediately read it back, many times, with
    every replica up. Count how often the read sees that latest write. Returns
    (sees_latest_pct, stale_pct)."""
    rng = random.Random(seed)
    store = QuorumStore(n, rng)
    up = list(range(n))
    stale = 0
    for _ in range(trials):
        v = store.write("x", w, up)
        got = store.read(r, up)
        if got < v:
            stale += 1
    stale_pct = stale / trials * 100
    return 100 - stale_pct, stale_pct


def theory_stale_pct(n, w, r):
    """The exact odds a random R-read misses a fixed W-write: pick all R readers
    from the N-W replicas that did not get the write. Zero once R + W > N."""
    if n - w < r:
        return 0.0
    return comb(n - w, r) / comb(n, r) * 100


def measure_availability(n, w, r, trials, seed, down_prob):
    """Each trial, flip every replica up or down independently, then ask whether
    a write (needs W up) and a read (needs R up) could be served. Returns
    (write_avail_pct, read_avail_pct, both_avail_pct)."""
    rng = random.Random(seed)
    writes_ok = reads_ok = both_ok = 0
    for _ in range(trials):
        up_count = sum(1 for _ in range(n) if rng.random() >= down_prob)
        w_ok = can_serve(up_count, w)
        r_ok = can_serve(up_count, r)
        writes_ok += w_ok
        reads_ok += r_ok
        both_ok += (w_ok and r_ok)
    return (writes_ok / trials * 100,
            reads_ok / trials * 100,
            both_ok / trials * 100)


# ---------------------------------------------------------------------------
# The three parts.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: R + W > N. The read set and the write set must overlap, so")
    print("        every read sees the latest write")
    print("=" * 78)
    print(f"  N = {N} replicas. Each write lands on W of them with a new version.")
    print("  Each read asks R of them and keeps the newest version it sees.")
    print()
    print(f"  {'config':<16}{'R+W':>5}{'overlap?':>10}{'sees latest':>14}{'theory':>10}")
    headline = None
    for w, r in [(3, 3), (4, 2), (1, 5), (5, 1)]:
        sees, _ = measure_consistency(N, w, r, TRIALS, SEED + w * 10 + r)
        theory_sees = 100 - theory_stale_pct(N, w, r)
        tag = "yes" if is_strong(N, w, r) else "no"
        print(f"  W={w}, R={r}         {w + r:>5}{tag:>10}"
              f"{sees:>13.1f}%{theory_sees:>9.1f}%")
        if (w, r) == (3, 3):
            headline = sees
    print()
    print("  Every row has R + W > N, so the R replicas a read asks can never")
    print("  completely miss the W that took the write. At least one replica sits")
    print("  in both sets, and it carries the newest version. 100 percent fresh,")
    print("  and not by luck: the overlap is forced by counting.")
    return headline


def part2():
    print("\n" + "=" * 78)
    print("Part 2: R + W <= N. Break the overlap, and reads start missing writes")
    print("=" * 78)
    print(f"  The classic Dynamo-fast setting: N={N_SMALL}, W=1, R=1. A write touches")
    print("  one replica, a read asks one replica, and R + W = 2 is not above 3.")
    print()
    _, stale_n3 = measure_consistency(N_SMALL, 1, 1, TRIALS, SEED + 777)
    theory = theory_stale_pct(N_SMALL, 1, 1)
    print(f"  N={N_SMALL}, W=1, R=1:   {stale_n3:.1f}% of reads are STALE "
          f"(theory {theory:.1f}%)")
    print("  Two times in three the one replica you read is not the one the write")
    print("  touched, so you get an older version. That is the cost of R + W <= N:")
    print("  no overlap guarantee, measurable staleness.")
    print()
    print(f"  Same story on N={N}, swept across weak settings (R + W <= {N}):")
    print(f"  {'config':<16}{'R+W':>5}{'stale':>10}{'theory':>10}")
    stale_n5_22 = None
    for w, r in [(1, 1), (2, 2), (1, 4), (2, 3)]:
        _, stale = measure_consistency(N, w, r, TRIALS, SEED + w * 100 + r)
        theory = theory_stale_pct(N, w, r)
        print(f"  W={w}, R={r}         {w + r:>5}{stale:>9.1f}%{theory:>9.1f}%")
        if (w, r) == (2, 2):
            stale_n5_22 = stale
    print()
    print("  The fewer replicas a write and a read touch between them, the wider")
    print("  the gap they can slip past each other through. Push W + R back above")
    print("  N and the gap shuts completely.")
    return stale_n3, stale_n5_22


def part3():
    print("\n" + "=" * 78)
    print("Part 3: tuning W and R on the same N, and what each setting trades")
    print("=" * 78)
    print(f"  N = {N}. All three settings below keep R + W > {N}, so all three give")
    print("  fresh reads. What changes is where the cost and the fragility land.")
    print(f"  Each replica is independently down {int(DOWN_PROB * 100)}% of the time.")
    print()
    print(f"  {'setting':<14}{'W':>3}{'R':>3}{'write avail':>14}"
          f"{'read avail':>12}{'both':>8}")
    balanced_both = None
    bal = N // 2 + 1
    for name, w, r in [("write-heavy", 1, N),
                       ("read-heavy", N, 1),
                       ("balanced", bal, bal)]:
        wa, ra, both = measure_availability(N, w, r, TRIALS, SEED + w + r, DOWN_PROB)
        print(f"  {name:<14}{w:>3}{r:>3}{wa:>13.2f}%{ra:>11.2f}%{both:>7.2f}%")
        if name == "balanced":
            balanced_both = both
    print()
    print("  write-heavy (W=1): a write waits for a single ack, so writes almost")
    print("    never block. But R=N means a read needs ALL replicas, so one dead")
    print("    replica takes reads down. Cheap durable writes, brittle reads.")
    print("  read-heavy (W=N): the mirror. Reads fly on R=1, but one dead replica")
    print("    stalls every write.")
    print(f"  balanced (W=R={bal}): both pay a medium cost, and both survive the most")
    print(f"    failures, {N - bal} replicas down, for reads and for writes alike.")
    print("  Same N, three bets. This knob is what Dynamo hands the operator.")
    return balanced_both


def part3_read_repair():
    print()
    print("  Read-repair: healing the laggards as a side effect of reading.")
    rng = random.Random(SEED + 999)
    store = QuorumStore(N, rng)
    up = list(range(N))
    v = store.write("fresh", 1, up)          # a weak write: newest on ONE replica
    behind = sum(1 for ver in store.versions if ver < v)
    print(f"    wrote the newest version to 1 of {N} replicas; {behind} are behind.")
    reads = 0
    while any(ver < v for ver in store.versions) and reads < 100:
        store.read(3, up, repair=True)       # R=3 reads that repair as they go
        reads += 1
    behind_after = sum(1 for ver in store.versions if ver < v)
    print(f"    after {reads} repaired reads, replicas still behind: {behind_after}.")
    print("    A read does double duty: it answers the client AND pushes the")
    print("    newest version onto any stale replica it touched, so the cluster")
    print("    converges even though the write only reached W. That is how a")
    print("    Dynamo store runs on a low W, stays available, and still heals")
    print("    toward agreement. Anti-entropy and hinted handoff finish the job")
    print("    for replicas no read happened to touch.")


def verdict(name, predicted, actual, unit="%"):
    if predicted is None:
        print(f"  {name:<32} actual = {actual:>7.1f} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    note = "     close enough" if diff <= max(3.0, 0.1 * abs(predicted)) \
        else f"  off by {diff:.1f}"
    print(f"  {name:<32} you = {predicted:>6.1f}   actual = {actual:>7.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The guess is the point, so make it first.\n")
        sys.exit(1)

    missing = first_blank_todo()
    if missing:
        print(f"\n  !! TODO {missing} is still blank. Fill in the four numbered")
        print("     TODOs, then run again. Nothing below works until each one")
        print(f"     returns a real value. Start with TODO {missing}.\n")
        sys.exit(0)

    p1 = part1()
    p2_n3, p2_n5 = part2()
    p4 = part3()
    part3_read_repair()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 strong W3R3 sees latest", PREDICTIONS["strong_sees_latest_pct"], p1)
    verdict("P2 weak N=3 W1R1 stale", PREDICTIONS["weak_stale_n3_pct"], p2_n3)
    verdict("P3 weak N=5 W2R2 stale", PREDICTIONS["weak_stale_n5_pct"], p2_n5)
    verdict("P4 balanced availability", PREDICTIONS["balanced_availability_pct"], p4)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  With R + W > N, every read overlapped the latest write: {p1:.0f}% fresh,")
    print(f"  no exceptions. Drop to R + W <= N and the floor falls out: {p2_n3:.0f}% of")
    print(f"  reads on N={N_SMALL}, W=1, R=1 came back stale. The overlap is the whole")
    print("  trick. You tune W and R to shift cost between reads and writes, but")
    print("  the instant R + W stops exceeding N you have swapped a strong read")
    print("  for a faster one.")
    print()


if __name__ == "__main__":
    main()
