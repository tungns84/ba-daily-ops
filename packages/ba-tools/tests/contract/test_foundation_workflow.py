"""Fast source contracts for the ordinary foundation workflow."""
from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "foundation.yml"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
USES = re.compile(r"^\s*uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE)


def _source() -> str:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "\t" not in source
    assert "\r" not in source
    return source


def _top_level_section(source: str, start: str, end: str) -> str:
    before, separator, remainder = source.partition(f"{start}:\n")
    assert separator and before is not None
    section, separator, _after = remainder.partition(f"{end}:\n")
    assert separator
    return section


def test_workflow_declares_read_only_permissions() -> None:
    source = _source()
    permissions = _top_level_section(source, "permissions", "jobs")

    assert permissions.strip() == "contents: read"
    assert source.count("\npermissions:\n") == 1
    assert not re.search(r"^\s{2,}permissions:", source, re.MULTILINE)


def test_no_job_elevates_permissions() -> None:
    source = _source().lower()
    write_capable = (
        "actions: write",
        "checks: write",
        "contents: write",
        "deployments: write",
        "id-token: write",
        "issues: write",
        "packages: write",
        "pull-requests: write",
        "security-events: write",
        "statuses: write",
    )

    assert all(permission not in source for permission in write_capable)
    assert "secrets." not in source
    assert "self-hosted" not in source


def test_workflow_matrix_has_six_required_jobs() -> None:
    source = _source()
    include, separator, _steps = source.partition("    steps:\n")
    assert separator
    rows = set(
        re.findall(
            r"- os: (windows-latest|macos-latest|ubuntu-latest)\n"
            r"\s+platform: (windows|macos|linux)\n"
            r'\s+python: "(3\.11|3\.14)"',
            include,
        )
    )

    assert rows == {
        ("windows-latest", "windows", "3.11"),
        ("windows-latest", "windows", "3.14"),
        ("macos-latest", "macos", "3.11"),
        ("macos-latest", "macos", "3.14"),
        ("ubuntu-latest", "linux", "3.11"),
        ("ubuntu-latest", "linux", "3.14"),
    }
    assert "runs-on: ${{ matrix.os }}" in source
    assert "python-version: ${{ matrix.python }}" in source


def test_actions_are_full_sha_pinned() -> None:
    actions = USES.findall(_source())

    assert {action for action, _revision in actions} == {
        "actions/checkout",
        "actions/setup-python",
        "actions/upload-artifact",
    }
    assert actions
    assert all(FULL_SHA.fullmatch(revision) for _action, revision in actions)


def test_jobs_use_locked_development_interpreter() -> None:
    source = _source()

    assert "packages/ba-tools/requirements-dev.lock" in source
    assert "--require-hashes" in source
    assert "--only-binary=:all:" in source
    assert "--no-deps --no-build-isolation" in source
    assert "--no-index --find-links" in source
    assert source.count(r".\.ba-tools-runtime\dev\Scripts\python.exe") >= 4
    assert source.count("./.ba-tools-runtime/dev/bin/python") >= 4
    assert "-m pytest packages/ba-tools/tests -q -m 'not online_install'" in source
    assert "-m ruff check packages/ba-tools/src packages/ba-tools/tests installer scripts" in source


def test_jobs_run_offline_smoke() -> None:
    source = _source()

    assert source.count("scripts/smoke_foundation.py") == 2
    assert "--repo-source" in source
    assert "--work-dir" in source
    assert "--wheelhouse" in source
    assert "--expected-platform" in source
    assert "--evidence-out" in source
    assert "ba smoke — Dự án có khoảng trắng" in source
    assert "packages/ba-tools/requirements.lock" in source
    assert "curl " not in source.lower()
    assert "invoke-webrequest" not in source.lower()


def test_windows_job_uses_powershell_51() -> None:
    source = _source()
    windows_steps = [
        section for section in source.split("      - name: ") if "runner.os == 'Windows'" in section
    ]

    assert windows_steps
    assert any("shell: powershell" in section for section in windows_steps)
    assert any("$PSVersionTable.PSEdition -ne 'Desktop'" in section for section in windows_steps)
    assert any("[version]'5.1'" in section for section in windows_steps)
    assert any("powershell.exe" in section for section in windows_steps)
    assert "windows-2019" not in source
    assert "macos-12" not in source


def test_workflow_source_makes_no_remote_success_claim() -> None:
    source = _source().lower()

    for claim in (
        "remote success",
        "matrix passed",
        "all jobs passed",
        "windows 10 evidence",
        "macos 12 evidence",
    ):
        assert claim not in source
