# 0002. Pass a result file, not the result itself

Status: accepted. Recorded after the fact, from the code and its tests.

## Context

The processing process has to hand its result to the window. Sending a large result through a multiprocessing queue means pickling it, pushing it through a pipe and unpickling it inside the window's process, which blocks the window and duplicates the data in memory. The screen needs very little of it: the totals, two small tables, the first 100 customers and the first 100 issues.

## Decision

The processing process saves the full summary to a temporary file and puts only a small "display result" plus the file's path on the queue (a claim check). The export later loads the file by path. The path is chosen by the parent before the process starts, so the parent knows which file to delete if the process is stopped or fails.

## Consequences

- The window's process only ever holds what it displays.
- Temporary files must be cleaned up in every ending: success, failure, crash, stop and window close. That logic is in one place (`process_utils.remove_result_files`) and tested.
- The summary is stored with `pickle`, which is unsafe to load from an untrusted file. The risk is accepted: the file is written by the app itself, in the user's own temp folder, under a random name, and is read back only from a path the app chose. That reasoning holds for a single-user desktop tool. It stops holding if the app runs on a shared machine or loads a result file the user picks; at that point the summary should move to JSON, as the invalid tickets already are. See [docs/security.md](../security.md).
