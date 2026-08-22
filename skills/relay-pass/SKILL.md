---
name: relay-pass
description: Write a portable, verifiable Relay handoff artifact using wire schema v2 so a zero-context agent can continue the work. Use when ending, pausing, branching, delegating, reviewing, or transferring a session.
---

Run Relay in `pass` mode.

Use the canonical behavior in `../relay/SKILL.md`, but force the action to `pass` even if the user did not type the word `pass`.

Resolve and read `../relay/references/handoff-v2.md` before drafting. For
`--full`, also read `../relay/references/full-mode.md` and execute its evidence
sweep, structured write, and reverse coverage audit. Finalize and validate with
`../relay/scripts/relay_artifact.py`; do not invent the final filename, Relay ID,
or digest in prose.

Treat all user arguments as the pass-mode focus and flags:

- `--keep` or `--persist`: save under `.relay/` at the stable project root resolved by the canonical skill.
- `--tmp` or `--temp`: save under the system temp directory, `${TMPDIR:-/tmp}`.
- `--full`: run the maximum-fidelity capture protocol, including source evidence, original wording, rationale, failed paths, validation, workspace/runtime state, unknowns, and a post-write coverage audit.
- `--compact` or `--brief`: write the compact relay document.
- Any other text: describe what the next session should focus on.

Do not summarise the `relay-pass` invocation itself. Summarise the real work that happened before this command.

Use the storage and detail rules from `../relay/SKILL.md`. Built-in defaults are project-local `.relay/` storage and compact detail. `.relay/config.json` may change those defaults, and invocation flags override settings for this pass only.

After writing the file, tell the user the path, `relay_id`, validation status,
and a short summary of what was captured.
