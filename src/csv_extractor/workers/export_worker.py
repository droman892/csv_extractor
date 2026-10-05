# Annotations are not evaluated at run time: multiprocessing's Queue can
# be written as Queue[...] for type checking but is not subscriptable.
from __future__ import annotations

import logging
import pickle
from multiprocessing import Process, Queue
from multiprocessing.queues import Queue as ProcessQueue
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from ..logging_config import setup_logging
from ..records import WorkerMessage
from ..services.results_export_service import ResultsExportService
from .process_utils import poll_result, remove_file, stop_process

logger = logging.getLogger(__name__)


def run_export(
    full_result_path: str,
    destination_path: str | Path,
    result_queue: ProcessQueue[WorkerMessage]
) -> None:
    # This runs in its own process, which does not share the main
    # process's logging setup.
    setup_logging(rotate=False)

    try:
        with open(
            full_result_path,
            "rb"
        ) as result_file:

            # SECURITY: unpickling runs whatever code the file asks for,
            # so it is only safe for a file this app wrote itself.
            # full_result_path comes from the upload worker (a random
            # name in the user's own temp folder, created exclusively),
            # never from the CSV or from anything the user types. Do not
            # point this at a file the user chooses. Accepted risk for a
            # local single-user tool; see docs/security.md.
            result = pickle.load(
                result_file
            )

        ResultsExportService.export_results(
            result,
            destination_path
        )

        logger.info("Export finished")

        result_queue.put(
            (
                "completed",
                destination_path
            )
        )

    except Exception as error:
        logger.exception("Export failed")

        result_queue.put(
            (
                "failed",
                str(error)
            )
        )


class ExportWorker(QObject):
    completed = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        full_result_path: str,
        destination_path: str
    ) -> None:
        super().__init__()

        self.full_result_path = full_result_path
        self.destination_path = destination_path

        self.process: Process | None = None
        self.result_queue: ProcessQueue[WorkerMessage] | None = None
        self.poll_timer: QTimer | None = None

        self.stopped = False

    @Slot()
    def export_file(self) -> None:
        self.result_queue = Queue()

        self.process = Process(
            target=run_export,
            args=(
                self.full_result_path,
                self.destination_path,
                self.result_queue
            )
        )

        self.process.start()

        logger.info(
            "Started the export process (pid %s)",
            self.process.pid
        )

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(50)
        self.poll_timer.timeout.connect(
            self.check_result
        )
        self.poll_timer.start()

    def stop(self) -> None:
        """Stop exporting (the window is closing).

        A report that was only partly written is deleted, so it cannot
        be mistaken for a complete one.
        """
        self.stopped = True

        if stop_process(self.process):
            remove_file(self.destination_path)

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
            self.failed.emit(value)