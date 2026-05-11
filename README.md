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

## Install

This repository is packaged with three discovery surfaces:

- `.claude-plugin/plugin.json`: registers the skill for plugin-aware installers.
- `commands/relay.md`: exposes a stable `/relay` command wrapper.
- `skills/relay/SKILL.md`: contains the full Relay behavior.

For Claude Code plugin-style installs, install this repository as a plugin so `.claude-plugin/plugin.json` can register `skills/`.

For manual skill installs, copy this directory into your coding agent's skills directory:

```text
skills/relay/
```

For manual slash-command installs, copy this command wrapper into your coding agent's commands directory:

```text
commands/relay.md
```

Different coding agents use different plugin, skill, and command locations. If your tool expects a different directory layout, copy `skills/relay/SKILL.md` and `commands/relay.md` into the equivalent locations for that tool.

## If `/relay` Does Not Appear

If installation succeeds but `/relay` is not listed, your runtime may not auto-expose skills as slash commands.

Use one of these fixes:

1. Install the repository as a Claude Code plugin so `.claude-plugin/plugin.json` is discovered.
2. Manually copy `commands/relay.md` into your commands directory.
3. Manually copy `skills/relay/` into your skills directory, then restart the agent runtime.

The command wrapper is intentionally thin. It exists so `/relay` has a stable user-facing entrypoint even when skill discovery behavior differs across runtimes.

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
