# Business case

This page says who CSV Extractor is for, what it would save, and how sure anyone can be. Numbers are sorted by how they are known. Nothing in the "assumed" and "hypothesized" sections has been observed, so treat those as values to replace with real ones from a real team.

## The problem

Teams that receive support-ticket data as CSV (from a help desk export, a vendor, or a hand-edited spreadsheet) have to find the rows that are wrong before the data can be billed against, reported on, or imported. Doing it in a spreadsheet is slow, inconsistent between people, and unreliable at size. For example, a filter that misses one misspelled status changes a report, and a spreadsheet stops opening past about a million rows.

**Who has the problem (hypothesis):** an analyst or operations person at a support organization who receives ticket exports regularly and is responsible for their accuracy. 

## What the tool does about it

It applies the same five rules to every row, lists each failure with its ticket, field, value, and reason, flags duplicate ticket IDs on every row involved, and gives back a full report. It runs on the user's own machine, so the data does not leave it.

## Why not AI

The rules are fixed and exact. For example, a ticket ID has nine digits, a priority is one of three values, and hours come in half-hour steps. A deterministic check is cheaper and faster than a model, gives the same answer every time, and can explain each failure row by row. A model would add cost, latency, and the chance of a wrong answer, with nothing gained in return.

A model could still help around the checking, though not in it. It could suggest a likely correction for a misspelled status or group the failures by cause. Neither is built because the checking proves its value without them.

### Measured on David's own machine (Windows)

These were timed on the app's actual target platform (Windows), one run each, using files from `scripts/generate_test_data.py`. Exact generation parameters (customer count, invalid-row rate) were not recorded for these specific runs.

| Rows | Processing time | Export time |
| --- | --- | --- |
| 2,000 | 0.2 s | 0.1 s |
| 30,000 | 1.8 s | 0.1 s |
| 400,000 | 24.3 s | 1.4 s |
| 5,000,000 | 283.8 s (4m 44s) | 16.2 s |

Processing time grows roughly in step with file size, meaning ten times the rows takes about ten times as long. Export is fast compared with processing at every size tested.
