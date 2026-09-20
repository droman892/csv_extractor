# 0005. Write invalid tickets to disk instead of keeping them in memory

Status: accepted (2026-09).

## Context

The report must list every problem. Keeping the details of every invalid ticket in memory does not scale: memory and the size of the saved result grow with the number of invalid rows, so a file where most or all rows are bad is the worst case.

## Decision

While processing, each invalid ticket (its ID and its errors, nothing else) is appended to a JSON Lines file. The counts stay exact in memory. The screen reads the first 100 issues from the file; the export streams the whole file into the report.

## Alternatives considered

- Cap the number of kept tickets (tried first, at 100,000, with a "first N of M" note in the report). Rejected because the user wants every error listed.
- Re-read the original CSV at export time instead of storing anything: no extra disk, but the report could disagree with what the screen showed if the file changed in between, and it doubles the processing time.

## Consequences

- Processing is slower than the capped-in-memory alternative because every invalid ticket is written out, not just counted.
- It needs disk space in the temp folder, proportional to the number of invalid tickets. The files are deleted when you go back to the upload screen or close the window.
- A report with about five million lines is more than Excel can open (1,048,576 rows). The CSV itself is complete.
- The file is JSON Lines, not pickle, so reading it back is safe even if the file is tampered with.
