from PySide6.QtCore import QObject, Signal, QThread

from ...workers.upload_worker import UploadWorker


class UploadViewModel(QObject):
    processing_failed = Signal(str)
    processing_completed = Signal(dict)

    def __init__(self) -> None:
        super().__init__()

        # Note: this hides QObject.thread(); nothing calls that method.
        self.thread: QThread | None = None  # type: ignore[assignment]
        self.worker: UploadWorker | None = None

    def upload_file(self, filename: str) -> None:
        self.thread = QThread()
        self.worker = UploadWorker(filename)

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.process_file
        )

        self.worker.completed.connect(
            self.processing_completed
        )

        self.worker.failed.connect(
            self.processing_failed
        )

        self.worker.completed.connect(
            self.thread.quit
        )

        self.worker.failed.connect(
            self.thread.quit
        )

        self.thread.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        self.thread.finished.connect(
            self.processing_finished
        )

        self.thread.start()

    def processing_finished(self) -> None:
        self.worker = None
        self.thread = None

    def shutdown(self) -> None:
        """Stop any processing in progress (the window is closing)."""
        worker = self.worker
        thread = self.thread

        try:
            if worker is not None:
                worker.stop()
        except RuntimeError:
            # The worker was already deleted: it had finished.
            pass

        if thread is not None:
            # Do not let the app exit while this thread is still running.
            thread.quit()
            thread.wait(3000)
