from __future__ import annotations

import errno
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "skills" / "relay" / "scripts" / "relay_artifact.py"
TOOL_SPEC = importlib.util.spec_from_file_location("relay_artifact_under_test", TOOL)
assert TOOL_SPEC is not None and TOOL_SPEC.loader is not None
RELAY_ARTIFACT = importlib.util.module_from_spec(TOOL_SPEC)
TOOL_SPEC.loader.exec_module(RELAY_ARTIFACT)


COMPACT_BODY = (ROOT / "tests" / "fixtures" / "v2-compact-body.md").read_text(
    encoding="utf-8"
)
FULL_BODY = (ROOT / "tests" / "fixtures" / "v2-full-body.md").read_text(
    encoding="utf-8"
)


class RelayArtifactTests(unittest.TestCase):
    def run_tool(
        self,
        *args: str,
        cwd: Path | None = None,
        expect: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(TOOL), *args],
            cwd=cwd or ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            expect,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def create(
        self,
        directory: Path,
        body: str = COMPACT_BODY,
        *extra: str,
    ) -> dict[str, object]:
        body_path = directory / "body.md"
        body_path.write_text(body, encoding="utf-8")
        result = self.run_tool(
            "create",
            "--body",
            str(body_path),
            "--slug",
            "reward logging",
            "--focus",
            "continue: reward logging #3",
            "--project-root",
            str(directory),
            "--output-dir",
            str(directory / "out"),
            "--created",
            "2026-08-19T06:30:45Z",
            "--json",
            *extra,
        )
        return json.loads(result.stdout)

    def validate(self, path: Path, expect: int = 0) -> dict[str, object]:
        result = self.run_tool("validate", str(path), "--json", expect=expect)
        return json.loads(result.stdout)

    def test_create_and_validate_compact_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            path = Path(str(created["path"]))

            self.assertRegex(
                path.name,
                r"^relay-20260819T063045Z-reward-logging-[0-9a-f]{12}\.md$",
            )
            result = self.validate(path)
            self.assertTrue(result["valid"])
            self.assertEqual(result["format"], "v2")
            self.assertEqual(result["integrity"], "verified")
            metadata = result["metadata"]
            self.assertEqual(metadata["schema_version"], 2)
            self.assertEqual(metadata["focus"], "continue: reward logging #3")
            self.assertEqual(path.name[-15:-3], metadata["artifact_sha256"][7:19])
            self.assertEqual(created["publication"], "atomic-exclusive")
            self.assertTrue(created["file_fsynced"])

            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_canonical_digest_golden_vector(self) -> None:
        metadata = {
            "schema_version": 2,
            "relay_id": "rly_" + "0" * 32,
            "created": "2026-08-19T06:30:45Z",
            "mode": "compact",
            "disposition": "continue",
            "storage": "temp",
            "project_root": "/tmp/项目",
            "working_directory": "/tmp/项目",
            "focus": "resume café",
            "slug": "digest-vector",
            "x_note": "opaque α",
        }
        body = RELAY_ARTIFACT.normalize_text(
            " \r\n# Relay: Vector\r\n\r\nBody\u00a0\r\n "
        )
        self.assertEqual(body, "# Relay: Vector\n\nBody\u00a0\n")
        self.assertEqual(
            RELAY_ARTIFACT.compute_digest(metadata, body),
            "c121267cdf37ad4b09739860358e346fce79384dda7bcb9d7b9879bda61b7940",
        )

    def test_slug_normalization_removes_relay_control_words(self) -> None:
        self.assertEqual(RELAY_ARTIFACT.normalize_slug("relay cache"), "cache-context")
        self.assertEqual(RELAY_ARTIFACT.normalize_slug("handoff"), "session-context")

    def test_create_preserves_digest_significant_unicode_trailing_space(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            body = COMPACT_BODY.rstrip("\n") + "\u00a0\n"
            created = self.create(root, body)
            result = self.validate(Path(str(created["path"])))
            self.assertTrue(result["valid"])
            self.assertEqual(result["integrity"], "verified")

    def test_validate_can_return_body_from_the_validated_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            result = self.run_tool(
                "validate",
                str(created["path"]),
                "--json",
                "--include-body",
            )
            validation = json.loads(result.stdout)
            self.assertTrue(validation["valid"])
            self.assertEqual(validation["body"], RELAY_ARTIFACT.normalize_text(COMPACT_BODY))

    def test_stable_read_rejects_ctime_only_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay.md"
            path.write_text("stable bytes\n", encoding="utf-8")
            opened = path.stat()
            changed = mock.Mock(
                st_mode=opened.st_mode,
                st_dev=opened.st_dev,
                st_ino=opened.st_ino,
                st_size=opened.st_size,
                st_mtime_ns=opened.st_mtime_ns,
                st_ctime_ns=opened.st_ctime_ns + 1,
            )
            with mock.patch.object(
                RELAY_ARTIFACT.os,
                "fstat",
                side_effect=[opened, changed],
            ):
                with self.assertRaises(RELAY_ARTIFACT.RelayError) as raised:
                    RELAY_ARTIFACT.read_regular_file(path, "relay", 1024)
            self.assertIn("changed while it was being read", str(raised.exception))

    def test_atomic_publication_fails_closed_when_hard_links_are_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-test.md"
            with mock.patch.object(
                RELAY_ARTIFACT.os,
                "link",
                side_effect=OSError(errno.EOPNOTSUPP, "hard links unsupported"),
            ):
                with self.assertRaises(RELAY_ARTIFACT.RelayError) as raised:
                    RELAY_ARTIFACT.write_exclusive_atomic(path, b"complete artifact\n")
            self.assertIn("no non-atomic fallback", str(raised.exception))
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(temp_dir).glob(".relay-write-*.tmp")), [])

    def test_directory_fsync_limitation_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-test.md"
            with mock.patch.object(RELAY_ARTIFACT, "fsync_directory_fd", return_value=False):
                result = RELAY_ARTIFACT.write_exclusive_atomic(path, b"complete artifact\n")
            self.assertTrue(path.is_file())
            self.assertFalse(result["directory_fsynced"])
            self.assertTrue(any("crash durability" in warning for warning in result["warnings"]))

    def test_post_publication_durability_failure_is_reported_as_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-test.md"
            with mock.patch.object(RELAY_ARTIFACT, "fsync_directory_fd", return_value=False):
                result = RELAY_ARTIFACT.write_exclusive_atomic(path, b"complete artifact\n")
            self.assertTrue(path.is_file())
            self.assertEqual(result["publication"], "atomic-exclusive")
            self.assertFalse(result["directory_fsynced"])
            self.assertTrue(result["warnings"])

    def test_fsync_directory_closes_descriptor_when_fsync_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(
                RELAY_ARTIFACT.os,
                "fsync",
                side_effect=OSError(errno.EIO, "fsync failed"),
            ), mock.patch.object(
                RELAY_ARTIFACT.os,
                "close",
                wraps=os.close,
            ) as close_mock:
                self.assertFalse(RELAY_ARTIFACT.fsync_directory(Path(temp_dir)))
            close_mock.assert_called_once()

    def test_artifact_parent_swap_cannot_redirect_publication(self) -> None:
        if os.name != "posix":
            self.skipTest("directory-fd publication is unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relay_dir = root / ".relay"
            relay_dir.mkdir(mode=0o700)
            original = root / ".relay-original"
            outside = root / "outside"
            outside.mkdir()
            path = relay_dir / "relay-test.md"
            real_link = os.link

            def swap_then_link(*args: object, **kwargs: object) -> None:
                relay_dir.rename(original)
                relay_dir.symlink_to(outside, target_is_directory=True)
                real_link(*args, **kwargs)

            with mock.patch.object(RELAY_ARTIFACT.os, "link", side_effect=swap_then_link):
                with self.assertRaises(RELAY_ARTIFACT.RelayError) as raised:
                    RELAY_ARTIFACT.write_exclusive_atomic(path, b"complete artifact\n")
            self.assertIn("rolled back", str(raised.exception))
            self.assertEqual(list(outside.iterdir()), [])
            self.assertFalse((original / "relay-test.md").exists())

    def test_artifact_parent_disappearance_rolls_back_publication(self) -> None:
        if os.name != "posix":
            self.skipTest("directory-fd publication is unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relay_dir = root / ".relay"
            relay_dir.mkdir(mode=0o700)
            moved = root / ".relay-moved"
            path = relay_dir / "relay-test.md"
            real_link = os.link

            def move_then_link(*args: object, **kwargs: object) -> None:
                real_link(*args, **kwargs)
                relay_dir.rename(moved)

            with mock.patch.object(RELAY_ARTIFACT.os, "link", side_effect=move_then_link):
                with self.assertRaises(RELAY_ARTIFACT.RelayError) as raised:
                    RELAY_ARTIFACT.write_exclusive_atomic(path, b"complete artifact\n")
            self.assertIn("rolled back", str(raised.exception))
            self.assertFalse((moved / "relay-test.md").exists())

    def test_v2_body_may_reference_legacy_schema_without_misclassification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            body = COMPACT_BODY.replace(
                "The wrapper drops the reward field before the final write call.",
                "The old handoff used this literal metadata line:\n\n```yaml\nschema_version: 1\n```",
            )
            created = self.create(root, body)
            result = self.validate(Path(str(created["path"])))
            self.assertTrue(result["valid"])
            self.assertEqual(result["format"], "v2")

    def test_create_and_validate_full_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(
                root,
                FULL_BODY,
                "--mode",
                "full",
                "--disposition",
                "review",
                "--source-context-state",
                "compacted",
            )
            result = self.validate(Path(str(created["path"])))
            self.assertTrue(result["valid"])
            self.assertEqual(result["metadata"]["mode"], "full")
            self.assertEqual(result["metadata"]["disposition"], "review")
            self.assertEqual(result["metadata"]["source_context_state"], "compacted")

    def test_tampered_body_fails_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            path = Path(str(created["path"]))
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "wrapper drops the reward field",
                    "adapter drops the reward field",
                ),
                encoding="utf-8",
            )
            result = self.validate(path, expect=1)
            self.assertFalse(result["valid"])
            self.assertIn("artifact SHA-256 mismatch", result["errors"])

    def test_tampered_metadata_fails_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            path = Path(str(created["path"]))
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    'focus: "continue: reward logging #3"',
                    'focus: "continue another task"',
                ),
                encoding="utf-8",
            )
            result = self.validate(path, expect=1)
            self.assertIn("artifact SHA-256 mismatch", result["errors"])

    def test_repeated_passes_in_same_second_have_unique_ids_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self.create(root)
            second = self.create(root)
            self.assertNotEqual(first["relay_id"], second["relay_id"])
            self.assertNotEqual(first["artifact_sha256"], second["artifact_sha256"])
            self.assertNotEqual(first["path"], second["path"])
            self.assertTrue(Path(str(first["path"])).is_file())
            self.assertTrue(Path(str(second["path"])).is_file())

    def test_renamed_artifact_fails_filename_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            original = Path(str(created["path"]))
            renamed = original.with_name("relay-20260819T063045Z-reward-logging.md")
            original.rename(renamed)
            result = self.validate(renamed, expect=1)
            self.assertIn("filename does not match the Relay v2 naming contract", result["errors"])

    def test_secret_pattern_blocks_creation_without_leaking_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            secret = "sk-" + "A" * 24
            body_path = root / "body.md"
            body_path.write_text(COMPACT_BODY + f"\nToken: {secret}\n", encoding="utf-8")
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--project-root",
                str(root),
                "--output-dir",
                str(root / "out"),
                expect=2,
            )
            self.assertIn("OpenAI-style API key pattern", result.stderr)
            self.assertNotIn(secret, result.stderr)
            self.assertFalse((root / "out").exists())

    def test_secret_shaped_git_branch_blocks_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Relay Test"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "relay@example.invalid"],
                check=True,
            )
            tracked = root / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            secret = "ghp_" + "D" * 24
            subprocess.run(["git", "-C", str(root), "branch", "-m", secret], check=True)
            body_path = root / "body.md"
            body_path.write_text(COMPACT_BODY, encoding="utf-8")
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--mode",
                "compact",
                "--storage",
                "project",
                "--project-root",
                str(root),
                expect=2,
            )
            self.assertNotIn(secret, result.stderr)
            self.assertIn("finalized payload", result.stderr)
            self.assertFalse((root / ".relay").exists())

    def test_validation_does_not_echo_sensitive_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            path = Path(str(created["path"]))
            secret = "ghp_" + "C" * 24
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    'focus: "continue: reward logging #3"',
                    f'focus: "{secret}"',
                ),
                encoding="utf-8",
            )
            validation = self.run_tool("validate", str(path), "--json", expect=1)
            self.assertNotIn(secret, validation.stdout)
            result = json.loads(validation.stdout)
            self.assertEqual(result["metadata"], {})
            self.assertTrue(any("GitHub token" in error for error in result["errors"]))

    def test_full_mode_rejects_missing_fidelity_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            body_path = root / "body.md"
            body_path.write_text(COMPACT_BODY, encoding="utf-8")
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--mode",
                "full",
                "--project-root",
                str(root),
                "--output-dir",
                str(root / "out"),
                expect=2,
            )
            self.assertIn("Acceptance Criteria", result.stderr)
            self.assertIn("Progress Ledger", result.stderr)
            self.assertIn("Validation", result.stderr)
            self.assertIn("Resume Prompt", result.stderr)

    def test_headings_inside_fenced_code_do_not_satisfy_body_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            body_path = root / "body.md"
            body_path.write_text("```markdown\n" + COMPACT_BODY + "```\n", encoding="utf-8")
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--project-root",
                str(root),
                "--output-dir",
                str(root / "out"),
                expect=2,
            )
            self.assertIn("# Relay", result.stderr)
            self.assertIn("missing required headings", result.stderr)
            self.assertFalse((root / "out").exists())

    def test_duplicate_heading_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            body_path = root / "body.md"
            body_path.write_text(
                COMPACT_BODY + "\n## Goal\n\nA conflicting second goal.\n",
                encoding="utf-8",
            )
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--project-root",
                str(root),
                "--output-dir",
                str(root / "out"),
                expect=2,
            )
            self.assertIn("duplicate headings: Goal", result.stderr)

    def test_config_supplies_mode_and_storage_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relay_dir = root / ".relay"
            relay_dir.mkdir()
            (relay_dir / "config.json").write_text(
                '{"storage":"project","detail":"full"}',
                encoding="utf-8",
            )
            body_path = root / "body.md"
            body_path.write_text(FULL_BODY, encoding="utf-8")
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--project-root",
                str(root),
                "--created",
                "2026-08-19T06:30:45Z",
                "--json",
            )
            created = json.loads(result.stdout)
            self.assertEqual(created["mode"], "full")
            self.assertEqual(created["storage"], "project")
            self.assertEqual(Path(created["path"]).parent, relay_dir)

    def test_config_set_updates_and_preserves_unspecified_setting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self.run_tool(
                "config-set",
                "--project-root",
                str(root),
                "--storage",
                "temp",
                "--detail",
                "full",
                "--json",
            )
            self.assertEqual(json.loads(first.stdout)["publication"], "atomic-replace")
            second = self.run_tool(
                "config-set",
                "--project-root",
                str(root),
                "--detail",
                "compact",
                "--json",
            )
            updated = json.loads(second.stdout)
            self.assertEqual(updated["storage"], "temp")
            self.assertEqual(updated["detail"], "compact")
            config = json.loads((root / ".relay" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config, {"storage": "temp", "detail": "compact"})

            shown = self.run_tool(
                "config-get",
                "--project-root",
                str(root),
                "--json",
            )
            effective = json.loads(shown.stdout)
            self.assertEqual(effective["source"], "config")
            self.assertEqual(effective["storage"], "temp")
            self.assertEqual(effective["detail"], "compact")

    def test_config_get_reports_built_in_defaults_without_creating_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shown = self.run_tool(
                "config-get",
                "--project-root",
                str(root),
                "--json",
            )
            effective = json.loads(shown.stdout)
            self.assertEqual(effective["source"], "built-in")
            self.assertEqual(effective["storage"], "project")
            self.assertEqual(effective["detail"], "compact")
            self.assertFalse((root / ".relay").exists())

    def test_config_set_rejects_symlinked_relay_directory(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symbolic links are unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root / "outside"
            outside.mkdir()
            (root / ".relay").symlink_to(outside, target_is_directory=True)
            result = self.run_tool(
                "config-set",
                "--project-root",
                str(root),
                "--storage",
                "temp",
                expect=2,
            )
            self.assertIn("symbolic-link directory", result.stderr)
            self.assertEqual(list(outside.iterdir()), [])

    def test_config_temp_cleanup_does_not_remove_preexisting_name(self) -> None:
        if os.name != "posix":
            self.skipTest("directory-fd config operations are unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            opened = RELAY_ARTIFACT.open_secure_config_directory(root, create=True)
            assert opened is not None
            relay_dir, directory_stat, directory_fd = opened
            sentinel = relay_dir / ".relay-config-write-aaaaaaaaaaaaaaaaaaaaaaaa.tmp"
            sentinel.write_text("do not delete\n", encoding="utf-8")
            try:
                with mock.patch.object(
                    RELAY_ARTIFACT.secrets,
                    "token_hex",
                    return_value="a" * 24,
                ), self.assertRaises(RELAY_ARTIFACT.RelayError):
                    RELAY_ARTIFACT.write_config_at(
                        relay_dir,
                        directory_stat,
                        directory_fd,
                        b'{"storage":"temp","detail":"full"}\n',
                    )
            finally:
                os.close(directory_fd)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "do not delete\n")

    def test_project_root_swap_is_rejected_before_artifact_publication(self) -> None:
        if os.name != "posix":
            self.skipTest("directory identity checks are POSIX-focused")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            root.mkdir()
            original = Path(temp_dir) / "project-original"
            outside = Path(temp_dir) / "outside"
            outside.mkdir()
            root_stat = RELAY_ARTIFACT.directory_identity(root, "project root")
            destination = root / ".relay" / "relay-test.md"
            real_mkdir = Path.mkdir

            def mkdir_then_swap(path: Path, *args: object, **kwargs: object) -> None:
                real_mkdir(path, *args, **kwargs)
                if path == root / ".relay":
                    root.rename(original)
                    root.symlink_to(outside, target_is_directory=True)

            with mock.patch.object(Path, "mkdir", new=mkdir_then_swap):
                with self.assertRaises(RELAY_ARTIFACT.RelayError):
                    RELAY_ARTIFACT.write_exclusive_atomic(
                        destination,
                        b"complete artifact\n",
                        expected_project_root=root,
                        expected_project_root_stat=root_stat,
                    )
            self.assertFalse((outside / ".relay" / "relay-test.md").exists())
            self.assertFalse((original / ".relay" / "relay-test.md").exists())

    def test_project_root_resolution_errors_are_structured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = Path(temp_dir) / "loop"
            loop.symlink_to(loop)
            result = self.run_tool(
                "snapshot",
                "--project-root",
                str(loop),
                expect=2,
            )
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("cannot resolve project root path", result.stderr)

    def test_config_directory_fstat_failure_closes_descriptor(self) -> None:
        if os.name != "posix":
            self.skipTest("directory-fd operations are POSIX-focused")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(
                RELAY_ARTIFACT.os,
                "fstat",
                side_effect=OSError(errno.EIO, "fstat failed"),
            ), mock.patch.object(
                RELAY_ARTIFACT.os,
                "close",
                wraps=os.close,
            ) as close_mock:
                with self.assertRaises(RELAY_ARTIFACT.RelayError):
                    RELAY_ARTIFACT.open_secure_config_directory(root, create=True)
            self.assertGreaterEqual(close_mock.call_count, 1)

    def test_json_output_is_ascii_safe_after_non_ascii_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "café"
            root.mkdir()
            body_path = root / "body.md"
            body_path.write_text(COMPACT_BODY, encoding="utf-8")
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "ascii:strict"
            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "create",
                    "--body",
                    str(body_path),
                    "--slug",
                    "reward logging",
                    "--project-root",
                    str(root),
                    "--output-dir",
                    str(root / "out"),
                    "--created",
                    "2026-08-19T06:30:45Z",
                    "--json",
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("ascii", "replace"))
            payload = json.loads(result.stdout.decode("ascii"))
            self.assertTrue(Path(payload["path"]).is_file())

    def test_config_set_partial_updates_are_serialized(self) -> None:
        if os.name != "posix":
            self.skipTest("POSIX advisory locking is unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            commands = [
                [
                    sys.executable,
                    str(TOOL),
                    "config-set",
                    "--project-root",
                    str(root),
                    "--storage",
                    "temp",
                ],
                [
                    sys.executable,
                    str(TOOL),
                    "config-set",
                    "--project-root",
                    str(root),
                    "--detail",
                    "full",
                ],
            ]
            processes = [
                subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for command in commands
            ]
            for process in processes:
                stdout, stderr = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0, msg=f"stdout:\n{stdout}\nstderr:\n{stderr}")
            config = json.loads((root / ".relay" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config, {"storage": "temp", "detail": "full"})

    def test_config_parent_swap_cannot_redirect_write(self) -> None:
        if os.name != "posix":
            self.skipTest("directory-fd replacement is unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            opened = RELAY_ARTIFACT.open_secure_config_directory(root, create=True)
            assert opened is not None
            relay_dir, directory_stat, directory_fd = opened
            original = root / ".relay-original"
            outside = root / "outside"
            outside.mkdir()
            relay_dir.rename(original)
            relay_dir.symlink_to(outside, target_is_directory=True)
            try:
                with self.assertRaises(RELAY_ARTIFACT.RelayError):
                    RELAY_ARTIFACT.write_config_at(
                        relay_dir,
                        directory_stat,
                        directory_fd,
                        b'{"storage":"temp","detail":"full"}\n',
                    )
            finally:
                os.close(directory_fd)
            self.assertEqual(list(outside.iterdir()), [])
            self.assertFalse((original / "config.json").exists())

    def test_config_directory_disappearance_returns_relay_error(self) -> None:
        if os.name != "posix":
            self.skipTest("directory-fd config operations are unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            real_mkdir = Path.mkdir

            def create_then_remove(path: Path, *args: object, **kwargs: object) -> None:
                real_mkdir(path, *args, **kwargs)
                path.rmdir()

            with mock.patch.object(Path, "mkdir", new=create_then_remove):
                with self.assertRaises(RELAY_ARTIFACT.RelayError) as raised:
                    RELAY_ARTIFACT.open_secure_config_directory(root, create=True)
            self.assertIn("disappeared", str(raised.exception))

    def test_config_post_replace_path_loss_reports_committed_state(self) -> None:
        if os.name != "posix":
            self.skipTest("directory-fd config operations are unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            opened = RELAY_ARTIFACT.open_secure_config_directory(root, create=True)
            assert opened is not None
            relay_dir, directory_stat, directory_fd = opened
            moved = root / ".relay-moved"
            real_replace = os.replace

            def replace_then_move(*args: object, **kwargs: object) -> None:
                real_replace(*args, **kwargs)
                relay_dir.rename(moved)

            try:
                with mock.patch.object(
                    RELAY_ARTIFACT.os,
                    "replace",
                    side_effect=replace_then_move,
                ):
                    with self.assertRaises(RELAY_ARTIFACT.RelayError) as raised:
                        RELAY_ARTIFACT.write_config_at(
                            relay_dir,
                            directory_stat,
                            directory_fd,
                            b'{"storage":"temp","detail":"full"}\n',
                        )
            finally:
                os.close(directory_fd)
            self.assertIn("atomically replaced", str(raised.exception))
            self.assertTrue((moved / "config.json").is_file())

    def test_malformed_config_type_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relay_dir = root / ".relay"
            relay_dir.mkdir()
            (relay_dir / "config.json").write_text(
                '{"storage":[],"detail":"compact"}',
                encoding="utf-8",
            )
            body_path = root / "body.md"
            body_path.write_text(COMPACT_BODY, encoding="utf-8")
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--project-root",
                str(root),
                expect=2,
            )
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("invalid Relay storage setting", result.stderr)

    def test_null_config_value_is_invalid_not_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            relay_dir = root / ".relay"
            relay_dir.mkdir()
            (relay_dir / "config.json").write_text(
                '{"storage":null,"detail":"compact"}',
                encoding="utf-8",
            )
            result = self.run_tool(
                "config-get",
                "--project-root",
                str(root),
                "--json",
                expect=2,
            )
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("invalid Relay storage setting", result.stderr)

    def test_v1_fixture_is_compatible_but_unverified(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "compact-relay.md"
        result = self.validate(fixture)
        self.assertTrue(result["valid"])
        self.assertEqual(result["format"], "v1")
        self.assertEqual(result["integrity"], "unverified")
        self.assertTrue(result["warnings"])

    def test_v1_full_fixture_is_compatible_without_v2_full_sections(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "full-relay.md"
        result = self.validate(fixture)
        self.assertTrue(result["valid"])
        self.assertEqual(result["format"], "v1")
        self.assertEqual(result["metadata"]["mode"], "full")
        self.assertEqual(result["integrity"], "unverified")

    def test_v1_compact_fixture_without_optional_next_step_remains_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = (ROOT / "tests" / "fixtures" / "compact-relay.md").read_text(
                encoding="utf-8"
            )
            source = re.sub(
                r"\n## Explicit Next Step\n.*?(?=\n## References)",
                "",
                source,
                flags=re.DOTALL,
            )
            path = Path(temp_dir) / "relay-v1-no-next-step.md"
            path.write_text(source, encoding="utf-8")
            result = self.validate(path)
            self.assertTrue(result["valid"])
            self.assertEqual(result["format"], "v1")

    def test_legacy_fixture_is_compatible_but_unverified(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "handoff-legacy-example.md"
        result = self.validate(fixture)
        self.assertTrue(result["valid"])
        self.assertEqual(result["format"], "legacy")
        self.assertEqual(result["integrity"], "unverified")

    def test_legacy_secret_pattern_blocks_automatic_use(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "handoff-secret.md"
            secret = "ghp_" + "B" * 24
            path.write_text(f"# Legacy handoff\n\nToken: {secret}\n", encoding="utf-8")
            result = self.validate(path, expect=1)
            self.assertFalse(result["valid"])
            self.assertTrue(any("GitHub token" in error for error in result["errors"]))

    def test_unknown_schema_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-20260819T063045Z-reward-logging-0123456789ab.md"
            path.write_text(
                "---\nschema_version: 99\n---\n\n" + COMPACT_BODY,
                encoding="utf-8",
            )
            result = self.validate(path, expect=1)
            self.assertIn("unsupported schema_version: 99", result["errors"])

    def test_non_integer_schema_version_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-20260819T063045Z-reward-logging-0123456789ab.md"
            path.write_text("---\nschema_version: 2.0\n---\n\n" + COMPACT_BODY, encoding="utf-8")
            result = self.validate(path, expect=1)
            self.assertTrue(any("unsupported schema_version" in error for error in result["errors"]))

    def test_nonstandard_json_constant_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-20260819T063045Z-reward-logging-0123456789ab.md"
            path.write_text(
                '---\nschema_version: 2\nfocus: NaN\n---\n\n' + COMPACT_BODY,
                encoding="utf-8",
            )
            result = self.validate(path, expect=1)
            self.assertIn("not valid JSON", result["errors"][0])

    def test_invalid_parent_id_is_rejected_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            body_path = root / "body.md"
            body_path.write_text(COMPACT_BODY, encoding="utf-8")
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--parent-relay-id",
                "not-a-relay-id",
                "--project-root",
                str(root),
                "--output-dir",
                str(root / "out"),
                expect=2,
            )
            self.assertIn("--parent-relay-id", result.stderr)
            self.assertFalse((root / "out").exists())

    def test_final_artifact_size_is_checked_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prefix = COMPACT_BODY.rstrip("\n") + "\n"
            padding = "x" * (RELAY_ARTIFACT.MAX_ARTIFACT_BYTES - len(prefix.encode("utf-8")))
            body_path = root / "body.md"
            body_path.write_text(prefix + padding, encoding="utf-8")
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--project-root",
                str(root),
                "--output-dir",
                str(root / "out"),
                expect=2,
            )
            self.assertIn("final Relay artifact exceeds", result.stderr)
            self.assertFalse((root / "out").exists())

    def test_undeclared_metadata_field_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            path = Path(str(created["path"]))
            text = path.read_text(encoding="utf-8").replace(
                'focus: "continue: reward logging #3"',
                'focus: "continue: reward logging #3"\nfuture_action: "auto-approve"',
            )
            path.write_text(text, encoding="utf-8")
            result = self.validate(path, expect=1)
            self.assertTrue(any("unknown metadata field" in error for error in result["errors"]))

    def test_information_only_string_extension_is_digest_covered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            path = Path(str(created["path"]))
            metadata, body = RELAY_ARTIFACT.parse_frontmatter(path.read_text(encoding="utf-8"))
            metadata["x_fixture_note"] = "receiver may ignore this note"
            unsigned = dict(metadata)
            del unsigned["artifact_sha256"]
            digest = RELAY_ARTIFACT.compute_digest(unsigned, body)
            metadata["artifact_sha256"] = "sha256:" + digest
            renamed = path.with_name(
                path.name[:-15] + digest[:12] + ".md"
            )
            renamed.write_text(RELAY_ARTIFACT.render_artifact(metadata, body), encoding="utf-8")
            path.unlink()

            result = self.validate(renamed)
            self.assertTrue(result["valid"])
            self.assertEqual(result["metadata"]["x_fixture_note"], "receiver may ignore this note")

    def test_structured_extension_value_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            path = Path(str(created["path"]))
            text = path.read_text(encoding="utf-8").replace(
                'focus: "continue: reward logging #3"',
                'focus: "continue: reward logging #3"\nx_numbers: {"small":1e-6}',
            )
            path.write_text(text, encoding="utf-8")
            result = self.validate(path, expect=1)
            self.assertTrue(any("extension metadata field" in error for error in result["errors"]))

    def test_nested_duplicate_json_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-20260819T063045Z-reward-logging-0123456789ab.md"
            path.write_text(
                '---\nschema_version: 2\nx_note: {"same":1,"same":2}\n---\n\n'
                + COMPACT_BODY,
                encoding="utf-8",
            )
            result = self.validate(path, expect=1)
            self.assertIn("not valid JSON", result["errors"][0])

    def test_lone_unicode_surrogate_fails_closed_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-20260819T063045Z-reward-logging-0123456789ab.md"
            path.write_text(
                '---\nschema_version: 2\nx_note: "\\ud800"\n---\n\n' + COMPACT_BODY,
                encoding="utf-8",
            )
            result = self.run_tool("validate", str(path), "--json", expect=1)
            self.assertNotIn("Traceback", result.stderr)
            parsed = json.loads(result.stdout)
            self.assertIn("not valid JSON", parsed["errors"][0])

    def test_deep_json_value_fails_closed_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-20260819T063045Z-reward-logging-0123456789ab.md"
            nested = "[" * 2000 + '"value"' + "]" * 2000
            path.write_text(
                "---\nschema_version: 2\nx_note: " + nested + "\n---\n\n" + COMPACT_BODY,
                encoding="utf-8",
            )
            result = self.run_tool("validate", str(path), "--json", expect=1)
            self.assertNotIn("Traceback", result.stderr)
            parsed = json.loads(result.stdout)
            self.assertIn("not valid JSON", parsed["errors"][0])

    def test_symlink_relay_fails_closed(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symbolic links are unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            created = self.create(root)
            target = Path(str(created["path"]))
            link = root / "relay-link.md"
            link.symlink_to(target)
            result = self.validate(link, expect=1)
            self.assertIn("relay path is a symbolic link", result["errors"])

    def test_non_regular_relay_path_fails_without_opening_it(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFOs are unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            fifo = Path(temp_dir) / "relay-fifo.md"
            os.mkfifo(fifo)
            result = self.validate(fifo, expect=1)
            self.assertIn("relay path is not a regular file", result["errors"])

    def test_project_storage_rejects_symlink_relay_directory(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symbolic links are unavailable")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root / "outside"
            outside.mkdir()
            (root / ".relay").symlink_to(outside, target_is_directory=True)
            body_path = root / "body.md"
            body_path.write_text(COMPACT_BODY, encoding="utf-8")
            result = self.run_tool(
                "create",
                "--body",
                str(body_path),
                "--slug",
                "reward logging",
                "--storage",
                "project",
                "--project-root",
                str(root),
                expect=2,
            )
            self.assertIn("symbolic-link directory", result.stderr)
            self.assertEqual(list(outside.iterdir()), [])

    def test_truncated_frontmatter_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "relay-20260819T063045Z-reward-logging-0123456789ab.md"
            path.write_text('---\nschema_version: 2\nrelay_id: "rly_deadbeef"\n', encoding="utf-8")
            result = self.validate(path, expect=1)
            self.assertIn("unterminated YAML frontmatter", result["errors"])

    def test_snapshot_reports_git_workspace_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Relay Test"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "relay@example.invalid"],
                check=True,
            )
            tracked = root / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)

            tracked.write_text("changed\n", encoding="utf-8")
            staged = root / "staged.txt"
            staged.write_text("staged\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "staged.txt"], check=True)
            (root / "untracked.txt").write_text("new\n", encoding="utf-8")

            result = self.run_tool("snapshot", "--project-root", str(root))
            snapshot = json.loads(result.stdout)
            self.assertTrue(snapshot["git"])
            self.assertTrue(snapshot["workspace_dirty"])
            self.assertEqual(snapshot["staged_files"], ["staged.txt"])
            self.assertEqual(snapshot["unstaged_files"], ["tracked.txt"])
            self.assertEqual(snapshot["untracked_files"], ["untracked.txt"])
            self.assertEqual(snapshot["conflicted_files"], [])

    def test_snapshot_handles_unborn_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "first.txt").write_text("first\n", encoding="utf-8")
            result = self.run_tool("snapshot", "--project-root", str(root))
            snapshot = json.loads(result.stdout)
            self.assertTrue(snapshot["git"])
            self.assertIsNone(snapshot["commit"])
            self.assertTrue(snapshot["workspace_dirty"])
            self.assertEqual(snapshot["untracked_files"], ["first.txt"])

    def test_snapshot_reports_unknown_dirty_state_when_git_queries_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Relay Test"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "relay@example.invalid"],
                check=True,
            )
            tracked = root / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            (root / ".git" / "index").write_bytes(b"corrupt index")

            result = self.run_tool("snapshot", "--project-root", str(root))
            snapshot = json.loads(result.stdout)
            self.assertTrue(snapshot["git"])
            self.assertIsNotNone(snapshot["commit"])
            self.assertFalse(snapshot["git_evidence_complete"])
            self.assertIsNone(snapshot["workspace_dirty"])
            self.assertTrue(snapshot["git_errors"])

    def test_explicit_nested_project_root_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            nested = repository / "packages" / "service"
            nested.mkdir(parents=True)
            result = self.run_tool("snapshot", "--project-root", str(nested))
            snapshot = json.loads(result.stdout)
            self.assertEqual(snapshot["project_root"], str(nested.resolve()))
            self.assertTrue(snapshot["git"])

    def test_nested_project_root_uses_whole_worktree_git_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            nested = repository / "packages" / "service"
            nested.mkdir(parents=True)
            (repository / "root-untracked.txt").write_text("new\n", encoding="utf-8")
            result = self.run_tool("snapshot", "--project-root", str(nested))
            snapshot = json.loads(result.stdout)
            self.assertEqual(snapshot["project_root"], str(nested.resolve()))
            self.assertEqual(snapshot["git_root"], str(repository.resolve()))
            self.assertTrue(snapshot["workspace_dirty"])
            self.assertEqual(snapshot["untracked_files"], ["root-untracked.txt"])

    def test_year_before_1000_uses_four_digit_canonical_timestamp(self) -> None:
        canonical, filename = RELAY_ARTIFACT.parse_created("0001-01-02T03:04:05Z")
        self.assertEqual(canonical, "0001-01-02T03:04:05Z")
        self.assertEqual(filename, "00010102T030405Z")

    def test_out_of_range_timezone_conversion_returns_structured_error(self) -> None:
        for value in (
            "0001-01-01T00:00:00+14:00",
            "9999-12-31T23:59:59-14:00",
        ):
            with self.subTest(value=value):
                with self.assertRaises(RELAY_ARTIFACT.RelayError):
                    RELAY_ARTIFACT.parse_created(value)

    def test_non_utf8_git_ref_does_not_crash_snapshot(self) -> None:
        if os.name != "posix":
            self.skipTest("raw-byte Git refs require POSIX paths")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Relay Test"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "relay@example.invalid"],
                check=True,
            )
            tracked = root / "tracked.txt"
            tracked.write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"]).strip()
            raw_ref = os.fsencode(root / ".git" / "refs" / "heads") + b"/nonutf8-\xff"
            fd = os.open(raw_ref, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(fd, head + b"\n")
            finally:
                os.close(fd)
            (root / ".git" / "HEAD").write_bytes(b"ref: refs/heads/nonutf8-\xff\n")

            result = self.run_tool("snapshot", "--project-root", str(root))
            snapshot = json.loads(result.stdout)
            self.assertTrue(snapshot["git"])
            self.assertIn("nonutf8-", snapshot["branch"])


if __name__ == "__main__":
    unittest.main()
