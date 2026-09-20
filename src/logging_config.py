"""Logging setup.

Everything the application logs goes through loggers named after the
module (``logging.getLogger(__name__)``), all of which sit under the
``src`` package logger configured here.

Rules for what gets logged:
  * Counts, durations, file names and error details: yes.
  * The contents of rows (customer names, ticket ids): never. The files
    being processed are customer data and the log outlives them.

Settings (environment variables):
  CSV_EXTRACTOR_LOG_LEVEL  DEBUG, INFO (default), WARNING or ERROR
  CSV_EXTRACTOR_LOG_FILE   full path of the log file, to override the
                           default location
"""

import logging
import os
import sys
from pathlib import Path

PACKAGE_LOGGER_NAME = "src"

LOG_FORMAT = (
    "%(asctime)s %(levelname)-7s [%(processName)s] "
    "%(name)s: %(message)s"
)

# When the log file grows past this at start-up it is kept as
# "<name>.old" and a fresh one is started.
MAX_LOG_BYTES = 5 * 1024 * 1024

logger = logging.getLogger(__name__)

_configured = False


def default_log_path() -> Path:
    """Where the log file lives unless CSV_EXTRACTOR_LOG_FILE says so."""
    override = os.environ.get("CSV_EXTRACTOR_LOG_FILE")

    if override:
        return Path(override)

    base = os.environ.get("LOCALAPPDATA")

    if base:
        folder = Path(base) / "csv_extractor"
    else:
        folder = Path.home() / ".csv_extractor"

    return folder / "logs" / "csv_extractor.log"


def _log_level() -> int:
    name = os.environ.get("CSV_EXTRACTOR_LOG_LEVEL", "INFO").upper()

    level = logging.getLevelName(name)

    return level if isinstance(level, int) else logging.INFO


def _rotate_if_large(path: Path) -> None:
    try:
        if path.exists() and path.stat().st_size > MAX_LOG_BYTES:
            path.replace(path.with_name(path.name + ".old"))
    except OSError:
        # Not worth failing start-up over; keep appending.
        pass


def setup_logging(rotate: bool = True) -> None:
    """Send the application's logs to stderr and to the log file.

    Safe to call more than once and from every process: the background
    processes call it too, because on Windows they start fresh and do not
    inherit the main process's setup. Only the main process should
    rotate the file (rotate=True), since a rotated file cannot be
    renamed while another process has it open.

    If the log file cannot be opened the application carries on with
    logging to stderr only.
    """
    global _configured

    if _configured:
        return

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    package_logger.setLevel(_log_level())
    package_logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(formatter)
    package_logger.addHandler(stderr_handler)

    path = default_log_path()

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        if rotate:
            _rotate_if_large(path)

        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        package_logger.addHandler(file_handler)

    except OSError as error:
        logger.warning(
            "Could not open the log file %s (%s); "
            "logging to the console only.",
            path,
            error
        )

    _configured = True


def reset_logging() -> None:
    """Undo setup_logging(). Used by tests."""
    global _configured

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    for handler in list(package_logger.handlers):
        handler.close()
        package_logger.removeHandler(handler)

    package_logger.propagate = True
    package_logger.setLevel(logging.NOTSET)
    _configured = False
