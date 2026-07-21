"""Fail-first end-to-end contract for the Phase 1 CLI-to-state path."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_DEFAULTS = (
    PROJECT_ROOT / "packages" / "ba-tools" / "src" / "ba_tools" / "state" / "resources" / "defaults"
)
STATE_FILES = (
    ".ba-ops/config.json",
    ".ba-ops/coverage-policy.json",
    ".ba-ops/business-goals.json",
)


def _expected_dev_python() -> Path:
    if sys.platform == "win32":
        return PROJECT_ROOT / ".ba-tools-runtime" / "dev" / "Scripts" / "python.exe"
    return PROJECT_ROOT / ".ba-tools-runtime" / "dev" / "bin" / "python"


def _canonical_json(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


def _invoke(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    assert Path(sys.executable).resolve() == _expected_dev_python().resolve()
    return subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "ba_tools", *arguments],
        cwd=cwd,
        capture_output=True,
        check=False,
        timeout=10,
    )


def _assert_success(
    result: subprocess.CompletedProcess[bytes],
    expected: dict[str, object],
    behavior: str,
) -> None:
    assert result.returncode == 0, (
        f"missing {behavior}: expected exit 0, got {result.returncode}; "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stderr == b"", (
        f"missing one-stream {behavior}: expected empty stderr, got {result.stderr!r}"
    )
    assert result.stdout == _canonical_json(expected), (
        f"missing exact {behavior} success envelope: got {result.stdout!r}"
    )
    assert json.loads(result.stdout.decode("utf-8")) == expected


def _make_unicode_repo_and_external_cwd(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "Dự án BA có dấu và khoảng trắng"
    external_cwd = tmp_path / "thư mục gọi bên ngoài"
    repo_root.mkdir()
    external_cwd.mkdir()
    assert external_cwd not in repo_root.parents
    assert repo_root not in external_cwd.parents
    return repo_root, external_cwd


def test_repo_root_init_walking_skeleton(tmp_path: Path) -> None:
    repo_root, external_cwd = _make_unicode_repo_and_external_cwd(tmp_path)

    result = _invoke(external_cwd, "--repo-root", str(repo_root), "init")

    _assert_success(
        result,
        {
            "command": "init",
            "data": {"changed": True, "created": list(STATE_FILES)},
            "ok": True,
            "schema_version": 1,
            "warnings": [],
        },
        "init command/state behavior",
    )
    assert sorted(
        path.relative_to(repo_root).as_posix()
        for path in repo_root.rglob("*")
        if path.is_file()
    ) == sorted(STATE_FILES)
    for relative_path in STATE_FILES:
        source = PACKAGE_DEFAULTS / Path(relative_path).name
        generated = repo_root / relative_path
        assert generated.read_bytes() == source.read_bytes()


def test_repo_root_init_is_idempotent(tmp_path: Path) -> None:
    repo_root, external_cwd = _make_unicode_repo_and_external_cwd(tmp_path)
    first = _invoke(external_cwd, "--repo-root", str(repo_root), "init")
    _assert_success(
        first,
        {
            "command": "init",
            "data": {"changed": True, "created": list(STATE_FILES)},
            "ok": True,
            "schema_version": 1,
            "warnings": [],
        },
        "initial init command/state behavior",
    )
    snapshots = {
        relative_path: (
            (repo_root / relative_path).read_bytes(),
            (repo_root / relative_path).stat().st_mtime_ns,
        )
        for relative_path in STATE_FILES
    }

    second = _invoke(external_cwd, "--repo-root", str(repo_root), "init")

    _assert_success(
        second,
        {
            "command": "init",
            "data": {"changed": False, "created": []},
            "ok": True,
            "schema_version": 1,
            "warnings": [],
        },
        "idempotent init behavior",
    )
    for relative_path, (expected_bytes, expected_mtime) in snapshots.items():
        generated = repo_root / relative_path
        assert generated.read_bytes() == expected_bytes
        assert generated.stat().st_mtime_ns == expected_mtime


def test_cli_version_is_exactly_0_1_0(tmp_path: Path) -> None:
    _, external_cwd = _make_unicode_repo_and_external_cwd(tmp_path)

    result = _invoke(external_cwd, "--version")

    _assert_success(
        result,
        {
            "command": "version",
            "data": {"version": "0.1.0"},
            "ok": True,
            "schema_version": 1,
            "warnings": [],
        },
        "exact 0.1.0 version behavior",
    )
