"""Permanent equality contract for approved binary dependency locks."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from scripts.verify_dependency_locks import (
    evaluate_target_markers,
    parse_approval_summary,
    parse_lock,
    verify_exact_lock_sets,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
APPROVAL_PATH = (
    PROJECT_ROOT
    / ".planning"
    / "phases"
    / "BAOPS-01-harness-foundation"
    / "01-01-SUMMARY.md"
)
RUNTIME_LOCK_PATH = PROJECT_ROOT / "packages" / "ba-tools" / "requirements.lock"
DEV_LOCK_PATH = PROJECT_ROOT / "packages" / "ba-tools" / "requirements-dev.lock"
COMPARATOR_PATH = PROJECT_ROOT / "scripts" / "verify_dependency_locks.py"
EXACT_HASHED_ENTRY = re.compile(
    r"^[A-Za-z0-9_.-]+==[^\s;]+(?:\s*;\s*.+?)?(?:\s+--hash=sha256:[0-9a-f]{64})+$"
)


def _contract() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return (
        parse_approval_summary(APPROVAL_PATH),
        parse_lock(RUNTIME_LOCK_PATH),
        parse_lock(DEV_LOCK_PATH),
    )


def _logical_requirement_lines(text: str) -> list[str]:
    logical: list[str] = []
    pending = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if (
            not line
            or line.startswith("#")
            or line.startswith("--only-")
            or line == "--require-hashes"
        ):
            continue
        if line.endswith("\\"):
            pending += line[:-1].rstrip() + " "
        else:
            logical.append((pending + line).strip())
            pending = ""
    assert pending == ""
    return logical


def test_lock_sets_equal_approved_target_closures(dev_python: Path) -> None:
    approval, runtime_entries, development_entries = _contract()

    result = subprocess.run(
        [
            str(dev_python),
            str(COMPARATOR_PATH),
            "--approval",
            str(APPROVAL_PATH),
            "--runtime-lock",
            str(RUNTIME_LOCK_PATH),
            "--dev-lock",
            str(DEV_LOCK_PATH),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stderr == b""
    report = json.loads(result.stdout.decode("utf-8"))
    assert report["ok"] is True
    assert report["targets_verified"] == 16
    for target in approval["targets"]:
        entries = runtime_entries if target.scope == "Runtime" else development_entries
        assert evaluate_target_markers(entries, target) == target.expected


def test_lock_unions_equal_approved_unions() -> None:
    approval, runtime_entries, development_entries = _contract()

    runtime_union = frozenset(entry.pin for entry in runtime_entries.values())
    development_union = frozenset(entry.pin for entry in development_entries.values())

    assert runtime_union == approval["closure_sets"]["R-WIN"]
    assert development_union == approval["closure_sets"]["D-WIN"]
    assert len(runtime_union) == 13
    assert len(development_union) == 17


def test_no_unapproved_or_source_packages() -> None:
    approval, runtime_entries, development_entries = _contract()

    report = verify_exact_lock_sets(approval, runtime_entries, development_entries)
    approved_union = approval["closure_sets"]["D-WIN"]
    actual_union = frozenset(entry.pin for entry in development_entries.values())

    assert report["missing"] == 0
    assert report["extra"] == 0
    assert actual_union == approved_union
    assert all(
        filename.endswith(".whl")
        for filenames in approval["artifact_names"].values()
        for filename in filenames
    )
    for lock_path in (RUNTIME_LOCK_PATH, DEV_LOCK_PATH):
        lock_text = lock_path.read_text(encoding="utf-8")
        assert "://" not in lock_text
        assert ".tar.gz" not in lock_text
        assert ".zip" not in lock_text


def test_every_lock_entry_is_exact_and_hashed() -> None:
    approval, runtime_entries, development_entries = _contract()

    for lock_path, entries in (
        (RUNTIME_LOCK_PATH, runtime_entries),
        (DEV_LOCK_PATH, development_entries),
    ):
        text = lock_path.read_text(encoding="utf-8")
        logical_entries = _logical_requirement_lines(text)
        assert len(logical_entries) == len(entries)
        assert all(EXACT_HASHED_ENTRY.fullmatch(line) for line in logical_entries)
        for entry in entries.values():
            assert entry.hashes == approval["artifact_hashes"][entry.pin]
            assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in entry.hashes)


def test_approved_substitutions_are_consumed() -> None:
    approval, runtime_entries, development_entries = _contract()
    approval_text = APPROVAL_PATH.read_text(encoding="utf-8")
    substitution_section = approval_text.split("## Approved Substitutions", 1)[1].split(
        "## Target Matrix", 1
    )[0]

    assert "SUBSTITUTIONS: none" in substitution_section
    assert approval["runtime_direct"] <= {
        entry.pin for entry in runtime_entries.values()
    }
    assert approval["development_direct"] <= {
        entry.pin for entry in development_entries.values()
    }
