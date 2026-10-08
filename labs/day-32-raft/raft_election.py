"""
Day 32 lab: consensus and Raft, the understandable heart of it. How a cluster
elects a leader, why a leader needs a MAJORITY, and why the election timeouts
are random.

Run it:      python3 raft_election.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only. This is a DISCRETE-EVENT SIMULATION: there is no real
network and no real time. We advance a simulated clock one tick at a time
(think of a tick as one millisecond) and deliver messages after a small,
seeded network delay. Everything is reproducible: the same SEED gives the same
run on every machine, every time. It finishes in a few seconds and leaves no
files behind.

We do NOT build full log replication. Leader election plus the majority rule is
the whole lesson today, and it is plenty. Log replication (the other half of
Raft) rides on exactly the same majority, so once this clicks, that does too.

The three parts, all measured on your own machine:

  - Part 1, a leader dies and the cluster heals. Five nodes, one leader sending
    heartbeats. We kill the leader. A follower that stops hearing heartbeats
    times out, becomes a candidate, bumps the term, and asks the others for
    votes. With votes from a MAJORITY it becomes the new leader. We measure how
    long the gap lasted and confirm the new leader really held a majority.

  - Part 2, split votes, and why the timeouts are random. If several followers
    time out at once they all become candidates, each votes for itself, and the
    votes split so nobody gets a majority. The term is wasted and everyone
    retries. We measure the split-vote rate for FIXED (equal) timeouts versus
    RANDOMIZED ones. Fixed timeouts keep colliding and elections stall.
    Randomized timeouts let one candidate almost always wake first and win, so
    elections converge in about one round.

  - Part 3, the majority rule is fault tolerance. A leader needs a majority of
    the WHOLE cluster, not of whoever happens to be alive. So a 5-node cluster
    tolerates floor((5-1)/2) = 2 failures: with 2 nodes down the surviving 3 are
    still a majority and elect a leader, but with 3 down the surviving 2 can
    never reach 3 votes, so there is no leader and the cluster is unavailable.

If you get stuck, the full working version is solution.py in this folder.
"""

import random
import sys
from collections import defaultdict

PREDICTIONS = {
    # P1: a 5-node cluster, leader sending heartbeats, then the leader dies.
    #     Roughly how many ticks (ms) pass before a new leader is elected?
    #     (Hint: it is bounded by the election timeout window below.)
    "elect_gap_ticks": None,

    # P2: run many cold-start elections with FIXED (equal) timeouts. What
    #     percent of election rounds end in a split vote (a wasted term with no
    #     leader)?
    "fixed_split_pct": None,

    # P3: now the same with RANDOMIZED timeouts. What percent of election rounds
    #     split this time?
    "random_split_pct": None,

    # P4: how many node failures can a 5-node cluster tolerate and still elect a
    #     leader? (The largest f for which the survivors are still a majority.)
    "failures_tolerated": None,
}

# ---------------------------------------------------------------------------
# Knobs. The clock is in "ticks"; read a tick as roughly one millisecond. The
# defaults make the contrast between fixed and randomized timeouts loud and the
# whole run quick and reproducible.
# ---------------------------------------------------------------------------
N = 5                 # nodes in the cluster (odd numbers avoid even splits)
SEED = 629            # master seed: same seed, same run, on every machine
HEARTBEAT = 15        # a leader sends heartbeats this often (ticks)
ELECTION_MIN = 150    # randomized election timeout: uniform in [MIN, MAX]
ELECTION_MAX = 200    # a window well wider than a message round-trip
ELECTION_FIXED = 150  # the "fixed" timeout everyone shares (plus tiny jitter)
FIXED_SPREAD = 4      # unavoidable timing noise even in the fixed case (ticks)
NET_DELAY = 1         # base one-way message delay (ticks)
NET_JITTER = 6        # extra random delay per message, so messages race (ticks)
TRIALS = 2000         # cold-start elections to run per mode in Part 2
MAX_TICKS = 20000     # hard stop per simulation, so nothing ever runs forever

_UNSET = object()     # marks a TODO you have not filled in yet


class TODONotDone(Exception):
    """Raised by a blank TODO so the lab stops cleanly instead of crashing."""
    def __init__(self, n):
        super().__init__(f"TODO {n} is not filled in yet")
        self.n = n


# ===========================================================================
# The four pieces you fill in. Each one is a sharp bit of the Raft heart.
# ===========================================================================

def majority(n):
    """How many votes a candidate needs to win in a cluster of n nodes.

    This single number is the whole of consensus. A strict majority of the WHOLE
    cluster, so two different majorities must always overlap in at least one
    node, which is why two leaders can never be elected for the same term."""
    # TODO 1 ------------------------------------------------------------------
    # A strict majority of n: more than half. For 5 nodes that is 3, for 7 it is
    # 4. The one-liner is:
    #     return n // 2 + 1
    # -------------------------------------------------------------------------
    result = _UNSET  # <-- replace this with the line above
    if result is _UNSET:
        raise TODONotDone(1)
    return result


def start_election(node):
    """A follower's election timer fired: it becomes a CANDIDATE. It increments
    its term (a brand new election), votes for itself, and starts its tally with
    that one self-vote. Then (back in the caller) it will ask everyone else."""
    # TODO 2 ------------------------------------------------------------------
    # Turn this node into a candidate for a new term. Four lines:
    #   - bump the term by one (this is a fresh election)
    #   - set the role to "candidate"
    #   - vote for itself (voted_for = its own id)
    #   - start the vote tally with just that self-vote (votes = {its id})
    #     node.term += 1
    #     node.role = "candidate"
    #     node.voted_for = node.id
    #     node.votes = {node.id}
    # -------------------------------------------------------------------------
    started = _UNSET  # <-- do the four lines above, then set started = True
    if started is not True:
        raise TODONotDone(2)


def grant_vote(voted_for, candidate_id):
    """Decide whether to grant a vote, given we are already at the candidate's
    term. The rule that makes split votes possible: one vote per term. Grant it
    only if we have not voted yet this term, or we already voted for this very
    candidate (so a resend is safe)."""
    # TODO 3 ------------------------------------------------------------------
    # Grant the vote only if we have NOT already voted this term, or we already
    # voted for this same candidate. `voted_for` is None when we have not voted:
    #     return voted_for is None or voted_for == candidate_id
    # -------------------------------------------------------------------------
    result = _UNSET  # <-- replace this
    if result is _UNSET:
        raise TODONotDone(3)
    return result


def election_timeout(rng, randomized):
    """How long a node waits without hearing from a leader before it starts its
    own election. The fixed case (given) is one shared value plus a little
    unavoidable noise, so nodes tend to fire together. The randomized case is
    the Raft fix: spread the timeouts across a wide window so one node almost
    always wakes clearly first and wins before the others stir."""
    if not randomized:
        return ELECTION_FIXED + rng.randint(0, FIXED_SPREAD)
    # TODO 4 ------------------------------------------------------------------
    # The randomized timeout: a uniform random integer in the window
    # [ELECTION_MIN, ELECTION_MAX]. This spread is the entire fix for split
    # votes, so one node almost always wakes clearly first:
    #     return rng.randint(ELECTION_MIN, ELECTION_MAX)
    # -------------------------------------------------------------------------
    timeout = _UNSET  # <-- replace this
    if timeout is _UNSET:
        raise TODONotDone(4)
    return timeout


# ===========================================================================
# The simulation engine: one node, and a cluster that steps a simulated clock.
# ===========================================================================

class Node:
    """One server in the cluster. It is a follower, a candidate, or a leader,
    and it knows only its own term, who it voted for this term, and (when it is
    a candidate) which votes it has collected."""

    def __init__(self, nid):
        self.id = nid
        self.role = "follower"
        self.term = 0
        self.voted_for = None
        self.votes = set()
        self.deadline = 0          # tick at which the election timer fires
        self.next_heartbeat = 0    # tick a leader next broadcasts (leaders only)
        self.dead = False


class Sim:
    """A discrete-event simulation of one Raft cluster electing a leader.

    No threads, no sockets, no wall clock. We hold a message queue keyed by the
    tick each message is delivered, and advance the clock one tick at a time.
    The first node to win a majority ends the run."""

    def __init__(self, randomized, seed, dead=(), initial_leader=None,
                 fail_leader_at=None, max_ticks=MAX_TICKS, n=N):
        self.n = n
        self.randomized = randomized
        self.rng = random.Random(seed)
        self.initial_leader = initial_leader
        self.fail_leader_at = fail_leader_at
        self.max_ticks = max_ticks
        self.nodes = [Node(i) for i in range(n)]
        self.inbox = defaultdict(list)   # delivery_tick -> [messages]
        self.tick = 0
        self.elected_leader = None
        self.elected_term = None
        self.elected_tick = None
        self.elected_votes = None

        for node in self.nodes:
            if node.id in set(dead):
                node.dead = True

        if initial_leader is not None:
            lead = self.nodes[initial_leader]
            lead.role = "leader"
            lead.term = 1
            lead.next_heartbeat = 0
            for node in self.nodes:
                if node.id != initial_leader and not node.dead:
                    node.term = 1
                    self.reset_deadline(node)
        else:
            # Cold start: no leader, everyone a follower, timers running.
            for node in self.nodes:
                if not node.dead:
                    self.reset_deadline(node)

    def reset_deadline(self, node):
        node.deadline = self.tick + election_timeout(self.rng, self.randomized)

    def send(self, msg):
        delay = NET_DELAY + self.rng.randint(0, NET_JITTER)
        self.inbox[self.tick + delay].append(msg)

    def become_leader(self, node):
        node.role = "leader"
        node.next_heartbeat = self.tick
        if self.elected_leader is None:
            self.elected_leader = node.id
            self.elected_term = node.term
            self.elected_tick = self.tick
            self.elected_votes = len(node.votes)

    def begin_election(self, node):
        start_election(node)                 # TODO 2: becomes candidate
        self.reset_deadline(node)            # retry later if this one splits
        if len(node.votes) >= majority(self.n):   # TODO 1: tiny clusters
            self.become_leader(node)
            return
        for other in self.nodes:
            if other.id != node.id:
                self.send({"type": "rv", "term": node.term,
                           "src": node.id, "dst": other.id})

    def handle(self, msg):
        node = self.nodes[msg["dst"]]
        if node.dead:
            return
        term = msg["term"]
        # Any message from a higher term drags us back to being a follower.
        if term > node.term:
            node.term = term
            node.role = "follower"
            node.voted_for = None
            node.votes = set()

        if msg["type"] == "rv":                      # a vote request
            cand = msg["src"]
            grant = False
            if term == node.term:                    # same term, decide by rule
                grant = grant_vote(node.voted_for, cand)   # TODO 3
            if grant:
                node.voted_for = cand
                self.reset_deadline(node)            # granting resets our timer
            self.send({"type": "vr", "term": node.term, "src": node.id,
                       "dst": cand, "granted": grant})

        elif msg["type"] == "vr":                    # a vote response
            if (node.role == "candidate" and term == node.term
                    and msg["granted"]):
                node.votes.add(msg["src"])
                if len(node.votes) >= majority(self.n):   # TODO 1
                    self.become_leader(node)

        elif msg["type"] == "hb":                    # a heartbeat from a leader
            if term >= node.term:
                node.term = term
                node.role = "follower"
                node.voted_for = None
                node.votes = set()
                self.reset_deadline(node)            # a live leader, so wait

    def step(self):
        t = self.tick
        if (self.fail_leader_at is not None and t == self.fail_leader_at
                and self.initial_leader is not None):
            self.nodes[self.initial_leader].dead = True   # the leader crashes

        for msg in self.inbox.pop(t, []):
            self.handle(msg)

        for node in self.nodes:                      # id order, so it is stable
            if node.dead:
                continue
            if node.role == "leader":
                if t >= node.next_heartbeat:
                    for other in self.nodes:
                        if other.id != node.id:
                            self.send({"type": "hb", "term": node.term,
                                       "src": node.id, "dst": other.id})
                    node.next_heartbeat = t + HEARTBEAT
            elif t >= node.deadline:
                self.begin_election(node)

        self.tick += 1

    def run(self):
        """Run until a leader is elected or we hit the hard tick ceiling."""
        while self.tick < self.max_ticks and self.elected_leader is None:
            self.step()
        return {
            "elected": self.elected_leader is not None,
            "leader": self.elected_leader,
            "term": self.elected_term,
            "tick": self.elected_tick,
            "votes": self.elected_votes,
        }


# ===========================================================================
# Part 1: a leader dies and the cluster elects a new one
# ===========================================================================

def part1():
    print("=" * 78)
    print("Part 1: the leader dies. A follower times out and wins a majority.")
    print("=" * 78)

    fail_at = 500
    sim = Sim(randomized=True, seed=SEED, initial_leader=0, fail_leader_at=fail_at)
    res = sim.run()

    maj = majority(N)
    gap = res["tick"] - fail_at
    print(f"  cluster of {N}, node 0 is the leader, heartbeating every {HEARTBEAT} ticks.")
    print(f"  at tick {fail_at} the leader crashes and the heartbeats stop.")
    print()
    if res["elected"]:
        print(f"  node {res['leader']} timed out, became a candidate, and asked for votes.")
        print(f"  it won with {res['votes']} of {N} votes (majority is {maj}) and became")
        print(f"  the leader for term {res['term']} at tick {res['tick']}.")
        print(f"  the cluster had NO leader for {gap} ticks, then healed itself.")
        print(f"  {res['votes']} >= {maj}, so a strict majority of the whole cluster")
        print("  agreed on one leader. No two nodes can both hold a majority in the")
        print("  same term, which is exactly why there is never more than one leader.")
    else:
        print("  !! no leader was elected; check the knobs.")
    return float(gap), res["votes"], res["term"]


# ===========================================================================
# Part 2: split votes, and why randomized timeouts fix them
# ===========================================================================

def run_cold_elections(randomized, trials):
    """Run `trials` independent cold-start elections (no leader to begin with)
    and report how many election rounds it took in total. A round is one term:
    the leader's winning term equals the number of rounds, and any round before
    the last was a split that elected nobody."""
    total_rounds = 0
    elected = 0
    worst_rounds = 0
    for i in range(trials):
        sim = Sim(randomized=randomized, seed=SEED + i * 7919)
        res = sim.run()
        if res["elected"]:
            elected += 1
            rounds = res["term"]           # term 1 means it won on the first try
            total_rounds += rounds
            worst_rounds = max(worst_rounds, rounds)
    split_rounds = total_rounds - elected
    split_pct = split_rounds / total_rounds * 100 if total_rounds else 0.0
    avg_rounds = total_rounds / elected if elected else 0.0
    return split_pct, avg_rounds, worst_rounds, elected


def part2():
    print("\n" + "=" * 78)
    print("Part 2: split votes. Fixed timeouts stall; randomized ones converge.")
    print("=" * 78)
    print(f"  {TRIALS:,} cold-start elections per mode, cluster of {N}, majority {majority(N)}.")
    print("  A 'round' is one term. If a round elects nobody, the votes split and")
    print("  everyone tries again on the next term.")
    print()

    f_split, f_avg, f_worst, f_elec = run_cold_elections(False, TRIALS)
    r_split, r_avg, r_worst, r_elec = run_cold_elections(True, TRIALS)

    print(f"  FIXED timeouts (everyone waits ~{ELECTION_FIXED} ticks, tiny jitter):")
    print(f"    split-vote rate:     {f_split:5.1f}% of rounds elected nobody")
    print(f"    rounds to a leader:  {f_avg:4.2f} on average, {f_worst} in the worst trial")
    print()
    print(f"  RANDOMIZED timeouts (each waits a random {ELECTION_MIN}-{ELECTION_MAX} ticks):")
    print(f"    split-vote rate:     {r_split:5.1f}% of rounds elected nobody")
    print(f"    rounds to a leader:  {r_avg:4.2f} on average, {r_worst} in the worst trial")
    print()
    drop = f_split / r_split if r_split else float("inf")
    print(f"  Randomizing the timeout cut the split-vote rate about {drop:.0f}x.")
    print("  With fixed timeouts the nodes keep waking together, splitting the vote,")
    print("  and burning term after term. Spreading the timeouts means one node")
    print("  almost always wakes first and locks up a majority before the rest")
    print("  stir. That one change is why Raft elections settle in about one round.")
    return f_split, r_split


# ===========================================================================
# Part 3: the majority rule is fault tolerance
# ===========================================================================

def elects_with_dead(num_dead, seeds=200):
    """Across many seeds, how often does a 5-node cluster elect a leader when
    `num_dead` of its nodes are down from the start?"""
    dead = tuple(range(num_dead))        # nodes 0..num_dead-1 are down
    wins = 0
    for i in range(seeds):
        sim = Sim(randomized=True, seed=SEED + i * 104729, dead=dead,
                  max_ticks=4000)
        if sim.run()["elected"]:
            wins += 1
    return wins


def part3():
    print("\n" + "=" * 78)
    print("Part 3: the majority rule is fault tolerance.")
    print("=" * 78)
    maj = majority(N)
    seeds = 200
    print(f"  cluster of {N}, so a leader needs {maj} votes, a majority of the WHOLE")
    print("  cluster, not of whoever is still alive. Count how often a leader is")
    print(f"  elected across {seeds} seeds as we kill more nodes:")
    print()

    tolerated = -1
    for down in range(0, N + 1):
        alive = N - down
        wins = elects_with_dead(down, seeds)
        possible = "yes" if alive >= maj else "NO (majority impossible)"
        print(f"    {down} down, {alive} alive:  elected in {wins:>3}/{seeds} seeds   "
              f"majority reachable? {possible}")
        if wins == seeds:
            tolerated = down

    print()
    print(f"  A 5-node cluster tolerated {tolerated} failures: with {tolerated} down the")
    print(f"  surviving {N - tolerated} are still a majority and always elect a leader.")
    print(f"  With {tolerated + 1} down only {N - tolerated - 1} remain, which can never reach {maj}")
    print("  votes, so no leader is elected and the cluster is UNAVAILABLE. That is")
    print("  floor((N-1)/2) failures tolerated, straight out of the majority rule.")
    print("  Log replication (the other half of Raft) commits an entry only once a")
    print("  majority has stored it, so it rides on this very same majority.")
    return tolerated


# ===========================================================================
# Scoreboard
# ===========================================================================

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>8,.1f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<30} you = {predicted:>7,.1f}   actual = {actual:>8,.1f} {unit}  {note}")


def self_test():
    """Exercise each TODO once, in isolation and instantly, before we run a
    single simulation. A blank TODO raises TODONotDone, which we turn into a
    clean 'fill in TODO N' message instead of a crash or a hang."""
    missing = set()

    # TODO 1: the majority threshold.
    try:
        majority(N)
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 2: becoming a candidate.
    try:
        start_election(Node(0))
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 3: the vote-granting rule.
    try:
        grant_vote(None, 1)
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 4: the randomized election timeout.
    try:
        election_timeout(random.Random(0), True)
    except TODONotDone as e:
        missing.add(e.n)

    return sorted(missing)


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    gaps = self_test()
    if gaps:
        print("\n  !! Some TODOs are not filled in yet:")
        for n in gaps:
            print(f"       - fill in TODO {n}")
        print("     Fill them in and run again. See solution.py if you get stuck.\n")
        sys.exit(1)

    gap, votes, term = part1()
    fixed_split, random_split = part2()
    tolerated = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 new-leader gap", PREDICTIONS["elect_gap_ticks"], gap, "ticks")
    verdict("P2 fixed split rate", PREDICTIONS["fixed_split_pct"], fixed_split, "%")
    verdict("P3 randomized split rate", PREDICTIONS["random_split_pct"], random_split, "%")
    verdict("P4 failures tolerated", PREDICTIONS["failures_tolerated"], float(tolerated))

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Fixed timeouts split the vote {fixed_split:.0f}% of rounds; randomizing them")
    print(f"  dropped that to {random_split:.0f}%, so elections settle in about one round.")
    print(f"  And a 5-node cluster elected a leader with {tolerated} nodes down but never")
    print(f"  with {tolerated + 1}: a majority of the whole cluster is the line between")
    print("  available and stuck. Consensus is just 'a majority agrees', and the")
    print("  random timeout is the trick that stops everyone agreeing to disagree.")
    print()


if __name__ == "__main__":
    main()
