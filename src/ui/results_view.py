from .view_models.results_view_model import ResultsViewModel
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
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

    def __init__(self, result):
        super().__init__()

        self.setStyleSheet("""
        QFrame {
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

        QLabel#sectionTitle {
            font-size: 18px;
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
        """)

        self.view_model = ResultsViewModel(result)

        filename = self.view_model.get_filename()
        summary_data = self.view_model.get_summary()
        invalid_rows = self.view_model.get_invalid_rows()

        title = QLabel(f"Results for {filename}")
        title.setObjectName("resultsTitle")

        summary_layout = QHBoxLayout()

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
            "Count"
        )

        tickets_by_priority_widget = self.create_summary_table(
            "Tickets by Priority",
            summary_data["tickets_by_priority"],
            "Count"
        )

        ticket_summary_title = QLabel("Ticket Summary")
        ticket_summary_title.setObjectName("sectionTitle")

        summary_tables_layout = QHBoxLayout()
        summary_tables_layout.addWidget(tickets_by_status_widget)
        summary_tables_layout.addWidget(tickets_by_priority_widget)

        ticket_summary_widget = QWidget()

        ticket_summary_layout = QVBoxLayout()
        ticket_summary_layout.addWidget(ticket_summary_title)
        ticket_summary_layout.addLayout(summary_tables_layout)

        ticket_summary_widget.setLayout(ticket_summary_layout)

        hours_by_customer_widget = self.create_summary_table(
            "Hours by Customer",
            summary_data["hours_by_customer"],
            "Hours"
        )

        customer_workload_title = QLabel("Customer Workload")
        customer_workload_title.setObjectName("sectionTitle")

        customer_workload_widget = QWidget()

        customer_workload_layout = QVBoxLayout()
        customer_workload_layout.addWidget(customer_workload_title)
        customer_workload_layout.addWidget(hours_by_customer_widget)

        customer_workload_widget.setLayout(customer_workload_layout)

        validation_title = QLabel("Validation Issues")
        validation_title.setObjectName("sectionTitle")

        if not invalid_rows:
            invalid_records = QFrame()

            invalid_layout = QVBoxLayout()

            invalid_title = QLabel("Invalid Records")
            invalid_title.setObjectName("summaryTitle")

            invalid_message = QLabel(
                "0 invalid records\n"
                "All records passed validation."
            )
            invalid_message.setAlignment(Qt.AlignmentFlag.AlignCenter)

            invalid_layout.addWidget(invalid_title)
            invalid_layout.addWidget(invalid_message)

            invalid_records.setLayout(invalid_layout)
        else:
            invalid_records = self.create_invalid_records_table(
                invalid_rows
            )

        validation_widget = QWidget()

        validation_layout = QVBoxLayout()
        validation_layout.addWidget(validation_title)
        validation_layout.addWidget(invalid_records)

        validation_widget.setLayout(validation_layout)

        upload_button = QPushButton("Upload Another File")
        upload_button.setMinimumHeight(40)
        upload_button.clicked.connect(
            self.upload_another_file_requested.emit
        )

        content_layout = QVBoxLayout()
        content_layout.addWidget(title)
        content_layout.addWidget(summary_widget)
        content_layout.addWidget(ticket_summary_widget)
        content_layout.addWidget(customer_workload_widget)
        content_layout.addWidget(validation_widget)
        content_layout.addWidget(upload_button)

        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def create_metric_card(self, label, value):
        card = QFrame()
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

    def create_summary_table(self, title, data, value_header):
        frame = QFrame()

        layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setObjectName("summaryTitle")

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(
            ["Category", value_header]
        )
        table.setRowCount(len(data))
        table.setMinimumHeight(120)

        for row_number, (category, count) in enumerate(data.items()):
            display_category = category.replace("_", " ").title()

            category_item = QTableWidgetItem(display_category)
            category_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            count_item = QTableWidgetItem(f"{count:,}")
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

        table.setEditTriggers(QTableWidget.NoEditTriggers)

        header = table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )

        table.verticalHeader().setDefaultSectionSize(30)
        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        table.verticalHeader().setMinimumWidth(40)
        table.setSelectionMode(QTableWidget.NoSelection)

        table.verticalHeader().setSectionResizeMode(
            QHeaderView.Fixed
        )
        table.verticalHeader().setDefaultSectionSize(30)

        layout.addWidget(title_label)
        layout.addWidget(table)

        frame.setLayout(layout)

        return frame

    def create_invalid_records_table(self, invalid_rows):
        frame = QFrame()

        layout = QVBoxLayout()

        title = QLabel("Invalid Records")
        title.setObjectName("summaryTitle")

        table = QTableWidget()
        table.setMinimumHeight(120)

        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(
            ["Ticket", "Field", "Invalid Value", "Reason"]
        )

        table.setRowCount(len(invalid_rows))

        for row_number, row_data in enumerate(invalid_rows):
            table.setItem(
                row_number,
                0,
                QTableWidgetItem(row_data["ticket_id"])
            )

            table.setItem(
                row_number,
                1,
                QTableWidgetItem(row_data["field"])
            )

            table.setItem(
                row_number,
                2,
                QTableWidgetItem(str(row_data["invalid_value"]))
            )

            table.setItem(
                row_number,
                3,
                QTableWidgetItem(row_data["reason"])
            )

        for row in range(table.rowCount()):
            for column in range(table.columnCount()):
                table.item(row, column).setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                table.setEditTriggers(QTableWidget.NoEditTriggers)

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

        table.setWordWrap(True)
        table.resizeRowsToContents()

        table.verticalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        table.verticalHeader().setMinimumWidth(40)
        table.setSelectionMode(QTableWidget.NoSelection)

        table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        layout.addWidget(title)
        layout.addWidget(table)

        frame.setLayout(layout)

        return frame