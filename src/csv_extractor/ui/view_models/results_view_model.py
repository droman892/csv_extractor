import os
from typing import Any

from PySide6.QtCore import QObject, Signal, QThread

from ...records import DisplayIssue, DisplayResult
from ...workers.export_worker import ExportWorker
from ...workers.process_utils import remove_result_files


class ResultsViewModel(QObject):
    export_started = Signal()
    export_completed = Signal(str)
    export_failed = Signal(str)

    def __init__(
        self,
        display_result: DisplayResult,
        full_result_path: str | None
    ) -> None:
        super().__init__()

        self.result = display_result
        self.full_result_path = full_result_path

        self.export_thread: QThread | None = None
        self.export_worker: ExportWorker | None = None

    def get_filename(self) -> str:
        return os.path.basename(
            self.result["filename"]
        )

    def get_summary(self) -> dict[str, Any]:
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

    def get_invalid_rows(self) -> list[DisplayIssue]:
        return self.result["invalid_records"]

    def get_customer_rows(self) -> list[tuple[str, float]]:
        return list(
            self.result["summary"][
                "hours_by_customer"
            ].items()
        )

    def get_total_customer_count(self) -> int:
        return self.result[
            "total_customer_count"
        ]

    def get_total_invalid_record_count(self) -> int:
        return self.result[
            "total_invalid_record_count"
        ]

    def get_total_invalid_error_count(self) -> int:
        return self.result[
            "total_invalid_error_count"
        ]

    def export_results(self, destination_path: str) -> None:
        if not self.full_result_path:
            # The window is closing and the result file is already gone.
            self.export_failed.emit(
                "The full results are no longer available."
            )
            return

        self.export_started.emit()

        self.export_thread = QThread()

        self.export_worker = ExportWorker(
            self.full_result_path,
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

    def export_finished(self) -> None:
        self.export_worker = None
        self.export_thread = None

    def shutdown(self) -> None:
        """Stop any export in progress, then delete the full result.

        The order matters: an export that is still running reads the
        full result file, so it must be stopped before that is deleted.
        """
        worker = self.export_worker
        thread = self.export_thread

        try:
            if worker is not None:
                worker.stop()
        except RuntimeError:
            # The worker was already deleted: it had finished.
            pass

        if thread is not None:
            thread.quit()
            thread.wait(3000)

        self.cleanup_full_result()

    def cleanup_full_result(self) -> None:
        if not self.full_result_path:
            return

        # Also deletes the invalid-ticket file that belongs to it.
        remove_result_files(self.full_result_path)

        self.full_result_path = None