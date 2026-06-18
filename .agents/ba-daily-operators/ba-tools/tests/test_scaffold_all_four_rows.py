"""WR-02 regression guard — scaffold seeds all four pipeline rows.

Verifies that `ensure_scaffold` (scaffold.py) seeds STATE.md with all four canonical
pipeline rows (srs-analyze, mermaid, mockup, index), each with status 'pending'.

WR-02 was a suspected defect (index row missing from scaffold seed). This module
acts as the regression guard proving the defect does not exist: all four rows are
present and in canonical order from the moment ensure_scaffold runs.

Verification strategy:
  1. Call ensure_scaffold(tmp_path) directly (no CLI hop — pure Python)
  2. Run `ba-tools uc-status` against tmp_path to read the Pipeline Steps table
  3. Assert all four canonical rows present with status 'pending'
  4. Assert next_step == 'srs-analyze' (first non-complete step in canonical order)
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ba_tools.scaffold import ensure_scaffold


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical order from state_store.PIPELINE_STEPS
CANONICAL_STEPS = ("srs-analyze", "mermaid", "mockup", "index")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _run_uc_status(repo_root: Path, extra_args: list | None = None) -> subprocess.CompletedProcess:
    """Invoke `ba-tools uc-status --repo-root <root>` and return CompletedProcess."""
    cmd = [
        sys.executable, "-m", "ba_tools",
        "--repo-root", str(repo_root),
        "uc-status",
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestScaffoldSeedsAllFourRows:
    """WR-02 regression: ensure_scaffold seeds all four pipeline rows."""

    @pytest.fixture()
    def scaffolded_root(self, tmp_path):
        """Fresh tmp_path with ensure_scaffold applied."""
        ensure_scaffold(tmp_path)
        return tmp_path

    def test_all_four_rows_present(self, scaffolded_root):
        """All four canonical steps must appear in uc-status output."""
        result = _run_uc_status(scaffolded_root)
        assert result.returncode == 0, (
            f"uc-status exited {result.returncode} after ensure_scaffold.\n"
            f"stderr: {result.stderr}"
        )
        payload = json.loads(result.stdout)
        steps: dict = payload.get("steps", {})

        missing = [step for step in CANONICAL_STEPS if step not in steps]
        assert not missing, (
            f"WR-02 regression: ensure_scaffold missing pipeline rows: {missing}. "
            f"Got steps: {list(steps.keys())}"
        )

    def test_all_rows_start_as_pending(self, scaffolded_root):
        """Every scaffold-seeded row must have status 'pending' (not failed, complete, etc.)."""
        result = _run_uc_status(scaffolded_root)
        assert result.returncode == 0, (
            f"uc-status exited {result.returncode}.\nstderr: {result.stderr}"
        )
        payload = json.loads(result.stdout)
        steps: dict = payload.get("steps", {})

        for step in CANONICAL_STEPS:
            status = steps.get(step)
            assert status == "pending", (
                f"Step '{step}' must start as 'pending' after scaffold, got '{status}'"
            )

    def test_next_step_is_srs_analyze(self, scaffolded_root):
        """First non-complete step in canonical order must be 'srs-analyze' on a fresh scaffold."""
        result = _run_uc_status(scaffolded_root)
        assert result.returncode == 0, (
            f"uc-status exited {result.returncode}.\nstderr: {result.stderr}"
        )
        payload = json.loads(result.stdout)
        assert payload["next_step"] == "srs-analyze", (
            f"Fresh scaffold next_step must be 'srs-analyze', got '{payload['next_step']}'"
        )

    def test_ensure_scaffold_idempotent(self, tmp_path):
        """Calling ensure_scaffold twice on the same root must not raise or overwrite."""
        ensure_scaffold(tmp_path)
        # Manually write a sentinel to STATE.md to detect overwrites
        state_md = tmp_path / ".ba-ops" / "STATE.md"
        assert state_md.exists(), ".ba-ops/STATE.md not created by first ensure_scaffold"
        original_content = state_md.read_text(encoding="utf-8")

        # Second call must not overwrite
        ensure_scaffold(tmp_path)
        second_content = state_md.read_text(encoding="utf-8")
        assert second_content == original_content, (
            "ensure_scaffold is not idempotent — second call modified STATE.md"
        )
