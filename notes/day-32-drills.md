---
title: "Day 32 drills"
parent: "Day 32: consensus and Raft"
grand_parent: "Week 5: distributed systems"
nav_order: 2
---

# Day 32 drills

Written on paper first. Terms, majorities, split votes, and the fault-tolerance arithmetic. Use `majority = floor(N/2) + 1` and `failures tolerated = floor((N-1)/2)`. Nothing else is needed.

D1 (a 5-node cluster, the leader dies: trace what one follower does step by step until a new leader exists, and say how many votes the winner must collect and why that number is 3, not 5):

D2 (three followers time out in the same instant and all become candidates for the same term: why can none of them win that term, what does each do next, and what single change to the timeouts makes this almost never repeat):

D3 (work out the majority and the failures tolerated for N = 3, 4, 5, 6, 7: then explain why 4 nodes tolerate the same number of failures as 3, and why odd cluster sizes are the sensible choice):

D4 (a 5-node cluster has 3 nodes down: the surviving 2 keep timing out, bumping the term, and requesting votes forever: why is no leader ever elected, what is the cluster able and unable to do in this state, and what has to happen for it to recover):

D5 (a network partition splits a 5-node cluster into a group of 3 and a group of 2, each side cut off from the other: which side (if any) can elect a leader and keep serving writes, which cannot, and why does this stop the classic split-brain where both sides accept writes):
