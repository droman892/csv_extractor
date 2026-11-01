# Changelog

## 1.0.0 (2026-11-01)

First release.

- Desktop app (PySide6) that validates a support-ticket CSV against five rules and shows totals, summaries, and the first 100 issues.
- Every row that shares a ticket ID is invalid, not just the second one.
- One record per line, with blank lines skipped and split records reported by line number.
- Lines are limited to 1,000 characters (one constant). A longer line is reported and not read into memory, so a file with no line breaks cannot exhaust memory.
- The upload screen and the missing-columns error list the required columns in the same order. A long filename in an upload error is shortened instead of stretching the message.
- A plain message for files that are not UTF-8, have the wrong columns, or cannot be read.
- A bundled sample file, `demo_data_file.csv`, that the upload screen offers, found the same way from source and from the `.exe`.
- Full report export, listing every issue. Text from the input is neutralized against spreadsheet formulas, and the "valid records only" note is a single cell.
- Processing and export run in a separate process, and invalid tickets are streamed to a temporary file, so memory does not grow with the number of bad rows. Files up to 5,000,000 lines are accepted.
- Temporary result files are JSON, so loading them can never run code.
- Closing the window stops the work and deletes the temporary files.
- Log file that never contains row contents.
- Tests (unit, view, and end-to-end with real processes), mypy type checking, and a dependency vulnerability audit, run by a Windows GitHub Actions workflow.
- Packaged as a single Windows `.exe`, `CSV-Extractor.exe`, built with PyInstaller (`csv_extractor.spec`) from the same entry point as `python -m csv_extractor`.
