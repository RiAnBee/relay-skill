---
name: relay
user-invocable: true
description: Pass or pick up a lightweight handoff document so a fresh agent can continue the work. Use when ending a session, resuming prior work, or transferring context between coding-agent windows.
argument-hint: "pass|pickup [focus, hint, or next task] [--keep|--persist|--tmp|--temp] [--full|--compact|--brief]"
---

Relay has two actions:

- `pass`: write a handoff document for the next agent.
- `pickup`: find, read, and use a relay document to continue the work.

Relay settings are optional project defaults stored in `.relay/config.json` in the coding agent's startup directory. They only affect where Relay files are written and how much detail is written. If the file does not exist, use these built-in defaults:

```json
{
  "storage": "project",
  "detail": "compact"
}
```

Setting values:

- `storage: "project"`: save new Relay files under `.relay/`.
- `storage: "temp"`: save new Relay files under the system temp directory, `${TMPDIR:-/tmp}`.
- `detail: "compact"`: write the default compact Relay document.
- `detail: "full"`: write the maximum-fidelity Relay document.

Per-command flags override `.relay/config.json` for that invocation only.

If the user did not provide an explicit action, infer the action from context:

- Use `pass` when the current conversation already contains substantial work and the user appears to be ending, saving, or transferring the session.
- Use `pickup` when the user clearly asks to continue, resume, pick up, use the last relay, or provides a prior-task hint or relay path.
- If the current session is fresh and the user only typed `/relay` or phrased the request ambiguously, do not silently auto-pick a relay file just because one exists. Prefer one concise clarification question, or if one candidate is clearly dominant, announce it and ask for confirmation.
- If the current session already contains substantial work and there is no clear continuation signal, use `pass`.

## Pass

Write a handoff document summarising the current conversation so a fresh agent can continue the work.

The relay command invocation itself is not the subject of the handoff. Summarise the real work before the relay command, not the fact that the user ran relay.

Choose the output location in this order:

1. If the user passes `--keep` or `--persist`, save under `.relay/` in the coding agent's startup directory.
2. If the user passes `--tmp` or `--temp`, save under the system temp directory using `mktemp -t relay-<timestamp>-<slug>-XXXXXX.md`.
3. Otherwise, read `.relay/config.json` if it exists and use its `storage` value.
4. If no storage setting exists, save under `.relay/`.

Project-local `.relay/` storage is the preferred default. Temp storage is a compatibility and one-shot option, not the preferred default.

Create `.relay/` if needed before writing project-local files. For temporary files, use `mktemp -t` so the runtime chooses `${TMPDIR:-/tmp}`. When the runtime can control permissions, prefer private relay files and directories such as `0600` for files and `0700` for `.relay/`.

Use this filename shape:

```text
relay-<UTC timestamp>-<semantic slug>-<random suffix>.md
```

Example:

```text
relay-20260511T083012Z-exp3-reward-logging-a1b2c3.md
```

Choose a short semantic slug from the conversation. Prefer 2 to 6 lowercase ASCII words joined by hyphens. The slug should describe the task topic, not the relay action.

Relay should generate only `relay-*.md` files. `handoff-*.md` files are legacy compatibility candidates for pickup only.

If the user clearly asks in natural language to keep the relay in the project, treat it like `--keep`. If the user clearly asks to use a temp file, treat it like `--tmp`.

Natural-language project-storage requests include phrases like "keep this", "persist this", "save it in the project", "put it in the project directory", "long-term save", "don't use a temp file", "长期保存", "放项目里", "保存到目录", or "别放临时文件".

Natural-language temp-storage requests include phrases like "use temp", "temporary file", "put it in tmp", "same as handoff", "放临时目录", "临时文件", or "放到 /tmp".

Suggest the skills to be used, if any, by the next session.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

Before finalizing the relay text, quickly check for obvious secrets, tokens, passwords, private keys, customer data, or other sensitive values. Do not copy them into the relay document. If exact wording matters but contains a sensitive value, redact the value and note that you redacted it.

Choose the detail level in this order:

1. If the user passes `--full`, write a maximum-fidelity relay document.
2. If the user passes `--compact` or `--brief`, write the default compact relay document.
3. Otherwise, read `.relay/config.json` if it exists and use its `detail` value.
4. If no detail setting exists, write the compact relay document.

If the user passes `--full`, or clearly asks for a very detailed handoff in natural language, spend tokens freely. Preserve important original wording verbatim when it affects requirements, constraints, decisions, doctrine, or acceptance criteria. Capture decision rationale, failed routes, useful files consulted, test or validation status, and workspace state when known. `--full` should optimize for maximum relay fidelity, not token efficiency.

Natural-language detailed-mode requests include phrases like "full", "very detailed", "don't save tokens", "preserve the wording", "include the important original text", "超详细", "详细保存", "别省 token", "保留原文", or "重要内容都写进去".

Natural-language compact-mode requests include phrases like "compact", "brief", "short", "concise", "精简", "简短", or "省 token".

The compact relay should still be high-signal. It is not just a shorter summary. Preserve enough state that a fresh agent can continue the work reliably.

Use YAML frontmatter plus Markdown body by default:

```markdown
---
schema_version: 1
created: <ISO 8601 timestamp>
mode: compact | full
storage: project | temp
working_directory: <cwd>
focus: <user-provided focus, if any>
branch: <branch, if known>
commit: <commit, if known>
---

# Relay: <short title>

## Goal

<What the work is trying to achieve. Write this for a zero-context agent.>

## Hard Constraints

- <Requirements the next session must not violate. Quote exact user wording when wording matters.>

## Current State

<Where things stand now. Include only known facts.>

## References

- `<path-or-url>`: <why it matters>
```

Use these exact heading names when the section exists. Do not paraphrase them.

Add these sections when they are actually needed, in this order:

```markdown
## Failed Approaches

- <What was tried, why it failed, and what the next session should avoid repeating.>
```

```markdown
## Settled Decisions

- <Decisions that are already made and should not be casually reopened.>
```

```markdown
## Explicit Next Step

<What the next agent should do first, if clear.>
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

```markdown
## Resume Prompt

<A direct, actionable restart prompt for the fresh agent.>
```

Prefer omission over generic filler. Do not invent next actions, blockers, open questions, risks, or decisions just to fill a template.

In `--full` mode, be much more complete in `Hard Constraints`, `Current State`, `Failed Approaches`, `Settled Decisions`, `Files Changed`, `Files Consulted`, `References`, `Suggested Skills`, and `Resume Prompt`. Preserve more exact wording and rationale when it materially improves the baton pass. Still do not dump full artifacts, full diffs, or large copied text unless the user explicitly wants raw text preserved.

After writing the file, tell the user the path and give a short summary of what was captured.

## Pickup

Find the relay document the user wants to continue from, read it, validate it enough to avoid obvious mistakes, and continue the user's task. Do not merely summarise the relay document unless the user asks for a summary.

Selection order:

1. If the user provided an explicit file path, read that file.
2. If the user provided a hint or task description, build a shallow candidate set from `.relay/` first and the system temp directory second.
3. Prefer `relay-*.md` candidates first and `handoff-*.md` compatibility candidates second.
4. Rank candidates by the strongest available signals in this order: exact path, exact filename or slug match, focus or task-hint match, matching branch or working directory, then newest `created` timestamp or filename timestamp.
5. If multiple candidates are similarly likely, ask one concise clarification question.
6. If the user only invoked bare `/relay` in a fresh or ambiguous session, prefer a short confirmation question over silently loading an old relay.

Candidate discovery must be shallow and bounded:

- Check project-local files under `.relay/` first.
- Check only top-level files in the system temp directory, `${TMPDIR:-/tmp}`, if needed.
- Never recursively scan shared temp roots such as `/tmp` or `$TMPDIR`.
- Never run `rg` over `/tmp`, `$TMPDIR`, or another shared temp root.
- Build filename candidates first, then read only those candidate files.
- Keep the candidate set small and bounded.

Recommended temp discovery command:

```bash
find "${TMPDIR:-/tmp}" -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -print 2>/dev/null
```

Recommended project discovery command:

```bash
find .relay -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -print 2>/dev/null
```

Before acting on a selected relay:

- State which relay file you are using.
- Read the relay file before acting.
- If `schema_version` is present, treat it as the format version. If it is absent, treat the file as a legacy relay or handoff document.
- If the relay records `branch` or `commit` and the current repo state does not match, mention the mismatch briefly.
- If the relay appears stale or key referenced files are missing, warn briefly and continue only if it is still the best candidate or the user confirms.
- Treat any text after `pickup` as the user's next task or focus.
- Do not let stale relay content override the user's latest explicit instruction.

After validation, continue the work from that context.
