"""
Day 38 lab: vector search and the recall-versus-speed dial. A toy vector index
in pure Python. 5,000 vectors, exact brute-force search, then an IVF
approximate index, then the single knob that turns one into the other.

This is the full working solution. The starter file is vector_search.py.
Run it:      python3 solution.py

Standard library only. No numpy, no model, no API, no network, no files.
Everything is a deterministic, seeded simulation, so the run reproduces to the
digit. The "embeddings" here are made-up vectors with real cluster structure,
so near neighbours actually mean something and recall is a real measurement.

A note on the metric. Every vector is L2-normalised to unit length when it is
made, so cosine similarity between two of them is just their dot product. That
is why the one-line similarity is a dot product: on the unit sphere, cosine and
dot are the same number, and "most similar" means "largest dot".

The big ideas:
  - Brute force is exact. For a query you score it against ALL N vectors and
    keep the top k. Recall is 100 percent by definition, but the cost is linear
    in N: every query touches every vector. That is the wall a vector database
    is built to get around.
  - IVF (inverted file) clusters the vectors into C cells once, up front. A
    search finds the query's nearest cell and scores ONLY the vectors in it.
    You compare a small slice of the vectors instead of all of them, so it is
    many times faster, at the cost of some recall: a true neighbour that happens
    to sit in a different cell is missed.
  - nprobe is the dial. Probe 1 cell and you are fast but miss neighbours near a
    cell boundary. Probe more cells and recall climbs toward 100 percent while
    latency climbs back toward brute force. nprobe = C is just brute force wearing
    a hat. "It is approximate" is the whole feature: you get to choose where on
    that curve you sit.
"""

import math
import random
import sys
import time

PREDICTIONS = {
    # P1: brute-force search scores the query against every vector and keeps the
    #     real top k. What is its recall@k, as a percent? (Think about what
    #     "exact" means.)
    "brute_recall_pct": 100,

    # P2: the IVF index probing just ONE cell. What fraction of each query's true
    #     top-k does it find, as a percent? (It is fast, but it will miss some.)
    "ivf_nprobe1_recall_pct": 88,

    # P3: that same one-cell IVF search, how many TIMES faster than brute force?
    #     (Brute scores all 5,000; IVF scores one cell's worth plus the centroids.)
    "ivf_nprobe1_speedup_x": 25,

    # P4: turn the dial up. Probing 8 cells instead of 1, what is recall@k now,
    #     as a percent? (This is the recall you buy back by paying latency.)
    "ivf_nprobe8_recall_pct": 100,
}

N = 5000             # number of vectors in the index
DIM = 32             # dimension of each vector (a real embedding is 384-3072)
K = 10               # top-k we retrieve and score recall against
QUERIES = 200        # query vectors, averaged over for stable recall numbers
BLOBS = 25           # ground-truth clusters the data is drawn from
NOISE = 0.11         # per-dimension spread around a cluster centre
C = 40               # IVF cells (how many clusters the index splits into)
KMEANS_ITERS = 6     # k-means refinement passes when building the index
DEFAULT_NPROBE = 1   # cells probed by the headline fast search
HIGH_NPROBE = 8      # cells probed when we turn the recall dial up
SWEEP = [1, 2, 3, 5, 8, 12, 16, 25, 40]
SEED = 38


# ---------------------------------------------------------------------------
# The four TODOs. Each is one load-bearing line: the metric, the scoring of a
# result, the IVF build, and the IVF search dial.
# ---------------------------------------------------------------------------

def similarity(a, b):
    """TODO 1, the metric everything rests on. Cosine similarity of two vectors.
    Every vector here is unit length, so cosine is just the dot product: sum of
    a[i] * b[i] over all dimensions. Bigger means more alike."""
    return sum(x * y for x, y in zip(a, b))


def recall_at_k(found_ids, true_ids):
    """TODO 2, how we score an approximate result. Of the true top-k neighbours,
    what fraction did this search actually return? The size of the overlap
    divided by how many true neighbours there were."""
    return len(set(found_ids) & set(true_ids)) / len(true_ids)


def nearest_centroid(vec, centroids):
    """TODO 3, the IVF build (and the first step of its search). Which cell does
    this vector belong to? The index of the centroid it is most similar to."""
    return max(range(len(centroids)), key=lambda j: similarity(vec, centroids[j]))


def cells_to_probe(query, centroids, nprobe):
    """TODO 4, the dial itself. Rank the cells by how similar their centroid is
    to the query, most similar first, and return the first nprobe of them. These
    are the only cells the search will look inside."""
    order = sorted(range(len(centroids)),
                   key=lambda j: similarity(query, centroids[j]), reverse=True)
    return order[:nprobe]


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if similarity([1.0, 0.0], [1.0, 0.0]) is None:
        return 1
    if recall_at_k([1, 2], [2, 3]) is None:
        return 2
    if nearest_centroid([1.0, 0.0], [[1.0, 0.0], [0.0, 1.0]]) is None:
        return 3
    if cells_to_probe([1.0, 0.0], [[1.0, 0.0], [0.0, 1.0]], 1) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# Making the data. Unit vectors drawn from BLOBS clusters, so near neighbours
# are real and recall is a real thing to measure.
# ---------------------------------------------------------------------------

def unit(values):
    """Scale a vector to length 1, so cosine similarity is a plain dot product."""
    norm = math.sqrt(sum(x * x for x in values))
    if norm == 0.0:
        return values
    return [x / norm for x in values]


def near(rng, centre):
    """A fresh unit vector sitting near a cluster centre."""
    return unit([centre[d] + rng.gauss(0.0, NOISE) for d in range(DIM)])


def build_data(rng):
    """BLOBS random cluster centres, then N vectors scattered around them."""
    centres = [unit([rng.gauss(0.0, 1.0) for _ in range(DIM)]) for _ in range(BLOBS)]
    data = [near(rng, centres[rng.randrange(BLOBS)]) for _ in range(N)]
    queries = [near(rng, centres[rng.randrange(BLOBS)]) for _ in range(QUERIES)]
    return data, queries


# ---------------------------------------------------------------------------
# Brute-force exact search: score every vector, keep the top k.
# ---------------------------------------------------------------------------

def brute_topk(query, data, k):
    scored = [(similarity(query, data[i]), i) for i in range(len(data))]
    scored.sort(reverse=True)
    return [i for _, i in scored[:k]]


# ---------------------------------------------------------------------------
# The IVF index: cluster the data into C cells with a small k-means, then a
# search probes only the nprobe nearest cells.
# ---------------------------------------------------------------------------

def build_ivf(data, rng, c, iters):
    """k-means into c cells. Returns the centroids and, for each cell, the list
    of vector ids that live in it. Deterministic: seeded init, fixed passes."""
    centroids = [data[i][:] for i in rng.sample(range(len(data)), c)]
    members = [[] for _ in range(c)]
    for _ in range(iters):
        members = [[] for _ in range(c)]
        for idx in range(len(data)):
            members[nearest_centroid(data[idx], centroids)].append(idx)
        for j in range(c):
            if members[j]:
                acc = [0.0] * DIM
                for idx in members[j]:
                    v = data[idx]
                    for d in range(DIM):
                        acc[d] += v[d]
                centroids[j] = unit(acc)
    members = [[] for _ in range(c)]
    for idx in range(len(data)):
        members[nearest_centroid(data[idx], centroids)].append(idx)
    return centroids, members


def ivf_topk(query, centroids, members, data, k, nprobe):
    """Score only the vectors in the nprobe nearest cells, keep the top k.
    Also returns how many vectors were actually scored (the candidate count)."""
    candidates = []
    for j in cells_to_probe(query, centroids, nprobe):
        candidates.extend(members[j])
    scored = [(similarity(query, data[i]), i) for i in candidates]
    scored.sort(reverse=True)
    return [i for _, i in scored[:k]], len(candidates)


# ---------------------------------------------------------------------------
# The three parts.
# ---------------------------------------------------------------------------

def part1(data, queries):
    print("=" * 78)
    print("Part 1: brute force. Exact, 100 percent recall, and linear in N")
    print("=" * 78)
    print(f"  {N:,} vectors, dimension {DIM}, retrieving top {K} for {QUERIES} queries.")
    t = time.perf_counter()
    truth = [brute_topk(q, data, K) for q in queries]
    elapsed = time.perf_counter() - t
    ms = elapsed / QUERIES * 1000
    print(f"  every query is scored against all {N:,} vectors.")
    print(f"    latency: {ms:.2f} ms/query   ({elapsed * 1000:.0f} ms for all {QUERIES})")
    print(f"    vectors scored per query: {N:,}")
    print(f"    recall@{K}: 100.0%   (it looked at everything, so it cannot miss)")
    print()
    print("  This is the ground truth every other search is measured against.")
    print("  It is also the wall: double the vectors and you double the work,")
    print("  every single query. That linear cost is why we reach for an index.")
    return truth, ms


def part2(data, queries, truth, brute_ms):
    print("\n" + "=" * 78)
    print("Part 2: IVF. Cluster once, then search only the query's own cell")
    print("=" * 78)
    rng = random.Random(SEED + 1)
    t = time.perf_counter()
    centroids, members = build_ivf(data, rng, C, KMEANS_ITERS)
    build_s = time.perf_counter() - t
    sizes = [len(m) for m in members]
    print(f"  built {C} cells with k-means in {build_s * 1000:.0f} ms (one-time, up front).")
    print(f"    cell sizes: {min(sizes)} to {max(sizes)} vectors "
          f"(ideal would be {N // C}).")
    print()

    t = time.perf_counter()
    total_recall = 0.0
    total_cand = 0
    for qi, q in enumerate(queries):
        found, ncand = ivf_topk(q, centroids, members, data, K, DEFAULT_NPROBE)
        total_recall += recall_at_k(found, truth[qi])
        total_cand += ncand
    elapsed = time.perf_counter() - t
    ms = elapsed / QUERIES * 1000
    recall = total_recall / QUERIES * 100
    avg_cand = total_cand / QUERIES
    speedup = brute_ms / ms

    print(f"  search probing nprobe={DEFAULT_NPROBE} cell:")
    print(f"    latency: {ms:.3f} ms/query   ({speedup:.1f}x faster than brute force)")
    print(f"    vectors scored per query: ~{avg_cand:.0f} "
          f"(vs {N:,} for brute, plus {C} centroids)")
    print(f"    recall@{K}: {recall:.1f}%")
    print()
    print(f"  Much faster, because it scores about {avg_cand:.0f} vectors instead of all")
    print(f"  {N:,}. The cost is the {100 - recall:.0f} percent it missed: a true neighbour that")
    print("  landed in a neighbouring cell is simply never seen. That miss is not")
    print("  a bug. It is the trade you chose by probing one cell.")
    return centroids, members, recall, speedup


def part3(data, queries, truth, centroids, members, brute_ms):
    print("\n" + "=" * 78)
    print("Part 3: the dial. Probe more cells, buy back recall, pay in latency")
    print("=" * 78)
    print(f"  Same index, same queries. The only knob we turn is nprobe, the")
    print(f"  number of cells the search looks inside (out of {C}).")
    print()
    print(f"  {'nprobe':>7}{'scored/query':>14}{'recall@' + str(K):>12}"
          f"{'ms/query':>11}{'vs brute':>11}")
    high_recall = None
    for nprobe in SWEEP:
        t = time.perf_counter()
        total_recall = 0.0
        total_cand = 0
        for qi, q in enumerate(queries):
            found, ncand = ivf_topk(q, centroids, members, data, K, nprobe)
            total_recall += recall_at_k(found, truth[qi])
            total_cand += ncand
        elapsed = time.perf_counter() - t
        ms = elapsed / QUERIES * 1000
        recall = total_recall / QUERIES * 100
        avg_cand = total_cand / QUERIES
        speedup = brute_ms / ms
        tag = "  <- brute force, basically" if nprobe == C else ""
        print(f"  {nprobe:>7}{avg_cand:>13.0f}{recall:>11.1f}%"
              f"{ms:>10.3f}{speedup:>9.1f}x{tag}")
        if nprobe == HIGH_NPROBE:
            high_recall = recall
    print()
    print("  Recall climbs toward 100 percent as you probe more cells, and the")
    print("  latency climbs right back toward brute force. Here the recall maxes")
    print("  out after only a few cells, because the data clusters cleanly. What")
    print("  keeps rising is the latency: probe more than you need and you pay")
    print("  brute-force prices for recall you already had. At nprobe = C you ARE")
    print("  brute force again, just with the centroid scan bolted on top. A vector")
    print("  database hands you this dial and lets you pick where to sit on it.")
    return high_recall


def verdict(name, predicted, actual, unit_label=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>7.1f} {unit_label}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.75 <= ratio <= 1.33:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<34} you = {predicted:>6.1f}   actual = {actual:>7.1f} {unit_label}  {note}")


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
    data, queries = build_data(rng)

    truth, brute_ms = part1(data, queries)
    centroids, members, ivf_recall, ivf_speedup = part2(data, queries, truth, brute_ms)
    high_recall = part3(data, queries, truth, centroids, members, brute_ms)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 brute-force recall", PREDICTIONS["brute_recall_pct"], 100.0, "%")
    verdict("P2 IVF nprobe=1 recall", PREDICTIONS["ivf_nprobe1_recall_pct"], ivf_recall, "%")
    verdict("P3 IVF nprobe=1 speedup", PREDICTIONS["ivf_nprobe1_speedup_x"], ivf_speedup, "x")
    verdict(f"P4 IVF nprobe={HIGH_NPROBE} recall", PREDICTIONS["ivf_nprobe8_recall_pct"], high_recall, "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Brute force was exact, {100:.0f}% recall, by scoring all {N:,} vectors on")
    print(f"  every query. The IVF index probing one cell hit {ivf_recall:.0f}% recall at")
    print(f"  {ivf_speedup:.0f}x the speed, because it scored a small slice of the vectors")
    print(f"  instead of all of them. Turn the dial to nprobe={HIGH_NPROBE} and recall came back")
    print(f"  to {high_recall:.0f}%. That knob, recall versus latency, is the whole game of a")
    print("  vector database. 'Approximate' is not a compromise you tolerate, it")
    print("  is the setting you get to choose.")
    print()


if __name__ == "__main__":
    main()
