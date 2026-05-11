# Relay Skill

English | [CN](README.zh-CN.md)

Relay is a lightweight pass/pickup handoff skill for coding agents.

It is based on the spirit and core wording of Matt Pocock's excellent [`handoff`](https://skills.sh/mattpocock/skills/handoff) skill, then extends it with pickup behavior, opt-in persistent storage, semantic filenames, and a detailed mode.

## Why

Matt Pocock's `handoff` skill is great at compacting the current conversation into a handoff document for another agent.

Relay keeps that design lightweight, but adds the missing second half of the workflow:

- `pass`: write a relay document for the next agent.
- `pickup`: find, read, and continue from a relay document.
- Smart `/relay`: infer whether the user is passing or picking up.

This is useful when you work across multiple coding-agent windows, hit context limits, pause a task, or want a fresh session to continue without re-explaining everything.

## Package Layout

Relay uses a core skill plus thin platform adapters:

- `skills/relay/SKILL.md`: canonical Relay behavior.
- `.claude-plugin/plugin.json`: Claude Code plugin metadata.
- `commands/relay.md`: Claude Code slash-command wrapper.
- `adapters/codex/`: Codex prompt-command fallback.
- `adapters/opencode/`: OpenCode skill and command wrappers.

The adapters are intentionally thin. They point back to the canonical Relay skill instead of duplicating product behavior.

## Install: Claude Code

This repository is packaged with three discovery surfaces:

- `.claude-plugin/plugin.json`: registers the skill for plugin-aware installers.
- `commands/relay.md`: exposes a stable `/relay` command wrapper.
- `skills/relay/SKILL.md`: contains the full Relay behavior.

For Claude Code plugin-style installs, install this repository as a plugin so `.claude-plugin/plugin.json` can register the package.

For manual skill installs, copy this directory into your coding agent's skills directory:

```text
skills/relay/
```

For manual slash-command installs, copy this command wrapper into your coding agent's commands directory:

```text
commands/relay.md
```

Different Claude Code versions and installation modes may expose plugin skills as namespaced commands. If you install Relay as a plugin, check both `/relay` and any namespaced Relay entry shown in your slash-command menu.

## Install: Codex

Codex custom prompts are deprecated in favor of skills, but they remain a practical fallback when you want an explicit command-like entrypoint in the Codex CLI.

Copy the Codex prompt adapter to:

```text
~/.codex/prompts/relay.md
```

Then restart Codex or start a new Codex session.

Invoke it as:

```text
/prompts:relay pass
```

See `adapters/codex/README.md` for details.

## Install: OpenCode

OpenCode treats skills and slash commands as separate configuration surfaces.

For skill discovery, copy:

```text
adapters/opencode/skills/relay/
```

to one of:

```text
~/.config/opencode/skills/relay/
.opencode/skills/relay/
```

For an explicit `/relay` command, copy:

```text
adapters/opencode/command/relay.md
```

to one of:

```text
~/.config/opencode/command/relay.md
.opencode/command/relay.md
```

Some OpenCode versions and UIs differ in whether project-local or GUI custom commands are loaded. If `/relay` does not appear, install the command globally and restart OpenCode.

See `adapters/opencode/README.md` for details.

## If `/relay` Does Not Appear

If installation succeeds but `/relay` is not listed, your runtime may not auto-expose skills as slash commands.

Use one of these fixes:

1. Confirm you installed the adapter for your actual agent runtime.
2. Restart the runtime so skills, prompts, or commands are reloaded.
3. For Claude Code, try plugin install or manually copy `commands/relay.md`.
4. For Codex, use `/prompts:relay` rather than plain `/relay` unless your Codex setup maps it differently.
5. For OpenCode, install both the skill and command adapter; if project-local commands do not load, install the command globally.

The command wrappers are intentionally thin. They exist so Relay has stable user-facing entrypoints where each runtime supports them, while `skills/relay/SKILL.md` remains the single canonical behavior definition.

## Usage

Pass the baton:

```text
/relay pass
```

Pass the baton and tell the next session what to focus on:

```text
/relay pass next session should continue experiment 3 and debug reward logging
```

Persist the relay document inside the project instead of using a temporary file:

```text
/relay pass --keep next session should continue experiment 3
```

Write a more detailed relay document:

```text
/relay pass --full preserve the important original wording and decisions
```

Pick up the newest likely relay document:

```text
/relay pickup
```

Pick up a specific thread of work and continue immediately:

```text
/relay pickup continue experiment 3 and debug reward logging
```

Let Relay infer the action:

```text
/relay
```

## Defaults

- Temporary relay files by default.
- Persistent `.relay/` files only when requested with `--keep`, `--persist`, or clear natural language.
- Filename format: `relay-<UTC timestamp>-<semantic slug>-<random suffix>.md`.
- Conditional Markdown sections: omit generic filler instead of inventing next steps, blockers, risks, or open questions.
- Existing artifacts are referenced by path or URL instead of copied.

## Persistent Files And Privacy

Relay documents can contain sensitive project context, private file paths, internal decisions, and user wording.

This repo's `.gitignore` ignores `.relay/` by default so generated relay documents are not accidentally committed. If you intentionally want to version relay documents, remove `.relay/` from `.gitignore` after reviewing the content.

Do not commit secrets, credentials, private tokens, customer data, or sensitive internal information in relay documents.

## Attribution

Relay is inspired by and partially preserves core wording from Matt Pocock's `handoff` skill in [`mattpocock/skills`](https://github.com/mattpocock/skills), licensed under MIT.

See `NOTICE.md` for attribution details.

## License

MIT. See `LICENSE`.
