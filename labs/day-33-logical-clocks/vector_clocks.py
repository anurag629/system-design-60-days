"""
Day 33 lab: logical clocks. Ordering events across machines without ever
trusting a wall clock.

Run it:      python3 vector_clocks.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only, no network, no threads, no files. The whole thing is a
deterministic simulation of three processes passing messages, so it prints the
same numbers on every machine and finishes in well under a second.

The story in three parts:

  Part 1, Lamport timestamps. Each process keeps one integer counter. It bumps
    the counter on every event, and on receiving a message it jumps the counter
    to max(mine, yours) + 1. This gives a beautiful property: if event a really
    happened before event b, then Lamport(a) < Lamport(b). But the converse is
    FALSE. Lamport(a) < Lamport(b) does not mean a happened before b. They might
    be concurrent, and Lamport cannot tell. So Lamport gives you a consistent
    total order, but it quietly invents an order between events that never
    actually influenced each other.

  Part 2, vector clocks. Each process keeps a whole vector of counters, one slot
    per process. Now, for ANY two events, you can tell the truth: one happened
    before the other, or they are genuinely concurrent (neither vector dominates
    the other). We classify every pair of events and count the concurrent ones.
    That count is the number Lamport could never recover.

  Part 3, why it matters. Two concurrent writes to the same key are exactly the
    "sibling" conflict from Dynamo (Day 31). Vector clocks SEE the conflict, so
    the system knows it has two versions to reconcile and keeps both. A wall
    clock (Day 29) just compares two timestamps, silently keeps the larger one,
    and throws the other write away. That is lost data, and nobody gets paged.

If you get stuck, the full working version is solution.py in this folder.
"""

import sys

# -----------------------------------------------------------------------------
# PREDICTIONS. Fill these in BEFORE running. They are your own guesses, written
# down first so the real numbers can surprise you. If every one is None, the lab
# refuses to run.
# -----------------------------------------------------------------------------
PREDICTIONS = {
    # P1: our run has 10 events across 3 processes, so 45 unordered pairs in
    #     total. How many of those pairs are causally ORDERED (one truly
    #     happened before the other, either direction)?
    "ordered_pairs": None,

    # P2: the headline. How many pairs are genuinely CONCURRENT (neither
    #     happened before the other)? This is the number vector clocks recover
    #     and Lamport cannot.
    "concurrent_pairs": None,

    # P3: of those concurrent pairs, how many does Lamport STRICTLY mis-order,
    #     i.e. Lamport(a) < Lamport(b) even though a and b never influenced each
    #     other? (The rest come out as Lamport ties.)
    "lamport_misordered": None,

    # P4: in the Part 3 shopping-cart run, how many concurrent write conflicts
    #     ("siblings") do vector clocks flag, each one a write that last-write-
    #     wins would silently drop?
    "sibling_conflicts": None,
}

# Process ids. Three of them. Think of three servers, or three phones.
P0, P1, P2 = 0, 1, 2
NUM_PROCS = 3

# -----------------------------------------------------------------------------
# The scenario. A fixed schedule of 10 events across the three processes, with
# three messages passed between them. The list is already in a valid processing
# order: every message is SENT earlier in the list than it is RECEIVED, so when
# we walk the list top to bottom, a receiver always has the sender's clock ready.
#
# Each row is (event_id, process, kind, msg_id):
#   kind "internal" -> a local step, talks to nobody
#   kind "send"     -> a local step that also fires message msg_id
#   kind "recv"     -> receives message msg_id (matched to its send by id)
#
# The message wiring:
#   m1:  P0 a2  -->  P1 b1
#   m2:  P1 b2  -->  P2 c2
#   m3:  P2 c3  -->  P0 a4
# -----------------------------------------------------------------------------
SCHEDULE = [
    ("a1", P0, "internal", None),
    ("a2", P0, "send",     "m1"),
    ("a3", P0, "internal", None),
    ("c1", P2, "internal", None),
    ("b1", P1, "recv",     "m1"),
    ("b2", P1, "send",     "m2"),
    ("b3", P1, "internal", None),
    ("c2", P2, "recv",     "m2"),
    ("c3", P2, "send",     "m3"),
    ("a4", P0, "recv",     "m3"),
]


# =============================================================================
# Ground truth: the real happened-before relation, built straight from the
# causal structure, with no clocks involved at all. This is the answer key we
# will grade both kinds of clock against.
# =============================================================================
def build_causal_edges():
    """Direct causal edges between events.

    Two sources of 'a directly happened before b':
      1. program order: on one process, each event precedes the next.
      2. messages: a send happens before its matching receive.
    """
    edges = {eid: set() for eid, _, _, _ in SCHEDULE}

    # Program order, per process, in the order the events occur.
    last_on_proc = {}
    for eid, proc, _, _ in SCHEDULE:
        if proc in last_on_proc:
            edges[last_on_proc[proc]].add(eid)
        last_on_proc[proc] = eid

    # Message edges: send -> matching recv.
    send_of = {}
    for eid, _, kind, msg in SCHEDULE:
        if kind == "send":
            send_of[msg] = eid
    for eid, _, kind, msg in SCHEDULE:
        if kind == "recv":
            edges[send_of[msg]].add(eid)

    return edges


def happened_before_sets(edges):
    """Transitive closure: for each event, every event it causally reaches."""
    reach = {}

    def dfs(start):
        seen = set()
        stack = list(edges[start])
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(edges[node])
        return seen

    for eid in edges:
        reach[eid] = dfs(eid)
    return reach


def classify_truth(reach):
    """For every unordered pair, is it ordered (one reaches the other) or
    concurrent (neither does)? Returns (ordered_pairs, concurrent_pairs) as
    lists of (x, y) tuples.
    """
    ids = [eid for eid, _, _, _ in SCHEDULE]
    ordered, concurrent = [], []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            x, y = ids[i], ids[j]
            if y in reach[x] or x in reach[y]:
                ordered.append((x, y))
            else:
                concurrent.append((x, y))
    return ordered, concurrent


# =============================================================================
# Part 1: Lamport timestamps. One integer per process.
# =============================================================================
def lamport_recv(local, received):
    """The Lamport receive rule."""
    # TODO 1 ------------------------------------------------------------------
    # When a process receives a message, it must not fall behind the sender.
    # It jumps its counter past BOTH its own value and the stamp the message
    # carried, then takes one more step for the receive event itself:
    #     return max(local, received) + 1
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def build_lamport():
    """Walk the schedule once, assigning each event a Lamport timestamp.

    A process keeps a single counter. Internal and send events bump it by one.
    A receive bumps it to max(local, sender's stamp) + 1.
    """
    counter = {P0: 0, P1: 0, P2: 0}
    msg_stamp = {}      # message id -> Lamport stamp it was sent with
    stamp = {}          # event id -> its Lamport stamp

    for eid, proc, kind, msg in SCHEDULE:
        if kind == "recv":
            counter[proc] = lamport_recv(counter[proc], msg_stamp[msg])
        else:
            counter[proc] += 1
        stamp[eid] = counter[proc]
        if kind == "send":
            msg_stamp[msg] = counter[proc]

    return stamp


def part1(reach, ordered, concurrent):
    print("=" * 78)
    print("Part 1: Lamport timestamps. One counter per process.")
    print("=" * 78)

    if lamport_recv(0, 5) is None:
        print("  (fill in TODO 1)")
        return None

    stamp = build_lamport()

    print("  Event Lamport stamps (one integer each):")
    line = "    "
    for eid, _, _, _ in SCHEDULE:
        line += f"{eid}={stamp[eid]}  "
    print(line)
    print()

    # The property that DOES hold: a happened-before b  =>  L(a) < L(b).
    holds = True
    for x, y in ordered:
        a, b = (x, y) if y in reach[x] else (y, x)   # a is the earlier one
        if not stamp[a] < stamp[b]:
            holds = False
    print("  The good news. For every pair where a really happened before b,")
    print(f"  we check that Lamport(a) < Lamport(b). Holds on all {len(ordered)} "
          f"ordered pairs: {holds}.")
    print("  So Lamport stamps never contradict real causality. A reply always")
    print("  outranks the message it answers. That alone is enough to build a")
    print("  single consistent total order out of a distributed mess.")
    print()

    # The property that does NOT hold: L(a) < L(b) does not imply a -> b.
    misordered = []
    ties = []
    for x, y in concurrent:
        if stamp[x] == stamp[y]:
            ties.append((x, y))
        else:
            misordered.append((x, y))
    print("  The catch. Lamport(a) < Lamport(b) does NOT mean a happened before b.")
    print(f"  Of the concurrent pairs, Lamport puts a strict order on {len(misordered)} of")
    print("  them anyway, inventing a 'first' between events that never spoke:")
    for x, y in misordered:
        a, b = (x, y) if stamp[x] < stamp[y] else (y, x)
        print(f"    {a}(L={stamp[a]}) < {b}(L={stamp[b]})   but {a} and {b} are concurrent")
    if ties:
        pretty = ", ".join(f"{x}~{y}" for x, y in ties)
        print(f"  Another {len(ties)} come out as ties Lamport cannot separate: {pretty}.")
    print("  A total order is handy, but Lamport has quietly lied about who")
    print("  influenced whom. It cannot see concurrency. That is the gap.")
    return len(misordered)


# =============================================================================
# Part 2: vector clocks. A whole vector per process.
# =============================================================================
def vc_tick(vc, pid):
    """Local step for an internal or send event."""
    out = list(vc)
    # TODO 2 ------------------------------------------------------------------
    # A local event only advances THIS process's own slot of the vector. Every
    # other slot stays exactly as it was. Bump slot `pid` by one:
    #     out[pid] += 1
    # -------------------------------------------------------------------------
    return out  # <-- after you bump out[pid], this returns the ticked vector


def vc_merge(local_vc, msg_vc, pid):
    """The vector-clock receive rule."""
    # TODO 3 ------------------------------------------------------------------
    # A receive learns everything the sender knew. For each slot, take the
    # bigger of what I already knew and what the message carried (elementwise
    # max). Then, because the receive is itself a new local event, bump my own
    # slot by one:
    #     merged = [max(a, b) for a, b in zip(local_vc, msg_vc)]
    #     merged[pid] += 1
    #     return merged
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def vc_compare(a, b):
    """Relate two vector clocks.

    'before'     -> a happened before b (a <= b in every slot, and smaller in one)
    'after'      -> b happened before a
    'equal'      -> same event / same vector
    'concurrent' -> neither dominates, so they are causally independent
    """
    # TODO 4 ------------------------------------------------------------------
    # One vector dominates another only if it is >= in EVERY slot. So compute
    # two facts: is a <= b everywhere (le), and is a >= b everywhere (ge)?
    #   - both true  -> the vectors are equal
    #   - only le    -> a is before b
    #   - only ge    -> a is after b
    #   - neither    -> concurrent (the case Lamport can never see)
    #     le = all(x <= y for x, y in zip(a, b))
    #     ge = all(x >= y for x, y in zip(a, b))
    #     if le and ge: return "equal"
    #     if le: return "before"
    #     if ge: return "after"
    #     return "concurrent"
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def build_vectors():
    """Walk the schedule once, assigning each event a vector clock."""
    clock = {P0: [0, 0, 0], P1: [0, 0, 0], P2: [0, 0, 0]}
    msg_vc = {}      # message id -> the vector it was sent with
    vc = {}          # event id -> its vector clock

    for eid, proc, kind, msg in SCHEDULE:
        if kind == "recv":
            clock[proc] = vc_merge(clock[proc], msg_vc[msg], proc)
        else:
            clock[proc] = vc_tick(clock[proc], proc)
        vc[eid] = list(clock[proc])
        if kind == "send":
            msg_vc[msg] = list(clock[proc])

    return vc


def part2(reach, ordered, concurrent):
    print("\n" + "=" * 78)
    print("Part 2: vector clocks. One counter per process, carried by everyone.")
    print("=" * 78)

    # vc_tick with a blank TODO 2 returns the vector unchanged, so we probe it
    # with a known step and check the slot actually moved.
    if vc_tick([0, 0, 0], 0) == [0, 0, 0]:
        print("  (fill in TODO 2)")
        return None
    if vc_merge([0, 0, 0], [0, 0, 0], 0) is None:
        print("  (fill in TODO 3)")
        return None

    vc = build_vectors()

    print("  Event vector clocks [P0, P1, P2]:")
    for eid, _, _, _ in SCHEDULE:
        print(f"    {eid} = {vc[eid]}")
    print()

    if vc_compare([1, 0, 0], [0, 1, 0]) is None:
        print("  (fill in TODO 4)")
        return None

    # Classify every pair using ONLY the vectors, then check it against truth.
    ids = [eid for eid, _, _, _ in SCHEDULE]
    vc_concurrent = []
    agree = True
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            x, y = ids[i], ids[j]
            rel = vc_compare(vc[x], vc[y])
            is_conc_by_vc = (rel == "concurrent")
            is_conc_truth = (y not in reach[x] and x not in reach[y])
            if is_conc_by_vc != is_conc_truth:
                agree = False
            if is_conc_by_vc:
                vc_concurrent.append((x, y))

    print(f"  Vector clocks classify all {len(ordered) + len(concurrent)} pairs. They match the")
    print(f"  ground-truth causal relation on every single pair: {agree}.")
    print()
    print(f"  Ordered pairs (one happened before the other): {len(ordered)}")
    print(f"  Concurrent pairs (neither did):                 {len(vc_concurrent)}")
    print("  These are the concurrent pairs, each one invisible to Lamport:")
    pretty = ", ".join(f"{x}|{y}" for x, y in vc_concurrent)
    print(f"    {pretty}")
    print()
    print("  Read one off to feel it. a3 = [3,0,0] and b2 = [2,2,0]. a3 is ahead")
    print("  on P0 (3 > 2), b2 is ahead on P1 (2 > 0). Neither vector dominates,")
    print("  so neither event could have known about the other. Concurrent, and")
    print("  the vectors prove it. Lamport had them as 3 < 4 and called it order.")
    return len(vc_concurrent)


# =============================================================================
# Part 3: why it matters. Concurrent writes are Dynamo siblings.
# =============================================================================
# A shopping cart, key "cart:42", written by three clients. Each write records
# the vector clock it was based on, a wall-clock timestamp, and the WHOLE cart
# value it is writing (a client that has seen earlier writes carries their items
# forward, exactly like a real Dynamo client reconciling before it writes). The
# wall clocks are SKEWED (Day 29): client B's clock runs fast, so last-write-
# wins will trust B over everyone, even over writes that really came later.
#
# Each row: (who, vector_clock_at_write, wall_clock_ts, cart_value)
CART_WRITES = [
    ("A",  [1, 0, 0], 100, {"milk"}),                   # A reads empty, adds milk
    ("B",  [0, 1, 0], 500, {"eggs"}),                   # B reads empty, adds eggs  (clock runs fast)
    ("C",  [1, 1, 1], 120, {"milk", "eggs", "bread"}),  # C saw A and B, then adds bread
    ("A2", [2, 0, 0], 130, {"milk", "butter"}),         # A, still on its stale view, adds butter
]


def part3():
    print("\n" + "=" * 78)
    print("Part 3: why it matters. Concurrent writes are Dynamo siblings.")
    print("=" * 78)

    if vc_compare([1, 0, 0], [0, 1, 0]) is None:
        print("  (fill in TODO 4)")
        return None

    print("  Key cart:42, written by three clients with SKEWED wall clocks.")
    print("  Vector clocks decide, for each new write, whether it supersedes what")
    print("  is stored or conflicts with it (a concurrent sibling kept alongside).")
    print()

    # Replay the writes. Keep the set of "live" versions. A stored version stays
    # live until some later write dominates (supersedes) it. A write that is
    # concurrent with a live version is a sibling, and both survive.
    live = []          # list of (who, vc, ts, value)
    conflicts = 0
    for who, vc, ts, value in CART_WRITES:
        relations = [vc_compare(vc, other[1]) for other in live]
        survivors = [v for v, rel in zip(live, relations) if rel != "after"]
        siblings = [v for v, rel in zip(live, relations) if rel == "concurrent"]
        shown = ",".join(sorted(value))
        if siblings:
            conflicts += 1
            names = ", ".join(s[0] for s in siblings)
            print(f"  write {who:<2} {{{shown}}} is CONCURRENT with [{names}] -> keep both as siblings")
        else:
            print(f"  write {who:<2} {{{shown}}} supersedes the stored version(s)")
        survivors.append((who, vc, ts, value))
        live = survivors

    vc_items = sorted(set().union(*(v[3] for v in live)))
    print()
    print(f"  Vector clocks flagged {conflicts} concurrent conflict(s). The cart keeps every")
    print(f"  live sibling, so a read reconciles to their union: {vc_items}")
    print(f"  Items preserved: {len(vc_items)}. Nothing lost.")
    print()

    # Now the wall-clock way: the single write with the largest timestamp wins
    # outright, and its value is the whole cart. Everyone else is overwritten.
    winner = max(CART_WRITES, key=lambda w: w[2])
    lww_items = sorted(winner[3])
    all_items = sorted(set().union(*(w[3] for w in CART_WRITES)))
    lost = sorted(set(all_items) - set(lww_items))
    print("  Last-write-wins (trust the wall clock) instead:")
    print(f"    highest timestamp is client {winner[0]} at t={winner[2]}, so the cart becomes")
    print(f"    just {lww_items}. Silently lost: {lost}.")
    print(f"  Same writes, same order. Vector clocks keep {len(vc_items)} items, the wall")
    print(f"  clock keeps {len(lww_items)} and drops {len(lost)} with nobody the wiser.")
    return conflicts


# =============================================================================
# Scoreboard
# =============================================================================
def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>6,.0f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<34} you = {predicted:>4,.0f}   actual = {actual:>6,.0f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    edges = build_causal_edges()
    reach = happened_before_sets(edges)
    ordered, concurrent = classify_truth(reach)

    lamport_misordered = part1(reach, ordered, concurrent)
    if lamport_misordered is None:
        sys.exit(1)

    concurrent_pairs = part2(reach, ordered, concurrent)
    if concurrent_pairs is None:
        sys.exit(1)

    sibling_conflicts = part3()
    if sibling_conflicts is None:
        sys.exit(1)

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 ordered pairs", PREDICTIONS["ordered_pairs"], len(ordered))
    verdict("P2 concurrent pairs (the number)", PREDICTIONS["concurrent_pairs"], concurrent_pairs)
    verdict("P3 Lamport mis-orderings", PREDICTIONS["lamport_misordered"], lamport_misordered)
    verdict("P4 Dynamo sibling conflicts", PREDICTIONS["sibling_conflicts"], sibling_conflicts)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Of 45 event pairs, {concurrent_pairs} are genuinely concurrent: neither event")
    print("  influenced the other. Vector clocks flag every one of them, because")
    print("  neither vector dominates. Lamport timestamps cannot, they hand back a")
    print(f"  tidy total order and mis-order {lamport_misordered} of those pairs as if one came first.")
    print("  That gap is not academic. A concurrent pair writing the same key is a")
    print("  Dynamo sibling. Vector clocks see the conflict and keep both versions.")
    print("  A wall clock picks the bigger timestamp and loses your data in silence.")
    print()


if __name__ == "__main__":
    main()
