from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject, Signal, QThread

from src.ui.view_models.upload_view_model import UploadViewModel


class FakeUploadWorker(QObject):
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def process_file(self):
        pass


class CompletingUploadWorker(QObject):
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def process_file(self):
        self.completed.emit(
            {"filename": self.filename}
        )


class FailingUploadWorker(QObject):
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def process_file(self):
        self.failed.emit(
            "Processing failed"
        )


def create_test_thread():
    thread = QThread()
    thread.start = MagicMock()

    return thread


def test_upload_file_creates_worker_with_filename():
    view_model = UploadViewModel()
    thread = create_test_thread()

    with patch(
        "src.ui.view_models.upload_view_model.UploadWorker",
        FakeUploadWorker
    ), patch(
        "src.ui.view_models.upload_view_model.QThread",
        return_value=thread
    ):
        view_model.upload_file("test.csv")

    assert view_model.worker.filename == "test.csv"

    thread.finished.emit()


def test_upload_file_creates_thread():
    view_model = UploadViewModel()
    thread = create_test_thread()

    with patch(
        "src.ui.view_models.upload_view_model.UploadWorker",
        FakeUploadWorker
    ), patch(
        "src.ui.view_models.upload_view_model.QThread",
        return_value=thread
    ):
        view_model.upload_file("test.csv")

    assert view_model.thread is thread

    thread.finished.emit()


def test_upload_file_moves_worker_to_thread():
    view_model = UploadViewModel()
    thread = create_test_thread()

    with patch(
        "src.ui.view_models.upload_view_model.UploadWorker",
        FakeUploadWorker
    ), patch(
        "src.ui.view_models.upload_view_model.QThread",
        return_value=thread
    ):
        view_model.upload_file("test.csv")

    assert view_model.worker.thread() is thread

    thread.finished.emit()


def test_upload_file_starts_thread():
    view_model = UploadViewModel()
    thread = create_test_thread()

    with patch(
        "src.ui.view_models.upload_view_model.UploadWorker",
        FakeUploadWorker
    ), patch(
        "src.ui.view_models.upload_view_model.QThread",
        return_value=thread
    ):
        view_model.upload_file("test.csv")

    thread.start.assert_called_once()

    thread.finished.emit()


def test_upload_file_forwards_completed_signal():
    view_model = UploadViewModel()
    thread = create_test_thread()

    received_results = []

    view_model.processing_completed.connect(
        received_results.append
    )

    with patch(
        "src.ui.view_models.upload_view_model.UploadWorker",
        FakeUploadWorker
    ), patch(
        "src.ui.view_models.upload_view_model.QThread",
        return_value=thread
    ):
        view_model.upload_file("test.csv")

        result = {"filename": "test.csv"}

        view_model.worker.completed.emit(result)

    assert received_results == [result]

    thread.finished.emit()


def test_upload_file_forwards_failed_signal():
    view_model = UploadViewModel()
    thread = create_test_thread()

    received_errors = []

    view_model.processing_failed.connect(
        received_errors.append
    )

    with patch(
        "src.ui.view_models.upload_view_model.UploadWorker",
        FakeUploadWorker
    ), patch(
        "src.ui.view_models.upload_view_model.QThread",
        return_value=thread
    ):
        view_model.upload_file("test.csv")

        error = "Missing required columns"

        view_model.worker.failed.emit(error)

    assert received_errors == [error]

    thread.finished.emit()


def test_upload_file_completed_worker_stops_thread(qtbot):
    view_model = UploadViewModel()
    thread = QThread()

    with patch(
        "src.ui.view_models.upload_view_model.UploadWorker",
        CompletingUploadWorker
    ), patch(
        "src.ui.view_models.upload_view_model.QThread",
        return_value=thread
    ):
        with qtbot.waitSignal(
            thread.finished,
            timeout=1000
        ):
            view_model.upload_file("test.csv")

    assert thread.isFinished()


def test_upload_file_failed_worker_stops_thread(qtbot):
    view_model = UploadViewModel()
    thread = QThread()

    with patch(
        "src.ui.view_models.upload_view_model.UploadWorker",
        FailingUploadWorker
    ), patch(
        "src.ui.view_models.upload_view_model.QThread",
        return_value=thread
    ):
        with qtbot.waitSignal(
            thread.finished,
            timeout=1000
        ):
            view_model.upload_file("test.csv")

    assert thread.isFinished()


def test_processing_finished_clears_worker_and_thread():
    view_model = UploadViewModel()

    view_model.worker = MagicMock()
    view_model.thread = MagicMock()

    view_model.processing_finished()

    assert view_model.worker is None
    assert view_model.thread is None