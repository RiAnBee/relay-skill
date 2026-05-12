---
name: relay-set
user-invocable: true
description: Configure project-local Relay defaults for storage and detail. Use when the user wants Relay to default to .relay or temp, compact or full documents.
argument-hint: "[project|keep|persist|tmp|temp] [compact|brief|full] [show|reset]"
---

Configure Relay defaults for the current project. Settings are stored in `.relay/config.json` in the coding agent's startup directory.

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

Examples:

```text
/relay-set full temp
/relay-set compact project
/relay-set tmp
/relay-set full
```

If the user provides both storage and detail words in any order, set both. If the user provides only one, update only that setting and preserve the other current setting.

If the user provides no arguments, or asks to show settings, read `.relay/config.json` if present and report the effective settings. If the file is missing, report the built-in defaults.

If the user asks to reset settings, write the built-in defaults to `.relay/config.json`.

When writing settings:

1. Create `.relay/` if needed.
2. Preserve valid existing settings that were not overridden.
3. Write `.relay/config.json` as compact JSON with exactly these keys:

```json
{"storage":"project","detail":"compact"}
```

Use only these values:

- `storage`: `project` or `temp`
- `detail`: `compact` or `full`

After writing settings, tell the user the effective defaults and the config path.
