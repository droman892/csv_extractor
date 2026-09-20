import logging
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
    main()
