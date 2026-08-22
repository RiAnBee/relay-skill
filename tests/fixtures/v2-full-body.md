# Relay: reward logging full handoff

## Goal

Finish the reward logging fix and preserve compatibility.

## Hard Constraints

- Keep the log format backward-compatible.

## Acceptance Criteria

- [ ] The reward field reaches the final write call.
- [ ] The targeted regression test passes.

## Progress Ledger

### Done

- Traced the field through the adapter.

### In Progress

- Patch the wrapper call site.

### Not Started

- Run broader validation if the targeted test passes.

## Current State

### Verified / Observed

- The field exists before the wrapper call.

### Assumptions / Unverified

- Unknown whether another adapter has the same defect; inspect sibling adapters if the targeted fix reveals shared code.

## Settled Decisions

- Keep the fix local because a storage redesign is outside scope.

## Failed Approaches

- Rewriting the adapter widened scope and did not isolate the bug.

## Validation

- Not checked after the pending patch: run the targeted regression test first.

## Known Blockers

- None known.

## Open Questions

- None known.

## Explicit Next Step

Patch `src/wrapper.py` at the final write call.

## References

- `src/wrapper.py`: patch target.
- `tests/test_reward_logging.py`: first validation command.

## Resume Prompt

Continue the reward logging fix. Start at the wrapper call and preserve compatibility.
