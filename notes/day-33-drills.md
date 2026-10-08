---
title: "Day 33 drills"
parent: "Day 33: logical clocks"
grand_parent: "Week 5: distributed systems"
nav_order: 2
---

# Day 33 drills

Drawn on paper first. Little message diagrams, Lamport counters, vector clocks, and the concurrency a wall clock misses.

D1 (state the one-way guarantee of Lamport timestamps precisely, then give a two-process example where Lamport(a) < Lamport(b) yet a and b are concurrent, and say why Lamport can never rule this out):

D2 (two processes P and Q. P: p1 internal, p2 send m1 to Q, p3 receive m2 from Q. Q: q1 internal, q2 receive m1, q3 send m2. Compute every event's Lamport timestamp, showing the max-plus-one at each receive):

D3 (same scenario as D2. Compute every event's vector clock as [P, Q], then classify p2 vs q1 and p2 vs q2 as ordered or concurrent, and say how the vectors tell you):

D4 (a cluster of N nodes, each carrying a vector clock: how many integers is each clock, what happens to the cost as N grows into the thousands, and one real technique a production system uses to keep them small):

D5 (two clients both read the cart version with clock [1,0,0] and each add one item without seeing the other: write the two resulting vector clocks, show they are concurrent, then say what a Dynamo-style store does versus what last-write-wins on wall-clock timestamps does, and which loses data):
