# 0007. Stop silently when the window closes

Status: accepted (2026-09).

## Context

Closing the window while a large file is processing or exporting could leave the background process running with nothing to show its result to, and could leave half-written files behind: a partial temporary result, or a partial report that looks like a real one.

## Decision

Closing the window stops any running process immediately and without asking, and deletes its partial output: the temporary result and, for an export, the partly written report. Files a finished process left behind are removed as well, so nothing survives a normal close. Nothing is shown to the user.

## Consequences

- No orphan processes and no misleading partial reports.
- A user who closes the window mid-export loses that export. There is no confirmation dialog.
- There is no cancel button, so closing the window is the only way to stop a run.
- The deletion rules are tested with fake processes. A separate end-to-end test kills a real processing process and checks that the failure is reported and no file is left.
