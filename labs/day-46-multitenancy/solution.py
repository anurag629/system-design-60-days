"""
Day 46 lab: multi-tenancy and isolation. One shared resource, several tenants,
and the one greedy tenant who ruins it for everyone (the noisy neighbour). Then
the two fixes that give the quiet tenants their fair share back.

This is the full working solution. The starter file is multitenancy.py.
Run it:      python3 solution.py

Standard library only. No network, no threads, no files, nothing to clean up.
Everything is a deterministic simulation: constant per-tick demand, so the run is
reproducible to the digit. A "tick" is one second of a shared service that can
handle CAPACITY requests per tick. We step through many ticks and add up what
each tenant actually got served.

The model, in one breath: a shared resource serves CAPACITY requests per tick.
When the tenants together ask for more than that, something has to give. WHO it
takes it from is the whole lesson.

The big ideas:
  - Shared everything, no limits. When the pool is overloaded, a shared first
    come first served queue serves each tenant in rough proportion to how much
    it asked for. So the tenant that floods the hardest gets the biggest slice,
    and the well-behaved tenants are starved. That is the noisy neighbour: one
    greedy tenant, and everyone else's throughput collapses.
  - Per-tenant quota. Put a rate limiter (a token bucket, Day 45) in front of
    each tenant at its fair share. The greedy tenant is capped at its share and
    the rest of its flood is rejected at the door, so it never reaches the shared
    pool. The pool is no longer overloaded, and the quiet tenants get their full
    share back. Simple and predictable, but it is not work conserving: a tenant's
    unused share is wasted rather than lent out.
  - Fair-share scheduling. Serve the shared capacity by max-min fairness instead
    of a hard cap. Every tenant is guaranteed its fair share whenever it wants
    it, and whatever is left over is handed to whoever is still hungry. So the
    greedy tenant can still soak up genuinely idle capacity (work conserving)
    but can never take it from a tenant that wants it.
  - The isolation spectrum. Shared everything is cheapest and has the worst
    isolation. Shared with per-tenant quotas is the usual middle. Dedicated
    resources per tenant give the best isolation and cost the most, because idle
    capacity in one tenant's box cannot help another. That cost is Day 48.
"""

import sys

PREDICTIONS = {
    # P1: the flood, NO isolation. A well-behaved tenant asks for its fair share
    #     of 20 req/tick. The greedy tenant floods the shared pool with 600. How
    #     many requests per tick does the WELL-BEHAVED tenant actually get served?
    "quiet_tput_no_isolation": 3.4,

    # P2: same flood, no isolation. How many req/tick does the GREEDY tenant get
    #     served? (Capacity is 120. Its "fair share" would be 20.)
    "greedy_tput_no_isolation": 103,

    # P3: now add a per-tenant quota (a token bucket at the fair share) in front
    #     of every tenant, and re-run the same flood. How many req/tick does the
    #     well-behaved tenant get served now?
    "quiet_tput_with_quota": 20,

    # P4: same quota run. How many req/tick is the GREEDY tenant now capped at?
    "greedy_tput_with_quota": 20,
}

# ---------------------------------------------------------------------------
# Knobs. The defaults make the noisy neighbour obvious and the numbers clean.
# ---------------------------------------------------------------------------
CAPACITY = 120           # the shared resource serves this many requests per tick
N_TENANTS = 6            # five well-behaved tenants plus one greedy one
QUIET = 20               # a well-behaved tenant's demand, req/tick (its fair share)
GREEDY = 600             # the greedy tenant's demand during the flood, req/tick
TICKS = 2000             # ticks we simulate
WARMUP = 200             # ticks to skip before we start measuring
SEED = 46                # determinism is explicit even though demand is constant

TENANTS = [f"t{i}" for i in range(1, N_TENANTS)] + ["greedy"]
QUIET_TENANTS = TENANTS[:-1]
GREEDY_TENANT = "greedy"


# ---------------------------------------------------------------------------
# The four TODOs. Each is one load-bearing line, the heart of one mechanism.
# ---------------------------------------------------------------------------

def fair_share(capacity, n):
    """TODO 1, the yardstick. If a shared resource of `capacity` req/tick is
    split evenly among `n` tenants, each tenant's fair share is this. It is also
    the rate we hand each tenant's limiter, and the slice a dedicated box gets."""
    return capacity // n


def proportional_share(capacity, demand, total_demand):
    """TODO 2, the noisy neighbour. A shared pool with no per-tenant accounting,
    when it is overloaded, serves each tenant in proportion to how much that
    tenant asked for. Flood harder, get a bigger slice. This single line is why
    one greedy tenant starves all the quiet ones."""
    return capacity * demand / total_demand


class TokenBucket:
    """A per-tenant rate limiter (Day 45). Tokens refill at `rate` per tick up to
    `burst`, and each admitted request spends one token. Requests above the rate
    find the bucket empty and are rejected (a 429) at the door, before they ever
    reach the shared pool."""

    def __init__(self, rate, burst):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)

    def admit(self, demand):
        """TODO 3, the quota. Refill the bucket, then let through as many of the
        `demand` requests as there are tokens for. The rest are turned away. For
        the greedy tenant whose demand dwarfs the rate, this caps it at the rate
        and rejects the flood; for a quiet tenant under the rate, it lets
        everything through."""
        self.tokens = min(self.tokens + self.rate, self.burst)
        admitted = min(int(self.tokens), demand)
        self.tokens -= admitted
        return admitted


def dedicated_share(capacity, n, demand):
    """TODO 4, dedicated resources. Give each tenant its own box of capacity/n
    and nothing else. A tenant gets exactly what it asks for, up to its own box,
    and not one request more: it can neither be stolen from (best isolation) nor
    borrow a neighbour's idle box (so idle capacity is simply wasted)."""
    return min(demand, capacity // n)


# ---------------------------------------------------------------------------
# Probing the TODOs so a blank one stops the run cleanly instead of lying.
# ---------------------------------------------------------------------------

def first_blank_todo():
    """Call each TODO once with trivial input. Return the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if fair_share(120, 6) is None:
        return 1
    if proportional_share(120, 20, 700) is None:
        return 2
    if TokenBucket(20, 20).admit(20) is None:
        return 3
    if dedicated_share(120, 6, 20) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# The shared pool with no isolation, and max-min fair scheduling.
# ---------------------------------------------------------------------------

def shared_pool_tick(demands, capacity):
    """One tick of a shared pool with no per-tenant limits. If the tenants ask
    for no more than capacity in total, everyone is served in full. If they ask
    for more, the pool is overloaded and each tenant is served in proportion to
    its demand (a shared first-come-first-served queue behaves this way: the more
    of the queue you fill, the more of it gets served). Returns served per tenant.
    """
    total = sum(demands.values())
    if total <= capacity:
        return dict(demands)
    return {t: proportional_share(capacity, d, total) for t, d in demands.items()}


def maxmin_fair_tick(demands, capacity):
    """One tick of max-min fair scheduling. Water-filling: raise a common level
    for every tenant at once; a tenant that wants less than the level is satisfied
    and drops out, freeing its slack for the rest, until the capacity runs out.
    Everyone is guaranteed its fair share, and leftover goes to whoever is still
    hungry. This is the ideal that round-robin and weighted fair queuing chase."""
    alloc = {t: 0.0 for t in demands}
    active = set(demands)
    remaining = float(capacity)
    while active and remaining > 1e-9:
        level = remaining / len(active)
        satisfied = [t for t in active if demands[t] - alloc[t] <= level]
        if not satisfied:
            for t in active:
                alloc[t] += level
            remaining = 0.0
            break
        for t in satisfied:
            give = demands[t] - alloc[t]
            alloc[t] += give
            remaining -= give
            active.remove(t)
    return alloc


def run(tick_fn, demands, label=""):
    """Step through TICKS ticks, accumulate served per tenant after warmup, and
    return average throughput (req/tick) per tenant. Demand is constant, so this
    just confirms the steady state, but stepping keeps it an honest simulation."""
    served = {t: 0.0 for t in demands}
    for now in range(TICKS):
        got = tick_fn(demands, CAPACITY)
        if now >= WARMUP:
            for t in demands:
                served[t] += got[t]
    measured = TICKS - WARMUP
    return {t: served[t] / measured for t in demands}


# ---------------------------------------------------------------------------
# Part 1: the noisy neighbour
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: the noisy neighbour. One shared pool, no limits, one bad actor.")
    print("=" * 78)
    fs = fair_share(CAPACITY, N_TENANTS)
    print(f"  The shared resource serves {CAPACITY} requests per tick.")
    print(f"  {N_TENANTS} tenants share it. An even split is {fs} req/tick each (the fair share).")
    print()

    # Baseline: everyone behaves. Total demand = capacity, so everyone is happy.
    calm = {t: QUIET for t in TENANTS}
    calm_tput = run(shared_pool_tick, calm)
    print(f"  Baseline, everyone well-behaved ({QUIET} req/tick each, {sum(calm.values())} total):")
    print(f"    every tenant served {calm_tput['t1']:.1f}/{QUIET}  "
          f"(demand = capacity, nobody is starved)")
    print()

    # The flood: the greedy tenant asks for 600 instead of 20.
    flood = {t: QUIET for t in QUIET_TENANTS}
    flood[GREEDY_TENANT] = GREEDY
    flood_tput = run(shared_pool_tick, flood)
    quiet = flood_tput["t1"]
    greedy = flood_tput[GREEDY_TENANT]
    print(f"  Now the greedy tenant floods: it asks for {GREEDY}/tick, the quiet ones")
    print(f"  still ask for {QUIET}. Total demand is {sum(flood.values())} for a {CAPACITY}-req/tick pool.")
    print(f"    well-behaved tenant served: {quiet:5.1f}/tick  (wanted {QUIET}, "
          f"{(1 - quiet / QUIET) * 100:.0f}% turned away)")
    print(f"    greedy tenant served:       {greedy:5.1f}/tick  (it alone eats "
          f"{greedy / CAPACITY * 100:.0f}% of the pool)")
    print()
    print("  The quiet tenant did nothing wrong and its throughput fell off a cliff.")
    print("  A shared queue serves whoever fills it, so the flood crowds everyone")
    print("  else out. The requests that are turned away pile up and time out: that")
    print("  is the latency collapse behind the throughput number.")
    print()

    # The sweep: the harder the neighbour floods, the worse for everyone else.
    print("  Watch the quiet tenant sink as the neighbour gets louder:")
    print(f"    {'greedy demand':>14}{'quiet served':>14}{'greedy served':>15}")
    for g in (20, 60, 120, 300, 600, 1200):
        d = {t: QUIET for t in QUIET_TENANTS}
        d[GREEDY_TENANT] = g
        tp = run(shared_pool_tick, d)
        print(f"    {g:>14}{tp['t1']:>14.1f}{tp[GREEDY_TENANT]:>15.1f}")
    print("  More flood from one tenant, less for each of the other five. No amount")
    print("  of flooding is refused, because nothing is counting per tenant.")
    return quiet, greedy


# ---------------------------------------------------------------------------
# Part 2: per-tenant quotas, then fair-share scheduling
# ---------------------------------------------------------------------------

def part2():
    print("\n" + "=" * 78)
    print("Part 2: contain the neighbour. A per-tenant quota, then fair scheduling.")
    print("=" * 78)
    fs = fair_share(CAPACITY, N_TENANTS)

    # Fix one: a token bucket per tenant at the fair-share rate (Day 45).
    buckets = {t: TokenBucket(fs, fs) for t in TENANTS}
    demands = {t: QUIET for t in QUIET_TENANTS}
    demands[GREEDY_TENANT] = GREEDY
    admitted_total = {t: 0.0 for t in TENANTS}
    rejected_greedy = 0.0
    for now in range(TICKS):
        admitted = {t: buckets[t].admit(demands[t]) for t in TENANTS}
        # Admitted requests reach the shared pool, which is no longer overloaded.
        served = shared_pool_tick(admitted, CAPACITY)
        if now >= WARMUP:
            for t in TENANTS:
                admitted_total[t] += served[t]
            rejected_greedy += demands[GREEDY_TENANT] - admitted[GREEDY_TENANT]
    measured = TICKS - WARMUP
    quiet_q = admitted_total["t1"] / measured
    greedy_q = admitted_total[GREEDY_TENANT] / measured
    rej = rejected_greedy / measured

    print(f"  Fix one: a token bucket in front of each tenant, refilling at the")
    print(f"  fair share ({fs} req/tick). Re-run the exact same flood.")
    print(f"    well-behaved tenant served: {quiet_q:5.1f}/tick  (back to its full share)")
    print(f"    greedy tenant served:       {greedy_q:5.1f}/tick  (capped at its share)")
    print(f"    greedy requests rejected:   {rej:5.0f}/tick  (429 at the door, never hit the pool)")
    print("  The limiter turns the flood away before it reaches the shared pool, so")
    print("  the pool is no longer overloaded and the quiet tenants are whole again.")
    print("  The greedy tenant is held to exactly what it is entitled to.")
    print()

    # Fix two: max-min fair scheduling, which is work conserving.
    flood = {t: QUIET for t in QUIET_TENANTS}
    flood[GREEDY_TENANT] = GREEDY
    fair_tput = run(maxmin_fair_tick, flood)
    print("  Fix two: fair-share (max-min) scheduling of the pool itself, no hard cap.")
    print(f"    well-behaved tenant served: {fair_tput['t1']:5.1f}/tick")
    print(f"    greedy tenant served:       {fair_tput[GREEDY_TENANT]:5.1f}/tick")
    print("  Same protection under this flood. The difference shows when a tenant")
    print("  goes idle and leaves slack on the table:")
    print()

    # One quiet tenant goes idle. Compare the hard cap against fair scheduling.
    idle = {t: QUIET for t in QUIET_TENANTS}
    idle["t1"] = 0                       # one well-behaved tenant sends nothing
    idle[GREEDY_TENANT] = GREEDY
    # Hard quota: each tenant still capped at the fair share, slack is wasted.
    cap_served = {t: min(idle[t], fs) for t in TENANTS}
    cap_total = sum(cap_served.values())
    # Fair scheduling: the idle tenant's slack is lent to whoever is hungry.
    fair_served = maxmin_fair_tick(idle, CAPACITY)
    fair_total = sum(fair_served.values())
    print(f"    one quiet tenant idle (sends 0); greedy still flooding {GREEDY}:")
    print(f"      {'':20}{'quiet active':>14}{'greedy':>10}{'pool used':>12}")
    print(f"      {'hard quota':<20}{cap_served['t2']:>14.1f}{cap_served[GREEDY_TENANT]:>10.1f}"
          f"{cap_total:>11.0f}/{CAPACITY}")
    print(f"      {'fair scheduling':<20}{fair_served['t2']:>14.1f}{fair_served[GREEDY_TENANT]:>10.1f}"
          f"{fair_total:>11.0f}/{CAPACITY}")
    print("  The hard quota protects the quiet tenants but wastes the idle share")
    print("  (greedy stays pinned at its cap, pool runs under capacity). Fair")
    print("  scheduling hands that idle share to the greedy tenant instead, so the")
    print("  pool stays full, yet an active quiet tenant can never be starved. That")
    print("  is the real trade: a hard cap is simple, fair scheduling is work")
    print("  conserving. Most real systems run a quota AND fair scheduling together.")
    return quiet_q, greedy_q


# ---------------------------------------------------------------------------
# Part 3: the isolation spectrum, and what it costs
# ---------------------------------------------------------------------------

def part3(quiet_shared, greedy_shared, quiet_quota, greedy_quota):
    print("\n" + "=" * 78)
    print("Part 3: the isolation spectrum, cheapest to safest")
    print("=" * 78)
    fs = fair_share(CAPACITY, N_TENANTS)

    # Dedicated: each tenant owns a box of capacity/n and cannot exceed it.
    ded_quiet = dedicated_share(CAPACITY, N_TENANTS, QUIET)
    ded_greedy = dedicated_share(CAPACITY, N_TENANTS, GREEDY)

    print(f"  The same flood ({GREEDY}/tick greedy, {QUIET}/tick quiet), three ways to share")
    print(f"  one {CAPACITY}-req/tick resource across {N_TENANTS} tenants:")
    print()
    print(f"  {'model':<24}{'quiet served':>13}{'greedy served':>14}{'isolation':>12}{'cost':>9}")
    print(f"  {'shared, no limits':<24}{quiet_shared:>13.1f}{greedy_shared:>14.1f}"
          f"{'none':>12}{'low':>9}")
    print(f"  {'shared + per-tenant quota':<24}{quiet_quota:>13.1f}{greedy_quota:>14.1f}"
          f"{'good':>12}{'medium':>9}")
    print(f"  {'dedicated per tenant':<24}{ded_quiet:>13.1f}{ded_greedy:>14.1f}"
          f"{'best':>12}{'high':>9}")
    print()
    print("  Shared, no limits: one pool, nothing counted per tenant. Cheapest to")
    print("    run, zero isolation, and Part 1 is what you get.")
    print("  Shared + quota: one pool, a cheap meter per tenant. The quiet tenants")
    print("    are protected and the pool is still shared, so idle capacity can be")
    print("    reused (with fair scheduling). This is the usual middle ground.")
    print(f"  Dedicated: give every tenant its own box of {fs} req/tick. The greedy")
    print("    tenant is physically walled off, but so is all the slack: if a box")
    print("    is idle, no one else can use it, so you provision and pay for the")
    print(f"    peak of all {N_TENANTS} tenants at once. Strongest isolation, highest bill.")
    print()
    print("  The move from a shared pool (statistical multiplexing, one bill for the")
    print("  aggregate) to dedicated boxes (one bill per tenant, idle or not) is the")
    print("  isolation-versus-cost dial. Putting real money on that dial is Day 48.")


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit="/tick"):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>6.1f} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    note = "     close enough" if diff <= max(3.0, 0.15 * abs(predicted)) \
        else f"  off by {diff:.1f}"
    print(f"  {name:<34} you = {predicted:>6.1f}   actual = {actual:>6.1f} {unit}  {note}")


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

    quiet_shared, greedy_shared = part1()
    quiet_quota, greedy_quota = part2()
    part3(quiet_shared, greedy_shared, quiet_quota, greedy_quota)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 quiet served, no isolation", PREDICTIONS["quiet_tput_no_isolation"], quiet_shared)
    verdict("P2 greedy served, no isolation", PREDICTIONS["greedy_tput_no_isolation"], greedy_shared)
    verdict("P3 quiet served, with quota", PREDICTIONS["quiet_tput_with_quota"], quiet_quota)
    verdict("P4 greedy served, with quota", PREDICTIONS["greedy_tput_with_quota"], greedy_quota)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Same shared resource, same flood, same quiet tenant wanting {QUIET}/tick.")
    print(f"  Shared with no limits: the quiet tenant got {quiet_shared:.1f}/tick while the")
    print(f"  greedy neighbour ate {greedy_shared:.0f} of the {CAPACITY}. Add a per-tenant quota")
    print(f"  and the quiet tenant is back to {quiet_quota:.0f}/tick, the greedy one pinned at")
    print(f"  {greedy_quota:.0f}. Isolation is not a feature you bolt on; it is the difference")
    print("  between one customer and all your other customers sharing the pain.")
    print()


if __name__ == "__main__":
    main()
