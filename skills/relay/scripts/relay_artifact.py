#!/usr/bin/env python3
"""Create and validate Relay Skill handoff artifacts using wire schema v2.

The LLM writes the Markdown body. This helper owns the fragile mechanics:
metadata serialization, IDs, hashing, filenames, permissions, and atomic writes.
It intentionally uses only the Python standard library.
"""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import stat as stat_module
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback is explicitly unverified.
    fcntl = None


SCHEMA_VERSION = 2
MAX_ARTIFACT_BYTES = 2 * 1024 * 1024
MAX_CONFIG_BYTES = 64 * 1024
MAX_JSON_NESTING = 32
MAX_SECRET_FINDINGS = 50
FILENAME_RE = re.compile(
    r"^relay-(?P<timestamp>\d{8}T\d{6}Z)-"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+){1,5})-"
    r"(?P<digest>[0-9a-f]{12})\.md$"
)
KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
EXTENSION_KEY_RE = re.compile(r"^x_[a-z0-9_]+$")
ASCII_OUTER_WHITESPACE = " \t\n\f\v"
RESERVED_SLUG_WORDS = {"relay", "handoff", "pass", "pickup"}
CORE_HEADINGS = [
    "Goal",
    "Hard Constraints",
    "Current State",
    "Explicit Next Step",
    "References",
]
LEGACY_CORE_HEADINGS = [
    "Goal",
    "Hard Constraints",
    "Current State",
    "References",
]
FULL_HEADINGS = [
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
DISPOSITIONS = (
    "continue",
    "review",
    "delegate",
    "blocked",
    "complete",
    "reference",
)
SOURCE_CONTEXT_STATES = ("full", "compacted", "partial", "unavailable", "unknown")
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----"),
    "OpenAI-style API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
}
METADATA_ORDER = [
    "schema_version",
    "relay_id",
    "created",
    "mode",
    "disposition",
    "storage",
    "project_root",
    "working_directory",
    "focus",
    "slug",
    "branch",
    "commit",
    "workspace_dirty",
    "parent_relay_id",
    "source_session",
    "source_context_state",
    "created_by",
    "artifact_sha256",
]
CORE_METADATA_KEYS = frozenset(METADATA_ORDER)


class RelayError(Exception):
    """A user-correctable Relay artifact error."""


def resolve_path(value: str | Path, label: str) -> Path:
    """Resolve a user/runtime path without leaking platform exceptions."""
    try:
        return Path(value).expanduser().resolve()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise RelayError(f"cannot resolve {label} path {value!s}: {exc}") from exc


def read_regular_file(
    path: Path,
    label: str,
    max_bytes: int,
) -> tuple[bytes, os.stat_result]:
    """Read one stable, bounded regular file without following a final symlink."""
    try:
        before = path.lstat()
    except OSError as exc:
        raise RelayError(f"cannot read {label}: {path}: {exc}") from exc
    if stat_module.S_ISLNK(before.st_mode):
        raise RelayError(f"{label} path is a symbolic link")
    if not stat_module.S_ISREG(before.st_mode):
        raise RelayError(f"{label} path is not a regular file")
    if before.st_size > max_bytes:
        raise RelayError(f"{label} exceeds {max_bytes} bytes")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise RelayError(f"cannot read {label}: {path}: {exc}") from exc
    try:
        with os.fdopen(fd, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat_module.S_ISREG(opened.st_mode):
                raise RelayError(f"{label} path is not a regular file")
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise RelayError(f"{label} path changed while it was opened")
            if opened.st_size > max_bytes:
                raise RelayError(f"{label} exceeds {max_bytes} bytes")
            raw = handle.read(max_bytes + 1)
            after = os.fstat(handle.fileno())
    except OSError as exc:
        raise RelayError(f"cannot read {label}: {path}: {exc}") from exc

    if len(raw) > max_bytes:
        raise RelayError(f"{label} exceeds {max_bytes} bytes")
    if (
        (opened.st_dev, opened.st_ino) != (after.st_dev, after.st_ino)
        or opened.st_size != after.st_size
        or opened.st_mtime_ns != after.st_mtime_ns
        or opened.st_ctime_ns != after.st_ctime_ns
    ):
        raise RelayError(f"{label} changed while it was being read")
    return raw, after


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def reject_duplicate_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def require_unicode_scalars(value: Any) -> None:
    pending: list[tuple[Any, int]] = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > MAX_JSON_NESTING:
            raise ValueError(f"JSON value nesting exceeds {MAX_JSON_NESTING}")
        if isinstance(current, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in current):
                raise ValueError("JSON strings must not contain lone Unicode surrogates")
        elif isinstance(current, list):
            pending.extend((item, depth + 1) for item in current)
        elif isinstance(current, dict):
            for key, item in current.items():
                pending.append((key, depth + 1))
                pending.append((item, depth + 1))


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.strip(ASCII_OUTER_WHITESPACE) + "\n"


def normalize_slug(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    words = [
        word
        for word in re.findall(r"[a-z0-9]+", ascii_value)
        if word not in RESERVED_SLUG_WORDS
    ][:6]
    if not words:
        words = ["session", "context"]
    elif len(words) == 1:
        words.append("context")

    slug = "-".join(words)
    if len(slug) > 48:
        slug = slug[:48].rstrip("-")
        if "-" not in slug:
            slug = f"{slug[:40]}-context"
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+){1,5}", slug):
        raise RelayError(f"could not normalize a valid semantic slug from {value!r}")
    return slug


def parse_created(value: str | None) -> tuple[str, str]:
    if value is None:
        instant = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    else:
        try:
            instant = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, OverflowError) as exc:
            raise RelayError("--created must be an ISO 8601 timestamp") from exc
        if instant.tzinfo is None:
            raise RelayError("--created must include a timezone")
        try:
            instant = instant.astimezone(dt.timezone.utc).replace(microsecond=0)
        except (ValueError, OverflowError) as exc:
            raise RelayError("--created cannot be represented as a UTC timestamp") from exc
    canonical = (
        f"{instant.year:04d}-{instant.month:02d}-{instant.day:02d}T"
        f"{instant.hour:02d}:{instant.minute:02d}:{instant.second:02d}Z"
    )
    filename_timestamp = (
        f"{instant.year:04d}{instant.month:02d}{instant.day:02d}T"
        f"{instant.hour:02d}{instant.minute:02d}{instant.second:02d}Z"
    )
    return canonical, filename_timestamp


def run_git(project_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), *args],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", "backslashreplace").strip()


def run_git_bytes(project_root: Path, *args: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), *args],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def git_paths(project_root: Path, *args: str) -> list[str] | None:
    raw = run_git_bytes(project_root, *args)
    if raw is None:
        return None
    return sorted(
        {
            item.decode("utf-8", "surrogateescape")
            for item in raw.split(b"\0")
            if item
        }
    )


def infer_project_root(value: str | None) -> Path:
    if value:
        return resolve_path(value, "project root")
    try:
        candidate = resolve_path(Path.cwd(), "current working directory")
    except RelayError:
        raise
    git_root = run_git(candidate, "rev-parse", "--show-toplevel")
    return resolve_path(git_root, "Git project root") if git_root else candidate


def workspace_snapshot(project_root_value: str | None, working_directory_value: str | None) -> dict[str, Any]:
    project_root = infer_project_root(project_root_value)
    working_directory = resolve_path(
        working_directory_value or Path.cwd(),
        "working directory",
    )
    inside_git_result = run_git(project_root, "rev-parse", "--is-inside-work-tree")
    inside_git = inside_git_result == "true"
    commit = run_git(project_root, "rev-parse", "HEAD")
    branch = run_git(project_root, "symbolic-ref", "--quiet", "--short", "HEAD")
    snapshot: dict[str, Any] = {
        "project_root": str(project_root),
        "working_directory": str(working_directory),
        "git": inside_git,
    }
    if not inside_git:
        git_marker_found = any(
            (candidate / ".git").exists() or (candidate / ".git").is_symlink()
            for candidate in (project_root, *project_root.parents)
        )
        if inside_git_result is None and git_marker_found:
            snapshot.update(
                {
                    "git_evidence_complete": False,
                    "workspace_dirty": None,
                    "git_errors": ["could not confirm the enclosing Git worktree"],
                }
            )
        return snapshot
    git_root_value = run_git(project_root, "rev-parse", "--show-toplevel")
    if not git_root_value:
        snapshot.update(
            {
                "git_evidence_complete": False,
                "workspace_dirty": None,
                "git_errors": ["could not resolve the Git worktree root"],
            }
        )
        return snapshot
    git_root = resolve_path(git_root_value, "Git worktree root")
    snapshot["git_root"] = str(git_root)
    path_queries = {
        "staged_files": ("diff", "--cached", "--name-only", "-z"),
        "unstaged_files": ("diff", "--name-only", "-z"),
        "untracked_files": ("ls-files", "--others", "--exclude-standard", "-z"),
        "conflicted_files": ("diff", "--name-only", "--diff-filter=U", "-z"),
    }
    snapshot.update(
        {
            "branch": branch,
            "commit": commit,
            "detached_head": branch is None,
        }
    )
    failed_queries: list[str] = []
    for key, query in path_queries.items():
        paths = git_paths(git_root, *query)
        snapshot[key] = paths
        if paths is None:
            failed_queries.append(key)
    snapshot["git_evidence_complete"] = not failed_queries
    if failed_queries:
        snapshot["workspace_dirty"] = None
        snapshot["git_errors"] = [f"could not collect {key}" for key in failed_queries]
    else:
        snapshot["workspace_dirty"] = any(
            snapshot[key]
            for key in ("staged_files", "unstaged_files", "untracked_files", "conflicted_files")
        )
    return snapshot


def decode_config(raw: bytes, path: Path) -> dict[str, str]:
    try:
        config = json.loads(
            raw.decode("utf-8"),
            parse_constant=reject_json_constant,
            object_pairs_hook=reject_duplicate_object_pairs,
        )
        require_unicode_scalars(config)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        RecursionError,
        RelayError,
    ) as exc:
        raise RelayError(f"invalid Relay config: {path}: {exc}") from exc
    if not isinstance(config, dict):
        raise RelayError(f"invalid Relay config: {path}: expected a JSON object")
    unknown = sorted(set(config) - {"storage", "detail"})
    if unknown:
        raise RelayError(f"invalid Relay config: unknown keys: {', '.join(unknown)}")
    storage = config.get("storage")
    detail = config.get("detail")
    if "storage" in config and (
        type(storage) is not str or storage not in {"project", "temp"}
    ):
        raise RelayError(f"invalid Relay storage setting: {storage!r}")
    if "detail" in config and (
        type(detail) is not str or detail not in {"compact", "full"}
    ):
        raise RelayError(f"invalid Relay detail setting: {detail!r}")
    return {key: value for key, value in config.items() if isinstance(value, str)}


def read_config(project_root: Path) -> dict[str, str]:
    if os.name == "posix":
        opened = open_secure_config_directory(project_root, create=False)
        if opened is None:
            return {}
        _, _, directory_fd = opened
        try:
            return read_config_at(
                directory_fd,
                project_root / ".relay" / "config.json",
            )
        finally:
            try:
                os.close(directory_fd)
            except OSError:
                pass

    relay_dir = project_root / ".relay"
    path = relay_dir / "config.json"
    if relay_dir.is_symlink():
        raise RelayError(f"refusing to read config through a symbolic-link directory: {relay_dir}")
    if relay_dir.exists() and not relay_dir.is_dir():
        raise RelayError(f"Relay config parent is not a directory: {relay_dir}")
    if path.is_symlink():
        raise RelayError(f"refusing to read a symbolic-link Relay config: {path}")
    if not path.exists():
        return {}
    try:
        raw, _ = read_regular_file(path, "Relay config", MAX_CONFIG_BYTES)
    except RelayError as exc:
        raise RelayError(f"invalid Relay config: {path}: {exc}") from exc
    return decode_config(raw, path)


def validate_config_values(storage: str, detail: str) -> None:
    if storage not in {"project", "temp"}:
        raise RelayError(f"invalid Relay storage setting: {storage!r}")
    if detail not in {"compact", "full"}:
        raise RelayError(f"invalid Relay detail setting: {detail!r}")


def directory_identity(path: Path, label: str) -> os.stat_result:
    try:
        observed = path.lstat()
    except OSError as exc:
        raise RelayError(f"cannot inspect {label}: {path}: {exc}") from exc
    if stat_module.S_ISLNK(observed.st_mode):
        raise RelayError(f"refusing to use a symbolic-link {label}: {path}")
    if not stat_module.S_ISDIR(observed.st_mode):
        raise RelayError(f"{label} is not a directory: {path}")
    return observed


def assert_directory_identity(path: Path, expected: os.stat_result, label: str) -> None:
    observed = directory_identity(path, label)
    if (observed.st_dev, observed.st_ino) != (expected.st_dev, expected.st_ino):
        raise RelayError(f"{label} changed while Relay was operating: {path}")


def open_secure_config_directory(
    project_root: Path,
    create: bool,
    expected_project_root: os.stat_result | None = None,
) -> tuple[Path, os.stat_result, int] | None:
    root_stat = expected_project_root or directory_identity(project_root, "project root")
    if expected_project_root is not None:
        assert_directory_identity(project_root, expected_project_root, "project root")
    if not project_root.is_dir():
        raise RelayError(f"project root is not a directory: {project_root}")
    relay_dir = project_root / ".relay"
    if create:
        try:
            relay_dir.mkdir(mode=0o700, exist_ok=True)
        except OSError as exc:
            raise RelayError(f"cannot create Relay config directory {relay_dir}: {exc}") from exc
        assert_directory_identity(project_root, root_stat, "project root")
    try:
        before = relay_dir.lstat()
    except FileNotFoundError:
        if create:
            raise RelayError(
                f"Relay config directory disappeared while opening; retry: {relay_dir}"
            )
        return None
    except OSError as exc:
        raise RelayError(f"cannot inspect Relay config directory {relay_dir}: {exc}") from exc
    if stat_module.S_ISLNK(before.st_mode):
        raise RelayError(f"refusing to use a symbolic-link directory: {relay_dir}")
    if not stat_module.S_ISDIR(before.st_mode):
        raise RelayError(f"Relay config parent is not a directory: {relay_dir}")
    if os.name == "posix" and before.st_mode & 0o022:
        raise RelayError(f"Relay config directory is group/world writable: {relay_dir}")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd: int | None = None
    try:
        directory_fd = os.open(relay_dir, flags)
        opened = os.fstat(directory_fd)
    except OSError as exc:
        if directory_fd is not None:
            try:
                os.close(directory_fd)
            except OSError:
                pass
        raise RelayError(f"cannot open Relay config directory {relay_dir}: {exc}") from exc
    if (
        not stat_module.S_ISDIR(opened.st_mode)
        or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
    ):
        try:
            os.close(directory_fd)
        except OSError:
            pass
        raise RelayError(f"Relay config directory changed while opening: {relay_dir}")
    assert_directory_identity(project_root, root_stat, "project root")
    return relay_dir, opened, directory_fd


def read_config_at(directory_fd: int, path: Path) -> dict[str, str]:
    try:
        before = os.stat("config.json", dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise RelayError(f"cannot inspect Relay config {path}: {exc}") from exc
    if stat_module.S_ISLNK(before.st_mode):
        raise RelayError(f"refusing to read a symbolic-link Relay config: {path}")
    if not stat_module.S_ISREG(before.st_mode):
        raise RelayError(f"Relay config path is not a regular file: {path}")
    if before.st_size > MAX_CONFIG_BYTES:
        raise RelayError(f"Relay config exceeds {MAX_CONFIG_BYTES} bytes")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open("config.json", flags, dir_fd=directory_fd)
        with os.fdopen(fd, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise RelayError(f"Relay config changed while opening: {path}")
            raw = handle.read(MAX_CONFIG_BYTES + 1)
            after = os.fstat(handle.fileno())
    except OSError as exc:
        raise RelayError(f"cannot read Relay config {path}: {exc}") from exc
    if len(raw) > MAX_CONFIG_BYTES:
        raise RelayError(f"Relay config exceeds {MAX_CONFIG_BYTES} bytes")
    if (
        (opened.st_dev, opened.st_ino) != (after.st_dev, after.st_ino)
        or opened.st_size != after.st_size
        or opened.st_mtime_ns != after.st_mtime_ns
        or opened.st_ctime_ns != after.st_ctime_ns
    ):
        raise RelayError(f"Relay config changed while being read: {path}")
    return decode_config(raw, path)


def write_config_at(
    relay_dir: Path,
    directory_stat: os.stat_result,
    directory_fd: int,
    content: bytes,
) -> dict[str, Any]:
    try:
        destination = os.stat("config.json", dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        destination = None
    except OSError as exc:
        raise RelayError(f"cannot inspect Relay config destination: {exc}") from exc
    if destination is not None and stat_module.S_ISLNK(destination.st_mode):
        raise RelayError(f"refusing to replace a symbolic-link file: {relay_dir / 'config.json'}")
    if destination is not None and not stat_module.S_ISREG(destination.st_mode):
        raise RelayError(f"Relay config destination is not a regular file: {relay_dir / 'config.json'}")

    temp_name = f".relay-config-write-{secrets.token_hex(12)}.tmp"
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_BINARY", 0)
    )
    temp_created = False
    published = False
    warnings: list[str] = []
    try:
        fd = os.open(temp_name, flags, 0o600, dir_fd=directory_fd)
        temp_created = True
        with os.fdopen(fd, "wb") as handle:
            if hasattr(os, "fchmod"):
                os.fchmod(handle.fileno(), 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        current = relay_dir.lstat()
        if (current.st_dev, current.st_ino) != (directory_stat.st_dev, directory_stat.st_ino):
            raise RelayError(f"Relay config directory changed before publication: {relay_dir}")
        os.replace(
            temp_name,
            "config.json",
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        published = True
        try:
            os.fsync(directory_fd)
            directory_fsynced = True
        except OSError:
            directory_fsynced = False
            warnings.append(
                "directory fsync is unsupported or failed; crash durability is unverified"
            )
        try:
            current = relay_dir.lstat()
            if (current.st_dev, current.st_ino) != (
                directory_stat.st_dev,
                directory_stat.st_ino,
            ):
                raise RelayError(
                    "Relay config was atomically replaced in the opened directory, "
                    f"but its project path changed after publication: {relay_dir}"
                )
        except OSError as exc:
            raise RelayError(
                "Relay config was atomically replaced in the opened directory, "
                f"but its project path could not be reverified after publication: {relay_dir}: {exc}"
            ) from exc
        return {
            "publication": "atomic-replace",
            "file_fsynced": True,
            "directory_fsynced": directory_fsynced,
            "private_permissions": True,
            "warnings": warnings,
        }
    except RelayError:
        raise
    except (OSError, TypeError) as exc:
        if published:
            warnings.append(f"post-publication durability operation failed: {exc}")
            return {
                "publication": "atomic-replace",
                "file_fsynced": True,
                "directory_fsynced": False,
                "private_permissions": True,
                "warnings": warnings,
            }
        raise RelayError(f"atomic config publication failed: {exc}") from exc
    finally:
        if temp_created:
            try:
                os.unlink(temp_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError:
                if published:
                    warnings.append("temporary config name cleanup failed after publication")


def set_config(args: argparse.Namespace) -> dict[str, Any]:
    project_root = infer_project_root(args.project_root)
    config_path = project_root / ".relay" / "config.json"
    if os.name == "posix" and fcntl is not None:
        opened = open_secure_config_directory(project_root, create=True)
        if opened is None:
            raise RelayError("Relay config directory could not be created; retry")
        relay_dir, directory_stat, directory_fd = opened
        lock_fd: int | None = None
        publication: dict[str, Any] | None = None
        try:
            lock_flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            try:
                lock_fd = os.open(".config.lock", lock_flags, 0o600, dir_fd=directory_fd)
                if not stat_module.S_ISREG(os.fstat(lock_fd).st_mode):
                    raise RelayError("Relay config lock is not a regular file")
                fcntl.flock(lock_fd, fcntl.LOCK_EX)
            except OSError as exc:
                raise RelayError(f"cannot lock Relay config: {exc}") from exc
            current = read_config_at(directory_fd, config_path)
            storage = args.storage or current.get("storage", "project")
            detail = args.detail or current.get("detail", "compact")
            validate_config_values(storage, detail)
            content = json.dumps(
                {"storage": storage, "detail": detail},
                separators=(",", ":"),
            ).encode("utf-8") + b"\n"
            publication = write_config_at(
                relay_dir,
                directory_stat,
                directory_fd,
                content,
            )
        finally:
            if lock_fd is not None:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                except OSError:
                    if publication is not None:
                        publication["warnings"].append("config lock release failed after publication")
                try:
                    os.close(lock_fd)
                except OSError:
                    if publication is not None:
                        publication["warnings"].append("config lock close failed after publication")
            try:
                os.close(directory_fd)
            except OSError:
                if publication is not None:
                    publication["warnings"].append(
                        "config directory close failed after publication"
                    )
        assert publication is not None
    else:  # pragma: no cover - Windows behavior is documented as degraded.
        current = read_config(project_root)
        storage = args.storage or current.get("storage", "project")
        detail = args.detail or current.get("detail", "compact")
        validate_config_values(storage, detail)
        content = json.dumps(
            {"storage": storage, "detail": detail},
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        publication = write_replace_atomic(config_path, content)
        publication["warnings"].append(
            "cross-process config locking and parent-directory no-follow semantics are unverified on this platform"
        )
    return {
        "path": str(config_path),
        "project_root": str(project_root),
        "storage": storage,
        "detail": detail,
        **publication,
    }


def get_config(args: argparse.Namespace) -> dict[str, Any]:
    project_root = infer_project_root(args.project_root)
    if os.name == "posix":
        opened = open_secure_config_directory(project_root, create=False)
        if opened is None:
            current = {}
        else:
            _, _, directory_fd = opened
            try:
                current = read_config_at(
                    directory_fd,
                    project_root / ".relay" / "config.json",
                )
            finally:
                try:
                    os.close(directory_fd)
                except OSError:
                    pass
    else:  # pragma: no cover - Windows behavior is documented as degraded.
        current = read_config(project_root)
    return {
        "path": str(project_root / ".relay" / "config.json"),
        "project_root": str(project_root),
        "storage": current.get("storage", "project"),
        "detail": current.get("detail", "compact"),
        "source": "config" if current else "built-in",
    }


def mask_fenced_code(body: str) -> str:
    """Mask fenced code while preserving byte offsets and newlines."""
    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in body.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        newline = line[len(content) :]
        if fence_character is not None:
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
                content,
            )
            output.append(" " * len(content) + newline)
            if closing:
                fence_character = None
                fence_length = 0
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})", content)
        if opening:
            marker = opening.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
            output.append(" " * len(content) + newline)
            continue
        output.append(line)
    return "".join(output)


def extract_sections(body: str) -> tuple[list[str], dict[str, str]]:
    visible_body = mask_fenced_code(body)
    matches = list(re.finditer(r"^## ([^\n]+)\s*$", visible_body, flags=re.MULTILINE))
    order = [match.group(1).strip() for match in matches]
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1).strip()] = body[match.end() : end].strip()
    return order, sections


def validate_body(
    body: str,
    mode: str,
    required_override: list[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    if body.startswith("---\n"):
        errors.append("body draft must not contain YAML frontmatter")
    visible_body = mask_fenced_code(body)
    if not re.search(r"^# Relay: \S", visible_body, flags=re.MULTILINE):
        errors.append("body must contain a non-empty '# Relay: <title>' heading")

    order, sections = extract_sections(body)
    heading_counts = Counter(order)
    duplicate_headings = sorted(
        heading for heading, count in heading_counts.items() if count > 1
    )
    if duplicate_headings:
        errors.append("duplicate headings: " + ", ".join(duplicate_headings))
    required = required_override or (FULL_HEADINGS if mode == "full" else CORE_HEADINGS)
    missing = [heading for heading in required if heading not in sections]
    if missing:
        errors.append("missing required headings: " + ", ".join(missing))

    positions = [order.index(heading) for heading in required if heading in order]
    if positions != sorted(positions):
        errors.append("required headings are out of canonical order")

    for heading in required:
        content = sections.get(heading, "")
        if not content:
            errors.append(f"section is empty: {heading}")
        elif re.fullmatch(r"(?:<[^>]+>|\[TODO[^]]*\])", content, flags=re.IGNORECASE):
            errors.append(f"section still contains a placeholder: {heading}")
    return errors


def secret_findings(text: str) -> list[str]:
    matches: list[tuple[int, str]] = []
    for label, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            matches.append((match.start(), label))
            if len(matches) >= MAX_SECRET_FINDINGS:
                break
        if len(matches) >= MAX_SECRET_FINDINGS:
            break
    matches.sort()
    findings: list[str] = []
    current_line = 1
    cursor = 0
    for position, label in matches:
        current_line += text.count("\n", cursor, position)
        cursor = position
        findings.append(f"{label} pattern on line {current_line}")
    if len(matches) == MAX_SECRET_FINDINGS:
        findings.append(f"secret finding report capped at {MAX_SECRET_FINDINGS} matches")
    return findings


def canonical_payload(metadata: dict[str, Any], body: str) -> bytes:
    payload = {"metadata": metadata, "body": body}
    try:
        require_unicode_scalars(payload)
        return json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise RelayError(f"metadata cannot be canonicalized: {exc}") from exc


def compute_digest(metadata: dict[str, Any], body: str) -> str:
    return hashlib.sha256(canonical_payload(metadata, body)).hexdigest()


def render_artifact(metadata: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key in METADATA_ORDER:
        if key in metadata:
            value = json.dumps(
                metadata[key],
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            lines.append(f"{key}: {value}")
    unknown = sorted(set(metadata) - set(METADATA_ORDER))
    for key in unknown:
        value = json.dumps(
            metadata[key],
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        lines.append(f"{key}: {value}")
    lines.extend(["---", "", body.rstrip("\n"), ""])
    return "\n".join(lines)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise RelayError("missing YAML frontmatter")
    closing = None
    for index in range(1, len(lines)):
        if lines[index].rstrip("\r\n") == "---":
            closing = index
            break
    if closing is None:
        raise RelayError("unterminated YAML frontmatter")

    metadata: dict[str, Any] = {}
    for line_number, raw_line in enumerate(lines[1:closing], start=2):
        line = raw_line.rstrip("\r\n")
        if not line:
            continue
        if ":" not in line:
            raise RelayError(f"invalid frontmatter line {line_number}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not KEY_RE.fullmatch(key):
            raise RelayError(f"invalid frontmatter key on line {line_number}: {key!r}")
        if key in metadata:
            raise RelayError(f"duplicate frontmatter key: {key}")
        try:
            parsed_value = json.loads(
                raw_value.strip(),
                parse_constant=reject_json_constant,
                object_pairs_hook=reject_duplicate_object_pairs,
            )
            require_unicode_scalars(parsed_value)
            metadata[key] = parsed_value
        except (json.JSONDecodeError, ValueError, RecursionError) as exc:
            raise RelayError(
                f"frontmatter value for {key!r} is not valid JSON on line {line_number}"
            ) from exc
    body = "".join(lines[closing + 1 :]).lstrip("\r\n")
    return metadata, normalize_text(body)


def fsync_directory_fd(directory_fd: int) -> bool:
    try:
        os.fsync(directory_fd)
    except OSError:
        return False
    return True


def fsync_directory(path: Path) -> bool:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        directory_fd = os.open(path, flags)
    except OSError:
        return False
    succeeded = True
    try:
        if not fsync_directory_fd(directory_fd):
            succeeded = False
    finally:
        try:
            os.close(directory_fd)
        except OSError:
            succeeded = False
    return succeeded


def write_exclusive_atomic(
    path: Path,
    content: bytes,
    expected_project_root: Path | None = None,
    expected_project_root_stat: os.stat_result | None = None,
) -> dict[str, Any]:
    if os.name != "posix":  # pragma: no cover - Windows privacy remains unverified.
        return write_exclusive_atomic_path_fallback(path, content)

    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        before = path.parent.lstat()
    except OSError as exc:
        raise RelayError(f"cannot create Relay destination {path.parent}: {exc}") from exc
    if stat_module.S_ISLNK(before.st_mode):
        raise RelayError(f"refusing to write through a symbolic-link directory: {path.parent}")
    if not stat_module.S_ISDIR(before.st_mode):
        raise RelayError(f"Relay destination is not a directory: {path.parent}")
    writable_by_others = before.st_mode & 0o022
    sticky = before.st_mode & stat_module.S_ISVTX
    if writable_by_others and not sticky:
        raise RelayError(
            f"Relay destination is group/world writable without sticky bit: {path.parent}"
        )
    if expected_project_root is not None:
        if expected_project_root_stat is None:
            expected_project_root_stat = directory_identity(
                expected_project_root,
                "project root",
            )
        assert_directory_identity(expected_project_root, expected_project_root_stat, "project root")

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd: int | None = None
    try:
        directory_fd = os.open(path.parent, flags)
        opened = os.fstat(directory_fd)
    except OSError as exc:
        if directory_fd is not None:
            try:
                os.close(directory_fd)
            except OSError:
                pass
        raise RelayError(f"cannot open Relay destination {path.parent}: {exc}") from exc
    if (
        not stat_module.S_ISDIR(opened.st_mode)
        or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
    ):
        try:
            os.close(directory_fd)
        except OSError:
            pass
        raise RelayError(f"Relay destination changed while opening: {path.parent}")

    temp_name = f".relay-write-{secrets.token_hex(12)}.tmp"
    temp_created = False
    published = False
    warnings: list[str] = []
    result: dict[str, Any] | None = None
    try:
        temp_flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_BINARY", 0)
        )
        fd = os.open(temp_name, temp_flags, 0o600, dir_fd=directory_fd)
        temp_created = True
        with os.fdopen(fd, "wb") as handle:
            if hasattr(os, "fchmod"):
                os.fchmod(handle.fileno(), 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        current = path.parent.lstat()
        if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
            raise RelayError(f"Relay destination changed before publication: {path.parent}")
        if expected_project_root is not None and expected_project_root_stat is not None:
            assert_directory_identity(expected_project_root, expected_project_root_stat, "project root")
        os.link(
            temp_name,
            path.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
            follow_symlinks=False,
        )
        published = True
        try:
            os.unlink(temp_name, dir_fd=directory_fd)
            temp_created = False
        except OSError as exc:
            warnings.append(f"temporary name cleanup failed: {exc}")

        directory_fsynced = fsync_directory_fd(directory_fd)
        if not directory_fsynced:
            warnings.append(
                "directory fsync is unsupported or failed; crash durability is unverified"
            )
        path_problem: str | None = None
        try:
            current = path.parent.lstat()
            if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
                path_problem = "changed"
        except OSError as exc:
            path_problem = f"could not be reverified: {exc}"
        if path_problem is not None:
            try:
                os.unlink(path.name, dir_fd=directory_fd)
                published = False
                fsync_directory_fd(directory_fd)
            except OSError as exc:
                raise RelayError(
                    "Relay artifact was published in the opened directory after its "
                    f"requested path {path_problem}, and rollback failed: {exc}"
                ) from exc
            raise RelayError(
                "Relay destination path changed during publication; "
                f"the new artifact was rolled back: {path.parent}"
            )
        if expected_project_root is not None and expected_project_root_stat is not None:
            assert_directory_identity(expected_project_root, expected_project_root_stat, "project root")
        result = {
            "publication": "atomic-exclusive",
            "file_fsynced": True,
            "directory_fsynced": directory_fsynced,
            "private_permissions": True,
            "warnings": warnings,
        }
    except FileExistsError:
        raise
    except RelayError:
        raise
    except (OSError, TypeError) as exc:
        if published:
            warnings.append(f"post-publication durability/cleanup operation failed: {exc}")
            result = {
                "publication": "atomic-exclusive",
                "file_fsynced": True,
                "directory_fsynced": False,
                "private_permissions": True,
                "warnings": warnings,
            }
        else:
            raise RelayError(
                f"atomic exclusive publication failed for {path}; no non-atomic fallback was used: {exc}"
            ) from exc
    finally:
        if temp_created:
            try:
                os.unlink(temp_name, dir_fd=directory_fd)
            except OSError:
                pass
        try:
            os.close(directory_fd)
        except OSError as exc:
            if result is not None:
                result["warnings"].append(
                    f"destination directory close failed after publication: {exc}"
                )
    if result is None:
        raise RelayError(f"atomic exclusive publication produced no result for {path}")
    return result


def write_exclusive_atomic_path_fallback(path: Path, content: bytes) -> dict[str, Any]:
    """Non-POSIX fallback with explicit ACL and locking limitations."""
    if path.parent.is_symlink():
        raise RelayError(f"refusing to write through a symbolic-link directory: {path.parent}")
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=".relay-write-",
            suffix=".tmp",
            dir=path.parent,
        )
    except OSError as exc:
        raise RelayError(f"cannot create Relay destination {path.parent}: {exc}") from exc
    temp_path = Path(temp_name)
    published = False
    warnings = ["private file ACL and parent-directory no-follow semantics are unverified"]
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temp_path, path)
        published = True
        temp_path.unlink(missing_ok=True)
        directory_fsynced = fsync_directory(path.parent)
        if not directory_fsynced:
            warnings.append(
                "directory fsync is unsupported or failed; crash durability is unverified"
            )
        return {
            "publication": "atomic-exclusive",
            "file_fsynced": True,
            "directory_fsynced": directory_fsynced,
            "private_permissions": False,
            "warnings": warnings,
        }
    except FileExistsError:
        raise
    except OSError as exc:
        if published:
            warnings.append(f"post-publication operation failed: {exc}")
            return {
                "publication": "atomic-exclusive",
                "file_fsynced": True,
                "directory_fsynced": False,
                "private_permissions": False,
                "warnings": warnings,
            }
        raise RelayError(
            f"atomic exclusive publication failed for {path}; no non-atomic fallback was used: {exc}"
        ) from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def write_replace_atomic(path: Path, content: bytes) -> dict[str, Any]:
    """Atomically create or replace a small trusted config file."""
    if path.parent.is_symlink():
        raise RelayError(f"refusing to write through a symbolic-link directory: {path.parent}")
    if path.is_symlink():
        raise RelayError(f"refusing to replace a symbolic-link file: {path}")
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.parent.is_symlink():
            raise RelayError(
                f"refusing to write through a symbolic-link directory: {path.parent}"
            )
        parent_stat = path.parent.stat()
        if not stat_module.S_ISDIR(parent_stat.st_mode):
            raise RelayError(f"Relay destination is not a directory: {path.parent}")
        if os.name == "posix":
            writable_by_others = parent_stat.st_mode & 0o022
            sticky = parent_stat.st_mode & stat_module.S_ISVTX
            if writable_by_others and not sticky:
                raise RelayError(
                    f"Relay destination is group/world writable without sticky bit: {path.parent}"
                )
        fd, temp_name = tempfile.mkstemp(
            prefix=".relay-config-write-",
            suffix=".tmp",
            dir=path.parent,
        )
    except OSError as exc:
        raise RelayError(f"cannot create Relay destination {path.parent}: {exc}") from exc

    temp_path = Path(temp_name)
    replaced = False
    warnings: list[str] = []
    try:
        with os.fdopen(fd, "wb") as handle:
            if hasattr(os, "fchmod"):
                os.fchmod(handle.fileno(), 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            raise RelayError(f"refusing to replace a symbolic-link file: {path}")
        os.replace(temp_path, path)
        replaced = True
        directory_fsynced = fsync_directory(path.parent)
        if not directory_fsynced:
            warnings.append("directory fsync is unsupported or failed; crash durability is unverified")
        private_permissions = os.name == "posix"
        if not private_permissions:
            warnings.append("private file ACL could not be verified on this platform")
        return {
            "publication": "atomic-replace",
            "file_fsynced": True,
            "directory_fsynced": directory_fsynced,
            "private_permissions": private_permissions,
            "warnings": warnings,
        }
    except RelayError:
        raise
    except OSError as exc:
        if replaced:
            warnings.append(f"post-publication durability operation failed: {exc}")
            return {
                "publication": "atomic-replace",
                "file_fsynced": True,
                "directory_fsynced": False,
                "private_permissions": os.name == "posix",
                "warnings": warnings,
            }
        raise RelayError(f"atomic config publication failed for {path}: {exc}") from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def load_body(path_value: str) -> str:
    if path_value == "-":
        raw = sys.stdin.buffer.read(MAX_ARTIFACT_BYTES + 1)
    else:
        path = Path(path_value)
        raw, _ = read_regular_file(path, "body draft", MAX_ARTIFACT_BYTES)
    if len(raw) > MAX_ARTIFACT_BYTES:
        raise RelayError(f"body draft exceeds {MAX_ARTIFACT_BYTES} bytes")
    try:
        return normalize_text(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise RelayError("body draft is not valid UTF-8") from exc


def create_artifact(args: argparse.Namespace) -> dict[str, Any]:
    project_root = infer_project_root(args.project_root)
    project_root_stat = directory_identity(project_root, "project root")
    working_directory = resolve_path(
        args.working_directory or Path.cwd(),
        "working directory",
    )
    config = {} if args.mode and args.storage else read_config(project_root)
    mode = args.mode or config.get("detail", "compact")
    storage = args.storage or config.get("storage", "project")
    slug = normalize_slug(args.slug)
    body = load_body(args.body)

    if args.parent_relay_id and not re.fullmatch(r"rly_[0-9a-f]{32}", args.parent_relay_id):
        raise RelayError("--parent-relay-id must be 'rly_' plus 32 lowercase hex characters")
    for option, value in (
        ("--source-session", args.source_session),
        ("--created-by", args.created_by),
    ):
        if value is not None and not value:
            raise RelayError(f"{option} must not be empty")

    errors = validate_body(body, mode)
    if errors:
        raise RelayError("invalid handoff body:\n- " + "\n- ".join(errors))
    sensitive_inputs = "\n".join(
        value
        for value in (body, args.focus, args.source_session, args.created_by)
        if value
    )
    findings = secret_findings(sensitive_inputs)
    if findings:
        raise RelayError(
            "possible sensitive values found; redact them before finalizing:\n- "
            + "\n- ".join(findings)
        )

    created, filename_timestamp = parse_created(args.created)
    snapshot = workspace_snapshot(str(project_root), str(working_directory))
    branch = snapshot.get("branch")
    commit = snapshot.get("commit")

    if args.output_dir:
        output_dir = resolve_path(args.output_dir, "output")
    elif storage == "project":
        output_dir = project_root / ".relay"
    else:
        output_dir = resolve_path(tempfile.gettempdir(), "temporary output")

    for _ in range(5):
        metadata: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "relay_id": "rly_" + secrets.token_hex(16),
            "created": created,
            "mode": mode,
            "disposition": args.disposition,
            "storage": storage,
            "project_root": str(project_root),
            "working_directory": str(working_directory),
            "focus": args.focus or "",
            "slug": slug,
        }
        if snapshot["git"] and type(snapshot.get("workspace_dirty")) is bool:
            metadata["workspace_dirty"] = snapshot["workspace_dirty"]
        if commit:
            metadata["commit"] = commit
        if branch:
            metadata["branch"] = branch
        if args.parent_relay_id:
            metadata["parent_relay_id"] = args.parent_relay_id
        if args.source_session:
            metadata["source_session"] = args.source_session
        if args.source_context_state:
            metadata["source_context_state"] = args.source_context_state
        if args.created_by:
            metadata["created_by"] = args.created_by

        metadata_findings = secret_findings(
            json.dumps(metadata, ensure_ascii=False, sort_keys=True)
            + "\n"
            + body
        )
        if metadata_findings:
            raise RelayError(
                "possible sensitive values found in the finalized payload; redact or rename them before finalizing:\n- "
                + "\n- ".join(metadata_findings)
            )
        digest = compute_digest(metadata, body)
        metadata["artifact_sha256"] = "sha256:" + digest
        filename = f"relay-{filename_timestamp}-{slug}-{digest[:12]}.md"
        output_path = output_dir / filename
        content = render_artifact(metadata, body).encode("utf-8")
        if len(content) > MAX_ARTIFACT_BYTES:
            raise RelayError(
                f"final Relay artifact exceeds {MAX_ARTIFACT_BYTES} bytes after adding metadata"
            )
        try:
            publication = write_exclusive_atomic(
                output_path,
                content,
                expected_project_root=project_root,
                expected_project_root_stat=project_root_stat,
            )
        except FileExistsError:
            continue
        result = {
            "path": str(output_path),
            "relay_id": metadata["relay_id"],
            "artifact_sha256": metadata["artifact_sha256"],
            "mode": mode,
            "storage": storage,
            **publication,
        }
        if snapshot.get("git_evidence_complete") is False:
            result["warnings"].append(
                "Git workspace evidence is incomplete; run snapshot and reconcile Git state manually"
            )
        return result
    raise RelayError("could not allocate a unique Relay filename after five attempts")


def parse_v1_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return {}, normalize_text(text)
    closing = None
    for index in range(1, len(lines)):
        if lines[index].rstrip("\r\n") == "---":
            closing = index
            break
    if closing is None:
        raise RelayError("unterminated legacy frontmatter")
    metadata: dict[str, str] = {}
    for raw_line in lines[1:closing]:
        line = raw_line.rstrip("\r\n")
        if not line:
            continue
        if ":" not in line:
            raise RelayError("invalid legacy frontmatter line")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    body = "".join(lines[closing + 1 :]).lstrip("\r\n")
    return metadata, normalize_text(body)


def frontmatter_declares_v1(text: str) -> bool:
    lines = text.splitlines()
    for line in lines[1:]:
        if line == "---":
            return False
        if re.fullmatch(r"schema_version:\s*1\s*", line):
            return True
    return False


def validate_path(path: Path, include_body: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "valid": False,
        "format": "unknown",
        "integrity": "unverified",
        "errors": [],
        "warnings": [],
        "metadata": {},
    }
    errors: list[str] = result["errors"]
    warnings: list[str] = result["warnings"]

    try:
        raw, relay_stat = read_regular_file(path, "relay", MAX_ARTIFACT_BYTES)
    except RelayError as exc:
        errors.append(str(exc))
        return result
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        errors.append("relay is not valid UTF-8")
        return result

    sensitive_findings = secret_findings(text)
    for finding in sensitive_findings:
        errors.append("possible sensitive value: " + finding)
    if os.name == "posix":
        mode = relay_stat.st_mode & 0o777
        if mode & 0o077:
            warnings.append(f"relay permissions are {mode:04o}; prefer 0600")

    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        result["format"] = "legacy"
        warnings.append("legacy relay has no schema or integrity metadata")
        has_title = bool(re.search(r"^# .+", text, flags=re.MULTILINE))
        if not has_title:
            errors.append("legacy relay has no title heading")
        result["valid"] = not errors
        if include_body and result["valid"]:
            result["body"] = normalize_text(text)
        return result

    try:
        if frontmatter_declares_v1(text):
            legacy_metadata, body = parse_v1_frontmatter(text)
            result["format"] = "v1"
            if not sensitive_findings:
                result["metadata"] = legacy_metadata
            warnings.append("schema v1 relay has no verifiable artifact digest")
            # V1 full predates the v2 fidelity sections; compatibility requires
            # only the stable core headings, regardless of the recorded v1 mode.
            if validate_body(body, "compact", LEGACY_CORE_HEADINGS):
                errors.append("schema v1 body does not satisfy the current core headings")
            result["valid"] = not errors
            if include_body and result["valid"]:
                result["body"] = body
            return result
        metadata, body = parse_frontmatter(text)
    except RelayError as exc:
        errors.append(str(exc))
        return result

    if not sensitive_findings:
        result["metadata"] = metadata
    if (
        type(metadata.get("schema_version")) is not int
        or metadata.get("schema_version") != SCHEMA_VERSION
    ):
        errors.append(f"unsupported schema_version: {metadata.get('schema_version')!r}")
        return result
    result["format"] = "v2"

    for key, value in metadata.items():
        if key in CORE_METADATA_KEYS:
            continue
        if not EXTENSION_KEY_RE.fullmatch(key):
            errors.append(
                f"unknown metadata field {key!r}; informational extensions must use x_<name>"
            )
        elif type(value) is not str or not value or len(value) > 4096:
            errors.append(
                f"extension metadata field {key!r} must be a non-empty string of at most 4096 characters"
            )

    required_fields = {
        "schema_version": int,
        "relay_id": str,
        "created": str,
        "mode": str,
        "disposition": str,
        "storage": str,
        "project_root": str,
        "working_directory": str,
        "focus": str,
        "slug": str,
        "artifact_sha256": str,
    }
    for key, expected_type in required_fields.items():
        if key not in metadata:
            errors.append(f"missing required metadata field: {key}")
        elif type(metadata[key]) is not expected_type:
            errors.append(f"metadata field {key!r} has the wrong type")
    if errors:
        return result

    if not re.fullmatch(r"rly_[0-9a-f]{32}", metadata["relay_id"]):
        errors.append("relay_id must be 'rly_' plus 32 lowercase hex characters")
    if metadata["mode"] not in {"compact", "full"}:
        errors.append(f"invalid mode: {metadata['mode']!r}")
    if metadata["storage"] not in {"project", "temp"}:
        errors.append(f"invalid storage: {metadata['storage']!r}")
    if metadata["disposition"] not in DISPOSITIONS:
        errors.append(f"invalid disposition: {metadata['disposition']!r}")
    for key in ("project_root", "working_directory"):
        if not metadata[key]:
            errors.append(f"metadata field {key!r} must not be empty")
    if len(metadata["slug"]) > 48 or not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+){1,5}", metadata["slug"]
    ):
        errors.append("slug does not match the Relay v2 semantic slug contract")
    elif set(metadata["slug"].split("-")) & RESERVED_SLUG_WORDS:
        errors.append("slug must describe the task and omit Relay control words")

    optional_strings = ("branch", "source_session", "created_by")
    for key in optional_strings:
        if key in metadata and (type(metadata[key]) is not str or not metadata[key]):
            errors.append(f"optional metadata field {key!r} must be a non-empty string")
    if "commit" in metadata and (
        type(metadata["commit"]) is not str
        or not re.fullmatch(r"[0-9a-f]{40,64}", metadata["commit"])
    ):
        errors.append("commit must be 40-64 lowercase hex characters")
    if "workspace_dirty" in metadata and type(metadata["workspace_dirty"]) is not bool:
        errors.append("workspace_dirty must be a boolean")
    if "parent_relay_id" in metadata and (
        type(metadata["parent_relay_id"]) is not str
        or not re.fullmatch(r"rly_[0-9a-f]{32}", metadata["parent_relay_id"])
    ):
        errors.append("parent_relay_id must match the Relay v2 ID contract")
    if "source_context_state" in metadata and metadata["source_context_state"] not in SOURCE_CONTEXT_STATES:
        errors.append("source_context_state has an unsupported value")

    if errors:
        return result

    expected_timestamp: str | None = None
    try:
        canonical_created, expected_timestamp = parse_created(metadata["created"])
    except RelayError as exc:
        errors.append(str(exc))
    else:
        if canonical_created != metadata["created"]:
            errors.append("created timestamp is not canonical UTC seconds")

    body_errors = validate_body(body, metadata["mode"])
    errors.extend(body_errors)
    digest_value = metadata["artifact_sha256"]
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest_value):
        errors.append("artifact_sha256 must be 'sha256:' plus 64 lowercase hex characters")
    else:
        unsigned_metadata = dict(metadata)
        del unsigned_metadata["artifact_sha256"]
        actual_digest = compute_digest(unsigned_metadata, body)
        expected_digest = digest_value.removeprefix("sha256:")
        if actual_digest != expected_digest:
            errors.append("artifact SHA-256 mismatch")
        else:
            result["integrity"] = "verified"

    filename_match = FILENAME_RE.fullmatch(path.name)
    if not filename_match:
        errors.append("filename does not match the Relay v2 naming contract")
    else:
        if expected_timestamp is not None and filename_match.group("timestamp") != expected_timestamp:
            errors.append("filename timestamp does not match metadata.created")
        if filename_match.group("slug") != metadata["slug"]:
            errors.append("filename slug does not match metadata.slug")
        if re.fullmatch(r"sha256:[0-9a-f]{64}", digest_value):
            if filename_match.group("digest") != digest_value[7:19]:
                errors.append("filename digest prefix does not match artifact_sha256")

    result["valid"] = not errors
    if include_body and result["valid"]:
        result["body"] = body
    return result


def print_result(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        # Keep machine-readable output safe even when stdout uses ASCII strict.
        print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
        return
    if "relay_id" in result and "path" in result and "valid" not in result:
        print(result["path"])
        print(f"relay_id: {result['relay_id']}")
        print(f"artifact_sha256: {result['artifact_sha256']}")
        print(f"publication: {result['publication']}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")
        return
    if "detail" in result and "storage" in result and "valid" not in result:
        print(result["path"])
        print(f"storage: {result['storage']}")
        print(f"detail: {result['detail']}")
        if "publication" in result:
            print(f"publication: {result['publication']}")
        if "source" in result:
            print(f"source: {result['source']}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")
        return
    label = "valid" if result.get("valid") else "invalid"
    print(f"{label}: {result.get('path', '')}")
    print(f"format: {result.get('format', 'unknown')}")
    print(f"integrity: {result.get('integrity', 'unverified')}")
    for warning in result.get("warnings", []):
        print(f"warning: {warning}")
    for error in result.get("errors", []):
        print(f"error: {error}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="finalize a Markdown body as a Relay v2 artifact")
    create.add_argument("--body", required=True, help="Markdown body path, or '-' for stdin")
    create.add_argument("--slug", required=True, help="2-6 word semantic topic slug")
    create.add_argument("--focus", default="", help="next-session focus")
    create.add_argument("--mode", choices=("compact", "full"))
    create.add_argument("--storage", choices=("project", "temp"))
    create.add_argument("--disposition", choices=DISPOSITIONS, default="continue")
    create.add_argument("--project-root")
    create.add_argument("--working-directory")
    create.add_argument("--output-dir", help="test/advanced override for the destination directory")
    create.add_argument("--parent-relay-id")
    create.add_argument("--source-session")
    create.add_argument("--source-context-state", choices=SOURCE_CONTEXT_STATES)
    create.add_argument("--created-by")
    create.add_argument("--created", help="test/replay override for the creation timestamp")
    create.add_argument("--json", action="store_true")

    validate = subparsers.add_parser("validate", help="validate a Relay artifact")
    validate.add_argument("path")
    validate.add_argument("--json", action="store_true")
    validate.add_argument(
        "--include-body",
        action="store_true",
        help="include the body captured from the validated file descriptor in JSON output",
    )

    snapshot = subparsers.add_parser(
        "snapshot",
        help="emit deterministic project and Git evidence for a handoff",
    )
    snapshot.add_argument("--project-root")
    snapshot.add_argument("--working-directory")

    config = subparsers.add_parser(
        "config-set",
        help="atomically create or update project-local Relay defaults",
    )
    config.add_argument("--project-root")
    config.add_argument("--storage", choices=("project", "temp"))
    config.add_argument("--detail", choices=("compact", "full"))
    config.add_argument("--json", action="store_true")

    config_get = subparsers.add_parser(
        "config-get",
        help="read effective project-local Relay defaults safely",
    )
    config_get.add_argument("--project-root")
    config_get.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "create":
            result = create_artifact(args)
            print_result(result, args.json)
            return 0
        if args.command == "snapshot":
            print(
                json.dumps(
                    workspace_snapshot(args.project_root, args.working_directory),
                    ensure_ascii=True,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "config-set":
            result = set_config(args)
            print_result(result, args.json)
            return 0
        if args.command == "config-get":
            result = get_config(args)
            print_result(result, args.json)
            return 0
        result = validate_path(Path(args.path), include_body=args.include_body)
        print_result(result, args.json)
        return 0 if result["valid"] else 1
    except RelayError as exc:
        try:
            print(f"relay artifact error: {exc}", file=sys.stderr)
        except UnicodeEncodeError:
            print("relay artifact error: output contains unrepresentable characters", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
