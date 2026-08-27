# from .csv_reader import read_csv
# from .validation import check_rows
# from .aggregation import aggregate_csv

# def process_csv(filename):
#     raw_rows = read_csv(filename)
#     processed_rows = check_rows(raw_rows)
#     summary = aggregate_csv(processed_rows["valid_records"])

#     result = {
#         "filename": filename,
#         "summary": summary,
#         "valid_tickets_count": processed_rows["valid_tickets_count"],
#         "invalid_tickets_count": processed_rows["invalid_tickets_count"],
#         "total_tickets_count": processed_rows["total_tickets_count"],
#         "invalid_records": processed_rows["errors"]
#     }

#     return result

# if __name__ == "__main__":
#     print(process_csv("data/empty_file.csv"))


import time

from .csv_reader import read_csv
from .validation import check_rows
from .aggregation import aggregate_csv


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

    total_time = time.perf_counter() - start

    print(f"read_csv: {read_time:.3f} seconds")
    print(f"check_rows: {validation_time:.3f} seconds")
    print(f"aggregate_csv: {aggregation_time:.3f} seconds")
    print(f"total: {total_time:.3f} seconds")

    result = {
        "filename": filename,
        "summary": summary,
        "valid_tickets_count": processed_rows["valid_tickets_count"],
        "invalid_tickets_count": processed_rows["invalid_tickets_count"],
        "total_tickets_count": processed_rows["total_tickets_count"],
        "invalid_records": processed_rows["errors"]
    }

    return result


if __name__ == "__main__":
    print(process_csv("data/empty_file.csv"))