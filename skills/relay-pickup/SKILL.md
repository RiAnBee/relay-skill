---
name: relay-pickup
user-invocable: true
description: Find and read a Relay handoff document, then continue the saved work. Use when starting or resuming from prior context.
argument-hint: "[file path, focus, hint, or next task]"
---

Run Relay in `pickup` mode.

Use the canonical behavior in `../relay/SKILL.md`, but force the action to `pickup` even if the user did not type the word `pickup`.

Treat all user arguments as pickup selection or continuation context:

- If the user provided a file path, read that file.
- If the user provided a hint or task description, build a shallow candidate set from `.relay/` and the system temp directory. Prefer matches by filename first, then by reading candidate file content.
- If the user provided no hint, use the newest likely relay document.
- If multiple candidates are similarly likely, ask one concise clarification question.

Likely relay files include names matching `relay-*.md` and, for compatibility with Matt Pocock's original handoff convention, `handoff-*.md`.

Candidate discovery must be shallow and bounded:

- Check project-local files under `.relay/`.
- Check only top-level files in the system temp directory, `${TMPDIR:-/tmp}`.
- Never recursively scan shared temp roots such as `/tmp` or `$TMPDIR`.
- Never run `rg` over `/tmp`, `$TMPDIR`, or another shared temp root.
- If content matching is needed, first build filename candidates, then read only those candidate files.

Recommended Linux temp discovery command:

```bash
find "${TMPDIR:-/tmp}" -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -printf '%T@ %p\n' 2>/dev/null
```

Recommended project discovery command:

```bash
find .relay -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -printf '%T@ %p\n' 2>/dev/null
```

Merge the candidate lists and prefer the newest file by modification time unless the user's hint points clearly to another candidate.

State which relay file you are using, read it before acting, and continue the user's task. Do not merely summarise the relay document unless the user asks for a summary.
