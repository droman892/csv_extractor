from queue import Empty
from unittest.mock import MagicMock, patch

from src.ui.workers.export_worker import (
    ExportWorker,
    run_export,
)


RESULT = {
    "total_tickets_count": 10,
    "valid_tickets_count": 8,
    "invalid_tickets_count": 2,
}


def test_run_export_puts_completed_result_in_queue():
    result_queue = MagicMock()

    with patch(
        "src.ui.workers.export_worker.ResultsExportService.export_results"
    ) as export_results:
        run_export(
            RESULT,
            "output.xlsx",
            result_queue
        )

    export_results.assert_called_once_with(
        RESULT,
        "output.xlsx"
    )

    result_queue.put.assert_called_once_with(
        (
            "completed",
            "output.xlsx"
        )
    )


def test_run_export_puts_failed_result_in_queue():
    result_queue = MagicMock()

    with patch(
        "src.ui.workers.export_worker.ResultsExportService.export_results",
        side_effect=Exception("Export failed")
    ) as export_results:
        run_export(
            RESULT,
            "output.xlsx",
            result_queue
        )

    export_results.assert_called_once_with(
        RESULT,
        "output.xlsx"
    )

    result_queue.put.assert_called_once_with(
        (
            "failed",
            "Export failed"
        )
    )


def test_export_worker_stores_result():

    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    assert worker.result is RESULT


def test_export_worker_stores_destination_path():

    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    assert worker.destination_path == "output.xlsx"


def test_export_worker_initializes_process_to_none():

    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    assert worker.process is None


def test_export_worker_initializes_result_queue_to_none():

    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    assert worker.result_queue is None


def test_export_worker_initializes_poll_timer_to_none():

    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    assert worker.poll_timer is None


def test_export_file_creates_result_queue():

    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    fake_queue = MagicMock()
    fake_process = MagicMock()

    with patch(
        "src.ui.workers.export_worker.Queue",
        return_value=fake_queue
    ), patch(
        "src.ui.workers.export_worker.Process",
        return_value=fake_process
    ):
        worker.export_file()

    assert worker.result_queue is fake_queue

    worker.poll_timer.stop()


def test_export_file_creates_process_with_expected_arguments():

    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    fake_queue = MagicMock()
    fake_process = MagicMock()

    with patch(
        "src.ui.workers.export_worker.Queue",
        return_value=fake_queue
    ), patch(
        "src.ui.workers.export_worker.Process",
        return_value=fake_process
    ) as process_factory:
        worker.export_file()

    process_factory.assert_called_once_with(
        target=run_export,
        args=(
            RESULT,
            "output.xlsx",
            fake_queue
        )
    )

    worker.poll_timer.stop()


def test_export_file_starts_process():

    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    fake_queue = MagicMock()
    fake_process = MagicMock()

    with patch(
        "src.ui.workers.export_worker.Queue",
        return_value=fake_queue
    ), patch(
        "src.ui.workers.export_worker.Process",
        return_value=fake_process
    ):
        worker.export_file()

    fake_process.start.assert_called_once()

    worker.poll_timer.stop()


def test_export_file_creates_poll_timer(qtbot):

    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    fake_queue = MagicMock()
    fake_process = MagicMock()

    with patch(
        "src.ui.workers.export_worker.Queue",
        return_value=fake_queue
    ), patch(
        "src.ui.workers.export_worker.Process",
        return_value=fake_process
    ):
        worker.export_file()

    assert worker.poll_timer is not None
    assert worker.poll_timer.interval() == 50
    assert worker.poll_timer.isActive()

    worker.poll_timer.stop()


def test_check_result_returns_when_queue_is_empty():
    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.side_effect = Empty

    worker.poll_timer = MagicMock()

    worker.check_result()

    worker.poll_timer.stop.assert_not_called()


def test_check_result_stops_poll_timer():
    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "completed",
        "output.xlsx"
    )

    worker.poll_timer = MagicMock()
    worker.process = MagicMock()

    worker.check_result()

    worker.poll_timer.stop.assert_called_once()


def test_check_result_joins_and_clears_process():
    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "completed",
        "output.xlsx"
    )

    worker.poll_timer = MagicMock()

    fake_process = MagicMock()
    worker.process = fake_process

    worker.check_result()

    fake_process.join.assert_called_once()
    assert worker.process is None


def test_check_result_closes_and_clears_queue():
    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    fake_queue = MagicMock()

    worker.result_queue = fake_queue
    worker.poll_timer = MagicMock()
    worker.process = MagicMock()

    fake_queue.get_nowait.return_value = (
        "completed",
        "output.xlsx"
    )

    worker.check_result()

    fake_queue.close.assert_called_once()
    assert worker.result_queue is None


def test_check_result_emits_completed_signal():
    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "completed",
        "output.xlsx"
    )

    worker.poll_timer = MagicMock()
    worker.process = MagicMock()

    received_results = []

    worker.completed.connect(
        received_results.append
    )

    worker.check_result()

    assert received_results == [
        "output.xlsx"
    ]


def test_check_result_emits_failed_signal():
    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "failed",
        "Export failed"
    )

    worker.poll_timer = MagicMock()
    worker.process = MagicMock()

    received_errors = []

    worker.failed.connect(
        received_errors.append
    )

    worker.check_result()

    assert received_errors == [
        "Export failed"
    ]


def test_check_result_joins_process_before_emitting_completed(qtbot):
    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "completed",
        "output.xlsx"
    )

    worker.poll_timer = MagicMock()

    fake_process = MagicMock()
    worker.process = fake_process

    events = []

    fake_process.join.side_effect = (
        lambda: events.append("joined")
    )

    worker.completed.connect(
        lambda value: events.append("completed")
    )

    worker.check_result()

    assert events == [
        "joined",
        "completed"
    ]


def test_check_result_joins_process_before_emitting_failed(qtbot):
    worker = ExportWorker(
        RESULT,
        "output.xlsx"
    )

    worker.result_queue = MagicMock()
    worker.result_queue.get_nowait.return_value = (
        "failed",
        "Export failed"
    )

    worker.poll_timer = MagicMock()

    fake_process = MagicMock()
    worker.process = fake_process

    events = []

    fake_process.join.side_effect = (
        lambda: events.append("joined")
    )

    worker.failed.connect(
        lambda value: events.append("failed")
    )

    worker.check_result()

    assert events == [
        "joined",
        "failed"
    ]