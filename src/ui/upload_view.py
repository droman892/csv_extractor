from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .view_models.upload_view_model import UploadViewModel

class UploadView(QWidget):
    def __init__(self):
        super().__init__()

        self.view_model = UploadViewModel()

        title = QLabel("CSV Extractor")
        description = QLabel(
            "Upload a CSV file to validate and analyze support tickets."
        )
        upload_button = QPushButton("Upload a File")

        upload_button.clicked.connect(self.handle_upload_clicked)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(upload_button)

        self.setLayout(layout)

    def handle_upload_clicked(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv)",
        )

        if filename:
            self.view_model.upload_file(filename)