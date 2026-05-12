# Security

Relay documents may contain private project context. Review generated relay files before sharing or committing them. This applies to project-local `.relay/` files and temp files under `${TMPDIR:-/tmp}`.

Do not include:

- API keys or tokens
- Passwords or private credentials
- Private customer data
- Internal URLs that should not be public
- Proprietary code excerpts that should stay private

The included `.gitignore` ignores `.relay/` by default to reduce accidental commits of generated relay documents and `.relay/config.json` settings.

If you discover a security issue in the skill text or packaging, open a private report through the repository owner's preferred contact channel.
