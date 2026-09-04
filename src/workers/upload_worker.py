import pickle
import tempfile

from multiprocessing import Process, Queue
from queue import Empty

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from ..processing.processor import process_csv


MAX_DISPLAYED_ROWS = 100


def count_validation_errors(result):

    total = sum(
        len(record.get("errors", []))
        for record in result["invalid_records"]
    )

    return total


def save_full_result(result):

    temp_file = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix="csv_extractor_result_",
        suffix=".pkl",
        delete=False
    )

    try:
        with temp_file:
            pickle.dump(
                result,
                temp_file,
                protocol=pickle.HIGHEST_PROTOCOL
            )

        return temp_file.name

    except (OSError, pickle.PickleError) as error:
        raise RuntimeError(
            "Unable to save the full processing result."
        ) from error


def build_display_result(result):

    customer_items = sorted(
        result["summary"]["hours_by_customer"].items(),
        key=lambda item: str(item[0]).lower()
    )

    display_invalid_rows = []

    for record in result["invalid_records"]:
        for error in record.get("errors", []):
            if len(display_invalid_rows) >= MAX_DISPLAYED_ROWS:
                break

            display_invalid_rows.append({
                "ticket_id": record["ticket_id"],
                "field": error["field"],
                "invalid_value": error["invalid_value"],
                "reason": error["reason"]
            })

        if len(display_invalid_rows) >= MAX_DISPLAYED_ROWS:
            break

    total_invalid_error_count = count_validation_errors(
        result
    )

    display_result = {
        "filename": result["filename"],

        "total_tickets_count":
            result["total_tickets_count"],

        "valid_tickets_count":
            result["valid_tickets_count"],

        "invalid_tickets_count":
            result["invalid_tickets_count"],

        "summary": {
            "total_hours":
                result["summary"]["total_hours"],

            "tickets_by_status":
                result["summary"]["tickets_by_status"],

            "tickets_by_priority":
                result["summary"]["tickets_by_priority"],

            "hours_by_customer":
                dict(
                    customer_items[:MAX_DISPLAYED_ROWS]
                )
        },

        "invalid_records":
            display_invalid_rows,

        "total_customer_count":
            len(customer_items),

        "total_invalid_record_count":
            len(result["invalid_records"]),

        "total_invalid_error_count":
            total_invalid_error_count
    }

    return display_result


def run_processing(filename, result_queue):

    try:

        result = process_csv(filename)

        full_result_path = save_full_result(
            result
        )

        display_result = build_display_result(
            result
        )

        result_queue.put(
            (
                "completed",
                {
                    "display_result": display_result,
                    "full_result_path": full_result_path
                }
            )
        )

    except ValueError as error:

        result_queue.put(
            (
                "failed",
                f"{type(error).__name__}: {str(error)}"
            )
        )

    except RuntimeError as error:

        result_queue.put(
            (
                "failed",
                f"{type(error).__name__}: {str(error)}"
            )
        )

    except Exception as error:

        result_queue.put(
            (
                "failed",
                f"Unexpected {type(error).__name__}: {str(error)}"
            )
        )


class UploadWorker(QObject):
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, filename):
        super().__init__()

        self.filename = filename
        self.process = None
        self.result_queue = None
        self.poll_timer = None

    @Slot()
    def process_file(self):
        self.result_queue = Queue()

        self.process = Process(
            target=run_processing,
            args=(
                self.filename,
                self.result_queue
            )
        )

        self.process.start()

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(50)
        self.poll_timer.timeout.connect(
            self.check_result
        )
        self.poll_timer.start()

    @Slot()
    def check_result(self):
        try:
            status, value = (
                self.result_queue.get_nowait()
            )

        except Empty:
            return

        self.poll_timer.stop()

        if self.process is not None:
            self.process.join()
            self.process = None

        self.result_queue.close()
        self.result_queue = None

        if status == "completed":
            self.completed.emit(value)
        else:
            self.failed.emit(value)