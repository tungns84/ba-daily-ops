"""Tests for ba-tools init (TOOL-01, TRACE-01)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_init(tmp_path: Path, operator: str) -> subprocess.CompletedProcess:
    """Run `python -m ba_tools --repo-root <tmp_path> init <operator>`.

    Note: --repo-root is a top-level argument that must precede the subcommand.
    """
    return subprocess.run(
        [sys.executable, "-m", "ba_tools", "--repo-root", str(tmp_path), "init", operator],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_init_creates_ba_ops_scaffold(tmp_path):
    """init creates .ba-ops/ with PROJECT.md, REQUIREMENTS.md, INDEX.md, STATE.md, config.json."""
    result = _run_init(tmp_path, "ba-uc")
    assert result.returncode == 0, f"init exited {result.returncode}: {result.stderr}"

    ba_ops = tmp_path / ".ba-ops"
    assert ba_ops.is_dir(), ".ba-ops/ directory must exist"
    for name in ("PROJECT.md", "REQUIREMENTS.md", "INDEX.md", "STATE.md", "config.json"):
        assert (ba_ops / name).is_file(), f".ba-ops/{name} must be created by init"


def test_init_returns_context_json(tmp_path):
    """init stdout is valid JSON with ok:true, config, routes, default_route, state keys."""
    result = _run_init(tmp_path, "ba-uc")
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert "config" in payload,       "context JSON must contain 'config' key"
    assert "routes" in payload,       "context JSON must contain 'routes' key"
    assert "default_route" in payload, "context JSON must contain 'default_route' key"
    assert "state" in payload,        "context JSON must contain 'state' key"
    assert payload["default_route"] == "deliver", "ba-uc default route is 'deliver'"
    assert "deliver" in payload["routes"], "ba-uc routes must include 'deliver'"


def test_init_idempotent(tmp_path):
    """Running init twice on the same root does not error or duplicate files."""
    # First run — creates files
    result1 = _run_init(tmp_path, "ba-uc")
    assert result1.returncode == 0, result1.stderr

    # Edit a scaffold file to verify it is NOT clobbered
    project_md = tmp_path / ".ba-ops" / "PROJECT.md"
    original_content = project_md.read_text(encoding="utf-8")
    sentinel = "HAND_EDITED_SENTINEL_DO_NOT_OVERWRITE"
    project_md.write_text(original_content + f"\n{sentinel}\n", encoding="utf-8")

    # Second run — must succeed without overwriting
    result2 = _run_init(tmp_path, "ba-uc")
    assert result2.returncode == 0, result2.stderr

    new_content = project_md.read_text(encoding="utf-8")
    assert sentinel in new_content, "init must not overwrite an existing scaffold file"


def test_init_unknown_operator_exits_2(tmp_path):
    """init with an unknown operator exits 2 with UNKNOWN_OPERATOR code."""
    result = _run_init(tmp_path, "ba-nonexistent")
    assert result.returncode == 2, "unknown operator must exit 2"
    error = json.loads(result.stderr)
    assert error["ok"] is False
    assert any(f.get("code") == "UNKNOWN_OPERATOR" for f in error["failures"])


def test_init_scaffold_subdirs_created(tmp_path):
    """init creates the .ba-ops/ subdirectories (srs/, mermaid/, mockup/, backlog/, plugins/)."""
    result = _run_init(tmp_path, "ba-srs-analyze")
    assert result.returncode == 0, result.stderr

    ba_ops = tmp_path / ".ba-ops"
    for subdir in ("srs", "mermaid", "mockup", "backlog", "plugins"):
        assert (ba_ops / subdir).is_dir(), f".ba-ops/{subdir}/ must be created by init"
