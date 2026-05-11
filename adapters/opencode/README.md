# Relay For OpenCode

This adapter is documentation only. Relay does not maintain OpenCode-specific skill or command copies.

OpenCode treats skills and slash commands as separate configuration surfaces. Install root `skills/` when you want the agent to discover Relay as reusable behavior. Install root `commands/` when you want explicit `/relay` entrypoints in OpenCode TUI/CLI.

## Install Skill

From the repository root, copy the skill directories into OpenCode's global skill location:

```bash
mkdir -p ~/.config/opencode/skills
cp -R skills/relay skills/relay-pass skills/relay-pickup ~/.config/opencode/skills/
```

The directory must contain:

```text
SKILL.md
```

## Install Command

From the repository root, copy the command wrappers into your OpenCode global commands location:

```bash
mkdir -p ~/.config/opencode/commands
cp commands/relay*.md ~/.config/opencode/commands/
```

Some OpenCode versions and UIs differ in whether project-local or GUI custom commands are loaded. Relay's documented OpenCode install path is global config to avoid modifying project-owned `.opencode` directories.

## Expected Global Layout

After install, OpenCode should see this layout:

```text
~/.config/opencode/commands/relay.md
~/.config/opencode/commands/relay-pass.md
~/.config/opencode/commands/relay-pickup.md
~/.config/opencode/skills/relay/SKILL.md
~/.config/opencode/skills/relay-pass/SKILL.md
~/.config/opencode/skills/relay-pickup/SKILL.md
```

Never delete, overwrite, or replace an existing `.opencode` directory to install Relay.

## Usage

After installing the command wrapper, invoke:

```text
/relay
```

or explicit modes:

```text
/relay-pass
/relay-pickup
```

## Notes

- `skills/relay/SKILL.md` remains the canonical smart Relay behavior.
- `skills/relay-pass/SKILL.md` and `skills/relay-pickup/SKILL.md` provide explicit modes.
- `commands/relay*.md` files are thin explicit slash-command entrypoints.
- OpenCode TUI/CLI command behavior can differ from GUI behavior in some versions.
