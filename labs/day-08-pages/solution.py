"""
Day 8 lab: how a row actually sits on a disk, and why column stores exist.

This is the full working solution. The starter file is page_lab.py.
Run it:      python3 solution.py

Standard library only. Builds two SQLite files (a few seconds), then reads one
of them byte by byte to prove the on-disk layout, and races a row store against
a column store on the same question.

The big ideas:
  - A database file is a stack of fixed-size pages (4096 bytes here). To read
    one row, it reads the whole page that row sits on.
  - A fat row means few rows per page, so a scan touches many pages.
  - A row store keeps all of a row's columns together. To add up ONE column it
    still reads every row's every column off the disk. A column store keeps each
    column apart, so the same sum reads almost nothing. That is the whole reason
    analytics databases are columnar.
"""

import os
import sqlite3
import struct
import sys
import time

PREDICTIONS = {
    # P1: the page size of a default SQLite file, in bytes.
    "page_size_bytes": 4096,

    # P2: a "fat" row here is about 180 bytes on disk. How many fit in one
    #     4096-byte page?
    "rows_per_page": 22,

    # P3: the row-store file holds 500,000 fat rows. Its size in megabytes?
    "row_store_mb": 90,

    # P4: the column store keeps only the one number we sum. How many times
    #     SMALLER is its file than the row store's?
    "col_store_smaller_x": 16,
}

ROW_DB = "store.db"
COL_DB = "store_col.db"
N = 500_000
PAD = "x" * 40  # four of these per row make the row fat


def build():
    for path in (ROW_DB, COL_DB):
        for s in ("", "-wal", "-shm", "-journal"):
            if os.path.exists(path + s):
                os.unlink(path + s)

    row = sqlite3.connect(ROW_DB)
    row.execute("PRAGMA page_size = 4096")
    row.execute("PRAGMA journal_mode = DELETE")
    row.execute("PRAGMA synchronous = OFF")
    row.execute(
        "CREATE TABLE events (id INTEGER PRIMARY KEY, a TEXT, b TEXT, c TEXT, d TEXT, val INTEGER)"
    )
    row.executemany(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
        ((i + 1, PAD, PAD, PAD, PAD, i % 1000) for i in range(N)),
    )
    row.commit()
    row.close()

    col = sqlite3.connect(COL_DB)
    col.execute("PRAGMA page_size = 4096")
    col.execute("PRAGMA journal_mode = DELETE")
    col.execute("PRAGMA synchronous = OFF")
    col.execute("CREATE TABLE events_val (id INTEGER PRIMARY KEY, val INTEGER)")
    col.executemany(
        "INSERT INTO events_val VALUES (?, ?)", ((i + 1, i % 1000) for i in range(N))
    )
    col.commit()
    col.close()


def read_header(path):
    """Return (magic, page_size, page_count) from a SQLite file's 100-byte header.

    The format is public and fixed. Bytes 0-15 are a magic string. Bytes 16-17
    are the page size, big-endian. Bytes 28-31 are the number of pages.
    """
    with open(path, "rb") as f:
        head = f.read(100)
    magic = head[0:16]
    page_size = struct.unpack(">H", head[16:18])[0]
    page_count = struct.unpack(">I", head[28:32])[0]
    return magic, page_size, page_count


def best_ms(path, sql, reps=5):
    out = []
    for _ in range(reps):
        c = sqlite3.connect(path)
        start = time.perf_counter()
        c.execute(sql).fetchone()
        out.append((time.perf_counter() - start) * 1000)
        c.close()
    return min(out)


def part1():
    print("=" * 78)
    print("Part 1: read the database file's own header, byte by byte")
    print("=" * 78)
    magic, page_size, page_count = read_header(ROW_DB)
    size = os.path.getsize(ROW_DB)
    print(f"  magic string:  {magic!r}")
    print(f"  page size:     {page_size} bytes")
    print(f"  page count:    {page_count:,}")
    print(f"  file size:     {size:,} bytes")
    print(f"  page_size x page_count = {page_size * page_count:,}  "
          f"({'matches' if page_size * page_count == size else 'does NOT match'})")
    print("  A database file is exactly a stack of fixed-size pages. To read one")
    print("  row, the engine reads the whole page that row lives on, never less.")
    return page_size, size


def part2(page_size, size):
    print("\n" + "=" * 78)
    print("Part 2: how many rows fit in one page")
    print("=" * 78)
    bytes_per_row = size / N
    rows_per_page = page_size / bytes_per_row
    print(f"  {N:,} rows in {size:,} bytes = {bytes_per_row:.1f} bytes per row")
    print(f"  so about {rows_per_page:.1f} rows fit in one {page_size}-byte page")
    print("  A fatter row means fewer rows per page, which means a scan reads more")
    print("  pages for the same number of rows. Row width is a performance knob.")
    return rows_per_page


def part3():
    print("\n" + "=" * 78)
    print("Part 3: add up ONE column. Row store vs column store.")
    print("=" * 78)
    row_sql = "SELECT SUM(val) FROM events"
    col_sql = "SELECT SUM(val) FROM events_val"
    row_ms = best_ms(ROW_DB, row_sql)
    col_ms = best_ms(COL_DB, col_sql)
    row_sz = os.path.getsize(ROW_DB)
    col_sz = os.path.getsize(COL_DB)
    print(f"  row store:    {row_sz / 1e6:>6.1f} MB on disk,  SUM(val) in {row_ms:>6.1f} ms")
    print(f"  column store: {col_sz / 1e6:>6.1f} MB on disk,  SUM(val) in {col_ms:>6.1f} ms")
    print(f"  the row-store file is {row_sz / col_sz:.1f}x bigger, and the scan is "
          f"{row_ms / col_ms:.1f}x slower")
    print("  Same sum, same answer. The row store had to read every row's four fat")
    print("  text columns off the disk just to reach the one number it needed. The")
    print("  column store kept that number apart, so it read almost nothing.")
    return row_sz, col_sz, row_ms, col_ms


def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<30} actual = {actual:>10,.1f} {unit}  (no prediction)")
        return
    ratio = actual / predicted if predicted else float("inf")
    if 0.7 <= ratio <= 1.4:
        note = "     close enough"
    elif ratio > 1:
        note = f"{ratio:>6.1f}x  too LOW"
    else:
        note = f"{1 / ratio:>6.1f}x  too HIGH"
    print(f"  {name:<30} you = {predicted:>8,.1f}   actual = {actual:>10,.1f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    build()
    page_size, size = part1()
    rows_per_page = part2(page_size, size)
    row_sz, col_sz, row_ms, col_ms = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 page size", PREDICTIONS["page_size_bytes"], page_size, "bytes")
    verdict("P2 rows per page", PREDICTIONS["rows_per_page"], rows_per_page, "")
    verdict("P3 row-store size", PREDICTIONS["row_store_mb"], row_sz / 1e6, "MB")
    verdict("P4 column store smaller", PREDICTIONS["col_store_smaller_x"], row_sz / col_sz, "x")

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  To add up one column over {N:,} rows, the row store read "
          f"{row_sz / 1e6:.0f} MB")
    print(f"  off the disk. The column store read {col_sz / 1e6:.1f} MB for the exact")
    print(f"  same answer, {row_sz / col_sz:.0f}x less. That gap is why the database behind")
    print("  your app (row store, fast to fetch a whole record) and the database")
    print("  behind your dashboards (column store, fast to scan one field) are not")
    print("  the same kind of database.")
    print("\nNow write labs/day-08-pages/RESULTS.md.\n")


if __name__ == "__main__":
    main()
