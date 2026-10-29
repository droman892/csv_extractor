try:
    import winsound
except ImportError:
    # Not Windows, so the error sound is skipped.
    winsound = None  # type: ignore[assignment]

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFontMetrics
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QFrame,
    QApplication,
    QScrollArea
)

from ..processing.rules import FORMAT_NOTE, format_hints
from ..services.demo_data_file_service import DemoDataFileService
from .view_models.upload_view_model import UploadViewModel


class UploadView(QWidget):
    processing_started = Signal()

    def __init__(self) -> None:
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

        QLabel#formatNote {
            font-size: 13px;
            color: #555555;
        }

        QLabel#demoDataFile {
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

        self.selected_filename: str | None = None

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

        # Built from the same rules validation uses, so these hints
        # cannot drift out of date again.
        columns = format_hints()

        format_grid = QGridLayout()
        format_grid.setHorizontalSpacing(8)
        format_grid.setVerticalSpacing(8)
        format_grid.setContentsMargins(120, 0, 120, 0)
        format_grid.setColumnMinimumWidth(0, 90)

        for row, (column, validation) in enumerate(columns):
            column_label = QLabel(column)
            column_label.setObjectName("columnName")
            column_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            validation_label = QLabel(validation)
            validation_label.setObjectName("columnDescription")
            validation_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            format_grid.addWidget(column_label, row, 0)
            format_grid.addWidget(validation_label, row, 1)

        format_note = QLabel(FORMAT_NOTE)
        format_note.setObjectName("formatNote")
        format_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        format_note.setWordWrap(True)

        demo_data_file = QLabel()
        demo_data_file.setObjectName("demoDataFile")
        demo_data_file.setText(
            'Demo Data File: <a href="#">demo_data_file.csv</a>'
        )
        demo_data_file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        demo_data_file.linkActivated.connect(self.download_demo_data_file)

        self.upload_button = QPushButton("Upload CSV File")
        self.upload_button.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        self.upload_button.clicked.connect(
            self.handle_upload_clicked
        )

        self.error_message = QLabel()
        self.error_message.setObjectName("errorMessage")
        self.error_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_message.setWordWrap(True)
        self.error_message.hide()

        self.card_layout = QVBoxLayout()
        self.card_layout.setSpacing(16)
        self.card_layout.setContentsMargins(40, 32, 40, 32)

        self.card_layout.addWidget(title)
        self.card_layout.addWidget(description)
        self.card_layout.addSpacing(12)
        self.card_layout.addWidget(format_title)
        self.card_layout.addLayout(format_grid)
        self.card_layout.addWidget(format_note)
        self.card_layout.addWidget(demo_data_file)
        self.card_layout.addSpacing(12)

        self.card_layout.addWidget(
            self.upload_button,
            0,
            Qt.AlignmentFlag.AlignHCenter
        )

        self.card_layout.addWidget(self.error_message)

        self.card = QFrame()
        self.card.setObjectName("contentCard")
        self.card.setFixedWidth(600)
        self.card.setLayout(self.card_layout)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(40, 24, 40, 24)

        content_layout.addStretch()

        content_layout.addWidget(
            self.card,
            0,
            Qt.AlignmentFlag.AlignHCenter
        )

        content_layout.addStretch()

        content = QWidget()
        content.setLayout(content_layout)

        # The window's minimum height does not grow when the error message
        # appears. Without the scroll area, Qt would squeeze the card to fit
        # and cut off the format rows. With it, the card keeps its full
        # height (see fit_card_to_contents) and the screen scrolls only if
        # the window is too short.
        scroll_area = QScrollArea()
        scroll_area.setObjectName("uploadScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(content)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

    def download_demo_data_file(self) -> None:
        destination_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Demo CSV File",
            "demo_data_file.csv",
            "CSV Files (*.csv)",
        )

        if not destination_path:
            return

        # Called directly, not through a view model, because the copy is
        # instant and has no state or lifecycle to manage.
        try:
            DemoDataFileService.download_demo_data_file(destination_path)
        except (FileNotFoundError, OSError) as error:
            self.show_error(str(error))

    def handle_upload_clicked(self) -> None:
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
        self.fit_card_to_contents()

        self.upload_button.setEnabled(False)
        self.processing_started.emit()

        self.view_model.upload_file(filename)

    def show_processing_error(self, message: str) -> None:
        self.upload_button.setEnabled(True)

        # A label that has never been shown has never been laid out, so its
        # width() is Qt's default (640) instead of its real width. Showing it
        # and applying the layout first gives the real width every time.
        self.error_message.show()
        self.card_layout.activate()

        available_width = self.error_message.width()

        font_metrics = QFontMetrics(
            self.error_message.font()
        )

        prefix = "Unable to process '"
        suffix = "': "

        remaining_width = (
            available_width
            - font_metrics.horizontalAdvance(prefix)
            - font_metrics.horizontalAdvance(suffix)
        )

        elided_filename = font_metrics.elidedText(
            self.selected_filename or "",
            Qt.TextElideMode.ElideMiddle,
            max(remaining_width, 100),
        )

        self.show_error(
            f"{prefix}{elided_filename}{suffix}{message}"
        )

        # Paints the hidden spinner and the new error message before the
        # beep, so the sound plays when the error appears and not before.
        QApplication.processEvents()

        if winsound is not None:
            winsound.MessageBeep(
                winsound.MB_ICONEXCLAMATION
            )

    def show_error(self, message: str) -> None:
        self.error_message.setText(message)
        self.error_message.show()
        self.fit_card_to_contents()

    def fit_card_to_contents(self) -> None:
        # Qt asks the centered card how tall it must be at the full width
        # of the window instead of at its own fixed width, so it
        # underestimates the height its word-wrapped labels need and
        # squeezes the format rows. The card's width is fixed, so the real
        # height is known and can be set as its minimum.
        self.card.setMinimumHeight(
            self.card.heightForWidth(self.card.width())
        )