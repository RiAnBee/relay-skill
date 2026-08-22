# Relay: reward logging

## Goal

Finish the reward logging fix without widening the storage design.

## Hard Constraints

- Keep the log format backward-compatible.

## Current State

The wrapper drops the reward field before the final write call.

## Explicit Next Step

Patch the wrapper call site, then run the targeted regression test.

## References

- `src/wrapper.py`: suspected bug location.
