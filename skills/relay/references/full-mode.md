# Relay Full Mode Protocol

Read this reference only for `--full` or a clear natural-language request for
maximum-fidelity transfer. Read `handoff-v2.md` first.

## Contents

1. Fidelity target
2. Stage A: evidence sweep
3. Stage B: structured write
4. Stage C: reverse coverage audit
5. Scenario checks
6. Receiver fallback
7. Failure handling

## 1. Fidelity Target

Full mode targets **zero avoidable information gap**, not a literal guarantee
that a summary contains every token from the source session. A source session
may already be compacted, tool output may be truncated, remote state may have
changed, and the outgoing agent may not have access to the raw transcript.

Optimize for successful continuation:

- preserve every load-bearing requirement, decision, rationale, exception,
  measurement, failed route, validation result, and unresolved item;
- give the receiver evidence and source pointers for independent recovery;
- mark missing or uncertain information instead of guessing;
- keep large durable artifacts out of the relay and point to them precisely;
- retain an authorized `source_session` pointer when the runtime supports
  targeted historical queries and the pointer is safe to store.

Full mode is a different capture protocol, not merely a longer compact summary.
Completeness is not repetition. Give each load-bearing fact one canonical home,
use short cross-references elsewhere, and remove prose that does not improve
action, verification, risk recognition, or targeted recovery. There is no fixed
size cap below the artifact limit because task complexity varies, but a full
relay should not grow beyond its evidence merely by restating the same facts.

## 2. Stage A: Evidence Sweep

Do not draft from recent conversational memory alone. Revisit every available
evidence surface before writing.

### A1. User Intent

- Recover the original goal and the user's latest instruction.
- Collect every explicit must, must-not, scope boundary, acceptance criterion,
  priority, numeric limit, ordering requirement, tone/audience requirement, and
  requested deliverable.
- Preserve exact or near-exact wording in `Verbatim Doctrine` only when wording
  carries intent that a paraphrase could weaken.
- Note later user instructions that supersede earlier ones.

### A2. Plans and Task State

- Inspect the current plan/checklist and preserve each item's real status.
- Separate Done, In Progress, Not Started, and Blocked.
- Record why the handoff is happening now.
- Do not turn possible future ideas into required remaining work.

### A3. Live Workspace and Artifacts

When a filesystem or repository is in scope, check the current state rather
than relying on remembered state:

```text
python <relay-skill-dir>/scripts/relay_artifact.py snapshot \
  --project-root <stable project root>
```

- stable project root and actual working directory;
- branch, full HEAD, detached state, worktree identity;
- tracked, untracked, staged, conflicted, and generated files;
- actual diff/stat and files touched during the session;
- referenced specs, plans, ADRs, issues, PRs, datasets, notebooks, reports, or
  generated outputs;
- missing or moved paths.

For a project root nested inside a Git worktree, interpret all helper file lists
as whole-worktree, repository-relative paths. Do not mix nested-relative
untracked paths with repository-relative tracked paths.

If the helper reports `git_evidence_complete: false`, null file lists, or
`workspace_dirty: null`, record Git state as `Unknown`/`Not checked` with the
failed evidence category. Do not treat command failure as an empty list or a
clean worktree.

The cross-runtime helper provides Git file-state evidence. If the harness also
exposes tool-call history, derive read/modified/generated file lists from that
history and reconcile them with Git rather than asking the model to remember.

Do not paste a full diff. Explain the role of each changed artifact and cite the
path, commit, or URL.

### A4. Commands, Tools, and Validation

Recover significant tool actions and their outcomes:

- tests, lint, type checks, builds, benchmarks, previews, screenshots, queries,
  evaluations, and deployment checks;
- exact command or reproducible equivalent;
- pass/fail/not-run state;
- relevant error text, counts, versions, and validation scope;
- whether a result predates the latest edit;
- commands tried that failed and the root cause, when known.

Do not say "tests pass" if only a targeted test ran. Do not say "not tested" if
there is tool evidence of a test result.

### A5. Runtime and External State

Check for state that a fresh session cannot infer from files:

- background processes, servers, ports, terminal/session/cell IDs, log paths;
- cloud jobs, deployments, feature flags, remote branches, issues, PRs,
  messages, drafts, approvals, or other external mutations;
- credentials, permissions, network, sandbox, or human-approval constraints;
- cleanup or rollback obligations.

For irreversible or externally visible actions, distinguish `prepared`,
`applied`, and independently `confirmed`. Record idempotency keys, operation
IDs, receipts, or audit URLs when available so the receiver does not repeat an
already-applied side effect.

Never include a secret value. State where the receiver is expected to obtain an
authorized credential without copying it.

### A6. Decisions, Failures, and Unknowns

- Record settled decisions with their rationale and rejected alternative.
- Record failed approaches that would otherwise be repeated, including the
  evidence that falsified them.
- Separate a failed implementation from a still-valid idea.
- Capture unresolved disagreements and assumptions.
- For every important unknown, provide the smallest verification action.

### A7. Delegated and Parallel Work

If subagents or collaborators participated, reconcile all of them:

- assignment and owner/agent;
- status: queued, running, completed, failed, interrupted, or uncollected;
- source/output path or message;
- evidence quality and any unsupported claims;
- conflicts between results and how they were resolved;
- live agents or sessions that still need to be waited on, interrupted, or
  resumed.

For fork, merge, delegate, or return boundaries, bind each important source by
relationship, relay ID, and artifact digest in `Delegated Work` or `References`.
The core `parent_relay_id` remains the primary linear parent; secondary lineage
does not silently become an automatic execution dependency.

Do not hand off while a required subagent/tool session is silently still
running. If it must remain live, record its exact handle and next control action.

### A8. Source Session and History

When the runtime exposes a safe source-session reference, record it in
frontmatter or `References`. Prefer a targeted query mechanism over dumping a
raw transcript into the handoff. State if the source history was already
compacted or otherwise incomplete.

When known, record that fact as `source_context_state`: `full`, `compacted`,
`partial`, `unavailable`, or `unknown`. This describes what the outgoing agent
could actually inspect, not whether a saved session happens to exist.

## 3. Stage B: Structured Write

Write the required full sections in the order defined by `handoff-v2.md`.

### Resume Brief

The first screen should let the receiver orient immediately:

- `Goal`: desired outcome and why;
- `Hard Constraints`: boundaries that cannot be violated;
- `Acceptance Criteria`: observable definition of done;
- `Progress Ledger`: exact stage of each required outcome.

### Fidelity Record

The middle of the document preserves the trajectory and evidence:

- `Current State`: verified/observed facts followed by assumptions/unverified
  claims when necessary;
- `Settled Decisions`: decision, rationale, rejected alternative, and status;
- `Failed Approaches`: approach, result, root cause or unknown cause, and lesson;
- `Validation`: command/check, result, scope, and freshness;
- required blockers/questions plus applicable scenario modules.

### Action Tail

End with execution-oriented context:

- `Explicit Next Step`: one best first action, not a menu;
- `References`: precise recovery index;
- `Resume Prompt`: direct instruction that repeats the first action and tells
  the receiver which constraints, unknowns, and validations govern it.

Apply a single-home rule while writing:

- expand a requirement once in `Hard Constraints` or `Acceptance Criteria`;
- expand a state fact once in `Current State`, `Progress Ledger`, or its most
  specific scenario module;
- keep `Resume Prompt` to the first action plus only the constraints most likely
  to be violated during that action;
- use criterion IDs or short references instead of copying full sentences;
- do not create a scenario module when it would only duplicate the universal
  core.

For `disposition: complete`, write that no continuation is required and state
what was completed and validated. For `blocked`, make the first action the
smallest unblock/reconciliation step. For `review`, the first action is an
independent check, not more implementation.

`Known Blockers` contains only conditions that prevent the next safe action or
the handoff's acceptance criteria from advancing. Put policy choices and later
branch decisions in `Open Questions` when the receiver can still perform an
independent first action. Write `Explicit Next Step` as one primary verb plus
one target/check; move subsequent actions to the progress ledger or resume
prompt instead of joining them with "then".

## 4. Stage C: Reverse Coverage Audit

After drafting, audit from source evidence back to the relay. Do not audit only
whether the template has headings.

### C1. Requirement Coverage

- Every user deliverable maps to `Acceptance Criteria`.
- Every hard boundary appears in `Hard Constraints` or `Verbatim Doctrine`.
- Superseded requirements are clearly marked and not presented as current.
- Exact values, exclusions, and ordering rules survived.

### C2. State Coverage

- Every acceptance criterion has a Done/In Progress/Not Started/Blocked state.
- Every claimed completion has supporting artifact or validation evidence.
- Current state matches live workspace/remote state as of pass time.
- Dirty/untracked/conflicted work is not hidden.

### C3. Trajectory Coverage

- Every settled decision that affects the receiver includes rationale.
- Every high-value dead end includes why it failed or explicitly says the cause
  is unknown.
- No tentative idea is mislabeled as settled.
- No completed historical task is mixed into remaining work.

### C4. Validation Coverage

- Tests/checks list exact outcome and scope.
- Results that predate later edits are marked stale.
- Unrun checks are `Not checked`, not omitted.
- The receiver can reproduce the next validation from the cited command/path.

### C5. Continuity Coverage

- `Explicit Next Step` is singular, feasible, and consistent with disposition.
- Open questions that affect only later work do not displace an earlier safe,
  independent action.
- The receiver knows which artifact to inspect first.
- Required skills are named exactly and are known to exist; otherwise describe
  capability rather than inventing a skill name.
- Live processes, subagents, and external mutations are either closed or have a
  precise continuation/control action.

### C6. Truth and Safety Coverage

- Load-bearing claims are verified/observed or clearly unverified.
- Unknowns are not silently filled with plausible prose.
- No relay instruction attempts to override current system/developer/user
  authority.
- Secret scan is clean; redactions preserve meaning without values.
- Large copied content is replaced by a precise path/URL/source-session pointer.

### C7. Artifact Coverage

- All required full headings exist and contain facts or explicit absence state.
- Conditional modules cover every applicable scenario and no inapplicable
  module was added for decoration.
- Frontmatter is generated by the helper, not hand-authored.
- Filename timestamp/slug/digest and full artifact digest validate.
- The final path is reported to the user.

### C8. Information Density

- Every material source fact appears, but each is expanded in one canonical
  location rather than repeated across the core, modules, and resume prompt.
- Scenario modules add evidence the universal core does not already carry.
- The relay does not copy durable artifacts or inflate uncertain claims into
  explanatory prose; it uses precise source pointers and verification actions.
- Removing any remaining paragraph would lose a requirement, decision,
  evidence item, risk, recovery pointer, or executable continuation cue.

If any audit item fails, revise the body and finalize a new artifact. Do not edit
the already-finalized v2 file in place because that invalidates its digest.

## 5. Scenario Checks

Use the relevant checks in addition to the universal audit.

### Coding and Git

- File operations are recovered from actual tool/diff state where possible.
- Read-only and modified/generated files are distinguished.
- Symbols, paths, errors, and commands retain exact spelling.
- Worktree/repo mismatches and uncommitted changes are explicit.

### Research

- Primary vs secondary sources are distinguished.
- URLs, source dates, versions/commits, and access dates are preserved.
- Claims are no stronger than the evidence.
- Conflicting sources and evidence gaps remain visible.

### Writing and Review

- Target audience/venue and requested voice remain explicit.
- Accepted, rejected, and unresolved edits/comments are distinguished.
- Claims needing evidence or citation remain marked.

### Data and Experiments

- Dataset/version/split/filter/seed/environment are present where relevant.
- Reported numbers point to real run artifacts and are not invented.
- Failed/incomplete runs and unexecuted ablations remain explicit.

### Deployment and Incident Work

- Environment, time, impact, mutation, approval, owner, and rollback status are
  exact.
- "Prepared" is not confused with "deployed"; "mitigated" is not "resolved".
- Monitoring and the next observation checkpoint are present.

### Multi-Agent Work

- Agent results are evidence, not automatic truth.
- Consensus, contradictions, missing returns, and merge decision are explicit.
- Parent/source IDs allow the receiver to trace important results.

## 6. Receiver Fallback

Maximum-fidelity transfer is strongest when the receiver can recover omitted
detail on demand. When safely available, include one or more of:

- source session ID/path plus a runtime-native targeted query method;
- commit/diff/issue/PR/run/notebook/report path;
- test/build/log artifact;
- previous relay ID for lineage.

Do not assume a source-session pointer is portable across machines or runtimes.
Label its scope and sensitivity. A missing pointer does not invalidate Relay;
it lowers recoverability and must make the written artifact more self-contained.

## 7. Failure Handling

- If a source cannot be revisited, write `Not checked` and explain why.
- If prior context was compacted/truncated, state the limitation.
- If sources conflict, preserve the conflict; do not manufacture consensus.
- If the helper rejects a secret, redact the draft and rerun it.
- If required full sections are missing, add truthful content or explicit
  absence/unknown state; do not downgrade silently to compact.
- If final validation fails, do not present the file as usable.
- If deterministic finalization is unavailable, disclose the degraded integrity
  state and never invent an ID or digest.
