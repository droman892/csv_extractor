from pathlib import Path
import csv

import pytest

from src.services.results_export_service import ResultsExportService


RESULT = {
    "filename": "C:/files/test_data.csv",
    "total_tickets_count": 5,
    "valid_tickets_count": 3,
    "invalid_tickets_count": 2,
    "summary": {
        "total_hours": 17.5,
        "tickets_by_status": {
            "open": 2,
            "in_progress": 1,
            "closed": 2
        },
        "tickets_by_priority": {
            "high": 2,
            "medium": 2,
            "low": 1
        },
        "hours_by_customer": {
            "Acme": 10.5,
            "Beta Corp": 7.0
        }
    },
    "invalid_records": [
        {
            "ticket_id": "INC001",
            "errors": [
                {
                    "field": "priority",
                    "invalid_value": "urgent",
                    "reason": "Invalid priority."
                }
            ]
        },
        {
            "ticket_id": "INC002",
            "errors": [
                {
                    "field": "status",
                    "invalid_value": "unknown",
                    "reason": "Invalid status."
                },
                {
                    "field": "hours",
                    "invalid_value": "-5",
                    "reason": "Hours cannot be negative."
                }
            ]
        }
    ]
}


def read_csv_file(path):
    with open(
        path,
        "r",
        newline="",
        encoding="utf-8"
    ) as csv_file:
        return list(csv.reader(csv_file))


def test_create_export_file_creates_csv_file(tmp_path, monkeypatch):
    def fake_mkdtemp(prefix):
        return str(tmp_path)

    monkeypatch.setattr(
        "src.services.results_export_service.tempfile.mkdtemp",
        fake_mkdtemp
    )

    export_path = ResultsExportService.create_export_file(
        RESULT
    )

    assert export_path == str(
        tmp_path / "test_data_results.csv"
    )
    assert Path(export_path).is_file()


def test_create_export_file_uses_source_filename_stem(
    tmp_path,
    monkeypatch
):
    result = dict(RESULT)
    result["filename"] = (
        "C:/files/customer_export_2026.csv"
    )

    monkeypatch.setattr(
        "src.services.results_export_service.tempfile.mkdtemp",
        lambda prefix: str(tmp_path)
    )

    export_path = ResultsExportService.create_export_file(
        result
    )

    assert Path(export_path).name == (
        "customer_export_2026_results.csv"
    )


def test_export_results_writes_title_section(tmp_path):
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        RESULT,
        destination
    )

    rows = read_csv_file(destination)

    assert rows[0] == ["CSV Extractor Results"]
    assert rows[1] == ["Filename", "test_data.csv"]


def test_export_results_writes_overall_section(tmp_path):
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        RESULT,
        destination
    )

    rows = read_csv_file(destination)

    assert ["Overall"] in rows
    assert ["Metric", "Count"] in rows
    assert ["Total Tickets", "5"] in rows
    assert ["Valid Tickets", "3"] in rows
    assert ["Invalid Tickets", "2"] in rows
    assert ["Total Hours", "17.5"] in rows


def test_export_results_writes_status_section(tmp_path):
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        RESULT,
        destination
    )

    rows = read_csv_file(destination)

    assert ["Tickets by Status"] in rows
    assert ["Status", "Count"] in rows
    assert ["Open", "2"] in rows
    assert ["In Progress", "1"] in rows
    assert ["Closed", "2"] in rows


def test_export_results_writes_priority_section(tmp_path):
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        RESULT,
        destination
    )

    rows = read_csv_file(destination)

    assert ["Tickets by Priority"] in rows
    assert ["Priority", "Count"] in rows
    assert ["High", "2"] in rows
    assert ["Medium", "2"] in rows
    assert ["Low", "1"] in rows


def test_export_results_writes_customer_section(tmp_path):
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        RESULT,
        destination
    )

    rows = read_csv_file(destination)

    assert ["Hours by Customer (Count: 2)"] in rows
    assert ["Customer #", "Customer", "Hours"] in rows
    assert ["1", "Acme", "10.5"] in rows
    assert ["2", "Beta Corp", "7.0"] in rows


def test_export_results_sorts_customers_case_insensitively(
    tmp_path
):
    result = dict(RESULT)
    result["summary"] = dict(RESULT["summary"])
    result["summary"]["hours_by_customer"] = {
        "Zulu": 5,
        "acme": 10,
        "Beta": 7
    }

    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        result,
        destination
    )

    rows = read_csv_file(destination)

    acme_index = rows.index(["1", "acme", "10"])
    beta_index = rows.index(["2", "Beta", "7"])
    zulu_index = rows.index(["3", "Zulu", "5"])

    assert acme_index < beta_index < zulu_index


def test_export_results_writes_validation_section(tmp_path):
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        RESULT,
        destination
    )

    rows = read_csv_file(destination)

    assert ["Validation Issues (Count: 3)"] in rows
    assert [
        "Issue #",
        "Ticket",
        "Field",
        "Invalid Value",
        "Validation Error"
    ] in rows

    assert [
        "1",
        "INC001",
        "priority",
        "urgent",
        "Invalid priority."
    ] in rows

    assert [
        "2",
        "INC002",
        "status",
        "unknown",
        "Invalid status."
    ] in rows

    assert [
        "3",
        "INC002",
        "hours",
        "-5",
        "Hours cannot be negative."
    ] in rows


def test_export_results_handles_records_without_errors(tmp_path):
    result = dict(RESULT)
    result["invalid_records"] = [
        {
            "ticket_id": "INC001",
            "errors": []
        },
        {
            "ticket_id": "INC002"
        }
    ]

    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        result,
        destination
    )

    rows = read_csv_file(destination)

    assert ["Validation Issues (Count: 0)"] in rows


def test_export_results_raises_value_error_when_required_data_is_missing(
    tmp_path
):
    result = dict(RESULT)
    del result["total_tickets_count"]

    destination = tmp_path / "results.csv"

    with pytest.raises(
        ValueError,
        match="Unable to export results because required result data is missing"
    ):
        ResultsExportService.export_results(
            result,
            destination
        )


def test_export_results_raises_os_error_when_destination_is_invalid():
    destination = Path(
        "Z:/this/path/does/not/exist/results.csv"
    )

    with pytest.raises(
        OSError,
        match="Unable to write the export file"
    ):
        ResultsExportService.export_results(
            RESULT,
            destination
        )


def test_copy_export_file_copies_file(tmp_path):
    source = tmp_path / "source.csv"
    destination = tmp_path / "destination.csv"

    source.write_text(
        "test,data\n123,abc",
        encoding="utf-8"
    )

    ResultsExportService.copy_export_file(
        source,
        destination
    )

    assert destination.is_file()
    assert destination.read_text(
        encoding="utf-8"
    ) == source.read_text(
        encoding="utf-8"
    )


def test_copy_export_file_raises_os_error_when_source_is_missing(
    tmp_path
):
    source = tmp_path / "missing.csv"
    destination = tmp_path / "destination.csv"

    with pytest.raises(
        OSError,
        match="Unable to save the exported file"
    ):
        ResultsExportService.copy_export_file(
            source,
            destination
        )