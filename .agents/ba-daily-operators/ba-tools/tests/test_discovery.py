"""Tests for ba-tools discovery add|list (TOOL-12)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_discovery(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ba_tools"] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


def test_discovery_add_appends(tmp_ba_ops):
    """discovery add appends a new entry to .ba-ops/discoveries.jsonl."""
    result = _run_discovery(
        ["--repo-root", str(tmp_ba_ops), "discovery", "add", "--note", "Found a gap in UC-001"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["added"] is True

    # Verify the file was created
    discoveries_file = tmp_ba_ops / ".ba-ops" / "discoveries.jsonl"
    assert discoveries_file.exists()
    lines = [l for l in discoveries_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["note"] == "Found a gap in UC-001"
    assert "ts" in entry


def test_discovery_list_returns_all(tmp_ba_ops):
    """discovery list returns all previously added discoveries."""
    notes = ["First discovery", "Second discovery", "Third discovery"]
    for note in notes:
        result = _run_discovery(
            ["--repo-root", str(tmp_ba_ops), "discovery", "add", "--note", note],
            cwd=tmp_ba_ops,
        )
        assert result.returncode == 0, f"add failed: {result.stderr}"

    result = _run_discovery(
        ["--repo-root", str(tmp_ba_ops), "discovery", "list"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["ok"] is True
    returned_notes = [e["note"] for e in data["discoveries"]]
    for note in notes:
        assert note in returned_notes


def test_discovery_list_empty_returns_empty_list(tmp_ba_ops):
    """discovery list on an empty store returns an empty list."""
    result = _run_discovery(
        ["--repo-root", str(tmp_ba_ops), "discovery", "list"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["discoveries"] == []


def test_discovery_list_filters_by_uc(tmp_ba_ops):
    """discovery list --uc UC-001 returns only entries tagged with UC-001."""
    _run_discovery(
        ["--repo-root", str(tmp_ba_ops), "discovery", "add",
         "--note", "UC-001 note", "--tag", "UC-001"],
        cwd=tmp_ba_ops,
    )
    _run_discovery(
        ["--repo-root", str(tmp_ba_ops), "discovery", "add",
         "--note", "UC-002 note", "--tag", "UC-002"],
        cwd=tmp_ba_ops,
    )
    _run_discovery(
        ["--repo-root", str(tmp_ba_ops), "discovery", "add",
         "--note", "Untagged note"],
        cwd=tmp_ba_ops,
    )

    result = _run_discovery(
        ["--repo-root", str(tmp_ba_ops), "discovery", "list", "--uc", "UC-001"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert len(data["discoveries"]) == 1
    assert data["discoveries"][0]["note"] == "UC-001 note"


def test_discovery_add_with_tag(tmp_ba_ops):
    """discovery add --tag stores the tag in the entry."""
    result = _run_discovery(
        ["--repo-root", str(tmp_ba_ops), "discovery", "add",
         "--note", "Tagged note", "--tag", "UC-042"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["tag"] == "UC-042"
