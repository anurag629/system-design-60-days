---
title: "Day 32 posts"
parent: "Day 32: consensus and Raft"
grand_parent: "Week 5: distributed systems"
nav_order: 3
---

# Day 32 posts: LinkedIn and X

The scoreboard makes a good screenshot: fixed timeouts split the vote about 55 percent of rounds, randomized ones about 2 percent, and a 5-node cluster that survives 2 failures but goes dark on the third. Swap in your own numbers and voice.

## LinkedIn

Day 32 of 60 days of system design. Today was Raft, the algorithm that lets a cluster of machines agree on a single leader even while some of them are crashing. I simulated the election part on my laptop, and two numbers stuck.

First, why the timeouts are random. In Raft, a node that stops hearing from the leader waits a bit, then nominates itself and asks the others to vote. If several nodes wait the exact same time, they all nominate themselves at once, each votes for itself, the votes split, and nobody gets a majority. The term is wasted and everyone tries again. I ran 2,000 cold-start elections both ways:

    fixed (equal) timeouts:      split 55% of rounds
    randomized timeouts:         split  2% of rounds

Same algorithm. The only change is that each node waits a random time inside a window instead of a fixed one, so one node almost always wakes first and locks up a majority before the others stir. That one trick is the difference between an election that stalls and one that settles in a single round.

Second, what a majority actually buys you. A leader needs votes from a majority of the whole cluster, not of whoever happens to be alive. So a 5-node cluster needs 3 votes, always. I killed nodes one at a time:

    2 down, 3 alive:  leader elected every time
    3 down, 2 alive:  no leader, ever

With 2 survivors you can never reach 3 votes, so there is no leader and the cluster stops accepting writes. That is the whole formula: N nodes tolerate floor((N-1)/2) failures. Five tolerates two. It is also why cluster sizes are odd, since a 6th node buys you no extra fault tolerance over 5, it just costs another vote to collect.

The part that clicked: consensus is not some mystical thing. It is "a majority agrees," plus a random timer so everyone does not shout at once.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #distributedsystems #raft #learninginpublic

## X thread

**1/**

Day 32 of 60 days of system design: Raft, how a cluster agrees on a leader while machines are crashing.

I simulated the election on my laptop. Two numbers made it click.

**2/**

Why are the timeouts random? If every node waits the same time to nominate itself, they all nominate at once, each votes for itself, the vote splits, nobody wins. Wasted term. Retry. Repeat.

2,000 elections:

fixed timeouts:   split 55% of rounds
random timeouts:  split  2%

**3/**

Same algorithm. The only change is each node waits a RANDOM time in a window instead of a fixed one.

So one node almost always wakes first and grabs a majority before the others stir. Elections go from stalling to settling in one round. That is the entire fix.

**4/**

Second number: what a majority buys.

A leader needs a majority of the WHOLE cluster, not of whoever is alive. 5 nodes means 3 votes, always.

2 down, 3 alive:  leader elected every time
3 down, 2 alive:  no leader, ever

**5/**

With 2 survivors you can never reach 3 votes. No leader, no writes, cluster unavailable.

The formula: N nodes tolerate floor((N-1)/2) failures. 5 tolerates 2.

It is also why clusters are odd-sized: a 6th node adds a vote to collect but no extra fault tolerance.

**6/**

The thing I will remember: consensus is not mystical.

It is "a majority agrees," plus a random timer so everyone does not shout at the same time.

Log replication (the other half of Raft) rides on the same majority.

Code: github.com/anurag629/system-design-60-days
