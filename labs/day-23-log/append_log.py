"""
Day 23 lab: the log as a primitive. Append-only, offsets, and the replay superpower.

Run it:      python3 append_log.py

Fill in PREDICTIONS below BEFORE you run anything. Then fill in the four TODOs.
Standard library only (a list for the log, sqlite3 for the durable offset store).
Single threaded, so the numbers are exact and it finishes in a couple of seconds.
It cleans up the one sqlite file it makes.

The whole day in three measured moves:
  - Part 1, append. Writing a record only ever adds to the end and hands back a
    strictly increasing offset: 0, 1, 2, ... Nothing is ever edited in place.
    Append N records and read the offsets straight back.
  - Part 2, a consumer with its own offset. The consumer reads forward from its
    position, processes each record, and commits its offset to a durable store.
    We crash it mid-stream and restart: it resumes from the committed offset, so
    nothing is missed. Because it commits AFTER processing, a crash in the gap
    between "done the work" and "committed" re-reads exactly one record. That is
    at-least-once, and it is the whole of Day 25 in one line.
  - Part 3, replay. A brand new, second consumer starts at offset 0 and re-reads
    the entire history on its own, while the first consumer sits at the far end.
    Two consumers, one log, two different positions. This is the thing a queue
    cannot do: the log kept every record, so you can add a reader later and let
    it reprocess all of history.

If you get stuck, the full working version is solution.py in this folder.
"""

import os
import sqlite3
import sys
import time
from collections import Counter

PREDICTIONS = {
    # P1: you append N records to a brand new, empty log. Offsets start at 0.
    #     What is the offset of the LAST record?
    "last_offset": None,

    # P2: the consumer commits its offset AFTER processing each record. It
    #     crashes in the gap between processing a record and committing it, then
    #     restarts from its committed offset. How many records get processed
    #     TWICE (the duplicate count)?
    "duplicates_after_crash": None,

    # P3: after that same crash and restart, how many of the N records were
    #     MISSED entirely (processed zero times)?
    "records_missed_after_crash": None,

    # P4: a brand new second consumer is added later and starts at offset 0,
    #     while the first consumer sits at the end. How many records does the
    #     new consumer re-read from the log?
    "replay_records": None,
}

DB_PATH = "offsets.db"

N = 100_000                 # records appended to the log
CRASH_AT = 59_999           # offset where the consumer dies, mid-stream
CONSUMER_A = "orders-writer"
CONSUMER_B = "analytics-v2"  # the new consumer added later, for replay


class TODONotDone(Exception):
    """Raised by a blank TODO so the lab stops cleanly with a clear message
    instead of crashing or hanging."""
    def __init__(self, n):
        super().__init__(f"TODO {n} is not filled in yet")
        self.n = n


# ---------------------------------------------------------------------------
# The log: an append-only sequence of records, each with an integer offset.
# ---------------------------------------------------------------------------

class Log:
    """An append-only log. You only ever add to the end; nothing in the middle
    is ever edited or removed. Each record gets the next integer offset, so the
    offsets are 0, 1, 2, ... in the exact order the records arrived."""

    def __init__(self):
        self._records = []

    def append(self, record):
        # TODO 1 ------------------------------------------------------------------
        # The whole append-only idea in one line. A new record's offset is simply
        # how many records are already in the log: the first record is offset 0,
        # the next is 1, and so on. You only ever add to the end.
        #     offset = len(self._records)
        # -------------------------------------------------------------------------
        offset = None  # <-- replace this
        if offset is None:
            raise TODONotDone(1)
        self._records.append(record)
        return offset

    def read_from(self, offset):
        """Yield (offset, record) from `offset` to the current end, in order.
        A consumer reads forward from wherever its own cursor sits."""
        for i in range(offset, len(self._records)):
            yield i, self._records[i]

    def __len__(self):
        return len(self._records)


# ---------------------------------------------------------------------------
# The offset store: a tiny durable table, consumer name -> next offset to read.
# This is what survives a crash. The log remembers the data; this remembers
# where each reader got to.
# ---------------------------------------------------------------------------

class OffsetStore:
    def __init__(self, path):
        # autocommit (isolation_level=None) + no fsync, so the thousands of tiny
        # offset writes stay fast. Our "crash" is a lost object, not a power cut,
        # so the committed value is safely on disk either way.
        self.conn = sqlite3.connect(path, isolation_level=None)
        self.conn.execute("PRAGMA synchronous = OFF")
        self.conn.execute("PRAGMA journal_mode = MEMORY")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS offsets "
            "(consumer TEXT PRIMARY KEY, position INTEGER NOT NULL)"
        )

    def committed(self, consumer):
        """The stored next-offset-to-read for a consumer, or 0 if it has none."""
        row = self.conn.execute(
            "SELECT position FROM offsets WHERE consumer = ?", (consumer,)
        ).fetchone()
        return row[0] if row else 0

    def commit(self, consumer, position):
        self.conn.execute(
            "INSERT INTO offsets (consumer, position) VALUES (?, ?) "
            "ON CONFLICT(consumer) DO UPDATE SET position = excluded.position",
            (consumer, position),
        )

    def close(self):
        self.conn.close()


# ---------------------------------------------------------------------------
# A crash, and a consumer that tracks its own offset.
# ---------------------------------------------------------------------------

class Crash(Exception):
    """Raised to simulate a consumer dying mid-stream, after it has processed a
    record but before it has committed that record's offset."""
    def __init__(self, offset):
        super().__init__(f"crashed at offset {offset}")
        self.offset = offset


class Consumer:
    """A consumer with its own cursor into one shared log. It reads forward from
    its position, processes each record via `sink`, and commits its offset to the
    durable store so a restart can resume exactly where it left off.

    `sink(offset, record)` is the downstream side effect, like writing a row to a
    reporting table. We model it as a Counter keyed by offset so we can see, after
    the fact, exactly how many times each record was processed."""

    def __init__(self, name, store, sink, start=None):
        self.name = name
        self.store = store
        self.sink = sink
        # start=None means "resume from my committed offset". The replay consumer
        # passes start=0 on purpose, to re-read from the very beginning.
        self.position = self._resume() if start is None else start

    def _resume(self):
        # TODO 2 ------------------------------------------------------------------
        # On restart, a consumer must pick up exactly where it left off. Read this
        # consumer's committed offset from the durable store and return it. That
        # one stored number is what makes a crash safe: it is the dividing line
        # between "already done" and "still to do".
        #     return self.store.committed(self.name)
        # -------------------------------------------------------------------------
        committed = None  # <-- replace this with: committed = self.store.committed(self.name)
        if committed is None:
            raise TODONotDone(2)
        return committed

    def commit(self, offset):
        """Persist progress. We store offset + 1, the NEXT offset to read, so a
        restart does not re-read a record we already finished. consume() calls
        this only AFTER the record is processed, which is what makes the log
        at-least-once rather than at-most-once."""
        # TODO 3 ------------------------------------------------------------------
        # Commit this consumer's position: store offset + 1 (the NEXT offset to
        # read) under its name. The ordering matters more than the line does.
        # consume() calls commit() only AFTER the record's work is done, so a
        # crash in the gap re-reads one record instead of skipping it. Commit
        # before the work and you would get at-most-once (gaps) instead.
        #     self.store.commit(self.name, offset + 1)
        # -------------------------------------------------------------------------
        raise TODONotDone(3)  # <-- delete this line and write the commit above

    def consume(self, log, crash_at=None):
        """Read forward, process, commit. Returns how many records were processed
        in this run. If crash_at is set, die right after processing that offset
        and before committing it."""
        processed = 0
        for offset, record in log.read_from(self.position):
            self.sink(offset, record)                 # (1) do the work
            processed += 1
            if crash_at is not None and offset == crash_at:
                raise Crash(offset)                   # (2) die BEFORE committing
            self.commit(offset)                       # (3) commit only after (1)
            self.position = offset + 1
        return processed


def replay_start_offset():
    """The offset a brand new consumer must start at to replay the whole log."""
    # TODO 4 ----------------------------------------------------------------------
    # A brand new consumer that wants the full history must start at the very
    # first record. In any log, the first record is offset 0, so a full replay
    # begins at 0. (A consumer that only wanted new records would start at
    # len(log) instead, but today we want all of it.)
    #     start = 0
    # -----------------------------------------------------------------------------
    start = None  # <-- replace this with: start = 0
    if start is None:
        raise TODONotDone(4)
    return start


# ---------------------------------------------------------------------------
# Part 1: append. Offsets are handed out 0, 1, 2, ... and never change.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: append. The log only grows, and every record gets an offset.")
    print("=" * 78)
    log = Log()

    start = time.perf_counter()
    offsets = [log.append(f"event-{i:06d}") for i in range(N)]
    append_ms = (time.perf_counter() - start) * 1000

    last_offset = offsets[-1]
    first_three = offsets[:3]
    last_three = offsets[-3:]

    print(f"  records appended:                 {len(log):,}")
    print(f"  first three offsets handed back:  {first_three}")
    print(f"  last three offsets handed back:   {last_three}")
    print(f"  the last record's offset:         {last_offset:,}")
    print(f"  (appending {N:,} records took {append_ms:.0f} ms, about {N / (append_ms / 1000):,.0f}/sec)")
    print("  Offsets start at 0 and climb by one. A record's offset is just its")
    print("  position in arrival order, and once written it never moves. Reading")
    print("  offset 0 tomorrow gives the same record it gave today.")
    return log, last_offset


# ---------------------------------------------------------------------------
# Part 2: a consumer with its own offset, a crash, and at-least-once.
# ---------------------------------------------------------------------------

def part2(log, store):
    print("\n" + "=" * 78)
    print("Part 2: a consumer that remembers its offset, crashes, and resumes.")
    print("=" * 78)

    applied = Counter()                      # the downstream effect, keyed by offset

    def sink(offset, record):
        applied[offset] += 1

    # First run: the consumer starts fresh (committed offset 0) and dies at CRASH_AT,
    # after processing that record but before committing it.
    consumer = Consumer(CONSUMER_A, store, sink, start=None)
    crashed_at = None
    try:
        consumer.consume(log, crash_at=CRASH_AT)
    except Crash as c:
        crashed_at = c.offset

    processed_before = sum(applied.values())
    committed_after_crash = store.committed(CONSUMER_A)
    del consumer                             # the crashed worker is gone for good

    # Restart: a brand new consumer object, same name. It reads its committed
    # offset from the store and resumes from there. Nothing in memory survived;
    # only the durable offset did.
    restarted = Consumer(CONSUMER_A, store, sink, start=None)
    resumed_from = restarted.position
    processed_after = restarted.consume(log)

    total_processed = sum(applied.values())
    missed = sum(1 for off in range(N) if applied[off] == 0)
    duplicates = sum(1 for off in range(N) if applied[off] > 1)
    dupe_offsets = [off for off in range(N) if applied[off] > 1]

    print(f"  crashed after processing offset:  {crashed_at:,}")
    print(f"  records processed before crash:   {processed_before:,}")
    print(f"  committed offset the store kept:  {committed_after_crash:,}")
    print(f"  restarted consumer resumed from:  {resumed_from:,}")
    print(f"  records processed after restart:  {processed_after:,}")
    print(f"  ----")
    print(f"  total records processed:          {total_processed:,}  (= N + {total_processed - N})")
    print(f"  records MISSED (processed 0x):    {missed}")
    print(f"  records DUPLICATED (processed 2x):{duplicates:>3}   at offset {dupe_offsets}")
    print("  The crash landed in the gap between processing a record and")
    print("  committing its offset. On restart the consumer resumed from the last")
    print("  COMMITTED offset, so it re-did that one in-flight record. Nothing was")
    print("  lost, and exactly one record ran twice. Committing after the work")
    print("  (not before) buys at-least-once: a crash costs a duplicate, never a")
    print("  gap. Flip the order and you would get at-most-once instead. Day 25.")
    return duplicates, missed


# ---------------------------------------------------------------------------
# Part 3: replay. A new consumer starts at 0 and re-reads all of history.
# ---------------------------------------------------------------------------

def part3(log, store):
    print("\n" + "=" * 78)
    print("Part 3: replay. Add a new consumer later, re-read the whole log.")
    print("=" * 78)

    a_offset = store.committed(CONSUMER_A)   # the first consumer is at the end

    replayed_offsets = []

    def sink(offset, record):
        replayed_offsets.append(offset)

    # A brand new, independent consumer. It starts at offset 0 on purpose, so it
    # replays the entire history, no matter how far along the first consumer is.
    start = replay_start_offset()
    new_consumer = Consumer(CONSUMER_B, store, sink, start=start)
    b_start = new_consumer.position

    replayed = new_consumer.consume(log)
    b_offset = store.committed(CONSUMER_B)
    a_offset_after = store.committed(CONSUMER_A)   # untouched by the new consumer

    saw_full_history = (replayed_offsets == list(range(N)))

    print(f"  log length (records still kept):  {len(log):,}")
    print(f"  consumer A ({CONSUMER_A}) offset:  {a_offset:,}")
    print(f"  consumer B ({CONSUMER_B}) starts:  {b_start}")
    print(f"  ----")
    print(f"  two consumers, one log, different positions: A at {a_offset:,}, B at {b_start}")
    print(f"  records consumer B replayed:      {replayed:,}")
    print(f"  B read every offset 0..{N - 1:,} in order: {saw_full_history}")
    print(f"  consumer A's offset after B ran:  {a_offset_after:,}  (unchanged, independent)")
    print(f"  consumer B's offset now:          {b_offset:,}")
    print("  The log kept every record, so a reader added long after the fact")
    print("  rebuilt all of history on its own cursor, while the first consumer")
    print("  sat untouched at the end. A queue cannot do this: once a message is")
    print("  taken it is gone, so a new reader sees nothing of the past. The log")
    print("  is a shared tape every consumer rewinds for itself.")
    return replayed


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def verdict(name, predicted, actual, unit=""):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>9,} {unit}  (no prediction)")
        return
    if predicted == actual:
        note = "     spot on"
    elif predicted and 0.6 <= actual / predicted <= 1.7:
        note = "     close enough"
    elif actual > predicted:
        note = "     too LOW"
    else:
        note = "     too HIGH"
    print(f"  {name:<34} you = {predicted:>9,}   actual = {actual:>9,} {unit}  {note}")


def self_test():
    """Exercise each TODO once, instantly and in isolation, before the real run.
    A blank TODO raises TODONotDone, which we turn into a clean 'fill in TODO N'
    message instead of a crash or a hang."""
    missing = set()

    # TODO 1: append hands back an offset.
    try:
        Log().append("probe")
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 2: a consumer resuming from its committed offset (start=None).
    try:
        store = OffsetStore(":memory:")
        Consumer("probe", store, lambda off, rec: None, start=None)
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 3: commit after processing. start=0 skips TODO 2 so this is isolated.
    try:
        store = OffsetStore(":memory:")
        Consumer("probe", store, lambda off, rec: None, start=0).commit(0)
    except TODONotDone as e:
        missing.add(e.n)

    # TODO 4: the replay start offset.
    try:
        replay_start_offset()
    except TODONotDone as e:
        missing.add(e.n)

    return sorted(missing)


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The surprise is the lesson, so earn it.\n")
        sys.exit(1)

    gaps = self_test()
    if gaps:
        print("\n  !! Some TODOs are not filled in yet:")
        for n in gaps:
            print(f"       - fill in TODO {n}")
        print("     Fill them in and run again. See solution.py if you get stuck.\n")
        sys.exit(1)

    wipe()
    store = OffsetStore(DB_PATH)
    try:
        log, last_offset = part1()
        duplicates, missed = part2(log, store)
        replayed = part3(log, store)

        print("\n" + "=" * 78)
        print("Scoreboard")
        print("=" * 78)
        verdict("P1 last offset after append", PREDICTIONS["last_offset"], last_offset)
        verdict("P2 duplicates after crash", PREDICTIONS["duplicates_after_crash"], duplicates)
        verdict("P3 records missed after crash", PREDICTIONS["records_missed_after_crash"], missed)
        verdict("P4 records replayed from 0", PREDICTIONS["replay_records"], replayed)

        print("\n" + "=" * 78)
        print("The number to carry")
        print("=" * 78)
        print(f"  One append-only log of {N:,} records. The first consumer crashed")
        print(f"  mid-stream, resumed from its committed offset, and re-ran exactly")
        print(f"  {duplicates} record ({missed} lost): that is at-least-once, bought by committing")
        print(f"  the offset AFTER the work. Then a brand new consumer started at")
        print(f"  offset 0 and replayed all {replayed:,} records on its own cursor, while")
        print(f"  the first consumer sat untouched at the end. Two readers, one log,")
        print(f"  two positions. The offset lives with the reader, not the log, and")
        print(f"  that one design choice is what Kafka is built on. Day 24 next.")
        print("\nNow write labs/day-23-log/RESULTS.md.\n")
    finally:
        store.close()
        wipe()


def wipe():
    for suffix in ("", "-wal", "-shm", "-journal"):
        p = DB_PATH + suffix
        if os.path.exists(p):
            os.unlink(p)


if __name__ == "__main__":
    main()
