---
name: relay-pass
user-invocable: true
description: Write a high-signal Relay handoff document so a fresh agent can continue the work. Use when ending, saving, or transferring a session.
argument-hint: "[focus, hint, or next task] [--keep|--persist|--tmp|--temp] [--full|--compact|--brief]"
---

Run Relay in `pass` mode.

Use the canonical behavior in `../relay/SKILL.md`, but force the action to `pass` even if the user did not type the word `pass`.

Treat all user arguments as the pass-mode focus and flags:

- `--keep` or `--persist`: save under `.relay/` in the coding agent's startup directory.
- `--tmp` or `--temp`: save under the system temp directory, `${TMPDIR:-/tmp}`.
- `--full`: write the maximum-fidelity relay document and preserve important original wording, rationale, and failed paths.
- `--compact` or `--brief`: write the compact relay document.
- Any other text: describe what the next session should focus on.

Do not summarise the `relay-pass` invocation itself. Summarise the real work that happened before this command.

Use the storage and detail rules from `../relay/SKILL.md`. Built-in defaults are project-local `.relay/` storage and compact detail. `.relay/config.json` may change those defaults, and invocation flags override settings for this pass only.

After writing the file, tell the user the path and give a short summary of what was captured.
