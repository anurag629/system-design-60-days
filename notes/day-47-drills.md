---
title: "Day 47 drills"
parent: "Day 47: security boundaries"
grand_parent: "Week 7: production"
nav_order: 2
---

# Day 47 drills

Written on paper first. Signing, replay, authentication, authorization, and the IDOR.

D1 (a request is signed with HMAC-SHA256 over method, path, timestamp, nonce and body. An attacker on the network changes the body but cannot change the signature. What happens at the server, and what part of the request is NOT protected if you forget to put it in the signed string?):

D2 (a valid, signed, non-idempotent transfer is captured and replayed. Explain why the signature still verifies. Then explain how a timestamp window and a nonce each stop the replay, and which one does what. Tie the nonce back to the idempotency key from Day 25):

D3 (define authentication and authorization in one line each. For a request GET /accounts/8821 from a logged-in user, say which check answers "is this a real user" and which answers "is 8821 theirs", and what goes wrong if you do only the first):

D4 (an IDOR, also called a BOLA. Describe the classic version with sequential ids in a URL, why it is the top item on the OWASP API Security list, and why rate limiting, HTTPS and a valid JWT do nothing to stop it):

D5 (where should the ownership check live: in the client, in an API gateway, or in the service that owns the data, and why? And why is "the id is a random UUID so nobody can guess it" not an access control?):
