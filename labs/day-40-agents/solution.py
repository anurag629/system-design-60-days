"""
Day 40 lab: agents, and why the token bill explodes. An agent loops: think,
call a tool, read the result, repeat until done. The quiet, expensive truth is
that the model keeps no memory between calls, so the harness re-sends the WHOLE
conversation so far on every single step. The context grows, the per-step cost
grows with it, and the total is the SUM over steps, which climbs roughly
quadratically with the number of steps.

This is the full working solution. The starter file is agent_loop.py.
Run it:      python3 solution.py

Standard library only, no model, no API, no network, no files. Everything is a
deterministic cost simulation. Token counts per step come from a seeded RNG, so
the same run reproduces to the digit. We do not call a real model; we model the
accounting that every agent framework pays.

The big ideas:
  - The loop re-sends everything. Call i sees the system prompt and tool
    schemas (fixed, re-sent every step), the task, and every prior step's
    assistant turn plus tool result. So the input to call i grows by a fixed
    chunk each step, and summing a growing input over K steps is ~ K^2 / 2.
    Doubling the steps roughly quadruples the cost.
  - Context management is the big lever. Keep the last few steps verbatim and
    collapse the older ones into one small fixed summary. Now the input per
    step is bounded, so the total grows LINEARLY in K instead of quadratically.
    On a long task that is most of the bill.
  - Fan-out brings back old friends. One user request becomes K sequential
    model calls, so latency is K round trips (Day 1), and the slow-call tail
    (Day 4) now gets K chances to fire, so a long loop is almost guaranteed to
    hit at least one slow step. More steps means more cost, more latency, and
    more ways to go wrong. A tight loop beats a sprawling one.
"""

import random
import sys

PREDICTIONS = {
    # P1: a NAIVE agent (re-sends the whole context every step). Going from a
    #     10-step task to a 20-step task, by what FACTOR does the total token
    #     cost grow? Linear would say 2x. What does "re-send everything" say?
    "double_steps_cost_factor": 3.2,

    # P2: the naive 20-step run. Its total tokens, as a MULTIPLE of "20 times
    #     the first call" (what you would budget if every call stayed the size
    #     of the first one). How many times bigger than that naive budget?
    "total_vs_k_first_calls": 8.0,

    # P3: context trimming (keep the last 4 steps, summarise the rest) on the
    #     SAME 20-step task. What PERCENT of the naive total tokens does it save?
    "trim_saving_pct": 55,

    # P4: tail latency. Each model call independently hits a slow tail 5% of the
    #     time. Over a 20-step run, what is the chance AT LEAST ONE step is slow?
    "any_slow_pct": 64,
}

SYSTEM_TOKENS = 1500     # system prompt + tool schemas, re-sent on EVERY call
USER_TOKENS = 200        # the user's task, also along for every call
KEEP = 4                 # context trimming keeps the last KEEP steps verbatim
SUMMARY_TOKENS = 300     # the older steps collapse into one fixed-size summary
PRICE_IN = 3.0 / 1_000_000    # dollars per input token  (example pricing)
PRICE_OUT = 15.0 / 1_000_000  # dollars per output token (output is pricier)

K_HEADLINE = 20          # the headline task length
K_SWEEP = (5, 10, 15, 20)

# latency model (Part 3), all in milliseconds
BASE_RTT = 120           # client to server and back, once per call (Day 1)
PREFILL_PER_TOKEN = 0.03  # time to read the whole prompt, grows with context
DECODE_PER_TOKEN = 0.25   # time to generate output, one token at a time
TAIL_EXTRA_MS = 2000     # a slow call: a queue wait, a GC pause, a retry (Day 4)
P_SLOW = 0.05            # per-call chance of hitting that tail
LAT_TRIALS = 20_000      # Monte Carlo runs for the latency measurement
SEED = 40


# ---------------------------------------------------------------------------
# The four TODOs: the whole cost story in four load-bearing lines.
# ---------------------------------------------------------------------------

def naive_input_tokens(system, user, history):
    """TODO 1, the heart of Part 1. The model remembers nothing between calls,
    so the WHOLE conversation is re-sent as input: the fixed system prompt and
    tool schemas, the user task, and every prior step's assistant turn plus its
    tool result. history is a list of (assistant_tokens, observation_tokens)."""
    return system + user + sum(a + o for (a, o) in history)


def trimmed_input_tokens(system, user, history, keep, summary_tokens):
    """TODO 2, the heart of Part 2. Keep only the last `keep` steps verbatim and
    collapse everything older into one fixed-size summary. Once the history is
    longer than `keep`, the input per step stops growing: it is the fixed
    overhead, plus the summary, plus the last `keep` steps. That bounded input
    is what turns a quadratic bill into a linear one."""
    recent = history[-keep:]
    summary = summary_tokens if len(history) > keep else 0
    return system + user + summary + sum(a + o for (a, o) in recent)


def call_cost(input_tokens, output_tokens, price_in, price_out):
    """TODO 3, the billing. Input and output tokens are charged at different
    rates (output is the pricier one), so one call costs input times the input
    price plus output times the output price."""
    return input_tokens * price_in + output_tokens * price_out


def any_slow_probability(p_slow, steps):
    """TODO 4, the tail over a loop (Day 4). If each of `steps` calls is slow
    with probability p_slow and they are independent, the chance that at least
    one is slow is one minus the chance that every single one is fast."""
    return 1 - (1 - p_slow) ** steps


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if naive_input_tokens(10, 5, [(3, 4)]) is None:
        return 1
    if trimmed_input_tokens(10, 5, [(3, 4), (2, 2)], 1, 2) is None:
        return 2
    if call_cost(100, 10, 1.0, 2.0) is None:
        return 3
    if any_slow_probability(0.1, 5) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# The agent loop, as pure accounting. No model is called; we tally what a
# real framework would send on each turn.
# ---------------------------------------------------------------------------

def generate_steps(k, rng):
    """One task as a list of steps. Each step is (assistant_tokens,
    observation_tokens): what the model generates that turn (reasoning plus the
    tool call), and the tool result that gets appended to the context for the
    next turn. Tool results are usually bigger than the model's own turn."""
    steps = []
    for _ in range(k):
        assistant = rng.randint(300, 600)     # the model's output this step
        observation = rng.randint(800, 1600)  # the tool result, appended after
        steps.append((assistant, observation))
    return steps


def run_naive(steps, system, user, price_in, price_out):
    """Walk the loop the naive way: every call re-sends the whole context.
    Returns (total_input, total_output, total_cost, per_call_input)."""
    history = []
    total_in = total_out = 0
    cost = 0.0
    per_call_in = []
    for (assistant, observation) in steps:
        in_tok = naive_input_tokens(system, user, history)      # TODO 1
        out_tok = assistant
        total_in += in_tok
        total_out += out_tok
        cost += call_cost(in_tok, out_tok, price_in, price_out)  # TODO 3
        per_call_in.append(in_tok)
        history.append((assistant, observation))  # this turn joins the context
    return total_in, total_out, cost, per_call_in


def run_trimmed(steps, system, user, keep, summary_tokens, price_in, price_out):
    """Walk the same loop, but cap the context: keep the last `keep` steps and
    summarise the rest. Returns (total_input, total_output, total_cost)."""
    history = []
    total_in = total_out = 0
    cost = 0.0
    for (assistant, observation) in steps:
        in_tok = trimmed_input_tokens(system, user, history,
                                      keep, summary_tokens)      # TODO 2
        out_tok = assistant
        total_in += in_tok
        total_out += out_tok
        cost += call_cost(in_tok, out_tok, price_in, price_out)  # TODO 3
        history.append((assistant, observation))
    return total_in, total_out, cost


def call_latency_ms(input_tokens, output_tokens, slow):
    """One call's wall-clock time: a round trip, prefill that grows with the
    input, decode that grows with the output, plus a tail hit if this call was
    the slow one. Bigger context means slower prefill, so a fat loop is slow
    even before the tail fires."""
    ms = (BASE_RTT
          + input_tokens * PREFILL_PER_TOKEN
          + output_tokens * DECODE_PER_TOKEN)
    if slow:
        ms += TAIL_EXTRA_MS
    return ms


# ---------------------------------------------------------------------------
# The three parts.
# ---------------------------------------------------------------------------

def part1(steps_by_k):
    print("=" * 78)
    print("Part 1: the loop re-sends everything, so cost grows ~ quadratically")
    print("=" * 78)
    steps = steps_by_k[K_HEADLINE]
    total_in, total_out, cost, per_call = run_naive(
        steps, SYSTEM_TOKENS, USER_TOKENS, PRICE_IN, PRICE_OUT)
    total_tok = total_in + total_out

    print(f"  A {K_HEADLINE}-step task. The model keeps no memory between calls, so")
    print("  every call re-sends the whole conversation so far as input.")
    print(f"  Fixed overhead re-sent each call: {SYSTEM_TOKENS + USER_TOKENS:,} tokens"
          " (system + tools + task).")
    print()
    print("  Watch the INPUT to each call climb as the context piles up:")
    print(f"    {'step':>5}{'input tokens':>15}{'this call $':>15}{'running $':>14}")
    running = 0.0
    for i in (1, 2, 3, 5, 10, 15, 20):
        in_tok = per_call[i - 1]
        this_cost = call_cost(in_tok, steps[i - 1][0], PRICE_IN, PRICE_OUT)
        # running cost up to and including step i
        running = sum(call_cost(per_call[j], steps[j][0], PRICE_IN, PRICE_OUT)
                      for j in range(i))
        print(f"    {i:>5}{in_tok:>15,}{this_cost:>14.4f}${running:>13.4f}$")
    print()
    first_call_tok = per_call[0] + steps[0][0]
    naive_budget = K_HEADLINE * first_call_tok
    mult = total_tok / naive_budget
    print(f"  the first call was {first_call_tok:,} tokens. If every call stayed")
    print(f"  that small, {K_HEADLINE} calls would be {naive_budget:,} tokens.")
    print(f"  the run ACTUALLY processed {total_tok:,} tokens, {mult:.1f}x that budget,")
    print(f"  and cost ${cost:.4f} for ONE user request.")
    print()

    print("  Now double the steps and watch the cost more than double:")
    print(f"    {'steps':>6}{'total tokens':>16}{'cost $':>12}{'cost / steps':>16}")
    costs = {}
    for k in K_SWEEP:
        ti, to, c, _ = run_naive(steps_by_k[k], SYSTEM_TOKENS, USER_TOKENS,
                                 PRICE_IN, PRICE_OUT)
        costs[k] = c
        print(f"    {k:>6}{ti + to:>16,}{c:>11.4f}${c / k:>15.5f}$")
    factor = costs[20] / costs[10]
    print()
    print(f"  10 steps cost ${costs[10]:.4f}, 20 steps cost ${costs[20]:.4f}: a {factor:.2f}x jump")
    print("  for only 2x the steps. Cost-per-step RISES as you add steps, which is")
    print("  the signature of a quadratic. The context you re-send is the tax.")
    return factor, mult, (total_in, total_out, cost)


def part2(steps_by_k, naive_totals):
    print("\n" + "=" * 78)
    print("Part 2: cap the context, and the quadratic collapses to a line")
    print("=" * 78)
    steps = steps_by_k[K_HEADLINE]
    naive_in, naive_out, naive_cost = naive_totals
    naive_tok = naive_in + naive_out

    t_in, t_out, t_cost = run_trimmed(steps, SYSTEM_TOKENS, USER_TOKENS,
                                      KEEP, SUMMARY_TOKENS, PRICE_IN, PRICE_OUT)
    t_tok = t_in + t_out
    saving = (1 - t_tok / naive_tok) * 100
    cost_saving = (1 - t_cost / naive_cost) * 100

    print(f"  Same {K_HEADLINE}-step task. Keep the last {KEEP} steps verbatim, collapse the")
    print(f"  rest into one {SUMMARY_TOKENS}-token summary. The input per step stops growing.")
    print()
    print(f"    {'approach':<14}{'input tok':>14}{'output tok':>13}{'total tok':>13}{'cost $':>11}")
    print(f"    {'naive':<14}{naive_in:>14,}{naive_out:>13,}{naive_tok:>13,}{naive_cost:>10.4f}$")
    print(f"    {'trimmed':<14}{t_in:>14,}{t_out:>13,}{t_tok:>13,}{t_cost:>10.4f}$")
    print()
    print(f"  trimming saved {saving:.1f}% of the tokens and {cost_saving:.1f}% of the dollars")
    print("  (dollars save a touch less, because output tokens are untouched and")
    print("  billed higher). Output is the same; all the saving is on re-sent input.")
    print()

    print("  The real win shows up as the task gets longer. Naive vs trimmed total")
    print("  tokens, by task length:")
    print(f"    {'steps':>6}{'naive tok':>14}{'trimmed tok':>14}{'naive/trim':>13}")
    for k in K_SWEEP:
        ni, no, _, _ = run_naive(steps_by_k[k], SYSTEM_TOKENS, USER_TOKENS,
                                 PRICE_IN, PRICE_OUT)
        ti2, to2, _ = run_trimmed(steps_by_k[k], SYSTEM_TOKENS, USER_TOKENS,
                                  KEEP, SUMMARY_TOKENS, PRICE_IN, PRICE_OUT)
        nt = ni + no
        tt = ti2 + to2
        print(f"    {k:>6}{nt:>14,}{tt:>14,}{nt / tt:>12.2f}x")
    print()
    print("  Naive climbs quadratically, trimmed climbs linearly, so the gap widens")
    print("  with every step. This one lever, what you keep in the context, is the")
    print("  biggest knob on an agent's bill. Prompt caching is the other one: it")
    print("  cuts the price of the re-sent prefix, but the SHAPE stays the same.")
    return saving


def part3(steps_by_k):
    print("\n" + "=" * 78)
    print("Part 3: one request, K round trips, and the tail fires K times")
    print("=" * 78)
    steps = steps_by_k[K_HEADLINE]
    _, _, _, naive_per_call = run_naive(steps, SYSTEM_TOKENS, USER_TOKENS,
                                        PRICE_IN, PRICE_OUT)

    # per-call input under trimming, for the latency comparison
    trimmed_per_call = []
    hist = []
    for (a, o) in steps:
        trimmed_per_call.append(
            trimmed_input_tokens(SYSTEM_TOKENS, USER_TOKENS, hist,
                                 KEEP, SUMMARY_TOKENS))
        hist.append((a, o))

    out_toks = [a for (a, _) in steps]

    def simulate(per_call_in):
        rng = random.Random(SEED + 7)
        total = 0.0
        any_slow_runs = 0
        for _ in range(LAT_TRIALS):
            run_ms = 0.0
            slow_here = False
            for i in range(K_HEADLINE):
                slow = rng.random() < P_SLOW
                slow_here = slow_here or slow
                run_ms += call_latency_ms(per_call_in[i], out_toks[i], slow)
            total += run_ms
            any_slow_runs += slow_here
        return total / LAT_TRIALS, any_slow_runs / LAT_TRIALS * 100

    naive_mean_ms, any_slow_measured = simulate(naive_per_call)
    trimmed_mean_ms, _ = simulate(trimmed_per_call)

    # a single, standalone call for comparison (the first-step context)
    single_ms = call_latency_ms(naive_per_call[0], out_toks[0], False)

    analytic_any_slow = any_slow_probability(P_SLOW, K_HEADLINE) * 100  # TODO 4

    print(f"  A single model call here is about {single_ms / 1000:.2f}s. But one user")
    print(f"  request becomes {K_HEADLINE} of them, run one after another (Day 1: latency")
    print("  is round trips). You pay the trips back to back, and the context keeps")
    print("  growing, so each trip is a little slower than the last.")
    print()
    print(f"    naive {K_HEADLINE}-step request, mean wall clock:   {naive_mean_ms / 1000:>6.2f}s")
    print(f"    trimmed {K_HEADLINE}-step request, mean wall clock: {trimmed_mean_ms / 1000:>6.2f}s")
    print("    (trimming is faster too: a smaller context prefills quicker.)")
    print()
    print(f"  Now the tail (Day 4). Each call is slow {int(P_SLOW * 100)}% of the time. Over one")
    print(f"  call that is a {int(P_SLOW * 100)}% worry. Over {K_HEADLINE} sequential calls, the chance that")
    print("  AT LEAST ONE is slow is 1 minus (every call fast):")
    print(f"    measured over {LAT_TRIALS:,} runs: {any_slow_measured:.1f}% of runs hit a slow step")
    print(f"    analytic 1 - (1 - {P_SLOW})^{K_HEADLINE}:      {analytic_any_slow:.1f}%")
    print()
    print("  So a long loop is almost guaranteed to stub its toe on the tail at")
    print("  least once, and that one slow step stalls the whole request. More")
    print("  steps means more cost, more latency, and more chances to go wrong.")
    print("  That is the case for a tight tool loop over a sprawling one.")
    return any_slow_measured


def verdict(name, predicted, actual, unit=""):
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

    # Build each task length once, from the same seed, so naive and trimmed
    # walk the EXACT same steps and the comparison is honest.
    rng = random.Random(SEED)
    steps_by_k = {}
    for k in sorted(set(K_SWEEP) | {K_HEADLINE}):
        steps_by_k[k] = generate_steps(k, random.Random(SEED + k))

    factor, mult, naive_totals = part1(steps_by_k)
    saving = part2(steps_by_k, naive_totals)
    any_slow = part3(steps_by_k)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 double-steps cost factor", PREDICTIONS["double_steps_cost_factor"], factor, "x")
    verdict("P2 total vs 20 first-calls", PREDICTIONS["total_vs_k_first_calls"], mult, "x")
    verdict("P3 trim saving", PREDICTIONS["trim_saving_pct"], saving, "%")
    verdict("P4 any step slow", PREDICTIONS["any_slow_pct"], any_slow, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    ni, no, nc = naive_totals
    print(f"  A naive {K_HEADLINE}-step agent re-sent the whole context every step and")
    print(f"  processed {ni + no:,} tokens, {mult:.1f}x what you would have budgeted for")
    print(f"  {K_HEADLINE} plain calls. Double the steps and the bill went up {factor:.1f}x, not 2x:")
    print("  that is the quadratic. Trimming the context (keep the last few,")
    print(f"  summarise the rest) saved {saving:.0f}% of the tokens and turned the curve")
    print("  back into a line. And because one request is K sequential calls, the")
    print(f"  {int(P_SLOW * 100)}% slow tail got {K_HEADLINE} chances and hit {any_slow:.0f}% of runs. Fewer, tighter")
    print("  steps win on all three: cost, latency, and the odds of going wrong.")
    print()


if __name__ == "__main__":
    main()
