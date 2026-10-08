"""
Day 41 lab: the engineering around the model. Three cheap, boring, familiar
tricks that decide whether an AI feature is affordable and whether it stays up:
a semantic cache, a token-based rate limiter, and a gateway with fallback.

This is the full working solution. The starter file is serving.py.
Run it:      python3 solution.py

Standard library only. No real model, no embedding API, no network, no numpy,
no pip install. Everything is a deterministic toy with made-up vectors, token
counts and failure coins, and every random choice comes from a seeded RNG, so
the run is reproducible to the digit.

The big ideas:
  - A semantic cache keys by MEANING, not by the exact string. We embed each
    query into a little vector (a toy bag-of-content-words embedding, the same
    idea as Day 38's), and if a new query is within a cosine-similarity
    threshold of something we already answered, we return the cached answer and
    skip the model. Paraphrases of one question collapse onto one model call.
    An exact-match cache keys by the raw string, so it misses every paraphrase.
  - LLM cost is per TOKEN, not per request. A request-per-minute limiter bakes
    in an assumed request size; reality does not cooperate. A token bucket
    meters the thing you actually pay for, so it admits many small requests or
    few large ones to the same budget, and never blows past it.
  - The primary model errors and times out. A gateway retries, and past a
    threshold falls back to a secondary model, so the user still gets an answer.
    Retries handle the odd transient blip. Fallback is the thing that saves you
    on the day the provider has an outage, and a semantic cache can keep serving
    cached answers right through it.
"""

import math
import random
import re
import sys

PREDICTIONS = {
    # P1: the semantic cache runs over a workload that is mostly paraphrases of a
    #     handful of questions. What percent of queries are a cache HIT (served
    #     without calling the model)?
    "semantic_hit_pct": 68,

    # P2: the SAME workload through a plain exact-match cache (key = raw string).
    #     What percent of queries are a hit? (It only catches literal repeats.)
    "exact_hit_pct": 7,

    # P3: a workload of big requests (~2000 tokens each) through a limiter that
    #     caps REQUESTS per window, not tokens. How many times OVER the token
    #     budget does it let spend go? (spent / budget, as a multiple.)
    "req_limiter_overspend_x": 20,

    # P4: the primary model is in a full outage (every call fails). With a
    #     gateway that falls back to a healthy secondary, what percent of users
    #     still get an answer?
    "outage_success_with_fallback_pct": 99,
}

SEED = 41

# Part 1 knobs
SIM_THRESHOLD = 0.60      # cosine at or above this counts as the same meaning
COST_PER_CALL = 0.01      # made-up dollars per model call, just to price the saving

# Part 2 knobs
BUDGET_TOKENS = 10_000    # tokens allowed per window
REQ_LIMIT = 100           # requests allowed per window (the naive limiter)

# Part 3 knobs
PRIMARY_FAIL = 0.30       # per-attempt failure of the primary model (transient)
SECONDARY_FAIL = 0.10     # per-attempt failure of the secondary (the fallback)
MAX_TRIES = 3             # attempts per model before the gateway gives up on it
TRIALS = 100_000          # requests per success-rate measurement


# ---------------------------------------------------------------------------
# The four TODOs: the load-bearing line of each trick. One expression each.
# ---------------------------------------------------------------------------

def cosine(a, b):
    """TODO 1, the meaning-distance. a and b are sparse unit vectors (dicts of
    dimension -> weight), already normalised to length 1 by embed(). The cosine
    of two unit vectors is just their dot product: sum the weights on the
    dimensions they share."""
    return sum(a[k] * b[k] for k in a if k in b)


def is_cache_hit(best_sim, threshold):
    """TODO 2, the semantic-cache decision. best_sim is the closest cached
    query's cosine to the new one. It is the same meaning, so a hit, when that
    similarity reaches the threshold."""
    return best_sim >= threshold


def can_admit(available_tokens, cost):
    """TODO 3, the token bucket. A request costs `cost` tokens. Admit it only if
    the bucket still holds at least that many. This meters tokens, the thing you
    actually pay for, not request count."""
    return available_tokens >= cost


def gateway_ok(primary_ok, secondary_ok):
    """TODO 4, the fallback. The user gets an answer if the primary succeeded,
    or, when it did not and we fell back, if the secondary did."""
    return primary_ok or secondary_ok


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if cosine({"x": 1.0}, {"x": 1.0}) is None:
        return 1
    if is_cache_hit(0.9, 0.6) is None:
        return 2
    if can_admit(100, 50) is None:
        return 3
    if gateway_ok(False, True) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# Part 1 helpers: a toy embedding and two caches.
# ---------------------------------------------------------------------------

STOPWORDS = {
    "how", "do", "does", "did", "i", "my", "me", "to", "can", "could", "the",
    "what", "whats", "is", "a", "an", "of", "for", "in", "on", "and", "or",
    "with", "please", "you", "your", "it", "this", "that", "want", "need",
    "will", "be", "am", "are", "if", "so", "we", "us", "there", "when",
    "where", "which", "who", "them", "they", "im", "ive", "id", "would",
    "should", "help", "any", "some", "about", "from", "at", "get", "got",
}


def tokenize(text):
    """Lowercase, pull out words, drop the generic filler. What is left is the
    content words that carry the meaning."""
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS]


def embed(text):
    """The toy embedding: a bag of content words, normalised to a unit vector.
    Two queries built from the same content words point the same way, so their
    cosine is high. No model, no API, just the words themselves. This is the
    same shape as Day 38's embedding, only hand-rolled and tiny."""
    toks = set(tokenize(text))
    if not toks:
        return {}
    w = 1.0 / math.sqrt(len(toks))      # each dim is 1 before normalising
    return {t: w for t in toks}


class SemanticCache:
    """Keys by meaning. Stores (vector, answer) pairs and, for a new query,
    finds the nearest stored vector by cosine. If that is close enough, it is a
    hit and we return the stored answer. Otherwise it is a miss."""

    def __init__(self, threshold):
        self.threshold = threshold
        self.entries = []               # list of (vector, answer)

    def lookup(self, vector):
        best_sim, best_answer = 0.0, None
        for v, answer in self.entries:
            s = cosine(vector, v)
            if s > best_sim:
                best_sim, best_answer = s, answer
        if best_answer is not None and is_cache_hit(best_sim, self.threshold):
            return best_answer          # hit
        return None                     # miss

    def store(self, vector, answer):
        self.entries.append((vector, answer))


class ExactCache:
    """Keys by the raw string. A hit only when the exact same text comes back."""

    def __init__(self):
        self.store_ = {}

    def lookup(self, text):
        return self.store_.get(text)

    def store(self, text, answer):
        self.store_[text] = answer


def build_workload(rng):
    """A realistic support-chat workload: five questions, each asked many ways
    (paraphrases), plus a few genuinely one-off questions, plus a couple of
    word-for-word repeats. Returns the shuffled list of query strings."""
    families = [
        # reset password
        ["reset my password", "how do i reset my password",
         "how can i reset my password", "i forgot my password reset",
         "steps to reset my password", "reset password please"],
        # cancel subscription
        ["cancel my subscription", "how do i cancel my subscription",
         "how to cancel my subscription", "i want to cancel my subscription",
         "cancel subscription now", "cancel my subscription please"],
        # track order
        ["track my order", "how do i track my order",
         "how can i track my order", "track my order status",
         "i want to track my order", "track order please"],
        # refund
        ["refund my payment", "how do i refund my payment",
         "how to refund my payment", "i want a refund payment",
         "refund payment please", "refund my payment now"],
        # change email
        ["change my email address", "how do i change my email address",
         "how to change my email address", "change email address please",
         "i want to change my email address", "change my email address now"],
    ]
    # genuine one-offs: no paraphrases, distinct content words
    oneoffs = [
        "upgrade to the business plan",
        "export all invoices as csv",
        "enable two factor authentication",
        "delete my analytics workspace",
        "connect the slack integration",
        "increase the api rate limit",
        "download the mobile app",
        "transfer ownership of the team",
    ]
    queries = []
    for fam in families:
        queries.extend(fam)
    queries.extend(oneoffs)
    # a couple of word-for-word repeats, the ONLY thing an exact cache catches
    queries.append("how do i reset my password")
    queries.append("track my order")
    queries.append("cancel my subscription")

    rng.shuffle(queries)
    return queries


def run_semantic(queries):
    cache = SemanticCache(SIM_THRESHOLD)
    hits = calls = 0
    for q in queries:
        v = embed(q)
        answer = cache.lookup(v)
        if answer is not None:
            hits += 1
        else:
            calls += 1                  # a miss means we call the model
            cache.store(v, f"answer::{q}")
    return hits, calls


def run_exact(queries):
    cache = ExactCache()
    hits = calls = 0
    for q in queries:
        answer = cache.lookup(q)
        if answer is not None:
            hits += 1
        else:
            calls += 1
            cache.store(q, f"answer::{q}")
    return hits, calls


def part1():
    print("=" * 78)
    print("Part 1: the semantic cache. Key by meaning, and the paraphrases")
    print("        collapse onto one model call")
    print("=" * 78)
    rng = random.Random(SEED)
    queries = build_workload(rng)
    total = len(queries)

    sem_hits, sem_calls = run_semantic(queries)
    exa_hits, exa_calls = run_exact(queries)

    sem_hit_pct = sem_hits / total * 100
    exa_hit_pct = exa_hits / total * 100

    print(f"  workload: {total} queries, mostly paraphrases of 5 questions,")
    print("  a handful of one-offs, and 3 word-for-word repeats.")
    print(f"  cosine threshold for 'same meaning': {SIM_THRESHOLD}")
    print()
    print(f"  {'cache':<18}{'hits':>8}{'model calls':>14}{'hit rate':>12}")
    print(f"  {'no cache':<18}{0:>8}{total:>14}{0.0:>11.1f}%")
    print(f"  {'exact-match':<18}{exa_hits:>8}{exa_calls:>14}{exa_hit_pct:>11.1f}%")
    print(f"  {'semantic':<18}{sem_hits:>8}{sem_calls:>14}{sem_hit_pct:>11.1f}%")
    print()
    saved_vs_exact = exa_calls - sem_calls
    print(f"  The exact-match cache caught only the {exa_hits} literal repeats. Every")
    print("  paraphrase looked like a brand new string to it, so it called the")
    print(f"  model {exa_calls} times. The semantic cache saw the meaning behind the")
    print(f"  wording and called the model just {sem_calls} times.")
    print(f"  model calls saved vs exact-match: {saved_vs_exact}  "
          f"(${saved_vs_exact * COST_PER_CALL:.2f} at ${COST_PER_CALL:.2f}/call)")
    print("  Same workload. One cache keys by string and saves almost nothing,")
    print("  the other keys by meaning and cuts calls by more than half.")
    return sem_hit_pct, exa_hit_pct


# ---------------------------------------------------------------------------
# Part 2 helpers: two limiters over the same budget.
# ---------------------------------------------------------------------------

class TokenBucket:
    """Meters tokens. Admits a request only while the budget can still cover its
    token cost. This is the thing you actually pay for."""

    def __init__(self, budget):
        self.budget = budget
        self.spent = 0
        self.admitted = 0

    def offer(self, cost):
        if can_admit(self.budget - self.spent, cost):
            self.spent += cost
            self.admitted += 1
            return True
        return False


class RequestLimiter:
    """Meters request COUNT. Admits the first REQ_LIMIT requests regardless of
    how many tokens each one costs. It has no idea what it is spending."""

    def __init__(self, limit):
        self.limit = limit
        self.count = 0
        self.spent = 0
        self.admitted = 0

    def offer(self, cost):
        if self.count < self.limit:
            self.count += 1
            self.spent += cost
            self.admitted += 1
            return True
        return False


def make_requests(rng, n, lo, hi):
    """n requests, each costing a uniformly random number of tokens in [lo, hi]."""
    return [rng.randint(lo, hi) for _ in range(n)]


def run_limiter(limiter, requests):
    for cost in requests:
        limiter.offer(cost)
    return limiter.admitted, limiter.spent


def part2():
    print("\n" + "=" * 78)
    print("Part 2: token-based rate limiting. Meter tokens, not requests, because")
    print("        the bill is per token")
    print("=" * 78)
    rng = random.Random(SEED + 1)
    small = make_requests(rng, 300, 30, 70)       # many small requests
    large = make_requests(rng, 150, 1500, 2500)   # few big requests

    print(f"  budget: {BUDGET_TOKENS:,} tokens per window.")
    print(f"  the naive limiter instead caps requests at {REQ_LIMIT} per window,")
    print(f"  which quietly assumes every request is about "
          f"{BUDGET_TOKENS // REQ_LIMIT} tokens.")
    print()
    print(f"  {'workload':<22}{'limiter':<16}{'admitted':>10}{'tokens spent':>15}")

    overspend_x = None
    for label, reqs in [("many small (~50 tok)", small), ("few large (~2000 tok)", large)]:
        tb_adm, tb_spent = run_limiter(TokenBucket(BUDGET_TOKENS), reqs)
        rl_adm, rl_spent = run_limiter(RequestLimiter(REQ_LIMIT), reqs)
        print(f"  {label:<22}{'token bucket':<16}{tb_adm:>10}{tb_spent:>15,}")
        print(f"  {'':<22}{'request cap':<16}{rl_adm:>10}{rl_spent:>15,}")
        if label.startswith("few large"):
            overspend_x = rl_spent / BUDGET_TOKENS
    print()
    print("  On the small workload the request cap stopped at 100 requests and")
    print("  spent only about half the budget, turning away requests that would")
    print("  have fit fine. On the large workload it waved through 100 big")
    print(f"  requests and blew the budget by about {overspend_x:.0f}x.")
    print("  The token bucket held spend at the budget in BOTH cases, because it")
    print("  meters the token, which is what the invoice is counted in.")
    return overspend_x


# ---------------------------------------------------------------------------
# Part 3 helpers: a model gateway with retries and fallback.
# ---------------------------------------------------------------------------

def model_attempt(fail_prob, tries, rng):
    """One model, up to `tries` attempts. Succeeds if any single attempt lands.
    Each attempt fails independently with probability fail_prob."""
    return any(rng.random() >= fail_prob for _ in range(tries))


def serve(rng, primary_fail, secondary_fail, tries, use_fallback):
    """The gateway serving one request. Try the primary up to `tries` times.
    If it is still failing and fallback is on, try the secondary up to `tries`
    times. The user succeeds if either model answered."""
    primary_ok = model_attempt(primary_fail, tries, rng)
    secondary_ok = False
    if use_fallback and not primary_ok:
        secondary_ok = model_attempt(secondary_fail, tries, rng)
    return gateway_ok(primary_ok, secondary_ok)


def success_rate(primary_fail, secondary_fail, tries, use_fallback, seed):
    rng = random.Random(seed)
    ok = sum(serve(rng, primary_fail, secondary_fail, tries, use_fallback)
             for _ in range(TRIALS))
    return ok / TRIALS * 100


def part3():
    print("\n" + "=" * 78)
    print("Part 3: the model gateway. Retries for blips, fallback for outages")
    print("=" * 78)
    print(f"  primary fails {int(PRIMARY_FAIL * 100)}% of attempts, secondary "
          f"{int(SECONDARY_FAIL * 100)}%, up to {MAX_TRIES} tries each.")
    print()
    print("  Normal day (failures are independent blips):")
    one = success_rate(PRIMARY_FAIL, SECONDARY_FAIL, 1, False, SEED + 2)
    retry = success_rate(PRIMARY_FAIL, SECONDARY_FAIL, MAX_TRIES, False, SEED + 3)
    retry_fb = success_rate(PRIMARY_FAIL, SECONDARY_FAIL, MAX_TRIES, True, SEED + 4)
    print(f"    primary, 1 try, no fallback:        {one:6.2f}%")
    print(f"    primary, {MAX_TRIES} tries, no fallback:       {retry:6.2f}%")
    print(f"    primary {MAX_TRIES} tries + fallback:          {retry_fb:6.2f}%")
    print("  Retries alone do most of the work when failures are independent:")
    print("  one bad roll rarely repeats three times. Fallback just tops it off.")
    print()
    print("  Outage day (the primary is fully down, every attempt fails):")
    out_no = success_rate(1.0, SECONDARY_FAIL, MAX_TRIES, False, SEED + 5)
    out_fb = success_rate(1.0, SECONDARY_FAIL, MAX_TRIES, True, SEED + 6)
    print(f"    primary {MAX_TRIES} tries, no fallback:       {out_no:6.2f}%")
    print(f"    primary {MAX_TRIES} tries + fallback:          {out_fb:6.2f}%")
    print("  Now retries are useless: three failures out of three every time.")
    print("  Only the fallback keeps users served. This is the day the second")
    print("  provider, and a semantic cache serving yesterday's answers, earn")
    print("  their keep. Fallback is cheap insurance you are glad to have paid.")
    return out_fb, out_no


def verdict(name, predicted, actual, unit="%"):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>7.1f} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    note = "     close enough" if diff <= max(3.0, 0.1 * abs(predicted)) \
        else f"  off by {diff:.1f}"
    print(f"  {name:<34} you = {predicted:>6.1f}   actual = {actual:>7.1f} {unit}  {note}")


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

    sem_hit, exa_hit = part1()
    overspend_x = part2()
    out_fb, out_no = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 semantic cache hit rate", PREDICTIONS["semantic_hit_pct"], sem_hit)
    verdict("P2 exact-match hit rate", PREDICTIONS["exact_hit_pct"], exa_hit)
    verdict("P3 request-cap overspend", PREDICTIONS["req_limiter_overspend_x"],
            overspend_x, "x")
    verdict("P4 outage success w/ fallback",
            PREDICTIONS["outage_success_with_fallback_pct"], out_fb)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Same support-chat workload, two caches. Keyed by string, the cache")
    print(f"  hit {exa_hit:.0f}% of the time and saved almost nothing. Keyed by meaning,")
    print(f"  it hit {sem_hit:.0f}% and cut model calls by more than half. That gap is the")
    print("  whole case for a semantic cache.")
    print(f"  A request cap let {overspend_x:.0f}x the token budget through on big requests,")
    print("  because it meters the wrong thing. A token bucket meters tokens and")
    print("  holds the line. And when the primary went fully down, success without")
    print(f"  fallback collapsed to {out_no:.0f}% while the gateway's fallback held it")
    print(f"  at {out_fb:.0f}%.")
    print("  None of this is AI magic. It is caching, rate limiting and failover,")
    print("  the same three moves from weeks 3, 4 and 5, pointed at a GPU.")
    print()


if __name__ == "__main__":
    main()
