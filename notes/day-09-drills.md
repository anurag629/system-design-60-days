---
title: "Day 9 drills"
parent: "Day 9: B-trees and LSM trees"
grand_parent: "Week 2: storage"
nav_order: 2
---

# Day 9 drills

Written on paper first. B-trees, page splits, LSM runs, and the read tax.

D1 (1M inserts into a B-tree, 50,000 leaf pages, cache holds 5,000: fraction of random inserts that hit a cold page, and why the sequential case barely touches the cache):

D2 (LSM flushes a sorted run every 64 MB, you write 2 GB: how many runs before compaction, and worst-case runs a read must check for a key not in the memtable):

D3 (B-tree with 8 KB pages updates one 100-byte row: minimum bytes written to disk, and how that write amplification compares to the LSM's append-then-compact):

D4 (classify four workloads as B-tree-friendly or LSM-friendly: banking ledger, 500k-writes/sec event log, time-series metrics, balanced users table):

D5 (LSM with 8 runs, a bloom filter per run at 1% false positives: average runs actually read from disk for an absent key, and what problem that solves):
