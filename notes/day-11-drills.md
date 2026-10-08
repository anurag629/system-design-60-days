---
title: "Day 11 drills"
parent: "Day 11: transactions and isolation"
grand_parent: "Week 2: storage"
nav_order: 2
---

# Day 11 drills

Paper first. The lost update, the four anomalies, and the isolation ladder.

D1 (two sessions both read balance 100, both add 10, both write back: final balance, correct balance, how much lost, and the one sentence why):

D2 (name the anomaly for each: read a row twice in one transaction and get two values; read data that later rolls back; same WHERE returns new rows the second time; two read-modify-writes clobber each other):

D3 (which of dirty read, non-repeatable read, phantom, lost update can still happen under READ COMMITTED? which under SERIALIZABLE?):

D4 (deduct 100 from a balance: `UPDATE accounts SET balance = balance - 100 WHERE id = 1` vs read-the-balance-then-update-in-code. which is safe under load and why? when do you still need an explicit BEGIN...COMMIT?):

D5 (serializable is safest: name two costs you pay for it, and one mechanism a database uses to provide it. tie it to the slowdown you measured in the lab):
