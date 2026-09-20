# 0004. One record per line

Status: accepted (2026-09).

## Context

CSV allows a quoted field to contain a line break, so one record can span several lines. Supporting that means the reader cannot process a line on its own: an unbalanced quote makes the reader consume everything up to the next quote, possibly the rest of the file, before it can say what is wrong.

## Decision

Each line is one record. A quoted field that continues onto the next line is reported: each line of the split record gets a "malformed row" issue that includes its line number. Blank lines are skipped.

A line may be at most 1,000 characters long, not counting the line break (`MAX_LINE_LENGTH` in `src/config.py`). The reader asks for at most that many characters at a time. A longer line becomes one issue ("longer than 1,000 characters") that shows the start of the line (the first 200 characters), the rest is discarded in pieces without being kept, and reading continues with the next line. A header row over the limit refuses the whole file.

## Consequences

- A bad line costs one issue and cannot swallow the rows after it, so line numbers in the report are reliable and the reader can stream a line at a time.
- A valid CSV file that uses multi-line fields will report errors. The upload screen states the rule ("One record per line") next to the format hints.
- A file with no line breaks no longer has to fit in memory: reading stops at `MAX_LINE_LENGTH` regardless of how long the actual line is, instead of the reader consuming the whole line looking for a break that never comes.
- A valid row longer than 1,000 characters is reported as invalid, with the reason "longer than 1,000 characters" rather than the field rules. The longest row that passes every rule without padding is 64 characters (96 if the customer is 30 quote characters, each written doubled), and the generated test files top out at 67 characters (measured), so the limit leaves room for padding, quoting and extra zeros in hours. The row length that real files need is not known, so 1,000 is a chosen value, not a measured one. It is one constant; raising it changes nothing else. An earlier draft used 100; it was raised because padded or fully quoted rows could exceed it.
- A line over the limit is not parsed, so its ticket ID is not checked for duplicates: it is reported for its length, not for anything else it contains.
