from PySide6.QtWidgets import QMainWindow, QMessageBox
from .upload_view import UploadView
from .results_view import ResultsView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CSV Extractor")
        self.resize(800, 600)

        self.show_upload_view()

    def show_upload_view(self):
        self.upload_view = UploadView()

        self.upload_view.view_model.processing_failed.connect(
            self.show_processing_error
        )
        
        self.upload_view.view_model.processing_completed.connect(
            self.show_results_view
        )

        self.setCentralWidget(self.upload_view)

    def show_processing_error(self, message):
        QMessageBox.critical(
            self,
            "Unable to Process File",
            message
        )

    def show_results_view(self, result):
        self.results_view = ResultsView(result)

        self.results_view.upload_another_file_requested.connect(
            self.show_upload_view
        )

        self.setCentralWidget(self.results_view) 