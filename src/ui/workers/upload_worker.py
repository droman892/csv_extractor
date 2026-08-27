from PySide6.QtCore import QObject, Signal, Slot
from ...processing.processor import process_csv

class UploadWorker(QObject):
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    @Slot()
    def process(self):
        try:
            result = process_csv(self.filename)
        except ValueError as error:
            self.failed.emit(str(error))
            return

        self.completed.emit(result)