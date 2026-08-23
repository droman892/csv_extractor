import pytest
from src.validation import validate_hours, check_rows


@pytest.fixture
def valid_row():
    return {
        "ticket_id": "1001",
        "customer": "Acme Corp",
        "priority": "high",
        "status": "open",
        "hours": "2.5"
    }


def test_check_rows_accepts_valid_row(valid_row):
    result = check_rows([valid_row])

    assert len(result["valid_records"]) == 1
    assert len(result["errors"]) == 0
    assert result["valid_tickets_count"] == 1
    assert result["invalid_tickets_count"] == 0
    assert result["total_tickets_count"] == 1

    assert result["valid_records"][0]["ticket_id"] == "1001"
    assert result["valid_records"][0]["customer"] == "Acme Corp"
    assert result["valid_records"][0]["priority"] == "high"
    assert result["valid_records"][0]["status"] == "open"
    assert result["valid_records"][0]["hours"] == 2.5


def test_check_rows_rejects_invalid_row():
    rows = [
        {
            "ticket_id": "1003",
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

    assert result["errors"][0]["ticket_id"] == "1003"
    assert result["errors"][0]["customer"] == "Acme Corp"
    assert result["errors"][0]["priority"] == "medium"
    assert result["errors"][0]["status"] == "open"
    assert result["errors"][0]["hours"] is None

    assert result["errors"][0]["errors"] == [
        {
            "field": "hours",
            "invalid_value": "-3.0",
            "reason": "hours cannot be less than 0"
        }
    ]


def test_check_rows_separates_valid_and_invalid_rows():
    rows = [
        {
            "ticket_id": "1001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": "2.5"
        },
        {
            "ticket_id": "1003",
            "customer": "Acme Corp",
            "priority": "medium",
            "status": "open",
            "hours": "-3.0"
        },
        {
            "ticket_id": "1004",
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


def test_check_rows_handles_empty_list():
    result = check_rows([])

    assert result["valid_records"] == []
    assert result["errors"] == []
    assert result["valid_tickets_count"] == 0
    assert result["invalid_tickets_count"] == 0
    assert result["total_tickets_count"] == 0


# -------------------------------------------------------------------
# validate_hours tests
# -------------------------------------------------------------------


def test_validate_hours_accepts_valid_number():
    result = validate_hours("2.5")

    assert result["valid"] is True
    assert result["value"] == 2.5
    assert result["error"] is None


def test_validate_hours_accepts_zero():
    result = validate_hours("0")

    assert result["valid"] is True
    assert result["value"] == 0
    assert result["error"] is None


def test_validate_hours_accepts_half_hour_increment():
    valid_values = ["0.5", "1.0", "1.5", "2.0", "2.5", "10.5", "39.5", "40.0"]

    for hours in valid_values:
        result = validate_hours(hours)

        assert result["valid"] is True
        assert result["error"] is None


def test_validate_hours_rejects_non_half_hour_increment():
    invalid_values = ["0.1", "1.25", "2.25", "2.75", "10.1", "39.9"]

    for hours in invalid_values:
        result = validate_hours(hours)

        assert result["valid"] is False
        assert result["error"] == f"{hours} must be in increments of 0.5"


def test_validate_hours_rejects_negative_number():
    result = validate_hours("-3.0")

    assert result["valid"] is False
    assert result["error"] == "hours cannot be less than 0"


def test_validate_hours_rejects_number_greater_than_40():
    result = validate_hours("41")

    assert result["valid"] is False
    assert result["error"] == "hours cannot be greater than 40"


def test_validate_hours_rejects_non_numeric_value():
    result = validate_hours("abc")

    assert result["valid"] is False
    assert result["error"] == "abc is not a number"


def test_validate_hours_rejects_none():
    result = validate_hours(None)

    assert result["valid"] is False
    assert result["error"] == "hours cannot be [None]"


def test_validate_hours_rejects_infinity():
    result = validate_hours("inf")

    assert result["valid"] is False
    assert result["error"] == "inf is not a finite number"


def test_validate_hours_rejects_nan():
    result = validate_hours("nan")

    assert result["valid"] is False
    assert result["error"] == "nan is not a finite number"