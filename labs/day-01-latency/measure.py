"""
Day 1 lab: measure the storage hierarchy on your own machine.

Run it:      python3 measure.py
Clean up:    rm -f bigfile.bin

Your job is the four blocks marked TODO. Everything else is written for you,
but read it anyway. The helpers at the top are where most of the real lessons
about benchmarking live.

Nothing here needs pip install. Standard library only.
"""

import os
import random
import socket
import statistics
import sys
import threading
import time

# ---------------------------------------------------------------------------
# Helpers. Read these before you write anything.
# ---------------------------------------------------------------------------

WARMUP = 10  # Throw away the first N samples. See below for why.


def percentile(samples, p):
    """The value below which p percent of samples fall.

    p50 is the median: half the samples were faster. p99 means only 1% were
    slower. You read about this in DDIA chapter 1 this morning. Averages hide
    the tail; percentiles show it.
    """
    if not samples:
        return float("nan")
    ordered = sorted(samples)
    idx = min(int(len(ordered) * p / 100), len(ordered) - 1)
    return ordered[idx]


def report(label, samples_ns, unit="ns"):
    """Print p50 and p99 side by side.

    Always look at both. When p99 is many times p50, something is queueing,
    or being interrupted, or crossing a network. That gap is a signal, not noise.
    """
    divisor = {"ns": 1, "us": 1_000, "ms": 1_000_000}[unit]
    p50 = percentile(samples_ns, 50) / divisor
    p99 = percentile(samples_ns, 99) / divisor
    print(f"  {label:<38} p50 = {p50:>10.2f} {unit}   p99 = {p99:>10.2f} {unit}")
    return p50


def timed(fn, iterations, warmup=WARMUP):
    """Run fn() `iterations` times, return a list of per-call nanoseconds.

    time.perf_counter_ns() is a MONOTONIC clock: it never jumps backwards when
    the system clock is adjusted, and it has nanosecond resolution. Never use
    time.time() for benchmarking. It can literally go backwards.

    `warmup` is tunable because it is not free. For a memory read costing 100ns,
    ten warmup iterations cost a microsecond and nobody notices. For a TCP
    connection to Brazil costing 430ms, ten warmup iterations cost 4.3 seconds
    of real time in which nothing whatsoever happens. Pass warmup=2 there.
    """
    samples = []
    for _ in range(warmup):
        fn()  # Warmup. The first calls pay for imports, page faults, JIT-ish
        # caching in the OS, and an unestablished network connection.
        # Timing them would measure startup, not steady state.
    for _ in range(iterations):
        start = time.perf_counter_ns()
        fn()
        samples.append(time.perf_counter_ns() - start)
    return samples


# ---------------------------------------------------------------------------
# 1. RAM: random access into a large in-memory buffer
# ---------------------------------------------------------------------------

def measure_ram():
    """Expect roughly 60-200 ns per access on a modern machine.

    A subtlety, and it matters: a single RAM read takes ~100ns, but ONE Python
    bytecode instruction costs ~30-80ns all by itself. So if we just timed the
    read, we would be reporting mostly Python's overhead.

    The fix is to time an identical loop that does everything EXCEPT the memory
    read, then subtract. What's left is (approximately) the memory access.
    This trick has a name in benchmarking: measuring against a baseline.

    Notice also that we pre-generate the random indices. Calling random.randrange()
    inside the timed loop would measure the random number generator, not RAM.
    """
    SIZE = 200 * 1024 * 1024  # 200 MB, comfortably larger than any CPU cache
    N = 200_000

    print("\n[1] RAM  (random 1-byte reads from a 200 MB buffer)")
    buf = bytearray(os.urandom(1024)) * (SIZE // 1024)
    mv = memoryview(buf)
    indices = [random.randrange(SIZE) for _ in range(N)]

    # Baseline: same loop, same list iteration, no memory read.
    start = time.perf_counter_ns()
    sink = 0
    for i in indices:
        sink += 1
    baseline_ns = (time.perf_counter_ns() - start) / N

    # TODO 1 ------------------------------------------------------------------
    # Write the measured loop. It should look exactly like the baseline above,
    # except that instead of `total += 1` it does `total += mv[i]`.
    #
    #   - time it the same way, with perf_counter_ns() around the whole loop
    #   - divide by N to get nanoseconds per iteration
    #   - store it in a variable called `measured_ns`
    #
    # Then the line below subtracts the baseline and gives you the real number.
    # -------------------------------------------------------------------------
    
    total = 0
    start = time.perf_counter_ns()
    for i in indices:
        total += mv[i]
    measured_ns = (time.perf_counter_ns() - start) / N

    if measured_ns == 0.0:
        print("  (did you fill in TODO 1?)")
        return None

    per_read = measured_ns - baseline_ns
    print(f"  loop baseline (no memory read)          {baseline_ns:>10.2f} ns")
    print(f"  loop with memory read                   {measured_ns:>10.2f} ns")
    print(f"  ==> RAM random read                     {per_read:>10.2f} ns")
    return per_read


# ---------------------------------------------------------------------------
# 2. SSD: random 4 KB reads, with the OS page cache defeated
# ---------------------------------------------------------------------------

FILENAME = "bigfile.bin"
FILE_SIZE = 512 * 1024 * 1024  # 512 MB
BLOCK = 4096  # 4 KB, the size of one page. Disks like to work in these.


def _make_file():
    if os.path.exists(FILENAME) and os.path.getsize(FILENAME) == FILE_SIZE:
        return
    print(f"  creating {FILE_SIZE // (1024*1024)} MB test file, one moment...")
    chunk = os.urandom(1024 * 1024)
    with open(FILENAME, "wb") as f:
        for _ in range(FILE_SIZE // len(chunk)):
            f.write(chunk)


def _open_uncached():
    """Open the file so that reads actually hit the disk.

    THIS IS THE MOST IMPORTANT COMMENT IN THE FILE.

    The operating system keeps recently-read file data in RAM, in something
    called the page cache. It does this silently and it is usually wonderful.
    But it means a naive disk benchmark reads the file once, and then every
    subsequent "disk read" is served from RAM at ~100ns, and your benchmark
    proudly reports that your SSD is as fast as memory. It is not. You measured
    the wrong thing and nothing warned you.

    On macOS, fcntl F_NOCACHE (the constant is 48) tells the kernel not to keep
    this file's pages around. On Linux, posix_fadvise with DONTNEED evicts them.

    Sanity check when you run this: if your SSD number comes out under 1000 ns,
    the cache is still on and the number is a lie.
    """
    fd = os.open(FILENAME, os.O_RDONLY)
    if sys.platform == "darwin":
        import fcntl
        F_NOCACHE = 48
        fcntl.fcntl(fd, F_NOCACHE, 1)
    elif sys.platform.startswith("linux"):
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    return fd

    
def measure_ssd():
    """Expect roughly 20-150 µs per random 4 KB read on an NVMe SSD."""
    print("\n[2] SSD  (random 4 KB reads, page cache disabled)")
    _make_file()
    fd = _open_uncached()
    max_offset = FILE_SIZE - BLOCK

    try:
        # TODO 2 --------------------------------------------------------------
        # Write a function `one_read()` that:
        #   - picks a random offset:  random.randrange(max_offset)
        #   - reads BLOCK bytes at that offset:  os.pread(fd, BLOCK, offset)
        #
        # os.pread reads at an absolute position without moving the file cursor,
        # which is what you want here.
        #
        # Then run it through the `timed` helper:
        #     samples = timed(one_read, 2000)
        #
        # Yes, this one times the random number generator too. At ~50ns against
        # a ~30,000ns disk read, that's a rounding error. Knowing WHEN you can
        # ignore overhead is as useful as knowing how to subtract it.
        # ---------------------------------------------------------------------
        def one_read():
            offset = random.randrange(max_offset)
            os.pread(fd, BLOCK, offset)
        samples = timed(one_read, 2000)

        if not samples:
            print("  (no samples — did you fill in TODO 2?)")
            return None
        p50 = report("SSD random 4 KB read", samples, "us")
        if percentile(samples, 50) < 1000:
            print("  !! Under 1 µs. You are measuring the page cache, not the disk.")
            print("     Re-read the comment in _open_uncached().")
        return p50 * 1000  # return ns
    finally:
        os.close(fd)


# ---------------------------------------------------------------------------
# 3. Localhost network: a TCP round trip that never leaves your machine
# ---------------------------------------------------------------------------

def _echo_server(ready):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    ready.append(srv.getsockname()[1])
    conn, _ = srv.accept()
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    while True:
        data = conn.recv(1)
        if not data:
            break
        conn.sendall(data)


def measure_localhost():
    """Expect roughly 20-100 µs.

    No wire, no distance, no router. This is the pure cost of the operating
    system's networking code: two context switches, two trips through the TCP
    stack, and the scheduler deciding to wake the other thread up.

    Every network call you ever make pays this on both ends, before a single
    photon moves. Worth knowing what it costs.
    """
    print("\n[3] Localhost  (TCP round trip, 1 byte each way)")
    ready = []
    t = threading.Thread(target=_echo_server, args=(ready,), daemon=True)
    t.start()
    while not ready:
        time.sleep(0.001)

    sock = socket.create_connection(("127.0.0.1", ready[0]))
    # Nagle's algorithm delays small packets to batch them. Great for throughput,
    # terrible for a latency benchmark. Turn it off.
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    try:
        def ping():
            sock.sendall(b"x")
            sock.recv(1)

        samples = timed(ping, 5000)

        if not samples:
            print("  (no samples — did you fill in TODO 3?)")
            return None
        p50 = report("localhost TCP round trip", samples, "us")
        return p50 * 1000  # ns
    finally:
        sock.close()


# ---------------------------------------------------------------------------
# 4. Real network: how long does distance actually cost?
# ---------------------------------------------------------------------------

# Choosing hosts is the hardest part of this measurement, and the first list I
# wrote was wrong. Most famous websites sit behind a CDN, which means your packet
# stops at a cache in a data center near you and never travels to the country on
# the label. www.mit.edu answers from Akamai. www.unimelb.edu.au answers from a
# CDN edge. Timing them tells you how far away the nearest CDN node is, which is
# a real thing to know, but it is not what we are trying to learn today.
#
# AWS regional endpoints do not hide behind a CDN. ec2.sa-east-1.amazonaws.com
# genuinely answers from Sao Paulo. That makes them honest rulers for distance.
#
# Add a host near you and one on the far side of the planet. The CONTRAST is the
# measurement. The specific hosts don't matter.
HOSTS = [
    ("ec2.ap-south-1.amazonaws.com", 443, "Mumbai, India"),
    ("ec2.ap-southeast-2.amazonaws.com", 443, "Sydney, Australia"),
    ("ec2.eu-west-1.amazonaws.com", 443, "Dublin, Ireland"),
    ("ec2.us-east-1.amazonaws.com", 443, "Virginia, USA"),
    ("ec2.sa-east-1.amazonaws.com", 443, "Sao Paulo, Brazil"),
]

NET_SAMPLES = 12  # Each one is a real round trip. Be polite, and be patient.
NET_WARMUP = 2  # See the note in timed(). Warmup across an ocean is expensive.
NET_TIMEOUT = 3  # A dead host costs this many seconds PER ATTEMPT. Keep it low.


def measure_internet():
    """Expect tens of ms for a nearby region, 300ms+ for the far side of Earth.

    We time how long a TCP connection takes to establish. That handshake is
    almost exactly one round trip: we send SYN, they reply SYN-ACK. So the
    connect time is a clean measurement of the distance, with very little
    server-side work mixed in.

    This section is slow, and the slowness IS the lesson. Every sample is a
    packet crossing an ocean and coming back. Nothing you can write makes that
    faster. Your CPU sits idle for essentially the entire run.

    Watch the p99 against the p50. On a real network they diverge, because
    packets queue behind other packets in routers you'll never see. This is the
    long tail from your reading, appearing in your own data.
    """
    print("\n[4] Internet  (TCP connect time ≈ one round trip)")
    print(f"    {len(HOSTS)} hosts x {NET_SAMPLES + NET_WARMUP} connections, "
          f"one at a time. This takes a while, on purpose.\n")
    results = {}
    for host, port, note in HOSTS:
        # Resolve DNS ONCE, up front, outside the timed loop.
        #
        # socket.create_connection((host, port)) quietly does a DNS lookup on
        # every single call. Our first version paid for that 30 times per host.
        # Worse, it meant we were timing "DNS lookup + TCP handshake" and
        # calling the total a round trip. Two different things, silently added
        # together. Resolving first means we time exactly one thing.
        try:
            ip = socket.getaddrinfo(host, port, socket.AF_INET,
                                    socket.SOCK_STREAM)[0][4][0]
        except socket.gaierror:
            print(f"  {host:<36} (DNS failed, skipping)")
            continue

        def connect():
            s = socket.create_connection((ip, port), timeout=NET_TIMEOUT)
            s.close()

        try:
            samples = timed(connect, NET_SAMPLES, warmup=NET_WARMUP)
        except (socket.error, OSError) as e:
            print(f"  {host:<36} (no response: {e})")
            continue

        p50 = report(f"{note:<20} {ip:<16}", samples, "ms")
        results[note] = p50 * 1_000_000  # ns
    return results


# ---------------------------------------------------------------------------

def main():
    random.seed(42)
    print("=" * 78)
    print("The storage hierarchy, measured on this machine")
    print("=" * 78)

    ram = measure_ram()
    ssd = measure_ssd()
    local = measure_localhost()
    net = measure_internet()

    print("\n" + "=" * 78)
    print("Ratios. THIS is the part you carry with you.")
    print("=" * 78)
    if ram and ram > 0:
        if ssd:
            print(f"  One SSD read costs as much as {ssd/ram:>12,.0f} RAM reads")
        if local:
            print(f"  One localhost RTT costs as much as {local/ram:>7,.0f} RAM reads")
        for host, ns in net.items():
            print(f"  One RTT to {host:<20} costs {ns/ram:>10,.0f} RAM reads")
    else:
        print("  (fill in the TODOs first)")

    print("\nNow write labs/day-01-latency/RESULTS.md.")
    print("Include: the table, the ratios as sentences, and the one number")
    print("that surprised you with your theory for why.\n")


if __name__ == "__main__":
    main()
