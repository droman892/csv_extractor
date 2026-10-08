# Security notes

CSV Extractor is a local desktop tool. It has no network access, no accounts, no secrets, and no configuration file. What it touches is the files a user chooses, its own temporary files, and its log. This page lists what it protects against, what it does not, and what a reviewer should know. It has not had an independent security review.

## What it protects against

| Risk | What the app does | How it is checked |
| --- | --- | --- |
| **Spreadsheet formula injection.** Text from the input file (customer names, bad values) can start with `=`, `+`, `-`, `@`, tab, or carriage return and run as a formula when the report is opened. | Every text value taken from the input is neutralized with a leading apostrophe before it is written to the report. See [ADR 0006](adr/0006-neutralize-formulas-in-the-export.md). | Unit tests for the function; an end-to-end test that sends a formula-like customer name through the whole path. |
| **Malformed or hostile input.** Broken quotes, wrong field counts, non-UTF-8 bytes, empty files, wrong columns. | Every field is validated; a bad line becomes a reported issue instead of an exception; non-UTF-8 and missing-column files are refused with a plain message. Ticket IDs must be ASCII digits (digits from other scripts are rejected). | Unit tests per rule; end-to-end tests for wrong columns, non-UTF-8, and missing files. |
| **A file with one enormous line** (for example, no line breaks at all). | A line is read at most 1,000 characters at a time. A longer line is reported as one issue and the rest of it is discarded without being held in memory. A header longer than 1,000 characters is refused. See [ADR 0004](adr/0004-one-record-per-line.md). | Unit tests just under, at, and just over the limit with each kind of line break. |
| **Running out of memory on a large file.** | Files are streamed a line at a time; at most 5,000,000 data lines are accepted; invalid tickets go to disk. | Measured; see [ADR 0005](adr/0005-invalid-tickets-go-to-disk.md). |
| **Leaking customer data through the log.** | The log records counts, timings, file names, and errors, never the contents of a row. | Tests read the log file and check that names and IDs are absent. |
| **Temporary files colliding or lingering.** | Random names, created so that an existing file is never overwritten; deleted on failure, stop, going back to the upload screen, and window close. | Unit and end-to-end tests. |
| **A tampered temporary file running code.** Loading a pickle can run code, so a result file someone else could change would be a way in. | Both temporary files are JSON (the summary as one document, the invalid tickets as JSON Lines). Loading JSON only builds data; it never runs code. | Tests save a real result and load it back, and run the export from a saved file. |
| **No third-party calls.** | The source has no network, subprocess, or `eval` calls. | Searched, not proven: a code search, not a formal analysis. |
| **Known vulnerabilities in dependencies.** | `pip-audit` (a dev dependency, `pyproject.toml`) checks installed packages against the PyPI/OSV vulnerability database. | Runs in [CI](../.github/workflows/ci.yml) on every push and pull request to `main`, and fails the build if a known vulnerability is found. It can also be run locally with `python -m pip_audit`. No known vulnerabilities as of 2026-10-07, against the one runtime dependency (PySide6) and the dev tooling (now including PyInstaller, added for [packaging](../README.md#packaging)). |

## What it does not protect against

- **Memory depends on the data.** A file with many distinct customers and valid ticket IDs uses far more memory than one with a few hundred (see [ADR 0003](adr/0003-two-pass-duplicate-detection.md)). There is no memory limit and no check before starting.
- **Reports are not encrypted.** The export is a plain CSV that contains whatever customer data was in the input. Storing and sharing it is up to the user.
- **The log records file names.** A file name can itself be sensitive.
- **Dependency scanning runs only when the code changes.** `pip-audit` reports what was known at the moment CI ran. A vulnerability disclosed after the last push is not caught until the next push. Two ways to close that gap were considered and not set up:
  - *A scheduled CI run* (a weekly `schedule:` trigger in the same workflow). It runs on GitHub's servers whether or not anyone pushes, so a newly disclosed vulnerability is reported within a week. This matters most for software that is deployed and then left alone, which is when nobody pushes and nothing else would notice. GitHub disables scheduled workflows in a public repository after 60 days without activity, so on a quiet project it needs re-enabling.
  - *GitHub Dependabot alerts.* GitHub watches the declared dependencies and notifies the maintainer when a vulnerability is published, and can open a pull request that updates the package. It needs no workflow code and covers the time between pushes. For a team, it puts the alert where the work already happens instead of relying on someone to read a CI log.

  For a tool used by one person, offline, with one runtime dependency, running on every push is proportionate. Either option becomes worth setting up once the app is distributed to other people, since a vulnerable release then stays on their machines after the code stops changing.
- **The formula rule is tested with the rule, not with each spreadsheet program.** The leading apostrophe is the documented approach; the behavior in every version of Excel, Google Sheets, and LibreOffice has not been tested.
- **The packaged `.exe` is not code-signed.** Windows SmartScreen will warn about it on another machine, and there is no way for someone who downloads it to verify it was built from this source without rebuilding it themselves (see [Packaging](../README.md#packaging)). Signing costs money (a code-signing certificate) and is not set up.

## Data in this repository

The files in `data/` are test files, generated by `scripts/generate_test_data.py` from a list of fictional company names or written by hand to exercise error cases. They are not meant to contain real customer data, and real data should not be added.

## Reporting a problem

Open an issue on the GitHub repository. Please do not include real customer data or credentials in an issue.
