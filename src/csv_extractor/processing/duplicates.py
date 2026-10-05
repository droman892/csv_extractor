from pathlib import Path

from .csv_reader import read_csv
from .validation import validate_ticket_id


def find_duplicate_ticket_ids(filename: str | Path) -> dict[str, int]:
    """First pass over the file: find ticket_ids that appear more than once.

    Returns {ticket_id: number_of_times_it_appears} for repeated IDs only,
    so the result is empty for a file with no duplicates.

    Rows whose CSV structure is malformed, and rows whose ticket_id is not
    a valid ID, are not counted: they are already invalid for a more basic
    reason, and their ticket_id text cannot be trusted.

    Memory: this holds every distinct valid ticket_id in a set. The rows
    themselves are never held.
    """
    seen: set[str] = set()
    counts: dict[str, int] = {}

    for row in read_csv(filename):
        if "_csv_error" in row:
            continue

        ticket_id = validate_ticket_id(row["ticket_id"])

        if not ticket_id["valid"]:
            continue

        value = ticket_id["value"]

        if value in seen:
            # The first sighting is already in seen, so a repeat means 2.
            counts[value] = counts.get(value, 1) + 1
        else:
            seen.add(value)

    return counts
