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

            validate_columns(fieldnames)

            for line in file:
                yield parse_row(
                    fieldnames,
                    line
                )

    except OSError:
        raise


def parse_row(fieldnames, line):
    if has_malformed_quote(line):
        return create_malformed_row(
            fieldnames,
            line,
            "Malformed quote detected"
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
            "Malformed CSV row"
        )

    if len(values) != len(fieldnames):
        return create_malformed_row(
            fieldnames,
            line,
            (
                f"Expected {len(fieldnames)} fields, "
                f"found {len(values)}"
            )
        )

    return dict(
        zip(
            fieldnames,
            values
        )
    )


def has_malformed_quote(line):
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
    fieldnames,
    line,
    error_message
):
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

    return row


def validate_columns(fieldnames):
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