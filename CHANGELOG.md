# Changelog

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
