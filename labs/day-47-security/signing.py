"""
Day 47 lab: security boundaries. The three checks every design must get right,
made concrete and measured. Not a security course, just the parts that show up
when you are drawing boxes and someone asks "wait, who is allowed to do that?"

THIS IS THE STARTER. Fill in PREDICTIONS, then the four numbered TODOs.
The full working version is solution.py in this same folder.
Run it:      python3 signing.py

Standard library only: hmac, hashlib, random, sys. No network, no threads, no
files. Everything is a deterministic simulation. Time is a logical clock (an
integer that ticks per request), so staleness is reproducible to the digit and
the whole run finishes in well under a second. Every random choice (which field
a tamperer flips, which accounts a user pokes at) comes from a seeded RNG.

The three boundaries:
  - Part 1, integrity. Sign a request with HMAC-SHA256 over a shared secret.
    The server recomputes the signature and compares. A tampered payload no
    longer matches, so you can trust the request arrived as it left.
  - Part 2, replay. A VALID signed request, captured off the wire and sent
    again, still verifies, because nothing about it changed. For a transfer
    that is a double charge (callback to Day 25: a nonce is an idempotency key
    at the transport layer). Add a timestamp and a nonce and the replay is
    rejected.
  - Part 3, authentication vs authorization. Authentication is "who are you".
    Authorization is "are you allowed to do THIS". A real logged-in user A asks
    for account B. Authentication passes. Without an ownership check the server
    hands over B's data anyway. That is an IDOR, also called a BOLA. Add the
    ownership check and it is blocked.

The sentence to carry out: a valid token answers "who", never "what". The
"what" is a separate check, and it is the one nobody writes until it is a CVE.
"""

import hashlib
import hmac
import random
import sys

PREDICTIONS = {
    # P1: 10,000 requests are signed, then their payload is tampered WITHOUT
    #     re-signing. How many of those tampered requests still pass signature
    #     verification?
    "tampered_pass": None,

    # P2: one valid signed transfer is captured and sent 50 times to the NAIVE
    #     server (it only checks the signature). How many go through as real
    #     transfers?
    "naive_replays_executed": None,

    # P3: the same 50 sends hit the HARDENED server (signature plus a timestamp
    #     window and a seen-nonce set). How many go through now?
    "hardened_replays_executed": None,

    # P4: user A is a real, authenticated user. A asks for accounts it does not
    #     own. On the authn-ONLY server, what percent of those cross-owner reads
    #     return someone else's data (the IDOR)?
    "authn_only_leak_pct": None,
}

SECRET = b"lab-shared-secret-not-a-real-key"   # a lab secret; never a real one
N_TAMPER_TRIALS = 10_000                        # Part 1 sample size
N_REPLAYS = 50                                  # Part 2: times the attacker resends
REPLAY_WINDOW = 30                              # Part 2: freshness window, in ticks
N_ACCOUNTS = 1_000                              # Part 3: accounts in the store
N_OWNERS = 10                                   # Part 3: users; A owns 1 in N_OWNERS
SEED = 47


# ---------------------------------------------------------------------------
# The four TODOs. Each boundary is one load-bearing line.
# ---------------------------------------------------------------------------

def sign(secret, canonical):
    """TODO 1, integrity (sender side). Produce an HMAC-SHA256 tag over the
    canonical request bytes, keyed by the shared secret. This tag travels with
    the request. Only someone holding the secret can produce it, so it both
    proves origin and pins the exact bytes."""
    # TODO 1 ------------------------------------------------------------------
    # hmac.new takes the key (bytes), the message (bytes), and the hash. The
    # canonical string must be encoded to bytes first. Return the hex digest:
    #     return hmac.new(secret, canonical.encode(), hashlib.sha256).hexdigest()
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def verify_sig(expected, provided):
    """TODO 2, integrity (server side). The server recomputes the tag from the
    bytes it received and compares it to the one that arrived. Use a
    constant-time compare so a timing side channel cannot leak the tag byte by
    byte."""
    # TODO 2 ------------------------------------------------------------------
    # Do NOT use ==. A plain string compare returns faster on an early
    # mismatch, which leaks the tag one byte at a time. Use the constant-time
    # compare built for exactly this:
    #     return hmac.compare_digest(expected, provided)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def is_fresh(now, ts, nonce, seen, window):
    """TODO 3, replay defense. A request is fresh only if its timestamp is
    inside the window (not stale, not from the future) AND its nonce has not
    been seen before. The nonce is a one-time idempotency key at the transport
    layer (Day 25)."""
    # TODO 3 ------------------------------------------------------------------
    # Two conditions, both must hold. The timestamp age `now - ts` must be
    # between 0 and `window` (not from the future, not too old), and the nonce
    # must not already be in `seen`:
    #     return (0 <= now - ts <= window) and (nonce not in seen)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def owns(resource_owner, caller):
    """TODO 4, authorization. Authentication already proved the caller is who
    they say. This answers the other question: does the thing they are reaching
    for actually belong to them. One comparison stands between a valid login and
    an IDOR."""
    # TODO 4 ------------------------------------------------------------------
    # The resource carries an owner. The caller is authenticated. Permission is
    # simply whether the owner is the caller:
    #     return resource_owner == caller
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if sign(b"k", "x") is None:
        return 1
    if verify_sig("a", "a") is None:
        return 2
    if is_fresh(10, 10, "n", set(), 30) is None:
        return 3
    if owns("user_0", "user_0") is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# A request, its canonical form, and the server-side integrity check.
# ---------------------------------------------------------------------------

def canonical(req):
    """The exact bytes both sides agree to sign. Order and separators are fixed,
    so sender and server build the identical string. Anything not in here is NOT
    protected, which is why the whole security-relevant payload goes in."""
    return "\n".join([
        req["method"],
        req["path"],
        str(req["ts"]),
        req["nonce"],
        req["body"],
    ])


def make_signed(secret, method, path, ts, nonce, body):
    """Build a request and attach its signature, the way a well-behaved client
    would before putting it on the wire."""
    req = {"method": method, "path": path, "ts": ts, "nonce": nonce, "body": body}
    req["sig"] = sign(secret, canonical(req))
    return req


def verify_request(secret, req):
    """Server-side integrity check: recompute the tag over the received bytes
    and compare it, in constant time, to the tag that arrived."""
    expected = sign(secret, canonical(req))
    return verify_sig(expected, req["sig"])


# ---------------------------------------------------------------------------
# Part 1: integrity. A tampered payload breaks the signature.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: integrity. Sign with HMAC, and a tampered payload stops")
    print("        matching")
    print("=" * 78)
    rng = random.Random(SEED)
    ops = ["transfer", "refund", "close", "update"]

    valid_pass = 0
    tampered_pass = 0
    sample = None
    for i in range(N_TAMPER_TRIALS):
        amount = rng.randint(1, 1000)
        nonce = f"{rng.getrandbits(64):016x}"
        req = make_signed(SECRET, "POST", "/transfers", 1000 + i, nonce,
                          f"op={rng.choice(ops)}&amount={amount}")

        # The honest request verifies.
        if verify_request(SECRET, req):
            valid_pass += 1

        # The attacker flips the amount in flight but cannot re-sign (no secret),
        # so the old signature travels on with the new body.
        tampered = dict(req)
        tampered["body"] = f"op=transfer&amount={amount * 1000}"
        if verify_request(SECRET, tampered):
            tampered_pass += 1

        if sample is None:
            sample = (req["body"], req["sig"], tampered["body"])

    print(f"  signed and sent {N_TAMPER_TRIALS:,} requests, then tampered each one.")
    print(f"    honest requests that verified:     {valid_pass:,} / {N_TAMPER_TRIALS:,}")
    print(f"    tampered requests that verified:   {tampered_pass:,} / {N_TAMPER_TRIALS:,}")
    print()
    print("  one example:")
    print(f"    body as signed:   {sample[0]}")
    print(f"    signature (HMAC): {sample[1][:24]}...")
    print(f"    body as tampered: {sample[2]}   <- attacker changed the amount")
    print("  The server recomputes the HMAC over the bytes it received. One")
    print("  changed character gives a completely different tag, so the stale")
    print("  signature no longer matches and the request is thrown out. Without")
    print("  the secret, the attacker cannot forge a tag for the new bytes.")
    return tampered_pass


# ---------------------------------------------------------------------------
# Part 2: replay. A valid request sent twice is still valid, until you add a
# timestamp and a nonce.
# ---------------------------------------------------------------------------

class Bank:
    """A toy ledger so a replay does visible damage: every accepted transfer
    moves real money. A transfer is NOT idempotent, which is the whole point."""

    def __init__(self, balance):
        self.balance = balance
        self.transfers = 0

    def transfer(self, amount):
        self.balance -= amount
        self.transfers += 1


def part2():
    print("\n" + "=" * 78)
    print("Part 2: replay. A valid signature does not stop the SAME request")
    print("        being sent again")
    print("=" * 78)

    # One genuine, correctly signed transfer of 5,000.
    amount = 5000
    captured = make_signed(SECRET, "POST", "/transfers", ts=1000,
                           nonce="a1b2c3d4e5f60718", body=f"op=transfer&amount={amount}")
    print(f"  the attacker captures ONE valid transfer of {amount} off the wire,")
    print(f"  then sends it {N_REPLAYS} times to each server.")
    print()

    # Naive server: signature check only. The signature is valid every time,
    # because nothing about the bytes changed.
    naive_bank = Bank(balance=100_000)
    naive_executed = 0
    for _ in range(N_REPLAYS):
        if verify_request(SECRET, captured):
            naive_bank.transfer(amount)
            naive_executed += 1

    print("  naive server (checks the signature, nothing else):")
    print(f"    replays that executed: {naive_executed} / {N_REPLAYS}")
    print(f"    account drained by:    {naive_executed * amount:,}  "
          f"(balance {100_000} -> {naive_bank.balance:,})")
    print("    The signature is valid on every copy, so every copy goes through.")
    print("    One real request became 50 real transfers. This is the replay hole.")
    print()

    # Hardened server: signature AND freshness (timestamp window + seen nonces).
    hardened_bank = Bank(balance=100_000)
    seen = set()
    now = 1000                      # logical clock; each send ticks it forward
    hardened_executed = 0
    for _ in range(N_REPLAYS):
        now += 1
        ok = (verify_request(SECRET, captured)
              and is_fresh(now, captured["ts"], captured["nonce"], seen, REPLAY_WINDOW))
        if ok:
            seen.add(captured["nonce"])
            hardened_bank.transfer(amount)
            hardened_executed += 1

    print("  hardened server (signature + timestamp window + seen-nonce set):")
    print(f"    replays that executed: {hardened_executed} / {N_REPLAYS}")
    print(f"    account drained by:    {hardened_executed * amount:,}  "
          f"(balance {100_000} -> {hardened_bank.balance:,})")
    print("    The first copy is accepted and its nonce is remembered. Every")
    print("    later copy carries the same nonce, so it is rejected as a replay.")
    print()

    # A second, separate defense: a stale timestamp is refused even with a fresh
    # nonce. This is what stops a request captured long ago from being useful.
    old = make_signed(SECRET, "POST", "/transfers", ts=1000,
                      nonce="ffffffffffffffff", body="op=transfer&amount=5000")
    far_future_now = 1000 + REPLAY_WINDOW + 50
    stale_ok = is_fresh(far_future_now, old["ts"], old["nonce"], set(), REPLAY_WINDOW)
    print(f"  stale-timestamp check: a validly signed, never-seen request whose")
    print(f"  timestamp is {REPLAY_WINDOW + 50} ticks old -> accepted? {stale_ok}")
    print("  So even a brand-new nonce cannot save a request that sat around too")
    print("  long. Timestamp bounds the window; the nonce kills repeats inside it.")
    return naive_executed, hardened_executed


# ---------------------------------------------------------------------------
# Part 3: authentication vs authorization, and the IDOR nobody checks.
# ---------------------------------------------------------------------------

def owner_of(account_index):
    """Which user owns a given account. Spread accounts round-robin across the
    users, so user_0 owns accounts 0, N_OWNERS, 2*N_OWNERS, and so on."""
    return f"user_{account_index % N_OWNERS}"


def handle_read(caller, account_index, enforce_authz):
    """Serve GET /accounts/<index> for an authenticated caller.

    Authentication has ALREADY passed: `caller` is a genuine, logged-in user.
    With enforce_authz False the server stops there and returns the data (the
    bug). With it True the server also checks ownership before answering.
    Returns the account data on success, or None when access is denied."""
    data = f"balance-and-pii-for-account-{account_index}"
    if enforce_authz and not owns(owner_of(account_index), caller):
        return None                          # 403: authenticated, but not yours
    return data                              # 200: here is the data


def part3():
    print("\n" + "=" * 78)
    print("Part 3: authentication vs authorization. A valid login is not")
    print("        permission")
    print("=" * 78)

    caller = "user_0"                        # a real, authenticated user
    owned = [i for i in range(N_ACCOUNTS) if owner_of(i) == caller]
    cross = [i for i in range(N_ACCOUNTS) if owner_of(i) != caller]
    print(f"  {N_ACCOUNTS:,} accounts across {N_OWNERS} users. The caller is {caller}, a")
    print(f"  genuine logged-in user who owns {len(owned)} accounts. Authentication")
    print(f"  passes for every request below; the only question is authorization.")
    print()

    # The authn-only server: a valid session is treated as permission.
    leaked = 0
    for i in cross:
        if handle_read(caller, i, enforce_authz=False) is not None:
            leaked += 1
    authn_only_leak_pct = leaked / len(cross) * 100

    print("  authn-ONLY server (a valid session is enough):")
    print(f"    cross-owner reads attempted: {len(cross)}")
    print(f"    that returned the data:      {leaked}  ({authn_only_leak_pct:.0f}%)")
    print("    Every account A does not own is handed over anyway. A just changes")
    print("    the id in the URL (/accounts/42 -> /accounts/43) and reads the next")
    print("    person's data. That is an IDOR, also called a BOLA. The number one")
    print("    API risk in the OWASP list, and it is a missing if-statement.")
    print()

    # Add the ownership check.
    leaked_authz = 0
    for i in cross:
        if handle_read(caller, i, enforce_authz=True) is not None:
            leaked_authz += 1
    served_own = sum(1 for i in owned
                     if handle_read(caller, i, enforce_authz=True) is not None)

    print("  with the ownership check added (authentication + authorization):")
    print(f"    cross-owner reads that leaked: {leaked_authz}  (0%)")
    print(f"    own-account reads still served: {served_own} / {len(owned)}  (100%)")
    print("    The check blocks every account A does not own, and still serves")
    print("    every account A does. It is not 'deny everything'; it is 'deny what")
    print("    is not yours'. Authentication answered WHO. This answers WHAT.")
    return authn_only_leak_pct, leaked_authz, served_own, len(owned)


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>7} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    note = "     close enough" if diff <= max(1.0, 0.1 * abs(predicted)) \
        else f"  off by {diff:g}"
    print(f"  {name:<34} you = {predicted:>6}   actual = {actual:>7} {unit}  {note}")


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

    p1 = part1()
    naive, hardened = part2()
    leak_pct, leaked_authz, served_own, owned_total = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 tampered requests passing", PREDICTIONS["tampered_pass"], p1)
    verdict("P2 naive replays executed", PREDICTIONS["naive_replays_executed"], naive)
    verdict("P3 hardened replays executed", PREDICTIONS["hardened_replays_executed"], hardened)
    verdict("P4 authn-only leak %", PREDICTIONS["authn_only_leak_pct"], round(leak_pct), "%")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  Integrity: {p1} of {N_TAMPER_TRIALS:,} tampered requests got through. A single")
    print("  changed byte breaks the HMAC, so the signature is a seal on the bytes.")
    print(f"  Replay: the same captured transfer executed {naive} times on the naive")
    print(f"  server and {hardened} time once a timestamp and nonce were added. A valid")
    print("  signature says the bytes are genuine, not that they are new.")
    print(f"  Authorization: the authn-only server leaked {leak_pct:.0f}% of other users'")
    print(f"  accounts; one ownership check took that to 0% while still serving all")
    print(f"  {owned_total} of the caller's own. Authentication is WHO. Authorization is WHAT.")
    print("  A valid token is not permission.")
    print()


if __name__ == "__main__":
    main()
