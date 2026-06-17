"""Tests for ba-tools uc-status (TOOL-09)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _make_state_md(ba_ops: Path, steps: dict[str, str], uc_id: str = "") -> None:
    """Write a .ba-ops/STATE.md with the given pipeline step statuses."""
    ba_ops.mkdir(parents=True, exist_ok=True)

    # Build Pipeline Steps table rows
    rows = []
    for step, status in steps.items():
        rows.append(f"| {step} | {status} | |")
    table = "\n".join(rows)

    state_content = f"""\
---
step: 0
current_step:
status: executing
operator: ba-uc
uc_id: {uc_id}
uc_name:
phase:
started_at:
updated_at:
completed_at:
last_action:
next_step:
position:
iteration: 0
note:
---

# State

## Pipeline Steps

| Step | Status | Completed At |
|------|--------|--------------|
{table}

## Gate Verdicts

| Gate | Verdict | Notes |
|------|---------|-------|

## Blockers

(none)
"""
    (ba_ops / "STATE.md").write_text(state_content, encoding="utf-8")


def _run_uc_status(tmp_path: Path, extra_args: list | None = None) -> subprocess.CompletedProcess:
    """Run `python -m ba_tools --repo-root <tmp_path> uc-status [extra_args]`."""
    cmd = [sys.executable, "-m", "ba_tools", "--repo-root", str(tmp_path), "uc-status"]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def test_uc_status_returns_pipeline_state(tmp_path):
    """uc-status returns JSON with ok:true, steps, and next_step fields."""
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "pending",
        "mockup": "pending",
        "index": "pending",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, f"uc-status exited {result.returncode}: {result.stderr}"

    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert "steps" in payload,    "response must contain 'steps' key"
    assert "next_step" in payload, "response must contain 'next_step' key"


def test_uc_status_partial_pipeline_next_step(tmp_path):
    """Given STATE.md with srs-analyze complete, next_step is 'mermaid'."""
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "pending",
        "mockup": "pending",
        "index": "pending",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["next_step"] == "mermaid", (
        f"next_step should be 'mermaid' when only srs-analyze is complete, got {payload['next_step']!r}"
    )


def test_uc_status_fully_complete_pipeline(tmp_path):
    """Given a fully complete pipeline, next_step is 'done'."""
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "complete",
        "mockup": "complete",
        "index": "complete",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["next_step"] == "done", (
        f"next_step should be 'done' when all steps complete, got {payload['next_step']!r}"
    )


def test_uc_status_missing_state_exits_2(tmp_path):
    """Missing STATE.md causes uc-status to exit 2 with NO_STATE error."""
    # No STATE.md — just ensure tmp_path exists (it does)
    result = _run_uc_status(tmp_path)
    assert result.returncode == 2, (
        f"uc-status should exit 2 for missing STATE.md, got {result.returncode}"
    )
    error = json.loads(result.stderr)
    assert error["ok"] is False
    assert any(f.get("code") == "NO_STATE" for f in error["failures"]), (
        f"Expected NO_STATE code in failures, got: {error['failures']}"
    )


def test_uc_status_first_step_next_when_all_pending(tmp_path):
    """When all steps are pending, next_step is 'srs-analyze' (first in spine)."""
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "pending",
        "mermaid": "pending",
        "mockup": "pending",
        "index": "pending",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["next_step"] == "srs-analyze", (
        f"next_step should be 'srs-analyze' when all pending, got {payload['next_step']!r}"
    )


def test_uc_status_steps_dict_contains_all_spine_steps(tmp_path):
    """The steps dict returned contains all four canonical spine steps."""
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "complete",
        "mockup": "pending",
        "index": "pending",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    steps = payload["steps"]
    for step in ("srs-analyze", "mermaid", "mockup", "index"):
        assert step in steps, f"steps dict must contain '{step}'"


def test_uc_status_uc_arg_passed_through(tmp_path):
    """--uc argument is reflected in the response uc field."""
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "pending",
        "mockup": "pending",
        "index": "pending",
    }, uc_id="UC-001")

    result = _run_uc_status(tmp_path, ["--uc", "UC-002"])
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    # --uc arg takes precedence over STATE.md uc_id
    assert payload["uc"] == "UC-002"
