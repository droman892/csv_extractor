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
        "filename": tmp_path / "test.csv",
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
                        "reason": "-3.0 cannot be less than 0"
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

    processed_rows = {
        "valid_records": [
            {
                "ticket_id": "100000001",
                "customer": "Acme Corp",
                "priority": "high",
                "status": "open",
                "hours": 2.5
            }
        ],
        "errors": [],
        "valid_tickets_count": 1,
        "invalid_tickets_count": 0,
        "total_tickets_count": 1,
        "total_validation_error_count": 0
    }

    expected_summary = {
        "tickets_by_status": {"open": 1},
        "tickets_by_priority": {"high": 1},
        "hours_by_customer": {"Acme Corp": 2.5},
        "total_hours": 2.5
    }

    expected_result = {
        "filename": "anything.csv",
        "summary": expected_summary,
        "valid_tickets_count": 1,
        "invalid_tickets_count": 0,
        "total_tickets_count": 1,
        "total_validation_error_count": 0,
        "invalid_records": []
    }

    with patch(
        "src.processing.processor.read_csv",
        return_value=raw_rows
    ):
        with patch(
            "src.processing.processor.check_rows",
            return_value=processed_rows
        ):
            with patch(
                "src.processing.processor.aggregate_csv",
                return_value=expected_summary
            ) as mock_aggregate:

                result = process_csv("anything.csv")

    assert result == expected_result
    mock_aggregate.assert_called_once_with(
        processed_rows["valid_records"]
    )


def test_process_csv_passes_raw_rows_to_validation():
    raw_rows = [
        {
            "ticket_id": "100000001",
            "customer": "Acme Corp",
            "priority": "high",
            "status": "open",
            "hours": "2.5"
        }
    ]

    processed_rows = {
        "valid_records": [],
        "errors": [],
        "valid_tickets_count": 0,
        "invalid_tickets_count": 1,
        "total_tickets_count": 1,
        "total_validation_error_count": 1
    }

    expected_summary = {
        "tickets_by_status": {},
        "tickets_by_priority": {},
        "hours_by_customer": {},
        "total_hours": 0
    }

    expected_result = {
        "filename": "anything.csv",
        "summary": expected_summary,
        "valid_tickets_count": 0,
        "invalid_tickets_count": 1,
        "total_tickets_count": 1,
        "total_validation_error_count": 1,
        "invalid_records": []
    }

    with patch(
        "src.processing.processor.read_csv",
        return_value=raw_rows
    ):
        with patch(
            "src.processing.processor.check_rows",
            return_value=processed_rows
        ) as mock_check_rows:
            with patch(
                "src.processing.processor.aggregate_csv",
                return_value=expected_summary
            ):

                result = process_csv("anything.csv")

    assert result == expected_result
    mock_check_rows.assert_called_once_with(raw_rows)


def test_process_csv_propagates_file_not_found_error():
    with patch(
        "src.processing.processor.read_csv",
        side_effect=FileNotFoundError
    ):
        with pytest.raises(FileNotFoundError):
            process_csv("missing.csv")