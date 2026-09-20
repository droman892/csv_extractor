"""End-to-end tests: real files, real background processes.

The unit tests mock the pieces around each function. These start the real
child processes through the real workers and check that the pieces fit
together: file -> processing process -> result file -> export process ->
report. (The workers are driven directly, without a QThread; the
view-model tests cover the thread wiring.)
"""

import csv
import logging
import os

from src.workers.export_worker import ExportWorker
from src.workers.process_utils import details_path_for, remove_result_files
from src.workers.upload_worker import UploadWorker


HEADER = "ticket_id,customer,priority,status,hours\n"

BODY = (
    "100000001,Acme,high,open,2.5\n"
    "100000002,Globex,low,closed,1.0\n"
    "100000001,Initech,medium,open,3.0\n"
    "100000003,=cmd|'/C calc'!A0,high,open,4.0\n"
    "100000004,Acme,high,open,abc\n"
    "\n"
    '100000005,"Multi\n'
    'line",high,open,1.0\n'
)

TIMEOUT = 60_000


def write_csv(tmp_path, body=BODY, name="tickets.csv"):
    csv_file = tmp_path / name

    csv_file.write_text(
        HEADER + body,
        encoding="utf-8",
        newline=""
    )

    return csv_file


def read_report(path):
    with open(path, newline="", encoding="utf-8") as report:
        return list(csv.reader(report))


def run_upload(qtbot, csv_file):
    """Run the real processing process; return ('completed'|'failed', value)."""
    worker = UploadWorker(str(csv_file))

    outcome = []

    worker.completed.connect(
        lambda value: outcome.append(("completed", value))
    )
    worker.failed.connect(
        lambda message: outcome.append(("failed", message))
    )

    worker.process_file()

    qtbot.waitUntil(lambda: bool(outcome), timeout=TIMEOUT)

    return worker, outcome[0]


def run_export(qtbot, full_result_path, destination):
    worker = ExportWorker(full_result_path, str(destination))

    outcome = []

    worker.completed.connect(
        lambda value: outcome.append(("completed", value))
    )
    worker.failed.connect(
        lambda message: outcome.append(("failed", message))
    )

    worker.export_file()

    qtbot.waitUntil(lambda: bool(outcome), timeout=TIMEOUT)

    return outcome[0]


def test_file_to_processing_process_to_export_report(qtbot, tmp_path):
    csv_file = write_csv(tmp_path)

    worker, (status, value) = run_upload(qtbot, csv_file)

    assert status == "completed"

    full_result_path = value["full_result_path"]
    display = value["display_result"]

    try:
        # 7 lines with content (the blank line is skipped):
        #   2 share a ticket_id            -> invalid
        #   1 has hours "abc"              -> invalid
        #   2 are one record split in two  -> invalid
        #   2 are fine (one has a formula as its customer name)
        assert display["total_tickets_count"] == 7
        assert display["valid_tickets_count"] == 2
        assert display["invalid_tickets_count"] == 5
        assert display["total_invalid_error_count"] == 5
        assert display["summary"]["total_hours"] == 5.0

        assert os.path.exists(full_result_path)
        assert full_result_path == worker.full_result_path

        # The invalid tickets are in a file beside the result file.
        assert os.path.exists(details_path_for(full_result_path))

        report_path = tmp_path / "report.csv"

        export_status, exported = run_export(
            qtbot,
            full_result_path,
            report_path
        )

        assert export_status == "completed"
        assert exported == str(report_path)
    finally:
        remove_result_files(full_result_path)

    assert not os.path.exists(full_result_path)
    assert not os.path.exists(details_path_for(full_result_path))

    rows = read_report(report_path)
    cells = [cell for row in rows for cell in row]

    # Both rows that share a ticket_id are reported.
    duplicates = [
        row for row in rows
        if len(row) == 5 and row[4].startswith("duplicate ticket_id")
    ]

    assert [row[1] for row in duplicates] == ["100000001", "100000001"]

    # The multi-line record is reported line by line.
    csv_issues = [
        row for row in rows
        if len(row) == 5 and row[2] == "CSV"
    ]

    assert len(csv_issues) == 2
    # Header is line 1, five data rows are lines 2-6, the blank is line 7.
    assert csv_issues[0][4].startswith("Line 8:")

    # The formula in the customer name is neutralized in the report.
    assert "'=cmd|'/C calc'!A0" in cells
    assert not [cell for cell in cells if cell.startswith("=")]

    assert ["Validation Issues (Count: 5)"] in rows


def test_a_clean_file_produces_a_report_with_no_issues(qtbot, tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,Acme,high,open,2.5\n"
        "100000002,Globex,low,closed,1.0\n"
    )

    _, (status, value) = run_upload(qtbot, csv_file)

    assert status == "completed"

    try:
        report_path = tmp_path / "report.csv"

        run_export(qtbot, value["full_result_path"], report_path)
    finally:
        remove_result_files(value["full_result_path"])

    assert ["Validation Issues (Count: 0)"] in read_report(report_path)


def test_a_file_with_the_wrong_columns_fails_and_leaves_no_temp_file(
    qtbot,
    tmp_path
):
    csv_file = tmp_path / "wrong.csv"
    csv_file.write_text("a,b,c\n1,2,3\n", encoding="utf-8")

    worker, (status, message) = run_upload(qtbot, csv_file)

    assert status == "failed"
    assert "Missing required columns" in message
    assert not os.path.exists(worker.full_result_path)
    assert not os.path.exists(details_path_for(worker.full_result_path))


def test_a_file_that_is_not_utf8_gets_a_plain_message(qtbot, tmp_path):
    csv_file = tmp_path / "latin1.csv"

    csv_file.write_bytes(
        HEADER.encode("ascii")
        + b"100000001,Caf\xe9,high,open,2.5\n"
    )

    worker, (status, message) = run_upload(qtbot, csv_file)

    assert status == "failed"
    assert "not valid UTF-8" in message
    assert "CSV UTF-8" in message
    assert not os.path.exists(worker.full_result_path)
    assert not os.path.exists(details_path_for(worker.full_result_path))


def test_a_missing_file_fails_with_a_message(qtbot, tmp_path):
    _, (status, message) = run_upload(qtbot, tmp_path / "gone.csv")

    assert status == "failed"
    assert message


def test_a_killed_processing_process_is_reported_not_waited_on_forever(
    qtbot,
    tmp_path
):
    # Big enough that the process is still working when it is killed.
    body = "".join(
        f"{100000000 + i},Customer {i % 100},high,open,2.5\n"
        for i in range(300_000)
    )

    csv_file = write_csv(tmp_path, body, "big.csv")

    worker = UploadWorker(str(csv_file))

    outcome = []
    worker.failed.connect(lambda message: outcome.append(message))
    worker.completed.connect(lambda value: outcome.append(value))

    worker.process_file()
    worker.process.kill()

    qtbot.waitUntil(lambda: bool(outcome), timeout=TIMEOUT)

    assert isinstance(outcome[0], str)
    assert "stopped unexpectedly" in outcome[0]
    assert not os.path.exists(worker.full_result_path)
    assert not os.path.exists(details_path_for(worker.full_result_path))


def test_the_background_processes_write_to_the_log_file(qtbot, tmp_path):
    csv_file = write_csv(tmp_path)

    _, (status, value) = run_upload(qtbot, csv_file)

    remove_result_files(value["full_result_path"])

    text = (tmp_path / "test.log").read_text(encoding="utf-8")

    assert status == "completed"
    assert "Processed 7 tickets" in text
    assert "Process-" in text

    # Row contents are never logged.
    assert "Acme" not in text
    assert "Globex" not in text


def test_every_invalid_ticket_is_listed_in_the_report(qtbot, tmp_path):
    # Far more invalid tickets than the screen shows (100), each with two
    # errors (a bad priority and a bad status), plus a few valid ones.
    invalid_count = 1_500

    body = "".join(
        f"{200000000 + i},Acme,urgent,pending,2.5\n"
        for i in range(invalid_count)
    )
    body += (
        "100000001,Acme,high,open,2.5\n"
        "100000002,Globex,low,closed,1.0\n"
    )

    csv_file = write_csv(tmp_path, body)

    _, (status, value) = run_upload(qtbot, csv_file)

    assert status == "completed"

    full_result_path = value["full_result_path"]
    display = value["display_result"]

    try:
        # The screen shows a page of them; the counts are the real totals.
        assert len(display["invalid_records"]) == 100
        assert display["invalid_tickets_count"] == invalid_count
        assert display["total_invalid_error_count"] == invalid_count * 2

        report_path = tmp_path / "report.csv"

        run_export(qtbot, full_result_path, report_path)
    finally:
        remove_result_files(full_result_path)

    rows = read_report(report_path)

    issues = [
        row for row in rows
        if len(row) == 5 and row[0].isdigit()
    ]

    assert ["Validation Issues (Count: 3000)"] in rows
    assert len(issues) == invalid_count * 2
    assert [row[0] for row in issues] == [
        str(number) for number in range(1, invalid_count * 2 + 1)
    ]

    listed_tickets = {row[1] for row in issues}

    assert listed_tickets == {
        str(200000000 + i) for i in range(invalid_count)
    }

    # No note about the list being cut short: nothing is cut.
    assert not [
        row for row in rows
        if row and row[0].startswith("Note: details are listed")
    ]
