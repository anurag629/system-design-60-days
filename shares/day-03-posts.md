---
title: "Day 3 posts"
parent: "Day 3: what happens when you type a URL"
grand_parent: "Week 1: ground truth"
nav_order: 3
---

# Day 3 posts: LinkedIn and X

Written with the reference run's numbers. That run went through a VPN, so its milliseconds are inflated; the round trip counts don't depend on distance, and they're the heart of the post. Swap in your own numbers. Attach the "counted in round trips" section of the output as a screenshot.

## LinkedIn

Day 3 of 60 days of system design, and the classic interview question: what happens when you type a URL?

Everyone answers with a list. DNS, TCP, TLS, HTTP. I timed each step of one HTTPS request to an AWS server in Virginia instead.

    DNS lookup           [your first lookup] ms (then ~1 ms, cached)
    TCP handshake        274 ms
    TLS 1.3 handshake    286 ms
    first byte           552 ms

The TCP handshake is almost exactly one round trip, so I used it as a ruler. Counted in round trips:

    TCP 1  +  TLS 1  +  HTTP 2  =  4 round trips before the first byte

Only one of those round trips carried what I actually asked for. The rest were setup.

Then I sent a second request on the same, already open connection. 280 ms. One round trip. Connection reuse made the request about 4x faster without a single line of server code changing. That's why browsers keep connections open and why HTTP/2 puts many requests down one connection.

But the textbook says HTTP should be 1 round trip, not 2. Where did the extra one come from?

Nagle's algorithm, from 1984. It holds back a small packet while an earlier one is still unacknowledged. My HTTP request sat waiting for the server to acknowledge the end of the TLS handshake, a full round trip. One line, setting TCP_NODELAY, and the count dropped from 4 to 3. curl and browsers set it by default. Python's plain sockets don't.

A reasonable default from before HTTPS existed, quietly costing a whole round trip. No profiler of my own code would ever have shown it.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #networking #learninginpublic

## X thread

**1/**

"What happens when you type a URL?" Everyone recites DNS, TCP, TLS, HTTP.

I timed each step of an HTTPS request to Virginia instead. Counted in round trips:

TCP 1 + TLS 1 + HTTP 2 = 4 before the first byte.

Only one of the four carried what I asked for.

**2/**

The same request again on the already open connection: 280 ms, one round trip.

Cold request: about 1,100 ms. Reused: 280.

No server change. Just fewer conversations. That's the entire case for keep-alive and HTTP/2.

**3/**

DNS: the first lookup took [your number] ms. The repeat took about 1 ms, because the OS cached it.

`dig` showed a TTL of 60 seconds on AWS's record. Short TTL means AWS can move traffic in a minute, at the cost of everyone asking again every minute.

**4/**

The mystery: HTTP should be 1 round trip, not 2.

Culprit: Nagle's algorithm (1984). It held my small request until the server acknowledged the end of the TLS handshake. A full round trip, wasted.

Set TCP_NODELAY and it went from 4 round trips to 3.

**5/**

curl and browsers turn Nagle off by default, which is why curl never showed the extra trip. Python's plain sockets don't.

Two tools, same request, one round trip apart, and neither one tells you why.

Day 3 of 60: github.com/anurag629/system-design-60-days
