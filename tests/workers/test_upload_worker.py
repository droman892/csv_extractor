from unittest.mock import MagicMock, patch

from src.workers.upload_worker import (
    MAX_DISPLAYED_ROWS,
    UploadWorker,
    build_display_result,
    count_validation_errors,
    run_processing,
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
        "invalid_records": invalid_records
    }

    display_result = build_display_result(result)

    assert len(display_result["invalid_records"]) == 100
    assert display_result["total_invalid_record_count"] == 150
    assert display_result["total_invalid_error_count"] == 150


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
            fake_queue
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