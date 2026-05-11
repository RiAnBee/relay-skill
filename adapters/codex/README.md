# Relay For Codex

This adapter provides an explicit Codex prompt-command wrapper for Relay.

Codex custom prompts are deprecated in favor of skills, but they remain a practical fallback when you want an explicit slash-command entrypoint in the Codex CLI.

## Install

Copy the prompt wrapper into your Codex prompts directory:

```text
~/.codex/prompts/relay.md
```

Then restart Codex or start a new Codex session so prompts are reloaded.

## Usage

In Codex, invoke:

```text
/prompts:relay pass
```

or:

```text
/prompts:relay pickup
```

Codex may not expose this as plain `/relay`; the documented custom prompt namespace is `/prompts:relay`.

## Notes

- Keep `skills/relay/SKILL.md` as the canonical Relay behavior.
- Use this adapter as a thin explicit entrypoint only.
- If Codex skill/plugin packaging changes, prefer the native Codex skill mechanism over custom prompts.
