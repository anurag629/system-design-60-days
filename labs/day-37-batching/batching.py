"""
Day 37 lab: the KV cache and continuous batching, the vLLM insight. Two things
decide your GPU bill when you serve an LLM, and neither is the model's cleverness.

  1. GPU MEMORY, not compute, caps how many requests you can run at once. The
     model caches a key/value tensor for every past token of every request (the
     KV cache), and that cache grows with sequence length. Long sequences eat the
     memory budget fast, so the batch you can fit shrinks as the conversations
     get longer.

  2. HOW you share the batch decides your throughput. STATIC batching runs a
     fixed group together and waits for the SLOWEST request before any slot
     frees, so short requests sit stuck behind one long one and the GPU goes
     half idle. This is head-of-line blocking, Day 4's "one shared line beats
     many separate lines." CONTINUOUS batching refills a finished slot
     immediately from a shared queue, so the GPU stays full. It wins by a large
     factor when output lengths vary, which they always do.

Run it:      python3 batching.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only. No model, no API, no network, no numpy, no files.
Everything is a deterministic simulation: the KV-cache maths is plain arithmetic,
and the workload of request output lengths comes from a seeded RNG, so the run is
reproducible to the digit. One "step" is one decode pass, in which every active
request in the batch emits one token; we never run a real tensor.

The big ideas:
  - KV cache memory per request = sequence_length * bytes_per_token. Divide the
    memory budget by that and you get the batch size the hardware allows. Double
    the sequence length, halve the batch. Memory is the ceiling, not FLOPs.
  - Static batching's cost is sum over batches of the longest request in each
    batch. With varied output lengths almost every batch holds a long request,
    so the GPU spends most of its slot-time idle, waiting.
  - Continuous batching's cost is close to total_work / batch_size, because a
    freed slot is immediately handed the next waiting request. Near 100 percent
    utilisation, and the throughput multiple over static is large.
  - It is the same lesson as Day 4 (keep the expensive server busy, and a shared
    queue beats separate lines) and Day 2/Day 6 (batching), now pointed at a GPU.

If you get stuck, the full working version is solution.py in this folder.
"""

import random
import sys
from collections import deque

PREDICTIONS = {
    # P1: the KV cache. GPU has 64 GiB of memory left for the KV cache after the
    #     weights. Each token of each request costs 0.5 MiB of KV cache. At a
    #     sequence length of 2048 tokens, how many requests fit at once?
    "fit_at_2048": None,

    # P2: same budget, but now each conversation is 8192 tokens (4x longer). How
    #     many requests fit at once now? (Feel the squeeze.)
    "fit_at_8192": None,

    # P3: static vs continuous batching on a workload of 200 requests with VARIED
    #     output lengths. How many times higher is continuous batching's
    #     throughput? (Guess the multiple. Most people guess 2. It is bigger.)
    "throughput_multiple": None,

    # P4: on that same varied workload, what percent of the GPU's slot-time does
    #     STATIC batching actually spend doing useful work? (How idle is it?)
    "static_utilisation_pct": None,
}

# ---- the model, a 7B-class transformer served in fp16 -----------------------
NUM_LAYERS = 32
NUM_KV_HEADS = 32
HEAD_DIM = 128
DTYPE_BYTES = 2            # fp16, 2 bytes per number
MIB = 1024 ** 2
GIB = 1024 ** 3

GPU_TOTAL_GIB = 80         # one H100-80GB
WEIGHTS_OVERHEAD_GIB = 16  # 7B weights (~14 GiB) plus activations and overhead
KV_BUDGET_BYTES = (GPU_TOTAL_GIB - WEIGHTS_OVERHEAD_GIB) * GIB   # 64 GiB left

# K and V, per layer, per kv-head, head_dim numbers, DTYPE_BYTES each.
KV_BYTES_PER_TOKEN = 2 * NUM_LAYERS * NUM_KV_HEADS * HEAD_DIM * DTYPE_BYTES  # 512 KiB

# ---- the Part 2 workload ----------------------------------------------------
NUM_REQUESTS = 200
MAX_BATCH = 16             # slots that fit in memory at once (the Part 1 ceiling)
SHORT_MIN, SHORT_MAX = 8, 40        # most requests are short answers
LONG_MIN, LONG_MAX = 400, 700       # a few are long essays
LONG_FRACTION = 0.10                # 1 in 10 is a long one
UNIFORM_LEN = 100          # the "everyone the same length" control workload
STEP_MS = 20               # wall-clock for one decode step, to make rates concrete
SEED = 37


# ---------------------------------------------------------------------------
# The four TODOs. Each is one load-bearing line.
# ---------------------------------------------------------------------------

def requests_that_fit(budget_bytes, seq_len, kv_bytes_per_token):
    """TODO 1, the KV-cache ceiling. One request's KV cache is
    seq_len * kv_bytes_per_token. The number that fit at once is the memory
    budget divided by that. This is why memory, not compute, caps the batch."""
    # TODO 1 ------------------------------------------------------------------
    # Whole-number divide the budget by one request's footprint:
    #     return budget_bytes // (seq_len * kv_bytes_per_token)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def static_batch_steps(batch_lengths):
    """TODO 2, head-of-line blocking in one line. A static batch runs together
    and nobody's slot frees until the SLOWEST (longest output) request in the
    batch finishes, so the batch takes as long as its longest member."""
    # TODO 2 ------------------------------------------------------------------
    # The batch lasts as long as its longest request:
    #     return max(batch_lengths)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def admit_count(active_count, max_batch, waiting):
    """TODO 3, the continuous-batching trick. The instant a slot frees, fill it
    from the waiting queue. The number to admit this step is however many free
    slots there are, capped by how many requests are still waiting."""
    # TODO 3 ------------------------------------------------------------------
    # Free slots are (max_batch - active_count); never admit more than are
    # waiting:
    #     return min(max_batch - active_count, waiting)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def throughput_multiple(static_steps, continuous_steps):
    """TODO 4, the headline. Both finish the SAME work (the same tokens). The
    one that needs fewer steps has higher throughput, by exactly this ratio."""
    # TODO 4 ------------------------------------------------------------------
    # Fewer steps for the same work means proportionally more throughput:
    #     return static_steps / continuous_steps
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if requests_that_fit(100, 2, 5) is None:
        return 1
    if static_batch_steps([3, 7, 2]) is None:
        return 2
    if admit_count(2, 8, 5) is None:
        return 3
    if throughput_multiple(100, 25) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# The two batching simulators. One "step" = one decode pass; every active
# request emits exactly one token and loses one from its remaining count.
# ---------------------------------------------------------------------------

def simulate_static(output_lengths, max_batch):
    """Static batching: take requests max_batch at a time, run each group until
    its LONGEST member is done, then start the next group. Returns (steps,
    useful_token_steps)."""
    steps = 0
    useful = 0
    for i in range(0, len(output_lengths), max_batch):
        batch = output_lengths[i:i + max_batch]
        steps += static_batch_steps(batch)   # the whole group waits for the slowest
        useful += sum(batch)                  # each request still does its own work
    return steps, useful


def simulate_continuous(output_lengths, max_batch):
    """Continuous batching: keep a shared queue, and at every step refill any
    free slot from it before decoding. A finished request's slot is reused on
    the very next step. Returns (steps, useful_token_steps)."""
    queue = deque(output_lengths)
    active = []            # remaining token counts of the requests in flight
    steps = 0
    useful = 0
    while queue or active:
        take = admit_count(len(active), max_batch, len(queue))   # fill freed slots now
        for _ in range(take):
            active.append(queue.popleft())
        steps += 1
        useful += len(active)                 # one token per active request this step
        active = [r - 1 for r in active]      # every active request emits a token
        active = [r for r in active if r > 0]  # finished ones free their slot
    return steps, useful


def utilisation_pct(useful_token_steps, steps, max_batch):
    """What fraction of the available slot-time (steps * slots) did real token
    work, as a percent. 100 means the GPU never had an idle slot."""
    return useful_token_steps / (steps * max_batch) * 100


def make_workload(n, rng):
    """A realistic mix: most requests are short, a few are long. The ORDER is
    shuffled by the RNG, which is what scatters the long ones across the static
    batches and causes the head-of-line blocking."""
    lengths = []
    for _ in range(n):
        if rng.random() < LONG_FRACTION:
            lengths.append(rng.randint(LONG_MIN, LONG_MAX))
        else:
            lengths.append(rng.randint(SHORT_MIN, SHORT_MAX))
    return lengths


# ---------------------------------------------------------------------------
# The three parts.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: the KV cache. GPU MEMORY caps the batch, not compute")
    print("=" * 78)
    print(f"  Model: {NUM_LAYERS} layers, {NUM_KV_HEADS} kv-heads, head_dim {HEAD_DIM}, fp16.")
    print(f"  Every token of every request keeps a key AND a value tensor cached")
    print(f"  so the model never recomputes the past. That costs, per token:")
    print(f"    2 (K,V) x {NUM_LAYERS} layers x {NUM_KV_HEADS} heads x {HEAD_DIM} dim x {DTYPE_BYTES} bytes"
          f" = {KV_BYTES_PER_TOKEN // 1024} KiB/token")
    print(f"  GPU has {GPU_TOTAL_GIB} GiB; weights and overhead take {WEIGHTS_OVERHEAD_GIB} GiB,")
    print(f"  leaving {KV_BUDGET_BYTES // GIB} GiB of KV-cache budget.")
    print()
    print(f"  {'seq length':>12}{'KV per request':>18}{'requests that fit':>20}")
    fit = {}
    for seq_len in (512, 1024, 2048, 4096, 8192, 16384, 32768):
        per_req = seq_len * KV_BYTES_PER_TOKEN
        n = requests_that_fit(KV_BUDGET_BYTES, seq_len, KV_BYTES_PER_TOKEN)
        fit[seq_len] = n
        if per_req >= GIB:
            per_str = f"{per_req / GIB:.2f} GiB"
        else:
            per_str = f"{per_req / MIB:.0f} MiB"
        print(f"  {seq_len:>12,}{per_str:>18}{n:>20,}")
    print()
    print("  The compute per token barely moves with sequence length, but the KV")
    print("  cache grows linearly with it, so the number of requests you can hold")
    print("  at once HALVES every time the conversation doubles in length. A chat")
    print("  that grows from 2k to 8k tokens drops your batch from "
          f"{fit[2048]} to {fit[8192]}.")
    print("  That is why 'memory-bound, not compute-bound' is the first fact of")
    print("  LLM serving, and why long contexts are expensive to serve, not just")
    print("  slow. The batch size is a memory decision.")
    return fit[2048], fit[8192]


def part2():
    print("\n" + "=" * 78)
    print("Part 2: static vs continuous batching. Same work, very different bill")
    print("=" * 78)
    rng = random.Random(SEED)
    varied = make_workload(NUM_REQUESTS, rng)
    total_tokens = sum(varied)
    longest = max(varied)
    n_long = sum(1 for x in varied if x >= LONG_MIN)
    print(f"  Workload: {NUM_REQUESTS} requests, all waiting at t=0 (a busy server).")
    print(f"    {NUM_REQUESTS - n_long} short ({SHORT_MIN}-{SHORT_MAX} tokens) and {n_long} long "
          f"({LONG_MIN}-{LONG_MAX} tokens).")
    print(f"    {total_tokens:,} output tokens in total, longest request {longest} tokens.")
    print(f"    {MAX_BATCH} slots fit in memory (the Part 1 ceiling).")
    print()

    # The control: when every request is the SAME length, batching style barely
    # matters. The win comes entirely from variance.
    uniform = [UNIFORM_LEN] * NUM_REQUESTS
    us, uu = simulate_static(uniform, MAX_BATCH)
    uc, ucu = simulate_continuous(uniform, MAX_BATCH)
    print(f"  Control, every request exactly {UNIFORM_LEN} tokens (no variance):")
    print(f"    static {us:,} steps, continuous {uc:,} steps  ->  "
          f"{throughput_multiple(us, uc):.2f}x. Basically a tie.")
    print("    With no variance there is no slow request to block the others, so")
    print("    refilling slots buys you almost nothing. Variance is the enemy.")
    print()

    # The real workload: varied lengths.
    ss, su = simulate_static(varied, MAX_BATCH)
    cs, cu = simulate_continuous(varied, MAX_BATCH)
    mult = throughput_multiple(ss, cs)
    static_util = utilisation_pct(su, ss, MAX_BATCH)
    cont_util = utilisation_pct(cu, cs, MAX_BATCH)

    static_s = ss * STEP_MS / 1000
    cont_s = cs * STEP_MS / 1000
    print(f"  Real workload, varied lengths (at {STEP_MS} ms per decode step):")
    print(f"    {'':12}{'steps':>10}{'wall time':>12}{'req/sec':>12}{'GPU busy':>12}")
    print(f"    {'static':12}{ss:>10,}{static_s:>10.1f} s"
          f"{NUM_REQUESTS / static_s:>12.1f}{static_util:>11.1f}%")
    print(f"    {'continuous':12}{cs:>10,}{cont_s:>10.1f} s"
          f"{NUM_REQUESTS / cont_s:>12.1f}{cont_util:>11.1f}%")
    print()
    print(f"  Continuous batching has {mult:.1f}x the throughput for the SAME requests")
    print(f"  on the SAME hardware. Static ran the GPU at only {static_util:.0f}% useful")
    print(f"  slot-time; continuous kept it at {cont_util:.0f}%.")
    print()
    print("  Why? In static batching a group of 16 cannot free ANY slot until its")
    print("  longest request is done. With a long request in almost every batch,")
    print("  15 short requests finish early and then sit idle for hundreds of")
    print("  steps, holding slots they are not using. Continuous batching hands a")
    print("  freed slot to the next waiting request on the very next step, so the")
    print("  short requests stream through instead of waiting. That is the whole")
    print("  vLLM throughput result, and it is head-of-line blocking from Day 4:")
    print("  one short request should never be stuck behind one long one.")
    print()
    print(f"  (Continuous is {cont_util:.0f}%, not 100%, only because we drain a FIXED")
    print("   batch: at the very end the queue empties and the last few long")
    print("   requests finish with slots to spare. On a real server that keeps")
    print("   receiving requests, that tail never happens and utilisation sits")
    print("   near 100%. The honest comparison is still 14% vs 72% here.)")
    return mult, static_util


def part3():
    print("\n" + "=" * 78)
    print("Part 3: you have seen this before. It is distributed systems, on a GPU")
    print("=" * 78)
    print("  Nothing today was new. It was three old lessons aimed at the GPU:")
    print()
    print("  Day 4, keep the expensive server busy. The GPU is the costliest box")
    print("    in the building. An idle slot is money on fire. Continuous batching")
    print("    exists to keep utilisation high, exactly the point of the")
    print("    utilisation chapter, just with a four-figure-an-hour server.")
    print()
    print("  Day 4 and Day 6, one shared queue beats separate lines. Static")
    print("    batching is 16 people forced to leave the bank together, so the")
    print("    whole counter waits on the one person opening a fixed deposit.")
    print("    Continuous batching is one shared queue feeding every teller: the")
    print("    moment a teller is free, the next person steps up. Same tellers,")
    print("    far more customers served per hour. The GPU's KV-cache slots are")
    print("    the tellers.")
    print()
    print("  Day 2 and Day 6, batching itself. Doing many requests in one pass")
    print("    beats one at a time, the same reason one batched commit beats a")
    print("    thousand fsyncs. The GPU only earns its keep when the batch is full.")
    print()
    print("  So the AI serving stack is your week 1-to-5 brain with a GPU in the")
    print("  middle. The KV cache is a memory-budget problem. Continuous batching")
    print("  is a queueing problem. Your token bill is a utilisation problem. The")
    print("  model is the magic; the engineering is everything around it.")


def verdict(name, predicted, actual, unit="%"):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>7.1f} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    note = "     close enough" if diff <= max(3.0, 0.15 * abs(predicted)) \
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

    fit_2048, fit_8192 = part1()
    mult, static_util = part2()
    part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 requests that fit at 2048", PREDICTIONS["fit_at_2048"], fit_2048, "reqs")
    verdict("P2 requests that fit at 8192", PREDICTIONS["fit_at_8192"], fit_8192, "reqs")
    verdict("P3 continuous throughput mult", PREDICTIONS["throughput_multiple"], mult, "x")
    verdict("P4 static GPU utilisation", PREDICTIONS["static_utilisation_pct"], static_util, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  At 2048 tokens, {fit_2048} requests fit in the KV-cache budget; at 8192 only")
    print(f"  {fit_8192}. Memory, not compute, sets the batch, and long contexts shrink it.")
    print(f"  Then continuous batching served the same 200 requests {mult:.1f}x faster than")
    print(f"  static, because static left the GPU {static_util:.0f}% busy while short requests")
    print("  sat trapped behind long ones. The KV cache is a memory-budget")
    print("  problem and batching is a queueing problem. You solved both in")
    print("  weeks 1 to 6; the GPU just raised the stakes.")
    print()


if __name__ == "__main__":
    main()
