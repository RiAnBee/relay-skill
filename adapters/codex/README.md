# Relay For Codex

This adapter is documentation only. Relay does not maintain Codex-specific skill copies.

Install the root `skills/` directory into Codex. Codex skills are the primary support path; Relay intentionally avoids custom prompt wrappers so there is only one behavior source.

## Install Skills

From the repository root, copy the Relay skills into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/relay skills/relay-pass skills/relay-pickup ~/.codex/skills/
```

Then restart Codex or start a new Codex session so skills are reloaded.

## Usage

In Codex, invoke:

```text
Use the relay-pass skill
```

or:

```text
Use the relay-pickup skill
```

## Notes

- Keep root `skills/relay*/SKILL.md` as the canonical Relay behavior.
- Codex custom prompts are not shipped because they would create another command surface to maintain.
- If Codex skill routing is unclear, ask naturally: `Use the relay skill to pass this session`.
