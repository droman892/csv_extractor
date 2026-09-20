import pickle
from queue import Empty
from unittest.mock import MagicMock, patch

import pytest

from src.processing.invalid_tickets import (
    iter_invalid_tickets,
    open_for_writing,
    write_invalid_ticket
)
from src.workers.process_utils import details_path_for
from src.workers.upload_worker import (
    MAX_DISPLAYED_ROWS,
    UploadWorker,
    build_display_result,
    count_validation_errors,
    run_processing,
    save_full_result,
)


RESULT = {
    "filename": "test.csv",
    "total_tickets_count": 10,
    "valid_tickets_count": 8,
    "invalid_tickets_count": 2,
    "total_validation_error_count": 3,
    "summary": {
        "total_hours": 20.0,
        "tickets_by_status": {
            "open": 6,
            "closed": 4
        },
        "tickets_by_priority": {
            "high": 5,
            "medium": 3,
            "low": 2
        },
        "hours_by_customer": {
            "Acme Corp": 12.0,
            "Globex": 8.0
        }
    },
    "invalid_records": [
        {
            "ticket_id": "1001",
            "customer": "Acme Corp",
            "priority": "urgent",
            "status": "open",
            "hours": 2.0,
            "errors": [
                {
                    "field": "priority",
                    "invalid_value": "urgent",
                    "reason": "Invalid priority."
                }
            ]
        },
        {
            "ticket_id": "1002",
            "customer": "Globex",
            "priority": "high",
            "status": "pending",
            "hours": None,
            "errors": [
                {
                    "field": "hours",
                    "invalid_value": "45",
                    "reason": "Hours must be between 0 and 40."
                },
                {
                    "field": "status",
                    "invalid_value": "pending",
                    "reason": "Invalid status."
                }
            ]
        }
    ]
}


def test_count_validation_errors_counts_all_errors():
    assert count_validation_errors(RESULT) == 3


def test_count_validation_errors_handles_record_without_errors():
    result = {
        "invalid_records": [
            {
                "ticket_id": "1001"
            },
            {
                "ticket_id": "1002",
                "errors": [
                    {
                        "field": "hours",
                        "invalid_value": "45",
                        "reason": "Invalid hours."
                    }
                ]
            }
        ]
    }

    assert count_validation_errors(result) == 1


def test_build_display_result_preserves_filename():
    display_result = build_display_result(RESULT)

    assert display_result["filename"] == "test.csv"


def test_build_display_result_preserves_ticket_counts():
    display_result = build_display_result(RESULT)

    assert display_result["total_tickets_count"] == 10
    assert display_result["valid_tickets_count"] == 8
    assert display_result["invalid_tickets_count"] == 2


def test_build_display_result_preserves_summary_values():
    display_result = build_display_result(RESULT)

    assert display_result["summary"]["total_hours"] == 20.0

    assert display_result["summary"]["tickets_by_status"] == {
        "open": 6,
        "closed": 4
    }

    assert display_result["summary"]["tickets_by_priority"] == {
        "high": 5,
        "medium": 3,
        "low": 2
    }


def test_build_display_result_sorts_customers_case_insensitively():
    result = {
        **RESULT,
        "summary": {
            **RESULT["summary"],
            "hours_by_customer": {
                "zeta": 5.0,
                "Acme": 10.0,
                "beta": 7.0
            }
        }
    }

    display_result = build_display_result(result)

    assert list(
        display_result["summary"]["hours_by_customer"].keys()
    ) == [
        "Acme",
        "beta",
        "zeta"
    ]


def test_build_display_result_limits_customers_to_100():
    customers = {
        f"Customer {index:03d}": float(index)
        for index in range(150)
    }

    result = {
        **RESULT,
        "summary": {
            **RESULT["summary"],
            "hours_by_customer": customers
        }
    }

    display_result = build_display_result(result)

    displayed_customers = (
        display_result["summary"]["hours_by_customer"]
    )

    assert len(displayed_customers) == MAX_DISPLAYED_ROWS
    assert display_result["total_customer_count"] == 150


def test_build_display_result_flattens_validation_errors():
    display_result = build_display_result(RESULT)

    assert display_result["invalid_records"] == [
        {
            "ticket_id": "1001",
            "field": "priority",
            "invalid_value": "urgent",
            "reason": "Invalid priority."
        },
        {
            "ticket_id": "1002",
            "field": "hours",
            "invalid_value": "45",
            "reason": "Hours must be between 0 and 40."
        },
        {
            "ticket_id": "1002",
            "field": "status",
            "invalid_value": "pending",
            "reason": "Invalid status."
        }
    ]


def test_build_display_result_limits_validation_errors_to_100():
    invalid_records = []

    for index in range(150):
        invalid_records.append({
            "ticket_id": str(index),
            "errors": [
                {
                    "field": "hours",
                    "invalid_value": "45",
                    "reason": "Invalid hours."
                }
            ]
        })

    result = {
        **RESULT,
        "invalid_tickets_count": 150,
        "total_validation_error_count": 150,
        "invalid_records": invalid_records
    }

    display_result = build_display_result(result)

    assert len(display_result["invalid_records"]) == 100
    assert display_result["total_invalid_record_count"] == 150
    assert display_result["total_invalid_error_count"] == 150


def test_build_display_result_reads_the_first_errors_from_the_details_file(
    tmp_path
):
    details = tmp_path / "invalid.jsonl"

    with open_for_writing(details) as file:
        for index in range(120):
            write_invalid_ticket(
                file,
                {
                    "ticket_id": str(index),
                    "errors": [
                        {
                            "field": "hours",
                            "invalid_value": "45",
                            "reason": "Invalid hours."
                        }
                    ]
                }
            )

    result = {
        **RESULT,
        "invalid_tickets_count": 1_000_000,
        "total_validation_error_count": 1_500_000,
        "invalid_records": [],
        "invalid_details_path": str(details)
    }

    display_result = build_display_result(result)

    assert len(display_result["invalid_records"]) == 100
    assert display_result["invalid_records"][0]["ticket_id"] == "0"
    assert display_result["total_invalid_record_count"] == 1_000_000
    assert display_result["total_invalid_error_count"] == 1_500_000

    # The details file was closed, so it can be deleted (Windows would
    # refuse to delete a file that is still open).
    details.unlink()


def test_build_display_result_counts_invalid_records():
    display_result = build_display_result(RESULT)

    assert display_result["total_invalid_record_count"] == 2


def test_build_display_result_counts_invalid_errors():
    display_result = build_display_result(RESULT)

    assert display_result["total_invalid_error_count"] == 3


def test_build_display_result_counts_total_customers():
    display_result = build_display_result(RESULT)

    assert display_result["total_customer_count"] == 2


def test_run_processing_puts_completed_result_in_queue():
    result_queue = MagicMock()

    with patch(
        "src.workers.upload_worker.process_csv",
        return_value=RESULT
    ), patch(
        "src.workers.upload_worker.save_full_result",
        return_value="C:/temp/result.pkl"
    ):

        run_processing(
            "test.csv",
            result_queue
        )

    result_queue.put.assert_called_once()

    status, value = result_queue.put.call_args.args[0]

    assert status == "completed"

    assert value["display_result"]["filename"] == "test.csv"

    assert value["full_result_path"] == (
        "C:/temp/result.pkl"
    )


def test_run_processing_puts_value_error_in_queue():
    result_queue = MagicMock()

    with patch(
        "src.workers.upload_worker.process_csv",
        side_effect=ValueError("Invalid CSV file.")
    ):
        run_processing(
            "test.csv",
            result_queue
        )

    result_queue.put.assert_called_once_with(
        (
            "failed",
            "ValueError: Invalid CSV file."
        )
    )


def test_run_processing_puts_unexpected_error_in_queue():
    result_queue = MagicMock()

    with patch(
        "src.workers.upload_worker.process_csv",
        side_effect=RuntimeError("Unexpected failure.")
    ):
        run_processing(
            "test.csv",
            result_queue
        )

    result_queue.put.assert_called_once_with(
        (
            "failed",
            "RuntimeError: Unexpected failure."
        )
    )


def test_upload_worker_stores_filename():
    worker = UploadWorker("test.csv")

    assert worker.filename == "test.csv"


def test_upload_worker_initializes_process_to_none():
    worker = UploadWorker("test.csv")

    assert worker.process is None


def test_upload_worker_initializes_result_queue_to_none():
    worker = UploadWorker("test.csv")

    assert worker.result_queue is None


def test_upload_worker_initializes_poll_timer_to_none():
    worker = UploadWorker("test.csv")

    assert worker.poll_timer is None


def test_process_file_creates_result_queue():
    worker = UploadWorker("test.csv")

    fake_queue = MagicMock()
    fake_process = MagicMock()

    with patch(
        "src.workers.upload_worker.Queue",
        return_value=fake_queue
    ), patch(
        "src.workers.upload_worker.Process",
        return_value=fake_process
    ), patch(
        "src.workers.upload_worker.QTimer",
        return_value=MagicMock()
    ):
        worker.process_file()

    assert worker.result_queue is fake_queue


def test_process_file_creates_process_with_expected_arguments():
    worker = UploadWorker("test.csv")

    fake_queue = MagicMock()
    fake_process = MagicMock()

    with patch(
        "src.workers.upload_worker.Queue",
        return_value=fake_queue
    ), patch(
        "src.workers.upload_worker.Process",
        return_value=fake_process
    ) as process_class, patch(
        "src.workers.upload_worker.QTimer",
        return_value=MagicMock()
    ):
        worker.process_file()

    process_class.assert_called_once_with(
        target=run_processing,
        args=(
            "test.csv",
            fake_queue,
            worker.full_result_path
        )
    )


def test_process_file_starts_process():
    worker = UploadWorker("test.csv")

    fake_queue = MagicMock()
    fake_process = MagicMock()
    fake_timer = MagicMock()

    with patch(
        "src.workers.upload_worker.Queue",
        return_value=fake_queue
    ), patch(
        "src.workers.upload_worker.Process",
        return_value=fake_process
    ), patch(
        "src.workers.upload_worker.QTimer",
        return_value=fake_timer
    ):
        worker.process_file()

    fake_process.start.assert_called_once()


def test_process_file_creates_poll_timer():
    worker = UploadWorker("test.csv")

    fake_queue = MagicMock()
    fake_process = MagicMock()

    with patch(
        "src.workers.upload_worker.Queue",
        return_value=fake_queue
    ), patch(
        "src.workers.upload_worker.Process",
        return_value=fake_process
    ):
        worker.process_file()

    assert worker.poll_timer is not None
    assert worker.poll_timer.interval() == 50


def test_check_result_returns_when_queue_is_empty():
    worker = UploadWorker("test.csv")

    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.side_effect = Empty
    worker.poll_timer = MagicMock()
    worker.process = MagicMock()

    worker.check_result()

    worker.poll_timer.stop.assert_not_called()


def test_check_result_emits_completed_and_cleans_up():
    worker = UploadWorker("test.csv")

    fake_process = MagicMock()
    fake_queue = MagicMock()
    fake_queue.get_nowait.return_value = (
        "completed",
        {"display_result": {}, "full_result_path": "x.pkl"}
    )

    worker.result_queue = fake_queue
    worker.poll_timer = MagicMock()
    worker.process = fake_process

    emitted = []
    worker.completed.connect(emitted.append)

    worker.check_result()

    assert emitted == [
        {"display_result": {}, "full_result_path": "x.pkl"}
    ]
    worker.poll_timer.stop.assert_called_once()
    fake_process.join.assert_called_once()
    fake_queue.close.assert_called_once()
    assert worker.process is None
    assert worker.result_queue is None


def test_check_result_emits_failed():
    worker = UploadWorker("test.csv")

    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "failed",
        "ValueError: bad file"
    )
    worker.poll_timer = MagicMock()
    worker.process = MagicMock()

    emitted = []
    worker.failed.connect(emitted.append)

    worker.check_result()

    assert emitted == ["ValueError: bad file"]


def test_check_result_reports_failure_when_the_process_died():
    worker = UploadWorker("test.csv")

    dead_process = MagicMock()
    dead_process.is_alive.return_value = False
    dead_process.exitcode = -9

    fake_queue = MagicMock()
    fake_queue.get_nowait.side_effect = Empty
    fake_queue.get.side_effect = Empty

    worker.result_queue = fake_queue
    worker.poll_timer = MagicMock()
    worker.process = dead_process

    emitted = []
    worker.failed.connect(emitted.append)

    worker.check_result()

    assert len(emitted) == 1
    assert "stopped unexpectedly" in emitted[0]
    worker.poll_timer.stop.assert_called_once()
    assert worker.process is None


def test_process_file_chooses_a_unique_result_path_in_the_temp_folder():
    first = UploadWorker("test.csv")
    second = UploadWorker("test.csv")

    for worker in (first, second):
        with patch(
            "src.workers.upload_worker.Queue",
            return_value=MagicMock()
        ), patch(
            "src.workers.upload_worker.Process",
            return_value=MagicMock()
        ):
            worker.process_file()

        worker.poll_timer.stop()

    assert first.full_result_path != second.full_result_path
    assert first.full_result_path.endswith(".pkl")


def test_save_full_result_writes_to_the_given_path(tmp_path):
    path = tmp_path / "result.pkl"

    assert save_full_result({"a": 1}, str(path)) == str(path)

    with open(path, "rb") as saved:
        assert pickle.load(saved) == {"a": 1}


def test_save_full_result_will_not_overwrite_an_existing_file(tmp_path):
    path = tmp_path / "result.pkl"
    path.write_bytes(b"keep me")

    with pytest.raises(RuntimeError):
        save_full_result({"a": 1}, str(path))

    assert path.read_bytes() == b"keep me"


def test_run_processing_saves_the_result_at_the_given_path(tmp_path):
    csv_file = tmp_path / "t.csv"
    csv_file.write_text(
        "ticket_id,customer,priority,status,hours\n"
        "100000001,Acme,high,open,2.5\n",
        encoding="utf-8"
    )

    path = tmp_path / "result.pkl"
    result_queue = MagicMock()

    run_processing(str(csv_file), result_queue, str(path))

    status, value = result_queue.put.call_args.args[0]

    assert status == "completed"
    assert value["full_result_path"] == str(path)
    assert path.exists()


def test_stop_kills_a_running_process_and_deletes_the_partial_result(
    tmp_path
):
    partial = tmp_path / "partial.pkl"
    partial.write_bytes(b"half")

    worker = UploadWorker("test.csv")
    worker.full_result_path = str(partial)
    worker.process = MagicMock()
    worker.process.is_alive.return_value = True

    worker.stop()

    worker.process.terminate.assert_called_once()
    assert not partial.exists()


def test_stop_keeps_the_result_of_a_process_that_already_finished(
    tmp_path
):
    finished = tmp_path / "result.pkl"
    finished.write_bytes(b"complete")

    worker = UploadWorker("test.csv")
    worker.full_result_path = str(finished)
    worker.process = MagicMock()
    worker.process.is_alive.return_value = False

    worker.stop()

    worker.process.terminate.assert_not_called()
    assert finished.exists()


def test_stop_does_nothing_without_a_process():
    UploadWorker("test.csv").stop()


def test_nothing_is_emitted_after_stop():
    worker = UploadWorker("test.csv")

    worker.process = MagicMock()
    worker.process.is_alive.return_value = True
    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "failed",
        "anything"
    )
    worker.poll_timer = MagicMock()

    emitted = []
    worker.failed.connect(emitted.append)
    worker.completed.connect(emitted.append)

    worker.stop()
    worker.check_result()

    assert emitted == []


def test_a_failed_run_deletes_its_result_file(tmp_path):
    leftover = tmp_path / "leftover.pkl"
    leftover.write_bytes(b"x")

    worker = UploadWorker("test.csv")
    worker.full_result_path = str(leftover)
    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "failed",
        "ValueError: bad file"
    )
    worker.poll_timer = MagicMock()
    worker.process = MagicMock()

    worker.check_result()

    assert not leftover.exists()


def test_run_processing_explains_a_file_that_is_not_utf8():
    result_queue = MagicMock()

    with patch(
        "src.workers.upload_worker.process_csv",
        side_effect=UnicodeDecodeError(
            "utf-8",
            b"\xe9",
            0,
            1,
            "invalid continuation byte"
        )
    ):
        run_processing(
            "test.csv",
            result_queue
        )

    status, message = result_queue.put.call_args.args[0]

    assert status == "failed"
    assert "not valid UTF-8" in message
    assert "CSV UTF-8" in message
    assert "codec" not in message


def test_run_processing_reports_a_real_non_utf8_file(tmp_path):
    csv_file = tmp_path / "latin1.csv"

    csv_file.write_bytes(
        b"ticket_id,customer,priority,status,hours\n"
        b"100000001,Caf\xe9,high,open,2.5\n"
    )

    result_queue = MagicMock()

    run_processing(
        str(csv_file),
        result_queue
    )

    status, message = result_queue.put.call_args.args[0]

    assert status == "failed"
    assert "not valid UTF-8" in message


def test_run_processing_reports_a_utf16_file_the_same_way(tmp_path):
    csv_file = tmp_path / "utf16.csv"

    csv_file.write_text(
        "ticket_id,customer,priority,status,hours\n"
        "100000001,Acme,high,open,2.5\n",
        encoding="utf-16"
    )

    result_queue = MagicMock()

    run_processing(
        str(csv_file),
        result_queue
    )

    status, message = result_queue.put.call_args.args[0]

    assert status == "failed"
    assert "not valid UTF-8" in message


def test_run_processing_writes_the_invalid_tickets_beside_the_result_file(
    tmp_path
):
    csv_file = tmp_path / "t.csv"
    csv_file.write_text(
        "ticket_id,customer,priority,status,hours\n"
        "100000001,Acme,high,open,2.5\n"
        "100000002,Acme,urgent,open,2.5\n",
        encoding="utf-8"
    )

    path = tmp_path / "result.pkl"
    result_queue = MagicMock()

    run_processing(str(csv_file), result_queue, str(path))

    status, value = result_queue.put.call_args.args[0]

    assert status == "completed"

    details = details_path_for(str(path))

    with open(path, "rb") as saved:
        full_result = pickle.load(saved)

    # The result file holds no invalid tickets; the details file does.
    assert full_result["invalid_records"] == []
    assert full_result["invalid_details_path"] == details
    assert [
        ticket["ticket_id"]
        for ticket in iter_invalid_tickets(full_result)
    ] == ["100000002"]

    assert value["display_result"]["invalid_records"][0]["ticket_id"] == (
        "100000002"
    )


def test_run_processing_without_a_path_still_writes_both_files():
    result_queue = MagicMock()

    with patch(
        "src.workers.upload_worker.process_csv",
        return_value=RESULT
    ) as process_csv, patch(
        "src.workers.upload_worker.save_full_result",
        return_value="C:/temp/result.pkl"
    ) as save:
        run_processing("test.csv", result_queue)

    result_path = save.call_args.args[1]

    assert process_csv.call_args.args == (
        "test.csv",
        details_path_for(result_path)
    )


def test_stop_deletes_the_partial_details_file_too(tmp_path):
    partial = tmp_path / "partial.pkl"
    partial.write_bytes(b"half")
    partial_details = tmp_path / "partial.invalid.jsonl"
    partial_details.write_text("half")

    worker = UploadWorker("test.csv")
    worker.full_result_path = str(partial)
    worker.process = MagicMock()
    worker.process.is_alive.return_value = True

    worker.stop()

    assert not partial.exists()
    assert not partial_details.exists()


def test_a_failed_run_deletes_the_details_file_too(tmp_path):
    leftover = tmp_path / "leftover.pkl"
    leftover.write_bytes(b"x")
    leftover_details = tmp_path / "leftover.invalid.jsonl"
    leftover_details.write_text("x")

    worker = UploadWorker("test.csv")
    worker.full_result_path = str(leftover)
    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "failed",
        "ValueError: bad file"
    )
    worker.poll_timer = MagicMock()
    worker.process = MagicMock()

    worker.check_result()

    assert not leftover.exists()
    assert not leftover_details.exists()
