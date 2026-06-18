"""Tests for mermaid_render_cmd.py (Task 1, plan 03-01).

TDD RED phase: all tests expected to FAIL before implementation exists.

Tests cover:
  - test_no_cli_hard_fail: no mmdc anywhere → exit 2, NO_MERMAID_CLI, no image written
  - test_fence_absent: artifact with no mermaid fence → exit 2, NO_MERMAID_FENCE
  - test_slug_path_traversal: --slug ../escape → exit 2, PATH_TRAVERSAL
  - test_success_path: subprocess.run patched to returncode-0 stub → diagram.mmd written, ok:true
"""

import json
import os
import subprocess
import sys
import unittest.mock
from pathlib import Path

import pytest

PYTHON = sys.executable

# Path to fixture files
_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "mermaid"
_SAMPLE_DIAGRAM = _FIXTURES_DIR / "sample_diagram.md"
_NO_FENCE = _FIXTURES_DIR / "no_fence.md"


def _run(args: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    """Invoke ba_tools via [PYTHON, "-m", "ba_tools", ...] with optional env override."""
    return subprocess.run(
        [PYTHON, "-m", "ba_tools"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def _make_repo(tmp_path: Path) -> Path:
    """Set up a minimal repo root with .ba-ops/mermaid/test-slug/ scaffold.

    Returns the repo root (tmp_path).
    """
    slug_dir = tmp_path / ".ba-ops" / "mermaid" / "test-slug"
    slug_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


def _env_no_mermaid() -> dict:
    """Return os.environ copy with MERMAID_CLI stripped out."""
    env = os.environ.copy()
    env.pop("MERMAID_CLI", None)
    return env


# ---------------------------------------------------------------------------
# test_no_cli_hard_fail
# ---------------------------------------------------------------------------

def test_no_cli_hard_fail(tmp_path):
    """With no mmdc available anywhere, mermaid-render exits 2 with NO_MERMAID_CLI.

    Verifies ROADMAP criterion 3: hard-fail exit 2 when no CLI resolves; no image written.

    Strategy: strip $MERMAID_CLI from subprocess env AND patch shutil.which via a
    wrapper script environment so no PATH mmdc or npx resolves.  Because we must
    test through the subprocess boundary (ba_tools runs in a child process), we
    instead test the unit-level function directly using importlib so we can apply
    unittest.mock inside the same process.
    """
    # Unit-level test: import the command module and test resolve_mmdc + run directly
    # (avoids needing to control the child-process PATH at subprocess level)
    from ba_tools.commands import mermaid_render_cmd  # noqa: PLC0415  (imported inside test)

    env = _env_no_mermaid()
    repo = _make_repo(tmp_path)

    # Patch shutil.which to return None (no mmdc, no npx on PATH)
    # Patch os.environ.get for MERMAID_CLI to also return None
    with (
        unittest.mock.patch("shutil.which", return_value=None),
        unittest.mock.patch.dict("os.environ", {}, clear=True),
    ):
        from ba_tools.errors import BaToolsError
        with pytest.raises(BaToolsError) as exc_info:
            mermaid_render_cmd.resolve_mmdc(None)

    failures = exc_info.value.failures
    codes = [f.get("code") for f in failures]
    assert "NO_MERMAID_CLI" in codes, f"Expected NO_MERMAID_CLI in failures; got {codes}"

    # Also verify no image file was written (out_dir should be empty / not contain .svg or .png)
    out_dir = repo / ".ba-ops" / "mermaid" / "test-slug"
    image_files = list(out_dir.glob("*.svg")) + list(out_dir.glob("*.png"))
    assert image_files == [], f"No image should be written on NO_MERMAID_CLI; found: {image_files}"


# ---------------------------------------------------------------------------
# test_fence_absent
# ---------------------------------------------------------------------------

def test_fence_absent(tmp_path):
    """Running against no_fence.md exits 2 with NO_MERMAID_FENCE.

    Uses CLI subprocess so the full dispatch path is exercised.
    Uses a fake mmdc so resolve_mmdc succeeds (fence check happens before mmdc call).
    """
    repo = _make_repo(tmp_path)

    # Create a fake mmdc script that does nothing (exit 0)
    # We only need it to be resolvable — the fence check happens before mmdc invocation
    fake_mmdc = tmp_path / "fake_mmdc"
    fake_mmdc.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    env = _env_no_mermaid()
    env["MERMAID_CLI"] = str(fake_mmdc)

    result = _run(
        [
            "--repo-root", str(repo),
            "mermaid-render",
            "--slug", "test-slug",
            "--artifact", str(_NO_FENCE),
        ],
        cwd=repo,
        env=env,
    )
    assert result.returncode == 2, (
        f"Expected exit 2 for missing fence; got {result.returncode}\n"
        f"stderr={result.stderr}\nstdout={result.stdout}"
    )
    err = json.loads(result.stderr)
    codes = [f.get("code") for f in err.get("failures", [])]
    assert "NO_MERMAID_FENCE" in codes, f"Expected NO_MERMAID_FENCE; got {codes}"


# ---------------------------------------------------------------------------
# test_slug_path_traversal
# ---------------------------------------------------------------------------

def test_slug_path_traversal(tmp_path):
    """--slug ../escape exits 2 with PATH_TRAVERSAL."""
    repo = _make_repo(tmp_path)

    env = _env_no_mermaid()

    result = _run(
        [
            "--repo-root", str(repo),
            "mermaid-render",
            "--slug", "../escape",
            "--artifact", str(_SAMPLE_DIAGRAM),
        ],
        cwd=repo,
        env=env,
    )
    assert result.returncode == 2, (
        f"Expected exit 2 for path traversal slug; got {result.returncode}\n"
        f"stderr={result.stderr}"
    )
    err = json.loads(result.stderr)
    codes = [f.get("code") for f in err.get("failures", [])]
    assert "PATH_TRAVERSAL" in codes, f"Expected PATH_TRAVERSAL in failures; got {codes}"


# ---------------------------------------------------------------------------
# test_success_path
# ---------------------------------------------------------------------------

def test_success_path(tmp_path):
    """With subprocess.run patched to returncode-0, diagram.mmd is written and ok:true returned.

    This test patches subprocess.run inside mermaid_render_cmd to avoid needing a real mmdc.
    resolve_mmdc is satisfied via $MERMAID_CLI env pointing to a fake path that shutil.which
    does not need to find (the flag path is returned directly).
    """
    repo = _make_repo(tmp_path)

    from ba_tools.commands import mermaid_render_cmd  # noqa: PLC0415

    # Build args namespace matching what argparse would produce
    import argparse  # noqa: PLC0415
    args = argparse.Namespace(
        repo_root=str(repo),
        slug="test-slug",
        artifact=str(_SAMPLE_DIAGRAM),
        format="svg",
        mermaid_cli="/fake/mmdc",  # direct path — resolve_mmdc returns ["/fake/mmdc"]
    )

    # Patch subprocess.run so no real mmdc is needed
    mock_proc = unittest.mock.MagicMock()
    mock_proc.returncode = 0
    mock_proc.stderr = b""
    mock_proc.stdout = b""

    captured_output = {}

    from ba_tools.output import ok_json as _real_ok_json  # noqa: PLC0415

    def _capture_ok_json(**kwargs):
        captured_output.update(kwargs)
        _real_ok_json(**kwargs)

    with (
        unittest.mock.patch("subprocess.run", return_value=mock_proc),
        unittest.mock.patch(
            "ba_tools.commands.mermaid_render_cmd.ok_json",
            side_effect=_capture_ok_json,
        ),
    ):
        mermaid_render_cmd.run(args)

    # diagram.mmd must exist under .ba-ops/mermaid/test-slug/
    out_dir = repo / ".ba-ops" / "mermaid" / "test-slug"
    mmd_path = out_dir / "diagram.mmd"
    assert mmd_path.exists(), f"diagram.mmd not written at {mmd_path}"

    # ok_json was called with argv, mmd, image keys
    assert "argv" in captured_output, "ok_json missing 'argv' key"
    assert "mmd" in captured_output, "ok_json missing 'mmd' key"
    assert "image" in captured_output, "ok_json missing 'image' key"
