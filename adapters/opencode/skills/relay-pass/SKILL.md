---
name: relay-pass
user-invocable: true
description: Write a Relay handoff document so a fresh agent can continue the work. Use when ending, saving, or transferring a session.
license: MIT
compatibility: opencode
metadata:
  workflow: handoff
  mode: pass
---

Run Relay in `pass` mode.

Use the canonical behavior in `../relay/SKILL.md`, but force the action to `pass` even if the user did not type the word `pass`.

Treat all user arguments as the pass-mode focus and flags:

- `--keep` or `--persist`: save under `.relay/` in the coding agent's startup directory.
- `--full`: write a more detailed relay document and preserve important original wording.
- Any other text: describe what the next session should focus on.

After writing the file, tell the user the path and give a short summary of what was captured.
