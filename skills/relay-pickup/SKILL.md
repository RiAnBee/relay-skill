---
name: relay-pickup
user-invocable: true
description: Find the best Relay handoff document, validate it enough to avoid obvious mistakes, then continue the saved work.
argument-hint: "[file path, focus, hint, or next task]"
---

Run Relay in `pickup` mode.

Use the canonical behavior in `../relay/SKILL.md`, but force the action to `pickup` even if the user did not type the word `pickup`.

Treat all user arguments as pickup selection or continuation context:

- If the user provided a file path, read that file.
- If the user provided a hint or task description, build a shallow candidate set from `.relay/` first and the system temp directory second. Prefer exact filename or slug matches before reading body content.
- If the user provided no hint, do not silently auto-pick on a fresh ambiguous session. Prefer one concise clarification question unless one candidate is clearly dominant.
- If multiple candidates are similarly likely, ask one concise clarification question.

Likely relay files include names matching `relay-*.md` and, for compatibility with Matt Pocock's original handoff convention, `handoff-*.md`.

Candidate discovery must be shallow and bounded:

- Check project-local files under `.relay/` first.
- Check only top-level files in the system temp directory, `${TMPDIR:-/tmp}`, if needed.
- Never recursively scan shared temp roots such as `/tmp` or `$TMPDIR`.
- Never run `rg` over `/tmp`, `$TMPDIR`, or another shared temp root.
- If content matching is needed, first build filename candidates, then read only those candidate files.

Recommended temp discovery command:

```bash
find "${TMPDIR:-/tmp}" -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -print 2>/dev/null
```

Recommended project discovery command:

```bash
find .relay -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -print 2>/dev/null
```

When you have a candidate:

- State which relay file you are using.
- Read it before acting.
- If it records `schema_version`, `branch`, or `commit`, use those details to sanity-check the pickup.
- If it looks stale, mismatched, or incomplete, warn briefly instead of pretending the baton pass is perfect.
- Continue the user's task from that context. Do not merely summarise the relay document unless the user asks for a summary.
