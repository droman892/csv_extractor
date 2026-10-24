from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from csv_extractor.ui.main_window import MainWindow
from csv_extractor.ui.upload_view import UploadView


DISPLAY_RESULT = {
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


class FakeViewModel(QWidget):
    export_started = Signal()
    export_completed = Signal(str)
    export_failed = Signal(str)

    def __init__(self):
        super().__init__()

        self.shutdown_called = False

    def shutdown(self):
        self.shutdown_called = True


class FakeResultsView(QWidget):
    upload_another_file_requested = Signal()

    def __init__(self, display_result, full_result_path):
        super().__init__()

        self.display_result = display_result
        self.full_result_path = full_result_path
        self.view_model = FakeViewModel()

        self.export_completed = MagicMock()
        self.export_failed = MagicMock()


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


def test_returning_to_upload_view_reuses_processing_overlay(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    overlay = window.processing_overlay

    window.show_upload_view()
    window.show_upload_view()

    assert window.processing_overlay is overlay
    assert window.findChildren(type(overlay)) == [overlay]


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

    display_result = DISPLAY_RESULT

    full_result_path = (
        "C:/temp/csv_extractor_result.json"
    )

    result = {
        "display_result": display_result,
        "full_result_path": full_result_path,
    }

    with patch(
        "csv_extractor.ui.main_window.ResultsView",
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


def test_processing_failed_shows_error_once_after_hiding_overlay(
    qtbot
):
    # Emits the real view model signal so the test covers the signal
    # wiring, not just the slot. Each beep records whether the spinner
    # was already hidden, which checks both how many times the error is
    # shown and the order of the slots.
    window = MainWindow()
    qtbot.addWidget(window)

    window.upload_view.selected_filename = "test.csv"
    window.show_processing_overlay()

    overlay_hidden_at_beep = []

    with patch(
        "csv_extractor.ui.upload_view.winsound"
    ) as winsound:
        winsound.MessageBeep.side_effect = (
            lambda *args: overlay_hidden_at_beep.append(
                window.processing_overlay.isHidden()
            )
        )

        window.upload_view.view_model.processing_failed.emit(
            "Invalid CSV file."
        )

    assert overlay_hidden_at_beep == [True]

    assert "Invalid CSV file." in (
        window.upload_view.error_message.text()
    )


@pytest.mark.parametrize(
    "signal_name",
    ["export_completed", "export_failed"]
)
def test_export_result_opens_one_dialog_after_hiding_overlay(
    qtbot,
    tmp_path,
    signal_name
):
    # Uses the real ResultsView so that a slot connected inside it would
    # also open a dialog and fail the test. The dialog is modal, so the
    # spinner must already be hidden when it opens.
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_results_view({
        "display_result": DISPLAY_RESULT,
        "full_result_path": str(tmp_path / "result.json"),
    })

    window.show_processing_overlay()

    overlay_hidden_at_dialog = []

    def fake_exec(message_box):
        overlay_hidden_at_dialog.append(
            window.processing_overlay.isHidden()
        )

    with patch.object(
        QMessageBox,
        "exec",
        fake_exec
    ):
        getattr(
            window.results_view.view_model,
            signal_name
        ).emit("detail")

    assert overlay_hidden_at_dialog == [True]
    assert window.results_view.export_button.isEnabled()


def test_show_export_completed_stops_overlay_and_forwards(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.results_view = FakeResultsView({}, "result.json")
    window.processing_overlay.stop = MagicMock()

    window.show_export_completed("C:/temp/export.csv")

    window.processing_overlay.stop.assert_called_once()

    window.results_view.export_completed.assert_called_once_with(
        "C:/temp/export.csv"
    )


def test_show_export_error_stops_overlay_and_forwards(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.results_view = FakeResultsView({}, "result.json")
    window.processing_overlay.stop = MagicMock()

    window.show_export_error("Disk full")

    window.processing_overlay.stop.assert_called_once()

    window.results_view.export_failed.assert_called_once_with(
        "Disk full"
    )


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


def test_close_shuts_down_the_upload_view_model(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    with patch.object(
        window.upload_view.view_model,
        "shutdown"
    ) as shutdown:
        window.close()

    shutdown.assert_called_once()


def test_close_shuts_down_the_results_view_model(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.results_view = FakeResultsView({}, "result.json")

    window.close()

    assert window.results_view.view_model.shutdown_called


def test_close_works_when_there_are_no_results(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.close()
