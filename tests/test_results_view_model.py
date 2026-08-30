from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject, Signal, QThread

from src.ui.view_models.results_view_model import ResultsViewModel


RESULT = {
    "filename": "/path/to/test.csv",
    "total_tickets_count": 10,
    "valid_tickets_count": 8,
    "invalid_tickets_count": 2,
    "total_customer_count": 3,
    "total_invalid_record_count": 2,
    "total_invalid_error_count": 4,
    "invalid_records": [
        {
            "ticket_id": "1001",
            "errors": ["Invalid priority"]
        },
        {
            "ticket_id": "1002",
            "errors": ["Missing status"]
        }
    ],
    "summary": {
        "total_hours": 125.5,
        "tickets_by_status": {
            "Open": 5,
            "Closed": 5
        },
        "tickets_by_priority": {
            "High": 3,
            "Medium": 4,
            "Low": 3
        },
        "hours_by_customer": {
            "Acme": 50.0,
            "Globex": 45.5,
            "Initech": 30.0
        }
    }
}


FULL_RESULT = {
    "rows": [
        {
            "ticket_id": "1001",
            "customer": "Acme"
        }
    ]
}


class FakeExportWorker(QObject):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, full_result, destination_path):
        super().__init__()

        self.full_result = full_result
        self.destination_path = destination_path

    def export_file(self):
        pass


class CompletingExportWorker(QObject):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, full_result, destination_path):
        super().__init__()

        self.full_result = full_result
        self.destination_path = destination_path

    def export_file(self):
        self.completed.emit(self.destination_path)


class FailingExportWorker(QObject):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, full_result, destination_path):
        super().__init__()

        self.full_result = full_result
        self.destination_path = destination_path

    def export_file(self):
        self.failed.emit("Export failed")


def create_view_model():
    return ResultsViewModel(
        RESULT,
        FULL_RESULT
    )


def create_test_thread():
    thread = QThread()
    thread.start = MagicMock()

    return thread


def test_init_stores_result():
    view_model = create_view_model()

    assert view_model.result is RESULT


def test_init_stores_full_result():
    view_model = create_view_model()

    assert view_model.full_result is FULL_RESULT


def test_init_sets_export_thread_to_none():
    view_model = create_view_model()

    assert view_model.export_thread is None


def test_init_sets_export_worker_to_none():
    view_model = create_view_model()

    assert view_model.export_worker is None


def test_get_filename_returns_filename_without_path():
    view_model = create_view_model()

    assert view_model.get_filename() == "test.csv"


def test_get_summary_returns_expected_summary():
    view_model = create_view_model()

    expected = {
        "total_tickets_count": 10,
        "valid_tickets_count": 8,
        "invalid_tickets_count": 2,
        "total_hours": 125.5,
        "tickets_by_status": {
            "Open": 5,
            "Closed": 5
        },
        "tickets_by_priority": {
            "High": 3,
            "Medium": 4,
            "Low": 3
        },
        "hours_by_customer": {
            "Acme": 50.0,
            "Globex": 45.5,
            "Initech": 30.0
        }
    }

    assert view_model.get_summary() == expected


def test_get_invalid_rows_returns_invalid_records():
    view_model = create_view_model()

    assert view_model.get_invalid_rows() == RESULT["invalid_records"]


def test_get_customer_rows_returns_customer_items():
    view_model = create_view_model()

    expected = [
        ("Acme", 50.0),
        ("Globex", 45.5),
        ("Initech", 30.0)
    ]

    assert view_model.get_customer_rows() == expected


def test_get_total_customer_count_returns_count():
    view_model = create_view_model()

    assert view_model.get_total_customer_count() == 3


def test_get_total_invalid_record_count_returns_count():
    view_model = create_view_model()

    assert view_model.get_total_invalid_record_count() == 2


def test_get_total_invalid_error_count_returns_count():
    view_model = create_view_model()

    assert view_model.get_total_invalid_error_count() == 4


def test_export_results_emits_export_started():
    view_model = create_view_model()
    thread = create_test_thread()

    received = []

    view_model.export_started.connect(
        lambda: received.append(True)
    )

    with patch(
        "src.ui.view_models.results_view_model.ExportWorker",
        FakeExportWorker
    ), patch(
        "src.ui.view_models.results_view_model.QThread",
        return_value=thread
    ):
        view_model.export_results("output.xlsx")

    assert received == [True]

    thread.finished.emit()

def test_export_results_creates_worker_with_full_result_and_destination():
    view_model = create_view_model()
    thread = create_test_thread()

    with patch(
        "src.ui.view_models.results_view_model.ExportWorker",
        FakeExportWorker
    ), patch(
        "src.ui.view_models.results_view_model.QThread",
        return_value=thread
    ):
        view_model.export_results("output.xlsx")

    assert isinstance(view_model.export_worker, FakeExportWorker)
    assert view_model.export_worker.full_result is FULL_RESULT
    assert view_model.export_worker.destination_path == "output.xlsx"

    thread.finished.emit()


def test_export_results_creates_thread():
    view_model = create_view_model()
    thread = create_test_thread()

    with patch(
        "src.ui.view_models.results_view_model.ExportWorker",
        FakeExportWorker
    ), patch(
        "src.ui.view_models.results_view_model.QThread",
        return_value=thread
    ):
        view_model.export_results("output.xlsx")

    assert view_model.export_thread is thread

    thread.finished.emit()


def test_export_results_moves_worker_to_thread():
    view_model = create_view_model()
    thread = create_test_thread()

    with patch(
        "src.ui.view_models.results_view_model.ExportWorker",
        FakeExportWorker
    ), patch(
        "src.ui.view_models.results_view_model.QThread",
        return_value=thread
    ):
        view_model.export_results("output.xlsx")

    assert view_model.export_worker.thread() is thread

    thread.finished.emit()


def test_export_results_starts_thread():
    view_model = create_view_model()
    thread = create_test_thread()

    with patch(
        "src.ui.view_models.results_view_model.ExportWorker",
        FakeExportWorker
    ), patch(
        "src.ui.view_models.results_view_model.QThread",
        return_value=thread
    ):
        view_model.export_results("output.xlsx")

    thread.start.assert_called_once()

    thread.finished.emit()


def test_export_results_forwards_completed_signal():
    view_model = create_view_model()
    thread = create_test_thread()

    received_results = []

    view_model.export_completed.connect(
        received_results.append
    )

    with patch(
        "src.ui.view_models.results_view_model.ExportWorker",
        FakeExportWorker
    ), patch(
        "src.ui.view_models.results_view_model.QThread",
        return_value=thread
    ):
        view_model.export_results("output.xlsx")

        result = "output.xlsx"

        view_model.export_worker.completed.emit(result)

    assert received_results == [result]

    thread.finished.emit()


def test_export_results_forwards_failed_signal():
    view_model = create_view_model()
    thread = create_test_thread()

    received_errors = []

    view_model.export_failed.connect(
        received_errors.append
    )

    with patch(
        "src.ui.view_models.results_view_model.ExportWorker",
        FakeExportWorker
    ), patch(
        "src.ui.view_models.results_view_model.QThread",
        return_value=thread
    ):
        view_model.export_results("output.xlsx")

        error = "Export failed"

        view_model.export_worker.failed.emit(error)

    assert received_errors == [error]

    thread.finished.emit()


def test_export_results_completed_worker_stops_thread(qtbot):
    view_model = create_view_model()
    thread = QThread()

    with patch(
        "src.ui.view_models.results_view_model.ExportWorker",
        CompletingExportWorker
    ), patch(
        "src.ui.view_models.results_view_model.QThread",
        return_value=thread
    ):
        with qtbot.waitSignal(
            thread.finished,
            timeout=1000
        ):
            view_model.export_results("output.xlsx")

    assert thread.isFinished()


def test_export_results_failed_worker_stops_thread(qtbot):
    view_model = create_view_model()
    thread = QThread()

    with patch(
        "src.ui.view_models.results_view_model.ExportWorker",
        FailingExportWorker
    ), patch(
        "src.ui.view_models.results_view_model.QThread",
        return_value=thread
    ):
        with qtbot.waitSignal(
            thread.finished,
            timeout=1000
        ):
            view_model.export_results("output.xlsx")

    assert thread.isFinished()


def test_export_finished_clears_worker_and_thread():
    view_model = create_view_model()

    view_model.export_worker = MagicMock()
    view_model.export_thread = MagicMock()

    view_model.export_finished()

    assert view_model.export_worker is None
    assert view_model.export_thread is None