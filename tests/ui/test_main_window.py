from unittest.mock import MagicMock, patch

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QWidget

from src.ui.main_window import MainWindow
from src.ui.upload_view import UploadView


class FakeViewModel(QWidget):
    export_started = Signal()
    export_completed = Signal(str)
    export_failed = Signal(str)

    def __init__(self):
        super().__init__()


class FakeResultsView(QWidget):
    upload_another_file_requested = Signal()

    def __init__(self, display_result, full_result_path):
        super().__init__()

        self.display_result = display_result
        self.full_result_path = full_result_path
        self.view_model = FakeViewModel()


def test_main_window_initializes_with_upload_view(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert isinstance(
        window.upload_view,
        UploadView
    )

    assert (
        window.centralWidget()
        is window.upload_view
    )


def test_main_window_sets_title(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "CSV Extractor"


def test_main_window_sets_minimum_size(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.minimumSize() == QSize(
        800,
        600
    )


def test_main_window_creates_processing_overlay(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.processing_overlay is not None
    assert not window.processing_overlay.isVisible()


def test_show_processing_overlay_starts_overlay(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.processing_overlay.start = MagicMock()

    window.show_processing_overlay()

    window.processing_overlay.start.assert_called_once()


def test_show_results_view_stops_processing_overlay(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.processing_overlay.stop = MagicMock()

    display_result = {
        "filename": "test.csv",
        "total_tickets_count": 10,
        "valid_tickets_count": 8,
        "invalid_tickets_count": 2,
        "summary": {
            "total_hours": 20.0,
            "tickets_by_status": {},
            "tickets_by_priority": {},
            "hours_by_customer": {},
        },
        "invalid_records": [],
        "total_customer_count": 0,
        "total_invalid_record_count": 0,
        "total_invalid_error_count": 0,
    }

    full_result_path = (
        "C:/temp/csv_extractor_result.pkl"
    )

    result = {
        "display_result": display_result,
        "full_result_path": full_result_path,
    }

    with patch(
        "src.ui.main_window.ResultsView",
        FakeResultsView
    ):
        window.show_results_view(result)

    window.processing_overlay.stop.assert_called_once()

    assert isinstance(
        window.results_view,
        FakeResultsView
    )

    assert (
        window.results_view.display_result
        is display_result
    )

    assert (
        window.results_view.full_result_path
        == full_result_path
    )

    assert (
        window.centralWidget()
        is window.results_view
    )


def test_show_processing_error_stops_overlay_and_forwards_error(
    qtbot
):
    window = MainWindow()
    qtbot.addWidget(window)

    window.processing_overlay.stop = MagicMock()
    window.upload_view.show_processing_error = MagicMock()

    window.show_processing_error(
        "Processing failed"
    )

    window.processing_overlay.stop.assert_called_once()

    window.upload_view.show_processing_error.assert_called_once_with(
        "Processing failed"
    )


def test_hide_processing_overlay_stops_overlay(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.processing_overlay.stop = MagicMock()

    window.hide_processing_overlay()

    window.processing_overlay.stop.assert_called_once()


def test_show_upload_view_replaces_results_view(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.results_view = MagicMock()

    window.show_upload_view()

    assert window.results_view is None
    assert isinstance(
        window.upload_view,
        UploadView
    )

    assert (
        window.centralWidget()
        is window.upload_view
    )


def test_main_window_resizes_processing_overlay(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show()
    qtbot.waitExposed(window)

    window.resize(
        1000,
        700
    )

    qtbot.wait(50)

    assert (
        window.processing_overlay.geometry()
        == window.rect()
    )