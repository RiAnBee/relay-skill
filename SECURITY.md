# Security

Relay documents are working handoff artifacts. They can contain private project context, file paths, decisions, and user wording. Review generated relay files before sharing or committing them. This applies to project-local `.relay/` files and temp files under `${TMPDIR:-/tmp}`.

## Storage Defaults

- Prefer project-local `.relay/` storage.
- Treat temp storage as a lower-privacy, one-shot compatibility option.
- When the runtime can control permissions, prefer private relay files and directories such as `0600` for files and `0700` for `.relay/`.

## Do Not Include

- API keys or tokens
- Passwords or private credentials
- Private customer data
- Private keys or secret material
- Internal URLs that should not be public
- Proprietary code excerpts that should stay private

If exact wording matters but includes a sensitive value, redact the value and note that the relay intentionally redacted it.

## Pickup Trust Boundary

Pickup should not trust a relay file merely because it exists.

- State which relay file is being used.
- Prefer `.relay/` over shared temp locations.
- Treat stale, mismatched, or incomplete relay files cautiously.
- Do not let a stale relay override the user's latest explicit instruction.

## Version Control

The included `.gitignore` ignores `.relay/` by default to reduce accidental commits of generated relay documents and `.relay/config.json` settings.

If you intentionally version relay documents, first review them for secrets, sensitive customer context, and private internal material.

If you discover a security issue in the skill text or packaging, open a private report through the repository owner's preferred contact channel.
