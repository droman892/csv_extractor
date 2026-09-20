import pytest

from src.processing import rules
from src.processing.validation import (
    validate_ticket_id,
    validate_customer,
    validate_priority,
    validate_status,
    validate_hours
)


# These tests tie rules.py to the validators, so changing a rule in one
# place cannot silently leave the other (or the upload screen) behind.


def test_ticket_id_length_matches_validation():
    assert validate_ticket_id("1" * rules.TICKET_ID_LENGTH)["valid"]
    assert not validate_ticket_id(
        "1" * (rules.TICKET_ID_LENGTH - 1)
    )["valid"]
    assert not validate_ticket_id(
        "1" * (rules.TICKET_ID_LENGTH + 1)
    )["valid"]


def test_customer_length_matches_validation():
    assert validate_customer("x" * rules.MAX_CUSTOMER_LENGTH)["valid"]
    assert not validate_customer(
        "x" * (rules.MAX_CUSTOMER_LENGTH + 1)
    )["valid"]


@pytest.mark.parametrize("priority", rules.PRIORITIES)
def test_every_listed_priority_is_valid(priority):
    assert validate_priority(priority)["valid"]


@pytest.mark.parametrize("status", rules.STATUSES)
def test_every_listed_status_is_valid(status):
    assert validate_status(status)["valid"]


def test_hours_limits_and_step_match_validation():
    assert validate_hours(str(rules.MIN_HOURS))["valid"]
    assert validate_hours(str(rules.MAX_HOURS))["valid"]

    assert not validate_hours(str(rules.MIN_HOURS - rules.HOURS_STEP))["valid"]
    assert not validate_hours(str(rules.MAX_HOURS + rules.HOURS_STEP))["valid"]
    assert not validate_hours(
        str(rules.MIN_HOURS + rules.HOURS_STEP / 2)
    )["valid"]


def test_format_hints_describe_the_current_rules():
    hints = dict(rules.format_hints())

    assert list(hints) == [
        "ticket_id",
        "customer",
        "priority",
        "status",
        "hours"
    ]

    assert hints["ticket_id"] == "Exactly 9 digits"
    assert "30" in hints["customer"]
    assert hints["priority"] == "low, medium, or high"
    assert hints["status"] == "open, closed, or in_progress"
    assert hints["hours"] == "0.5\u201340, in increments of 0.5"


def test_format_note_states_the_one_record_per_line_and_length_rules():
    assert "One record per line" in rules.FORMAT_NOTE
    assert "1,000 characters" in rules.FORMAT_NOTE


def test_valid_records_note_is_safe_to_write_as_a_plain_line():
    # The export writes it without CSV quoting, so it must not contain
    # anything that quoting exists to protect.
    assert '"' not in rules.VALID_RECORDS_NOTE
    assert "\n" not in rules.VALID_RECORDS_NOTE
    assert "\r" not in rules.VALID_RECORDS_NOTE
