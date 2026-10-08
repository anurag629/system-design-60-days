"""
Day 36 lab: how an LLM actually serves a request. Two phases, prefill and
decode, and the one fact that explains your whole token bill: decode is
memory-bound, not compute-bound.

This is the full working solution. The starter file is inference.py.
Run it:      python3 solution.py

Standard library only. No real model, no API, no network, no numpy. Everything
is a deterministic COST MODEL: we give the "GPU" a memory bandwidth and a
compute rate, give the "model" a parameter count, and work out how long each
phase takes from first principles. The one seeded random bit is a small
per-step timing jitter, so the "measurement" (a least-squares fit) has
something real to recover. Same seed, same numbers, every run.

The toy machine and model (made up, but the right order of magnitude):
  - a 7 billion parameter model stored in fp16, so 2 bytes per parameter,
    which is 14 GB of weights that have to be read to run the model once.
  - a forward pass costs about 2 FLOPs per parameter per token (one multiply,
    one add), so 14 GFLOPs per token.
  - a GPU with 2 TB/s of memory bandwidth and 300 TFLOP/s of compute.

The big ideas:
  - Prefill reads the whole prompt in ONE parallel pass. All N prompt tokens go
    through the model together, so the weights are read once for the lot. That
    makes prefill compute-bound and cheap per token. Its cost is the
    time-to-first-token (TTFT).
  - Decode generates output tokens ONE AT A TIME. Each new token is a full pass
    over the model, reading all 14 GB of weights again, to do the arithmetic of
    a single token. That one step is the time-per-output-token (TPOT), and it is
    set by memory bandwidth, not compute.
  - So total latency is TTFT + M * TPOT: a flat start-up cost, then a straight
    line in the number of OUTPUT tokens. A long output costs far more than a
    long prompt of the same length, because output is sequential and input is
    parallel. On this machine one output token costs about 150 prompt tokens.
  - Why 150? A batch-1 decode step does about 1 FLOP per byte it reads, while
    the machine can do 150 FLOPs in the time it takes to read one byte. The
    compute units sit idle 149/150 of the time. That gap is the memory wall, and
    it is why batching many requests behind one weight read is the only way to
    get throughput. That is Day 37.
"""

import random
import sys

PREDICTIONS = {
    # P1: TPOT, the time for ONE decode step, i.e. the model producing one more
    #     output token. In milliseconds. (Hint: a step reads all 14 GB of
    #     weights at 2 TB/s.)
    "tpot_ms": 7,

    # P2: one OUTPUT token versus one PROMPT token. How many times more wall time
    #     does generating a single output token cost than feeding in a single
    #     prompt token? (Prompt tokens ride through prefill in one shared pass.)
    "output_over_input": 150,

    # P3: the arithmetic intensity of a batch-1 decode step, in FLOPs per byte.
    #     How much math does the GPU do per byte of weights it drags in?
    "decode_intensity": 1,

    # P4: same 200-token prompt, two replies: one of 50 tokens, one of 500. How
    #     many times longer does the 500-token reply take than the 50-token one?
    "reply_latency_ratio": 10,
}

# ---- the toy model and the toy GPU --------------------------------------
MODEL_PARAMS = 7_000_000_000        # 7B parameter model
BYTES_PER_PARAM = 2                 # fp16 weights
MODEL_BYTES = MODEL_PARAMS * BYTES_PER_PARAM          # 14 GB to read per pass
FLOPS_PER_TOKEN = 2 * MODEL_PARAMS                    # ~2 FLOPs per param per token

MEM_BANDWIDTH = 2.0e12              # 2 TB/s, bytes per second
COMPUTE = 3.0e14                    # 300 TFLOP/s, FLOPs per second

JITTER = 0.05                       # +/- 5% seeded timing noise on a decode step
SEED = 36


# ---------------------------------------------------------------------------
# The four TODOs. Each is one load-bearing line, the physics of inference.
# ---------------------------------------------------------------------------

def roofline_time_s(flops, bytes_moved):
    """TODO 1, the roofline. A step has to BOTH move its bytes from memory and
    do its arithmetic, and it cannot finish before the slower of the two. So its
    time is the max of (bytes / bandwidth) and (flops / compute). Whichever wins
    is the bottleneck for that step."""
    return max(bytes_moved / MEM_BANDWIDTH, flops / COMPUTE)


def prefill_flops(n_prompt):
    """TODO 2, prefill is one parallel pass. All n_prompt tokens go through the
    model together, so the arithmetic is n_prompt tokens' worth in a single
    pass (and the weights are read just once). Return the FLOPs for that pass."""
    return n_prompt * FLOPS_PER_TOKEN


def total_latency_s(ttft_s, n_output, tpot_s):
    """TODO 3, latency is linear in OUTPUT. Decode emits output tokens one at a
    time, each one a full step costing tpot_s. So the total is the first-token
    wait plus one tpot per output token: ttft + M * tpot."""
    return ttft_s + n_output * tpot_s


def arithmetic_intensity(flops, bytes_moved):
    """TODO 4, the number that decides memory-bound vs compute-bound. Arithmetic
    intensity is how many FLOPs you do for each byte you move. Low means you are
    waiting on memory; high means you are waiting on the math units."""
    return flops / bytes_moved


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if roofline_time_s(1.0, 1.0) is None:
        return 1
    if prefill_flops(2) is None:
        return 2
    if total_latency_s(1.0, 3, 1.0) is None:
        return 3
    if arithmetic_intensity(2.0, 1.0) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# The simulator: serve one request, in simulated seconds.
# ---------------------------------------------------------------------------

class InferenceSim:
    """Serves a request as a cost model. Prefill is one pass whose time is the
    TTFT. Decode is n_output sequential steps, each a full pass over the weights.
    A small seeded jitter on each decode step stands in for real-world wobble, so
    the fit in Part 1 has genuine noise to see through."""

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.tpot_nominal = roofline_time_s(FLOPS_PER_TOKEN, MODEL_BYTES)

    def ttft_s(self, n_prompt):
        # Time to first token is the prefill pass: all prompt tokens at once.
        return roofline_time_s(prefill_flops(n_prompt), MODEL_BYTES)

    def serve(self, n_prompt, n_output):
        """Return (ttft, total) in seconds. Decode steps carry +/- JITTER."""
        ttft = self.ttft_s(n_prompt)
        decode = 0.0
        for _ in range(n_output):
            decode += self.tpot_nominal * (1 + self.rng.uniform(-JITTER, JITTER))
        return ttft, ttft + decode


def fit_line(xs, ys):
    """Least-squares fit y = slope * x + intercept, pure Python. Here x is the
    number of output tokens and y is the measured total latency, so the slope is
    the measured TPOT and the intercept is the measured TTFT."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    var = sum((x - mx) ** 2 for x in xs)
    slope = cov / var
    return slope, my - slope * mx


# ---------------------------------------------------------------------------
# The three parts.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: prefill vs decode. One parallel pass, then a token at a time")
    print("=" * 78)
    print(f"  model: {MODEL_PARAMS / 1e9:.0f}B params, fp16, so {MODEL_BYTES / 1e9:.0f} GB of weights to read per pass")
    print(f"  gpu:   {MEM_BANDWIDTH / 1e12:.0f} TB/s memory bandwidth, {COMPUTE / 1e12:.0f} TFLOP/s compute")
    print()

    sim = InferenceSim(SEED)
    prompt = 500

    # Prefill: the whole prompt in one pass. That time IS the TTFT.
    ttft = sim.ttft_s(prompt)
    tpot = sim.tpot_nominal
    print(f"  TTFT (prefill a {prompt}-token prompt, one pass): {ttft * 1e3:7.2f} ms")
    print(f"  TPOT (one decode step, one output token):        {tpot * 1e3:7.2f} ms")
    print()

    # Measure: sweep the output length, record total latency, fit a line.
    outs = [1, 25, 50, 100, 200, 400, 800]
    totals = []
    print(f"  Serving the same {prompt}-token prompt with growing output:")
    print(f"    {'output tokens':>14}{'total latency':>16}")
    for m in outs:
        _, total = sim.serve(prompt, m)
        totals.append(total)
        print(f"    {m:>14}{total * 1e3:>13.1f} ms")
    slope, intercept = fit_line(outs, totals)
    print()
    print("  Fit total = intercept + slope * (output tokens):")
    print(f"    measured TPOT (slope)     = {slope * 1e3:6.3f} ms per output token")
    print(f"    measured TTFT (intercept) = {intercept * 1e3:6.2f} ms")
    print("  A straight line. Total latency is TTFT + M * TPOT, linear in OUTPUT")
    print("  tokens. The prompt sets a one-off start cost; every output token")
    print("  after that adds a fixed TPOT, because the model runs once per token.")
    print()

    # The asymmetry: 500 in the prompt vs 500 in the output.
    input_500 = sim.ttft_s(500)                 # one parallel pass
    output_500 = 500 * tpot                      # 500 sequential passes
    ratio = output_500 / input_500
    print("  Now the punchline. 500 tokens as INPUT vs 500 tokens as OUTPUT:")
    print(f"    500 prompt tokens  (prefill, one pass) : {input_500 * 1e3:8.2f} ms")
    print(f"    500 output tokens  (decode, 500 passes): {output_500 * 1e3:8.2f} ms")
    print(f"    output is {ratio:.0f}x slower, for the SAME number of tokens")
    print("  Input tokens share one pass. Output tokens each need their own. That")
    print("  asymmetry is the whole economics of serving an LLM.")

    per_input = input_500 / 500
    per_output = tpot
    return tpot * 1e3, per_output / per_input


def part2():
    print("\n" + "=" * 78)
    print("Part 2: memory-bound, not compute-bound. Why batching is the whole game")
    print("=" * 78)

    # One decode step: read all the weights, do one token's worth of math.
    flops = FLOPS_PER_TOKEN
    bytes_moved = MODEL_BYTES
    intensity = arithmetic_intensity(flops, bytes_moved)
    balance = COMPUTE / MEM_BANDWIDTH
    mem_time = bytes_moved / MEM_BANDWIDTH
    compute_time = flops / COMPUTE

    print("  A single decode step, batch of 1:")
    print(f"    reads {bytes_moved / 1e9:.0f} GB of weights, does {flops / 1e9:.0f} GFLOPs of math")
    print(f"    time if memory-bound  = {mem_time * 1e3:7.3f} ms   (bytes / bandwidth)")
    print(f"    time if compute-bound = {compute_time * 1e3:7.3f} ms   (flops / compute)")
    print(f"    memory loses by {mem_time / compute_time:.0f}x, so the step waits on MEMORY.")
    print()
    print(f"    arithmetic intensity = {intensity:.1f} FLOP/byte  (math done per byte read)")
    print(f"    machine balance      = {balance:.0f} FLOP/byte  (compute / bandwidth)")
    print(f"    {intensity:.0f} is far below {balance:.0f}, so the math units are idle "
          f"{(1 - intensity / balance) * 100:.1f}% of the time.")
    print("  The GPU reads 14 GB to do the arithmetic of ONE token. That is the")
    print("  memory wall: the weights, not the maths, set the clock.")
    print()

    # Batching: one weight read, many tokens. Intensity scales with batch size.
    print("  So reuse the read. Batch B requests, and one 14 GB read feeds all B")
    print("  tokens. Intensity becomes B FLOP/byte, and throughput climbs until")
    print("  the step finally turns compute-bound (at B = machine balance).")
    print()
    print(f"    {'batch':>6}{'intensity':>12}{'step time':>13}{'throughput':>16}{'bound by':>12}")
    for b in [1, 8, 16, 64, 150, 300]:
        step = roofline_time_s(b * flops, bytes_moved)
        tput = b / step
        bound = "memory" if b * intensity <= balance else "compute"
        print(f"    {b:>6}{b * intensity:>10.0f}  {step * 1e3:>10.3f} ms"
              f"{tput:>12,.0f} tok/s{bound:>12}")
    print()
    print("  From batch 1 to batch 150 the step time barely moves, but throughput")
    print("  goes up 150x, because the one expensive read now pays for 150 tokens.")
    print("  Past 150 the math units are full, so throughput plateaus and latency")
    print("  starts to climb. THIS is why an LLM server batches: Day 37.")
    return intensity, balance


def part3():
    print("\n" + "=" * 78)
    print("Part 3: your token bill. Output is the part that costs")
    print("=" * 78)

    sim = InferenceSim(SEED)
    prompt = 200
    tpot = sim.tpot_nominal

    short_ttft, short = sim.serve(prompt, 50)
    _, long = sim.serve(prompt, 500)
    lat_ratio = long / short

    # Illustrative API pricing. Output is priced higher than input almost
    # everywhere, and it is also the slow part, so it dominates twice over.
    in_price = 0.50 / 1e6       # dollars per input token
    out_price = 1.50 / 1e6      # dollars per output token (3x input, typical)
    cost_50 = prompt * in_price + 50 * out_price
    cost_500 = prompt * in_price + 500 * out_price
    cost_ratio = cost_500 / cost_50

    print(f"  Same {prompt}-token prompt, two replies. TTFT is a flat {short_ttft * 1e3:.1f} ms,")
    print(f"  then every output token adds {tpot * 1e3:.1f} ms.")
    print()
    print(f"    {'reply':>12}{'latency':>14}{'cost':>14}")
    print(f"    {'50 tokens':>12}{short * 1e3:>11.1f} ms{'$' + format(cost_50, '.6f'):>14}")
    print(f"    {'500 tokens':>12}{long * 1e3:>11.1f} ms{'$' + format(cost_500, '.6f'):>14}")
    print()
    print(f"  10x the output tokens -> {lat_ratio:.1f}x the latency and "
          f"{cost_ratio:.1f}x the cost.")
    print("  Latency scales almost 1:1 with output because decode dwarfs the fixed")
    print("  prefill. Cost scales with output because output tokens are priced")
    print("  higher AND there are more of them. A chatbot that streams 500 tokens")
    print("  is a different animal from one that returns 50, on both the clock and")
    print("  the invoice. Trim the output before you trim anything else.")
    print()
    # A quick extrapolation so the number has a home.
    daily = 100_000
    month_50 = cost_50 * daily * 30
    month_500 = cost_500 * daily * 30
    print(f"  At {daily:,} replies a day: the 50-token answer costs ${month_50:,.0f} a")
    print(f"  month, the 500-token answer ${month_500:,.0f}. Same prompt, same model.")
    return lat_ratio


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>8,.2f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<34} you = {predicted:>7,.1f}   actual = {actual:>8,.2f} {unit}  {note}")


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

    tpot_ms, output_over_input = part1()
    decode_intensity, balance = part2()
    reply_ratio = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 TPOT per output token", PREDICTIONS["tpot_ms"], tpot_ms, "ms")
    verdict("P2 output vs input token", PREDICTIONS["output_over_input"], output_over_input, "x")
    verdict("P3 decode arithmetic intensity", PREDICTIONS["decode_intensity"], decode_intensity, "FLOP/byte")
    verdict("P4 500-token vs 50-token reply", PREDICTIONS["reply_latency_ratio"], reply_ratio, "x")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  One decode step reads all {MODEL_BYTES / 1e9:.0f} GB of weights to make a single")
    print(f"  token: {tpot_ms:.0f} ms, set by memory bandwidth, not by the {COMPUTE / 1e12:.0f} TFLOP/s of")
    print(f"  compute that sits {balance:.0f}x idle. So an output token costs about")
    print(f"  {output_over_input:.0f}x a prompt token, total latency is TTFT + M * TPOT (a line in")
    print(f"  M), and the same {balance:.0f} is the batch size you need to put the compute")
    print("  to work. Memory-bound decode is the one fact that explains prefill vs")
    print("  decode, your latency, your bill, and why Day 37 is all about batching.")
    print()


if __name__ == "__main__":
    main()
