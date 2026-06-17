"""Tests for ba-tools template fill (TOOL-11)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_template(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ba_tools"] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


def _seed_template(repo_root: Path, name: str, content: str) -> Path:
    """Create a template file in the ba-core/templates dir under repo_root."""
    tpl_dir = (
        repo_root
        / ".agents"
        / "ba-daily-operators"
        / "ba-tools"
        / "ba-core"
        / "templates"
    )
    tpl_dir.mkdir(parents=True, exist_ok=True)
    tpl_file = tpl_dir / f"{name}.md"
    tpl_file.write_text(content, encoding="utf-8")
    return tpl_file


def test_template_fill_creates_file(tmp_ba_ops):
    """template fill writes a scaffold file with substituted variables."""
    _seed_template(
        tmp_ba_ops,
        "test-tpl",
        "# ${title}\n\nAuthor: ${author}\n",
    )
    out_file = tmp_ba_ops / "output" / "result.md"

    result = _run_template(
        [
            "--repo-root", str(tmp_ba_ops),
            "template", "fill", "test-tpl",
            "--out", str(out_file),
            "--var", "title=My SRS",
            "--var", "author=BA Team",
        ],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["ok"] is True

    # Verify the file was written with substituted content
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "My SRS" in content
    assert "BA Team" in content
    # Original placeholder syntax should be gone (substituted)
    assert "${title}" not in content
    assert "${author}" not in content


def test_template_fill_out_traversal_guard(tmp_ba_ops):
    """template fill rejects --out paths outside the repo root (T-1-09)."""
    _seed_template(
        tmp_ba_ops,
        "test-tpl",
        "# ${title}\n",
    )
    # Attempt to write outside repo root using path traversal
    escape_path = str(tmp_ba_ops / ".." / "escape.md")

    result = _run_template(
        [
            "--repo-root", str(tmp_ba_ops),
            "template", "fill", "test-tpl",
            "--out", escape_path,
        ],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 2
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert any(f["code"] == "PATH_ESCAPE" for f in err_data["failures"])


def test_template_fill_unknown_name_exits_2(tmp_ba_ops):
    """template fill exits 2 for an unknown template name."""
    out_file = tmp_ba_ops / "result.md"

    result = _run_template(
        [
            "--repo-root", str(tmp_ba_ops),
            "template", "fill", "nonexistent-template-xyz",
            "--out", str(out_file),
        ],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 2
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert any(f["code"] == "TEMPLATE_NOT_FOUND" for f in err_data["failures"])


def test_template_fill_safe_substitute_preserves_unknown_vars(tmp_ba_ops):
    """template fill uses safe_substitute so unreplaced ${vars} remain as-is."""
    _seed_template(
        tmp_ba_ops,
        "partial-tpl",
        "# ${title}\n\nUnfilled: ${missing_var}\n",
    )
    out_file = tmp_ba_ops / "partial_result.md"

    result = _run_template(
        [
            "--repo-root", str(tmp_ba_ops),
            "template", "fill", "partial-tpl",
            "--out", str(out_file),
            "--var", "title=Hello",
        ],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    content = out_file.read_text(encoding="utf-8")
    assert "Hello" in content
    # Unknown variable stays as-is (safe_substitute)
    assert "${missing_var}" in content
