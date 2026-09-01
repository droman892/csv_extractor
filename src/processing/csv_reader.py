import csv


REQUIRED_COLUMNS = {
    "ticket_id",
    "status",
    "priority",
    "customer",
    "hours",
}


def read_csv(filename):
    try:
        with open(
            filename,
            mode="r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            header_line = file.readline()

            if not header_line:
                raise ValueError(
                    "CSV file does not contain a header row."
                )

            header_reader = csv.reader(
                [header_line]
            )

            fieldnames = next(
                header_reader,
                None
            )

            validate_columns(fieldnames)

            for line in file:
                yield parse_row(
                    fieldnames,
                    line
                )

    except csv.Error as error:
        raise ValueError(
            f"CSV file is malformed: {error}"
        ) from error


def parse_row(fieldnames, line):
    if has_unmatched_quote(line):
        row = parse_malformed_row(
            fieldnames,
            line
        )

        row["_csv_error"] = "Malformed quote detected"

        return row

    reader = csv.reader(
        [line]
    )

    values = next(
        reader,
        []
    )

    return dict(
        zip(
            fieldnames,
            values
        )
    )


def has_unmatched_quote(line):
    in_quotes = False
    index = 0

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

            else:
                in_quotes = True

        index += 1

    return in_quotes


def parse_malformed_row(fieldnames, line):
    values = line.rstrip("\r\n").split(",")

    row = dict(
        zip(
            fieldnames,
            values
        )
    )

    for fieldname in fieldnames:
        if fieldname not in row:
            row[fieldname] = ""

    return row


def validate_columns(fieldnames):
    if not fieldnames:
        raise ValueError(
            "CSV file does not contain a header row."
        )

    missing_columns = REQUIRED_COLUMNS - set(fieldnames)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )