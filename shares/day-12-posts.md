---
title: "Day 12 posts"
parent: "Day 12: replication and lag"
grand_parent: "Week 2: storage"
nav_order: 3
---

# Day 12 posts: LinkedIn and X

The 100% to 0% stale-read number and the async vs sync write-latency gap both make good screenshots. Swap in your own numbers and voice.

## LinkedIn

Day 12 of 60 days of system design. Today I built the bug everyone has hit and nobody could name: you post a comment, refresh, and it is gone for a second.

The cause is replication. One database takes all the writes (the leader). Copies of it serve reads (the followers). The follower does not get a write the instant the leader takes it. There is a small delay, called replication lag. For that window the follower still has the old data.

So I simulated it in plain Python: a leader, one follower, and 40 ms of lag between them. Then I wrote a value and read it straight back from the follower, 300 times.

    stale reads: 300 of 300 = 100%

Every single read came back with the old value. Of course it did. The read reached the follower before the follower had the write. That is "you refresh and your comment is missing," reproduced on a laptop.

Then the two fixes:

    read your own writes (send recent reads to the leader):  0% stale
    wait for the follower to catch up, then read it:         0% stale

The lag did not go away. I just stopped reading from a replica that was not caught up yet.

The part people skip: why not make writes wait for the follower every time, so reads are never stale? You can. It is called synchronous replication. In my run a synchronous write took about 44 ms versus microseconds for async, because now the write pays the full replication delay. Worse, if the follower is down, the write just stalls. Async is fast but eventually consistent and can lose a few writes on failover. That is the whole tradeoff, and there is no free side.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #databases #learninginpublic

## X thread

**1/**

You post a comment, refresh, and it is gone for a second. Then it comes back.

That is not a bug in the app. It is database replication lag, and today I reproduced it in ~150 lines of Python.

Day 12 of 60 days of system design.

**2/**

The setup: one database takes all writes (the leader). Copies serve reads (followers). A follower gets each write a little late. That delay is replication lag.

I built a leader, one follower, and 40 ms of lag between them.

**3/**

Then I wrote a value and read it straight back from the follower. 300 times.

    stale reads: 300 of 300 = 100%

Every read showed the OLD value, because the read hit the follower before the follower had the write. Your missing comment, on a laptop.

**4/**

Two fixes, both drop it to 0%:

read your own writes: send recent reads to the leader, not a follower
wait for catch-up: hold the read until the follower has your write

The lag stays. You just stop reading from a replica that is behind.

**5/**

"So make writes wait for the follower, then reads are never stale." That is synchronous replication.

My run: sync write ~44 ms, async write ~microseconds. And if the follower is down, the sync write stalls.

**6/**

The tradeoff, no free side:

async: fast writes, stale reads, can lose writes on failover
sync: no stale reads, slow writes, one down follower stalls everything

Pick per read. Your own data: read the leader. A stranger's old posts: a stale follower is fine.

Code: github.com/anurag629/system-design-60-days
