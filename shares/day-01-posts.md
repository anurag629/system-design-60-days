---
title: "Day 1 posts"
parent: "Day 1: how slow is slow?"
grand_parent: "Week 1: ground truth"
nav_order: 3
---

# Day 1 posts: LinkedIn and X

These are the author's own Day 1 posts, written with the reference machine's numbers. Use them for shape, then write yours with your numbers and your surprise. Attach a screenshot of your terminal output. The ratios block at the bottom of the script output is the most shareable thing you produce today.

## LinkedIn

I started 60 days of system design today. Four hours a day. Day 1 was supposed to
be the easy one: learn the latency numbers.

Instead I found out my laptop's network is faster than its disk.

    SSD random 4 KB read     84.7 µs
    localhost TCP round trip 19.5 µs

That's a full TCP round trip, through the kernel, with two context switches. It
beats a single read off an NVMe drive by more than four times.

Everyone teaches the hierarchy as RAM, then disk, then network, each about 100x
slower than the last. That's not what my machine does. The "network is slow"
intuition is really "distance is slow." Loopback has no distance. What's left is
just CPU work.

Meanwhile the SSD was being read one 4 KB block at a time with the OS cache
disabled, which is the worst possible way to use an NVMe drive. NVMe earns its
throughput from having dozens of requests in flight. I gave it one.

The other thing I measured, the one I'll actually carry:

    One round trip to São Paulo = 2,360,722 reads from my RAM.

In the time it takes to ask a server in Brazil a single question, this laptop
could read a value out of memory 2.36 million times. Every cache, every CDN, and
every read replica ever built exists because of that number.

Three bugs I hit, all of which returned confident wrong answers rather than
crashing:

1. I tried to measure the round trip to MIT and to the University of Melbourne.
   Melbourne answered in 41 ms. It's on the other side of the planet. Light in
   fiber can't do that trip in under ~104 ms. Both sites sit behind CDNs, so I
   was timing the distance to a cache down the road, not to a campus.

2. My connect timer was silently including a DNS lookup on every single call.
   Two different things, added together, reported as one.

3. My disk benchmark measured RAM for a while and told me my SSD did 4 KB reads
   in 1.8 µs. The file had just been written, so it was still sitting in the OS
   page cache. Real answer after fixing it: 84.7 µs. A 46x error. The sanity
   check I'd written was set at 1 µs, just below the failure it was meant to
   catch, so it stayed silent and made the wrong number look verified.

Benchmarks don't fail loudly. They hand you a number you're happy with.

Day 1 of 60. Code and notes are public, mistakes included:
github.com/anurag629/system-design-60-days

#systemdesign #softwareengineering #learninginpublic

## X thread

Five posts. Every one has a number in it. No thread emoji, no "let that sink in." Attach the terminal screenshot to post 3.

**1/**

My laptop's network is faster than its disk.

    SSD random 4KB read      84.7 µs
    localhost TCP round trip 19.5 µs

I did not expect that. Day 1 of 60 days of system design, and the first thing I
measured broke the mental model I was given that morning.


**2/**

The textbook hierarchy is RAM → disk → network, each ~100x slower than the last.

But "network is slow" actually means "distance is slow." Loopback has no
distance. Strip out the distance and a TCP round trip is just CPU work, and CPU
work is cheap.


**3/**

The number I'll actually remember, measured from my own machine:

    1 round trip to São Paulo = 2,360,722 reads from my RAM
    1 round trip to Virginia  = 1,669,751
    1 round trip to Mumbai    =   306,069
    1 read from my SSD        =       478

Every CDN that has ever existed is justified by row one.


**4/**

Nobody beats the speed of light, and almost nobody gets close.

Light in fiber does ~200,000 km/s, so a round trip can't beat distance/100 in ms.

    Sydney:     104 ms floor,  measured 199 ms  (1.9x)
    Mumbai:      12 ms floor,  measured  54 ms  (4.7x)

Fiber follows railways, not great circles. Every router stops the packet.


**5/**

My disk benchmark reported 1.8 µs per read for a while. That's RAM, not an SSD.
The file had just been written and was still in the OS page cache.

Real answer: 84.7 µs. A 46x error, no crash, no warning.

Benchmarks don't fail loudly. They hand you a number you like.

github.com/anurag629/system-design-60-days
