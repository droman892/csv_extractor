# from PySide6.QtCore import QObject, Signal

# from ...processing.processor import process_csv


# class UploadViewModel(QObject):
#     processing_failed = Signal(str)
#     processing_completed = Signal(dict)

#     def upload_file(self, filename):
#         try:
#             result = process_csv(filename)
#         except ValueError as error:
#             self.processing_failed.emit(str(error))
#             return
#         self.processing_completed.emit(result)


from PySide6.QtCore import QObject, Signal, QThread
from ..workers.upload_worker import UploadWorker

class UploadViewModel(QObject):
    processing_failed = Signal(str)
    processing_completed = Signal(dict)

    def __init__(self):
        super().__init__()

        self.thread = None
        self.worker = None

    def upload_file(self, filename):
        self.thread = QThread()
        self.worker = UploadWorker(filename)

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(
            self.worker.process
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

    def processing_finished(self):
        self.worker = None
        self.thread = None