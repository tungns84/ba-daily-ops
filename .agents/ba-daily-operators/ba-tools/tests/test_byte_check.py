"""Tests for ba-tools byte-check (GATE-04, CDX-04).

Verifies the 32768 B Codex silent-truncation gate:
- Files strictly < limit pass (exit 0)
- Files >= limit fail (exit 2, EXCEEDS_LIMIT)
- Missing files produce FILE_NOT_FOUND failure
- --limit override is respected
- Path-escape attempts rejected with PATH_ESCAPE failure (T-1-01)

All tests invoke `python -m ba_tools byte-check` as a subprocess.
Note: --repo-root is a global argument that must precede the subcommand.
"""

import json
import subprocess
import sys
from pathlib import Path

CODEX_LIMIT = 32768  # bytes — DESIGN §7 hard limit


def _run_byte_check(repo_root: str, *args):
    """Run `python -m ba_tools --repo-root <root> byte-check <args>` and return CompletedProcess.

    --repo-root is a global argument (before the subcommand) per __main__.py architecture.
    """
    return subprocess.run(
        [sys.executable, "-m", "ba_tools", "--repo-root", repo_root, "byte-check", *args],
        capture_output=True,
        text=True,
    )


# ── File size boundary tests ──────────────────────────────────────────────────

def test_file_under_limit_passes(tmp_path):
    """byte-check exits 0 for a file of 32767 bytes (strictly < 32768)."""
    f = tmp_path / "under.md"
    f.write_bytes(b"x" * 32767)
    result = _run_byte_check(str(tmp_path), "under.md")
    assert result.returncode == 0, (
        f"Expected exit 0 for 32767-byte file. stderr={result.stderr!r}"
    )
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["failures"] == []


def test_file_at_limit_fails(tmp_path):
    """byte-check exits 2 with EXCEEDS_LIMIT for a file of exactly 32768 bytes."""
    f = tmp_path / "at_limit.md"
    f.write_bytes(b"x" * 32768)
    result = _run_byte_check(str(tmp_path), "at_limit.md")
    assert result.returncode == 2, (
        f"Expected exit 2 for 32768-byte file. stderr={result.stderr!r}"
    )
    stderr_data = json.loads(result.stderr)
    assert stderr_data["ok"] is False
    failure_codes = [f["code"] for f in stderr_data["failures"]]
    assert "EXCEEDS_LIMIT" in failure_codes, (
        f"Expected EXCEEDS_LIMIT failure, got: {failure_codes}"
    )


def test_file_over_limit_fails(tmp_path):
    """byte-check exits 2 with EXCEEDS_LIMIT for a file of 33000 bytes."""
    f = tmp_path / "over.md"
    f.write_bytes(b"x" * 33000)
    result = _run_byte_check(str(tmp_path), "over.md")
    assert result.returncode == 2
    stderr_data = json.loads(result.stderr)
    failure_codes = [f["code"] for f in stderr_data["failures"]]
    assert "EXCEEDS_LIMIT" in failure_codes


# ── Missing file test ─────────────────────────────────────────────────────────

def test_missing_file_fails(tmp_path):
    """byte-check exits 2 with FILE_NOT_FOUND failure for a non-existent path."""
    result = _run_byte_check(str(tmp_path), "does_not_exist.md")
    assert result.returncode == 2, (
        f"Expected exit 2 for missing file. stderr={result.stderr!r}"
    )
    stderr_data = json.loads(result.stderr)
    assert stderr_data["ok"] is False
    failure_codes = [f["code"] for f in stderr_data["failures"]]
    assert "FILE_NOT_FOUND" in failure_codes, (
        f"Expected FILE_NOT_FOUND failure, got: {failure_codes}"
    )


# ── --limit override test ─────────────────────────────────────────────────────

def test_custom_limit_respected(tmp_path):
    """byte-check respects --limit override: 37000-byte file passes with --limit 38000."""
    f = tmp_path / "workflow.md"
    f.write_bytes(b"x" * 37000)
    result = _run_byte_check(str(tmp_path), "--limit", "38000", "workflow.md")
    assert result.returncode == 0, (
        f"Expected exit 0 for 37000-byte file with --limit 38000. stderr={result.stderr!r}"
    )
    data = json.loads(result.stdout)
    assert data["ok"] is True


def test_custom_limit_enforced(tmp_path):
    """byte-check fails a file that exceeds the custom --limit."""
    f = tmp_path / "big.md"
    f.write_bytes(b"x" * 38001)
    result = _run_byte_check(str(tmp_path), "--limit", "38000", "big.md")
    assert result.returncode == 2
    stderr_data = json.loads(result.stderr)
    failure_codes = [f["code"] for f in stderr_data["failures"]]
    assert "EXCEEDS_LIMIT" in failure_codes


# ── Path-escape test (T-1-01) ─────────────────────────────────────────────────

def test_path_escape_rejected(tmp_path):
    """A ../outside.md path argument is rejected with PATH_ESCAPE failure (T-1-01)."""
    # Create a file OUTSIDE tmp_path to ensure the path actually exists if resolved
    outside = tmp_path.parent / "outside.md"
    outside.write_bytes(b"x" * 100)
    try:
        result = _run_byte_check(str(tmp_path), "../outside.md")
        assert result.returncode == 2, (
            f"Expected exit 2 for path-escape. stderr={result.stderr!r}"
        )
        stderr_data = json.loads(result.stderr)
        failure_codes = [f["code"] for f in stderr_data["failures"]]
        assert "PATH_ESCAPE" in failure_codes, (
            f"Expected PATH_ESCAPE failure, got: {failure_codes}"
        )
    finally:
        if outside.exists():
            outside.unlink()


# ── Result structure test ─────────────────────────────────────────────────────

def test_success_result_includes_path_and_size(tmp_path):
    """Successful byte-check output includes checks list with size_bytes, limit_bytes, passed."""
    f = tmp_path / "small.md"
    f.write_bytes(b"hello" * 10)
    result = _run_byte_check(str(tmp_path), "small.md")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "checks" in data, f"Expected 'checks' key in output, got: {list(data.keys())}"
    checks = data["checks"]
    assert len(checks) == 1
    check = checks[0]
    assert "size_bytes" in check
    assert "limit_bytes" in check
    assert check["passed"] is True
    assert check["size_bytes"] == 50  # 5 * 10
