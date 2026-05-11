---
name: relay-pickup
user-invocable: true
description: Find and read a Relay handoff document, then continue the saved work. Use when starting or resuming from prior context.
license: MIT
compatibility: opencode
metadata:
  workflow: handoff
  mode: pickup
---

Run Relay in `pickup` mode.

Use the canonical behavior in `../relay/SKILL.md`, but force the action to `pickup` even if the user did not type the word `pickup`.

Treat all user arguments as pickup selection or continuation context:

- If the user provided a file path, read that file.
- If the user provided a hint or task description, search likely relay files in `.relay/` and temporary relay locations.
- If the user provided no hint, use the newest likely relay document.
- If multiple candidates are similarly likely, ask one concise clarification question.

State which relay file you are using, read it before acting, and continue the user's task.
