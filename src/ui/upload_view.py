from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QFrame,
)

from ..services.test_file_service import TestFileService
from .view_models.upload_view_model import UploadViewModel


class UploadView(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
        QFrame#contentCard {
            border: 1px solid #d0d0d0;
            border-radius: 8px;
            background-color: #f7f7f7;
        }

        QLabel#appTitle {
            font-size: 28px;
            font-weight: bold;
        }

        QLabel#description {
            font-size: 16px;
        }

        QLabel#formatTitle {
            font-size: 18px;
            font-weight: bold;
        }

        QLabel#columnName {
            font-weight: bold;
        }

        QLabel#columnDescription {
            font-size: 14px;
        }

        QLabel#testFile {
            font-size: 14px;
        }

        QLabel#errorMessage {
            font-size: 14px;
            font-weight: bold;
            color: #c62828;
        }

        QPushButton {
            font-size: 15px;
            font-weight: bold;
            padding: 10px 24px;
            background-color: #ffffff;
            border: 1px solid #bdbdbd;
            border-radius: 6px;
        }

        QPushButton:hover {
            background-color: #eeeeee;
            border: 1px solid #8f8f8f;
        }

        QPushButton:pressed {
            background-color: #e0e0e0;
            border: 1px solid #7a7a7a;
        }
        """)

        self.view_model = UploadViewModel()

        self.selected_filename = None

        self.view_model.processing_failed.connect(
            self.show_processing_error
        )

        title = QLabel("CSV Extractor")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description = QLabel(
            "Upload a CSV file to validate and analyze support tickets."
        )
        description.setObjectName("description")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)

        format_title = QLabel("Expected CSV Format")
        format_title.setObjectName("formatTitle")
        format_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        columns = [
            ("ticket_id", "Exactly 4 digits"),
            ("customer", "Cannot be empty"),
            ("priority", "low, medium, or high"),
            ("status", "open, closed, or in_progress"),
            ("hours", "0–40, in increments of 0.5"),
        ]

        format_grid = QGridLayout()
        format_grid.setHorizontalSpacing(8)
        format_grid.setVerticalSpacing(8)
        format_grid.setContentsMargins(120, 0, 120, 0)

        for row, (column, validation) in enumerate(columns):
            column_label = QLabel(column)
            column_label.setObjectName("columnName")
            column_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            validation_label = QLabel(validation)
            validation_label.setObjectName("columnDescription")
            validation_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            format_grid.addWidget(column_label, row, 0)
            format_grid.addWidget(validation_label, row, 1)

        format_grid.setColumnMinimumWidth(0, 90)
        format_grid.setColumnMinimumWidth(1, 0)

        test_file = QLabel()
        test_file.setObjectName("testFile")
        test_file.setText(
            'Test File: <a href="#">test_data.csv</a>'
        )
        test_file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        test_file.linkActivated.connect(self.download_test_file)

        upload_button = QPushButton("Upload CSV File")
        upload_button.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        upload_button.clicked.connect(self.handle_upload_clicked)

        self.error_message = QLabel()
        self.error_message.setObjectName("errorMessage")
        self.error_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_message.setWordWrap(True)
        self.error_message.hide()

        card_layout = QVBoxLayout()
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(40, 32, 40, 32)

        card_layout.addWidget(title)
        card_layout.addWidget(description)
        card_layout.addSpacing(12)
        card_layout.addWidget(format_title)
        card_layout.addLayout(format_grid)
        card_layout.addWidget(test_file)
        card_layout.addSpacing(12)

        card_layout.addWidget(
            upload_button,
            0,
            Qt.AlignmentFlag.AlignHCenter
        )

        card_layout.addWidget(self.error_message)

        card = QFrame()
        card.setObjectName("contentCard")
        card.setFixedWidth(600)
        card.setLayout(card_layout)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        layout.addStretch()

        layout.addWidget(
            card,
            0,
            Qt.AlignmentFlag.AlignHCenter
        )

        layout.addStretch()

        self.setLayout(layout)

    def download_test_file(self):
        destination_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Test CSV File",
            "test_data.csv",
            "CSV Files (*.csv)",
        )

        if not destination_path:
            return

        try:
            TestFileService.download_test_file(destination_path)
        except (FileNotFoundError, OSError) as error:
            self.show_error(str(error))

    def handle_upload_clicked(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv)",
        )

        if not filename:
            return

        self.selected_filename = filename.split("/")[-1]
        self.error_message.hide()

        self.view_model.upload_file(filename)

    def show_processing_error(self, message):
        self.show_error(
            f"Unable to process '{self.selected_filename}': {message}"
        )

    def show_error(self, message):
        self.error_message.setText(message)
        self.error_message.show()