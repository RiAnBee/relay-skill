# Relay For Codex

This adapter is documentation only. Relay does not maintain Codex-specific skill copies.

Install the root `skills/` directory into Codex. Codex skills are the primary support path; Relay intentionally avoids custom prompt wrappers so there is only one behavior source.

## Install Skills

From the repository root, copy the Relay skills into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skills/relay skills/relay-pass skills/relay-pickup skills/relay-set ~/.codex/skills/
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

or configure defaults naturally:

```text
Use the relay-set skill with full temp
```

Behavior notes:

- Relay now prefers project-local `.relay/` storage by default.
- The default relay document is compact but structured for reliable pickup.
- New passes use the bundled Python helper for schema-v2 artifact IDs, filename digests, atomic
  private writes, Git snapshots, and pickup validation. Install the whole
  `skills/relay/` directory, not only `SKILL.md`.
- `--full` runs evidence sweep, structured write, and reverse coverage audit;
  it is not merely a longer summary.
- In a fresh ambiguous session, smart Relay should prefer a short clarification over silently loading an old handoff.
- Within one coherent Codex chat, use native resume/compact/fork when that
  preserves the desired history; use Relay for portable or inspectable transfer.

## Notes

- Keep root `skills/relay*/SKILL.md` as the canonical Relay behavior.
- Codex custom prompts are not shipped because they would create another command surface to maintain.
- If Codex skill routing is unclear, ask naturally: `Use the relay skill to pass this session`.
