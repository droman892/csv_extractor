from .csv_reader import read_csv
from .validation import check_rows
from .aggregation import aggregate_csv

def process_csv(filename):
    raw_rows = read_csv(filename)
    processed_rows = check_rows(raw_rows)
    summary = aggregate_csv(processed_rows["valid_records"])

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