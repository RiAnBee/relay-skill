---
name: relay-set
description: Configure project-local Relay defaults for storage and detail. Use when the user wants Relay to default to .relay or temp, compact or full documents.
---

Configure Relay defaults for the stable project root. Resolve it once using an
explicit root, otherwise the enclosing Git root, otherwise the invocation cwd.
Store settings in `<project-root>/.relay/config.json`.

This skill only changes Relay defaults. It does not change the core pass/pickup handoff behavior in `../relay/SKILL.md`.

Built-in defaults when `.relay/config.json` does not exist:

```json
{
  "storage": "project",
  "detail": "compact"
}
```

Accepted storage words:

- `project`, `.relay`, `keep`, `persist`: set `storage` to `project`.
- `tmp`, `temp`, `/tmp`, `temporary`: set `storage` to `temp`.

Accepted detail words:

- `compact`, `brief`, `short`, `concise`: set `detail` to `compact`.
- `full`, `detailed`, `detail`: set `detail` to `full`.

Common defaults to recommend:

- `/relay-set compact project`: the default high-signal everyday setting.
- `/relay-set full project`: the best default when the team prefers maximum relay fidelity.
- `/relay-set compact temp`: closest to Matt-style disposable handoffs.
- `/relay-set full temp`: detailed but intentionally one-shot.

Examples:

```text
/relay-set full temp
/relay-set compact project
/relay-set tmp
/relay-set full
```

If the user provides both storage and detail words in any order, set both. If
the user provides only one, update only that setting and preserve the other
current setting through the canonical helper.

If the user provides no arguments, or asks to show settings, run the canonical
helper:

```text
python <relay-skill-dir>/scripts/relay_artifact.py config-get \
  --project-root <stable-project-root>
```

It safely reads a bounded regular config without following a final symlink and returns
the built-in defaults when the file is absent. For malformed or unsafe config,
report the error rather than following or repairing the path.

If the user asks to reset settings, pass both built-in defaults to the helper.

When explaining settings to the user:

- `project + compact` means structured everyday Relay with project-local storage.
- `project + full` means maximum-fidelity Relay kept under `.relay/`.
- `temp + compact` means disposable lightweight handoffs.
- `temp + full` means disposable but very detailed handoffs.

When writing settings, locate the canonical helper relative to `../relay/SKILL.md`
and run:

```text
python <relay-skill-dir>/scripts/relay_artifact.py config-set \
  --project-root <stable-project-root> \
  [--storage project|temp] \
  [--detail compact|full]
```

Do not write `.relay/config.json` directly. The helper preserves an unspecified
valid setting, emits compact JSON with exactly these keys, rejects symlinked or
unsafe config paths, and publishes the update with a private file-fsynced atomic
replace:

```json
{"storage":"project","detail":"compact"}
```

Use only these values:

- `storage`: `project` or `temp`
- `detail`: `compact` or `full`

After writing settings, tell the user the effective defaults, config path, and
any directory-fsync or platform ACL warning returned by the helper.
