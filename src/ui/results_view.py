from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class ResultsView(QWidget):
    upload_another_file_requested = Signal()

    def __init__(self, result):
        super().__init__()

        summary_data = result["summary"]

        title = QLabel("Results")

        summary = QLabel(
            f"Total Tickets: {result['total_tickets_count']}\n"
            f"Valid Tickets: {result['valid_tickets_count']}\n"
            f"Invalid Tickets: {result['invalid_tickets_count']}\n"
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

        invalid_text = "Invalid Records\n"

        if not result["invalid_records"]:
            invalid_text += "0 invalid records"
        else:
            for record in result["invalid_records"]:
                invalid_text += f"\nTicket: {record['ticket_id']}\n"

                for error in record["errors"]:
                    invalid_text += (
                        f"Field: {error['field']}\n"
                        f"Value: {error['invalid_value']}\n"
                        f"Reason: {error['reason']}\n"
                    )

        invalid_records = QLabel(invalid_text)
        invalid_records.setWordWrap(True)

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