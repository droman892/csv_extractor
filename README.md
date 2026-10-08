# CSV Extractor

[![CI](https://github.com/droman892/csv_extractor/actions/workflows/ci.yml/badge.svg)](https://github.com/droman892/csv_extractor/actions/workflows/ci.yml)

A Windows desktop app that checks a support-ticket CSV file against a fixed set of rules, tells you exactly which rows are wrong and why, and exports a report. It handles files of up to 5 million rows without freezing the window.

**[Download CSV-Extractor.exe](https://github.com/droman892/csv_extractor/releases/latest/download/CSV-Extractor.exe)** — no Python install needed. It is not code-signed (see [Packaging](#packaging)), so Windows SmartScreen will warn on first run; if you'd rather not run an unsigned binary from the internet, build it yourself with the steps below.

## The problem

Support teams get ticket exports as CSV files: from a help desk, a vendor, or a spreadsheet someone edited by hand. Before the data can be used for billing, reporting, or import into another system, someone has to find the rows that are wrong: a misspelled status, hours that make no sense, a ticket ID used twice. In a spreadsheet that means filters, formulas, and eyeballing, and past a few hundred thousand rows the spreadsheet stops opening at all.

CSV Extractor does that check the same way every time and shows the result in one screen. See [docs/business-case.md](docs/business-case.md) for who it is for, what is measured, and what is only assumed.

## What it does

- Checks every row against the [rules below](#the-rules) and lists each problem with the ticket, the field, the bad value, and the reason.
- Treats a ticket ID that appears more than once as an error on **every** row that uses it, not just the second one.
- Summarizes the valid rows: tickets by status, tickets by priority, and hours by customer.
- Exports the full report as a CSV file. Every problem is listed, however many there are.
- Keeps the window responsive on large files: the work runs in a separate process.
- Closing the window stops the work and deletes the temporary files.

## Demo

_Screenshots and a walkthrough video are to be added._

<!--
When the screenshots exist, put them in docs/images/ and replace the line above with:

| Upload | Results | Exported report |
| --- | --- | --- |
| ![Upload screen](docs/images/upload.png) | ![Results screen](docs/images/results.png) | ![Report opened in a spreadsheet](docs/images/report.png) |

Video: add the real link here once it exists.
-->

## The rules

| Column | Rule |
| --- | --- |
| `ticket_id` | Exactly 9 digits (0-9). Must appear only once in the file. |
| `customer` | Required, up to 30 characters. |
| `priority` | `low`, `medium`, or `high`. |
| `status` | `open`, `closed`, or `in_progress`. |
| `hours` | A number from 0.5 to 40, in steps of 0.5. |

The file must be UTF-8 (a leading byte-order mark is fine), have a header row with all five columns, and hold one record per line of at most 1,000 characters. Blank lines are skipped.

Extra columns beyond the five are allowed and ignored: they are not validated, summarized, or exported. The 1,000-character limit is a memory safeguard, not a format rule. A valid row with only the five columns is about 65 characters. The limit leaves room for extra columns, padding, and quoting, and stops a file with no line breaks from being read into memory as one huge line. The rules live in one file, [`src/csv_extractor/processing/rules.py`](src/csv_extractor/processing/rules.py), and the format hints on the upload screen are generated from it.

## Getting started

You need Python 3.11 or newer and Windows. The app is developed on Windows with Python 3.13.

```powershell
git clone https://github.com/droman892/csv_extractor.git
cd csv_extractor
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m csv_extractor
```

`pip install -e ".[dev]"` installs PySide6 plus the test and type-checking tools, all listed in [`pyproject.toml`](pyproject.toml). The editable install (`-e`) points Python at `src/csv_extractor`, so code changes take effect without reinstalling.

## Using it

1. Click **Upload CSV File** and choose a file. To try it first, click the **demo_data.csv** link on the upload screen to save a sample file, then upload that.
2. Wait for the results screen. It shows the totals, the two summary tables, hours by customer (first 100 customers, alphabetical), and the first 100 validation issues.
3. Click **Export Results** to save the full report as a CSV file. Click **Upload Another File** to start over.

To make a large test file: `python scripts/generate_test_data.py --rows 1000000 --customers 150 --output data/my_test.csv`. About 20% of the rows it writes are deliberately invalid.

## Tests and type checking

```powershell
python -m pytest
python -m mypy
```

The tests cover each layer on its own, the window and views with pytest-qt, and the whole path end to end with real background processes (`tests/test_pipeline.py`). The same two commands run on every push in [GitHub Actions](.github/workflows/ci.yml), and again locally before every push if you opt into the pre-push hook: `git config core.hooksPath .githooks` (one-time, per clone; see [`.githooks/pre-push`](.githooks/pre-push)).

Dependencies are checked for known vulnerabilities with [`pip-audit`](https://pypi.org/project/pip-audit/) (a dev dependency): `python -m pip_audit`. CI runs it on every push and pull request to `main`; see [docs/security.md](docs/security.md) for what that does and does not catch.

## Packaging

```powershell
python -m pip install -e ".[dev]"
python -m PyInstaller csv_extractor.spec
```

This builds `dist\CSV-Extractor.exe`: a single file with Python, PySide6, and the sample CSV bundled in, so it runs on a Windows machine with no Python install. [`csv_extractor.spec`](csv_extractor.spec) drives the build, starting from the same entry point as `python -m csv_extractor` ([`src/csv_extractor/__main__.py`](src/csv_extractor/__main__.py)).

Notes:

- It is a one-file build, so each launch unpacks to a temp folder first; start-up is a couple of seconds slower than running from source.
- The background processes described [below](#how-it-works) are the packaged `.exe` re-launching itself, handled by `multiprocessing.freeze_support()` at the start of `main()`.
- The `.exe` is not code-signed, so Windows SmartScreen will warn on first run on another machine; see [docs/security.md](docs/security.md).

The [download link above](#csv-extractor) points at `releases/latest/download/CSV-Extractor.exe`, a fixed URL GitHub resolves to the newest release's matching asset. Cutting a release: attach `dist\CSV-Extractor.exe` to a new GitHub release. The file name must stay exactly that for the link to work.

## Logs

The app writes a log to `%LOCALAPPDATA%\csv_extractor\logs\csv_extractor.log`. It records counts, timings, file names, and errors. It never records the contents of a row.

| Environment variable | Effect |
| --- | --- |
| `CSV_EXTRACTOR_LOG_LEVEL` | `INFO` (default), `WARNING`, or `ERROR`; an unknown value falls back to `INFO` |
| `CSV_EXTRACTOR_LOG_FILE` | Full path to use for the log file instead |

## How it works

The window never does the heavy work itself. A worker starts a separate process that reads the file twice (first to find repeated ticket IDs, then to validate each row), streams every invalid ticket to a temporary file, and saves the summary. Only the small part the screen needs comes back through a queue. The export reads those temporary files and writes the report one ticket at a time, so memory use does not grow with the number of bad rows.

- [docs/architecture.md](docs/architecture.md): layers, data flow, and process model
- [docs/adr/](docs/adr/README.md): the design decisions and what each one cost
- [docs/security.md](docs/security.md): what is protected, what is not
- [docs/business-case.md](docs/business-case.md): the case for the tool, with measured and assumed numbers kept apart

## Limitations

- Windows is the supported platform. The code has no Windows-only parts except one optional error beep, and the tests run on Linux, but nothing else has been tried.
- One record per line. A quoted field that continues onto the next line is reported as a malformed row.
- A line may be at most 1,000 characters (`MAX_LINE_LENGTH` in [`src/csv_extractor/config.py`](src/csv_extractor/config.py)). A longer line is reported as one issue and its rest is not read; a longer header row refuses the file. A valid row is about 65 characters.
- At most 5,000,000 data lines per file (`MAX_DATA_ROWS` in [`src/csv_extractor/config.py`](src/csv_extractor/config.py)).
- Peak memory depends on the data: see the worst case above. A file that has millions of distinct customers needs more than one with a few hundred.
- A report with more than 1,048,576 rows cannot be opened completely in Excel. The CSV itself is complete.
- There is no cancel button. Closing the window is the only way to stop a run.
- Packaged as a portable `.exe` (see [Packaging](#packaging)), not an installer. It needs no install and no admin rights and writes nothing to the registry. The trade-off: there is no Start menu entry or uninstaller, and the log folder in `%LOCALAPPDATA%\csv_extractor` stays behind when the `.exe` is deleted.
- The results screen shows the first 100 issues and 100 customers only; the export has all of them.

## License

[MIT](LICENSE). The app depends on PySide6, which has its own license terms; read them before distributing a bundled build.
