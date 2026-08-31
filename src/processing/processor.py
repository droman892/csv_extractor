from .csv_reader import read_csv
from .validation import validate_row
from .aggregation import (
    create_aggregation,
    add_valid_record
)


def process_csv(filename):
    summary = create_aggregation()

    invalid_records = []

    valid_tickets_count = 0
    invalid_tickets_count = 0
    total_tickets_count = 0
    total_validation_error_count = 0

    for raw_row in read_csv(filename):

        validation_result = validate_row(
            raw_row
        )

        total_tickets_count += 1

        if validation_result["valid"]:

            add_valid_record(
                summary,
                validation_result["record"]
            )

            valid_tickets_count += 1

        else:

            invalid_records.append(
                validation_result["record"]
            )

            invalid_tickets_count += 1

            total_validation_error_count += (
                validation_result["error_count"]
            )

    return {
        "filename": filename,

        "summary": summary,

        "valid_tickets_count":
            valid_tickets_count,

        "invalid_tickets_count":
            invalid_tickets_count,

        "total_tickets_count":
            total_tickets_count,

        "total_validation_error_count":
            total_validation_error_count,

        "invalid_records":
            invalid_records
    }