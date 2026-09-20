import pytest
from src.processing.aggregation import (
    create_aggregation,
    add_valid_record
)
from src.processing.rules import PRIORITIES, STATUSES


def aggregate(records):
    summary = create_aggregation()

    for record in records:
        add_valid_record(summary, record)

    return summary


@pytest.fixture
def valid_records():
    return [
        {
            "ticket_id": "000001001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": 2.5
        },
        {
            "ticket_id": "000001002",
            "customer": "Globex",
            "priority": "low",
            "status": "closed",
            "hours": 1.0
        },
        {
            "ticket_id": "000001004",
            "customer": "Initech",
            "priority": "high",
            "status": "closed",
            "hours": 4.5
        },
        {
            "ticket_id": "000001005",
            "customer": "Globex",
            "priority": "high",
            "status": "open",
            "hours": 2.0
        }
    ]


def test_aggregation_groups_tickets_by_status(valid_records):
    result = aggregate(valid_records)

    assert result["tickets_by_status"] == {
        "open": 2,
        "closed": 2,
        "in_progress": 0
    }


def test_aggregation_groups_tickets_by_priority(valid_records):
    result = aggregate(valid_records)

    assert result["tickets_by_priority"] == {
        "low": 1,
        "medium": 0,
        "high": 3
    }


def test_aggregation_sums_hours_by_customer(valid_records):
    result = aggregate(valid_records)

    assert result["hours_by_customer"] == {
        "Acme Corp": 2.5,
        "Globex": 3.0,
        "Initech": 4.5
    }


def test_aggregation_calculates_total_hours(valid_records):
    result = aggregate(valid_records)

    assert result["total_hours"] == 10.0


def test_aggregation_handles_empty_records():
    result = aggregate([])

    assert result == {
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


def test_create_aggregation_has_a_counter_for_every_rule_value():
    summary = create_aggregation()

    assert list(summary["tickets_by_status"]) == list(STATUSES)
    assert list(summary["tickets_by_priority"]) == list(PRIORITIES)
