import pytest
from unittest.mock import patch
from src.processing.invalid_tickets import iter_invalid_tickets
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
        "src.processing.processor.find_duplicate_ticket_ids",
        return_value={}
    ), patch(
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
        "src.processing.processor.find_duplicate_ticket_ids",
        return_value={}
    ), patch(
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


# -------------------------------------------------------------------
# duplicate ticket_ids and one record per line (real files, no mocks)
# -------------------------------------------------------------------

HEADER = "ticket_id,customer,priority,status,hours\n"


def write_csv(tmp_path, body):
    csv_file = tmp_path / "tickets.csv"

    csv_file.write_text(
        HEADER + body,
        encoding="utf-8",
        newline=""
    )

    return csv_file


def test_process_csv_marks_every_row_with_a_duplicate_ticket_id_invalid(
    tmp_path
):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5\n"
        "100000002,Globex,low,closed,1.0\n"
        "100000001,Initech,medium,open,3.0\n"
        "100000003,Acme,high,open,4.0\n"
        "100000002,Globex,low,closed,1.0\n"
        "100000002,Acme,low,open,0.5\n"
    )

    result = process_csv(csv_file)

    assert result["total_tickets_count"] == 6
    assert result["valid_tickets_count"] == 1
    assert result["invalid_tickets_count"] == 5
    assert result["total_validation_error_count"] == 5

    # Only the one unique ticket reaches the summary.
    assert result["summary"]["total_hours"] == 4.0
    assert result["summary"]["hours_by_customer"] == {"Acme": 4.0}
    assert result["summary"]["tickets_by_status"]["open"] == 1

    reasons = [
        (
            record["ticket_id"],
            record["errors"][0]["reason"]
        )
        for record in result["invalid_records"]
    ]

    assert reasons == [
        (
            "100000001",
            "duplicate ticket_id: appears 2 times in the file"
        ),
        (
            "100000002",
            "duplicate ticket_id: appears 3 times in the file"
        ),
        (
            "100000001",
            "duplicate ticket_id: appears 2 times in the file"
        ),
        (
            "100000002",
            "duplicate ticket_id: appears 3 times in the file"
        ),
        (
            "100000002",
            "duplicate ticket_id: appears 3 times in the file"
        ),
    ]


def test_process_csv_keeps_the_other_errors_of_a_duplicate_row(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5\n"
        "100000001,Globex,urgent,open,2.5\n"
    )

    result = process_csv(csv_file)

    assert result["valid_tickets_count"] == 0
    assert result["total_validation_error_count"] == 3

    fields = [
        error["field"]
        for record in result["invalid_records"]
        for error in record["errors"]
    ]

    assert fields == ["ticket_id", "priority", "ticket_id"]


def test_process_csv_does_not_treat_unique_ids_as_duplicates(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5\n"
        "100000002,Globex,low,closed,1.0\n"
    )

    result = process_csv(csv_file)

    assert result["valid_tickets_count"] == 2
    assert result["invalid_records"] == []


def test_process_csv_reports_a_multi_line_record_as_one_error_per_line(
    tmp_path
):
    csv_file = write_csv(
        tmp_path,
        '100000001,"Acme\nCorp",high,open,2.5\n'
        "100000002,Globex,low,closed,1.0\n"
    )

    result = process_csv(csv_file)

    assert result["total_tickets_count"] == 3
    assert result["valid_tickets_count"] == 1
    assert result["invalid_tickets_count"] == 2
    assert result["total_validation_error_count"] == 2

    assert [
        record["errors"][0]["field"]
        for record in result["invalid_records"]
    ] == ["CSV", "CSV"]

    assert result["invalid_records"][0]["errors"][0]["reason"].startswith(
        "Line 2:"
    )


def test_process_csv_does_not_call_a_malformed_row_a_duplicate(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5\n"
        '100000001,"Globex,low,closed,1.0\n'
    )

    result = process_csv(csv_file)

    # The good row is not a duplicate: the bad line has no usable record.
    assert result["valid_tickets_count"] == 1
    assert result["invalid_tickets_count"] == 1
    assert result["invalid_records"][0]["errors"][0]["field"] == "CSV"


def test_process_csv_skips_blank_lines(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5\n"
        "\n"
        "100000002,Globex,low,closed,1.0\n"
        "\n"
    )

    result = process_csv(csv_file)

    assert result["total_tickets_count"] == 2
    assert result["valid_tickets_count"] == 2
    assert result["invalid_records"] == []


# -------------------------------------------------------------------
# invalid tickets written to a file instead of kept in memory
# -------------------------------------------------------------------


def ten_invalid_rows():
    return "".join(
        f"1000000{i:02d},Acme,urgent,open,2.5\n"
        for i in range(10)
    )


def test_process_csv_writes_every_invalid_ticket_to_the_details_file(
    tmp_path
):
    details = tmp_path / "invalid.jsonl"

    result = process_csv(
        write_csv(tmp_path, ten_invalid_rows()),
        details
    )

    # Counts are exact and nothing is held in memory.
    assert result["total_tickets_count"] == 10
    assert result["invalid_tickets_count"] == 10
    assert result["total_validation_error_count"] == 10
    assert result["invalid_records"] == []
    assert result["invalid_details_path"] == str(details)

    tickets = list(iter_invalid_tickets(result))

    assert [ticket["ticket_id"] for ticket in tickets] == [
        f"1000000{i:02d}" for i in range(10)
    ]
    assert tickets[0]["errors"][0]["field"] == "priority"


def test_process_csv_keeps_valid_tickets_out_of_the_details_file(tmp_path):
    details = tmp_path / "invalid.jsonl"

    result = process_csv(
        write_csv(
            tmp_path,
            "100000001,Acme,high,open,2.5\n"
            "100000002,Acme,urgent,open,2.5\n"
        ),
        details
    )

    assert [
        ticket["ticket_id"]
        for ticket in iter_invalid_tickets(result)
    ] == ["100000002"]
    assert result["valid_tickets_count"] == 1


def test_process_csv_without_a_details_file_keeps_them_in_memory(tmp_path):
    result = process_csv(write_csv(tmp_path, ten_invalid_rows()))

    assert len(result["invalid_records"]) == 10
    assert "invalid_details_path" not in result
    assert len(list(iter_invalid_tickets(result))) == 10


def test_process_csv_will_not_overwrite_an_existing_details_file(tmp_path):
    details = tmp_path / "invalid.jsonl"
    details.write_text("keep me")

    with pytest.raises(FileExistsError):
        process_csv(
            write_csv(tmp_path, ten_invalid_rows()),
            details
        )

    assert details.read_text() == "keep me"


def test_process_csv_deletes_its_details_file_when_processing_fails(
    tmp_path
):
    details = tmp_path / "invalid.jsonl"

    # Some invalid rows, then a line the reader refuses to accept.
    rows = ten_invalid_rows()
    csv_file = write_csv(tmp_path, rows)

    with patch(
        "src.processing.processor.validate_row",
        side_effect=[
            {
                "valid": False,
                "record": {"ticket_id": "1", "errors": []},
                "error_count": 1
            },
            RuntimeError("boom")
        ]
    ):
        with pytest.raises(RuntimeError):
            process_csv(csv_file, details)

    assert not details.exists()


def test_process_csv_details_file_survives_odd_characters(tmp_path):
    details = tmp_path / "invalid.jsonl"

    # Curly quotes, an accent, and U+2028 (which some code treats as a
    # line break) must come back unchanged.
    odd_priority = "\u201curgent\u201d caf\u00e9\u2028x"

    csv_file = write_csv(
        tmp_path,
        f"100000001,Acme,{odd_priority},open,2.5\n"
    )

    result = process_csv(csv_file, details)

    (ticket,) = list(iter_invalid_tickets(result))

    assert odd_priority in [
        error["invalid_value"]
        for error in ticket["errors"]
    ]

    # One ticket, one line.
    assert details.read_bytes().count(b"\n") == 1
