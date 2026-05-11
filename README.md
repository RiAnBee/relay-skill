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

Relay uses one canonical skill set plus thin command entrypoints:

- `skills/relay/SKILL.md`: canonical smart Relay behavior.
- `skills/relay-pass/SKILL.md`: explicit pass-mode behavior.
- `skills/relay-pickup/SKILL.md`: explicit pickup-mode behavior.
- `.claude-plugin/plugin.json`: Claude Code plugin metadata.
- `commands/`: thin slash-command wrappers for runtimes that support command files.
- `adapters/codex/`: Codex installation notes only.
- `adapters/opencode/`: OpenCode installation notes only.

The adapters intentionally do not duplicate skills or commands. Install the same root `skills/` everywhere, and install root `commands/` only where the runtime supports slash-command files.

## Install: Claude Code

This repository is packaged with three discovery surfaces:

- `.claude-plugin/plugin.json`: registers the skill for plugin-aware installers.
- `commands/`: exposes `/relay`, `/relay-pass`, and `/relay-pickup` command wrappers.
- `skills/`: contains the Relay behavior skills.

For Claude Code plugin-style installs, install this repository as a plugin so `.claude-plugin/plugin.json` can register the package.

For manual skill installs, copy the skill directories into your Claude skills directory:

```bash
mkdir -p ~/.claude/skills
cp -R skills/relay skills/relay-pass skills/relay-pickup ~/.claude/skills/
```

For manual slash-command installs, copy command wrappers into your Claude commands directory:

```bash
mkdir -p ~/.claude/commands
cp commands/relay*.md ~/.claude/commands/
```

Different Claude Code versions and installation modes may expose plugin skills as namespaced commands. If you install Relay as a plugin, check both `/relay` and any namespaced Relay entry shown in your slash-command menu.

## Install: Codex

Codex support is important enough to use native Codex skills first. Relay no longer ships Codex-specific skill copies or prompt-command wrappers; the root `skills/` directory is the canonical install source.

Install the Codex skills:

```bash
mkdir -p ~/.codex/skills
cp -R skills/relay skills/relay-pass skills/relay-pickup ~/.codex/skills/
```

Then restart Codex or start a new Codex session. You can trigger these from Codex's skill UI or by asking naturally, for example `Use the relay-pass skill`.

See `adapters/codex/README.md` for details.

## Install: OpenCode

OpenCode treats skills and slash commands as separate configuration surfaces.

Never delete, overwrite, or replace an existing `.opencode` directory to install Relay. Treat `.opencode` as user/project-owned configuration.

For a global install, copy or symlink the root `commands/` and `skills/` entries into your OpenCode config:

```bash
mkdir -p ~/.config/opencode/commands ~/.config/opencode/skills
ln -s /path/to/relay-skill/commands/relay.md ~/.config/opencode/commands/relay.md
ln -s /path/to/relay-skill/commands/relay-pass.md ~/.config/opencode/commands/relay-pass.md
ln -s /path/to/relay-skill/commands/relay-pickup.md ~/.config/opencode/commands/relay-pickup.md
ln -s /path/to/relay-skill/skills/relay ~/.config/opencode/skills/relay
ln -s /path/to/relay-skill/skills/relay-pass ~/.config/opencode/skills/relay-pass
ln -s /path/to/relay-skill/skills/relay-pickup ~/.config/opencode/skills/relay-pickup
```

Some OpenCode versions and UIs differ in whether project-local or GUI custom commands are loaded. Relay's documented OpenCode install path is global config to avoid modifying project-owned `.opencode` directories.

See `adapters/opencode/README.md` for details.

## If `/relay` Does Not Appear

If installation succeeds but `/relay` is not listed, your runtime may not auto-expose skills as slash commands.

Use one of these fixes:

1. Confirm you installed the root `skills/` and, where supported, root `commands/` for your actual agent runtime.
2. Restart the runtime so skills, prompts, or commands are reloaded.
3. For Claude Code, try plugin install or manually copy all `commands/relay*.md` and `skills/relay*/` entries.
4. For Codex, install the root `skills/relay*/` directories and trigger them from the skill UI or natural language.
5. For OpenCode, install root `skills/relay*/` and root `commands/relay*.md` under global `~/.config/opencode/`.

The command wrappers are intentionally thin. They exist so Relay has stable user-facing entrypoints where each runtime supports them, while `skills/relay/SKILL.md` remains the single canonical behavior definition.

## Usage

Smart mode, infer whether to pass or pickup:

```text
/relay
```

Pass the baton without typing a subcommand:

```text
/relay-pass
```

Pass the baton and tell the next session what to focus on:

```text
/relay-pass next session should continue experiment 3 and debug reward logging
```

Persist the relay document inside the project instead of using a temporary file:

```text
/relay-pass --keep next session should continue experiment 3
```

Write a more detailed relay document:

```text
/relay-pass --full preserve the important original wording and decisions
```

Pick up the newest likely relay document:

```text
/relay-pickup
```

Pick up a specific thread of work and continue immediately:

```text
/relay-pickup continue experiment 3 and debug reward logging
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
