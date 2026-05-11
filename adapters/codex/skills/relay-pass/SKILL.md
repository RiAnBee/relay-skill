---
name: relay-pass
description: Write a Relay handoff document so a fresh Codex session can continue the work.
---

Force the Relay action to `pass`. Treat user input as the focus for the next session plus optional flags such as `--keep`, `--persist`, or `--full`.

Write a Markdown handoff document summarising the current conversation so a fresh agent can continue the work. Do not summarise the `relay-pass` invocation itself; summarise the real work before this command.

By default, save it to a temporary file named like `relay-<UTC timestamp>-<semantic slug>-<random suffix>.md`. If the user passes `--keep`, `--persist`, or clearly asks to save in the project, save it under `.relay/` in the coding agent's startup directory.

If the user passes `--full`, preserve important original wording verbatim when it affects requirements, constraints, decisions, or doctrine.

After writing the relay file, report the path and a short summary of what was captured.
