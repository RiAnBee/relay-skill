# Relay For OpenCode

This adapter provides OpenCode-native skill and command entrypoints for Relay.

OpenCode treats skills and slash commands as separate configuration surfaces. Install the skill when you want the agent to discover Relay as reusable behavior. Install the command when you want an explicit `/relay` entrypoint in OpenCode TUI/CLI.

## Install Skill

Copy the skill directory into one of OpenCode's skill locations:

```text
~/.config/opencode/skills/relay/
```

or, for a project-local install:

```text
.opencode/skills/relay/
```

The directory must contain:

```text
SKILL.md
```

## Install Command

Copy the command wrapper into your OpenCode command location:

```text
~/.config/opencode/command/relay.md
```

or, for a project-local install if supported by your OpenCode version:

```text
.opencode/command/relay.md
```

Some OpenCode versions and UIs differ in whether project-local or GUI custom commands are loaded. If `/relay` does not appear, install the command globally and restart OpenCode.

## Usage

After installing the command wrapper, invoke:

```text
/relay pass
```

or:

```text
/relay pickup
```

## Notes

- `skills/relay/SKILL.md` remains the canonical Relay behavior.
- `command/relay.md` is only a thin explicit slash-command entrypoint.
- OpenCode TUI/CLI command behavior can differ from GUI behavior in some versions.
