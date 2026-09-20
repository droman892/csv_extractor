from pathlib import Path
import csv
import os

import pytest

from src.processing.invalid_tickets import (
    open_for_writing,
    write_invalid_ticket
)
from src.processing.rules import VALID_RECORDS_NOTE
from src.services.results_export_service import (
    ResultsExportService,
    safe_cell
)


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


def test_export_results_writes_title_section(tmp_path):
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        RESULT,
        destination
    )

    rows = read_csv_file(destination)

    assert rows[0] == ["CSV Extractor Results"]
    assert rows[1] == ["Filename", "test_data.csv"]


def test_export_results_writes_the_note_without_quotes(tmp_path):
    # Read the raw text: the csv module hides quoting.
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        RESULT,
        destination
    )

    lines = destination.read_text(encoding="utf-8").splitlines()

    assert lines[2] == VALID_RECORDS_NOTE
    assert '"' not in lines[2]


def test_export_results_writes_the_note_on_its_own_line(tmp_path):
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(
        RESULT,
        destination
    )

    rows = read_csv_file(destination)

    # A spreadsheet splits the line at its commas; the pieces put back
    # together are the note, and the line after it is the blank separator.
    assert ",".join(rows[2]) == VALID_RECORDS_NOTE
    assert rows[3] == []
    assert rows[4] == ["Overall"]


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


# -------------------------------------------------------------------
# CSV / formula injection
# -------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "=1+1",
        "+SUM(A1:A9)",
        "-2+3",
        "@SUM(A1)",
        "\tcmd",
        "\rcmd",
        '=HYPERLINK("http://evil.example","x")',
        "-3.0 cannot be less than 0.5"
    ]
)
def test_safe_cell_prefixes_text_a_spreadsheet_could_run(value):
    assert safe_cell(value) == "'" + value


@pytest.mark.parametrize(
    "value",
    ["Acme", "", "100000001", "-3.0", "-5", "+5", "1.5", 7, 2.5, None]
)
def test_safe_cell_leaves_ordinary_values_alone(value):
    assert safe_cell(value) == value


def test_export_results_neutralizes_formulas_from_the_input_file(
    tmp_path
):
    result = dict(RESULT)

    result["filename"] = "C:/files/=cmd.csv"

    result["summary"] = dict(RESULT["summary"])
    result["summary"]["hours_by_customer"] = {
        "=1+1": 1.0,
        "Acme": 2.0
    }

    result["invalid_records"] = [
        {
            "ticket_id": "@bad",
            "errors": [
                {
                    "field": "customer",
                    "invalid_value": "+1+1",
                    "reason": "+1+1 is not valid"
                }
            ]
        }
    ]

    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(result, destination)

    cells = [
        cell
        for row in read_csv_file(destination)
        for cell in row
    ]

    assert "'=cmd.csv" in cells
    assert "'=1+1" in cells
    assert "'@bad" in cells
    assert "'+1+1" in cells
    assert "'+1+1 is not valid" in cells

    # Nothing is left that starts like a formula.
    assert not [
        cell for cell in cells
        if cell.startswith(("=", "@", "+"))
    ]


# -------------------------------------------------------------------
# invalid tickets kept in a file by the processor
# -------------------------------------------------------------------


def result_with_details_file(tmp_path, count):
    details = tmp_path / "invalid.jsonl"

    with open_for_writing(details) as file:
        for number in range(count):
            write_invalid_ticket(
                file,
                {
                    "ticket_id": str(1000 + number),
                    "errors": [
                        {
                            "field": "priority",
                            "invalid_value": "urgent",
                            "reason": "Invalid priority."
                        },
                        {
                            "field": "status",
                            "invalid_value": "pending",
                            "reason": "Invalid status."
                        }
                    ]
                }
            )

    result = dict(RESULT)
    result["invalid_tickets_count"] = count
    result["total_validation_error_count"] = count * 2
    result["invalid_records"] = []
    result["invalid_details_path"] = str(details)

    return result


def test_export_results_lists_every_ticket_from_the_details_file(tmp_path):
    result = result_with_details_file(tmp_path, 25_000)

    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(result, destination)

    rows = read_csv_file(destination)

    issues = [
        row for row in rows
        if len(row) == 5 and row[0].isdigit()
    ]

    assert ["Validation Issues (Count: 50000)"] in rows
    assert len(issues) == 50_000
    assert issues[0] == [
        "1", "1000", "priority", "urgent", "Invalid priority."
    ]
    assert issues[-1][:2] == ["50000", "25999"]


def test_export_results_says_so_when_the_details_file_is_gone(tmp_path):
    result = result_with_details_file(tmp_path, 3)

    os.remove(result["invalid_details_path"])

    with pytest.raises(RuntimeError, match="no longer available"):
        ResultsExportService.export_results(
            result,
            tmp_path / "results.csv"
        )


def test_export_results_counts_errors_itself_when_no_total_is_given(
    tmp_path
):
    result = result_with_details_file(tmp_path, 4)
    del result["total_validation_error_count"]

    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(result, destination)

    assert ["Validation Issues (Count: 8)"] in read_csv_file(destination)


def test_export_results_never_adds_a_cut_short_note(
    tmp_path
):
    destination = tmp_path / "results.csv"

    ResultsExportService.export_results(RESULT, destination)

    cells = [
        cell
        for row in read_csv_file(destination)
        for cell in row
    ]

    assert not [cell for cell in cells if cell.startswith("Note: details")]
