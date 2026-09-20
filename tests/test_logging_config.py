import logging

from src.logging_config import (
    MAX_LOG_BYTES,
    PACKAGE_LOGGER_NAME,
    default_log_path,
    reset_logging,
    setup_logging
)


def flush(logger):
    for handler in logger.handlers:
        handler.flush()


def test_setup_logging_writes_to_the_log_file(tmp_path):
    setup_logging()

    logger = logging.getLogger("src.some_module")
    logger.info("hello from a test")

    flush(logging.getLogger(PACKAGE_LOGGER_NAME))

    text = (tmp_path / "test.log").read_text(encoding="utf-8")

    assert "hello from a test" in text
    assert "INFO" in text
    assert "src.some_module" in text


def test_setup_logging_is_idempotent():
    setup_logging()
    setup_logging()

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    # One console handler and one file handler, not four.
    assert len(package_logger.handlers) == 2


def test_the_log_level_comes_from_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("CSV_EXTRACTOR_LOG_LEVEL", "WARNING")

    setup_logging()

    logging.getLogger("src.some_module").info("too quiet to keep")
    logging.getLogger("src.some_module").warning("worth keeping")

    flush(logging.getLogger(PACKAGE_LOGGER_NAME))

    text = (tmp_path / "test.log").read_text(encoding="utf-8")

    assert "too quiet to keep" not in text
    assert "worth keeping" in text


def test_an_unknown_log_level_falls_back_to_info(monkeypatch):
    monkeypatch.setenv("CSV_EXTRACTOR_LOG_LEVEL", "LOUD")

    setup_logging()

    assert logging.getLogger(PACKAGE_LOGGER_NAME).level == logging.INFO


def test_setup_logging_survives_an_unwritable_log_location(
    tmp_path,
    monkeypatch
):
    blocker = tmp_path / "a_file"
    blocker.write_text("not a folder")

    # A folder cannot be created inside a file.
    monkeypatch.setenv(
        "CSV_EXTRACTOR_LOG_FILE",
        str(blocker / "logs" / "x.log")
    )

    setup_logging()

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    # Only the console handler is left.
    assert len(package_logger.handlers) == 1


def test_a_large_log_file_is_rotated_at_start(tmp_path, monkeypatch):
    log_file = tmp_path / "test.log"
    log_file.write_bytes(b"x" * (MAX_LOG_BYTES + 1))

    setup_logging()

    assert (tmp_path / "test.log.old").exists()
    assert log_file.stat().st_size < MAX_LOG_BYTES


def test_background_processes_do_not_rotate_the_log_file(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_bytes(b"x" * (MAX_LOG_BYTES + 1))

    setup_logging(rotate=False)

    assert not (tmp_path / "test.log.old").exists()


def test_reset_logging_removes_the_handlers():
    setup_logging()

    reset_logging()

    assert logging.getLogger(PACKAGE_LOGGER_NAME).handlers == []


def test_default_log_path_uses_localappdata(monkeypatch, tmp_path):
    monkeypatch.delenv("CSV_EXTRACTOR_LOG_FILE")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert default_log_path() == (
        tmp_path / "csv_extractor" / "logs" / "csv_extractor.log"
    )
