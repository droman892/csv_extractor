# Changelog

## 0.1.0 (unreleased)

First release.

- Desktop app (PySide6) that validates a support-ticket CSV against five rules and shows totals, summaries and the first 100 issues.
- Every row that shares a ticket ID is invalid, not just the second one.
- One record per line; blank lines are skipped and split records are reported by line number.
- Lines are limited to 1,000 characters (one constant). A longer line is reported and not read into memory, so a file with no line breaks can no longer exhaust memory.
- Full report export: every issue is listed. Text from the input is neutralized against spreadsheet formulas.
- Processing and export run in a separate process; invalid tickets are streamed to a temporary file, so memory does not grow with the number of bad rows. Files up to 5,000,000 lines are accepted.
- Closing the window stops the work and deletes the temporary files.
- A plain message for files that are not UTF-8, have the wrong columns, or cannot be read.
- Log file that never contains row contents.
- Tests (unit, view and end-to-end with real processes), mypy type checking and a Windows GitHub Actions workflow.
