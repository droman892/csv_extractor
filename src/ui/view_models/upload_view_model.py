from PySide6.QtCore import QObject, Signal

from ...processing.processor import process_csv


class UploadViewModel(QObject):
    processing_completed = Signal(dict)

    def upload_file(self, filename):
        result = process_csv(filename)
        self.processing_completed.emit(result)