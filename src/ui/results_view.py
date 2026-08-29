from pathlib import Path

from .view_models.results_view_model import ResultsViewModel
from ..services.results_export_service import ResultsExportService

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
)

class ResultsView(QWidget):
    upload_another_file_requested = Signal()

    MAX_DISPLAYED_ROWS = 100

    def __init__(self, result, full_result):
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

        self.view_model = ResultsViewModel(result)
        self.full_result = full_result

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

        export_button = QPushButton(
            "Export Results"
        )

        export_button.setFixedWidth(190)
        export_button.setMinimumHeight(40)
        export_button.setCursor(
            QCursor(
                Qt.CursorShape.PointingHandCursor
            )
        )

        export_button.clicked.connect(
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
        button_layout.addWidget(export_button)
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

        table.setMinimumHeight(120)

        table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )

        table.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
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

        table.setEditTriggers(
            QTableWidget.NoEditTriggers
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

        table.verticalHeader().setDefaultSectionSize(
            30
        )

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(
            40
        )

        layout.addWidget(table)

        frame.setLayout(layout)

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

            layout.addWidget(
                empty_label
            )

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

        table.setMinimumHeight(120)

        table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )

        table.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
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

        table.setEditTriggers(
            QTableWidget.NoEditTriggers
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

        table.verticalHeader().setDefaultSectionSize(
            30
        )

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(
            40
        )

        layout.addWidget(table)

        frame.setLayout(layout)

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

        table.setMinimumHeight(120)

        table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )

        table.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

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

        table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        table.setWordWrap(True)

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

        table.verticalHeader().setDefaultSectionSize(
            30
        )

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(
            40
        )

        layout.addWidget(table)

        frame.setLayout(layout)

        return frame

    def export_results(self):
        filename = self.view_model.get_filename()

        destination_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            f"{Path(filename).stem}_results.xlsx",
            "Excel Files (*.xlsx)",
        )

        if not destination_path:
            return

        try:
            ResultsExportService.export_results(
                self.full_result,
                destination_path
            )

        except Exception as error:
            self.show_export_error(
                str(error)
            )

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