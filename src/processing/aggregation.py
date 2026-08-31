def create_aggregation():

    return {
        "tickets_by_status": {
            "open": 0,
            "closed": 0,
            "in_progress": 0
        },

        "tickets_by_priority": {
            "low": 0,
            "medium": 0,
            "high": 0
        },

        "hours_by_customer": {},

        "total_hours": 0
    }


def add_valid_record(summary, row):

    summary["tickets_by_status"][
        row["status"]
    ] += 1

    summary["tickets_by_priority"][
        row["priority"]
    ] += 1

    customer = row["customer"]
    hours = row["hours"]

    if customer not in summary["hours_by_customer"]:
        summary["hours_by_customer"][customer] = hours
    else:
        summary["hours_by_customer"][customer] += hours

    summary["total_hours"] += hours


def aggregate_csv(valid_records):

    summary = create_aggregation()

    for row in valid_records:
        add_valid_record(
            summary,
            row
        )

    return summary