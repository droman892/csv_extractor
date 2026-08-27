from .view_models.results_view_model import ResultsViewModel
from ..services.results_export_service import ResultsExportService

from PySide6.QtCore import Signal, Qt
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
)


class ResultsView(QWidget):
    upload_another_file_requested = Signal()

    MAX_DISPLAYED_ROWS = 100

    def __init__(self, result):
        super().__init__()

        self.setStyleSheet("""
        QFrame#metricCard,
        QFrame#summaryContainer {
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
        }

        QTableWidget {
            gridline-color: #d0d0d0;
        }

        QTableWidget::item {
            padding: 4px;
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

        filename = self.view_model.get_filename()
        summary_data = self.view_model.get_summary()
        invalid_rows = self.view_model.get_invalid_rows()
        customer_rows = self.view_model.get_customer_rows()

        title = QLabel()
        title.setObjectName("resultsTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        font_metrics = QFontMetrics(title.font())
        available_width = 600

        display_filename = font_metrics.elidedText(
            f"Results for {filename}",
            Qt.TextElideMode.ElideRight,
            available_width
        )

        title.setText(display_filename)
        title.setToolTip(filename)

        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)

        summary_layout.addWidget(
            self.create_metric_card(
                "TOTAL TICKETS",
                summary_data["total_tickets_count"]
            )
        )

        summary_layout.addWidget(
            self.create_metric_card(
                "VALID TICKETS",
                summary_data["valid_tickets_count"]
            )
        )

        summary_layout.addWidget(
            self.create_metric_card(
                "INVALID TICKETS",
                summary_data["invalid_tickets_count"]
            )
        )

        summary_layout.addWidget(
            self.create_metric_card(
                "TOTAL HOURS",
                summary_data["total_hours"]
            )
        )

        summary_widget = QWidget()
        summary_widget.setLayout(summary_layout)

        tickets_by_status_widget = self.create_summary_table(
            "Tickets by Status",
            summary_data["tickets_by_status"],
            "Status",
            "Count",
            "No status data available."
        )

        tickets_by_priority_widget = self.create_summary_table(
            "Tickets by Priority",
            summary_data["tickets_by_priority"],
            "Priority",
            "Count",
            "No priority data available."
        )

        summary_tables_layout = QHBoxLayout()
        summary_tables_layout.setSpacing(12)
        summary_tables_layout.addWidget(tickets_by_status_widget)
        summary_tables_layout.addWidget(tickets_by_priority_widget)

        hours_by_customer_widget = self.create_customer_table(
            customer_rows
        )

        validation_widget = self.create_validation_widget(
            invalid_rows
        )

        export_button = QPushButton("Export Results")
        export_button.setFixedWidth(190)
        export_button.setMinimumHeight(40)
        export_button.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
        )
        export_button.clicked.connect(self.export_results)

        upload_button = QPushButton("Upload Another File")
        upload_button.setFixedWidth(190)
        upload_button.setMinimumHeight(40)
        upload_button.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor)
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
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)

        content_layout.addWidget(title)
        content_layout.addWidget(summary_widget)
        content_layout.addLayout(summary_tables_layout)
        content_layout.addWidget(hours_by_customer_widget)
        content_layout.addWidget(validation_widget)
        content_layout.addLayout(button_layout)

        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def create_metric_card(self, label, value):
        card = QFrame()
        card.setObjectName("metricCard")
        card.setMinimumHeight(120)

        layout = QVBoxLayout()

        title = QLabel(label)
        title.setObjectName("metricTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label = QLabel(f"{value:,}")
        value_label.setObjectName("metricValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        frame.setObjectName("summaryContainer")

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setObjectName("summaryTitle")

        layout.addWidget(title_label)

        if not data:
            empty_label = QLabel(empty_message)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty_label)

            frame.setLayout(layout)

            return frame

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(
            [category_header, value_header]
        )
        table.setRowCount(len(data))
        table.setMinimumHeight(120)

        for row_number, (category, count) in enumerate(data.items()):
            display_category = category.replace(
                "_",
                " "
            ).title()

            category_item = QTableWidgetItem(display_category)
            category_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            count_item = QTableWidgetItem(f"{count:,}")
            count_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            table.setItem(row_number, 0, category_item)
            table.setItem(row_number, 1, count_item)

        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)

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

        table.verticalHeader().setDefaultSectionSize(30)

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(40)

        layout.addWidget(table)

        frame.setLayout(layout)

        return frame

    def create_customer_table(self, customer_rows):
        frame = QFrame()
        frame.setObjectName("summaryContainer")

        layout = QVBoxLayout()

        title_layout = QHBoxLayout()

        title = QLabel("Hours by Customer")
        title.setObjectName("summaryTitle")

        total_customers = len(customer_rows)
        displayed_customers = min(
            total_customers,
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
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty_label)

            frame.setLayout(layout)

            return frame

        displayed_rows = customer_rows[
            :self.MAX_DISPLAYED_ROWS
        ]

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(
            ["Customer", "Hours"]
        )
        table.setRowCount(len(displayed_rows))
        table.setMinimumHeight(120)

        for row_number, (customer, hours) in enumerate(
            displayed_rows
        ):
            customer_item = QTableWidgetItem(customer)
            customer_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            hours_item = QTableWidgetItem(f"{hours:g}")
            hours_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            table.setItem(row_number, 0, customer_item)
            table.setItem(row_number, 1, hours_item)

        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)

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

        table.verticalHeader().setDefaultSectionSize(30)

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(40)

        layout.addWidget(table)

        frame.setLayout(layout)

        return frame

    def create_validation_widget(self, invalid_rows):
        frame = QFrame()
        frame.setObjectName("summaryContainer")

        layout = QVBoxLayout()

        title_layout = QHBoxLayout()

        title = QLabel("Validation Issues")
        title.setObjectName("summaryTitle")

        total_errors = len(invalid_rows)
        displayed_errors = min(
            total_errors,
            self.MAX_DISPLAYED_ROWS
        )

        count_label = QLabel(
            f"— Showing {displayed_errors:,} "
            f"errors out of {total_errors:,}"
        )

        title_layout.addWidget(title)
        title_layout.addWidget(count_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        if not invalid_rows:
            message = QLabel(
                "All records passed validation."
            )
            message.setAlignment(Qt.AlignmentFlag.AlignCenter)

            layout.addWidget(message)

            frame.setLayout(layout)

            return frame

        displayed_rows = invalid_rows[
            :self.MAX_DISPLAYED_ROWS
        ]

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(
            [
                "Ticket",
                "Field",
                "Invalid Value",
                "Validation Error"
            ]
        )
        table.setRowCount(len(displayed_rows))
        table.setMinimumHeight(120)

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

        for row in range(table.rowCount()):
            for column in range(table.columnCount()):
                table.item(
                    row,
                    column
                ).setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
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

        table.verticalHeader().setDefaultSectionSize(30)

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(40)

        layout.addWidget(table)

        frame.setLayout(layout)

        return frame

    def export_results(self):
        filename = self.view_model.get_filename()

        destination_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            f"{filename.rsplit('.', 1)[0]}_results.csv",
            "CSV Files (*.csv)",
        )

        if not destination_path:
            return

        ResultsExportService.export_results(
            self.view_model.get_export_data(),
            destination_path
        )