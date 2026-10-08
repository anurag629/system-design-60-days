"""
Day 48 lab: cost and capacity planning. The arithmetic that tells you whether a
design is affordable BEFORE you build it.

Run it:      python3 cost_model.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only, no network, no files, runs in a few seconds. If you get
stuck, the full working version is solution.py in this folder.

The story, in three parts:
  Part 1, capacity. Little's Law (Day 4): requests in flight at peak = arrival
    rate times service time. Spread that concurrency across worker slots so each
    is only 70% busy (Day 4's cliff), then add a spare so losing one still holds
    the peak (Day 6, N minus 1). A slower request needs more servers, in
    proportion. Then a seeded simulation checks the sizing under failures.
  Part 2, the monthly bill. compute + storage + egress, with realistic cloud
    rates. Find the DOMINANT line, because teams reliably pour effort into the
    cheap one.
  Part 3, a lever. Put a CDN in front so static bytes leave the edge, not the
    origin (Day 20), and recompute. One lever on the big line beats a bigger
    effort on a small one.

The number to carry: the servers you need at a 70% target, the monthly bill and
which line dominates it, and the saving from one well-aimed lever.
"""

import heapq
import math
import random
import sys

PREDICTIONS = {
    # P1: how many servers to carry the peak of 8,000 requests/second, each
    #     needing 20 ms of work, sized for 70% busy with one spare for N minus 1?
    "servers_at_70pct": None,

    # P2: the whole monthly bill, in dollars (compute + storage + egress).
    "monthly_bill_usd": None,

    # P3: the single biggest line item's share of that bill, as a percent.
    "dominant_line_pct": None,

    # P4: percent of the bill a CDN on the dominant line removes.
    "cdn_saving_pct": None,
}

# ---------------------------------------------------------------------------
# The design we are costing. One realistic read-heavy web service.
# ---------------------------------------------------------------------------
PEAK_RPS = 8_000             # requests per second at the busiest minute
SERVICE_TIME_MS = 20         # work per request, on one worker slot
CORES_PER_SERVER = 8         # worker slots per instance (an 8 vCPU box)
TARGET_UTIL = 0.70           # size for 70% busy, not 100% (Day 4's cliff)
REDUNDANCY_SERVERS = 1       # one spare so losing a server still holds peak
STORAGE_GB = 20_000          # 20 TB of primary data (DB + object store)
EGRESS_GB = 200_000          # 200 TB/month served out to users

# Realistic-ish cloud rates (AWS list, late 2024 ballpark). Stated, not hidden,
# because every capacity argument is only as honest as its rate card.
COMPUTE_PER_HOUR = 0.34      # 8 vCPU general-purpose instance, on-demand $/hr
HOURS_PER_MONTH = 730        # the cloud convention: 24 * 365 / 12
STORAGE_PER_GB = 0.08        # SSD-backed primary storage, $/GB-month
EGRESS_PER_GB = 0.09         # origin data transfer out to the internet, $/GB
CDN_EGRESS_PER_GB = 0.06     # CDN egress, blended over volume tiers, $/GB
RESERVED_DISCOUNT = 0.35     # a 1 yr commit knocks ~35% off compute (contrast)

SIM_REQUESTS = 120_000       # requests per simulated scenario; keeps it quick
SEED = 48


# ---------------------------------------------------------------------------
# The four TODOs. Each is one load-bearing line of the cost model.
# ---------------------------------------------------------------------------

def concurrency(peak_rps, service_time_s):
    """TODO 1, Little's Law. The average number of requests in flight is the
    arrival rate times how long each one spends in the system. That in-flight
    count is the concurrency the whole fleet has to carry at once."""
    # TODO 1 ------------------------------------------------------------------
    # Little's Law, L = lambda * W. Here lambda is peak_rps and W is the service
    # time in seconds. One line:
    #     return peak_rps * service_time_s
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def servers_needed(conc, cores_per_server, target_util, redundancy):
    """TODO 2, size the fleet. Spread the concurrency across worker slots so each
    slot is only `target_util` busy (the Day 4 headroom), turn slots into whole
    servers, then add spares so losing one still holds the peak (Day 6)."""
    # TODO 2 ------------------------------------------------------------------
    # First, how many slots do we need so each is only target_util busy? That is
    # conc / target_util. Then turn slots into whole servers (round UP, you
    # cannot buy a third of a box) and add the redundancy spares:
    #     slots = conc / target_util
    #     return math.ceil(slots / cores_per_server) + redundancy
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def egress_cost(egress_gb, rate_per_gb):
    """TODO 3, the egress line. Bytes out times the per-GB rate. Keep an eye on
    this one: it is the line teams forget, and the one that usually dominates."""
    # TODO 3 ------------------------------------------------------------------
    # The simplest line on the bill, and the biggest. Bytes going out to users
    # times the per-GB egress rate:
    #     return egress_gb * rate_per_gb
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def saving_pct(before, after):
    """TODO 4, the lever's payoff. How much of the old bill did it remove, as a
    percent of the original total."""
    # TODO 4 ------------------------------------------------------------------
    # The money removed, as a share of the ORIGINAL bill (so a 22% saving reads
    # as 22, not as a fraction of the smaller new bill):
    #     return (before - after) / before * 100.0
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if concurrency(100, 0.01) is None:
        return 1
    if servers_needed(1.0, 8, 0.7, 1) is None:
        return 2
    if egress_cost(10, 0.09) is None:
        return 3
    if saving_pct(100.0, 80.0) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# A seeded queue simulation, so we can MEASURE that the sizing holds up.
# One shared queue, `slots` identical workers, Poisson arrivals, exponential
# service times. Event-driven, no threads, deterministic for a fixed seed.
# ---------------------------------------------------------------------------

def simulate_fleet(peak_rps, service_mean_s, slots, n_requests, seed):
    """Push n_requests through `slots` workers sharing one queue and measure what
    actually happens. Returns (utilisation, mean_latency_x, p99_latency_x), where
    the two latencies are in multiples of the mean service time (1.0x means a
    request spent no time waiting, just being served)."""
    rng = random.Random(seed)
    free = [0.0] * slots                 # each worker's next-free time, a heap
    arrival = 0.0
    busy_time = 0.0
    last_finish = 0.0
    latencies = []
    for _ in range(n_requests):
        arrival += rng.expovariate(peak_rps)          # Poisson arrivals
        soonest = heapq.heappop(free)                 # worker that frees first
        start = arrival if arrival >= soonest else soonest
        service = rng.expovariate(1.0 / service_mean_s)
        finish = start + service
        heapq.heappush(free, finish)
        busy_time += service
        latencies.append((finish - arrival) / service_mean_s)
        if finish > last_finish:
            last_finish = finish
    util = busy_time / (slots * last_finish)
    latencies.sort()
    mean_x = sum(latencies) / len(latencies)
    p99_x = latencies[int(len(latencies) * 0.99)]
    return util, mean_x, p99_x


def fleet_note(util, mean_x):
    """A plain-words verdict on a simulated scenario. Mean latency is the honest
    overload signal: utilisation can only ever read up to 100%, but a queue that
    is genuinely over capacity shows up as the mean climbing without bound."""
    if mean_x > 6:
        return "OVERLOAD, queue runs away"
    if util >= 0.97:
        return "at the wall, no margin"
    if util >= 0.85:
        return "hot, little margin"
    return "comfortable"


# ---------------------------------------------------------------------------
# Part 1: capacity. How many servers, and why not 100% busy.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: capacity. Turn a request rate into a server count.")
    print("=" * 78)

    service_s = SERVICE_TIME_MS / 1000.0
    conc = concurrency(PEAK_RPS, service_s)
    if conc is None:
        print("  (fill in TODO 1)")
        return None

    print(f"  peak traffic:        {PEAK_RPS:,} requests/second")
    print(f"  work per request:    {SERVICE_TIME_MS} ms on one worker slot")
    print(f"  slots per server:    {CORES_PER_SERVER}")
    print()
    print(f"  Little's Law: requests in flight at peak = {PEAK_RPS:,} x "
          f"{service_s:.3f}s = {conc:.0f}.")
    print(f"  So at any instant about {conc:.0f} requests are being worked on. That")
    print("  concurrency, not the request rate, is what the fleet has to carry.")

    if servers_needed(conc, CORES_PER_SERVER, TARGET_UTIL, 0) is None:
        print("  (fill in TODO 2)")
        return None

    at_100 = math.ceil(conc / CORES_PER_SERVER)           # flat out, no headroom
    at_70 = servers_needed(conc, CORES_PER_SERVER, TARGET_UTIL, 0)
    final = servers_needed(conc, CORES_PER_SERVER, TARGET_UTIL, REDUNDANCY_SERVERS)
    headroom_pct = (at_70 / at_100 - 1) * 100

    print()
    print("  Sizing the fleet:")
    print(f"    at 100% busy (no headroom):  {at_100} servers   <- the cliff edge")
    print(f"    at {int(TARGET_UTIL * 100)}% busy (Day 4 headroom): {at_70} servers   "
          f"<- {headroom_pct:.0f}% more, to stay off the cliff")
    print(f"    plus {REDUNDANCY_SERVERS} spare for N-1 (Day 6):  {final} servers   "
          f"<- lose one, still holds peak")
    print()
    print(f"  The {at_70 - at_100} extra servers past the bare 100% figure are not waste.")
    print("  They are the room random bursts need so latency does not fall off")
    print("  Day 4's cliff, plus one spare so a dead instance is a shrug, not an")
    print("  incident. Running flat out to save money is how you pay for it later.")

    # A slower request needs proportionally more servers. Little's Law again.
    print()
    print("  If each request gets slower (say the database slows down), the")
    print("  concurrency rises in lockstep, and so does the server count:")
    print(f"    {'service time':<14}{'in flight':>11}{'servers (70% + spare)':>24}")
    for ms in (20, 25, 30, 40):
        c = concurrency(PEAK_RPS, ms / 1000.0)
        s = servers_needed(c, CORES_PER_SERVER, TARGET_UTIL, REDUNDANCY_SERVERS)
        print(f"    {str(ms) + ' ms':<14}{c:>11.0f}{s:>24}")
    print("  Double the work per request and you roughly double the fleet, at the")
    print("  same traffic. A slow dependency is a capacity problem wearing a")
    print("  latency costume, and the bill feels it directly.")

    # Now MEASURE it. Does a 70%-sized fleet really ride out a failure, and does
    # a fleet run hot to save money really tip over?
    print()
    print("  Does the headroom earn its keep? Simulate the peak hour and start")
    print("  killing servers. Latency is in multiples of the 20 ms service time.")
    hot = servers_needed(conc, CORES_PER_SERVER, 0.95, 0)   # ran hot, no spare
    print(f"    (healthy fleet = {final} servers at 70% + spare;  "
          f"hot fleet = {hot} servers at 95%, no spare)")
    print(f"    {'scenario':<34}{'util':>7}{'mean':>8}{'p99':>8}  note")
    scenarios = [
        (f"healthy, all {final} up", final, 0),
        (f"healthy, 1 down ({final - 1} up)", final, 1),
        (f"healthy, 3 down ({final - 3} up)", final, 3),
        (f"hot, all {hot} up", hot, 0),
        (f"hot, 1 down ({hot - 1} up)", hot, 1),
        (f"hot, 2 down ({hot - 2} up)", hot, 2),
        (f"hot, 3 down ({hot - 3} up)", hot, 3),
    ]
    for label, servers, dead in scenarios:
        slots = (servers - dead) * CORES_PER_SERVER
        util, mean_x, p99_x = simulate_fleet(
            PEAK_RPS, service_s, slots, SIM_REQUESTS, SEED + servers * 10 + dead)
        print(f"    {label:<34}{util * 100:>6.0f}%{mean_x:>7.1f}x"
              f"{p99_x:>7.1f}x  {fleet_note(util, mean_x)}")
    print("  With this many pooled servers the cliff is gentler than one lonely")
    print("  box (sharing a queue buys tolerance, the Day 4 result), so read the")
    print("  trend, not one row. The healthy fleet never leaves the comfort zone,")
    print("  even three servers down. The hot fleet looked cheaper on the")
    print("  spreadsheet, then climbed 90 to 94 to 99% as servers died, and once")
    print("  it was genuinely over capacity the mean latency ran away. That gap")
    print("  between the two tables is exactly what the 70% target buys you.")
    return final


# ---------------------------------------------------------------------------
# Part 2: the monthly bill, and the line that dominates it.
# ---------------------------------------------------------------------------

def part2(servers):
    print("\n" + "=" * 78)
    print("Part 2: the monthly bill. Three lines, and one of them is most of it.")
    print("=" * 78)

    compute = servers * COMPUTE_PER_HOUR * HOURS_PER_MONTH
    storage = STORAGE_GB * STORAGE_PER_GB
    egress = egress_cost(EGRESS_GB, EGRESS_PER_GB)
    if egress is None:
        print("  (fill in TODO 3)")
        return None
    total = compute + storage + egress

    print(f"  rates: compute ${COMPUTE_PER_HOUR}/hr x {HOURS_PER_MONTH} hrs, "
          f"storage ${STORAGE_PER_GB}/GB, egress ${EGRESS_PER_GB}/GB")
    print()
    lines = [
        ("compute", f"{servers} servers x ${COMPUTE_PER_HOUR}/hr x {HOURS_PER_MONTH}h", compute),
        ("storage", f"{STORAGE_GB:,} GB x ${STORAGE_PER_GB}", storage),
        ("egress", f"{EGRESS_GB:,} GB out x ${EGRESS_PER_GB}", egress),
    ]
    print(f"  {'line':<10}{'how':<34}{'per month':>14}{'share':>9}")
    for name, how, amount in lines:
        print(f"  {name:<10}{how:<34}{'$' + format(amount, ',.0f'):>14}"
              f"{amount / total * 100:>8.0f}%")
    print(f"  {'':<10}{'TOTAL':<34}{'$' + format(total, ',.0f'):>14}{'100%':>9}")

    dominant_name, _, dominant_amount = max(lines, key=lambda x: x[2])
    dominant_share = dominant_amount / total * 100
    print()
    print(f"  The dominant line is {dominant_name.upper()} at {dominant_share:.0f}% of the bill.")
    print("  Notice the shape. Storage, the line everyone frets about, is the")
    print("  smallest. Compute is the one teams spend weeks right-sizing. And the")
    print("  real monster is egress, the bytes going out to users, which rarely")
    print("  gets a second look because there is no server to point at. Cost work")
    print("  that ignores the biggest line is theatre.")
    return total, dominant_share, compute, storage, egress


# ---------------------------------------------------------------------------
# Part 3: one lever, aimed at the dominant line.
# ---------------------------------------------------------------------------

def part3(before, compute, storage, egress):
    print("\n" + "=" * 78)
    print("Part 3: a lever. Aim it at the dominant line, not the comfortable one.")
    print("=" * 78)

    # The lever: a CDN in front, so static bytes leave the edge, not the origin.
    # Origin-to-CDN transfer is free within the cloud, and CDN egress is cheaper
    # at volume, so the whole egress line reprices (Day 20).
    egress_cdn = egress_cost(EGRESS_GB, CDN_EGRESS_PER_GB)
    total_cdn = compute + storage + egress_cdn
    cdn_pct = saving_pct(before, total_cdn)
    if cdn_pct is None:
        print("  (fill in TODO 4)")
        return None

    # The contrast lever: commit to reserved instances, ~35% off compute.
    compute_ri = compute * (1 - RESERVED_DISCOUNT)
    total_ri = compute_ri + storage + egress
    ri_pct = saving_pct(before, total_ri)

    print("  Lever: put a CDN in front (Day 20). The static bytes now leave the")
    print("  CDN edge, origin-to-CDN transfer is free, and edge egress is cheaper")
    print(f"  at volume, so the egress line reprices from ${EGRESS_PER_GB} to "
          f"${CDN_EGRESS_PER_GB} per GB.")
    print()
    print(f"    egress before:  ${egress:>10,.0f}")
    print(f"    egress after:   ${egress_cdn:>10,.0f}")
    print(f"    bill before:    ${before:>10,.0f}")
    print(f"    bill after:     ${total_cdn:>10,.0f}")
    print(f"    saved:          ${before - total_cdn:>10,.0f}   "
          f"= {cdn_pct:.1f}% of the whole bill")
    print()
    print("  Now the lever teams usually reach for first, on the comfortable line:")
    print(f"    reserved instances, {int(RESERVED_DISCOUNT * 100)}% off compute -> "
          f"saves ${before - total_ri:,.0f} = {ri_pct:.1f}% of the bill")
    print()
    print(f"  The CDN saved {cdn_pct:.1f}% and the compute commit saved {ri_pct:.1f}%, "
          f"roughly {cdn_pct / ri_pct:.1f}x as")
    print("  much, for comparable effort. Both are worth doing. But the order")
    print("  matters: you get the big money by pulling the lever on the line that")
    print("  is actually big, and only egress was ever going to move this bill.")
    return cdn_pct


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>10,.1f} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    note = "     close enough" if diff <= max(3.0, 0.1 * abs(predicted)) \
        else f"  off by {diff:,.1f}"
    print(f"  {name:<30} you = {predicted:>9,.1f}   actual = {actual:>10,.1f} "
          f"{unit}  {note}")


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

    servers = part1()
    if servers is None:
        sys.exit(1)

    res2 = part2(servers)
    if res2 is None:
        sys.exit(1)
    total, dominant_share, compute, storage, egress = res2

    cdn_pct = part3(total, compute, storage, egress)
    if cdn_pct is None:
        sys.exit(1)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 servers at 70% + spare", PREDICTIONS["servers_at_70pct"], servers)
    verdict("P2 monthly bill", PREDICTIONS["monthly_bill_usd"], total, "$")
    verdict("P3 dominant line share", PREDICTIONS["dominant_line_pct"], dominant_share, "%")
    verdict("P4 CDN saving", PREDICTIONS["cdn_saving_pct"], cdn_pct, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  {PEAK_RPS:,} rps at {SERVICE_TIME_MS} ms each needs {servers} servers once you size")
    print(f"  for 70% busy and keep one spare. That design costs ${total:,.0f} a month,")
    print(f"  and egress is {dominant_share:.0f}% of it, not the compute everyone stares at.")
    print(f"  One CDN on that dominant line takes {cdn_pct:.0f}% off the bill. Capacity and")
    print("  cost are the same arithmetic read twice: Little's Law sets the server")
    print("  count, the server count plus the rate card sets the bill, and the")
    print("  biggest line is where the savings live. A design you cannot cost is")
    print("  a design you cannot defend.")
    print()


if __name__ == "__main__":
    main()
