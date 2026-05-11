---
name: relay-pass
user-invocable: true
description: Write a lightweight Relay handoff document so a fresh agent can continue the work. Use when ending, saving, or transferring a session.
argument-hint: "[focus, hint, or next task] [--keep|--persist] [--full]"
---

Run Relay in `pass` mode.

Use the canonical behavior in `../relay/SKILL.md`, but force the action to `pass` even if the user did not type the word `pass`.

Treat all user arguments as the pass-mode focus and flags:

- `--keep` or `--persist`: save under `.relay/` in the coding agent's startup directory.
- `--full`: write a more detailed relay document and preserve important original wording.
- Any other text: describe what the next session should focus on.

Do not summarise the `relay-pass` invocation itself. Summarise the real work that happened before this command.

By default, save it to a temporary file named like `relay-<UTC timestamp>-<semantic slug>-<random suffix>.md`. If the user passes `--keep`, `--persist`, or clearly asks to save in the project, save it under `.relay/` in the coding agent's startup directory.

After writing the file, tell the user the path and give a short summary of what was captured.
