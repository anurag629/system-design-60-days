"""
Day 10 lab: indexes in depth, and the days the planner ignores your index.

This is the full working solution. The starter file is indexes.py.
Run it:      python3 solution.py

Standard library only (sqlite3). Builds one SQLite table of a few million rows
(a few seconds), then for five cases prints the EXPLAIN QUERY PLAN line AND the
timing, so you can watch the plan flip between SCAN and SEARCH with your own eyes.

The five cases:
  a. A filter with NO index. A full table SCAN. Slow.
  b. A single-column index on that same filter. A SEARCH. Fast.
  c. A composite index on (country, city). Used when you filter on country (the
     leftmost prefix) or on country AND city, but NOT when you filter on city
     alone. The plan flips straight back to SCAN. This is the leftmost-prefix rule.
  d. A covering index (one that holds every column the query needs) so SQLite
     answers from the index alone, an index-only scan with no table lookups, vs a
     non-covering index that must jump to the table for every matching row.
  e. A query that DEFEATS the index. Wrap the column in a function,
     lower(email) = ..., and the index on email is useless, because the index is
     on email, not on lower(email). Back to a SCAN.

The one line to carry home: an index is not a magic "make this column fast" button.
It is a sorted copy of some columns, and the planner uses it ONLY when your query
matches the way it is sorted. Break that shape and you silently pay a full scan.
"""

import os
import sqlite3
import sys
import time

PREDICTIONS = {
    # P1: single-column index. How many times FASTER is the SEARCH (case b, with
    #     an index on user_id) than the full SCAN (case a, no index)? A ratio.
    "single_index_speedup": 5000,

    # P2: leftmost prefix. A composite index on (country, city). How many times
    #     SLOWER is the city-only query (index unusable, back to SCAN) than the
    #     country+city query (index used)? A ratio.
    "leftmost_prefix_penalty": 2000,

    # P3: covering index. How many times FASTER is the covering index
    #     (country, amount) than the non-covering index on (country) alone, for
    #     SELECT SUM(amount) WHERE country = ? ? A ratio.
    "covering_speedup": 10,

    # P4: a defeated index. How many times SLOWER is WHERE lower(email) = ?
    #     (forced SCAN) than WHERE email = ? (index SEARCH)? A ratio.
    "function_defeat_penalty": 20000,
}

DB = "idx.db"
N = 2_000_000


def build():
    """Build one table of N rows. No user indexes yet, every case adds its own."""
    for s in ("", "-wal", "-shm", "-journal"):
        if os.path.exists(DB + s):
            os.unlink(DB + s)

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA page_size = 4096")
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute(
        "CREATE TABLE events ("
        " id INTEGER PRIMARY KEY,"
        " user_id INTEGER,"
        " country TEXT,"
        " city TEXT,"
        " amount INTEGER,"
        " email TEXT)"
    )

    def rows():
        for i in range(N):
            yield (
                i + 1,
                i % 100_000,                      # ~20 rows per user_id
                "C" + str(i % 20),                # 20 countries, ~100k rows each
                "T" + str((i // 20) % 1000),      # 1000 cities, ~2k rows each
                i % 100,                          # the number we sum
                "user" + str(i) + "@ex.com",      # unique per row
            )

    conn.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)", rows())
    conn.commit()
    return conn


def drop_user_indexes(conn):
    """Drop every index we created, so each case starts from a known state."""
    names = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]
    for name in names:
        conn.execute("DROP INDEX " + name)


def plan(conn, sql, params=()):
    """Return the EXPLAIN QUERY PLAN detail line(s), joined."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    return " / ".join(r[3] for r in rows)


def best_ms(conn, sql, params=(), reps=7):
    """Run the query reps times on a warm cache, return the best (min) time in ms."""
    out = []
    for _ in range(reps):
        start = time.perf_counter()
        conn.execute(sql, params).fetchone()
        out.append((time.perf_counter() - start) * 1000)
    return min(out)


def show(conn, label, sql, params=()):
    p = plan(conn, sql, params)
    ms = best_ms(conn, sql, params)
    kind = "SEARCH" if p.startswith("SEARCH") else ("SCAN" if p.startswith("SCAN") else "?")
    print(f"  {label}")
    print(f"    EXPLAIN QUERY PLAN:  {p}")
    print(f"    [{kind}]  time: {ms:8.3f} ms")
    return ms


def part1(conn):
    print("=" * 78)
    print("Part 1: no index (case a) vs a single-column index (case b)")
    print("=" * 78)
    print("  Query: SELECT SUM(amount) FROM events WHERE user_id = 42424")
    print()
    q = "SELECT SUM(amount) FROM events WHERE user_id = ?"
    uid = (42_424,)

    drop_user_indexes(conn)
    scan_ms = show(conn, "case a, NO index:", q, uid)

    print()
    idx_user_sql = "CREATE INDEX idx_user ON events(user_id)"
    conn.execute(idx_user_sql)
    search_ms = show(conn, "case b, index on user_id:", q, uid)

    print()
    print(f"  the index turned a SCAN of {N:,} rows into a SEARCH of about 20.")
    print(f"  speedup: {scan_ms / search_ms:,.0f}x faster.")
    return scan_ms / search_ms


def part2(conn):
    print("\n" + "=" * 78)
    print("Part 2: composite index on (country, city), the leftmost-prefix rule")
    print("=" * 78)
    drop_user_indexes(conn)
    conn.execute("CREATE INDEX idx_cc ON events(country, city)")
    print("  index: CREATE INDEX idx_cc ON events(country, city)")
    print("  (each query sums amount, which is NOT in the index, so the plan shows")
    print("   a plain SEARCH or SCAN instead of a covering one)")
    print()

    a_ms = show(
        conn,
        "filter on country only (the leftmost column):",
        "SELECT SUM(amount) FROM events WHERE country = ?",
        ("C7",),
    )
    print()
    ab_ms = show(
        conn,
        "filter on country AND city (full prefix):",
        "SELECT SUM(amount) FROM events WHERE country = ? AND city = ?",
        ("C7", "T500"),
    )
    print()
    city_only_sql = "SELECT SUM(amount) FROM events WHERE city = ?"
    b_ms = show(
        conn,
        "filter on city only (skips the leftmost column):",
        city_only_sql,
        ("T500",),
    )
    print()
    print("  country alone and country+city both SEARCH the index. city alone can")
    print("  not: the index is sorted by country first, so the cities are scattered")
    print(f"  all through it. The planner gives up and SCANs all {N:,} rows.")
    print("  both the city-only and the country+city filter match only a handful of")
    print(f"  rows, yet one scans everything. penalty: {b_ms / ab_ms:,.0f}x slower.")
    return b_ms / ab_ms


def part3(conn):
    print("\n" + "=" * 78)
    print("Part 3: covering index vs non-covering, for SUM(amount) WHERE country = ?")
    print("=" * 78)
    q = "SELECT SUM(amount) FROM events WHERE country = ?"
    c = ("C7",)

    drop_user_indexes(conn)
    conn.execute("CREATE INDEX idx_country ON events(country)")
    print("  index: CREATE INDEX idx_country ON events(country)")
    noncov_ms = show(conn, "non-covering, must fetch amount from the table:", q, c)

    print()
    drop_user_indexes(conn)
    cover_sql = "CREATE INDEX idx_cover ON events(country, amount)"
    conn.execute(cover_sql)
    print("  index: CREATE INDEX idx_cover ON events(country, amount)")
    cov_ms = show(conn, "covering, amount is IN the index already:", q, c)

    print()
    print("  the covering index holds country AND amount, so SQLite never touches")
    print("  the table. Watch for USING COVERING INDEX in the plan above.")
    print(f"  the ~100,000 saved table lookups make it {noncov_ms / cov_ms:,.1f}x faster.")
    return noncov_ms / cov_ms


def part4(conn):
    print("\n" + "=" * 78)
    print("Part 4: the defeated index, wrapping the column in a function")
    print("=" * 78)
    drop_user_indexes(conn)
    conn.execute("CREATE INDEX idx_email ON events(email)")
    print("  index: CREATE INDEX idx_email ON events(email)")
    print("  (each query sums amount so the plan shows a plain SEARCH or SCAN)")
    print()

    good_ms = show(
        conn,
        "WHERE email = ? (uses the index):",
        "SELECT SUM(amount) FROM events WHERE email = ?",
        ("user1500000@ex.com",),
    )
    print()
    defeat_sql = "SELECT SUM(amount) FROM events WHERE lower(email) = ?"
    bad_ms = show(
        conn,
        "WHERE lower(email) = ? (index defeated):",
        defeat_sql,
        ("user1500000@ex.com",),
    )
    print()
    print("  the index is sorted by email, not by lower(email). SQLite can not use")
    print("  it, so it SCANs every row and calls lower() on each one.")
    print(f"  penalty: {bad_ms / good_ms:,.0f}x slower for one small function wrapper.")
    return bad_ms / good_ms


def verdict(name, predicted, actual, unit="x"):
    if predicted is None:
        print(f"  {name:<28} actual = {actual:>10,.1f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.4 <= ratio <= 2.5:
        note = "   close enough"
    elif ratio > 1:
        note = f"{ratio:>5.1f}x  you guessed too LOW"
    else:
        note = f"{1 / ratio:>5.1f}x  you guessed too HIGH"
    print(f"  {name:<28} you = {predicted:>8,.0f}   actual = {actual:>10,.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    conn = build()
    try:
        p1 = part1(conn)
        p2 = part2(conn)
        p3 = part3(conn)
        p4 = part4(conn)
    finally:
        conn.close()
        for s in ("", "-wal", "-shm", "-journal"):
            if os.path.exists(DB + s):
                os.unlink(DB + s)

    print("\n" + "=" * 78)
    print("Scoreboard, predicted ratio vs actual")
    print("=" * 78)
    verdict("P1 single-index speedup", PREDICTIONS["single_index_speedup"], p1)
    verdict("P2 leftmost-prefix penalty", PREDICTIONS["leftmost_prefix_penalty"], p2)
    verdict("P3 covering speedup", PREDICTIONS["covering_speedup"], p3)
    verdict("P4 function-defeat penalty", PREDICTIONS["function_defeat_penalty"], p4)

    print("\n" + "=" * 78)
    print("The numbers to carry")
    print("=" * 78)
    print(f"  A single-column index turned a full scan into a point lookup, about")
    print(f"  {p1:,.0f}x faster. A covering index skipped ~100,000 table lookups to run")
    print(f"  {p3:,.1f}x faster than a plain one. And TWO perfectly good indexes got")
    print(f"  ignored: the composite index for a non-leftmost filter ({p2:,.0f}x slower),")
    print(f"  and the email index wrapped in lower() ({p4:,.0f}x slower). The index exists.")
    print("  The planner still SCANs. Shape your query to match the index, or the")
    print("  index you lovingly created does nothing.")
    print("\nNow write labs/day-10-indexes/RESULTS.md.\n")


if __name__ == "__main__":
    main()
