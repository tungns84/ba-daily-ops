"""Tests for ba-tools confirm gate (GATE-02)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_confirm(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ba_tools"] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        # Ensure stdin is not connected (confirms pass-through does not block)
        stdin=subprocess.DEVNULL,
    )


def test_confirm_exits_0(tmp_ba_ops):
    """confirm always exits 0 in v1 (pass-through gate)."""
    result = _run_confirm(
        ["confirm"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["confirmed"] is True
    assert data["gate"] == "confirm"


def test_confirm_with_yes_flag_exits_0(tmp_ba_ops):
    """confirm --yes exits 0 (non-interactive bypass)."""
    result = _run_confirm(
        ["confirm", "--yes"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["confirmed"] is True


def test_confirm_with_message_exits_0(tmp_ba_ops):
    """confirm --message exits 0 and outputs confirmed envelope."""
    result = _run_confirm(
        ["confirm", "--message", "About to write SRS output. Proceed?"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["confirmed"] is True


def test_confirm_does_not_block(tmp_ba_ops):
    """confirm completes without reading stdin (pass-through, non-blocking)."""
    # Run with DEVNULL stdin — if confirm tried to read stdin it would get EOF
    # immediately; it should still exit 0
    result = _run_confirm(
        ["confirm"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0
    # No stderr output expected on success
    assert result.stderr.strip() == ""


def test_confirm_flat_envelope(tmp_ba_ops):
    """confirm output is a flat JSON envelope with ok:true and failures:[]."""
    result = _run_confirm(
        ["confirm"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "ok" in data
    assert "failures" in data
    assert data["failures"] == []
    assert data["ok"] is True
