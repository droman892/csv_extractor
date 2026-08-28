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
            content = file.read()

        validate_csv_quotes(content)

        raw_rows = csv.DictReader(
            content.splitlines()
        )

        validate_columns(raw_rows.fieldnames)

        return list(raw_rows)

    except csv.Error as error:
        raise ValueError(
            f"CSV file is malformed: {error}"
        ) from error


def validate_csv_quotes(content):
    in_quotes = False
    index = 0

    while index < len(content):
        character = content[index]

        if character == '"':
            if in_quotes:
                if index + 1 < len(content) and content[index + 1] == '"':
                    index += 2
                    continue

                in_quotes = False
            else:
                in_quotes = True

        index += 1

    if in_quotes:
        raise ValueError(
            "CSV file is malformed — an opening quote does not have a matching closing quote."
        )


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