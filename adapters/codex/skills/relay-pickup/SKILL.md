---
name: relay-pickup
description: Pick up from a Relay handoff document and continue saved work in Codex.
---

Force the Relay action to `pickup`. Treat user input as a file path, search hint, or continuation focus.

Selection order:

1. If the user provided an explicit file path, read that file.
2. If the user provided a hint or task description, search likely relay files in `.relay/` and temporary relay locations. Prefer matches by filename first, then by document content.
3. If the user provided no hint, use the newest likely relay document.
4. If multiple candidates are similarly likely, ask one concise clarification question.

Likely relay files include names matching `relay-*.md` and `handoff-*.md`.

Read the selected relay document before acting, state which file you used, and continue the work rather than merely summarising the handoff.
