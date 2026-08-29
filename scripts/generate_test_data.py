"""
Generate CSV test data.

Example:
python scripts/generate_test_data.py --rows 2000000 --customers 150 --output data/2m_test_data.csv
"""

import argparse
import csv
import random


CUSTOMERS = [
    "Acme",
    "Globex",
    "Initech",
    "Umbrella",
    "Stark Industries",
    "Wayne Enterprises",
    "Cyberdyne Systems",
    "Wonka Industries",
    "Hooli",
    "Vandelay Industries",
    "Oceanic Airlines",
    "Tyrell Corporation",
    "Massive Dynamic",
    "Soylent Corp",
    "Gringotts",
    "Prestige Worldwide",
    "Duff Brewing",
    "Monarch Solutions",
    "Oscorp",
    "LexCorp",
    "Aperture Labs",
    "Black Mesa",
    "Weyland-Yutani",
    "Nakatomi Corporation",
    "Vehement Capital",
    "Dunder Mifflin",
    "Sterling Cooper",
    "Pied Piper",
    "Gekko & Co",
    "Wonka Chocolate",
    "Cyberdyne Industries",
    "Roxxon",
    "Umbrella Health",
    "Stark Technologies",
    "Wayne Financial",
    "Queen Consolidated",
    "Grayson Industries",
    "Kord Industries",
    "Lexington Labs",
    "Hooli Ventures",
    "Monarch Industries",
    "Massive Dynamics",
    "Tyrell Industries",
    "Oceanic Logistics",
    "Acme Logistics",
    "Globex Solutions",
    "Initech Systems",
    "Vandelay Imports",
    "Wonka Foods",
    "Oscorp Industries",
    "Aperture Systems",
    "Black Mesa Research",
    "Weyland Industries",
    "Nakatomi Holdings",
    "Dunder Mifflin Paper",
    "Sterling Cooper Media",
    "Pied Piper Technologies",
    "Roxxon Energy",
    "Queen Industries",
    "Wayne Medical",
    "Stark Logistics",
    "LexCorp Financial",
    "Kord Enterprises",
    "Grayson Technologies",
    "Queen Consolidated Labs",
    "Acme Manufacturing",
    "Globex Manufacturing",
    "Initech Consulting",
    "Umbrella Pharmaceuticals",
    "Stark Manufacturing",
    "Wayne Construction",
    "Cyberdyne Robotics",
    "Wonka Confectionery",
    "Hooli Communications",
    "Vandelay Trading",
    "Oceanic Travel",
    "Tyrell Research",
    "Massive Dynamic Labs",
    "Soylent Foods",
    "Gringotts Financial",
    "Prestige Worldwide Media",
    "Duff Distribution",
    "Monarch Financial",
    "Oscorp Research",
    "Aperture Robotics",
    "Black Mesa Technologies",
    "Weyland-Yutani Logistics",
    "Nakatomi Security",
    "Vehement Holdings",
    "Dunder Mifflin Logistics",
    "Sterling Cooper Advertising",
    "Pied Piper Software",
    "Gekko Investments",
    "Roxxon Pharmaceuticals",
    "Umbrella Research",
    "Stark Defense",
    "Wayne Technologies",
    "Queen Consolidated Energy",
    "Kord Financial",
    "Grayson Holdings",
    "Lexington Technologies",
    "Hooli Software",
    "Monarch Research",
    "Massive Dynamic Security",
    "Tyrell Robotics",
    "Oceanic Shipping",
    "Acme Technologies",
    "Globex International",
    "Initech Digital",
    "Umbrella Medical",
    "Stark Energy",
    "Wayne Aerospace",
    "Cyberdyne Research",
    "Wonka Foods International",
    "Hooli Media",
    "Vandelay Textiles",
    "Oceanic Shipping",
    "Tyrell Biotech",
    "Massive Dynamic Analytics",
    "Soylent Nutrition",
    "Gringotts Banking",
    "Prestige Worldwide Entertainment",
    "Duff Beverages",
    "Monarch Technology",
    "Oscorp Medical",
    "Aperture Science",
    "Black Mesa Security",
    "Weyland Aerospace",
    "Nakatomi Development",
    "Vehement Technologies",
    "Dunder Mifflin Consulting",
    "Sterling Cooper Partners",
    "Pied Piper Networks",
    "Gekko Capital",
    "Roxxon Industries",
    "Queen Consolidated Technologies",
    "Wayne Enterprises International",
    "Stark Industries International",
    "LexCorp Technologies",
    "Kord Industries International",
    "Grayson Financial",
    "Hooli Cloud",
    "Monarch Global",
    "Massive Dynamic International",
    "Tyrell Corporation International",
    "Acme Global",
    "Globex Corporation International",
    "Initech Global",
    "Umbrella Global",
    "Cyberdyne Global"
]

PRIORITIES = [
    "low",
    "medium",
    "high",
]

STATUSES = [
    "open",
    "closed",
    "in_progress",
]


def generate_valid_row(ticket_id, customers):
    return {
        "ticket_id": f"{ticket_id:09d}",
        "customer": random.choice(customers),
        "priority": random.choice(PRIORITIES),
        "status": random.choice(STATUSES),
        "hours": f"{random.randint(0, 80) / 2:.1f}",
    }


def generate_invalid_row(ticket_id, customers):
    row = generate_valid_row(
        ticket_id,
        customers,
    )

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


def generate_dataset(
    row_count,
    output_file,
    seed,
    customer_count,
):
    if customer_count > len(CUSTOMERS):
        raise ValueError(
            f"customer count cannot exceed "
            f"{len(CUSTOMERS)}"
        )

    random.seed(seed)

    customers = CUSTOMERS[:customer_count]

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

        for ticket_number in range(row_count):
            ticket_id = ticket_number % 10000

            if random.random() < 0.20:
                row = generate_invalid_row(
                    ticket_id,
                    customers,
                )
            else:
                row = generate_valid_row(
                    ticket_id,
                    customers,
                )

            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate CSV Extractor test data."
        )
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=1000,
        help=(
            "Number of CSV records to generate."
        ),
    )

    parser.add_argument(
        "--customers",
        type=int,
        default=150,
        help=(
            "Number of unique customers to use."
        ),
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
        help=(
            "Random seed for reproducible "
            "test data."
        ),
    )

    args = parser.parse_args()

    if args.rows <= 0:
        raise ValueError(
            "rows must be greater than 0"
        )

    if args.customers <= 0:
        raise ValueError(
            "customers must be greater than 0"
        )

    if args.customers > len(CUSTOMERS):
        raise ValueError(
            f"customers cannot exceed "
            f"{len(CUSTOMERS)}"
        )

    generate_dataset(
        args.rows,
        args.output,
        args.seed,
        args.customers,
    )

    print(
        f"Generated {args.rows:,} rows "
        f"with {args.customers:,} customers "
        f"in {args.output}"
    )


if __name__ == "__main__":
    main()