import pytest

from src.logging_config import reset_logging


@pytest.fixture(autouse=True)
def isolated_logging(tmp_path, monkeypatch):
    """Keep tests from writing to the real log file.

    The variable is inherited by the background processes tests start,
    so they log into the test's temporary folder too.
    """
    monkeypatch.setenv(
        "CSV_EXTRACTOR_LOG_FILE",
        str(tmp_path / "test.log")
    )

    reset_logging()

    yield

    reset_logging()
