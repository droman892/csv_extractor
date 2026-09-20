from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.workers.process_utils import (
    details_path_for,
    poll_result,
    remove_file,
    remove_result_files,
    stop_process
)


def make_process(alive, exitcode=None):
    return SimpleNamespace(
        is_alive=lambda: alive,
        exitcode=exitcode
    )


def test_poll_result_returns_the_message_when_one_is_ready():
    result_queue = Queue()
    result_queue.put(("completed", "value"))

    assert poll_result(
        make_process(alive=True),
        result_queue
    ) == ("completed", "value")


def test_poll_result_returns_none_while_the_process_is_still_working():
    assert poll_result(
        make_process(alive=True),
        Queue()
    ) is None


def test_poll_result_returns_none_when_there_is_no_process():
    assert poll_result(None, Queue()) is None


def test_poll_result_treats_a_mock_process_as_running():
    assert poll_result(MagicMock(), Queue()) is None


def test_poll_result_reports_failure_when_the_process_died_silently():
    result = poll_result(
        make_process(alive=False, exitcode=-9),
        Queue()
    )

    status, message = result

    assert status == "failed"
    assert "stopped unexpectedly" in message
    assert "-9" in message


def test_poll_result_prefers_a_late_message_over_reporting_a_crash():
    class QueueThatDeliversLate:
        def __init__(self):
            self.calls = 0

        def get_nowait(self):
            from queue import Empty
            raise Empty

        def get(self, timeout):
            return ("completed", "late value")

    assert poll_result(
        make_process(alive=False, exitcode=0),
        QueueThatDeliversLate()
    ) == ("completed", "late value")


def test_stop_process_terminates_a_running_process():
    process = MagicMock()
    process.is_alive.return_value = True

    assert stop_process(process) is True

    process.terminate.assert_called_once()
    process.join.assert_called_once()


def test_stop_process_leaves_a_finished_process_alone():
    process = MagicMock()
    process.is_alive.return_value = False

    assert stop_process(process) is False

    process.terminate.assert_not_called()


def test_stop_process_accepts_no_process():
    assert stop_process(None) is False


def test_remove_file_deletes_the_file(tmp_path):
    path = tmp_path / "x.pkl"
    path.write_bytes(b"x")

    remove_file(str(path))

    assert not path.exists()


def test_remove_file_ignores_a_missing_file_or_no_path(tmp_path):
    remove_file(str(tmp_path / "missing.pkl"))
    remove_file(None)
    remove_file("")


def test_details_path_sits_beside_the_result_file_with_the_same_name():
    assert details_path_for("/tmp/csv_extractor_result_abc.pkl") == str(
        Path("/tmp/csv_extractor_result_abc.invalid.jsonl")
    )


def test_remove_result_files_deletes_both_files(tmp_path):
    result = tmp_path / "result.pkl"
    details = tmp_path / "result.invalid.jsonl"
    other = tmp_path / "other.pkl"

    for path in (result, details, other):
        path.write_bytes(b"x")

    remove_result_files(str(result))

    assert not result.exists()
    assert not details.exists()
    assert other.exists()


def test_remove_result_files_copes_with_missing_files_and_no_path(tmp_path):
    remove_result_files(str(tmp_path / "missing.pkl"))
    remove_result_files(None)
    remove_result_files("")


def test_remove_result_files_deletes_the_details_when_the_result_is_gone(
    tmp_path
):
    details = tmp_path / "result.invalid.jsonl"
    details.write_bytes(b"x")

    remove_result_files(str(tmp_path / "result.pkl"))

    assert not details.exists()
