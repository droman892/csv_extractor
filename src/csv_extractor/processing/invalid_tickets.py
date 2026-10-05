"""Keeping the invalid tickets of a large file on disk instead of in memory.

A file where most rows are bad can have millions of invalid tickets, each
with several errors. Holding them all in memory does not scale, so the
processor can write each one to a file as it finds it (JSON Lines: one
ticket per line) and the report reads them back one at a time.
"""

import json
from collections.abc import Generator
from pathlib import Path
from typing import TextIO

from ..records import InvalidTicket, ProcessingResult


def open_for_writing(path: str | Path) -> TextIO:
    # "x" refuses to open a file that already exists.
    return open(path, "x", encoding="utf-8", newline="\n")


def write_invalid_ticket(file: TextIO, ticket: InvalidTicket) -> None:
    line = {
        "ticket_id": ticket["ticket_id"],
        "errors": ticket.get("errors", [])
    }

    # ensure_ascii (the default) keeps every line free of raw newlines and
    # unusual characters. default=str means an odd value can never abort a
    # long run.
    file.write(
        json.dumps(line, separators=(",", ":"), default=str)
    )
    file.write("\n")


def read_invalid_tickets(
    path: str | Path
) -> Generator[InvalidTicket, None, None]:
    try:
        file = open(path, encoding="utf-8")
    except FileNotFoundError as error:
        raise ValueError(
            "The list of invalid tickets is no longer available."
        ) from error

    with file:
        for line in file:
            yield json.loads(line)


def iter_invalid_tickets(
    result: ProcessingResult
) -> Generator[InvalidTicket, None, None]:
    """Every invalid ticket of a result, wherever it is stored.

    This is a generator so that it can be closed early (see
    contextlib.closing), which closes the file it is reading.
    """
    path = result.get("invalid_details_path")

    if path is None:
        yield from result["invalid_records"]
    else:
        yield from read_invalid_tickets(path)
