from PySide6.QtCore import QObject, Signal, QThread

from ..workers.export_worker import ExportWorker


class ResultsViewModel(QObject):
    export_started = Signal()
    export_completed = Signal(str)
    export_failed = Signal(str)

    def __init__(self, result, full_result):
        super().__init__()

        self.result = result
        self.full_result = full_result

        self.export_thread = None
        self.export_worker = None

    def get_filename(self):
        import os

        return os.path.basename(
            self.result["filename"]
        )

    def get_summary(self):
        return {
            "total_tickets_count":
                self.result["total_tickets_count"],

            "valid_tickets_count":
                self.result["valid_tickets_count"],

            "invalid_tickets_count":
                self.result["invalid_tickets_count"],

            "total_hours":
                self.result["summary"]["total_hours"],

            "tickets_by_status":
                self.result["summary"]["tickets_by_status"],

            "tickets_by_priority":
                self.result["summary"]["tickets_by_priority"],

            "hours_by_customer":
                self.result["summary"]["hours_by_customer"]
        }

    def get_invalid_rows(self):
        return self.result["invalid_records"]

    def get_customer_rows(self):
        return list(
            self.result["summary"][
                "hours_by_customer"
            ].items()
        )

    def get_total_customer_count(self):
        return self.result[
            "total_customer_count"
        ]

    def get_total_invalid_record_count(self):
        return self.result[
            "total_invalid_record_count"
        ]

    def get_total_invalid_error_count(self):
        return self.result[
            "total_invalid_error_count"
        ]

    def export_results(self, destination_path):
        self.export_started.emit()

        self.export_thread = QThread()
        self.export_worker = ExportWorker(
            self.full_result,
            destination_path
        )

        self.export_worker.moveToThread(
            self.export_thread
        )

        self.export_thread.started.connect(
            self.export_worker.export_file
        )

        self.export_worker.completed.connect(
            self.export_completed
        )

        self.export_worker.failed.connect(
            self.export_failed
        )

        self.export_worker.completed.connect(
            self.export_thread.quit
        )

        self.export_worker.failed.connect(
            self.export_thread.quit
        )

        self.export_thread.finished.connect(
            self.export_worker.deleteLater
        )

        self.export_thread.finished.connect(
            self.export_thread.deleteLater
        )

        self.export_thread.finished.connect(
            self.export_finished
        )

        self.export_thread.start()

    def export_finished(self):
        self.export_worker = None
        self.export_thread = None