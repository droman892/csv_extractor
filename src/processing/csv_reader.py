import csv
from collections.abc import Iterator
from pathlib import Path
from typing import TextIO

from ..config import MAX_DATA_ROWS, MAX_LINE_LENGTH
from ..records import RawRow


REQUIRED_COLUMNS: set[str] = {
    "ticket_id",
    "status",
    "priority",
    "customer",
    "hours",
}

# When the rest of an over-long line is thrown away, it is read in pieces
# of this size, so memory use does not depend on how long the line is.
SKIP_CHUNK_SIZE: int = 64 * 1024


def read_csv(filename: str | Path) -> Iterator[RawRow]:
    """Yield one dict per data line of the CSV file.

    The application handles one record per line: a line is never joined
    with the next one. Blank lines are skipped. A bad line is not raised
    as an error; it is yielded with a "_csv_error" key so the caller can
    report it. That includes a line longer than MAX_LINE_LENGTH: only
    its first MAX_LINE_LENGTH characters are kept.
    """
    with open(
        filename,
        mode="r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        # Two extra characters leave room for a "\r\n" line break.
        header_line = file.readline(MAX_LINE_LENGTH + 2)

        if not header_line:
            raise ValueError(
                "CSV file does not contain a header row."
            )

        if len(header_line.rstrip("\r\n")) > MAX_LINE_LENGTH:
            raise ValueError(
                f"The header row is longer than "
                f"{MAX_LINE_LENGTH:,} characters."
            )

        header_reader = csv.reader(
            [header_line],
            strict=True
        )

        try:
            fieldnames = next(
                header_reader,
                None
            )
        except csv.Error as error:
            raise ValueError(
                f"CSV file is malformed: {error}"
            ) from error

        fieldnames = validate_columns(fieldnames)

        lines = read_lines(file)

        for row_number, (line, too_long) in enumerate(lines, start=1):
            if row_number > MAX_DATA_ROWS:
                raise ValueError(
                    f"CSV cannot contain more than "
                    f"{MAX_DATA_ROWS:,} data rows"
                )

            if too_long:
                yield create_malformed_row(
                    fieldnames,
                    line[:MAX_LINE_LENGTH],
                    (
                        f"Line {row_number + 1}: longer than "
                        f"{MAX_LINE_LENGTH:,} characters "
                        f"(the rest of the line was not read)"
                    )
                )
                continue

            # Blank lines are not records.
            if not line.strip():
                continue

            # The header is line 1, so the first data row is line 2.
            yield parse_row(
                fieldnames,
                line,
                row_number + 1
            )


def read_lines(file: TextIO) -> Iterator[tuple[str, bool]]:
    """Yield (line, too_long) for every line, holding one line at a time.

    A line longer than MAX_LINE_LENGTH is not read into memory. Only its
    first part is returned, with too_long set, and the rest is discarded.
    """
    while True:
        # Two extra characters leave room for a "\r\n" line break.
        line = file.readline(MAX_LINE_LENGTH + 2)

        if not line:
            return

        if len(line.rstrip("\r\n")) <= MAX_LINE_LENGTH:
            yield line, False
            continue

        skip_rest_of_line(file, line)

        yield line, True


def skip_rest_of_line(file: TextIO, piece: str) -> None:
    """Discard what is left of the line that `piece` is the start of."""
    while piece and not piece.endswith("\n"):
        if piece.endswith("\r"):
            # Either a line break of its own, or the first half of
            # "\r\n". Take the "\n" if it is there; otherwise the
            # character belongs to the next line, so put it back.
            position = file.tell()

            if file.read(1) != "\n":
                file.seek(position)

            return

        piece = file.readline(SKIP_CHUNK_SIZE)


def parse_row(
    fieldnames: list[str],
    line: str,
    line_number: int | None = None
) -> RawRow:
    # One record per line: a quoted field cannot continue onto the next
    # line, so each line of such a record is reported as malformed.
    where = f"Line {line_number}: " if line_number else ""

    if has_malformed_quote(line):
        return create_malformed_row(
            fieldnames,
            line,
            (
                f"{where}unbalanced or misplaced quote "
                f"(each record must be on a single line)"
            )
        )

    reader = csv.reader(
        [line],
        strict=True
    )

    try:
        values = next(
            reader,
            []
        )
    except csv.Error:
        return create_malformed_row(
            fieldnames,
            line,
            f"{where}malformed CSV row"
        )

    if len(values) != len(fieldnames):
        return create_malformed_row(
            fieldnames,
            line,
            (
                f"{where}expected {len(fieldnames)} fields, "
                f"found {len(values)}"
            )
        )

    return dict(
        zip(
            fieldnames,
            values
        )
    )


def has_malformed_quote(line: str) -> bool:
    in_quotes = False
    field_start = True
    index = 0

    line = line.rstrip("\r\n")

    while index < len(line):
        character = line[index]

        if character == '"':

            if in_quotes:
                if (
                    index + 1 < len(line)
                    and line[index + 1] == '"'
                ):
                    index += 2
                    continue

                in_quotes = False
                field_start = False

            else:
                if not field_start:
                    return True

                in_quotes = True
                field_start = False

        elif character == ",":
            if not in_quotes:
                field_start = True

        index += 1

    return in_quotes


def create_malformed_row(
    fieldnames: list[str],
    line: str,
    error_message: str
) -> RawRow:
    values = line.rstrip(
        "\r\n"
    ).split(",")

    row = dict(
        zip(
            fieldnames,
            values
        )
    )

    for fieldname in fieldnames:
        if fieldname not in row:
            row[fieldname] = ""

    row["_csv_error"] = error_message
    row["_csv_line"] = shorten(line.rstrip("\r\n"))

    return row


def shorten(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text

    return text[:limit] + "..."


def validate_columns(fieldnames: list[str] | None) -> list[str]:
    if not fieldnames:
        raise ValueError(
            "CSV file does not contain a header row."
        )

    missing_columns = (
        REQUIRED_COLUMNS - set(fieldnames)
    )

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    return fieldnames