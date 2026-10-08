"""
Day 44 lab: SLOs and error budgets. Why 100 percent uptime is the wrong goal,
turned from a slogan into three numbers you can actually spend.

This is the full working solution. The starter file is slos.py.
Run it:      python3 solution.py

Standard library only, no network, no threads, no files. Everything is a
deterministic simulation of one month of a service's request stream. Every
random outcome (which request failed, which dependency was up) comes from a
seeded RNG, so the run is reproducible to the digit.

The three ideas, measured:
  - The SLI is what you measured; the SLO is what you promised. From a stream
    of request outcomes over a month we count the good ones, divide by the
    total, and get availability. Then we hold it up against a 99.9 percent SLO
    and say plainly whether we are meeting it.
  - The error budget is the failures you are ALLOWED. It is (1 - SLO) times the
    total, and you can read it two ways: as failed requests, and as downtime
    minutes per month (99.9 percent is about 43.8 minutes, 99.99 percent about
    4.4). The budget turns reliability from a vibe into a number you can spend.
    A burn rate says how fast you are spending it: a burn rate of 1 means the
    budget lasts exactly the month, a burn rate of 8 means one day ate eight
    days' worth. This is also why you do NOT chase 100 percent. The last nine
    costs 10x the one before it, and 100 percent leaves no room to ever ship a
    change or have a bad afternoon.
  - Dependencies multiply. If your service needs all 5 of its dependencies and
    each promises 99.9 percent, your ceiling is 0.999 to the 5th, about 99.5
    percent, before you have written a single bug of your own. This is Day 2's
    nines table and its dependency-multiplication rule, now watched falling one
    dependency at a time.
"""

import random
import sys

PREDICTIONS = {
    # P1: the time budget. A 99.9 percent SLO over one month. How many MINUTES
    #     of downtime does that allow you in the month? (Day 2 had this in a
    #     table; see if it stuck.)
    "budget_minutes_999": 44,

    # P2: the request budget. The service handled 2,000,000 requests this month
    #     under a 99.9 percent SLO. How many of them are you ALLOWED to fail?
    "budget_requests": 2000,

    # P3: the burn rate. A multi-hour incident lands on one day. That single day
    #     spent how many times the sustainable daily slice of the budget?
    #     (1x = exactly on budget for the day, so the month lasts the month.)
    "incident_burn_rate": 8,

    # P4: dependencies multiply. Your service needs all 5 dependencies, each
    #     promising 99.9 percent. What combined availability can you offer,
    #     as a percent, before adding any faults of your own?
    "combined_avail_5deps_pct": 99.5,
}

# ---------------------------------------------------------------------------
# Knobs. Chosen so the month is a realistic "good month with one bad day":
# we meet the SLO, but a single incident eats a big slice of the budget.
# ---------------------------------------------------------------------------
SEED = 44
SLO = 0.999                  # the promise: three nines
MINUTES_PER_MONTH = 43830    # the average Gregorian month, 30.4375 days. This
                             # is the figure behind Day 2's nines table, so the
                             # budget here matches the 43.8 / 4.4 you saw then.
DAYS_PER_MONTH = 30.4375
MINUTES_PER_DAY = 1440
TOTAL_REQUESTS = 2_000_000   # requests the service served over the month

BASE_FAIL = 0.00045          # normal background failure probability per request
INCIDENT_DAY = 15            # the day a dependency wobbled (0-indexed into month)
INCIDENT_START_HOUR = 10     # incident begins mid-morning
INCIDENT_HOURS = 3           # and lasts three hours
INCIDENT_FAIL = 0.06         # failure probability per request during the incident
NORMAL_DAY = 10              # a quiet day to contrast against the incident

DEP_SLO = 0.999              # each dependency promises three nines
DEP_COUNT = 5                # and your service needs ALL of them
FANOUT_TRIALS = 200_000      # Monte Carlo trials for the dependency measurement


# ---------------------------------------------------------------------------
# The four TODOs: four one-line definitions that are the whole day.
# ---------------------------------------------------------------------------

def sli(good, total):
    """TODO 1, the measurement. The service level indicator is just the fraction
    of requests that succeeded: the good ones over all of them. This is the
    number you compare to the SLO."""
    return good / total


def error_budget_requests(slo, total):
    """TODO 2, the budget. The failures you are ALLOWED over the window: the
    slice of the total that the SLO lets you miss, which is (1 - SLO) times the
    total. Everything about error budgets grows out of this one line."""
    return (1.0 - slo) * total


def burn_rate(error_rate, slo):
    """TODO 3, the speed. How fast are we spending the budget? Compare the error
    rate we are actually serving to the error rate the SLO permits, (1 - SLO).
    A burn rate of 1 spends the budget exactly over the window; 8 means eight
    times too fast, so the month's budget is gone in a month over 8."""
    return error_rate / (1.0 - slo)


def combined_availability(avails):
    """TODO 4, the multiplication. If you need EVERY dependency to be up, their
    availabilities multiply: the chance all are up at once is the product. Five
    independent 99.9 percent dependencies give 0.999**5, not 99.9 percent."""
    product = 1.0
    for a in avails:
        product *= a
    return product


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in. This is what
    lets the starter stop cleanly on a blank TODO instead of crashing."""
    if sli(1, 2) is None:
        return 1
    if error_budget_requests(0.999, 1000) is None:
        return 2
    if burn_rate(0.001, 0.999) is None:
        return 3
    if combined_availability([0.999, 0.999]) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# The month: simulate a real stream of request outcomes, minute by minute.
# ---------------------------------------------------------------------------

def simulate_month(rng):
    """Walk every minute of the month. Each minute carries a few dozen requests;
    each request fails with the background probability, except during the
    incident window, when the failure probability spikes. Returns the per-day
    (requests, failures) and the month totals. This is the stream we measure."""
    per_min = TOTAL_REQUESTS // MINUTES_PER_MONTH
    extra = TOTAL_REQUESTS - per_min * MINUTES_PER_MONTH  # spread the remainder

    n_days = (MINUTES_PER_MONTH + MINUTES_PER_DAY - 1) // MINUTES_PER_DAY
    day_reqs = [0] * n_days
    day_fails = [0] * n_days

    incident_start = INCIDENT_DAY * MINUTES_PER_DAY + INCIDENT_START_HOUR * 60
    incident_end = incident_start + INCIDENT_HOURS * 60

    total_good = 0
    total_fail = 0
    for m in range(MINUTES_PER_MONTH):
        day = m // MINUTES_PER_DAY
        p = INCIDENT_FAIL if incident_start <= m < incident_end else BASE_FAIL
        reqs = per_min + (1 if m < extra else 0)
        fails = 0
        for _ in range(reqs):
            if rng.random() < p:
                fails += 1
        day_reqs[day] += reqs
        day_fails[day] += fails
        total_fail += fails
        total_good += reqs - fails

    return day_reqs, day_fails, total_good, total_fail


def simulate_fanout(rng, k, trials):
    """Measured dependency fan-out. Each trial, ask whether all k dependencies
    are up at this instant (each up with probability DEP_SLO, independently).
    Returns the fraction of trials where every one was up: the availability your
    service can actually offer when it needs all k."""
    all_up = 0
    for _ in range(trials):
        up = True
        for _ in range(k):
            if rng.random() >= DEP_SLO:
                up = False
                break
        if up:
            all_up += 1
    return all_up / trials


# ---------------------------------------------------------------------------
# Part 1: measure the SLI, compare it to the SLO.
# ---------------------------------------------------------------------------

def part1(day_reqs, day_fails, good, fail):
    print("=" * 78)
    print("Part 1: the SLI vs the SLO. Measure what you shipped, hold it up to")
    print("        what you promised")
    print("=" * 78)
    total = good + fail
    avail = sli(good, total)
    print(f"  one month of traffic: {total:,} requests, {fail:,} of them failed.")
    print(f"  SLI (measured availability) = {avail * 100:.3f}%")
    print(f"  SLO (the promise)           = {SLO * 100:.3f}%")
    meeting = avail >= SLO
    verdict = "MEETING the SLO" if meeting else "MISSING the SLO"
    print(f"  verdict: {verdict}.")
    print()
    print("  Notice the SLI is a plain count: good requests over all requests,")
    print("  over a fixed window. The SLO is the line you drew in advance. Day 43")
    print("  gave you the metrics to compute this; today you give the number a")
    print("  target and a consequence. We are above the line this month, but look")
    print("  how little room 'above the line' actually is, next.")
    return avail, total


# ---------------------------------------------------------------------------
# Part 2: the error budget, in minutes and requests, and the burn rate.
# ---------------------------------------------------------------------------

def part2(day_reqs, day_fails, avail, total, fail):
    print("\n" + "=" * 78)
    print("Part 2: the error budget. The failures you are ALLOWED, and how fast")
    print("        you are spending them")
    print("=" * 78)

    budget_reqs = error_budget_requests(SLO, total)
    budget_min = (1.0 - SLO) * MINUTES_PER_MONTH
    print("  The budget is (1 - SLO) times the window. Two ways to read it:")
    print(f"    in requests: (1 - {SLO}) x {total:,} = {budget_reqs:,.0f} failures allowed")
    print(f"    in minutes:  (1 - {SLO}) x {MINUTES_PER_MONTH:,} = {budget_min:.1f} "
          f"minutes of downtime a month")
    print()

    spent = fail
    left = budget_reqs - spent
    spent_pct = spent / budget_reqs * 100
    print(f"  This month you spent {spent:,} of {budget_reqs:,.0f} failures "
          f"({spent_pct:.1f}% of the budget).")
    print(f"  Budget left: {left:,.0f} failures. You are {'in the black' if left >= 0 else 'OVER budget'}.")
    print()

    # Burn rate: a quiet day versus the incident day.
    print("  Burn rate = the error rate you are serving / the error rate the SLO")
    print("  allows. 1x spends the budget exactly over the month. Watch one day:")
    print()
    print(f"  {'day':<16}{'requests':>12}{'failures':>12}{'error rate':>14}{'burn rate':>12}")
    daily_budget = budget_reqs / DAYS_PER_MONTH
    incident_burn = None
    for label, d in [("a quiet day", NORMAL_DAY), ("the incident day", INCIDENT_DAY)]:
        er = day_fails[d] / day_reqs[d]
        br = burn_rate(er, SLO)
        print(f"  {label:<16}{day_reqs[d]:>12,}{day_fails[d]:>12,}"
              f"{er * 100:>13.3f}%{br:>11.2f}x")
        if d == INCIDENT_DAY:
            incident_burn = br
    print()
    days_to_empty = DAYS_PER_MONTH / incident_burn
    print(f"  The sustainable daily slice is {daily_budget:.1f} failures. The quiet day")
    print(f"  stayed well under it (burn rate below 1, the budget would outlast the")
    print(f"  month). The incident day burned {incident_burn:.1f}x: at that pace the whole")
    print(f"  month's budget is gone in {days_to_empty:.1f} days. One bad afternoon ate a")
    print(f"  real slice of the month, and that is exactly what the budget is for,")
    print(f"  to tell you so in a number instead of an argument.")
    print()

    # Why not 100 percent: each extra nine costs 10x.
    print("  Why not just aim for 100 percent? Because each extra nine costs 10x")
    print("  the room of the one before, and 100 percent allows zero failures ever:")
    print(f"  {'SLO':<12}{'budget / month':>20}{'vs previous':>16}")
    prev = None
    for nines in (0.99, 0.999, 0.9999, 0.99999):
        bmin = (1.0 - nines) * MINUTES_PER_MONTH
        ratio = f"{prev / bmin:.0f}x less room" if prev else "-"
        print(f"  {nines * 100:<12.3f}{bmin:>16.1f} min{ratio:>16}")
        prev = bmin
    print("  100.000     0.0 min, which means you can never ship a risky change,")
    print("  never have an incident, never patch under load. Infinitely expensive,")
    print("  and it buys you a system too scared to move. The budget is permission")
    print("  to spend failure on purpose: on deploys, experiments, and real life.")
    return budget_min, budget_reqs, incident_burn


# ---------------------------------------------------------------------------
# Part 3: dependencies multiply. Your ceiling falls as you add them.
# ---------------------------------------------------------------------------

def part3(rng):
    print("\n" + "=" * 78)
    print("Part 3: dependencies multiply. Each one you must call lowers your")
    print("        ceiling, before you add a single bug of your own")
    print("=" * 78)
    print(f"  Each dependency promises {DEP_SLO * 100:.1f}%. You need ALL of them to")
    print("  answer, so their availabilities multiply (Day 2's rule, Day 4's")
    print("  fan-out: a caller is only as up as every service it waits on).")
    print()
    print(f"  {'dependencies':>14}{'combined (theory)':>20}{'measured':>12}"
          f"{'downtime / month':>20}")
    combined_5 = None
    for k in range(1, DEP_COUNT + 3):
        theory = combined_availability([DEP_SLO] * k)
        measured = simulate_fanout(rng, k, FANOUT_TRIALS)
        down_min = (1.0 - theory) * MINUTES_PER_MONTH
        print(f"  {k:>14}{theory * 100:>19.3f}%{measured * 100:>11.3f}%"
              f"{down_min:>16.0f} min")
        if k == DEP_COUNT:
            combined_5 = theory
    print()
    down_5 = (1.0 - combined_5) * MINUTES_PER_MONTH
    print(f"  With {DEP_COUNT} dependencies at {DEP_SLO * 100:.1f}%, your ceiling is already")
    print(f"  {combined_5 * 100:.2f}% = about {down_5:.0f} minutes ({down_5 / 60:.1f} hours) of downtime a")
    print(f"  month, and you have not shipped one line of your own yet. The measured")
    print(f"  column (a Monte Carlo of whether all {DEP_COUNT} are up) sits right on the")
    print("  theory, because this is multiplication, not luck. This is why you")
    print("  fight it on purpose: fewer hard dependencies, timeouts and fallbacks")
    print("  so a dependency being down degrades you instead of taking you down,")
    print("  and caches so you do not have to call it every time.")
    return combined_5 * 100


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>8.2f} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    tol = max(0.5, 0.15 * abs(predicted))
    note = "     close enough" if diff <= tol else f"  off by {diff:.2f}"
    print(f"  {name:<34} you = {predicted:>7.2f}   actual = {actual:>8.2f} {unit}  {note}")


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

    rng = random.Random(SEED)
    day_reqs, day_fails, good, fail = simulate_month(rng)

    avail, total = part1(day_reqs, day_fails, good, fail)
    budget_min, budget_reqs, incident_burn = part2(day_reqs, day_fails, avail, total, fail)
    combined_5 = part3(rng)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 budget minutes (99.9%)", PREDICTIONS["budget_minutes_999"], budget_min, "min")
    verdict("P2 budget requests", PREDICTIONS["budget_requests"], budget_reqs)
    verdict("P3 incident-day burn rate", PREDICTIONS["incident_burn_rate"], incident_burn, "x")
    verdict("P4 combined avail, 5 deps", PREDICTIONS["combined_avail_5deps_pct"], combined_5, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  A 99.9% SLO is NOT 'basically always up'. It is a budget: {budget_reqs:,.0f}")
    print(f"  failed requests, or {budget_min:.0f} minutes of downtime, for the whole month.")
    print(f"  This month spent {fail:,} of them, and one 3-hour incident burned")
    print(f"  {incident_burn:.0f}x the daily rate on its own. Stack {DEP_COUNT} dependencies at 99.9%")
    print(f"  and your ceiling is already {combined_5:.1f}% before your own bugs. That is")
    print("  why 100% is the wrong goal: it is infinitely expensive and leaves no")
    print("  room to ship. Pick a number you can defend, then spend the budget on")
    print("  purpose.")
    print()


if __name__ == "__main__":
    main()
