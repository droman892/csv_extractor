# 0002. Pass a result file, not the result itself

## Context

The processing process has to hand its result to the window. Sending a large result through a multiprocessing queue means converting it to bytes, pushing it through a pipe, and rebuilding it inside the window's process, which blocks the window and duplicates the data in memory. The screen needs very little of it: the totals, two small tables, the first 100 customers, and the first 100 issues.

## Decision

The processing process saves the full summary to a temporary file and puts only a small "display result" plus the file's path on the queue (a claim check). The export later loads the file by path. The path is chosen by the parent before the process starts, so the parent knows which file to delete if the process is stopped or fails.

## Consequences

- The window's process only ever holds what it displays.
- Temporary files must be cleaned up in every ending: success, failure, crash, stop, and window close. That logic is in one place (`process_utils.remove_result_files`) and tested.
- The summary is stored as JSON, so loading it cannot run code even if the file is tampered with. The only value JSON cannot hold, a `Path` file name, is saved as text. Any other unexpected type makes the save fail instead of being silently converted. See [docs/security.md](../security.md).
