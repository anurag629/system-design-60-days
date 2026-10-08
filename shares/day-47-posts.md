---
title: "Day 47 posts"
parent: "Day 47: security boundaries"
grand_parent: "Week 7: production"
nav_order: 3
---

# Day 47 posts: LinkedIn and X

The scoreboard makes a clean screenshot: 0 tampered requests through, a captured transfer going from 50 replays to 1, and an authn-only server leaking 100% of other people's accounts until one ownership check takes it to 0%. Swap in your own numbers and voice.

## LinkedIn

Day 47 of 60 days of system design. Today was the unglamorous one: the three security checks every design has to get right, measured on my own machine with nothing but Python's hmac and hashlib.

First, integrity. I signed 10,000 requests with HMAC-SHA256 over a shared secret, then tampered the payload on each one without re-signing. How many slipped past verification?

    tampered requests that verified:   0 / 10,000

Zero. Change one byte and the recomputed tag is completely different, so the old signature no longer matches. Without the secret, an attacker cannot produce a tag for the new bytes. The signature is a seal on the exact payload.

Then the thing that surprised me. I captured ONE valid, correctly signed transfer and sent it again 50 times.

    naive server (signature only):     50 / 50 executed, account drained by 250,000
    hardened server (+ timestamp, nonce): 1 / 50 executed

A valid signature says the bytes are genuine. It does not say they are new. A replayed transfer verifies perfectly, because nothing about it changed, and for a non-idempotent action that is a double charge 50 times over. The fix is a timestamp window plus a one-time nonce, which is the idempotency key from Day 25 moved down to the transport layer.

Last, the one that ships to production constantly. A real, logged-in user asks for accounts they do not own:

    authn-only server:  leaked 100% of other users' accounts
    + ownership check:  leaked 0%, still served all 100 of the caller's own

That is an IDOR, also called a BOLA, and it is the number one item on the OWASP API Security list. The user is genuinely authenticated. The server just never asked whether the account was theirs. Authentication answers who you are. Authorization answers what you are allowed to touch. They are different checks, and the second one is a single if-statement that everybody forgets.

A valid token is not permission. That is the whole day.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #security #learninginpublic

## X thread

**1/**

I captured ONE valid, signed money transfer today and sent it again 50 times.

naive server (signature only):   50 transfers went through
+ timestamp and nonce:            1 went through

Day 47 of 60 days of system design. A valid signature is not the whole story.

**2/**

Start with integrity. Sign a request with HMAC-SHA256 over a shared secret, then tamper the body without the secret.

10,000 tampered requests. 0 verified.

One changed byte means a totally different tag, so the stale signature no longer matches. The signature seals the bytes.

**3/**

But here is the catch. A REPLAYED request is byte-for-byte identical to the original, so the signature verifies every single time.

For a transfer, that is a double charge, 50 times over. The signature says "genuine", not "new".

**4/**

Fix: put a timestamp and a one-time nonce inside the signed data.

Timestamp bounds how long a request is usable. The nonce is accepted once and then remembered, so every replay is rejected.

That nonce is just an idempotency key (Day 25) at the transport layer.

**5/**

Then the big one. A real, logged-in user asks for accounts they do not own.

authn-only server:  leaked 100% of other people's accounts
+ ownership check:  leaked 0%

The user was authenticated. The server just never checked ownership.

**6/**

That is an IDOR / BOLA, the #1 item on the OWASP API Security list.

HTTPS, a valid JWT, rate limiting: none of them stop it. It is a missing if-statement.

**7/**

Authentication = who are you.
Authorization = are you allowed to do THIS.

Two different checks. The second one is the one nobody writes until it is a CVE.

A valid token is not permission.

Code: github.com/anurag629/system-design-60-days
