# Changelog

## 0.3.0 - 2026-05-12

- Add `/relay-set` and `relay-set` for project-local Relay default settings.
- Change the built-in storage default from temp files to project-local `.relay/` files.
- Add `--tmp` and `--temp` one-shot temporary storage overrides.
- Add `--compact` and `--brief` one-shot compact-detail overrides alongside `--full`.
- Keep Matt-compatible `handoff-*.md` pickup candidates while continuing to generate only `relay-*.md` files.
- Fix temp pickup discovery guidance by requiring shallow top-level `find -maxdepth 1` checks instead of recursive temp scans.

## 0.2.0 - 2026-05-12

- Simplify the cross-agent package around one canonical root `skills/` directory.
- Remove Codex-specific and OpenCode-specific duplicate skill, command, and prompt copies from `adapters/`.
- Keep `commands/relay*.md` as thin explicit slash-command entrypoints for runtimes that support command files.
- Convert `adapters/codex/` and `adapters/opencode/` into documentation-only platform install notes.
- Update English and Chinese docs to make root `skills/` the only behavior source.

## 0.1.4 - 2026-05-12

- Add explicit `/relay-pass` and `/relay-pickup` command wrappers alongside smart `/relay`.
- Add `relay-pass` and `relay-pickup` skills for Claude Code-compatible direct skill invocation.
- Add Codex-native `relay`, `relay-pass`, and `relay-pickup` skill adapters under `adapters/codex/skills/`.
- Add Codex prompt fallback wrappers for `/prompts:relay-pass` and `/prompts:relay-pickup`.
- Add OpenCode command and skill adapters for all three Relay entrypoints.
- Remove guidance that suggests cloning over or replacing `.opencode`; `.opencode` must be treated as user/project-owned configuration.

## 0.1.3 - 2026-05-12

- Fix OpenCode adapter paths from `command/` to the expected `commands/` directory.
- Document the project-local `.opencode/commands/` and `.opencode/skills/` layout used by popular OpenCode skill repositories.
- Mark Relay skills as `user-invocable: true` to align with direct slash-style skill invocation in runtimes that support it.

## 0.1.2 - 2026-05-12

- Add a cross-agent `adapters/` layout for Codex and OpenCode.
- Add a Codex prompt-command fallback adapter at `adapters/codex/prompts/relay.md`.
- Add OpenCode skill and command adapters under `adapters/opencode/`.
- Update English and Chinese docs to explain platform-specific install paths and avoid promising one universal `/relay` command everywhere.

## 0.1.1 - 2026-05-12

- Add `.claude-plugin/plugin.json` so plugin-aware runtimes can discover the Relay skill.
- Add `commands/relay.md` as a thin `/relay` command wrapper for more reliable slash-command visibility.
- Document fallback steps for runtimes where `/relay` does not appear automatically.

## 0.1.0 - 2026-05-11

- Initial open-source draft.
- Add `relay` skill with `pass`, `pickup`, and smart default behavior.
- Add temporary-file default with opt-in `.relay/` persistence.
- Add semantic timestamped relay filenames.
- Add `--full` detailed handoff mode.
- Add attribution to Matt Pocock's MIT-licensed `handoff` skill.
