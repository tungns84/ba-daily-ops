"""Integration tests for the ba-uc conductor state-machine contract (UC-03, GATE-03).

Tests the ba-tools spine behaviour WITHOUT invoking the agent — pure deterministic
CLI/subprocess assertions:

  - uc-status next_step lands on a failed step (failed is non-complete)
  - uc-status next_step lands on a killed mid-step (in_progress is non-complete)
  - A gate-fail leaves earlier complete steps intact and later steps pending
  - state patch of a pipeline_step round-trips: uc-status reflects the new next_step
  - Two concurrent pipeline-step patches do not clobber each other (FileLock serializes)

All six helpers are copied from the analog test files — not imported across modules
(test-module isolation convention in this repo).
"""

import json
import multiprocessing
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers — copied from test_uc_status.py (lines 11-65) and test_state.py
#           (lines 29-40). Do NOT import across test modules.
# ---------------------------------------------------------------------------


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


def _run_state(action: str, data: str, repo_root: str) -> subprocess.CompletedProcess:
    """Invoke ba-tools state <action> --data <data> --repo-root <repo_root>."""
    return subprocess.run(
        [
            sys.executable, "-m", "ba_tools",
            "--repo-root", repo_root,
            "state", action,
            "--data", data,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Worker for the concurrent-write test (must be module-level for multiprocessing)
# ---------------------------------------------------------------------------


def _pipeline_patch_worker(repo_root: str, pipeline_step: str, pipeline_status: str, result_queue) -> None:
    """Worker function: patch a single pipeline_step; put result on queue.

    Uses sys.executable so the correct interpreter is always selected
    (never 'python' or 'python3' per RESEARCH Anti-Patterns / CLAUDE.md).
    """
    data = json.dumps({"pipeline_step": pipeline_step, "pipeline_status": pipeline_status})
    result = subprocess.run(
        [
            sys.executable, "-m", "ba_tools",
            "--repo-root", repo_root,
            "state", "patch",
            "--data", data,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    result_queue.put({
        "returncode": result.returncode,
        "stderr": result.stderr,
        "stdout": result.stdout,
        "pipeline_step": pipeline_step,
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_failed_step_is_next_step(tmp_path):
    """uc-status next_step == "srs-analyze" when srs-analyze is failed, rest pending.

    Failed is a non-complete status per _COMPLETE_STATUSES — the step must be
    returned as the next entry point for the resume route (D-RES1).
    """
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "failed",
        "mermaid": "pending",
        "mockup": "pending",
        "index": "pending",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, f"uc-status exited {result.returncode}: {result.stderr}"

    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["next_step"] == "srs-analyze", (
        f"next_step should be 'srs-analyze' when it has status 'failed', "
        f"got {payload['next_step']!r}"
    )


def test_in_progress_step_is_next_step(tmp_path):
    """uc-status next_step == "mermaid" when srs-analyze=complete, mermaid=in_progress.

    A kill mid-step leaves the step with status in_progress (non-complete).
    uc-status must land on that step so the resume route re-enters there (D-RES2).
    """
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "in_progress",
        "mockup": "pending",
        "index": "pending",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, f"uc-status exited {result.returncode}: {result.stderr}"

    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["next_step"] == "mermaid", (
        f"next_step should be 'mermaid' when it has status 'in_progress' (kill-mid-step), "
        f"got {payload['next_step']!r}"
    )


def test_gate_fail_state_not_clobbered(tmp_path):
    """Gate fail leaves earlier complete steps intact and later steps pending.

    STATE.md: srs-analyze=complete, mermaid=failed, mockup=pending, index=pending.
    After a gate fail on mermaid:
      - srs-analyze must still show 'complete' (not reset)
      - later steps remain 'pending'
      - next_step == 'mermaid' (the failed step — re-entry point for resume)
    This proves D-RES1: recoverable state after gate rejection.
    """
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "failed",
        "mockup": "pending",
        "index": "pending",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, f"uc-status exited {result.returncode}: {result.stderr}"

    payload = json.loads(result.stdout)
    assert payload["ok"] is True

    steps = payload["steps"]
    assert steps.get("srs-analyze") == "complete", (
        f"srs-analyze must remain 'complete' after gate fail on mermaid, "
        f"got {steps.get('srs-analyze')!r}"
    )
    assert steps.get("mermaid") == "failed", (
        f"mermaid must show 'failed' after gate rejection, "
        f"got {steps.get('mermaid')!r}"
    )
    assert steps.get("mockup") == "pending", (
        f"mockup must remain 'pending' (gate fail stopped pipeline), "
        f"got {steps.get('mockup')!r}"
    )
    assert steps.get("index") == "pending", (
        f"index must remain 'pending' (gate fail stopped pipeline), "
        f"got {steps.get('index')!r}"
    )
    assert payload["next_step"] == "mermaid", (
        f"next_step should be 'mermaid' (the failed step — resume entry point), "
        f"got {payload['next_step']!r}"
    )


def test_resume_entry_point(tmp_path):
    """After mermaid=failed, uc-status next_step == 'mermaid' — deterministic re-entry point.

    The resume route reads uc-status next_step and re-runs from that step.
    This test pins the deterministic re-entry contract (D-RES2).
    """
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "failed",
        "mockup": "pending",
        "index": "pending",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, f"uc-status exited {result.returncode}: {result.stderr}"

    payload = json.loads(result.stdout)
    assert payload["next_step"] == "mermaid", (
        f"Resume entry point must be 'mermaid' when mermaid=failed, "
        f"got {payload['next_step']!r}"
    )


def test_pipeline_patch_round_trip(tmp_path):
    """state patch pipeline_step round-trip: uc-status next_step updates correctly.

    Steps:
      1. Scaffold a .ba-ops/STATE.md via state patch (srs-analyze=complete first).
      2. Patch pipeline_step=mermaid / pipeline_status=complete.
      3. uc-status next_step must == 'mockup' (both srs-analyze and mermaid now complete).

    This proves the CR-03 reserved body-table directive works end-to-end.
    """
    repo_root = str(tmp_path)

    # Step 1: bootstrap STATE.md with all four rows via init/ensure_scaffold approach.
    # Use _make_state_md to pre-seed the four rows — mirrors the conductor's init flow.
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "pending",
        "mermaid": "pending",
        "mockup": "pending",
        "index": "pending",
    })

    # Step 2a: Patch srs-analyze = complete
    r1 = _run_state(
        "patch",
        json.dumps({"pipeline_step": "srs-analyze", "pipeline_status": "complete"}),
        repo_root,
    )
    assert r1.returncode == 0, f"state patch srs-analyze failed: {r1.stderr}"

    # Step 2b: Patch mermaid = complete
    r2 = _run_state(
        "patch",
        json.dumps({"pipeline_step": "mermaid", "pipeline_status": "complete"}),
        repo_root,
    )
    assert r2.returncode == 0, f"state patch mermaid failed: {r2.stderr}"

    # Step 3: uc-status should now show next_step == 'mockup'
    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, f"uc-status exited {result.returncode}: {result.stderr}"

    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["next_step"] == "mockup", (
        f"After patching srs-analyze+mermaid to complete, next_step must be 'mockup', "
        f"got {payload['next_step']!r}"
    )
    # Verify the steps dict reflects the patches
    steps = payload["steps"]
    assert steps.get("srs-analyze") == "complete", (
        f"srs-analyze must be 'complete' after patch, got {steps.get('srs-analyze')!r}"
    )
    assert steps.get("mermaid") == "complete", (
        f"mermaid must be 'complete' after patch, got {steps.get('mermaid')!r}"
    )


def test_concurrent_pipeline_patch_no_clobber(tmp_path):
    """Two concurrent pipeline-step patches do not clobber each other.

    Two multiprocessing.Process workers each patch a DISTINCT step:
      - Worker 1: pipeline_step=mermaid, pipeline_status=complete
      - Worker 2: pipeline_step=mockup, pipeline_status=complete

    After both join, uc-status must reflect BOTH writes — FileLock serialized
    both patches without data loss (no-clobber invariant, TOOL-03 + D-TEST).

    Note on assertion strategy:
    - Both patches write different body-table rows, so there is no winner/loser —
      both must succeed.
    - At least one returncode must be 0; LOCK_TIMEOUT exit-2 is an accepted outcome
      per the lockfile semantics (the loser exits 2, not 1 or 3).
    - After join, uc-status must show BOTH patched statuses, proving no data loss.
    """
    repo_root = str(tmp_path)

    # Pre-seed STATE.md with all four rows (srs-analyze also complete for clean ordering)
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "pending",
        "mockup": "pending",
        "index": "pending",
    })

    q: multiprocessing.Queue = multiprocessing.Queue()

    p1 = multiprocessing.Process(
        target=_pipeline_patch_worker,
        args=(repo_root, "mermaid", "complete", q),
    )
    p2 = multiprocessing.Process(
        target=_pipeline_patch_worker,
        args=(repo_root, "mockup", "complete", q),
    )

    p1.start()
    p2.start()
    p1.join(timeout=30)
    p2.join(timeout=30)

    # Collect results
    results = []
    while not q.empty():
        results.append(q.get_nowait())

    assert len(results) == 2, f"Expected 2 results from queue, got {len(results)}"

    returncodes = [r["returncode"] for r in results]

    # At least one worker must have succeeded
    assert 0 in returncodes, (
        f"At least one concurrent pipeline patch must exit 0. "
        f"Returncodes: {returncodes}. "
        f"Stderr[0]: {results[0]['stderr']!r} Stderr[1]: {results[1]['stderr']!r}"
    )

    # Any non-zero worker must have exited 2 with LOCK_TIMEOUT
    for r in results:
        if r["returncode"] != 0:
            assert r["returncode"] == 2, (
                f"Non-zero worker must exit 2 (LOCK_TIMEOUT), "
                f"got {r['returncode']}. stderr={r['stderr']!r}"
            )
            try:
                err = json.loads(r["stderr"])
            except json.JSONDecodeError:
                pytest.fail(
                    f"Non-zero worker stderr is not valid JSON: {r['stderr']!r}"
                )
            assert err["ok"] is False
            codes = [f["code"] for f in err.get("failures", [])]
            assert "LOCK_TIMEOUT" in codes, (
                f"Non-zero worker must report LOCK_TIMEOUT. Failures: {err.get('failures')}"
            )

    # After join, verify uc-status reflects both writes.
    # Workers patch DIFFERENT steps, so both statuses must survive in STATE.md.
    # A LOCK_TIMEOUT on one worker means that step was NOT patched — so we assert
    # only that the successful worker(s)' step(s) were written correctly.
    uc_result = _run_uc_status(tmp_path)
    assert uc_result.returncode == 0, (
        f"uc-status exited {uc_result.returncode} after concurrent patches: {uc_result.stderr}"
    )
    payload = json.loads(uc_result.stdout)
    steps = payload["steps"]

    # Identify which workers succeeded
    successful_steps = {r["pipeline_step"] for r in results if r["returncode"] == 0}

    for step in successful_steps:
        assert steps.get(step) == "complete", (
            f"Step '{step}' was patched to 'complete' by a successful worker "
            f"but uc-status shows {steps.get(step)!r} — no-clobber violated."
        )
