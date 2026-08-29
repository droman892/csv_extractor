from PySide6.QtWidgets import QMainWindow

from .upload_view import UploadView
from .results_view import ResultsView
from .processing_overlay import ProcessingOverlay


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CSV Extractor")
        self.resize(800, 600)
        self.setMinimumSize(800, 600)

        self.show_upload_view()

    def show_upload_view(self):
        if hasattr(self, "results_view"):
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

        self.setCentralWidget(self.upload_view)

        self.processing_overlay = ProcessingOverlay(self)
        self.processing_overlay.setGeometry(
            self.rect()
        )

    def show_processing_overlay(self):
        self.processing_overlay.setGeometry(
            self.rect()
        )

        self.processing_overlay.start()

    def show_results_view(self, result):
        display_result = result["display_result"]
        full_result = result["result"]

        self.results_view = ResultsView(
            display_result,
            full_result
        )

        self.results_view.upload_another_file_requested.connect(
            self.show_upload_view
        )

        self.setCentralWidget(
            self.results_view
        )

    def show_processing_error(self, message):
        self.processing_overlay.stop()

        self.upload_view.show_processing_error(message)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(self, "processing_overlay"):
            self.processing_overlay.setGeometry(
                self.rect()
            )