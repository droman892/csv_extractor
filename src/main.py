import logging
import multiprocessing
import sys
from PySide6.QtWidgets import QApplication
from .logging_config import default_log_path, setup_logging
from .ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()

    logger.info("CSV Extractor starting (log file: %s)", default_log_path())

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    exit_code = app.exec()

    logger.info("CSV Extractor closed")

    sys.exit(exit_code)


if __name__ == "__main__":
    # Required before anything else when frozen (PyInstaller) on Windows:
    # a frozen build has no python.exe to re-launch, so the multiprocessing
    # child processes started in workers/upload_worker.py and
    # export_worker.py re-run this same .exe. freeze_support() detects
    # that a child is starting, runs it, and returns without opening a
    # second window. It is a no-op when not frozen.
    multiprocessing.freeze_support()
    main()
