import time

from .csv_reader import read_csv
from .validation import check_rows
from .aggregation import aggregate_csv
from ..services.results_export_service import ResultsExportService

MAX_DISPLAYED_ROWS = 100

def process_csv(filename):
    start = time.perf_counter()


    read_start = time.perf_counter()
    raw_rows = read_csv(filename)
    read_time = time.perf_counter() - read_start

    validation_start = time.perf_counter()
    processed_rows = check_rows(raw_rows)
    validation_time = time.perf_counter() - validation_start

    aggregation_start = time.perf_counter()
    summary = aggregate_csv(processed_rows["valid_records"])
    aggregation_time = time.perf_counter() - aggregation_start

    full_result = {
        "filename": filename,
        "summary": summary,
        "valid_tickets_count": processed_rows["valid_tickets_count"],
        "invalid_tickets_count": processed_rows["invalid_tickets_count"],
        "total_tickets_count": processed_rows["total_tickets_count"],
        "invalid_records": processed_rows["errors"],
    }

    export_start = time.perf_counter()

    export_file = ResultsExportService.create_export_file(
        full_result
    )

    export_time = time.perf_counter() - export_start

    display_result = {
        "filename": filename,

        "total_tickets_count":
            full_result["total_tickets_count"],

        "valid_tickets_count":
            full_result["valid_tickets_count"],

        "invalid_tickets_count":
            full_result["invalid_tickets_count"],

        "summary": {
            "total_hours":
                summary["total_hours"],

            "tickets_by_status":
                summary["tickets_by_status"],

            "tickets_by_priority":
                summary["tickets_by_priority"],

            "hours_by_customer":
                dict(
                    list(
                        summary["hours_by_customer"].items()
                    )[:MAX_DISPLAYED_ROWS]
                ),
        },

        "invalid_records":
            full_result["invalid_records"][
                :MAX_DISPLAYED_ROWS
            ],

        "total_customer_count":
            len(summary["hours_by_customer"]),

        "total_invalid_record_count":
            len(full_result["invalid_records"]),

        "export_file":
            export_file,
    }

    total_time = time.perf_counter() - start

    print(f"read_csv: {read_time:.3f} seconds")
    print(f"check_rows: {validation_time:.3f} seconds")
    print(f"aggregate_csv: {aggregation_time:.3f} seconds")
    print(f"export_file: {export_time:.3f} seconds")
    print(f"total: {total_time:.3f} seconds")

    return display_result


if __name__ == "__main__":
    print(process_csv("data/empty_file.csv"))
