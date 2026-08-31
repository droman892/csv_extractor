import pytest
from src.processing.validation import (
    validate_ticket_id,
    validate_customer,
    validate_priority,
    validate_status,
    validate_hours,
    check_rows
)


@pytest.fixture
def valid_row():
    return {
        "ticket_id": "000001001",
        "customer": "Acme Corp",
        "priority": "high",
        "status": "open",
        "hours": "2.5"
    }


# -------------------------------------------------------------------
# check_rows tests
# -------------------------------------------------------------------


def test_check_rows_accepts_valid_row(valid_row):
    result = check_rows([valid_row])

    assert len(result["valid_records"]) == 1
    assert len(result["errors"]) == 0
    assert result["valid_tickets_count"] == 1
    assert result["invalid_tickets_count"] == 0
    assert result["total_tickets_count"] == 1
    assert result["total_validation_error_count"] == 0

    assert result["valid_records"][0]["ticket_id"] == "000001001"
    assert result["valid_records"][0]["customer"] == "Acme Corp"
    assert result["valid_records"][0]["priority"] == "high"
    assert result["valid_records"][0]["status"] == "open"
    assert result["valid_records"][0]["hours"] == 2.5


def test_check_rows_rejects_invalid_row():
    rows = [
        {
            "ticket_id": "000001003",
            "customer": "Acme Corp",
            "priority": "medium",
            "status": "open",
            "hours": "-3.0"
        }
    ]

    result = check_rows(rows)

    assert len(result["valid_records"]) == 0
    assert len(result["errors"]) == 1
    assert result["valid_tickets_count"] == 0
    assert result["invalid_tickets_count"] == 1
    assert result["total_tickets_count"] == 1
    assert result["total_validation_error_count"] == 1

    assert result["errors"][0]["ticket_id"] == "000001003"
    assert result["errors"][0]["customer"] == "Acme Corp"
    assert result["errors"][0]["priority"] == "medium"
    assert result["errors"][0]["status"] == "open"
    assert result["errors"][0]["hours"] is None

    assert result["errors"][0]["errors"] == [
        {
            "field": "hours",
            "invalid_value": "-3.0",
            "reason": "-3.0 cannot be less than 0.5"
        }
    ]


def test_check_rows_separates_valid_and_invalid_rows():
    rows = [
        {
            "ticket_id": "000001001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": "2.5"
        },
        {
            "ticket_id": "000001003",
            "customer": "Acme Corp",
            "priority": "medium",
            "status": "open",
            "hours": "-3.0"
        },
        {
            "ticket_id": "000001004",
            "customer": "Initech",
            "priority": "high",
            "status": "closed",
            "hours": "4.5"
        }
    ]

    result = check_rows(rows)

    assert len(result["valid_records"]) == 2
    assert len(result["errors"]) == 1

    assert result["valid_tickets_count"] == 2
    assert result["invalid_tickets_count"] == 1
    assert result["total_tickets_count"] == 3
    assert result["total_validation_error_count"] == 1


def test_check_rows_handles_empty_list():
    result = check_rows([])

    assert result["valid_records"] == []
    assert result["errors"] == []
    assert result["valid_tickets_count"] == 0
    assert result["invalid_tickets_count"] == 0
    assert result["total_tickets_count"] == 0
    assert result["total_validation_error_count"] == 0


# -------------------------------------------------------------------
# validate_ticket_id tests
# -------------------------------------------------------------------


def test_validate_ticket_id_accepts_valid_nine_digit_id():
    result = validate_ticket_id("123456789")

    assert result["valid"] is True
    assert result["value"] == "123456789"
    assert result["error"] is None


def test_validate_ticket_id_accepts_leading_zeroes():
    result = validate_ticket_id("000000001")

    assert result["valid"] is True
    assert result["value"] == "000000001"
    assert result["error"] is None


def test_validate_ticket_id_accepts_all_zeroes():
    result = validate_ticket_id("000000000")

    assert result["valid"] is True
    assert result["value"] == "000000000"
    assert result["error"] is None


def test_validate_ticket_id_strips_whitespace():
    result = validate_ticket_id(" 123456789 ")

    assert result["valid"] is True
    assert result["value"] == "123456789"


def test_validate_ticket_id_rejects_less_than_nine_characters():
    result = validate_ticket_id("12345678")

    assert result["valid"] is False
    assert result["error"] == (
        "12345678 must be exactly 9 characters long"
    )


def test_validate_ticket_id_rejects_more_than_nine_characters():
    result = validate_ticket_id("1234567890")

    assert result["valid"] is False
    assert result["error"] == (
        "1234567890 must be exactly 9 characters long"
    )


def test_validate_ticket_id_rejects_non_digit_characters():
    result = validate_ticket_id("12345678A")

    assert result["valid"] is False
    assert result["error"] == (
        "12345678A must contain only digits"
    )


def test_validate_ticket_id_rejects_none():
    result = validate_ticket_id(None)

    assert result["valid"] is False
    assert result["error"] == "ticket_id cannot be [None]"


def test_validate_ticket_id_rejects_non_string():
    result = validate_ticket_id(123456789)

    assert result["valid"] is False
    assert result["error"] == (
        "123456789 must be a string"
    )


# -------------------------------------------------------------------
# validate_customer tests
# -------------------------------------------------------------------


def test_validate_customer_accepts_valid_customer():
    result = validate_customer("Acme Corp")

    assert result["valid"] is True
    assert result["value"] == "Acme Corp"
    assert result["error"] is None


def test_validate_customer_strips_whitespace():
    result = validate_customer("  Acme Corp  ")

    assert result["valid"] is True
    assert result["value"] == "Acme Corp"


def test_validate_customer_rejects_empty_string():
    result = validate_customer("")

    assert result["valid"] is False
    assert result["error"] == "customer cannot be empty"


def test_validate_customer_rejects_whitespace_only():
    result = validate_customer("   ")

    assert result["valid"] is False
    assert result["error"] == "customer cannot be empty"


def test_validate_customer_rejects_none():
    result = validate_customer(None)

    assert result["valid"] is False
    assert result["error"] == "customer cannot be [None]"


def test_validate_customer_rejects_non_string():
    result = validate_customer(123)

    assert result["valid"] is False
    assert result["error"] == "123 must be a string"


# -------------------------------------------------------------------
# validate_priority tests
# -------------------------------------------------------------------


def test_validate_priority_accepts_valid_priorities():
    for priority in ["low", "medium", "high"]:
        result = validate_priority(priority)

        assert result["valid"] is True
        assert result["value"] == priority
        assert result["error"] is None


def test_validate_priority_strips_whitespace():
    result = validate_priority(" high ")

    assert result["valid"] is True
    assert result["value"] == "high"


def test_validate_priority_rejects_invalid_priority():
    result = validate_priority("urgent")

    assert result["valid"] is False
    assert result["error"] == (
        "urgent is not a valid priority"
    )


def test_validate_priority_rejects_none():
    result = validate_priority(None)

    assert result["valid"] is False
    assert result["error"] == "priority cannot be [None]"


def test_validate_priority_rejects_non_string():
    result = validate_priority(1)

    assert result["valid"] is False
    assert result["error"] == "1 must be a string"


# -------------------------------------------------------------------
# validate_status tests
# -------------------------------------------------------------------


def test_validate_status_accepts_valid_statuses():
    for status in ["open", "in_progress", "closed"]:
        result = validate_status(status)

        assert result["valid"] is True
        assert result["value"] == status
        assert result["error"] is None


def test_validate_status_strips_whitespace():
    result = validate_status(" closed ")

    assert result["valid"] is True
    assert result["value"] == "closed"


def test_validate_status_rejects_invalid_status():
    result = validate_status("pending")

    assert result["valid"] is False
    assert result["error"] == (
        "pending is not a valid status"
    )


def test_validate_status_rejects_none():
    result = validate_status(None)

    assert result["valid"] is False
    assert result["error"] == "status cannot be [None]"


def test_validate_status_rejects_non_string():
    result = validate_status(1)

    assert result["valid"] is False
    assert result["error"] == "1 must be a string"


# -------------------------------------------------------------------
# validate_hours tests
# -------------------------------------------------------------------


def test_validate_hours_accepts_valid_number():
    result = validate_hours("2.5")

    assert result["valid"] is True
    assert result["value"] == 2.5
    assert result["error"] is None


def test_validate_hours_accepts_minimum_value():
    result = validate_hours("0.5")

    assert result["valid"] is True
    assert result["value"] == 0.5
    assert result["error"] is None


def test_validate_hours_accepts_half_hour_increment():
    valid_values = [
        "0.5",
        "1.0",
        "1.5",
        "2.0",
        "2.5",
        "10.5",
        "39.5",
        "40.0"
    ]

    for hours in valid_values:
        result = validate_hours(hours)

        assert result["valid"] is True
        assert result["error"] is None


def test_validate_hours_rejects_less_than_minimum():
    invalid_values = [
        "0",
        "0.1",
        "0.25"
    ]

    for hours in invalid_values:
        result = validate_hours(hours)

        assert result["valid"] is False
        assert result["error"] == (
            f"{hours} cannot be less than 0.5"
        )


def test_validate_hours_rejects_non_half_hour_increment():
    invalid_values = [
        "1.25",
        "2.25",
        "2.75",
        "10.1",
        "39.9"
    ]

    for hours in invalid_values:
        result = validate_hours(hours)

        assert result["valid"] is False
        assert result["error"] == (
            f"{hours} must be in increments of 0.5"
        )


def test_validate_hours_rejects_negative_number():
    result = validate_hours("-3.0")

    assert result["valid"] is False
    assert result["error"] == (
        "-3.0 cannot be less than 0.5"
    )


def test_validate_hours_rejects_number_greater_than_40():
    result = validate_hours("41")

    assert result["valid"] is False
    assert result["error"] == (
        "41 cannot be greater than 40"
    )


def test_validate_hours_rejects_non_numeric_value():
    result = validate_hours("abc")

    assert result["valid"] is False
    assert result["error"] == (
        "abc must be a number"
    )


def test_validate_hours_rejects_none():
    result = validate_hours(None)

    assert result["valid"] is False
    assert result["error"] == (
        "hours cannot be [None]"
    )


def test_validate_hours_rejects_infinity():
    result = validate_hours("inf")

    assert result["valid"] is False
    assert result["error"] == (
        "inf must be a finite number"
    )


def test_validate_hours_rejects_nan():
    result = validate_hours("nan")

    assert result["valid"] is False
    assert result["error"] == (
        "nan must be a finite number"
    )