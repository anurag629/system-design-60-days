# Day 1 — Twitter/X thread

Five tweets. Every one has a number in it. No 🧵 emoji, no "let that sink in."
Attach the terminal screenshot to tweet 3.

---

**1/**

My laptop's network is faster than its disk.

    SSD random 4KB read      84.7 µs
    localhost TCP round trip 19.5 µs

I did not expect that. Day 1 of 60 days of system design, and the first thing I
measured broke the mental model I was given that morning.

---

**2/**

The textbook hierarchy is RAM → disk → network, each ~100x slower than the last.

But "network is slow" actually means "distance is slow." Loopback has no
distance. Strip out the distance and a TCP round trip is just CPU work, and CPU
work is cheap.

---

**3/**

The number I'll actually remember, measured from my own machine:

    1 round trip to São Paulo = 2,360,722 reads from my RAM
    1 round trip to Virginia  = 1,669,751
    1 round trip to Mumbai    =   306,069
    1 read from my SSD        =       478

Every CDN that has ever existed is justified by row one.

---

**4/**

Nobody beats the speed of light, and almost nobody gets close.

Light in fiber does ~200,000 km/s, so a round trip can't beat distance/100 in ms.

    Sydney:     104 ms floor,  measured 199 ms  (1.9x)
    Mumbai:      12 ms floor,  measured  54 ms  (4.7x)

Fiber follows railways, not great circles. Every router stops the packet.

---

**5/**

My disk benchmark reported 1.8 µs per read for a while. That's RAM, not an SSD.
The file had just been written and was still in the OS page cache.

Real answer: 84.7 µs. A 46x error, no crash, no warning.

Benchmarks don't fail loudly. They hand you a number you like.

github.com/anurag629/system-design-60-days
