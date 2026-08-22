from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_contains(text: str, needle: str, label: str) -> None:
    require(needle in text, f"{label} missing: {needle}")


def headings(markdown: str) -> list[str]:
    return re.findall(r"^##\s+(.+)$", markdown, flags=re.MULTILINE)


def parse_legacy_frontmatter(markdown: str) -> dict[str, str]:
    lines = markdown.splitlines()
    require(lines and lines[0] == "---", "missing YAML frontmatter start")
    frontmatter: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            return frontmatter
        require(":" in line, f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    raise AssertionError("missing YAML frontmatter end")


def validate_skill_router() -> None:
    text = read("skills/relay/SKILL.md")
    for needle in [
        "references/handoff-v2.md",
        "references/full-mode.md",
        "references/pickup-protocol.md",
        "scripts/relay_artifact.py",
        "evidence sweep",
        "reverse coverage audit",
        "zero avoidable information gap",
        "relay-<UTC timestamp>-<2-to-6-word-slug>-<digest12>.md",
        "do not silently load a file",
        "at most 20 automatic candidates per location",
        "handoff-*.md",
    ]:
        require_contains(text, needle, "skills/relay/SKILL.md")
    require(len(text.splitlines()) < 500, "canonical SKILL.md should stay below 500 lines")


def validate_v2_reference() -> None:
    text = read("skills/relay/references/handoff-v2.md")
    for needle in [
        "schema_version: 2",
        "relay_id",
        "artifact_sha256",
        "Integrity and Trust",
        "Compact Required Sections",
        "Full Required Sections",
        "Scenario Modules",
        "None known.",
        "Unknown.",
        "Not checked.",
        "continue",
        "review",
        "delegate",
        "blocked",
        "complete",
        "reference",
        "scripts/relay_artifact.py create",
        "scripts/relay_artifact.py validate",
    ]:
        require_contains(text, needle, "handoff-v2.md")
    require_contains(
        text,
        r"^relay-\d{8}T\d{6}Z-[a-z0-9]+(?:-[a-z0-9]+){1,5}-[0-9a-f]{12}\.md$",
        "handoff-v2.md",
    )
    schema = json.loads(read("skills/relay/references/relay-v2.schema.json"))
    require(schema.get("properties", {}).get("schema_version", {}).get("const") == 2, "v2 schema version must be 2")
    for key in ["relay_id", "disposition", "artifact_sha256"]:
        require(key in schema.get("required", []), f"v2 schema missing required field: {key}")
    require(schema.get("additionalProperties") is False, "v2 schema must reject undeclared fields")
    extension = schema.get("patternProperties", {}).get("^x_[a-z0-9_]+$", {})
    require(extension.get("type") == "string", "v2 x_ extensions must be strings")
    require(extension.get("maxLength") == 4096, "v2 x_ extensions must be bounded")


def validate_full_reference() -> None:
    text = read("skills/relay/references/full-mode.md")
    for needle in [
        "Stage A: Evidence Sweep",
        "Stage B: Structured Write",
        "Stage C: Reverse Coverage Audit",
        "User Intent",
        "Live Workspace and Artifacts",
        "Commands, Tools, and Validation",
        "Runtime and External State",
        "Delegated and Parallel Work",
        "Requirement Coverage",
        "Truth and Safety Coverage",
        "Information Density",
        "single-home rule",
        "one primary verb",
        "source_session",
    ]:
        require_contains(text, needle, "full-mode.md")


def validate_pickup_reference() -> None:
    text = read("skills/relay/references/pickup-protocol.md")
    for needle in [
        "Authority and Trust",
        "Bounded Discovery",
        "Deterministic Selection",
        "Workspace Reconciliation",
        "Acceptance Gate",
        "Aligned",
        "Drifted",
        "Orphaned",
        "Invalid",
        "Recency alone",
        "integrity check, not a signature",
    ]:
        require_contains(text, needle, "pickup-protocol.md")


def validate_helper_surface() -> None:
    text = read("skills/relay/scripts/relay_artifact.py")
    for needle in [
        "SCHEMA_VERSION = 2",
        "FILENAME_RE",
        "artifact_sha256",
        "relay_id",
        "write_exclusive_atomic",
        "workspace_snapshot",
        '"create"',
        '"validate"',
        '"snapshot"',
        '"config-set"',
        '"config-get"',
    ]:
        require_contains(text, needle, "relay_artifact.py")


def validate_wrappers() -> None:
    pass_text = read("skills/relay-pass/SKILL.md")
    pickup_text = read("skills/relay-pickup/SKILL.md")
    for needle in [
        "../relay/references/handoff-v2.md",
        "../relay/references/full-mode.md",
        "../relay/scripts/relay_artifact.py",
    ]:
        require_contains(pass_text, needle, "relay-pass/SKILL.md")
    for needle in [
        "../relay/references/pickup-protocol.md",
        "../relay/scripts/relay_artifact.py validate",
        "Aligned, Drifted, Orphaned, or Invalid",
    ]:
        require_contains(pickup_text, needle, "relay-pickup/SKILL.md")


def validate_commands() -> None:
    for name in ["relay", "relay-pass", "relay-pickup", "relay-set"]:
        text = read(f"commands/{name}.md")
        require_contains(text, "locate the installed", f"commands/{name}.md")
        require_contains(text, "Do not assume", f"commands/{name}.md")


def validate_relay_set_guidance() -> None:
    text = read("skills/relay-set/SKILL.md")
    for needle in [
        "/relay-set compact project",
        "/relay-set full project",
        "/relay-set compact temp",
        "/relay-set full temp",
        "config-set",
        "config-get",
        "Do not write `.relay/config.json` directly",
    ]:
        require_contains(text, needle, "skills/relay-set/SKILL.md")


def validate_readmes() -> None:
    shared = [
        "schema_version: 2",
        "relay_id",
        "artifact_sha256",
        "relay-<UTC timestamp>-<2-to-6-word-slug>-<digest12>.md",
        "Evidence sweep",
        "Reverse coverage audit",
        "Aligned",
        "Drifted",
        "Orphaned",
        "Invalid",
        "python tests/check_relay_contracts.py",
        "python -m unittest -v tests/test_relay_artifact.py",
    ]
    english = read("README.md")
    chinese = read("README.zh-CN.md")
    for phrase in shared:
        require_contains(english, phrase, "README.md")
    for phrase in [
        "schema_version: 2",
        "relay_id",
        "artifact_sha256",
        "relay-<UTC timestamp>-<2 到 6 个单词的 slug>-<digest12>.md",
        "Evidence sweep",
        "Reverse coverage audit",
        "Aligned",
        "Drifted",
        "Orphaned",
        "Invalid",
        "python tests/check_relay_contracts.py",
        "python -m unittest -v tests/test_relay_artifact.py",
    ]:
        require_contains(chinese, phrase, "README.zh-CN.md")


def validate_packaging() -> None:
    manifest = json.loads(read(".claude-plugin/plugin.json"))
    require(manifest.get("version") == "0.5.0", "plugin version must be 0.5.0")
    require("verifiable" in manifest.get("description", ""), "plugin description must mention verifiable")
    changelog = read("CHANGELOG.md")
    require_contains(changelog, "## 0.5.0 - 2026-08-19", "CHANGELOG.md")
    require_contains(changelog, "artifact_sha256", "CHANGELOG.md")


def validate_v1_compatibility_fixtures() -> None:
    for rel_path, expected_mode in [
        ("tests/fixtures/compact-relay.md", "compact"),
        ("tests/fixtures/full-relay.md", "full"),
    ]:
        text = read(rel_path)
        fm = parse_legacy_frontmatter(text)
        require(fm.get("schema_version") == "1", f"{rel_path} must remain a v1 fixture")
        require(fm.get("mode") == expected_mode, f"{rel_path} has wrong mode")
        for heading in ["Goal", "Hard Constraints", "Current State", "Explicit Next Step", "References"]:
            require(heading in headings(text), f"{rel_path} missing heading: {heading}")


def validate_v2_body_fixtures() -> None:
    compact = read("tests/fixtures/v2-compact-body.md")
    full = read("tests/fixtures/v2-full-body.md")
    for heading in ["Goal", "Hard Constraints", "Current State", "Explicit Next Step", "References"]:
        require(heading in headings(compact), f"v2 compact body missing heading: {heading}")
    expected_full = [
        "Goal",
        "Hard Constraints",
        "Acceptance Criteria",
        "Progress Ledger",
        "Current State",
        "Settled Decisions",
        "Failed Approaches",
        "Validation",
        "Known Blockers",
        "Open Questions",
        "Explicit Next Step",
        "References",
        "Resume Prompt",
    ]
    actual = headings(full)
    positions = [actual.index(heading) for heading in expected_full]
    require(positions == sorted(positions), "v2 full body headings are out of order")
    for marker in ["Verified / Observed", "Assumptions / Unverified", "None known.", "Not checked"]:
        require_contains(full, marker, "v2-full-body.md")


def validate_legacy_fixture() -> None:
    text = read("tests/fixtures/handoff-legacy-example.md")
    require(not text.startswith("---\n"), "legacy fixture should not have YAML frontmatter")
    for heading in ["Summary", "Current State", "References"]:
        require(heading in headings(text), f"legacy fixture missing heading: {heading}")
    require("Created:" in text, "legacy fixture missing Created field")
    require("Working directory:" in text, "legacy fixture missing Working directory field")


def main() -> int:
    validate_skill_router()
    validate_v2_reference()
    validate_full_reference()
    validate_pickup_reference()
    validate_helper_surface()
    validate_wrappers()
    validate_commands()
    validate_relay_set_guidance()
    validate_readmes()
    validate_packaging()
    validate_v2_body_fixtures()
    validate_v1_compatibility_fixtures()
    validate_legacy_fixture()
    print("relay documentation and packaging contracts passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, json.JSONDecodeError) as exc:
        print(f"relay contract check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
