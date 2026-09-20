# 0006. Neutralize spreadsheet formulas in the export

Status: accepted (2026-09).

## Context

The report is a CSV file that people open in a spreadsheet, and it contains text copied from the uploaded file: customer names, ticket IDs, and the invalid values themselves. A cell that starts with `=`, `+`, `-`, `@`, a tab or a carriage return is executed as a formula by Excel, Google Sheets and LibreOffice. A hostile or careless input file could therefore run a formula, or leak data, on whoever opens the report ("CSV injection").

## Decision

Every text value that comes from the input file is passed through `safe_cell()` before it is written. A value that starts with one of those characters gets a leading apostrophe, which makes spreadsheets treat it as plain text. Plain numbers such as `-3.0` are left alone: they cannot run anything, and the Invalid Value column often holds exactly such a number. Counts and hours the app computes itself are not text from the file and are not changed.

## Consequences

- Nothing in the report starts like a formula. This is checked by a unit test and by an end-to-end test that pushes a formula-like customer name all the way through to the report.
- A value that legitimately starts with `-` or `=` shows an extra apostrophe in the report. That is deliberate.
- The apostrophe rule is what spreadsheet applications document; it has not been tested against every spreadsheet version.
