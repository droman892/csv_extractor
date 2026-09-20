# Business case

This page says who CSV Extractor is for, what it would save, and how sure anyone can be. Numbers are sorted by how they are known. Nothing in the "assumed" and "hypothesized" sections has been observed: those are values to replace with real ones from a real team.

## The problem

Teams that receive support-ticket data as CSV (from a help desk export, a vendor or a hand-edited spreadsheet) have to find the rows that are wrong before the data can be billed against, reported on or imported. Doing it in a spreadsheet is slow, inconsistent between people and unreliable at size: a filter that misses one misspelled status changes a report, and a spreadsheet stops opening past about a million rows.

**Who has the problem (hypothesis):** an analyst or operations person at a support organization who receives ticket exports regularly and is responsible for their accuracy. 

## What the tool does about it

It applies the same five rules to every row, lists each failure with its ticket, field, value and reason, flags duplicate ticket IDs on every row involved, and gives back a full report. It runs on the user's own machine, so the data does not leave it.

## Why not AI

The rules are fixed and exact (nine digits, one of three priorities, hours in half-hour steps). A deterministic check is cheaper, faster, gives the same answer every time and can be explained row by row. A model would add cost, latency and the chance of a wrong answer for no gain. Where a model could help, in a tool like this, is outside the checking: suggesting a likely correction for a misspelled status, or grouping the failures by cause. Neither is built, and neither is needed to prove the value of the checking itself.

### Measured on David's own machine (Windows)

These were timed on the app's actual target platform (Windows), one run each, using files from `scripts/generate_test_data.py`. Exact generation parameters (customer count, invalid-row rate) were not recorded for these specific runs.

| Rows | Processing time | Export time |
| --- | --- | --- |
| 2,000 | 0.2 s | 0.1 s |
| 30,000 | 1.8 s | 0.1 s |
| 400,000 | 24.3 s | 1.4 s |
| 5,000,000 | 283.8 s (4m 44s) | 16.2 s |

From 30,000 rows up, per-row processing cost is steady at about 60 microseconds/row (30,000: 60 µs/row; 400,000: 61 µs/row; 5,000,000: 57 µs/row). The 2,000-row figure (100 µs/row) is higher per row, most likely fixed per-run overhead (starting the worker process, opening the file) rather than a per-row cost, since that overhead is the same regardless of file size and matters more when there are few rows to spread it over. Export time is small next to processing time at every size tested here.
