---
title: "Day 47: security boundaries"
parent: "Week 7: production"
nav_order: 5
has_children: true
---

# Day 47
## Authentication vs authorization, signed requests, and the IDOR nobody checks 🔐

Today's one idea: every design has to answer three security questions, and people keep collapsing them into one. Is this request really from who it claims? Is it a fresh request or an old one played back? And even when the caller is genuine, are they allowed to touch this particular thing? The first is a signature, the second is a timestamp and a nonce, the third is an ownership check. Skip the third and a real, logged-in user quietly reads everybody else's data, which is the single most common serious bug shipped to production APIs.

This is not a security course, and I am not going to turn you into a pentester in one day. This is the slice of security that shows up when you are drawing boxes and arrows, the part an interviewer prods when they ask "and how does service B know this request is allowed?" Four small measurements, pure Python, no libraries. By the end you will have watched a tampered request get caught, a replayed transfer drain an account 50 times, and an authenticated user walk straight into other people's accounts until one if-statement stops them.

---

## Before you start ⏪

You need Day 25 fresh, delivery semantics and idempotency, because today's replay attack is the same problem wearing a hoodie. On Day 25 a message arrived more than once because the network retried, and you made the handler idempotent so duplicates did nothing. Today an attacker resends the message on purpose, and the defence, a one-time nonce, is the idempotency key moved down to the transport layer. Same idea, hostile instead of accidental.

No new Python. If you can call a function and compare two strings, you can do this lab. The whole thing is `hmac` and `hashlib` from the standard library, both of which are a few lines each.

---

## Words you will meet today 📖

A message authentication code (MAC) is a short tag computed from a message and a secret key. Anyone with the key can produce it and check it; anyone without the key cannot. It proves two things at once, that the message came from someone holding the key, and that the bytes were not changed on the way.

HMAC is the standard way to build a MAC out of a hash function like SHA-256. You will call `hmac.new(key, message, hashlib.sha256)` and get a tag. It is everywhere: API request signing, webhooks, session cookies, JWT signatures.

A canonical string is the exact, agreed-upon serialisation of a request that both the sender and the server sign. Same fields, same order, same separators. If the two sides build even slightly different bytes, the tags will never match, so the format has to be pinned down precisely.

A nonce is a number used once. The client puts a fresh random nonce in each request, the server remembers the ones it has seen, and a repeat is rejected. It is what turns a valid-forever signed request into a valid-once one.

A replay attack is capturing a legitimate request and sending it again. The signature still checks out, because nothing about the bytes changed, so for anything that is not idempotent (a transfer, a vote, a "ship the order") it does real damage.

Authentication is establishing who the caller is. A valid signature, a session cookie, a token. It answers "who".

Authorization is deciding whether that caller may do this specific thing to this specific resource. It answers "what are you allowed to touch". Different question, different check, and the one people forget.

IDOR, insecure direct object reference, also called BOLA, broken object level authorization, is the bug where a request names an object directly (an id in the URL) and the server hands it over without checking the caller owns it. Change the id, read someone else's data.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these:
- [OWASP API Security Top 10: Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/). The number one item on the list, which is today's Part 3. Short, and it names the exact mistake you are about to measure. If you read one thing, read this.
- [PortSwigger: Insecure direct object references](https://portswigger.net/web-security/access-control/idor). The hands-on view of the same bug, with the sequential-id and leaked-reference variants laid out plainly.
- [AWS Signature Version 4](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_aws-signing.html). The real-world version of Part 1 and Part 2: a canonical request, an HMAC signature, and a timestamp so a captured request cannot be replayed later. This is the production shape of today's lab.
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html). The checklist version: enforce at the right layer, deny by default, check ownership on every object access.

Watch:
- [HMAC explained](https://www.youtube.com/watch?v=MKn3cxFNN1I) by Jan Goebel, about 7 minutes. Exactly the mechanism behind Part 1, drawn out step by step. Watch before the lab.
- [Insecure Direct Object Reference (IDOR) Explained](https://www.youtube.com/watch?v=rloqMGcPMkI) by PwnFunction, about 8 minutes. The clearest short walk through the Part 3 bug, with real request examples. Watch after the lab.

### The signature is a seal on the bytes (14 min)

Picture sending a cheque by courier. Anyone along the way can read it, and a dishonest courier can change the amount with a pen. What stops them is not that the envelope is sealed, it is that the cheque carries your signature, and your signature only matches the figures you actually wrote. Change the amount and the signature no longer belongs to it. That is HMAC.

Here is the mechanism. The client and the server share a secret key, agreed ahead of time, never sent on the wire. The client builds a canonical string out of the request, the method, the path, a timestamp, a nonce, and the body, in a fixed order with fixed separators. It runs HMAC-SHA256 over those bytes with the secret, and gets a tag, a hex string. That tag rides along with the request. When the request lands, the server rebuilds the exact same canonical string from the fields it received, runs the same HMAC with its copy of the secret, and compares its tag to the one that arrived. Match means the request is genuine and untouched. Mismatch means it was altered, or the sender did not hold the secret, and the server throws it out.

Two details matter more than they look. First, only the bytes you put in the canonical string are protected. If you sign the path and body but forget the amount, an attacker changes the amount freely and your signature still matches. So you sign the whole security-relevant payload, and you pin the canonical form exactly, because if the two sides build different bytes the tags will never agree and every honest request fails too. Second, compare the tags with a constant-time compare, `hmac.compare_digest`, not with `==`. A plain string compare returns the instant it hits a difference, and that tiny timing difference, measured over many tries, leaks the correct tag one byte at a time. It sounds paranoid. It is a real, named attack, and the fix is one function call, so just use it.

In Part 1 you sign 10,000 requests, tamper the payload of each one without re-signing, and count how many still verify. Write down your guess now. The answer is a round number, and it is the point of the whole exercise.

### A valid request sent twice is a replay (12 min)

Now the part that catches people, because it feels like the signature should have handled it. A signature proves the bytes are genuine and unaltered. It says nothing about whether you have seen them before. So if an attacker captures one perfectly valid, perfectly signed request off the wire and sends it again, byte for byte, it verifies. Of course it does. Nothing changed, so the tag still matches.

For a read, who cares, you read the same thing twice. For anything that changes state, this is a disaster. A signed "transfer 5,000 rupees" request, captured and sent 50 times, is 50 real transfers, each one with a flawless signature. This is Day 25 turned hostile. There the duplicate came from the network retrying; here it comes from an attacker with a packet capture. The damage is identical, and so, it turns out, is the fix.

You add two things to the signed data. A timestamp, so each request is only valid for a short window, which means a request captured today cannot be useful next week, it is stale. And a nonce, a unique value the client generates per request, which the server records the first time it sees it and rejects on every repeat. The timestamp bounds how long a request lives, which also keeps the set of remembered nonces from growing forever (you only have to remember nonces inside the current window). The nonce kills duplicates inside that window. Together they turn a valid-forever request into a valid-once one. And notice what the nonce actually is: the idempotency key from Day 25, pushed down to the transport. At-least-once on the wire, made safe by refusing the duplicate. In Part 2 you watch a captured transfer drain an account on the naive server, then add the timestamp and nonce and watch the same 50 sends collapse to one.

### Authentication is who, authorization is what (14 min)

This is the most important idea of the day, and it is almost embarrassingly simple, which is exactly why it gets skipped.

Authentication is proving who you are. Authorization is deciding what you are allowed to do. A bank makes the distinction physical. The guard at the door checks your ID, that is authentication, he confirms you are a real customer. But he does not then let you open any locker in the vault. A second check, is this your locker, stands between you and the box, and that is authorization. Collapse the two, let anyone who got past the guard open any locker, and you do not have a vault, you have a shelf.

Software does this collapse constantly. A user logs in, gets a valid session or token, and the server treats "has a valid token" as "is allowed to do this". Then the endpoint is `GET /accounts/8821`, the user is genuinely logged in, authentication passes cleanly, and the server returns account 8821. The user did not need to hack anything. They changed 8821 to 8822 in the URL and read the next person's account. The token was valid the whole time. The token was never the question. Ownership was the question, and nobody asked it.

That is an IDOR, also called a BOLA, and it is the number one item on the OWASP API Security Top 10 for a reason: it is everywhere, and exploiting it is just incrementing a number. The defence is not a better token, not HTTPS, not rate limiting, none of which is an ownership check. The defence is one line at the point where you fetch the object: does this object belong to the caller, and if not, 403. Ideally you bake it into the query itself, `WHERE owner_id = :caller`, so a forgotten check cannot leak. And do not reach for "the id is a random UUID so nobody can guess it". That is not access control, it is hoping, and UUIDs leak through logs, shared links, referrer headers and error messages all the time. Hard to guess is not the same as not allowed. In Part 3 you watch an authenticated user read 100% of other people's accounts, then add the ownership check and watch it drop to zero while they keep full access to their own.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-47-drills.md`](../notes/day-47-drills.md).

D1. A request is signed with HMAC-SHA256 over method, path, timestamp, nonce and body. An attacker on the network changes the body but cannot change the signature (no secret). What happens at the server? And what part of the request is NOT protected if you forget to include it in the signed string?

D2. A valid, signed, non-idempotent transfer is captured and replayed. Explain why the signature still verifies. Then explain how a timestamp window and a nonce each stop the replay, and which one does what. Tie the nonce back to the idempotency key from Day 25.

D3. Define authentication and authorization in one line each. For `GET /accounts/8821` from a logged-in user, say which check answers "is this a real user" and which answers "is 8821 theirs", and what goes wrong if you do only the first.

D4. An IDOR, also called a BOLA. Describe the classic version with sequential ids in a URL, say why it is the top item on the OWASP API Security list, and explain why rate limiting, HTTPS and a valid JWT do nothing to stop it.

D5. Where should the ownership check live: in the client, in an API gateway, or in the service that owns the data, and why? And why is "the id is a random UUID so nobody can guess it" not an access control?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-47-security/signing.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-47-security/signing.py).

It is in three parts. Part 1 signs 10,000 requests with HMAC-SHA256, tampers each payload, and counts how many tampered requests still verify. Part 2 captures one valid signed transfer and replays it 50 times, first against a naive server that checks only the signature, then against a hardened one that also checks a timestamp window and a seen-nonce set. Part 3 sets up 1,000 accounts across 10 users, has one authenticated user ask for accounts it does not own, and measures the leak with and without an ownership check.

Standard library only, `hmac` and `hashlib`. Time is a logical clock (an integer that ticks per request), so the run is deterministic and finishes in under a second. Nothing to clean up.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. 10,000 requests are signed, then their payload is tampered without re-signing. How many of those tampered requests still pass verification?
- P2. One valid signed transfer is captured and sent 50 times to the naive server (signature check only). How many go through as real transfers?
- P3. The same 50 sends hit the hardened server (signature plus timestamp window plus seen-nonce set). How many go through now?
- P4. A real, authenticated user asks for accounts it does not own. On the authn-only server, what percent of those cross-owner reads return someone else's data?

P4 is the one to sit with. The user is genuinely logged in, every request is authentic. Guess the percent anyway, then see if your gut was too generous.

### Fill in the TODOs

1. TODO 1 is the signature itself, one call to `hmac.new(...).hexdigest()` over the canonical bytes. The seal.
2. TODO 2 is the verify, a constant-time compare of the two tags. Use `hmac.compare_digest`, not `==`, and the comment tells you why.
3. TODO 3 is the replay defence, the freshness predicate: the timestamp is inside the window and the nonce has not been seen. This one line is the whole Part 2 fix.
4. TODO 4 is the authorization check, does this resource belong to the caller. One comparison stands between a valid login and an IDOR.

```bash
cd labs/day-47-security
python3 signing.py
```

### What you're going to discover

Part 1 is clean and absolute. Zero of 10,000 tampered requests get through. One changed byte gives a completely different tag, so the stale signature cannot match, and without the secret there is no way to forge a new one. The signature is a seal on the exact bytes.

Part 2 is the one that should make you sit up. The naive server runs all 50 replays as real transfers and drains the account, because the signature is valid on every copy. The signature proved the request was genuine, which it was, it just never asked whether it was new. Add the timestamp and nonce and the same 50 sends collapse to one: the first is accepted and its nonce remembered, every later copy is rejected as a replay. There is also a separate check that a stale timestamp is refused even with a fresh nonce, which is what stops a request captured long ago from ever being useful.

Part 3 is the quiet disaster. The authn-only server leaks 100% of the accounts the user does not own. Not because the user hacked anything, but because the server mistook "is a valid user" for "is allowed to see this". Add one ownership check and the leak goes to zero, while the user keeps full access to all 100 of their own accounts. It is not "deny everything", it is "deny what is not yours", and it is a single if-statement.

### Traps ⚠️

- Do not compare signatures with `==`. The lab uses `hmac.compare_digest` on purpose. Plain `==` short-circuits on the first mismatched byte, and that timing difference is a real side channel that leaks the tag. One function call fixes it, so there is no excuse to use the leaky one.
- Everything security-relevant must go into the canonical string. If you leave a field out of what you sign, you have not protected it, and an attacker can change exactly that field. The lab signs the whole payload for this reason.
- The nonce set has to be bounded by the timestamp window in real life, or it grows forever and becomes its own denial-of-service. The lab keeps it simple, but note why the timestamp is not optional: it is what lets you forget old nonces safely.
- Do not confuse "hard to guess" with "not allowed". A random UUID id is not authorization. The ownership check is authorization. In Part 3 the ids are plain integers to make the IDOR obvious, but switching them to UUIDs would not have fixed a thing.

### Deliverable

[`labs/day-47-security/RESULTS.md`](../labs/day-47-security/RESULTS.md) has a skeleton. Paste the output, and write one line: a valid signature caught the tampered request but not the replay, and a valid login was not permission. Why are those three separate checks, not one?

---

## Block 4: write (30 min) 📣

Your angle today is the reframe that most people have backwards: "I captured one valid, signed money transfer and replayed it 50 times, and it went through 50 times, because a valid signature means the bytes are genuine, not that they are new. And an authenticated user read 100% of other people's accounts until one ownership check stopped them. Authentication is who you are. Authorization is what you are allowed to touch. They are different checks, and the second is the one everyone forgets." The scoreboard, 0 tampered through, 50 replays to 1, 100% leak to 0%, is the screenshot.

Example posts are on the [Day 47 posts](../shares/day-47-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the replay numbers (naive versus hardened) and the authn-only leak percent you measured, and one thing you still cannot explain.

Day 48 is cost and capacity planning: reading a cloud bill, right-sizing, and the arithmetic that tells you whether a design is affordable before you build it. Today you made sure the system cannot be tricked or walked into. Tomorrow you make sure you can actually pay for it.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The server rebuilds the canonical string from the fields it received, runs HMAC-SHA256 over it with its own copy of the secret, and compares that tag to the one that arrived, in constant time. The changed body produces a different tag, so the comparison fails and the request is dropped. What is not protected is anything you left out of the signed string. If the amount, a header, or a query parameter is not in the canonical form, the attacker can change exactly that field and the signature still matches, because the signature only ever covered the bytes you fed it. This is why you sign the whole security-relevant payload and define the canonical form strictly, so the sender and server build identical bytes.

D2. The signature verifies on a replay because HMAC is computed over bytes, and a replay is the identical bytes, so the tag is identical too. HMAC proves the request is genuine and unaltered; it carries no notion of "have I seen this before". The timestamp gives each request a short validity window, so a request captured and sat on goes stale and is refused later, and it also bounds how many nonces the server must remember. The nonce is a unique one-time value the server records on first use and rejects on any repeat, which catches a replay even inside the window. So the timestamp bounds the window, the nonce kills duplicates within it. The nonce is the idempotency key from Day 25 moved to the transport layer: the wire delivers at-least-once, and refusing the duplicate makes the effect exactly-once.

D3. Authentication is proving who the caller is (a valid signature, session or token). Authorization is deciding whether that caller may perform this specific action on this specific resource. For `GET /accounts/8821`, authentication answers "is this a real, logged-in user", authorization answers "does account 8821 belong to them". If you do only authentication, any logged-in user can read any account by changing the id in the URL, because being a genuine user was mistaken for being allowed. That is the IDOR, and it is why the two checks must stay separate.

D4. An IDOR (insecure direct object reference), also called a BOLA (broken object level authorization), is when a request names an object directly, usually an id in the URL or body, and the server returns or changes it without checking the caller owns it. The classic version is sequential ids: `/invoices/1001` is yours, so you try `/invoices/1002` and read the next customer's invoice. It is the top item on the OWASP API Security list because it is extremely common and trivial to exploit, you just increment a number. Rate limiting only slows a bulk scrape, it does not stop a single unauthorized read; HTTPS protects data in transit but the attacker is a perfectly legitimate TLS client; a valid JWT proves identity, which was never in doubt. None of them is an ownership check, and the ownership check is the only thing that closes the hole.

D5. The ownership check must live in the service that owns the data, as close to the data as possible, because that is the only layer that knows the true owner and cannot be bypassed. A gateway can do coarse checks (valid token, active tenant) but it usually does not know that account 8821 belongs to user 42, so object-level authorization belongs in the service, ideally folded into the query itself (`WHERE owner_id = :caller`) so a forgotten check cannot leak. Never in the client, which the attacker fully controls. And a random UUID is not access control, it is security by obscurity: UUIDs leak through logs, referrer headers, shared links, browser history and error messages, and the moment one leaks the object is wide open, because there was never a check. Hard to guess is not the same as not allowed.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-47-security/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-47-security/solution.py).

TODO 1, the signature, one HMAC-SHA256 over the canonical bytes:

```python
return hmac.new(secret, canonical.encode(), hashlib.sha256).hexdigest()
```

TODO 2, the verify, a constant-time compare (never `==`):

```python
return hmac.compare_digest(expected, provided)
```

TODO 3, the replay defence, fresh only if the timestamp is in the window and the nonce is new:

```python
return (0 <= now - ts <= window) and (nonce not in seen)
```

TODO 4, authorization, the ownership check that stands between a valid login and an IDOR:

```python
return resource_owner == caller
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. Runs in under a second.

```
==============================================================================
Part 1: integrity. Sign with HMAC, and a tampered payload stops
        matching
==============================================================================
  signed and sent 10,000 requests, then tampered each one.
    honest requests that verified:     10,000 / 10,000
    tampered requests that verified:   0 / 10,000

  one example:
    body as signed:   op=update&amount=361
    signature (HMAC): a81b0557de48bfabaff5cc41...
    body as tampered: op=transfer&amount=361000   <- attacker changed the amount
  The server recomputes the HMAC over the bytes it received. One
  changed character gives a completely different tag, so the stale
  signature no longer matches and the request is thrown out. Without
  the secret, the attacker cannot forge a tag for the new bytes.

==============================================================================
Part 2: replay. A valid signature does not stop the SAME request
        being sent again
==============================================================================
  the attacker captures ONE valid transfer of 5000 off the wire,
  then sends it 50 times to each server.

  naive server (checks the signature, nothing else):
    replays that executed: 50 / 50
    account drained by:    250,000  (balance 100000 -> -150,000)
    The signature is valid on every copy, so every copy goes through.
    One real request became 50 real transfers. This is the replay hole.

  hardened server (signature + timestamp window + seen-nonce set):
    replays that executed: 1 / 50
    account drained by:    5,000  (balance 100000 -> 95,000)
    The first copy is accepted and its nonce is remembered. Every
    later copy carries the same nonce, so it is rejected as a replay.

  stale-timestamp check: a validly signed, never-seen request whose
  timestamp is 80 ticks old -> accepted? False
  So even a brand-new nonce cannot save a request that sat around too
  long. Timestamp bounds the window; the nonce kills repeats inside it.

==============================================================================
Part 3: authentication vs authorization. A valid login is not
        permission
==============================================================================
  1,000 accounts across 10 users. The caller is user_0, a
  genuine logged-in user who owns 100 accounts. Authentication
  passes for every request below; the only question is authorization.

  authn-ONLY server (a valid session is enough):
    cross-owner reads attempted: 900
    that returned the data:      900  (100%)
    Every account A does not own is handed over anyway. A just changes
    the id in the URL (/accounts/42 -> /accounts/43) and reads the next
    person's data. That is an IDOR, also called a BOLA. The number one
    API risk in the OWASP list, and it is a missing if-statement.

  with the ownership check added (authentication + authorization):
    cross-owner reads that leaked: 0  (0%)
    own-account reads still served: 100 / 100  (100%)
    The check blocks every account A does not own, and still serves
    every account A does. It is not 'deny everything'; it is 'deny what
    is not yours'. Authentication answered WHO. This answers WHAT.

==============================================================================
Scoreboard
==============================================================================
  P1 tampered requests passing       you =      0   actual =       0        close enough
  P2 naive replays executed          you =     50   actual =      50        close enough
  P3 hardened replays executed       you =      1   actual =       1        close enough
  P4 authn-only leak %               you =    100   actual =     100 %       close enough

==============================================================================
The number to carry
==============================================================================
  Integrity: 0 of 10,000 tampered requests got through. A single
  changed byte breaks the HMAC, so the signature is a seal on the bytes.
  Replay: the same captured transfer executed 50 times on the naive
  server and 1 time once a timestamp and nonce were added. A valid
  signature says the bytes are genuine, not that they are new.
  Authorization: the authn-only server leaked 100% of other users'
  accounts; one ownership check took that to 0% while still serving all
  100 of the caller's own. Authentication is WHO. Authorization is WHAT.
  A valid token is not permission.
```

Part 1 is the seal. 10,000 requests signed, every payload tampered, and not one tampered request verified. HMAC is computed over the exact bytes, so flipping any of them yields a different tag, and the attacker cannot forge a matching one without the secret. This is what "signed request" buys you: tamper-evidence on the whole payload you chose to sign.

Part 2 is the trap. The naive server, checking only the signature, ran all 50 replays as real transfers and pushed the account to minus 150,000, because every copy carried the same valid signature. The signature was never lying, the request really was genuine, it just was not new, and the server had no way to tell. Add a timestamp window and a seen-nonce set and the same 50 sends drop to a single transfer. The first is accepted and its nonce recorded, and every replay after that is refused. The stale-timestamp line shows the other half: a request whose timestamp is too old is refused even with a fresh nonce, which is what stops something captured last week from working today.

Part 3 is the one to remember. The user was authenticated the entire time, a real account holder with a valid session. On the authn-only server they read 100% of the 900 accounts they did not own, by nothing more than asking for them. The server confused "who" with "what". Add the ownership check and the leak is zero, and the user still reads all 100 accounts that are actually theirs. That is the shape of a correct authorization check: it blocks what is not yours and nothing else.

The one line to carry out of today: a signature proves the bytes are genuine, a nonce proves they are fresh, and an ownership check proves the caller is allowed. Three different questions, three different checks, and a valid token answers only the first.

</details>
