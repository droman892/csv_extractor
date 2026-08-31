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

            reader = csv.DictReader(file)

            validate_columns(reader.fieldnames)

            for row in reader:
                yield row

    except csv.Error as error:
        raise ValueError(
            f"CSV file is malformed: {error}"
        ) from error


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