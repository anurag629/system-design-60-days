---
title: "Day 29 drills"
parent: "Day 29: failure, time, and the eight fallacies"
grand_parent: "Week 5: distributed systems"
nav_order: 2
---

# Day 29 drills

Paper first, with numbers. Unreliable time, last-write-wins, and the fallacies.

D1 (node A's clock is 120 ms ahead of node B's; a client writes X on node A at true time 1000 ms, then writes Y on node B 40 ms later at true time 1040 ms, last-write-wins by timestamp: what stamp does each write carry, which value survives, which did the user actually intend, and how small must the skew get before Y correctly wins):

D2 (writes to a key arrive on average every 50 ms, two nodes kept within 10 ms by NTP: roughly what fraction of consecutive write pairs could the skew possibly misorder, what happens to that fraction if you tighten NTP to 1 ms, and why can you never drive it to a guaranteed zero on a hot key):

D3 (why can two writes that both land on the SAME node never be misordered by that node's clock skew, no matter how wrong its clock is; and why does that make the bug specifically a multi-leader problem, so a single-leader design sidesteps it):

D4 (list as many of the eight fallacies of distributed computing as you can from memory, then pick two and give a one-sentence example of a bug that assuming each one causes; add "time is global" as the ninth and say what believing it costs):

D5 (you run a multi-leader store losing writes to skew under LWW: for each fix, say its cost and when you would pick it, (a) tighten clocks with NTP or PTP, (b) switch to version vectors and keep siblings, (c) route all writes for a key through one leader; which one actually eliminates the silent loss and which only shrinks it):
