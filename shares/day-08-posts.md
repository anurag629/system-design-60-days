---
title: "Day 8 posts"
parent: "Day 8: how a row sits on disk"
grand_parent: "Week 2: storage"
nav_order: 3
---

# Day 8 posts: LinkedIn and X

The header bytes and the row-vs-column size ratio both make good screenshots. Swap in your own numbers and voice.

## LinkedIn

Day 8 of 60 days of system design, start of week 2, storage. Today I opened a database file and read its header with about 20 lines of Python. Turns out there is no magic in there at all.

A SQLite file is literally a stack of fixed-size pages, 4 KB each. The first 100 bytes told me the page size, the page count, and a magic string that says "SQLite format 3". The file size came out exactly page size times page count. That is the whole structure.

The fact that reframes everything: the database never reads a row, it reads a page. Ask for one 8-byte number and it pulls the entire 4 KB page that number sits on. So a fatter row means fewer rows per page, which means every scan reads more pages. Row width is a performance decision.

Then the payoff. I summed one column over 500,000 rows, two ways:

    row store (all columns together):   read 89 MB
    column store (that column apart):   read 5.5 MB

Same answer. 16 times less data. Because the row store had to drag every row's four fat text columns off the disk just to reach the one number I wanted, and the column store kept that number by itself.

That is why the database behind your app and the database behind your dashboards are not the same kind of database. Row stores are fast at "give me this whole record." Column stores are fast at "scan one field across everything." Opposite jobs.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #databases #learninginpublic

## X thread

**1/**

I read a database file's raw header with ~20 lines of Python today.

A SQLite file is just a stack of 4 KB pages. First 100 bytes: magic string "SQLite format 3", page size, page count. File size = page size x page count, exactly. No magic.

Day 8 of 60 days of system design.

**2/**

The fact that changes everything: the database reads PAGES, not rows.

Ask for one 8-byte number and it reads the whole 4 KB page that number lives on. So a fatter row = fewer rows per page = every scan reads more pages. Row width is a performance knob.

**3/**

Then I summed one column over 500,000 rows two ways:

row store:    read 89 MB
column store: read 5.5 MB

Same answer. 16x less data, because the row store dragged every row's fat columns off disk to reach one number.

**4/**

That is the whole reason there are two kinds of database.

Row store (Postgres, MySQL): fast at "give me this whole record." Your app.
Column store (Snowflake, ClickHouse): fast at "scan one field across everything." Your dashboards.

Opposite jobs, opposite layouts.

**5/**

The best part: none of this was a diagram in a book. I read the bytes off my own disk and measured the gap myself.

Open the black box. It is just pages.

Code: github.com/anurag629/system-design-60-days
