"""
Day 5 lab: why "page 50,000" is slow and how to make every page fast.

Run it:      python3 pagination_lab.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only. Builds a 2,000,000 row SQLite table once (about 35 MB,
a few seconds), then reuses it. The whole thing runs in well under a minute.

Two ways to paginate, and this lab makes you feel the difference:

  OFFSET   SELECT ... ORDER BY id LIMIT 20 OFFSET 1000000
           "skip a million rows, then give me twenty." Simple, and the default
           in almost every tutorial. The database has to walk past all million
           rows it is skipping, every single time.

  KEYSET   SELECT ... WHERE id > :last_seen ORDER BY id LIMIT 20
           also called cursor or seek pagination. "give me twenty rows after
           the last id I saw." The database jumps straight there using the
           index, so it never walks past anything.

If you get stuck, the full working version is solution.py in this folder.
"""

import os
import sqlite3
import statistics
import sys
import time

# ---------------------------------------------------------------------------
# YOUR PREDICTIONS. Paper first, then here, then run.
# ---------------------------------------------------------------------------

PREDICTIONS = {
    # The table has 2,000,000 posts. A page is 20 rows. We fetch one page from
    # different depths and time it.

    # P1: milliseconds to fetch the FIRST page with OFFSET (depth 0).
    "offset_first_ms": None,

    # P2: milliseconds to fetch a page deep in the table with OFFSET,
    #     skipping 1,000,000 rows.
    "offset_deep_ms": None,

    # P3: milliseconds to fetch that same deep page with KEYSET
    #     (WHERE id > 1000000). You measured a warm index lookup on Day 2.
    "keyset_deep_ms": None,

    # P4: how many times slower is the deep OFFSET page than the deep KEYSET
    #     page? (just the ratio, e.g. 50 means 50x)
    "deep_ratio": None,
}

# ---------------------------------------------------------------------------

DB = "posts.db"
N_ROWS = 2_000_000
PAGE = 20
DEPTHS = [0, 1_000, 10_000, 100_000, 1_000_000, N_ROWS - PAGE]
WALK_PAGE = 100
WALK_OFFSET_PAGES = 2_000   # we walk this many offset pages, then extrapolate


def build_db():
    if os.path.exists(DB) and os.path.getsize(DB) > 30_000_000:
        return
    for s in ("", "-wal", "-shm"):
        if os.path.exists(DB + s):
            os.unlink(DB + s)
    print(f"  building a {N_ROWS:,} row table, one moment...")
    c = sqlite3.connect(DB)
    c.execute("PRAGMA journal_mode = WAL")
    c.execute("PRAGMA synchronous = OFF")
    c.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, author_id INTEGER, created_at INTEGER)")
    c.executemany(
        "INSERT INTO posts VALUES (?, ?, ?)",
        ((i + 1, i % 50_000, 1_700_000_000 + i) for i in range(N_ROWS)),
    )
    c.commit()
    c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    c.close()


def best_ms(fn, reps=7):
    """Fastest of a few runs, in ms. Fastest, not average, because we want the
    cost of the query, not the cost of the query plus a random hiccup."""
    out = []
    for _ in range(reps):
        start = time.perf_counter()
        fn()
        out.append((time.perf_counter() - start) * 1000)
    return min(out)


def offset_page(conn, offset):
    # TODO 1 ------------------------------------------------------------------
    # Return one page using OFFSET. Skip `offset` rows, then take PAGE rows,
    # ordered by id:
    #
    #     return conn.execute(
    #         "SELECT id, author_id, created_at FROM posts ORDER BY id LIMIT ? OFFSET ?",
    #         (PAGE, offset),
    #     ).fetchall()
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def keyset_page(conn, cursor):
    # TODO 2 ------------------------------------------------------------------
    # Return one page using KEYSET. Take the next PAGE rows whose id is greater
    # than `cursor`, ordered by id. No OFFSET anywhere:
    #
    #     return conn.execute(
    #         "SELECT id, author_id, created_at FROM posts WHERE id > ? ORDER BY id LIMIT ?",
    #         (cursor, PAGE),
    #     ).fetchall()
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def plan(conn, sql):
    return " / ".join(r[-1] for r in conn.execute("EXPLAIN QUERY PLAN " + sql))


# ---------------------------------------------------------------------------
# Part 1: one page, from different depths
# ---------------------------------------------------------------------------

def part1(conn):
    print("=" * 78)
    print(f"Part 1: fetch ONE page of {PAGE} rows, from different depths")
    print("=" * 78)
    if offset_page(conn, 0) is None or keyset_page(conn, 0) is None:
        print("  (fill in TODO 1 and TODO 2)")
        return None, None
    print(f"  {'depth':>12} {'offset ms':>11} {'keyset ms':>11} {'offset / keyset':>16}")
    first = {}
    deep = {}
    for d in DEPTHS:
        o = best_ms(lambda: offset_page(conn, d))
        k = best_ms(lambda: keyset_page(conn, d))
        if d == 0:
            first["offset"] = o
        if d == 1_000_000:
            deep["offset"], deep["keyset"] = o, k
        print(f"  {d:>12,} {o:>11.3f} {k:>11.3f} {o / k:>15.0f}x")

    print("\n  offset pagination gets slower the deeper you go. keyset does not")
    print("  even notice the depth. Here is why, straight from the query planner:")
    print(f"    offset deep : {plan(conn, 'SELECT id FROM posts ORDER BY id LIMIT 20 OFFSET 1000000')}")
    print(f"    keyset deep : {plan(conn, 'SELECT id FROM posts WHERE id > 1000000 ORDER BY id LIMIT 20')}")
    print("  SCAN means it reads and throws away every row it skips. SEARCH means")
    print("  it jumps straight to the right spot using the primary key index.")
    return first, deep


# ---------------------------------------------------------------------------
# Part 2: walk the whole table, both ways
# ---------------------------------------------------------------------------

def part2(conn):
    print("\n" + "=" * 78)
    print(f"Part 2: page through the table in pages of {WALK_PAGE}")
    print("=" * 78)

    # Keyset: walk the entire table. One row read per row returned.
    start = time.perf_counter()
    cursor, pages, seen = 0, 0, 0
    while True:
        rows = conn.execute(
            "SELECT id FROM posts WHERE id > ? ORDER BY id LIMIT ?", (cursor, WALK_PAGE)
        ).fetchall()
        if not rows:
            break
        seen += len(rows)
        pages += 1
        # TODO 3 --------------------------------------------------------------
        # Advance the cursor to the last id you just saw, so the next loop asks
        # for rows AFTER it. Without this the query returns the same first page
        # forever:
        #     cursor = rows[-1][0]
        # ---------------------------------------------------------------------
        pass  # <-- replace this
        if cursor == 0:
            print("  (fill in TODO 3: advance the cursor, or this loops forever)")
            return
    keyset_secs = time.perf_counter() - start
    print(f"  keyset: walked all {seen:,} rows in {pages:,} pages, "
          f"{keyset_secs:.2f} s, touched {seen:,} rows")

    # Offset: walk only the first WALK_OFFSET_PAGES, time it, then extrapolate.
    start = time.perf_counter()
    rows_touched = 0
    for p in range(WALK_OFFSET_PAGES):
        off = p * WALK_PAGE
        rows = conn.execute(
            "SELECT id FROM posts ORDER BY id LIMIT ? OFFSET ?", (WALK_PAGE, off)
        ).fetchall()
        # TODO 4 --------------------------------------------------------------
        # Count the rows the database actually had to touch for this page. To
        # serve OFFSET `off`, it reads and discards `off` rows, then reads the
        # `len(rows)` it returns:
        #     rows_touched += off + len(rows)
        # ---------------------------------------------------------------------
        pass  # <-- replace this
    offset_secs = time.perf_counter() - start
    if rows_touched == 0:
        print("  (fill in TODO 4: count rows_touched)")
        return
    rows_done = WALK_OFFSET_PAGES * WALK_PAGE
    print(f"  offset: walked the first {rows_done:,} rows in {WALK_OFFSET_PAGES:,} pages, "
          f"{offset_secs:.2f} s, touched {rows_touched:,} rows")

    total_pages = N_ROWS // WALK_PAGE
    full_touched = WALK_PAGE * total_pages * (total_pages + 1) // 2
    scale = full_touched / rows_touched if rows_touched else 0
    print(f"\n  To finish the whole table with offset would touch about "
          f"{full_touched / 1e9:.0f} billion rows")
    print(f"  and take roughly {offset_secs * scale:.0f} s, versus "
          f"{keyset_secs:.2f} s for keyset.")
    print("  Same data, same page size. One reads each row once. The other reads")
    print("  the first row two million times.")


# ---------------------------------------------------------------------------
# Part 3: the correctness bug nobody mentions (fully written, just watch)
# ---------------------------------------------------------------------------

def part3():
    print("\n" + "=" * 78)
    print("Part 3: offset does not just get slow, it shows wrong results")
    print("=" * 78)
    print("  A feed, newest first, 5 per page. You read page 1. While you read it,")
    print("  3 new posts arrive. Then you ask for page 2.\n")

    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE feed (id INTEGER PRIMARY KEY)")
    c.executemany("INSERT INTO feed VALUES (?)", ((i,) for i in range(1, 21)))

    def off(o):
        return [r[0] for r in c.execute(
            "SELECT id FROM feed ORDER BY id DESC LIMIT 5 OFFSET ?", (o,))]

    def key(cur):
        return [r[0] for r in c.execute(
            "SELECT id FROM feed WHERE id < ? ORDER BY id DESC LIMIT 5", (cur,))]

    p1 = off(0)
    c.executemany("INSERT INTO feed VALUES (?)", ((i,) for i in (21, 22, 23)))
    p2 = off(5)
    dupes = sorted(set(p1) & set(p2), reverse=True)
    print(f"  OFFSET  page 1: {p1}")
    print(f"          then 3 posts arrive (21, 22, 23)")
    print(f"          page 2: {p2}")
    print(f"          shown twice: {dupes}  <- the user sees {len(dupes)} posts again\n")

    c.execute("DELETE FROM feed WHERE id > 20")

    p1 = key(10 ** 9)
    cur = p1[-1]
    c.executemany("INSERT INTO feed VALUES (?)", ((i,) for i in (21, 22, 23)))
    p2 = key(cur)
    dupes = sorted(set(p1) & set(p2), reverse=True)
    print(f"  KEYSET  page 1: {p1}   (cursor = last id seen = {cur})")
    print(f"          then 3 posts arrive (21, 22, 23)")
    print(f"          page 2: {p2}")
    print(f"          shown twice: {dupes if dupes else 'nothing'}  <- correct, "
          f"the cursor is anchored to a row, not a position")
    c.close()


# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit="ms"):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>10,.3f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.5 <= ratio <= 2:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>7.0f}x  too LOW"
    else:
        note = f"{1 / ratio:>7.0f}x  too HIGH"
    print(f"  {name:<30} you = {predicted:>9,.2f}   actual = {actual:>10,.3f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    build_db()
    conn = sqlite3.connect(DB)
    first, deep = part1(conn)
    if first is None:
        conn.close()
        sys.exit(1)
    part2(conn)
    conn.close()
    part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 offset, first page", PREDICTIONS["offset_first_ms"], first["offset"])
    verdict("P2 offset, deep page", PREDICTIONS["offset_deep_ms"], deep["offset"])
    verdict("P3 keyset, deep page", PREDICTIONS["keyset_deep_ms"], deep["keyset"])
    verdict("P4 deep offset / keyset", PREDICTIONS["deep_ratio"],
            deep["offset"] / deep["keyset"], unit="x")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    r = deep["offset"] / deep["keyset"]
    print(f"  The deep offset page was about {r:.0f}x slower than the keyset page,")
    print("  for the exact same 20 rows. The offset query gets slower every page.")
    print("  The keyset query is flat forever. This is why infinite scroll uses a")
    print("  cursor, and why 'jump to page 5000' quietly disappeared from the web.")
    print("\nNow write labs/day-05-pagination/RESULTS.md.\n")


if __name__ == "__main__":
    main()
