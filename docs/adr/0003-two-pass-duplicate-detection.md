# 0003. Find duplicate ticket IDs in a first pass

Status: accepted (2026-09).

## Context

A ticket ID must appear only once. If two rows share an ID, neither can be trusted, so both are invalid. That cannot be decided in a single pass: the first row with an ID looks fine until the second one appears, and by then the first has already been counted.

## Decision

Read the file twice. Pass 1 collects the valid ticket IDs it has seen and counts those seen more than once. Pass 2 validates each row and marks every row whose ID is in the repeated set. The file is streamed both times; it is never loaded whole.

## Alternatives considered

- Keep every row in memory and compare afterwards: memory grows with the file, which contradicts the 5-million-row goal.
- Report only a count of duplicates: cheaper, but the user cannot see which rows to fix.
- A fixed-size bitmap of the 9-digit ID space instead of a set: fixed size regardless of file size, against a set that grows with the data.

## Consequences

- Pass 1 adds a second full read of the file and holds the set of distinct valid ticket IDs in memory for its duration; neither has been measured separately from the whole-file timings in `docs/business-case.md`.
- Every row that shares an ID gets its own issue, so a heavily duplicated file has a large report.
