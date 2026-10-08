---
title: "Day 47 lab results"
parent: "Day 47: security boundaries"
grand_parent: "Week 7: production"
nav_order: 1
---

# Day 47 results: integrity, replay, and the authorization gap

Measured on: (machine, OS, Python version)

## Output

Paste part 1, part 2, part 3 and the scoreboard here.

```
```

## One sentence per prediction

- P1 (tampered requests that still verified):
- P2 (naive server, replays executed):
- P3 (hardened server, replays executed):
- P4 (authn-only leak percent):

## Integrity, in my own words

What did the HMAC actually protect, and why could the attacker not forge a tag for the changed bytes:

## Replay

The signature was valid on every copy of the captured request. Why, and what did the timestamp plus nonce add that the signature alone could not:

## Authentication vs authorization

The caller was a genuine logged-in user on every request. So what exactly was the hole, and what was the one check that closed it:

## The number that matters

Tampered requests through: ___ . Replays on naive vs hardened: ___ vs ___ . Authn-only leak: ___% , dropping to ___% once ownership was checked. Say in one line why a valid token is not permission:

## Can't explain yet
