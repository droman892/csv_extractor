import pytest
from unittest.mock import patch
from src.processing.processor import process_csv


def test_process_csv_returns_summary(tmp_path):
    csv_file = tmp_path / "test.csv"

    csv_file.write_text(
        "ticket_id,customer,priority,status,hours\n"
        "100000001,Acme Corp,high,open,2.5\n"
        "100000002,Globex,low,closed,1.0\n"
        "100000003,Acme Corp,medium,open,-3.0\n"
        "100000004,Initech,high,closed,4.5\n"
        "100000005,Globex,high,open,2.0\n",
        encoding="utf-8"
    )

    result = process_csv(csv_file)

    assert result == {
        "filename": csv_file,
        "summary": {
            "tickets_by_status": {
                "open": 2,
                "closed": 2,
                "in_progress": 0
            },
            "tickets_by_priority": {
                "low": 1,
                "medium": 0,
                "high": 3
            },
            "hours_by_customer": {
                "Acme Corp": 2.5,
                "Globex": 3.0,
                "Initech": 4.5
            },
            "total_hours": 10.0
        },
        "valid_tickets_count": 4,
        "invalid_tickets_count": 1,
        "total_tickets_count": 5,
        "total_validation_error_count": 1,
        "invalid_records": [
            {
                "ticket_id": "100000003",
                "customer": "Acme Corp",
                "priority": "medium",
                "status": "open",
                "hours": None,
                "errors": [
                    {
                        "field": "hours",
                        "invalid_value": "-3.0",
                        "reason": "-3.0 cannot be less than 0.5"
                    }
                ]
            }
        ]
    }


def test_process_csv_passes_valid_records_to_aggregation():
    raw_rows = [
        {
            "ticket_id": "100000001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": "2.5"
        }
    ]

    validation_result = {
        "valid": True,
        "record": {
            "ticket_id": "100000001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": 2.5
        },
        "error_count": 0
    }

    expected_summary = {
        "tickets_by_status": {"open": 1},
        "tickets_by_priority": {"high": 1},
        "hours_by_customer": {"Acme Corp": 2.5},
        "total_hours": 2.5
    }

    with patch(
        "src.processing.processor.read_csv",
        return_value=iter(raw_rows)
    ):
        with patch(
            "src.processing.processor.validate_row",
            return_value=validation_result
        ) as mock_validate_row:
            with patch(
                "src.processing.processor.create_aggregation",
                return_value={}
            ) as mock_create_aggregation:
                with patch(
                    "src.processing.processor.add_valid_record"
                ) as mock_add_valid_record:

                    result = process_csv("anything.csv")

    assert result == {
        "filename": "anything.csv",
        "summary": {},
        "valid_tickets_count": 1,
        "invalid_tickets_count": 0,
        "total_tickets_count": 1,
        "total_validation_error_count": 0,
        "invalid_records": []
    }

    mock_create_aggregation.assert_called_once_with()

    mock_validate_row.assert_called_once_with(
        raw_rows[0]
    )

    mock_add_valid_record.assert_called_once_with(
        {},
        validation_result["record"]
    )


def test_process_csv_passes_invalid_records_to_result():
    raw_rows = [
        {
            "ticket_id": "100000003",
            "customer": "Acme Corp",
            "priority": "medium",
            "status": "open",
            "hours": "-3.0"
        }
    ]

    invalid_record = {
        "ticket_id": "100000003",
        "customer": "Acme Corp",
        "priority": "medium",
        "status": "open",
        "hours": None,
        "errors": [
            {
                "field": "hours",
                "invalid_value": "-3.0",
                "reason": "-3.0 cannot be less than 0.5"
            }
        ]
    }

    validation_result = {
        "valid": False,
        "record": invalid_record,
        "error_count": 1
    }

    with patch(
        "src.processing.processor.read_csv",
        return_value=iter(raw_rows)
    ):
        with patch(
            "src.processing.processor.validate_row",
            return_value=validation_result
        ) as mock_validate_row:

            result = process_csv("anything.csv")

    assert result["filename"] == "anything.csv"
    assert result["valid_tickets_count"] == 0
    assert result["invalid_tickets_count"] == 1
    assert result["total_tickets_count"] == 1
    assert result["total_validation_error_count"] == 1
    assert result["invalid_records"] == [invalid_record]

    mock_validate_row.assert_called_once_with(
        raw_rows[0]
    )


def test_process_csv_propagates_file_not_found_error():
    with patch(
        "src.processing.processor.read_csv",
        side_effect=FileNotFoundError
    ):
        with pytest.raises(FileNotFoundError):
            process_csv("missing.csv")