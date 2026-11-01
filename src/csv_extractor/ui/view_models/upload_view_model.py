from PySide6.QtCore import QObject, Signal, QThread

from ...workers.upload_worker import UploadWorker


class UploadViewModel(QObject):
    processing_failed = Signal(str)
    processing_completed = Signal(dict)

    def __init__(self) -> None:
        super().__init__()

        self.worker_thread: QThread | None = None
        self.worker: UploadWorker | None = None

    def upload_file(self, filename: str) -> None:
        self.worker_thread = QThread()
        self.worker = UploadWorker(filename)

        self.worker.moveToThread(
            self.worker_thread
        )

        # Starts the work once the thread is running.
        self.worker_thread.started.connect(
            self.worker.process_file
        )

        # Passes the result on to the screen.
        self.worker.completed.connect(
            self.processing_completed
        )

        # Passes the error message on to the screen.
        self.worker.failed.connect(
            self.processing_failed
        )

        # Stops the thread's event loop after a success.
        self.worker.completed.connect(
            self.worker_thread.quit
        )

        # Stops the thread's event loop after a failure.
        self.worker.failed.connect(
            self.worker_thread.quit
        )

        # Deletes the worker once the thread has stopped.
        self.worker_thread.finished.connect(
            self.worker.deleteLater
        )

        # Deletes the thread object and clears the references so the next
        # upload starts fresh.
        self.worker_thread.finished.connect(
            self.processing_finished
        )

        self.worker_thread.start()

    def processing_finished(self) -> None:
        thread = self.worker_thread

        if thread is not None:
            # finished is emitted from the thread just before it exits, so
            # deleting the thread object straight away can abort with
            # "QThread: Destroyed while thread is still running". Waiting
            # for the exit first takes only moments.
            thread.wait()
            thread.deleteLater()

        self.worker = None
        self.worker_thread = None

    def shutdown(self) -> None:
        """Stop any processing in progress (the window is closing)."""
        worker = self.worker
        thread = self.worker_thread

        try:
            if worker is not None:
                worker.stop()
        except RuntimeError:
            # The worker was already deleted because it had finished.
            pass

        if thread is not None:
            # Do not let the app exit while this thread is still running.
            thread.quit()
            thread.wait(3000)
