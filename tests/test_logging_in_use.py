"""The application logs what happened, and never what is in the rows."""

import logging
import os
from queue import Queue
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.processing.processor import process_csv
from src.workers.export_worker import run_export
from src.workers.process_utils import poll_result, remove_file
from src.workers.upload_worker import run_processing


HEADER = "ticket_id,customer,priority,status,hours\n"


def read_log_file(tmp_path):
    """run_processing / run_export set up logging as a real background
    process would, which sends the logs to the file rather than to
    pytest's capture, so the tests read the file."""
    for handler in logging.getLogger("src").handlers:
        handler.flush()

    return (tmp_path / "test.log").read_text(encoding="utf-8")


def write_csv(tmp_path, body):
    csv_file = tmp_path / "tickets.csv"
    csv_file.write_text(HEADER + body, encoding="utf-8")
    return csv_file


def test_process_csv_logs_counts_but_never_row_contents(
    tmp_path,
    caplog
):
    caplog.set_level(logging.DEBUG)

    csv_file = write_csv(
        tmp_path,
        "100000001,SecretCorp,high,open,2.5\n"
        "100000002,SecretCorp,urgent,open,2.5\n"
    )

    process_csv(csv_file)

    text = caplog.text

    assert "Processing tickets.csv" in text
    assert "Processed 2 tickets" in text
    assert "1 valid, 1 invalid" in text

    assert "SecretCorp" not in text
    assert "100000001" not in text
    assert "urgent" not in text


def test_process_csv_logs_no_row_contents_when_writing_a_details_file(
    tmp_path,
    caplog
):
    csv_file = write_csv(
        tmp_path,
        "100000001,SecretCorp,urgent,open,2.5\n"
    )

    with caplog.at_level(logging.DEBUG):
        process_csv(csv_file, tmp_path / "invalid.jsonl")

    assert "1 invalid" in caplog.text
    assert "SecretCorp" not in caplog.text
    assert "100000001" not in caplog.text


def test_run_processing_logs_a_rejected_file(tmp_path):
    csv_file = tmp_path / "wrong.csv"
    csv_file.write_text("a,b,c\n1,2,3\n", encoding="utf-8")

    run_processing(str(csv_file), Queue())

    assert "Rejected the file: Missing required columns" in (
        read_log_file(tmp_path)
    )


def test_run_processing_logs_an_unexpected_error_with_traceback(
    tmp_path,
    monkeypatch
):
    def explode(*args):
        raise KeyError("boom")

    monkeypatch.setattr(
        "src.workers.upload_worker.process_csv",
        explode
    )

    run_processing("x.csv", Queue())

    text = read_log_file(tmp_path)

    assert "Unexpected error while processing" in text
    assert "KeyError" in text


def test_run_export_logs_a_failure(tmp_path):
    run_export(
        str(tmp_path / "missing.pkl"),
        str(tmp_path / "out.csv"),
        Queue()
    )

    assert "Export failed" in read_log_file(tmp_path)


def test_a_process_that_died_silently_is_logged(caplog):
    dead = SimpleNamespace(is_alive=lambda: False, exitcode=-9)

    with caplog.at_level(logging.ERROR):
        poll_result(dead, Queue())

    assert "exit code -9" in caplog.text


def test_remove_file_logs_a_file_it_could_not_delete(
    tmp_path,
    caplog,
    monkeypatch
):
    def refuse(path):
        raise PermissionError("in use")

    monkeypatch.setattr("src.workers.process_utils.os.remove", refuse)

    with caplog.at_level(logging.WARNING):
        remove_file(str(tmp_path / "x.pkl"))

    assert "Could not delete" in caplog.text


def test_remove_file_is_quiet_when_the_file_is_already_gone(
    tmp_path,
    caplog
):
    with caplog.at_level(logging.DEBUG):
        remove_file(str(tmp_path / "missing.pkl"))

    assert caplog.text == ""


def test_running_a_background_task_sets_up_logging_to_the_file(tmp_path):
    csv_file = write_csv(
        tmp_path,
        "100000001,A,high,open,2.5\n"
    )

    result_queue = MagicMock()

    run_processing(str(csv_file), result_queue)

    assert "Processed 1 tickets" in read_log_file(tmp_path)

    _, value = result_queue.put.call_args.args[0]

    os.remove(value["full_result_path"])
