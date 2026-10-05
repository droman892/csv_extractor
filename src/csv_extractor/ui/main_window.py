import logging

from typing import Any

from PySide6.QtGui import QCloseEvent, QResizeEvent
from PySide6.QtWidgets import QMainWindow

from ..records import CompletedPayload
from .upload_view import UploadView
from .results_view import ResultsView
from .processing_overlay import ProcessingOverlay

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CSV Extractor")
        self.resize(800, 600)
        self.setMinimumSize(800, 600)

        self.results_view: ResultsView | None = None

        self.show_upload_view()

    def show_upload_view(self) -> None:
        if self.results_view is not None:
            self.results_view.view_model.cleanup_full_result()

            self.results_view = None

        self.upload_view = UploadView()

        self.upload_view.processing_started.connect(
            self.show_processing_overlay
        )

        self.upload_view.view_model.processing_completed.connect(
            self.show_results_view
        )

        self.upload_view.view_model.processing_failed.connect(
            self.show_processing_error
        )

        self.setCentralWidget(
            self.upload_view
        )

        self.processing_overlay = ProcessingOverlay(
            self
        )

        self.processing_overlay.setGeometry(
            self.rect()
        )

    def show_processing_overlay(self) -> None:
        self.processing_overlay.setGeometry(
            self.rect()
        )

        self.processing_overlay.start()

    def show_results_view(self, result: CompletedPayload) -> None:
        self.processing_overlay.stop()

        display_result = result[
            "display_result"
        ]

        full_result_path = result[
            "full_result_path"
        ]

        self.results_view = ResultsView(
            display_result,
            full_result_path
        )

        self.results_view.upload_another_file_requested.connect(
            self.show_upload_view
        )

        self.results_view.view_model.export_started.connect(
            self.show_processing_overlay
        )

        self.results_view.view_model.export_completed.connect(
            self.hide_processing_overlay
        )

        self.results_view.view_model.export_failed.connect(
            self.hide_processing_overlay
        )

        self.setCentralWidget(
            self.results_view
        )

    def show_processing_error(self, message: str) -> None:
        self.processing_overlay.stop()

        self.upload_view.show_processing_error(
            message
        )

    def hide_processing_overlay(self, *args: Any) -> None:
        self.processing_overlay.stop()

    def closeEvent(self, event: QCloseEvent) -> None:
        # Closing stops any processing or export that is still running,
        # silently, and removes the files they leave behind.
        logger.info("Window closing")

        self.upload_view.view_model.shutdown()

        if self.results_view is not None:
            self.results_view.view_model.shutdown()

        super().closeEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        if hasattr(
            self,
            "processing_overlay"
        ):
            self.processing_overlay.setGeometry(
                self.rect()
            )