"""
Day 3 lab: take one HTTPS request apart and time every piece of it.

Run it:      python3 anatomy.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only, nothing to install. Takes about a minute, most of it
spent waiting on São Paulo.

What happens when you type a URL is usually recited as a list of steps. Here
you measure each step, and you find out that the list is really a list of
round trips, and that round trips are almost the whole bill.
"""

import socket
import ssl
import statistics
import sys
import time

# ---------------------------------------------------------------------------
# YOUR PREDICTIONS. Paper first, then here, then run.
# ---------------------------------------------------------------------------

PREDICTIONS = {
    # Q1: for a brand new HTTPS request, how many network round trips happen
    #     before the first byte of the response arrives? Don't count DNS.
    #     Count TCP, TLS and the HTTP request itself. A whole number.
    "round_trips_before_first_byte": None,

    # Q2: milliseconds for one brand new HTTPS request to Virginia, from
    #     "start DNS lookup" to "first byte of the response". On Day 1 you
    #     measured a round trip to Virginia at about 296 ms. Use it.
    "cold_request_ms_virginia": None,

    # Q3: milliseconds for a SECOND request to Virginia, sent over the same
    #     connection that is already open (no new DNS, TCP or TLS).
    "reused_request_ms_virginia": None,

    # Q4: milliseconds for a DNS lookup of a name you looked up a second ago.
    "dns_repeat_ms": None,
}

# ---------------------------------------------------------------------------

# Same AWS regional endpoints as Day 1. They answer from the region on the
# label instead of from a CDN cache down the road, so distance is real.
HOSTS = [
    ("ec2.ap-south-1.amazonaws.com", "Mumbai"),
    ("ec2.us-east-1.amazonaws.com", "Virginia"),
    ("ec2.sa-east-1.amazonaws.com", "Sao Paulo"),
]
PORT = 443
SAMPLES = 5          # cold requests per host; we keep the median
TIMEOUT = 10

# One TLS context for the whole run. Building it loads the certificate store
# from disk, which is slow and has nothing to do with the network.
CTX = ssl.create_default_context()


def ms(seconds):
    return seconds * 1000


def request_bytes(host):
    """A minimal HTTP/1.1 GET. `Connection: keep-alive` asks the server to leave
    the connection open after answering, so we can send a second request on it.
    """
    return (f"GET / HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: day03-lab\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n").encode()


def read_rest_of_response(sock, already=b""):
    """Read one full HTTP response, starting from whatever bytes we already have.

    We have to read exactly one response, no more and no less, or the second
    request on this connection gets confused. HTTP tells you where the body
    ends with the Content-Length header, so: read headers, find that number,
    read that many body bytes. These AWS endpoints reply with a 301 redirect
    and an empty body, which keeps it simple.
    """
    buf = already
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("server closed the connection mid-response")
        buf += chunk
    head, _, body = buf.partition(b"\r\n\r\n")
    status = head.split(b"\r\n", 1)[0].decode(errors="replace")
    length = 0
    for line in head.split(b"\r\n")[1:]:
        name, _, value = line.partition(b":")
        if name.strip().lower() == b"content-length":
            length = int(value.strip())
    while len(body) < length:
        body += sock.recv(4096)
    return status


def cold_request(host):
    """One brand new HTTPS request, every phase timed on its own.

    Returns a dict of phase -> seconds, plus the TLS version and HTTP status.
    """
    t = {}

    # TODO 1 ------------------------------------------------------------------
    # DNS: turn the name into an IP address.
    #
    #   start = time.perf_counter()
    #   ip = socket.getaddrinfo(host, PORT, socket.AF_INET,
    #                           socket.SOCK_STREAM)[0][4][0]
    #   t["dns"] = time.perf_counter() - start
    # -------------------------------------------------------------------------
    ip = None  # <-- replace this block

    if ip is None:
        return None

    # TODO 2 ------------------------------------------------------------------
    # TCP: the three-way handshake. create_connection() sends SYN, waits for
    # SYN-ACK, sends ACK, and returns. We pass the IP, NOT the host name, so
    # it cannot sneak a second DNS lookup into our timing. (That exact bug
    # cost us an hour on Day 1.)
    #
    #   start = time.perf_counter()
    #   raw = socket.create_connection((ip, PORT), timeout=TIMEOUT)
    #   t["tcp"] = time.perf_counter() - start
    # -------------------------------------------------------------------------
    raw = None  # <-- replace this block

    # STRETCH (only after your first full run, see the day page) -------------
    # One line goes here. Don't add it until the day page tells you to.
    # -------------------------------------------------------------------------

    # TODO 3 ------------------------------------------------------------------
    # TLS: wrap the TCP socket. The handshake (agree on a cipher, check the
    # certificate, agree on keys) happens inside wrap_socket(). server_hostname
    # is how the server knows which certificate to show you, and how Python
    # knows which name the certificate must match.
    #
    #   start = time.perf_counter()
    #   conn = CTX.wrap_socket(raw, server_hostname=host)
    #   t["tls"] = time.perf_counter() - start
    # -------------------------------------------------------------------------
    conn = None  # <-- replace this block

    # TODO 4 ------------------------------------------------------------------
    # HTTP: send the request and wait for the FIRST byte of the answer. Time
    # to first byte (TTFB) = one round trip + however long the server thought.
    #
    #   start = time.perf_counter()
    #   conn.sendall(request_bytes(host))
    #   first = conn.recv(1)
    #   t["ttfb"] = time.perf_counter() - start
    # -------------------------------------------------------------------------
    first = None  # <-- replace this block

    if raw is None or conn is None or first is None:
        return None

    status = read_rest_of_response(conn, first)

    # The same request again, on the connection we already paid for.
    # No DNS, no TCP handshake, no TLS handshake. Just the HTTP round trip.
    start = time.perf_counter()
    conn.sendall(request_bytes(host))
    second_first = conn.recv(1)
    t["reused"] = time.perf_counter() - start
    read_rest_of_response(conn, second_first)

    version = conn.version()
    conn.close()
    return t, version, status


def median_of(runs, key):
    return statistics.median(r[key] for r in runs)


def measure(host, label):
    runs, version, status = [], None, None
    for i in range(SAMPLES):
        try:
            out = cold_request(host)
        except (OSError, ssl.SSLError) as e:
            print(f"  {label:<10} request {i + 1} failed: {e}")
            continue
        if out is None:
            return None
        t, version, status = out
        runs.append(t)
    if not runs:
        return None
    first_dns = runs[0]["dns"]
    m = {k: median_of(runs, k) for k in ("dns", "tcp", "tls", "ttfb", "reused")}
    m["dns_first"] = first_dns
    m["dns_repeat"] = statistics.median(r["dns"] for r in runs[1:]) if len(runs) > 1 else first_dns
    m["cold_total"] = m["dns_first"] + m["tcp"] + m["tls"] + m["ttfb"]
    m["version"], m["status"] = version, status
    return m


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>10,.2f} {unit:<4}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.8 <= ratio <= 1.25:
        note = "     nailed it"
    elif ratio > 1:
        note = f"{ratio:>7.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>7.1f}x  too HIGH"
    print(f"  {name:<30} you = {predicted:>9,.2f}   "
          f"actual = {actual:>10,.2f} {unit:<4}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. Guessing after you see the answer is not guessing.\n")
        sys.exit(1)

    print("=" * 78)
    print(f"One HTTPS request, taken apart   ({SAMPLES} cold requests per host, median)")
    print("=" * 78)
    print(f"  {'':<10} {'DNS':>8} {'TCP':>8} {'TLS':>8} {'TTFB':>8} "
          f"{'COLD':>9} {'REUSED':>8}   all in ms")

    results = {}
    for host, label in HOSTS:
        m = measure(host, label)
        if m is None:
            print(f"  {label:<10} (fill in the TODOs first)")
            sys.exit(1)
        results[label] = m
        print(f"  {label:<10} {ms(m['dns_first']):>8.1f} {ms(m['tcp']):>8.1f} "
              f"{ms(m['tls']):>8.1f} {ms(m['ttfb']):>8.1f} "
              f"{ms(m['cold_total']):>9.1f} {ms(m['reused']):>8.1f}")

    any_m = next(iter(results.values()))
    print(f"\n  TLS version negotiated: {any_m['version']}.   "
          f"Server answered: {any_m['status']}")
    print("  DNS column is the FIRST lookup of each run. Repeats are below.")

    # -----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("Counted in round trips   (TCP connect time = 1 round trip)")
    print("=" * 78)
    for label, m in results.items():
        rtt = m["tcp"]
        tls_rt = m["tls"] / rtt
        ttfb_rt = m["ttfb"] / rtt
        total_rt = (m["tcp"] + m["tls"] + m["ttfb"]) / rtt
        print(f"  {label:<10} TCP 1.0  +  TLS {tls_rt:.1f}  +  HTTP {ttfb_rt:.1f}"
              f"  =  {total_rt:.1f} round trips before the first byte")
    print("\n  If TLS shows ~1, you got TLS 1.3. If ~2, TLS 1.2. Anything well")
    print("  above that is the server's CPU doing crypto, or the certificate being")
    print("  big enough to need more than one flight of packets.")

    # -----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("DNS: first lookup vs repeat")
    print("=" * 78)
    for label, m in results.items():
        print(f"  {label:<10} first {ms(m['dns_first']):>8.2f} ms    "
              f"repeat {ms(m['dns_repeat']):>8.3f} ms")
    print("\n  The repeat never leaves your laptop. The OS keeps a DNS cache, and")
    print("  it keeps each answer for as long as the record's TTL allows.")

    # -----------------------------------------------------------------------
    v = results.get("Virginia")
    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    trips = (v["tcp"] + v["tls"] + v["ttfb"]) / v["tcp"]
    verdict("Q1 round trips before 1st byte", PREDICTIONS["round_trips_before_first_byte"], trips)
    verdict("Q2 cold request, Virginia", PREDICTIONS["cold_request_ms_virginia"], ms(v["cold_total"]), "ms")
    verdict("Q3 reused request, Virginia", PREDICTIONS["reused_request_ms_virginia"], ms(v["reused"]), "ms")
    verdict("Q4 repeat DNS lookup", PREDICTIONS["dns_repeat_ms"], ms(v["dns_repeat"]), "ms")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  A new connection to Virginia cost {ms(v['cold_total']):,.0f} ms before a")
    print(f"  single byte came back. Reusing it cost {ms(v['reused']):,.0f} ms.")
    print(f"  Connection reuse made the request {v['cold_total'] / v['reused']:.1f}x faster, and")
    print("  not one line of server code changed. That is why browsers keep")
    print("  connections open, why HTTP/2 puts many requests on one connection,")
    print("  and why every serious HTTP client has a connection pool.")
    print("\nNow write labs/day-03-url/RESULTS.md.\n")


if __name__ == "__main__":
    main()
