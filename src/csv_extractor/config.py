"""Limits that apply across the application."""

# The most data lines (after the header) a file may contain.
MAX_DATA_ROWS: int = 5_000_000

# The longest a single line may be, not counting the line break. A valid
# ticket row is at most about 100 characters even when quoted, so this
# leaves plenty of room for padding. Longer lines are reported, not read:
# without a limit, a file with no line breaks would be read as one line,
# all of it into memory.
MAX_LINE_LENGTH: int = 1000

# How many customers and validation issues the results screen shows.
# The exported report is not limited by this.
MAX_DISPLAYED_ROWS: int = 100
