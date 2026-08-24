from PySide6.QtCore import QObject, Signal

from ...processing.processor import process_csv


class UploadViewModel(QObject):
    processing_failed = Signal(str)
    processing_completed = Signal(dict)

    def upload_file(self, filename):
        try:
            result = process_csv(filename)
        except ValueError as error:
            self.processing_failed.emit(str(error))
            return
        self.processing_completed.emit(result)