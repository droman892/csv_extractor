import argparse
import csv
import random


CUSTOMERS = [
    "Acme",
    "Globex",
    "Initech",
    "Umbrella",
    "Stark Industries",
]

PRIORITIES = ["low", "medium", "high"]

STATUSES = ["open", "closed", "in_progress"]


def generate_valid_row(ticket_id):
    return {
        "ticket_id": f"{ticket_id:04d}",
        "customer": random.choice(CUSTOMERS),
        "priority": random.choice(PRIORITIES),
        "status": random.choice(STATUSES),
        "hours": f"{random.randint(0, 80) / 2:.1f}",
    }


def generate_invalid_row(ticket_id):
    row = generate_valid_row(ticket_id)

    invalid_type = random.choice([
        "ticket_id",
        "customer",
        "priority",
        "status",
        "hours",
        "multiple",
    ])

    if invalid_type == "ticket_id":
        row["ticket_id"] = random.choice([
            "",
            "ABC1",
            "123",
            "12345",
        ])

    elif invalid_type == "customer":
        row["customer"] = ""

    elif invalid_type == "priority":
        row["priority"] = "urgent"

    elif invalid_type == "status":
        row["status"] = "pending"

    elif invalid_type == "hours":
        row["hours"] = random.choice([
            "-2",
            "41",
            "abc",
            "1.25",
        ])

    elif invalid_type == "multiple":
        row["ticket_id"] = "ABC1"
        row["priority"] = "urgent"
        row["status"] = "pending"
        row["hours"] = "-2"

    return row


def generate_dataset(row_count, output_file, seed):
    random.seed(seed)

    rows = []

    for ticket_number in range(row_count):
        ticket_id = ticket_number % 10000

        if random.random() < 0.20:
            row = generate_invalid_row(ticket_id)
        else:
            row = generate_valid_row(ticket_id)

        rows.append(row)

    with open(
        output_file,
        mode="w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "ticket_id",
                "customer",
                "priority",
                "status",
                "hours",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Generate CSV Extractor test data."
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=1000,
        help="Number of CSV records to generate.",
    )

    parser.add_argument(
        "--output",
        default="data/large_test_data.csv",
        help="Output CSV file.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible test data.",
    )

    args = parser.parse_args()

    if args.rows <= 0:
        raise ValueError("rows must be greater than 0")

    generate_dataset(
        args.rows,
        args.output,
        args.seed,
    )

    print(
        f"Generated {args.rows} rows in {args.output}"
    )


if __name__ == "__main__":
    main()