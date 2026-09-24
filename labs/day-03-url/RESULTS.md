---
title: "Day 3 lab results"
parent: "Day 3: what happens when you type a URL"
grand_parent: "Week 1: ground truth"
nav_order: 1
---

# Day 3 results: one HTTPS request, taken apart

Measured 2026-09-24. Apple Silicon laptop, macOS, Python 3, `anatomy.py`. VPN off: yes / no.

## The table

Paste the "taken apart" table, the round trips section and the scoreboard here.

```
```

## Round trip accounting, Virginia

| Phase | ms | Round trips | What it was for |
|---|---|---|---|
| DNS (first) | | | |
| TCP | | 1 | |
| TLS | | | |
| HTTP first byte | | | |
| Reused request | | | |

TLS version I got:

## curl cross-check

Paste curl's line. Which phase, if any, did curl and Python disagree on?

## The TTL

`dig` said the TTL is ___ seconds. After a few seconds it said ___.

## My answer to "what happens when you type a URL"

One paragraph, with my own numbers in it.

## Stretch

Round trips before first byte, without TCP_NODELAY: ___. With it: ___.
Why, in my own words:

## Can't explain yet
