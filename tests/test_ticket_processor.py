import pytest

from ticket_processor import validate_hours


def test_validate_hours_accepts_valid_number():
    result = validate_hours("2.5")

    assert result["valid"] is True
    assert result["value"] == 2.5
    assert result["error"] is None


def test_validate_hours_accepts_zero():
    result = validate_hours("0")

    assert result["valid"] is True
    assert result["value"] == 0


def test_validate_hours_rejects_negative_number():
    result = validate_hours("-3.0")

    assert result["valid"] is False
    assert result["error"] == "hours cannot be less than 0"


def test_validate_hours_rejects_number_greater_than_24():
    result = validate_hours("25")

    assert result["valid"] is False
    assert result["error"] == "hours cannot be greater than 24"


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
