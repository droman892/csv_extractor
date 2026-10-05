from typing import cast

from ..records import Summary, TicketRecord
from .rules import PRIORITIES, STATUSES


def create_aggregation() -> Summary:

    return {
        "tickets_by_status": {
            status: 0 for status in STATUSES
        },

        "tickets_by_priority": {
            priority: 0 for priority in PRIORITIES
        },

        "hours_by_customer": {},

        "total_hours": 0
    }


def add_valid_record(summary: Summary, row: TicketRecord) -> None:

    summary["tickets_by_status"][
        row["status"]
    ] += 1

    summary["tickets_by_priority"][
        row["priority"]
    ] += 1

    customer = row["customer"]
    # A valid record always has its hours.
    hours = cast(float, row["hours"])

    if customer not in summary["hours_by_customer"]:
        summary["hours_by_customer"][customer] = hours
    else:
        summary["hours_by_customer"][customer] += hours

    summary["total_hours"] += hours
