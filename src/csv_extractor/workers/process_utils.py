# Annotations are not evaluated at run time: multiprocessing's Queue can
# be written as Queue[...] for type checking but is not subscriptable.
from __future__ import annotations

import logging
import os
from pathlib import Path
from multiprocessing.process import BaseProcess
from multiprocessing.queues import Queue as ProcessQueue
from queue import Empty

from ..records import WorkerMessage

logger = logging.getLogger(__name__)


def poll_result(
    process: BaseProcess | None,
    result_queue: ProcessQueue[WorkerMessage]
) -> WorkerMessage | None:
    """Check a background process for its result without blocking.

    Returns:
        (status, value) - the message the process sent
        None            - nothing yet; the process is still working

    If the process has ended without sending anything (it crashed, ran out
    of memory, or was killed), a ("failed", message) result is returned
    instead of None. Without this the caller would poll forever and the
    progress overlay would never go away.
    """
    try:
        return result_queue.get_nowait()
    except Empty:
        pass

    if process is None or process.is_alive():
        return None

    # The process is gone. A message it sent just before exiting may still
    # be on its way through the queue's pipe, so wait briefly for it.
    try:
        return result_queue.get(timeout=0.5)
    except Empty:
        logger.error(
            "The background process ended without sending a result "
            "(exit code %s)",
            process.exitcode
        )

        return (
            "failed",
            "Processing stopped unexpectedly "
            f"(exit code {process.exitcode})."
        )


def stop_process(process: BaseProcess | None) -> bool:
    """Kill a background process if it is still running.

    Returns True if it was running (so it was killed before it could
    finish), False if it had already ended or there is no process.
    """
    if process is None or not process.is_alive():
        return False

    logger.info("Stopping the background process")

    process.terminate()
    process.join(timeout=2)

    return True


def remove_file(path: str | None) -> None:
    """Delete a file if it exists. Never raises."""
    if not path:
        return

    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError as error:
        logger.warning("Could not delete %s: %s", path, error)


def details_path_for(result_path: str) -> str:
    """Where the invalid tickets of a result are written.

    It sits beside the result file and shares its name:
    csv_extractor_result_<id>.pkl -> csv_extractor_result_<id>.invalid.jsonl
    """
    return str(Path(result_path).with_suffix(".invalid.jsonl"))


def remove_result_files(result_path: str | None) -> None:
    """Delete a result file and the invalid-ticket file beside it."""
    if not result_path:
        return

    remove_file(result_path)
    remove_file(details_path_for(result_path))
