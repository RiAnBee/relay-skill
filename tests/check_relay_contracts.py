from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def headings(markdown: str) -> list[str]:
    return re.findall(r"^##\s+(.+)$", markdown, flags=re.MULTILINE)


def parse_frontmatter(markdown: str) -> dict[str, str]:
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


def require_contains(text: str, needle: str, label: str) -> None:
    require(needle in text, f"{label} missing: {needle}")


def validate_skill_contract() -> None:
    text = read("skills/relay/SKILL.md")
    for needle in [
        "schema_version: 1",
        "## Goal",
        "## Hard Constraints",
        "## Failed Approaches",
        "## Settled Decisions",
        "## Verbatim Doctrine",
        "## Resume Prompt",
        "do not silently auto-pick a relay file",
        "find \"${TMPDIR:-/tmp}\" -maxdepth 1 -type f",
        "handoff-*.md",
    ]:
        require_contains(text, needle, "skills/relay/SKILL.md")


def validate_relay_set_guidance() -> None:
    text = read("skills/relay-set/SKILL.md")
    for needle in [
        "/relay-set compact project",
        "/relay-set full project",
        "/relay-set compact temp",
        "/relay-set full temp",
    ]:
        require_contains(text, needle, "skills/relay-set/SKILL.md")


def validate_readmes() -> None:
    for rel_path, phrases in [
        (
            "README.md",
            [
                "### 3. Compact Template You Can Copy",
                "### 4. Full Template You Can Copy",
                "schema_version: 1",
                "Verbatim Doctrine",
                "python tests/check_relay_contracts.py",
            ],
        ),
        (
            "README.zh-CN.md",
            [
                "### 3. 可直接复制的 compact 模板",
                "### 4. 可直接复制的 full 模板",
                "schema_version: 1",
                "Verbatim Doctrine",
                "python tests/check_relay_contracts.py",
            ],
        ),
    ]:
        text = read(rel_path)
        for phrase in phrases:
            require_contains(text, phrase, rel_path)


def validate_compact_fixture() -> None:
    text = read("tests/fixtures/compact-relay.md")
    fm = parse_frontmatter(text)
    for key in [
        "schema_version",
        "created",
        "mode",
        "storage",
        "working_directory",
        "focus",
    ]:
        require(key in fm, f"compact fixture missing frontmatter key: {key}")
    require(fm["schema_version"] == "1", "compact fixture schema_version must be 1")
    require(fm["mode"] == "compact", "compact fixture mode must be compact")
    for heading in [
        "Goal",
        "Hard Constraints",
        "Current State",
        "Failed Approaches",
        "Settled Decisions",
        "Explicit Next Step",
        "References",
    ]:
        require(heading in headings(text), f"compact fixture missing heading: {heading}")
    require("## Summary" not in text, "compact fixture should use Goal, not Summary")


def validate_full_fixture() -> None:
    text = read("tests/fixtures/full-relay.md")
    fm = parse_frontmatter(text)
    require(fm.get("schema_version") == "1", "full fixture schema_version must be 1")
    require(fm.get("mode") == "full", "full fixture mode must be full")
    for heading in [
        "Goal",
        "Hard Constraints",
        "Current State",
        "Failed Approaches",
        "Settled Decisions",
        "Verbatim Doctrine",
        "Explicit Next Step",
        "Known Blockers",
        "Open Questions",
        "Files Changed",
        "Files Consulted",
        "Suggested Skills",
        "References",
        "Resume Prompt",
    ]:
        require(heading in headings(text), f"full fixture missing heading: {heading}")
    require(
        "The single best first step" in read("README.md"),
        "README.md should describe Explicit Next Step as one best first move",
    )


def validate_legacy_fixture() -> None:
    text = read("tests/fixtures/handoff-legacy-example.md")
    require(not text.startswith("---\n"), "legacy fixture should not have YAML frontmatter")
    for heading in ["Summary", "Current State", "References"]:
        require(heading in headings(text), f"legacy fixture missing heading: {heading}")
    require("Created:" in text, "legacy fixture missing Created field")
    require("Working directory:" in text, "legacy fixture missing Working directory field")


def main() -> int:
    validate_skill_contract()
    validate_relay_set_guidance()
    validate_readmes()
    validate_compact_fixture()
    validate_full_fixture()
    validate_legacy_fixture()
    print("relay contract checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"relay contract check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
