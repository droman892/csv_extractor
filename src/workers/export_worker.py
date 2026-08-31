import pickle
from multiprocessing import Process, Queue
from queue import Empty

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from ..services.results_export_service import ResultsExportService


def run_export(
    full_result_path,
    destination_path,
    result_queue
):
    try:
        with open(
            full_result_path,
            "rb"
        ) as result_file:

            result = pickle.load(
                result_file
            )

        ResultsExportService.export_results(
            result,
            destination_path
        )

        result_queue.put(
            (
                "completed",
                destination_path
            )
        )

    except Exception as error:
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
        full_result_path,
        destination_path
    ):
        super().__init__()

        self.full_result_path = full_result_path
        self.destination_path = destination_path

        self.process = None
        self.result_queue = None
        self.poll_timer = None

    @Slot()
    def export_file(self):
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