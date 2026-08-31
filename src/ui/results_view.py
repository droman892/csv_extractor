from pathlib import Path

from .view_models.results_view_model import ResultsViewModel

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFontMetrics, QCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QSizePolicy,
    QMessageBox,
    QApplication,
)


class ResultsView(QWidget):
    upload_another_file_requested = Signal()

    MAX_DISPLAYED_ROWS = 100

    def __init__(
        self,
        display_result,
        full_result_path
    ):
        super().__init__()

        self.setStyleSheet("""
        QFrame#metricCard,
        QFrame#summaryContainer,
        QFrame#resultsTitleContainer {
            border: 1px solid #d0d0d0;
            border-radius: 8px;
            background-color: #f7f7f7;
        }

        QLabel#metricTitle {
            font-size: 16px;
            font-weight: bold;
        }

        QLabel#metricValue {
            font-size: 28px;
            font-weight: bold;
        }

        QLabel#resultsTitle {
            font-size: 24px;
            font-weight: bold;
        }

        QLabel#summaryTitle {
            font-size: 16px;
            font-weight: bold;
        }

        QHeaderView::section {
            font-weight: bold;
            background-color: #eeeeee;
            border: none;
            border-bottom: 1px solid #d0d0d0;
            border-right: 1px solid #d8d8d8;
            padding: 5px;
        }

        QHeaderView::section:last {
            border-right: none;
        }

        QHeaderView::section:hover {
            background-color: #eeeeee;
        }

        QTableWidget {
            gridline-color: #dddddd;
            border: 1px solid #d8d8d8;
            border-radius: 4px;
            alternate-background-color: #f8f8f8;
            background-color: #ffffff;
        }

        QTableWidget::item {
            padding: 4px;
            border: none;
        }

        QTableWidget::item:hover {
            background-color: transparent;
        }

        QTableWidget::item:selected {
            background-color: transparent;
            color: black;
        }

        QHeaderView {
            background-color: #eeeeee;
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

        self.view_model = ResultsViewModel(
            display_result,
            full_result_path
        )

        self.view_model.export_started.connect(
            self.export_started
        )

        self.view_model.export_completed.connect(
            self.export_completed
        )

        self.view_model.export_failed.connect(
            self.export_failed
        )

        filename = self.view_model.get_filename()
        summary_data = self.view_model.get_summary()
        invalid_rows = self.view_model.get_invalid_rows()
        customer_rows = self.view_model.get_customer_rows()

        total_customers = (
            self.view_model.get_total_customer_count()
        )

        total_invalid_errors = (
            self.view_model.get_total_invalid_error_count()
        )

        self.filename = filename

        self.results_title = QLabel()
        self.results_title.setObjectName(
            "resultsTitle"
        )
        self.results_title.setAlignment(
            Qt.AlignmentFlag.AlignLeft
        )
        self.results_title.setWordWrap(False)
        self.results_title.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        self.results_title.setToolTip(filename)

        title_container = QFrame()
        title_container.setObjectName(
            "resultsTitleContainer"
        )

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(
            16, 12, 16, 12
        )

        title_layout.addWidget(
            self.results_title
        )

        results_note = QLabel(
            "Note: Only data from valid records is included in Tickets by Status, Tickets by Priority, and Hours by Customer."
        )

        results_note.setWordWrap(True)

        title_layout.addWidget(
            results_note
        )

        title_container.setLayout(
            title_layout
        )

        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)
        summary_layout.setContentsMargins(
            0, 0, 0, 0
        )

        metric_cards = [
            self.create_metric_card(
                "TOTAL TICKETS",
                summary_data["total_tickets_count"]
            ),
            self.create_metric_card(
                "VALID TICKETS",
                summary_data["valid_tickets_count"]
            ),
            self.create_metric_card(
                "INVALID TICKETS",
                summary_data["invalid_tickets_count"]
            ),
            self.create_metric_card(
                "TOTAL HOURS",
                summary_data["total_hours"]
            )
        ]

        for card in metric_cards:
            summary_layout.addWidget(card)

        summary_widget = QWidget()
        summary_widget.setLayout(
            summary_layout
        )

        tickets_by_status_widget = (
            self.create_summary_table(
                "Tickets by Status",
                summary_data["tickets_by_status"],
                "Status",
                "Count",
                "No status data available."
            )
        )

        tickets_by_priority_widget = (
            self.create_summary_table(
                "Tickets by Priority",
                summary_data["tickets_by_priority"],
                "Priority",
                "Count",
                "No priority data available."
            )
        )

        summary_tables_layout = QHBoxLayout()
        summary_tables_layout.setSpacing(12)
        summary_tables_layout.setContentsMargins(
            0, 0, 0, 0
        )

        summary_tables_layout.addWidget(
            tickets_by_status_widget
        )

        summary_tables_layout.addWidget(
            tickets_by_priority_widget
        )

        hours_by_customer_widget = (
            self.create_customer_table(
                customer_rows,
                total_customers
            )
        )

        validation_widget = (
            self.create_validation_widget(
                invalid_rows,
                total_invalid_errors
            )
        )

        self.export_button = QPushButton(
            "Export Results"
        )

        self.export_button.setFixedWidth(190)
        self.export_button.setMinimumHeight(40)
        self.export_button.setCursor(
            QCursor(
                Qt.CursorShape.PointingHandCursor
            )
        )

        self.export_button.clicked.connect(
            self.export_results
        )

        upload_button = QPushButton(
            "Upload Another File"
        )

        upload_button.setFixedWidth(190)
        upload_button.setMinimumHeight(40)
        upload_button.setCursor(
            QCursor(
                Qt.CursorShape.PointingHandCursor
            )
        )

        upload_button.clicked.connect(
            self.upload_another_file_requested.emit
        )

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        button_layout.addWidget(upload_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(
            24, 24, 24, 24
        )
        content_layout.setSpacing(20)

        content_layout.addWidget(
            title_container
        )

        content_layout.addWidget(
            summary_widget
        )

        content_layout.addLayout(
            summary_tables_layout
        )

        content_layout.addWidget(
            hours_by_customer_widget
        )

        content_layout.addWidget(
            validation_widget
        )

        content_layout.addLayout(
            button_layout
        )

        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred
        )
        self.content_widget.setLayout(
            content_layout
        )

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(
            self.content_widget
        )
        self.scroll_area.setWidgetResizable(
            True
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(
            8, 8, 8, 8
        )
        main_layout.addWidget(
            self.scroll_area
        )

        self.setLayout(main_layout)

        QTimer.singleShot(
            0,
            self.finalize_table_heights
        )

        QTimer.singleShot(
            0,
            self.update_filename_display
        )

    def create_metric_card(self, label, value):
        card = QFrame()
        card.setObjectName("metricCard")
        card.setMinimumHeight(120)

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout()

        title = QLabel(label)
        title.setObjectName("metricTitle")
        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        value_label = QLabel(
            f"{value:,.1f}"
            if isinstance(value, float)
            else f"{value:,}"
        )

        value_label.setObjectName(
            "metricValue"
        )

        value_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(title)
        layout.addWidget(value_label)

        card.setLayout(layout)

        return card

    def create_summary_table(
        self,
        title,
        data,
        category_header,
        value_header,
        empty_message
    ):
        frame = QFrame()
        frame.setObjectName(
            "summaryContainer"
        )

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setObjectName(
            "summaryTitle"
        )

        layout.addWidget(title_label)

        if not data:
            empty_label = QLabel(
                empty_message
            )

            empty_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            layout.addWidget(
                empty_label
            )

            frame.setLayout(layout)

            return frame

        table = QTableWidget()
        table.setColumnCount(2)

        table.setHorizontalHeaderLabels([
            category_header,
            value_header
        ])

        table.setRowCount(
            len(data)
        )

        table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )

        table.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        for row_number, (
            category,
            count
        ) in enumerate(data.items()):

            display_category = (
                category.replace(
                    "_",
                    " "
                ).title()
            )

            category_item = QTableWidgetItem(
                display_category
            )

            category_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            count_item = QTableWidgetItem(
                f"{count:,}"
            )

            count_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            table.setItem(
                row_number,
                0,
                category_item
            )

            table.setItem(
                row_number,
                1,
                count_item
            )

        header = table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )

        table.verticalHeader().setSectionResizeMode(
            QHeaderView.Fixed
        )

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(
            40
        )

        layout.addWidget(table)

        frame.setLayout(layout)

        if title == "Tickets by Status":
            self.status_table = table

        elif title == "Tickets by Priority":
            self.priority_table = table

        return frame

    def create_customer_table(
        self,
        customer_rows,
        total_customers
    ):
        frame = QFrame()
        frame.setObjectName(
            "summaryContainer"
        )

        layout = QVBoxLayout()

        title_layout = QHBoxLayout()

        title = QLabel(
            "Hours by Customer"
        )

        title.setObjectName(
            "summaryTitle"
        )

        displayed_customers = min(
            len(customer_rows),
            self.MAX_DISPLAYED_ROWS
        )

        count_label = QLabel(
            f"— Showing {displayed_customers:,} "
            f"customers out of {total_customers:,}"
        )

        title_layout.addWidget(title)
        title_layout.addWidget(count_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        if not customer_rows:
            empty_label = QLabel(
                "No customer workload data available."
            )

            empty_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            layout.addWidget(empty_label)

            frame.setLayout(layout)

            return frame

        displayed_rows = customer_rows[
            :self.MAX_DISPLAYED_ROWS
        ]

        table = QTableWidget()
        table.setColumnCount(2)

        table.setHorizontalHeaderLabels([
            "Customer",
            "Hours"
        ])

        table.setRowCount(
            len(displayed_rows)
        )

        table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )

        table.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        for row_number, (
            customer,
            hours
        ) in enumerate(displayed_rows):

            customer_item = QTableWidgetItem(
                customer
            )

            customer_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            hours_item = QTableWidgetItem(
                f"{hours:,.1f}"
            )

            hours_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            table.setItem(
                row_number,
                0,
                customer_item
            )

            table.setItem(
                row_number,
                1,
                hours_item
            )

        header = table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )

        table.verticalHeader().setSectionResizeMode(
            QHeaderView.Fixed
        )

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(
            40
        )

        table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout.addWidget(table)

        frame.setLayout(layout)

        self.customer_table = table

        return frame

    def create_validation_widget(
        self,
        invalid_rows,
        total_invalid_errors
    ):
        frame = QFrame()
        frame.setObjectName(
            "summaryContainer"
        )

        layout = QVBoxLayout()

        title_layout = QHBoxLayout()

        title = QLabel(
            "Validation Issues"
        )

        title.setObjectName(
            "summaryTitle"
        )

        displayed_errors = min(
            len(invalid_rows),
            self.MAX_DISPLAYED_ROWS
        )

        count_label = QLabel(
            f"— Showing {displayed_errors:,} "
            f"errors out of {total_invalid_errors:,}"
        )

        title_layout.addWidget(title)
        title_layout.addWidget(count_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        if not invalid_rows:
            message = QLabel(
                "All records passed validation."
            )

            message.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            layout.addWidget(message)

            frame.setLayout(layout)

            return frame

        displayed_rows = invalid_rows[
            :self.MAX_DISPLAYED_ROWS
        ]

        table = QTableWidget()
        table.setColumnCount(4)

        table.setHorizontalHeaderLabels([
            "Ticket",
            "Field",
            "Invalid Value",
            "Validation Error"
        ])

        table.setRowCount(
            len(displayed_rows)
        )

        table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )

        table.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        table.setWordWrap(True)

        for row_number, row_data in enumerate(
            displayed_rows
        ):
            table.setItem(
                row_number,
                0,
                QTableWidgetItem(
                    str(row_data["ticket_id"])
                )
            )

            table.setItem(
                row_number,
                1,
                QTableWidgetItem(
                    row_data["field"]
                )
            )

            table.setItem(
                row_number,
                2,
                QTableWidgetItem(
                    str(row_data["invalid_value"])
                )
            )

            table.setItem(
                row_number,
                3,
                QTableWidgetItem(
                    row_data["reason"]
                )
            )

        for row in range(
            table.rowCount()
        ):
            for column in range(
                table.columnCount()
            ):
                table.item(
                    row,
                    column
                ).setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

        header = table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.Stretch
        )

        table.verticalHeader().setSectionResizeMode(
            QHeaderView.Fixed
        )

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(
            40
        )

        table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout.addWidget(table)

        frame.setLayout(layout)

        self.validation_table = table

        return frame

    def finalize_table_heights(self):
        tables = []

        if hasattr(self, "status_table"):
            tables.append(self.status_table)

        if hasattr(self, "priority_table"):
            tables.append(self.priority_table)

        if hasattr(self, "customer_table"):
            tables.append(self.customer_table)

        if hasattr(self, "validation_table"):
            tables.append(self.validation_table)

        if not tables:
            return

        QApplication.processEvents()

        reference_table = None

        if hasattr(self, "status_table"):
            reference_table = self.status_table
        elif hasattr(self, "priority_table"):
            reference_table = self.priority_table

        if reference_table is None:
            return

        reference_table.doItemsLayout()

        if reference_table.rowCount() == 0:
            return

        finalized_row_height = (
            reference_table.rowHeight(0)
        )

        if finalized_row_height <= 0:
            return

        for table in tables:
            table.verticalHeader().setDefaultSectionSize(
                finalized_row_height
            )

            for row in range(
                table.rowCount()
            ):
                table.setRowHeight(
                    row,
                    finalized_row_height
                )

        for table in tables:
            header_height = (
                table.horizontalHeader().height()
            )

            frame_height = (
                2 * table.frameWidth()
            )

            required_height = (
                header_height
                + (
                    finalized_row_height
                    * table.rowCount()
                )
                + frame_height
            )

            table.setFixedHeight(
                required_height
            )

    def export_results(self):
        filename = self.view_model.get_filename()

        destination_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            f"{Path(filename).stem}_results.csv",
            "CSV Files (*.csv)",
        )

        if not destination_path:
            return

        self.view_model.export_results(
            destination_path
        )

    def export_started(self):
        self.export_button.setEnabled(False)

    def export_completed(self, destination_path):
        self.export_button.setEnabled(True)

        message_box = QMessageBox(self)

        message_box.setWindowTitle(
            "Export Complete"
        )

        message_box.setIcon(
            QMessageBox.Icon.Information
        )

        message_box.setText(
            "The results were exported successfully."
        )

        message_box.setStandardButtons(
            QMessageBox.StandardButton.Ok
        )

        ok_button = message_box.button(
            QMessageBox.StandardButton.Ok
        )

        if ok_button is not None:
            ok_button.setCursor(
                QCursor(
                    Qt.CursorShape.PointingHandCursor
                )
            )

        message_box.exec()

    def export_failed(self, message):
        self.export_button.setEnabled(True)

        message_box = QMessageBox(self)

        message_box.setWindowTitle(
            "Export Failed"
        )

        message_box.setIcon(
            QMessageBox.Icon.Critical
        )

        message_box.setText(
            "The results could not be exported."
        )

        message_box.setInformativeText(
            message
        )

        message_box.setStandardButtons(
            QMessageBox.StandardButton.Ok
        )

        ok_button = message_box.button(
            QMessageBox.StandardButton.Ok
        )

        if ok_button is not None:
            ok_button.setCursor(
                QCursor(
                    Qt.CursorShape.PointingHandCursor
                )
            )

        message_box.exec()

    def update_filename_display(self):
        if not hasattr(
            self,
            "results_title"
        ):
            return

        available_width = (
            self.results_title.width()
        )

        if available_width <= 0:
            return

        font_metrics = QFontMetrics(
            self.results_title.font()
        )

        display_filename = (
            font_metrics.elidedText(
                f"Results for {self.filename}",
                Qt.TextElideMode.ElideMiddle,
                available_width
            )
        )

        self.results_title.setText(
            display_filename
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(
            self,
            "scroll_area"
        ):
            viewport_width = (
                self.scroll_area.viewport().width()
            )

            self.content_widget.setMinimumWidth(
                viewport_width
            )

            QTimer.singleShot(
                0,
                self.update_filename_display
            )