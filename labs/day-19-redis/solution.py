"""
Day 19 lab: Redis internals, taught through the one thing that matters most in
practice, the round trip.

This is the full working solution. The starter file is pipelining.py.
Run it:      python3 solution.py

Standard library only. One real TCP server on 127.0.0.1 with an OS-assigned
port, single threaded, handling one client connection. Runs in a few seconds and
cleans up its socket. No temp files.

The big ideas, all measured on your own machine:
  - A key-value op (GET, SET) is tiny: a dict lookup, microseconds of CPU. The
    expensive part is the ROUND TRIP: your bytes travel to the server and you
    WAIT for the reply before sending the next command. Part 1 does N ops one at
    a time and measures the throughput that round trip pins you to.
  - PIPELINING is the fix. Send a batch of M commands in one write, then read all
    M replies together. Now N ops cost N/M round trips, not N. Part 2 sweeps the
    batch size and the throughput climbs several times over, then plateaus once
    the round trip is no longer the bottleneck.
  - That plateau is why Redis is single threaded, and why rich commands (hashes,
    sorted sets, MGET) exist: each op is so cheap that the network, not the CPU,
    was the wall the whole time. Part 3 shows it with a multi-key command.
"""

import math
import socket
import sys
import threading
import time

PREDICTIONS = {
    # P1: N = 50,000 GETs, ONE AT A TIME (send one, wait for the reply, send the
    #     next). Roughly how many ops per second does that get you?
    "one_at_a_time_ops_per_sec": 45_000,

    # P2: pipelining at a batch of M = 100. For 50,000 ops, how many round trips
    #     does that take? (N / M)
    "pipelined_round_trips_at_100": 500,

    # P3: the headline. Pipelined throughput at M = 100 divided by the one-at-a-
    #     time throughput. How many TIMES faster is pipelining?
    "pipeline_speedup_at_100": 20,

    # P4: pipelined throughput at M = 100, in ops per second.
    "pipelined_ops_per_sec_at_100": 1_000_000,
}

HOST = "127.0.0.1"
N = 50_000                      # ops in the timed workload
BATCHES = [1, 2, 5, 10, 50, 100, 500, 1000]
HEADLINE_M = 100                # the batch size the scoreboard reports
RECV = 65536


# ---------------------------------------------------------------------------
# The server: single threaded, in memory, one connection, a tiny text protocol
# ---------------------------------------------------------------------------
#
# Protocol, one command per line, each line ends in "\n":
#   SET key value   -> +OK
#   GET key         -> $value   (or $-1 if the key is missing)
#   MGET k1 k2 ...   -> *v1|v2|...   (one reply line for the whole lot)
#
# Notice there is not a single lock in here. One thread owns the dict and
# processes commands from the one connection in the order they arrive. That is
# Redis in miniature: single threaded on purpose.

def process(line, store):
    parts = line.split(b" ")
    cmd = parts[0].upper()
    if cmd == b"SET":
        store[parts[1]] = parts[2]
        return b"+OK\n"
    if cmd == b"GET":
        v = store.get(parts[1])
        return b"$" + v + b"\n" if v is not None else b"$-1\n"
    if cmd == b"MGET":
        vals = [store.get(k, b"") for k in parts[1:]]
        return b"*" + b"|".join(vals) + b"\n"
    return b"-ERR unknown\n"


class Server:
    def __init__(self):
        self.store = {}
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.lsock.bind((HOST, 0))          # OS picks a free port
        self.lsock.listen(1)
        self.port = self.lsock.getsockname()[1]
        self.conn = None
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        try:
            conn, _ = self.lsock.accept()
        except OSError:
            return
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.conn = conn
        buf = b""
        store = self.store
        while True:
            try:
                chunk = conn.recv(RECV)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            if b"\n" not in buf:
                continue
            # Process every complete line we have, batch all replies into one
            # write. A real server does exactly this: drain what the socket gave
            # you, answer it in one go.
            lines = buf.split(b"\n")
            buf = lines.pop()               # last piece is the incomplete tail
            out = [process(line, store) for line in lines if line]
            if out:
                try:
                    conn.sendall(b"".join(out))
                except OSError:
                    break
        try:
            conn.close()
        except OSError:
            pass

    def shutdown(self):
        try:
            self.lsock.close()
        except OSError:
            pass
        if self.conn is not None:
            try:
                self.conn.close()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# The client: a plain socket with a small read buffer so we can pull one reply
# line at a time, or many
# ---------------------------------------------------------------------------

class Client:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.buf = b""

    def send(self, data):
        self.sock.sendall(data)

    def read_line(self):
        while b"\n" not in self.buf:
            chunk = self.sock.recv(RECV)
            if not chunk:
                raise ConnectionError("server closed the connection")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return line

    def read_lines(self, n):
        return [self.read_line() for _ in range(n)]

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def round_trip(client, cmd):
    """One full round trip: send ONE command, wait for its ONE reply.

    This is the unit of cost in Part 1. Your bytes go to the server and you
    block here until the answer comes back, before you can send anything else.
    """
    client.send(cmd)
    return client.read_line()


def pipeline_batch(client, batch):
    """One round trip for a WHOLE batch: send every command in a single write,
    then read all the replies together.

    This is pipelining. len(batch) commands, but still just one trip out and one
    trip back. That is the entire trick of Part 2.
    """
    client.send(b"".join(batch))
    return client.read_lines(len(batch))


# ---------------------------------------------------------------------------

def preload(client, n):
    """Fill the store with n keys so the GETs in the timed parts all hit. Done
    with pipelining (internal plumbing, not the thing we are measuring)."""
    cmds = [b"SET key:%d val%d\n" % (i, i) for i in range(n)]
    for batch in chunks(cmds, 1000):
        client.send(b"".join(batch))
        client.read_lines(len(batch))


def part1(client, gets):
    print("=" * 78)
    print("Part 1: N = 50,000 GETs, ONE AT A TIME. Each op is a full round trip.")
    print("=" * 78)

    # Warm up the connection and confirm the round trip works before timing.
    probe = round_trip(client, b"GET key:0\n")
    if probe is None:
        print("  (fill in TODO 1)")
        return None

    n = len(gets)
    start = time.perf_counter()
    for cmd in gets:
        round_trip(client, cmd)
    elapsed = time.perf_counter() - start

    throughput = n / elapsed
    us_per_rt = elapsed / n * 1_000_000

    print(f"  ops:                 {n:>12,}")
    print(f"  round trips:         {n:>12,}   (one per op)")
    print(f"  total time:          {elapsed * 1000:>11.1f} ms")
    print(f"  throughput:          {throughput:>12,.0f} ops/sec")
    print(f"  time per round trip: {us_per_rt:>11.1f} us")
    print("  The server work per op is a dict lookup, well under a microsecond.")
    print("  Almost all of that per-op time is the round trip: send, wait, recv.")
    print("  You are not CPU bound here. You are latency bound.")
    return elapsed, throughput, n


def part2(client, gets, one_throughput):
    print("\n" + "=" * 78)
    print("Part 2: PIPELINING. Send M commands in one write, read M replies.")
    print("=" * 78)

    probe = pipeline_batch(client, gets[:2])
    if probe is None:
        print("  (fill in TODO 3)")
        return None

    n = len(gets)
    print(f"  {'batch M':>8} {'round trips':>12} {'ops/sec':>14} {'vs one-at-a-time':>18}")
    results = {}
    for m in BATCHES:
        start = time.perf_counter()
        for batch in chunks(gets, m):
            pipeline_batch(client, batch)
        elapsed = time.perf_counter() - start
        tput = n / elapsed
        trips = math.ceil(n / m)
        results[m] = (tput, trips)
        speed = tput / one_throughput if one_throughput else 0
        print(f"  {m:>8} {trips:>12,} {tput:>14,.0f} {speed:>16.1f}x")

    pipe_through, rt_at_100 = results[HEADLINE_M]
    speedup = pipe_through / one_throughput

    print(f"\n  At M = {HEADLINE_M}: {rt_at_100:,} round trips instead of {n:,}, and the")
    print(f"  throughput is {speedup:.1f}x the one-at-a-time rate. Same server, same")
    print("  ops, same dict. The ONLY thing that changed is how many times you")
    print("  stopped to wait for a reply. Notice the climb flattens at the top:")
    print("  once the round trip is amortised away, the server's own per-op cost")
    print("  is all that is left, and that cost is tiny.")
    return results, speedup, pipe_through, rt_at_100


def part3(client):
    print("\n" + "=" * 78)
    print("Part 3: why single threaded, and how rich commands save round trips.")
    print("=" * 78)

    k = 100
    reps = 200
    keys = [b"key:%d" % i for i in range(k)]

    # K keys the slow way: K separate GET round trips.
    start = time.perf_counter()
    for _ in range(reps):
        for key in keys:
            round_trip(client, b"GET " + key + b"\n")
    t_singles = time.perf_counter() - start

    # The same K keys in ONE round trip with a multi-key command.
    mget = b"MGET " + b" ".join(keys) + b"\n"
    start = time.perf_counter()
    for _ in range(reps):
        round_trip(client, mget)
    t_mget = time.perf_counter() - start

    rt_singles = reps * k
    rt_mget = reps
    saving = t_singles / t_mget if t_mget else 0

    print(f"  fetch {k} keys, {reps} times over:")
    print(f"    {k} single GETs each time:   {rt_singles:>8,} round trips  {t_singles * 1000:>8.1f} ms")
    print(f"    one MGET of {k} keys each:    {rt_mget:>8,} round trips  {t_mget * 1000:>8.1f} ms")
    print(f"    the one rich command is {saving:.1f}x faster, for the same data")
    print()
    print("  Single threaded, on purpose. Each op is a handful of microseconds of")
    print("  CPU, so the bottleneck is the network and (de)serialisation, not the")
    print("  core. One thread means no locks, no contention, no race conditions,")
    print("  and a simple mental model. This whole server never took a lock.")
    print()
    print("  Rich data structures (hashes, sorted sets, lists) and multi-key")
    print("  commands (MGET, HSET, ZADD) are the same lesson as pipelining, baked")
    print("  into the server: do in ONE command and ONE round trip what would")
    print("  otherwise be many. A leaderboard ZADD, a session HSET, an MGET of a")
    print("  user's keys. The round trip was always the expensive part.")
    return saving, rt_singles, rt_mget


# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>10,.0f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.5 <= ratio <= 2.0:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<34} you = {predicted:>10,.0f}   actual = {actual:>10,.0f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    server = Server()
    client = None
    try:
        client = Client(HOST, server.port)
        preload(client, N)
        gets = [b"GET key:%d\n" % i for i in range(N)]

        p1 = part1(client, gets)
        if p1 is None:
            sys.exit(1)
        _, one_throughput, n = p1

        p2 = part2(client, gets, one_throughput)
        if p2 is None:
            sys.exit(1)
        results, speedup, pipe_through, rt_at_100 = p2

        part3(client)

        print("\n" + "=" * 78)
        print("Scoreboard")
        print("=" * 78)
        verdict("P1 one-at-a-time ops/sec", PREDICTIONS["one_at_a_time_ops_per_sec"],
                one_throughput, "")
        verdict("P2 pipelined round trips @100", PREDICTIONS["pipelined_round_trips_at_100"],
                rt_at_100, "")
        verdict("P3 pipeline speedup @100", PREDICTIONS["pipeline_speedup_at_100"],
                speedup, "x")
        verdict("P4 pipelined ops/sec @100", PREDICTIONS["pipelined_ops_per_sec_at_100"],
                pipe_through, "")

        print("\n" + "=" * 78)
        print("The number to carry")
        print("=" * 78)
        print(f"  The same 50,000 GETs. One at a time: {one_throughput:,.0f} ops/sec. Pipelined")
        print(f"  at a batch of {HEADLINE_M}: {pipe_through:,.0f} ops/sec, about {speedup:.0f}x faster, from")
        print(f"  {n:,} round trips down to {rt_at_100:,}. The server never got busier.")
        print("  You just stopped waiting for a reply after every single command.")
        print("  Round trips, not server CPU, were the wall the whole time. That is")
        print("  also why Redis is single threaded and loves one rich command over")
        print("  a hundred small ones.")
        print("\nNow write labs/day-19-redis/RESULTS.md.\n")
    finally:
        if client is not None:
            client.close()
        server.shutdown()


if __name__ == "__main__":
    main()
