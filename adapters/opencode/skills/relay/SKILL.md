---
name: relay
user-invocable: true
description: Pass or pick up a lightweight handoff document so a fresh agent can continue the work. Use when ending a session, resuming prior work, or transferring context between coding-agent windows.
license: MIT
compatibility: opencode
metadata:
  workflow: handoff
  audience: coding-agents
---

Relay has two actions:

- `pass`: write a handoff document for the next agent.
- `pickup`: find, read, and use a relay document to continue the work.

If the user did not provide an explicit action, infer the action from context:

- Use `pass` when the current conversation contains substantial work and the user appears to be ending, saving, or transferring the session.
- Use `pickup` when the current conversation is thin, the user appears to be starting or resuming work, or the user mentions continuing, resuming, picking up, last time, a prior task, or a brief task hint.
- If uncertain and this is a fresh session with relay files available, use `pickup` on the newest likely relay file.
- If uncertain and this session already contains substantial work, use `pass`.

## Pass

Write a handoff document summarising the current conversation so a fresh agent can continue the work.

The relay command invocation itself is not the subject of the handoff. Summarise the real work before the relay command, not the fact that the user ran relay.

By default, save it to a path produced by `mktemp -t relay-<timestamp>-<slug>-XXXXXX.md` (read the file before you write to it).

Use this filename shape:

```text
relay-<UTC timestamp>-<semantic slug>-<random suffix>.md
```

Example:

```text
relay-20260511T083012Z-exp3-reward-logging-a1b2c3.md
```

Choose a short semantic slug from the conversation. Prefer 2 to 6 lowercase ASCII words joined by hyphens. The slug should describe the task topic, not the relay action.

If the user passes `--keep`, `--persist`, or clearly asks in natural language to keep the relay in the project, save it under `.relay/` in the coding agent's startup directory instead of using a temporary path. Create `.relay/` if needed.

Natural-language persistence requests include phrases like "keep this", "persist this", "save it in the project", "put it in the project directory", "long-term save", "don't use a temp file", "长期保存", "放项目里", "保存到目录", or "别放临时文件".

Suggest the skills to be used, if any, by the next session.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

If the user passes `--full`, or clearly asks for a very detailed handoff in natural language, write a more detailed relay document. Preserve important original wording verbatim when it affects requirements, constraints, decisions, or doctrine. Spend tokens when needed, but still do not duplicate existing artifacts; reference them instead.

Natural-language detailed-mode requests include phrases like "full", "very detailed", "don't save tokens", "preserve the wording", "include the important original text", "超详细", "详细保存", "别省 token", "保留原文", or "重要内容都写进去".

Use this Markdown structure by default:

```markdown
# Relay: <short title>

Created: <ISO 8601 timestamp>
Working directory: `<cwd>`
Mode: temporary | persistent
Focus: <user-provided focus, if any>

## Summary

<Compact summary of the current conversation so a fresh agent can continue the work.>

## Current State

<Where things stand now. Include completed/in-progress/pending facts only when they are actually known.>

## References

- `<path-or-url>`: <why it matters>
```

Add these sections only when they are actually needed:

```markdown
## Explicit Next Step

<Only include if the user, plan, issue, or current work clearly established the next action.>
```

```markdown
## Known Blockers

<Only include if something is actually blocked.>
```

```markdown
## Open Questions

<Only include if unresolved questions were explicitly raised.>
```

```markdown
## Important Verbatim

<Short exact quotes when original user wording is a constraint, decision, or doctrine. In --full mode, preserve more.>
```

```markdown
## Files Changed

- `<path>`: <what changed>
```

```markdown
## Files Consulted

- `<path>`: <why it mattered>
```

```markdown
## Suggested Skills

- `<skill>`: <why the next session should use it>
```

Prefer omission over generic filler. Do not invent next actions, blockers, open questions, risks, or decisions just to fill a template.

After writing the file, tell the user the path and give a short summary of what was captured.

## Pickup

Find the relay document the user wants to continue from, read it, and continue the user's task. Do not merely summarise the relay document unless the user asks for a summary.

Selection order:

1. If the user provided an explicit file path, read that file.
2. If the user provided a hint or task description, search likely relay files in `.relay/` and temporary relay locations. Prefer matches by filename first, then by document content.
3. If the user provided no hint, use the newest likely relay document.
4. If multiple candidates are similarly likely, ask one concise clarification question.

Likely relay files include names matching `relay-*.md` and, for compatibility with the original handoff convention, `handoff-*.md`.

When picking up:

- State which relay file you are using.
- Read the relay file before acting.
- Treat any text after `pickup` as the user's next task or focus.
- Continue the work from that context.
- Do not let stale relay content override the user's latest explicit instruction.
