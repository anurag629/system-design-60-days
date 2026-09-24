---
title: "Day 3: what happens when you type a URL"
parent: "Week 1: ground truth"
nav_order: 3
has_children: true
---

# Day 3, Thursday 2026-09-24
## What happens when you type a URL, counted in round trips 🌐

Today's one idea: loading a web page is a chain of conversations, and every conversation costs at least one round trip. Once you count the round trips, you can predict how slow a page will be before anyone writes a line of code.

This is the most famous interview question in the business. Most people answer it by reciting steps: DNS, TCP, TLS, HTTP. You're going to time each step on your own laptop, and then you'll answer it with numbers instead.

---

## Before you start ⏪

Day 2 comes first. If your Day 2 predictions, lab and log aren't done yet, finish those before opening this. Day 3 doesn't need anything from Day 2's lab, but it does lean hard on the habit Day 2 builds: write the number down before you measure it.

You need one number from Day 1 today: your round trip to Virginia (`us-east-1`). If you don't have it, the reference run from India measured about 296 ms. Keep it next to you.

---

## Words you will meet today 📖

An IP address is the actual address of a machine on the internet, like `13.200.90.189`. Computers route packets to IP addresses, not to names.

DNS (Domain Name System) is the internet's phone book. It turns a name like `flipkart.com` into an IP address. The program that does the looking up for you is called a resolver, usually run by your ISP, your office, or someone like Google (`8.8.8.8`) or Cloudflare (`1.1.1.1`).

TTL (time to live) is how long a DNS answer may be cached before someone has to ask again. It's set by whoever owns the name, in seconds.

A packet is one small chunk of data sent across the network, usually up to about 1,500 bytes. Everything you send gets chopped into packets.

TCP is the protocol that turns a stream of unreliable packets into a reliable, in-order conversation. Before any data flows, the two sides do a three-way handshake. The client sends SYN ("I want to talk, my numbers start here"), the server replies SYN-ACK ("fine, mine start here"), and the client sends ACK ("got it"). That costs one round trip before you can send anything useful.

TLS is the encryption layer on top of TCP, the S in HTTPS. Its handshake agrees on keys and proves the server is who it claims to be, using a certificate: a document signed by a trusted authority that says "this key belongs to `flipkart.com`." TLS 1.3 needs one round trip for this. The older TLS 1.2 needs two.

HTTP is the actual request and response: "GET me this page," "here it is." One round trip, plus however long the server takes to think.

TTFB (time to first byte) is how long you wait between sending a request and receiving the first byte of the answer. It's the number that tells you whether the network or the server is slow.

Keep-alive, or connection reuse, means leaving a connection open after one request so the next request can skip DNS, TCP and TLS entirely. Keep this one in mind. It's the hero of today's lab.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [How DNS works](https://howdns.works/), a comic in eight short episodes. It's the gentlest possible introduction, and it covers the whole lookup chain from your laptop to the root servers. About 15 minutes.
- [High Performance Browser Networking, the three-way handshake](https://hpbn.co/building-blocks-of-tcp/#three-way-handshake) and then [the TLS handshake](https://hpbn.co/transport-layer-security-tls/#tls-handshake) by Ilya Grigorik. Read only those two sections today. This is the book that taught a generation of engineers to count round trips, and it's free.
- [What happens when...](https://github.com/alex/what-happens-when), the famous GitHub answer to the interview question. It's long and goes deep into keyboard interrupts. Skim it, and read the DNS, TCP, TLS and HTTP parts properly.

Watch these two:
- [What happens when you type a URL into your browser?](https://www.youtube.com/watch?v=AlkDbnbv7dk) by ByteByteGo, 5 minutes. Watch this one before the lab, as the map for the day.
- [Wiresharking TLS, TLS 1.2 and 1.3 handshakes](https://www.youtube.com/watch?v=06Kq50P01sI) by Hussein Nasser, 17 minutes. Watch this after the lab, especially if you try the `tcpdump` bonus. He shows the same packets you'll see, one by one.

### The story, one request at a time (20 min)

You type `https://www.flipkart.com` and press Enter. Here's what happens, told as a list of round trips.

Step 1 is DNS. Your laptop needs an IP address. It checks its own cache first. If the answer is there and the TTL hasn't run out, this step costs almost nothing. If not, it asks your resolver. If the resolver has it cached, that's one round trip to the resolver, usually close by. If the resolver doesn't have it either, the resolver asks a root server, then the `.com` servers, then Flipkart's own DNS servers, before it can answer you. That's several round trips, but they happen from the resolver, not from you, and they happen rarely, because everyone caches.

Step 2 is TCP. Your laptop sends SYN to that IP and waits for SYN-ACK. That's one full round trip before a single byte of your actual request can leave. For a user in Chennai hitting a server in Virginia, that's a quarter of a second spent saying hello.

Step 3 is TLS. Your laptop and the server agree on encryption keys, and the server sends its certificate for your laptop to check. With TLS 1.3 that's one more round trip. With TLS 1.2, two.

Step 4 is HTTP. Now, finally, your laptop sends `GET /`. The server thinks, then answers. One more round trip, plus server time.

Add it up for a brand new HTTPS connection with DNS already cached: TCP 1 + TLS 1 + HTTP 1 = 3 round trips before you see the first byte. At 250 ms per round trip, that's 750 ms, and the server hasn't even done anything clever yet. Only one of those three round trips carried the thing you actually wanted.

Now the good news. Once the connection is open, the next request on it skips steps 1 to 3. It costs one round trip. That's why your browser holds connections open, and why HTTP/2 sends dozens of requests down one connection at the same time instead of opening dozens of connections.

And the part that turns this into system design: the round trip length is set by distance, and you can't make light go faster. So the fixes are all about removing round trips (connection reuse, HTTP/2, TLS 1.3, HTTP/3) or shortening them (put a server near the user). A CDN is the second fix: copies of the page sit on machines in Indian cities, not in the US, and a 250 ms round trip becomes a 10 ms one. Big Billion Days would be unusable without it.

### The DNS caching layers (10 min)

DNS answers are cached in layers, and each layer respects the TTL:

| Where | Typical cost if the answer is cached here |
|---|---|
| Your browser | almost nothing |
| Your operating system | well under a millisecond |
| Your home router | one hop on your LAN, a few ms |
| Your ISP's or public resolver | one round trip, usually 5 to 30 ms |
| Nobody has it | several round trips, can be 100+ ms |

Here's the catch with caching. When a company changes its IP address, the old answer lives on in all those caches until the TTL runs out. Set a TTL of one day and some users will keep hitting your old server for a day. Set a TTL of 60 seconds and you can move traffic in about a minute, but every resolver has to ask you again every minute. Speed versus control. That's a trade you'll see again in week 3, with every cache ever built.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-03-drills.md`](../notes/day-03-drills.md).

For all of these, assume DNS is already cached unless a question says otherwise, and ignore server think time.

D1. A user in Mumbai, a server in Virginia, and a 250 ms round trip. A brand new HTTPS connection with TLS 1.3. How long until the first byte of the response arrives?

D2. The same request with TLS 1.2. Then with HTTP/3, which runs over QUIC, a protocol that does the transport handshake and the encryption handshake together in one round trip. How long for each?

D3. A page needs 1 HTML file plus 30 images and scripts, all from the same server as D1 (250 ms round trip, TLS 1.3). How long does the page take to load in each of these setups?
- (a) HTTP/1.1 with no keep-alive: every file gets a brand new connection, one after another.
- (b) HTTP/1.1 with keep-alive: one connection, files fetched one after another.
- (c) HTTP/2: one connection. Fetch the HTML first, then all 30 files at the same time.
- (d) Same as (c), but served from a CDN in Mumbai with a 10 ms round trip.

D4. IRCTC is moving its booking servers to a new IP address. The DNS record has a TTL of 3,600 seconds. They change it at 10:00. What's the earliest they can switch off the old servers? What should they have done the day before? And tonight's lab will show you that AWS gives its endpoints a TTL of just 60 seconds. Why might AWS choose such a short one, and what does that cost them?

D5. Tatkal opens at 10:00:00 and one million people hit refresh in the same second, each opening a brand new HTTPS connection. Assume each TLS handshake costs the server 1 ms of CPU time. That's roughly right for older RSA certificates; modern ECDSA certificates are several times cheaper. How many CPU cores are busy doing nothing but handshakes during that first second? What would change if those users' browsers still had connections open from 9:59?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-03-url/anatomy.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-03-url/anatomy.py).

It sends real HTTPS requests to the same three AWS endpoints as Day 1 (Mumbai, Virginia, São Paulo) and times DNS, TCP, TLS and TTFB separately. Then it sends a second request on the same open connection. Then it counts everything in round trips, using your measured TCP connect time as the length of one round trip.

Standard library only. It takes about a minute to run, mostly waiting on São Paulo.

### Predict first

Fill in `PREDICTIONS` at the top of the file. Use the story above and your Day 1 Virginia number (or 296 ms, the reference run's).

- Q1. How many round trips happen before the first byte of a brand new HTTPS request, not counting DNS?
- Q2. How many milliseconds does a brand new request to Virginia take, from starting the DNS lookup to the first byte?
- Q3. How many milliseconds does a second request to Virginia take on the connection that's already open?
- Q4. How many milliseconds does a DNS lookup take for a name you looked up one second ago?

### Fill in the TODOs

1. TODO 1 times the DNS lookup with `socket.getaddrinfo`.
2. TODO 2 times the TCP handshake with `socket.create_connection`. Pass it the IP address, not the host name. If you pass the name, it quietly does a second DNS lookup inside your TCP timing, which was exactly the Day 1 bug.
3. TODO 3 times the TLS handshake with `CTX.wrap_socket`.
4. TODO 4 sends the request and times the wait for the first byte of the answer.

Each TODO is three or four lines, and the comment above it shows you the shape. Type them out yourself. Leave the STRETCH spot empty for now.

```bash
cd labs/day-03-url
python3 anatomy.py
```

### Cross-check with curl and dig

Your Python numbers are one opinion. Get a second one from `curl`, which has timing built in:

```bash
curl -so /dev/null -w "dns %{time_namelookup}  connect %{time_connect}  tls %{time_appconnect}  first-byte %{time_starttransfer}\n" https://ec2.us-east-1.amazonaws.com/
```

curl's numbers are cumulative, measured from the start, not per phase. So `connect` includes DNS, and `tls` includes DNS and connect. Subtract to get each phase on its own, then compare with your table. Keep an eye out for any phase where curl and Python disagree. It will matter in the stretch below.

Then look at the DNS record itself:

```bash
dig ec2.us-east-1.amazonaws.com
```

Find the ANSWER SECTION. The number between the name and `IN` is the TTL in seconds. Run it twice, a few seconds apart, and watch the TTL count down. That's a cache telling you how long it will keep the answer.

### What you're going to discover

I'll spoil the shape, not the numbers.

The cold request will cost several times the reused one, and the reused one will cost almost exactly one round trip. Nothing about the server changed between them. Only the number of conversations did.

The first DNS lookup will be slow and the repeats will be close to free. If even your first lookup is fast, the OS already had it cached from a previous run or from curl. See the traps.

And the round-trips section of the output might not match theory exactly. If it doesn't, don't fix it yet. Write down what you see, then do the stretch.

### Traps ⚠️

- Turn off any VPN or office proxy. They send every packet through some faraway box first, and the "Mumbai" row stops meaning Mumbai. A quick check: Mumbai should be clearly the fastest of the three rows, as it was on Day 1. If it isn't, something is in the way.
- To see a truly cold DNS lookup on a Mac, flush the OS cache first: `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`. Your router and resolver may still have the answer cached, so "cold" is always relative.
- The script keeps the median of five cold requests for each phase. One unlucky sample on a noisy Wi-Fi network would otherwise wreck your table. Day 1 taught you why a single measurement is a rumour.
- Don't run it while something big is downloading. You'd be measuring your own queue, and queues are Day 4's topic, not today's.

### Stretch: the round trip that shouldn't be there 🕵️

Do this only after your first full run and your first pass at RESULTS.md.

<details markdown="1">
<summary>Open when you're ready</summary>

Look at the "Counted in round trips" section. Theory says HTTP should cost 1 round trip on the cold request. What did yours say? Now compare it with the reused request, which costs one round trip, and with curl's first-byte number.

If the cold HTTP step on your machine costs about 2 round trips while the reused request costs 1, you've found a real production gotcha, one that nearly every HTTP library has had to work around. Before reading on, spend 10 minutes trying to explain it yourself. Hint: the extra wait happens right after the TLS handshake finishes, and it involves your laptop deciding to hold back a small packet.

Then put this line in the STRETCH spot in the lab, and run again:

```python
raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
```

Watch what happens to the round trip count. Then look up two terms: Nagle's algorithm and delayed ACK. The explanation is at the bottom of this page, under the drill answers, if you get stuck.

</details>

### Bonus: watch the handshake with tcpdump (optional, needs sudo)

`tcpdump` prints every packet your machine sends and receives. In one terminal, find the IP with `dig +short ec2.us-east-1.amazonaws.com`, then run:

```bash
sudo tcpdump -i en0 -n host <that-ip> and port 443
```

In a second terminal, run the curl command from above. You'll see the handshake as flags in square brackets: `[S]` is SYN, `[S.]` is SYN-ACK, `[.]` is ACK. Look at the timestamps between them. The gap between `[S]` and `[S.]` is your round trip, measured by the kernel itself. Press Ctrl-C to stop. If `en0` shows nothing, you're on a different interface; `ifconfig` will show you which one has your IP.

### Deliverable

[`labs/day-03-url/RESULTS.md`](../labs/day-03-url/RESULTS.md) has a skeleton waiting. Paste the tables and the scoreboard, fill in the round trip accounting, and write your one-paragraph answer to the interview question, using your own numbers.

---

## Block 4: write (30 min) 📣

Your angle today: everyone can recite what happens when you type a URL. You timed it.

The shape: "I timed every step of one HTTPS request from India. DNS took X, TCP took Y, TLS took Z. Only one of the round trips carried the thing I wanted. Reusing the connection made the same request N times faster." If you did the stretch, that's an even better post. "There was a round trip in my request that shouldn't have been there. Here's the 1984 algorithm that put it there."

Example posts, written with the reference run's numbers, are on the [Day 3 posts](../shares/day-03-posts.md) page. Swap in your numbers and your words. Lead with the number that surprised you, and attach the round trip table as a screenshot. Drafts go in `shares/`.

---

## End of day: log it 📝

Add a Day 3 entry to your progress log with three things:

1. What you completed, and what you skipped.
2. Your cold vs reused request to Virginia, in ms, and how many round trips your machine counted before the first byte.
3. One thing you still can't explain. If the stretch left you confused, that's a perfectly good answer.

Then compare your work with the Solutions below. Day 4 is latency vs throughput, and the queue: why a system at 90% busy feels fine and at 99% falls over.

---

## Solutions 🔑

Open these only after you've done the day. Reading answers first feels like learning and isn't.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. TCP 1 + TLS 1.3 1 + HTTP 1 = 3 round trips × 250 ms = 750 ms.

D2. TLS 1.2: TCP 1 + TLS 2 + HTTP 1 = 4 round trips = 1,000 ms. HTTP/3 over QUIC: handshake 1 + HTTP 1 = 2 round trips = 500 ms. Same server, same distance, and the protocol alone halves the wait compared with TLS 1.2. On a repeat visit, QUIC and TLS 1.3 can even send the request with the very first packet (called 0-RTT), though that comes with a security catch for requests that change data.

D3. A new connection costs 2 round trips (TCP + TLS), then each request costs 1.
- (a) No keep-alive: 31 files × 3 round trips = 93 round trips = 23.25 s. Unusable, and this is exactly how the early web behaved.
- (b) Keep-alive: 2 + 31 = 33 round trips = 8.25 s. Better, but still painful, because the files queue behind each other.
- (c) HTTP/2: 2 (setup) + 1 (HTML) + 1 (all 30 at once) = 4 round trips = 1.0 s.
- (d) CDN with HTTP/2: 4 × 10 ms = 40 ms.

Same page, same files. The range runs from 23 seconds to 40 milliseconds, a factor of almost 600, and not one byte of content changed. That's the whole argument for connection reuse, multiplexing and CDNs in one question. In real life bandwidth and browser limits blur this a bit, but the order of magnitude is right, and it's what you'd say in an interview.

D4. The earliest is 11:00, when the last cached copy of the old answer should expire. In practice, wait longer, because some resolvers and apps ignore TTLs and hold answers for hours. The day before, they should have lowered the TTL to 60 seconds, waited for the old 3,600-second answers to expire, then made the change. After that, raise it again.

AWS uses 60 seconds so it can pull a failing machine or a whole data center out of rotation within about a minute. The cost is more DNS queries: every resolver in the world asks again every minute instead of every hour. For AWS, being able to steer traffic fast is worth far more than the query load.

D5. 1,000,000 handshakes × 1 ms = 1,000 CPU-seconds of work, all landing in one second. That's 1,000 CPU cores busy doing nothing but handshakes, before a single ticket gets booked. If the browsers already had connections open from 9:59, the handshakes happened a minute earlier and spread out, and at 10:00 each request is just one HTTP round trip. This is why big sites terminate TLS at a fleet of load balancers, prefer cheaper ECDSA certificates, and use session resumption so returning clients skip most of the handshake. It's also one reason tatkal traffic looks the way it does. We'll come back to that crowd on Day 4, and properly in week 3 when we meet the thundering herd.

</details>

<details markdown="1">
<summary>Stretch explanation: the extra round trip</summary>

The culprit is Nagle's algorithm, from 1984. It says: if I've sent a small packet that hasn't been acknowledged yet, hold the next small packet until the ACK comes back, so I can bundle them together. It was built to stop remote terminals from sending one keystroke per packet, and it's on by default for every TCP socket, including Python's.

At the end of the TLS 1.3 handshake, your laptop sends a small "Finished" message. Straight after, your code sends the small HTTP request. Nagle sees that Finished hasn't been acknowledged yet, so it holds the request back. The request only leaves when the server's acknowledgement for Finished arrives, a full round trip later. So HTTP costs you 2 round trips instead of 1. The reused request doesn't suffer, because by then nothing is waiting to be acknowledged.

Its famous partner in crime is delayed ACK, where the receiver waits up to a few hundred milliseconds before acknowledging, hoping to piggyback the ACK on a reply. When a server does that, the same bug costs you a round trip plus that delay. Here the AWS server replies straight away (it sends a session ticket that carries the ACK), so you only lose the one round trip.

`TCP_NODELAY` turns Nagle off for that socket. curl, browsers, and most HTTP libraries set it by default for exactly this reason, which is why curl didn't show the extra trip. The general lesson is bigger than this one flag: a reasonable default, written decades before HTTPS existed, can quietly cost you a whole round trip. On a 250 ms link, that's a 33% slower first request, and no profiler of your own code will ever show it.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-03-url/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-03-url/solution.py). It includes the stretch line, commented out.

TODO 1, DNS:

```python
start = time.perf_counter()
ip = socket.getaddrinfo(host, PORT, socket.AF_INET,
                        socket.SOCK_STREAM)[0][4][0]
t["dns"] = time.perf_counter() - start
```

TODO 2, the TCP handshake, connecting to the IP so no second DNS lookup sneaks in:

```python
start = time.perf_counter()
raw = socket.create_connection((ip, PORT), timeout=TIMEOUT)
t["tcp"] = time.perf_counter() - start
```

TODO 3, the TLS handshake:

```python
start = time.perf_counter()
conn = CTX.wrap_socket(raw, server_hostname=host)
t["tls"] = time.perf_counter() - start
```

TODO 4, send the request and wait for the first byte:

```python
start = time.perf_counter()
conn.sendall(request_bytes(host))
first = conn.recv(1)
t["ttfb"] = time.perf_counter() - start
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS. One honest caveat: this run went through a VPN, so every packet made a detour first, and the milliseconds are bigger than a direct connection from India would give. The round trip counts don't depend on distance, and they're the part that matters.

```
                  DNS      TCP      TLS     TTFB      COLD   REUSED   all in ms
  Mumbai          3.3    327.6    339.9    655.4    1326.2    336.5
  Virginia        2.1    274.1    286.4    551.5    1114.1    279.9
  Sao Paulo       1.8    360.2    376.0    724.7    1462.7    370.0

  TLS version negotiated: TLSv1.3.   Server answered: HTTP/1.1 301 Moved Permanently

  Mumbai     TCP 1.0  +  TLS 1.0  +  HTTP 2.0  =  4.0 round trips before the first byte
  Virginia   TCP 1.0  +  TLS 1.0  +  HTTP 2.0  =  4.0 round trips before the first byte
  Sao Paulo  TCP 1.0  +  TLS 1.0  +  HTTP 2.0  =  4.0 round trips before the first byte
```

Q1, round trips before the first byte: theory says 3 (TCP 1, TLS 1.3 1, HTTP 1). The lab measures 4, because of Nagle's algorithm (see the stretch explanation below). With the stretch line added, Virginia measured TCP 1.0 + TLS 1.1 + HTTP 1.0 = 3.1.

Q2, a cold request to Virginia: about 4 round trips plus DNS. With a 296 ms round trip that's around 1,200 ms, 900 ms if you've fixed Nagle. The server's own thinking time is tiny: the reused request (280 ms) is almost exactly one TCP round trip (274 ms), so the server took about 6 ms.

Q3, a reused request: one round trip, 280 ms. 4x faster than the cold one, with nothing changed on the server.

Q4, a repeat DNS lookup: about 1 to 3 ms. The first-ever lookup of a name is typically tens to hundreds of milliseconds, and after that the OS cache answers. This run's DNS column shows cached lookups because the names had been looked up minutes earlier. `dig` showed a TTL of 60 seconds on these records.

The VPN is visible in the data, which is a lesson of its own: Mumbai came out slower than Virginia, although Mumbai is far closer to India. Every packet was going to the VPN server first. If your nearest region isn't your fastest, something is in the path.

</details>
