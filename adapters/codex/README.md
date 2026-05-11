# Relay For Codex

This adapter provides Codex-native Relay skills plus optional custom prompt wrappers.

Codex custom prompts are deprecated in favor of skills, so install skills first. Prompt wrappers remain a practical fallback when you want an explicit slash-command entrypoint in the Codex CLI.

## Install Skills

Copy the Relay skills into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/relay skills/relay-pass skills/relay-pickup ~/.codex/skills/
```

Then restart Codex or start a new Codex session so skills are reloaded.

## Optional Prompt Fallback

Copy prompt wrappers into your Codex prompts directory:

```bash
mkdir -p ~/.codex/prompts
cp prompts/relay*.md ~/.codex/prompts/
```

Then restart Codex or start a new Codex session so prompts are reloaded.

## Usage

In Codex, invoke:

```text
Use the relay-pass skill
```

or:

```text
Use the relay-pickup skill
```

If using prompt fallback, invoke `/prompts:relay`, `/prompts:relay-pass`, or `/prompts:relay-pickup`.

## Notes

- Keep root `skills/relay*/SKILL.md` as the canonical Relay behavior.
- Prefer Codex skills over custom prompts.
- Use prompt wrappers as thin explicit entrypoints only.
