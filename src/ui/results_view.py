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
)

class ResultsView(QWidget):
    upload_another_file_requested = Signal()

    def __init__(self, result):
        super().__init__()
        self.view_model = ResultsViewModel(result)

        filename = self.view_model.get_filename()
        summary_data = self.view_model.get_summary()
        invalid_rows = self.view_model.get_invalid_rows()

        title = QLabel(f"Results for {filename}")

        summary = QLabel(
            f"Total Tickets: {summary_data['total_tickets_count']}\n"
            f"Valid Tickets: {summary_data['valid_tickets_count']}\n"
            f"Invalid Tickets: {summary_data['invalid_tickets_count']}\n"
            f"Total Hours: {summary_data['total_hours']}"
        )

        status_text = "Tickets by Status\n"

        for status, count in summary_data["tickets_by_status"].items():
            status_text += f"{status}: {count}\n"

        status = QLabel(status_text)

        priority_text = "Tickets by Priority\n"

        for priority, count in summary_data["tickets_by_priority"].items():
            priority_text += f"{priority}: {count}\n"

        priority = QLabel(priority_text)

        customer_text = "Hours by Customer\n"

        for customer, hours in summary_data["hours_by_customer"].items():
            customer_text += f"{customer}: {hours}\n"

        customer = QLabel(customer_text)

        if not invalid_rows:
            invalid_records = QLabel(
                "Invalid Records\n"
                "0 invalid records"
            )
        else:
            invalid_records = QTableWidget()

            invalid_records.setColumnCount(4)
            invalid_records.setHorizontalHeaderLabels(
                ["Ticket", "Field", "Invalid Value", "Reason"]
            )

            invalid_records.setRowCount(len(invalid_rows))

            for row_number, row_data in enumerate(invalid_rows):
                invalid_records.setItem(
                    row_number,
                    0,
                    QTableWidgetItem(row_data["ticket_id"])
                )
                invalid_records.setItem(
                    row_number,
                    1,
                    QTableWidgetItem(row_data["field"])
                )
                invalid_records.setItem(
                    row_number,
                    2,
                    QTableWidgetItem(str(row_data["invalid_value"]))
                )
                invalid_records.setItem(
                    row_number,
                    3,
                    QTableWidgetItem(row_data["reason"])
                )

            for row in range(invalid_records.rowCount()):
                for column in range(invalid_records.columnCount()):
                    invalid_records.item(row, column).setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

            invalid_records.setEditTriggers(
                QTableWidget.NoEditTriggers
            )

            invalid_records.resizeColumnsToContents()
            invalid_records.horizontalHeader().setStretchLastSection(True)

        upload_button = QPushButton("Upload Another File")
        upload_button.clicked.connect(
            self.upload_another_file_requested.emit
        )

        content_layout = QVBoxLayout()
        content_layout.addWidget(title)
        content_layout.addWidget(summary)
        content_layout.addWidget(status)
        content_layout.addWidget(priority)
        content_layout.addWidget(customer)
        content_layout.addWidget(invalid_records)
        content_layout.addWidget(upload_button)

        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)