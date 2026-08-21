from .csv_reader import read_csv
from .validation import check_rows
from .aggregation import aggregate_csv


def process_csv(filename):
    raw_rows = read_csv(filename)
    processed_rows = check_rows(raw_rows)
    summary = aggregate_csv(processed_rows["valid_records"])
    return summary


if __name__ == "__main__":
    print(process_csv("data/test_data.csv"))