# Annotations are not evaluated at run time: multiprocessing's Queue can
# be written as Queue[...] for type checking but is not subscriptable.
from __future__ import annotations

import logging
import pickle
from contextlib import closing
import tempfile
import uuid
from typing import IO
from multiprocessing import Process, Queue
from multiprocessing.queues import Queue as ProcessQueue
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from ..config import MAX_DISPLAYED_ROWS
from ..logging_config import setup_logging
from ..processing.invalid_tickets import iter_invalid_tickets
from ..processing.processor import process_csv
from ..records import (
    CompletedPayload,
    DisplayIssue,
    DisplayResult,
    ProcessingResult,
    WorkerMessage
)
from .process_utils import (
    details_path_for,
    poll_result,
    remove_result_files,
    stop_process
)

logger = logging.getLogger(__name__)



def count_validation_errors(result: ProcessingResult) -> int:

    total = sum(
        len(record.get("errors", []))
        for record in result["invalid_records"]
    )

    return total


def new_result_path() -> str:
    """A unique path in the temp folder for the full result file."""
    return str(
        Path(tempfile.gettempdir())
        / f"csv_extractor_result_{uuid.uuid4().hex}.pkl"
    )


def save_full_result(
    result: ProcessingResult,
    path: str | None = None
) -> str:
    # The caller normally chooses the path, so it knows which file to
    # delete if the process is stopped part-way through writing it.
    try:
        result_file: IO[bytes]

        if path is None:
            result_file = tempfile.NamedTemporaryFile(
                mode="wb",
                prefix="csv_extractor_result_",
                suffix=".pkl",
                delete=False
            )
        else:
            # "xb" refuses to open a file that already exists.
            result_file = open(path, "xb")

        # pickle is used because the summary holds Python objects that
        # the export needs back unchanged. Loading a pickle can run code,
        # so this file must only ever be read by run_export, and only
        # from a path this app chose. See docs/security.md.
        with result_file:
            pickle.dump(
                result,
                result_file,
                protocol=pickle.HIGHEST_PROTOCOL
            )

        return result_file.name

    except (OSError, pickle.PickleError) as error:
        raise RuntimeError(
            "Unable to save the full processing result."
        ) from error


def build_display_result(result: ProcessingResult) -> DisplayResult:

    customer_items = sorted(
        result["summary"]["hours_by_customer"].items(),
        key=lambda item: str(item[0]).lower()
    )

    display_invalid_rows: list[DisplayIssue] = []

    # Only the first few are needed, so only that much is read.
    with closing(iter_invalid_tickets(result)) as invalid_tickets:
        for record in invalid_tickets:
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

    total_invalid_error_count = result.get(
        "total_validation_error_count",
        count_validation_errors(result)
    )

    display_result: DisplayResult = {
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
            result["invalid_tickets_count"],

        "total_invalid_error_count":
            total_invalid_error_count
    }

    return display_result


def run_processing(
    filename: str,
    result_queue: ProcessQueue[WorkerMessage],
    full_result_path: str | None = None
) -> None:

    # This runs in its own process, which does not share the main
    # process's logging setup.
    setup_logging(rotate=False)

    if full_result_path is None:
        full_result_path = new_result_path()

    try:

        # Every invalid ticket goes to a file beside the result file, so
        # a file full of bad rows does not fill the memory.
        result = process_csv(
            filename,
            details_path_for(full_result_path)
        )

        full_result_path = save_full_result(
            result,
            full_result_path
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

    except UnicodeDecodeError as error:

        # Must come before ValueError: it is a kind of ValueError.
        logger.warning("Not valid UTF-8: %s", error)

        result_queue.put(
            (
                "failed",
                "The file is not valid UTF-8 text. Re-save it as "
                "\"CSV UTF-8\" and try again."
            )
        )

    except ValueError as error:

        logger.warning("Rejected the file: %s", error)

        result_queue.put(
            (
                "failed",
                f"{type(error).__name__}: {str(error)}"
            )
        )

    except RuntimeError as error:

        logger.exception("Processing failed")

        result_queue.put(
            (
                "failed",
                f"{type(error).__name__}: {str(error)}"
            )
        )

    except Exception as error:

        logger.exception("Unexpected error while processing")

        result_queue.put(
            (
                "failed",
                f"Unexpected {type(error).__name__}: {str(error)}"
            )
        )


class UploadWorker(QObject):
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, filename: str) -> None:
        super().__init__()

        self.filename = filename
        self.process: Process | None = None
        self.result_queue: ProcessQueue[WorkerMessage] | None = None
        self.poll_timer: QTimer | None = None

        self.full_result_path: str | None = None
        self.stopped = False

    @Slot()
    def process_file(self) -> None:
        self.result_queue = Queue()
        self.full_result_path = new_result_path()

        self.process = Process(
            target=run_processing,
            args=(
                self.filename,
                self.result_queue,
                self.full_result_path
            )
        )

        self.process.start()

        logger.info(
            "Started the processing process (pid %s)",
            self.process.pid
        )

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(50)
        self.poll_timer.timeout.connect(
            self.check_result
        )
        self.poll_timer.start()

    def stop(self) -> None:
        """Stop processing (the window is closing) and delete its output.

        Nothing is emitted afterwards: nobody is left to show a result.
        """
        self.stopped = True

        if stop_process(self.process):
            remove_result_files(self.full_result_path)

    @Slot()
    def check_result(self) -> None:
        result_queue = self.result_queue
        poll_timer = self.poll_timer

        if self.stopped or result_queue is None or poll_timer is None:
            return

        # Also notices a process that died without sending a result.
        result = poll_result(
            self.process,
            result_queue
        )

        if result is None:
            return

        status, value = result

        poll_timer.stop()

        if self.process is not None:
            self.process.join()
            self.process = None

        result_queue.close()
        self.result_queue = None

        if status == "completed":
            self.completed.emit(value)
        else:
            # Nothing was saved that will ever be used.
            remove_result_files(self.full_result_path)
            self.failed.emit(value)