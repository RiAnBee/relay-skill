---
name: relay
description: Pass or pick up a lightweight handoff document so a fresh Codex session can continue the work. Use when ending, resuming, or transferring context between coding-agent windows.
---

Relay has two actions:

- `pass`: write a handoff document for the next agent.
- `pickup`: find, read, and use a relay document to continue the work.

If no explicit action is provided, infer whether the user is passing or picking up from the conversation context.

For explicit pass or pickup entrypoints, prefer the `relay-pass` and `relay-pickup` skills.

## Smart Behavior

- Use `pass` when the current conversation contains substantial work and the user appears to be ending, saving, or transferring the session.
- Use `pickup` when the current conversation is thin, the user appears to be starting or resuming work, or the user mentions continuing, resuming, picking up, last time, a prior task, or a brief task hint.
- If uncertain and this is a fresh session with relay files available, use `pickup` on the newest likely relay file.
- If uncertain and this session already contains substantial work, use `pass`.

For pass mode, write a Markdown relay document summarising the current conversation so a fresh agent can continue the work. By default, save it to a temporary `relay-*.md` file. If the user asks to keep or persist it, save it under `.relay/` in the startup directory.

For pickup mode, find the requested relay document, read it, state which file you are using, and continue the saved work rather than merely summarising it.
