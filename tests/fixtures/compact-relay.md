---
schema_version: 1
created: 2026-06-03T09:15:30Z
mode: compact
storage: project
working_directory: /workspace/example-app
focus: continue reward logging fix
branch: main
commit: a1b2c3d4
---

# Relay: reward logging fix

## Goal

Continue the reward logging fix without reopening the storage design.

## Hard Constraints

- Keep the current log format backward-compatible.
- Do not widen scope into a general analytics refactor.

## Current State

The wrapper path was traced and the missing reward field is likely dropped before the final write call. The targeted regression test exists but was not rerun after the last edit.

## Failed Approaches

- Rewriting the whole logging adapter added unrelated churn and did not isolate the bug.

## Settled Decisions

- The fix should stay local to reward logging rather than changing the broader experiment storage layout.

## Explicit Next Step

Patch the wrapper call site, then rerun the targeted reward logging test.

## References

- `src/wrapper.py`: likely source of the missing reward field.
- `tests/test_reward_logging.py`: targeted regression coverage.
