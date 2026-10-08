"""
Day 43 lab: observability, the three signals. Logs, metrics and traces, and
the one truth that hides in plain sight: a mean looks healthy while the p99 is
on fire.

This is the full working solution. The starter file is observability.py.
Run it:      python3 solution.py

Standard library only. No network, no threads, no files, nothing to clean up.
Everything is a deterministic simulation off a seeded RNG, so the run is
reproducible to the digit. Runs in well under a second.

One request stream, looked at three ways, because that is what the three
signals are: three lenses on the same traffic.

  Part 1, metrics (RED). Rate, Errors, Duration over the whole stream. We
    compute the mean, then p50 and p99. The mean and the median both look fine.
    The p99 is a different planet. That gap is why you alert on p99, not the
    mean (callback to Day 1's percentiles and Day 4's queue tail: the tail is
    what users actually feel, and an average hides it).

  Part 2, logs (structured vs unstructured). The same requests, written once as
    structured records (tenant, endpoint, status, latency as real fields) and
    once as a blob of free text. We ask one real production question, "errors
    for tenant acme slower than one second", and watch the structured store
    answer it exactly while the text blob can only fumble at it.

  Part 3, traces. One slow request fanned out across three downstream services,
    carrying a shared trace id and per-span timings. Metrics told you the
    request took half a second. Only the trace tells you WHICH of the three
    services ate 86 percent of it. That is the thing metrics alone cannot do.
"""

import math
import random
import sys
from collections import namedtuple

PREDICTIONS = {
    # P1: the request stream's MEAN latency, in milliseconds. This is the number
    #     a naive dashboard shows. Does it look healthy to you? Guess it.
    "mean_ms": 70,

    # P2: the SAME stream's p99 latency, in milliseconds. One request in a
    #     hundred is slower than this. Most people guess far too low here.
    "p99_ms": 1500,

    # P3: structured-log query. Of the whole stream, how many records match
    #     tenant == "acme" AND status is an error AND latency > 1000 ms? A
    #     question you answer in one line IF your logs have fields.
    "acme_slow_errors": 50,

    # P4: the trace. One request fanned out to three services. The slowest
    #     single span took how many milliseconds? (This is the span the trace
    #     fingers, the one a metric can never point to.)
    "slow_span_ms": 430,
}

# ---------------------------------------------------------------------------
# Knobs. Chosen so the mean looks calm, the p99 screams, and the numbers land
# on clean, repeatable values.
# ---------------------------------------------------------------------------
N = 20_000               # requests in the stream
WINDOW_S = 60            # seconds the stream was collected over (for Rate)
SEED = 43

TENANTS = ["acme", "globex", "initech", "umbrella"]
TENANT_WEIGHTS = [25, 25, 25, 25]          # acme is a quarter of the traffic
ENDPOINTS = ["/checkout", "/search", "/feed", "/login"]

# The latency mixture: a calm body and a heavy tail. 90 percent of requests are
# fast, 8 percent are middling, and 2 percent fall off a cliff. The errors live
# mostly in that 2 percent, exactly like a real timeout: slow and failed.
FAST_FRAC = 0.90
MED_FRAC = 0.08          # the remaining 2 percent is the heavy tail
SLOW_ERR_RATE = 0.50     # a heavy-tail request is an error half the time
BODY_ERR_RATE = 0.01     # a fast or middling request errors rarely

Rec = namedtuple("Rec", "ts trace_id tenant endpoint status latency_ms")


# ---------------------------------------------------------------------------
# The four TODOs: each is one load-bearing line of an observability stack.
# ---------------------------------------------------------------------------

def percentile(values, p):
    """TODO 1, the heart of Part 1. Return the p-th percentile of `values`
    (0 <= p <= 100) by linear interpolation between the two nearest ranks.
    Sort first. p=50 is the median, p=99 is the number only your unhappiest
    1 percent of requests exceed. This one function is why a dashboard can
    show the tail instead of hiding it inside a mean."""
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return s[int(k)]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def error_rate(records):
    """TODO 2, the E in RED. The fraction of requests that failed, as a percent.
    A failure is any status of 500 or more. This is the signal a mean latency
    will never show you: a service can be fast on average and still be failing."""
    if not records:
        return 0.0
    errors = sum(1 for r in records if r.status >= 500)
    return errors / len(records) * 100.0


def matches_query(rec, tenant, min_latency_ms):
    """TODO 3, the whole point of structured logs. Return True if this record is
    for `tenant`, is an error (status >= 500), AND is slower than
    `min_latency_ms`. Three fields, one boolean. Trivial when the log has
    fields; a parsing nightmare when it is a line of prose."""
    return (rec.tenant == tenant
            and rec.status >= 500
            and rec.latency_ms > min_latency_ms)


def slowest_span(spans):
    """TODO 4, what a trace gives you that a metric cannot. Given the spans of
    one request, return the single span that took the longest. A metric says
    'the request took 500 ms'. This says WHICH span those 500 ms were spent in."""
    return max(spans, key=lambda s: s.dur_ms)


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if percentile([1.0, 2.0, 3.0], 50) is None:
        return 1
    probe = [Rec(0, "t", "acme", "/x", 500, 10.0)]
    if error_rate(probe) is None:
        return 2
    if matches_query(probe[0], "acme", 1.0) is None:
        return 3
    Span = namedtuple("Span", "name trace_id span_id parent start_ms dur_ms")
    if slowest_span([Span("a", "t", "s", None, 0, 5.0)]) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# The request stream: generated once, then viewed as metrics, logs and a trace.
# ---------------------------------------------------------------------------

def gen_stream(rng, n, window_s):
    """Build n structured request records off the seeded RNG. Each carries a
    timestamp, a trace id, a tenant, an endpoint, an HTTP status and a latency.
    The latency is a calm body plus a heavy tail, and the errors cluster in the
    tail, which is what makes the mean lie."""
    recs = []
    for i in range(n):
        ts = rng.uniform(0, window_s)
        tenant = rng.choices(TENANTS, weights=TENANT_WEIGHTS)[0]
        endpoint = rng.choice(ENDPOINTS)

        roll = rng.random()
        if roll < FAST_FRAC:
            latency = rng.gauss(35, 8)          # the fast body
            heavy = False
        elif roll < FAST_FRAC + MED_FRAC:
            latency = rng.gauss(150, 40)        # the middling band
            heavy = False
        else:
            latency = rng.uniform(900, 2200)    # the heavy tail, 2 percent
            heavy = True
        latency = max(1.0, latency)

        err_rate = SLOW_ERR_RATE if heavy else BODY_ERR_RATE
        status = 500 if rng.random() < err_rate else 200

        trace_id = "trc-%08x" % rng.getrandbits(32)
        recs.append(Rec(ts, trace_id, tenant, endpoint, status, latency))
    recs.sort(key=lambda r: r.ts)
    return recs


# ---------------------------------------------------------------------------
# Part 1: metrics. The RED method, and the mean that hides the fire.
# ---------------------------------------------------------------------------

def part1(records):
    print("=" * 78)
    print("Part 1: metrics (RED). Rate, Errors, Duration. The mean looks calm;")
    print("        the p99 is on fire.")
    print("=" * 78)

    latencies = [r.latency_ms for r in records]
    rate = len(records) / WINDOW_S
    errs = error_rate(records)
    mean = sum(latencies) / len(latencies)
    p50 = percentile(latencies, 50)
    p90 = percentile(latencies, 90)
    p99 = percentile(latencies, 99)
    p999 = percentile(latencies, 99.9)
    worst = max(latencies)

    print(f"  stream: {len(records):,} requests over {WINDOW_S}s")
    print()
    print("  R  Rate      %9.1f req/s" % rate)
    print("  E  Errors    %9.2f %%      (status >= 500)" % errs)
    print("  D  Duration:")
    print(f"       mean   {mean:9.1f} ms   <- the number on the calm dashboard")
    print(f"       p50    {p50:9.1f} ms   <- half your requests are faster than this")
    print(f"       p90    {p90:9.1f} ms")
    print(f"       p99    {p99:9.1f} ms   <- 1 request in 100 is SLOWER than this")
    print(f"       p99.9  {p999:9.1f} ms")
    print(f"       max    {worst:9.1f} ms")
    print()
    print(f"  The mean is {mean:.0f} ms and the median is {p50:.0f} ms. If that is all your")
    print(f"  dashboard shows, the service looks healthy. But the p99 is {p99:.0f} ms,")
    print(f"  about {p99 / mean:.0f}x the mean. One user in a hundred is waiting over a")
    print("  second while the average says everything is fine.")
    print("  This is Day 1's percentiles and Day 4's queue tail, made concrete:")
    print("  the average is the one summary number that is guaranteed to hide")
    print("  your worst customers. You alert on the p99, never the mean.")
    return mean, p99


# ---------------------------------------------------------------------------
# Part 2: logs. Structure the log at write time, or pay forever at read time.
# ---------------------------------------------------------------------------

def to_text_line(r):
    """Render a record as an unstructured log line, the way a tired service
    scatters print() statements: a human sentence, no fields."""
    verb = "failed" if r.status >= 500 else "served"
    return (f"[{r.ts:6.2f}] request from {r.tenant} to {r.endpoint} "
            f"{verb} after {r.latency_ms:.0f}ms")


def part2(records):
    print("\n" + "=" * 78)
    print("Part 2: logs. Structured fields you can query vs a blob you cannot.")
    print("=" * 78)

    tenant, threshold = "acme", 1000.0
    question = f'errors for tenant "{tenant}" with latency over {threshold:.0f}ms'
    print(f"  The on-call question at 3am: {question}.")
    print()

    # The structured answer: three fields, one filter, exact.
    hits = [r for r in records if matches_query(r, tenant, threshold)]
    structured_count = len(hits)
    print("  Structured logs (records with real fields):")
    print(f"    [r for r in log if r.tenant=='{tenant}' and r.status>=500 "
          f"and r.latency_ms>{threshold:.0f}]")
    print(f"    -> {structured_count} matching records, exactly. Here are three:")
    for r in hits[:3]:
        print(f"       tenant={r.tenant} {r.endpoint} status={r.status} "
              f"latency={r.latency_ms:.0f}ms")
    print()

    # The unstructured attempt: a blob of text. Substring grep cannot do math.
    blob = [to_text_line(r) for r in records]
    naive = [ln for ln in blob if tenant in ln and "failed" in ln]
    print("  Unstructured logs (the same events as prose):")
    print(f'       {blob[0]}')
    print(f"    grep '{tenant}' | grep 'failed'  ->  {len(naive)} lines")
    print(f"    ...but that counts EVERY acme error, including the fast ones.")
    print(f"    It has no idea what '> {threshold:.0f}ms' means, because 'latency' is")
    print("    not a field here, it is three digits buried in a sentence. To get")
    print("    the real answer from text you must regex the number out of every")
    print("    line and compare it, which is just rebuilding the field you threw")
    print("    away at write time. Structure the log once, or parse it forever.")
    print()

    # One aggregation, trivial once the data has fields: p99 per endpoint.
    print("  And aggregation is free once you have fields. p99 latency by endpoint:")
    for ep in ENDPOINTS:
        lat = [r.latency_ms for r in records if r.endpoint == ep]
        print(f"       {ep:<11} p99 = {percentile(lat, 99):7.1f} ms  "
              f"({len(lat):,} requests)")
    print("  Try writing THAT over a blob of prose. Fields are what make a log a")
    print("  database you can ask questions of, instead of a wall of text.")
    return structured_count


# ---------------------------------------------------------------------------
# Part 3: traces. One request, three services, and which span ate the time.
# ---------------------------------------------------------------------------

Span = namedtuple("Span", "name trace_id span_id parent start_ms dur_ms")


def build_trace(rng):
    """Simulate one slow request fanning out to three downstream services,
    called in sequence by the gateway. Every span shares ONE trace id and
    carries its own span id, its parent, a start offset and a duration. This is
    exactly a request sitting in Part 1's p99 tail, taken apart."""
    trace_id = "trc-%08x" % rng.getrandbits(32)
    root_id = "span-%04x" % rng.getrandbits(16)

    gw_pre = 8.0                                   # gateway parses, authnz
    auth = max(1.0, rng.gauss(20, 3))              # user service: fast
    db = max(1.0, rng.gauss(430, 20))              # search / DB: the culprit
    render = max(1.0, rng.gauss(35, 5))            # render service: fast
    gw_post = 7.0                                  # gateway serialises response

    t = gw_pre
    children = []
    for name, dur in [("user-service.lookup", auth),
                      ("search-service.query", db),
                      ("render-service.html", render)]:
        children.append(Span(name, trace_id, "span-%04x" % rng.getrandbits(16),
                             root_id, t, dur))
        t += dur

    total = gw_pre + auth + db + render + gw_post
    root = Span("api-gateway.request", trace_id, root_id, None, 0.0, total)
    return root, children


def part3(rng):
    print("\n" + "=" * 78)
    print("Part 3: traces. Metrics say the request was slow. The trace says why.")
    print("=" * 78)

    root, children = build_trace(rng)
    spans = [root] + children
    total = root.dur_ms

    print(f"  One request, trace id {root.trace_id}. Metrics (Part 1) would")
    print(f"  record just one number for it: {total:.0f} ms, somewhere out in the p99")
    print("  tail. Useful for an alert, useless for a fix. Now the trace:")
    print()
    print(f"  {'span':<26}{'start':>8}{'dur':>9}{'% of req':>10}")
    print(f"  {root.name:<26}{root.start_ms:>7.0f}ms{root.dur_ms:>7.0f}ms"
          f"{100.0:>9.0f}%")
    for c in children:
        bar = "#" * max(1, int(c.dur_ms / total * 40))
        print(f"    {c.name:<24}{c.start_ms:>7.0f}ms{c.dur_ms:>7.0f}ms"
              f"{c.dur_ms / total * 100:>9.0f}%  {bar}")
    print()

    slow = slowest_span(children)
    print(f"  Every span shares the one trace id ({root.trace_id}) and points at")
    print("  its parent, so the collector can rebuild this tree from spans that")
    print("  arrived separately from three different services.")
    print()
    print(f"  The slowest span is {slow.name} at {slow.dur_ms:.0f} ms, which is")
    print(f"  {slow.dur_ms / total * 100:.0f}% of the whole {total:.0f} ms request. THAT is what a")
    print("  trace buys you. The metric knew the request was slow. Only the trace")
    print("  knows it was the search service, not auth, not render, not the")
    print("  gateway. This is RED per request; the USE method (utilisation,")
    print("  saturation, errors) is the same instinct pointed at the resource")
    print("  behind that slow span: is the DB's disk or CPU saturated?")
    return slow.dur_ms, total


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>8.1f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if abs(actual - predicted) <= 2 or 0.6 <= ratio <= 1.7:
        note = "     close enough"
    elif ratio > 1:
        note = f"  {ratio:.1f}x  you guessed LOW"
    else:
        note = f"  {1 / ratio:.1f}x  you guessed HIGH"
    print(f"  {name:<30} you = {predicted:>7.1f}   actual = {actual:>8.1f} {unit}  {note}")


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
    records = gen_stream(rng, N, WINDOW_S)

    mean, p99 = part1(records)
    acme_slow = part2(records)
    slow_span, total = part3(rng)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 mean latency", PREDICTIONS["mean_ms"], mean, "ms")
    verdict("P2 p99 latency", PREDICTIONS["p99_ms"], p99, "ms")
    verdict("P3 acme slow errors", PREDICTIONS["acme_slow_errors"], acme_slow, "")
    verdict("P4 slowest span", PREDICTIONS["slow_span_ms"], slow_span, "ms")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Same stream, one mean and one p99. The mean was {mean:.0f} ms and looked")
    print(f"  healthy. The p99 was {p99:.0f} ms, about {p99 / mean:.0f}x higher, and that is the")
    print("  number your slowest users actually live in. A mean hides the fire;")
    print("  the percentile shows it. That is the whole case for metrics done right.")
    print(f"  And when one request was slow, the trace put {slow_span:.0f} of its {total:.0f} ms")
    print("  on a single span, the search service. Metrics find the fire, logs")
    print("  tell you who was burned, traces point at the match. Three signals,")
    print("  one system, and you need all three on call at 3am.")
    print()


if __name__ == "__main__":
    main()
