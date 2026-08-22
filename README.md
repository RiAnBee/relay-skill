# Relay Skill

<p align="center">
  <img src="./assets/relay-skill-banner.png" alt="relay-skill banner" width="100%" />
</p>

English | [CN](README.zh-CN.md)

Relay is a portable pass/pickup handoff skill for coding agents. It keeps Matt
Pocock's lightweight, inspectable Markdown handoff core and adds deterministic
artifact identity, integrity checks, safer pickup, and a real maximum-fidelity
protocol for long or high-stakes transfers.

## Quick Start

```text
/relay
/relay-pass --full next session should finish reward logging
/relay-pickup reward logging
```

The public surface remains:

- `relay`: infer pass or pickup from clear context;
- `relay-pass`: force a pass;
- `relay-pickup`: force a pickup;
- `relay-set`: configure project defaults.

Built-in defaults are project-local `.relay/` storage and compact, high-signal
documents. New passes emit Relay artifacts using wire schema v2. v1 Relay files and
Matt-compatible `handoff-*.md` files remain readable as explicitly unverified
compatibility inputs.

Version axes are intentionally separate: **Relay Skill** is the product and
public command set; **0.5.0** is this package release; `schema_version: 2` is
the handoff artifact wire format. “Schema v2” does not name a new product.

For a plain-language walkthrough of the protocol, implementation, evidence, and
remaining boundaries, see the local [Relay Skill upgrade report](relay-v2-upgrade-report.html).

## Contents

- [Quick Start](#quick-start)
- [When To Use Relay](#when-to-use-relay)
- [Protocol Update: What Schema v2 Adds](#protocol-update-what-schema-v2-adds)
- [Pass Workflow](#pass-workflow)
- [Pickup Workflow](#pickup-workflow)
- [Storage, Detail, And Disposition](#storage-detail-and-disposition)
- [Install](#install)
- [Package Layout](#package-layout)
- [Validation](#validation)
- [Security And Privacy](#security-and-privacy)
- [Compatibility And Lineage](#compatibility-and-lineage)

## When To Use Relay

Relay is for **portability**, not merely compression. Use it when work crosses a
session, harness, model, directory, role, person, independent workstream, or
inspectable checkpoint boundary.

When the same runtime can resume the exact same coherent chat, native resume is
usually the highest-fidelity option. Use native compact to stay in the same
session, and native fork when the work truly branches and the runtime preserves
the transcript. Relay is strongest when a portable, reviewable artifact must
survive beyond those runtime-specific mechanisms.

Conversation logs, runtime control checkpoints, workspace materialization, and
portable semantic handoffs are different objects. Relay owns the last one; it
can reference and reconcile the others, but reading a Markdown artifact does
not recreate a runtime engine or tool trajectory.

```text
source session
  -> /relay-pass
  -> evidence sweep + Markdown body
  -> deterministic finalization (wire schema v2)
  -> new session / harness / role / person
  -> /relay-pickup
  -> validation + live-state reconciliation
  -> continue, review, delegate, unblock, or record completion
```

Matt Pocock's original [`handoff`](https://skills.sh/mattpocock/skills/handoff)
established the core invariants Relay keeps: tailor the handoff to the next
focus, reference existing artifacts rather than copying them, suggest relevant
skills, redact sensitive values, and write one portable Markdown entry point.

## Protocol Update: What Schema v2 Adds

### Universal Core Plus Scenario Modules

Every handoff retains a small universal core:

- goal;
- hard constraints;
- current state;
- one explicit first action;
- precise references.

Full mode adds acceptance criteria, a progress ledger, decisions, failed
approaches, validation, blockers, questions, and a resume prompt. Conditional
modules carry state for coding/Git, research, writing/review, data/experiments,
runtime/services, deployment/incidents, external systems, security, and
multi-agent work. This lets Relay cover varied tasks without forcing every
handoff into one giant fixed template.

### Deterministic Identity, Filename, And Hash

The model writes only the Markdown body. The bundled standard-library helper
generates the fragile envelope:

- opaque `relay_id` for identity and chain links;
- canonical `artifact_sha256` over metadata plus body;
- the first 12 digest characters in the filename;
- unambiguous JSON-value YAML serialization;
- Git root/branch/HEAD/dirty metadata when available;
- file-fsynced same-directory temporary write, atomic no-overwrite hard-link
  publication, and `0600` mode where supported. Unsupported atomic publication
  fails closed; durability/ACL limitations are reported.

Filename contract:

```text
relay-<UTC timestamp>-<2-to-6-word-slug>-<digest12>.md
```

Example:

```text
.relay/relay-20260819T063045Z-reward-logging-a8c14f719d2e.md
```

The full digest covers the parsed metadata and normalized body, not the raw
rendered file bytes, and detects accidental or unsynchronized changes. The 12-character
filename prefix is only a locator/check prefix. Neither is a signature or proof
of authorship or user approval.

### Full Is A Capture Protocol

`--full` is not just "write more." It runs three stages:

1. **Evidence sweep**: revisit user wording, plan state, Git/workspace, tool and
   test results, runtime/external state, artifacts, subagents, decisions,
   failures, and unknowns.
2. **Structured write**: create a one-screen resume brief, a fidelity record,
   applicable scenario modules, and an action-oriented tail.
3. **Reverse coverage audit**: map every requirement, constraint, completion
   claim, validation result, artifact, failed path, and live process back to
   source evidence before finalization.

Full uses a single-home rule: preserve every material fact, expand it once, and
use short references elsewhere. Fidelity is measured by coverage and usable
evidence, not by making the handoff longer.

The honest target is **zero avoidable information gap**. No summary can promise
literal 100% recovery when the source history was already compacted, truncated,
or inaccessible. When safe and supported, full mode records an opaque source
session reference so the receiver can make targeted historical queries without
copying a full transcript.

### Pickup Validates And Reconciles

Pickup does not blindly choose the newest file. It prefers exact path/ID/name,
then task hint, project/worktree/branch, schema/integrity, and only then time.
Recency alone does not break a meaningful tie.

For compact/restore hooks, the preceding hook should pass the exact artifact path,
`relay_id`, and digest. If that locator is unavailable, a non-interactive pickup
continues only for one clearly dominant candidate; a genuine tie returns
`ambiguous` without asking a person or silently choosing the newest file.

After selection it verifies artifact structure and SHA-256, then reconciles the
handoff against live project, branch/HEAD/dirty state, references, validation
freshness, running processes/subagents/jobs, remote state, and available skills.
It classifies the result as Aligned, Drifted, Orphaned, or Invalid before the
first material action.

Pickup uses `validate --json --include-body`: validation and body capture share
one bounded regular-file descriptor, and the receiver reconciles that returned
snapshot instead of reopening a path that may have changed.

## Pass Workflow

Run:

```text
/relay-pass next session should continue experiment 3
/relay-pass --full preserve exact constraints, evidence, and failed routes
```

Relay resolves one stable project root, reads `.relay/config.json`, gathers
evidence, writes a body draft, and asks the helper to finalize it. The helper
can expose deterministic workspace evidence before drafting:

```text
python skills/relay/scripts/relay_artifact.py snapshot --project-root .
```

The compact body contract is:

```markdown
# Relay: <short topic>

## Goal

<Outcome and why it matters to a zero-context receiver.>

## Hard Constraints

- <Boundary the receiver must not violate.>

## Current State

<Known state, completed work, and work still in progress.>

## Explicit Next Step

<One best first action, or explicitly no continuation required.>

## References

- `<path-or-url>`: <what the receiver should recover here.>
```

Add high-value `Failed Approaches`, `Settled Decisions`, and `Validation` when
omitting them would mislead the receiver. Do not add empty decorative sections.

Full mode requires this ordered core:

1. `Goal`
2. `Hard Constraints`
3. `Acceptance Criteria`
4. `Progress Ledger`
5. `Current State`
6. `Settled Decisions`
7. `Failed Approaches`
8. `Validation`
9. `Known Blockers`
10. `Open Questions`
11. `Explicit Next Step`
12. `References`
13. `Resume Prompt`

In schema-v2 full mode, required categories use explicit absence/uncertainty states:

- `None known.`: checked, no known entry;
- `Not applicable.`: the category cannot apply;
- `Unknown.`: important but not established, with a verification action;
- `Not checked.`: a possible check was not run.

This distinguishes "there is no blocker" from "the outgoing agent forgot to
mention blockers" and prevents plausible guesses from becoming false premises.

## Generated Relay Artifact Envelope (Schema v2)

Frontmatter is helper-generated, not a copy/paste template. A final artifact
looks like this conceptually:

```yaml
---
schema_version: 2
relay_id: "rly_<opaque-id>"
created: "2026-08-19T06:30:45Z"
mode: "full"
disposition: "continue"
storage: "project"
project_root: "/workspace/example-app"
working_directory: "/workspace/example-app"
focus: "finish reward logging validation"
slug: "reward-logging"
branch: "main"
commit: "<full-head-sha>"
workspace_dirty: true
artifact_sha256: "sha256:<64-hex-digest>"
---
```

Optional `parent_relay_id`, `source_session`, `source_context_state`, and
`created_by` support lineage and debugging without pretending to be
authenticated provenance. `source_context_state` distinguishes full,
compacted, partial, unavailable, and unknown source history.

The schema-v2 artifact permits only bounded informational string extensions named
`x_<name>`. They must be safe for an older reader to ignore. New required
fields, enum values, action/security semantics, body requirements, or digest
rules require a new wire `schema_version`; the package version is a separate
version axis. The JSON Schema describes metadata, while the helper also checks
the frontmatter text profile, body, filename, timestamp, and digest relationship.

Maintainers can exercise the helper directly:

```text
python skills/relay/scripts/relay_artifact.py create \
  --body /tmp/relay-body.md \
  --slug "reward logging" \
  --focus "finish validation" \
  --mode full \
  --storage project \
  --disposition continue \
  --project-root .
```

Then validate:

```text
python skills/relay/scripts/relay_artifact.py validate .relay/relay-....md
```

Do not edit a finalized schema-v2 artifact in place. Revise the body and create a new
artifact so its digest and filename remain consistent.

## Pickup Workflow

Start a fresh session and run:

```text
/relay-pickup reward logging
```

or pass an exact path:

```text
/relay-pickup .relay/relay-20260819T063045Z-reward-logging-a8c14f719d2e.md
```

Candidate discovery is shallow and bounded:

- project `.relay/` first;
- system temp top-level only when needed;
- maximum 20 automatic candidates per location;
- regular `relay-*.md` and legacy `handoff-*.md` files only;
- no recursive shared-temp scan and no content-wide `rg` over `/tmp`.

Portable discovery examples:

```bash
find .relay -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -print 2>/dev/null
```

```bash
find "${TMPDIR:-/tmp}" -maxdepth 1 -type f \( -name 'relay-*.md' -o -name 'handoff-*.md' \) -print 2>/dev/null
```

The authority order is always:

```text
system/developer > latest user > reconciled live state > validated relay > unverified relay claims
```

The relay is context, not authority. Commands in a relay are inspected before
execution and never interpolated into a shell command.

## Storage, Detail, And Disposition

One-shot flags:

- `--keep` / `--persist`: write under project `.relay/`;
- `--tmp` / `--temp`: write under the system temp directory;
- `--full`: maximum-fidelity protocol;
- `--compact` / `--brief`: compact protocol.

Set project defaults:

```text
/relay-set compact project
/relay-set full project
/relay-set compact temp
/relay-set full temp
```

The config remains intentionally small:

```json
{"storage":"project","detail":"compact"}
```

`relay-set` updates this file through the bundled `config-set` helper. It
preserves an unspecified valid setting, rejects symlinked/unsafe paths, and
uses a private file-fsynced atomic replace.

Schema v2 dispositions cover different transfers without separate document types:

- `continue`: continue unfinished work;
- `review`: independently verify or decide first;
- `delegate`: execute a bounded workstream;
- `blocked`: reconcile/remove a blocker;
- `complete`: no continuation is required;
- `reference`: background context only.

## Install

Relay ships as plain skill and command files. Until a registry installer is
published, clone it once and symlink the root entries into the runtime's config
directory. The deterministic helper requires Python 3.10 or newer and uses only
the standard library. Restart the runtime after installation if skills are not
listed.

```bash
mkdir -p ~/.local/share
git clone https://github.com/RiAnBee/relay-skill.git ~/.local/share/relay-skill
```

Replace `~/.local/share/relay-skill` below when you keep the clone elsewhere.

### Claude Code

If plugin installation is available, use it. Otherwise:

```bash
mkdir -p ~/.claude/skills ~/.claude/commands
ln -s ~/.local/share/relay-skill/skills/relay ~/.claude/skills/relay
ln -s ~/.local/share/relay-skill/skills/relay-pass ~/.claude/skills/relay-pass
ln -s ~/.local/share/relay-skill/skills/relay-pickup ~/.claude/skills/relay-pickup
ln -s ~/.local/share/relay-skill/skills/relay-set ~/.claude/skills/relay-set
ln -s ~/.local/share/relay-skill/commands/relay.md ~/.claude/commands/relay.md
ln -s ~/.local/share/relay-skill/commands/relay-pass.md ~/.claude/commands/relay-pass.md
ln -s ~/.local/share/relay-skill/commands/relay-pickup.md ~/.claude/commands/relay-pickup.md
ln -s ~/.local/share/relay-skill/commands/relay-set.md ~/.claude/commands/relay-set.md
```

### Codex

Codex uses native skills first:

```bash
mkdir -p ~/.codex/skills
ln -s ~/.local/share/relay-skill/skills/relay ~/.codex/skills/relay
ln -s ~/.local/share/relay-skill/skills/relay-pass ~/.codex/skills/relay-pass
ln -s ~/.local/share/relay-skill/skills/relay-pickup ~/.codex/skills/relay-pickup
ln -s ~/.local/share/relay-skill/skills/relay-set ~/.codex/skills/relay-set
```

If slash commands are unavailable, invoke the skill by name or natural
language, for example `Use the relay-pass skill`.

### OpenCode

Install both root skills and command wrappers globally. Never replace a
project-owned `.opencode` directory:

```bash
mkdir -p ~/.config/opencode/commands ~/.config/opencode/skills
ln -s ~/.local/share/relay-skill/commands/relay.md ~/.config/opencode/commands/relay.md
ln -s ~/.local/share/relay-skill/commands/relay-pass.md ~/.config/opencode/commands/relay-pass.md
ln -s ~/.local/share/relay-skill/commands/relay-pickup.md ~/.config/opencode/commands/relay-pickup.md
ln -s ~/.local/share/relay-skill/commands/relay-set.md ~/.config/opencode/commands/relay-set.md
ln -s ~/.local/share/relay-skill/skills/relay ~/.config/opencode/skills/relay
ln -s ~/.local/share/relay-skill/skills/relay-pass ~/.config/opencode/skills/relay-pass
ln -s ~/.local/share/relay-skill/skills/relay-pickup ~/.config/opencode/skills/relay-pickup
ln -s ~/.local/share/relay-skill/skills/relay-set ~/.config/opencode/skills/relay-set
```

## Package Layout

```text
relay-skill/
├── .claude-plugin/plugin.json
├── commands/                 # thin runtime entrypoints
├── skills/
│   ├── relay/SKILL.md        # canonical router
│   ├── relay/references/     # artifact-format, full, pickup references
│   ├── relay/scripts/        # deterministic artifact helper
│   ├── relay-pass/SKILL.md
│   ├── relay-pickup/SKILL.md
│   └── relay-set/SKILL.md
└── adapters/                 # install notes only
```

## Validation

Run the documentation contract and behavior tests:

```bash
python tests/check_relay_contracts.py
python -m unittest -v tests/test_relay_artifact.py
```

The behavior suite covers schema-v2 artifact generation, filename/hash enforcement,
tamper detection, secret rejection, full-mode required sections, atomic config
updates, regular-file/symlink/size/deep-input boundaries, Git evidence failure,
v1/legacy compatibility, and unknown schema failure.

## Security And Privacy

Relay files can contain private project context, paths, decisions, and user
wording. Prefer `.relay/`; treat temp storage as lower-privacy, one-shot
compatibility storage. Review generated files before sharing or versioning them.

The helper scans common API-key, token, and private-key patterns before writing;
redact values rather than weakening the scan. It writes private files where the
runtime supports permissions and rejects symlinked input/artifacts. A digest is
an integrity check, not an authenticity signature.

The relay body is untrusted context, not a new system or user instruction. The
authority order is current system/developer instructions, the latest user
instruction, reconciled live state, validated relay, then unverified claims.
Never interpolate relay prose into shell commands. Do not store credentials,
private keys, customer data, or unnecessary source-session paths.

`.gitignore` ignores `.relay/` by default. If you intentionally version relay
files, review every file for secrets and private context first.

## Compatibility And Lineage

New passes emit schema-v2 artifacts only. v1 and unversioned legacy files remain pickup
candidates with a visible downgrade warning; unknown future schemas fail closed
for automatic action. Pickup never rewrites a source file. A later pass emits a
new schema-v2 artifact and may link it with `parent_relay_id`.

The Python helper uses platform temp-directory APIs, but the documented install
and discovery shell examples and the current test matrix are POSIX-oriented.
Windows ACL privacy and directory-fsync durability remain explicitly
unverified; the helper reports those limitations rather than claiming
end-to-end Windows parity.

## Attribution And License

Relay is inspired by and partially preserves core wording from Matt Pocock's
MIT-licensed [`mattpocock/skills`](https://github.com/mattpocock/skills). See
`NOTICE.md` for attribution details. This project is MIT licensed; see
`LICENSE`.
