import csv

REQUIRED_COLUMNS = {
    "ticket_id",
    "status",
    "priority",
    "customer",
    "hours",
}

def read_csv(filename):
    with open(filename, mode='r', newline='', encoding='utf-8-sig') as file:
        raw_rows = csv.DictReader(file)
        validate_columns(raw_rows.fieldnames)
        return list(raw_rows)

def validate_columns(fieldnames):
    missing_columns = REQUIRED_COLUMNS - set(fieldnames)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )