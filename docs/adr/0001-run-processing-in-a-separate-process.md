# 0001. Run processing and export in a separate process

Status: accepted. Recorded after the fact, from the code and its tests.

## Context

Validating millions of rows is CPU-bound Python. In a thread it would share the interpreter lock with the window and make it stutter or freeze. A thread also cannot be stopped from outside, so closing the window mid-run would have to wait for it or leave it running.

## Decision

The work runs in a `multiprocessing.Process`. A worker object living on a `QThread` starts the process, polls its result queue every 50 ms and emits a Qt signal when the answer arrives. If the process ends without sending an answer, the worker reports that it stopped unexpectedly.

## Consequences

- The window keeps painting while a large file is processed, and the process can be killed when the window closes.
- The process starts fresh on Windows (it does not inherit the parent's logging setup or state), so it configures its own logging and everything it needs is passed as arguments.
- Results must cross a process boundary, which is what [0002](0002-pass-a-result-file-not-the-result.md) is about.
- The worker/thread wiring is covered by tests that use a real `QThread` and, separately, by end-to-end tests that drive the workers with real processes. In the Linux development sandbox, some of the tests that use a real `QThread` crashed intermittently; the cause has not been investigated.
