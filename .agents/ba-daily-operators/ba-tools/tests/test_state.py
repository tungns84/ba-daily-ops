"""Tests for ba-tools state (TOOL-03) including concurrent-write guard.

Tests cover:
- state update writes fields to .ba-ops/STATE.md (exits 0)
- state patch merges without overwriting existing keys
- state advance increments the step counter
- malformed --data fails with BAD_DATA exit 2
- concurrent writes: no-clobber guarantee (the heavyweight test ~0-10s)
- stale lock file is reclaimed and write succeeds
"""

import json
import multiprocessing
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    )


# ---------------------------------------------------------------------------
# Unit tests: basic state commands
# ---------------------------------------------------------------------------

def test_state_update_writes_fields(tmp_path):
    """state update writes provided JSON fields to STATE.md and exits 0."""
    root = str(tmp_path)
    result = _run_state("update", '{"step": "s1", "status": "active"}', root)
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr={result.stderr}"

    stdout = json.loads(result.stdout)
    assert stdout["ok"] is True
    assert stdout["action"] == "update"

    state_md = tmp_path / ".ba-ops" / "STATE.md"
    assert state_md.exists(), ".ba-ops/STATE.md must be created by state update"
    content = state_md.read_text(encoding="utf-8")
    assert "step: s1" in content, "STATE.md should contain written step value"
    assert "status: active" in content, "STATE.md should contain written status value"


def test_state_patch_merges_fields(tmp_path):
    """state patch merges new fields without overwriting existing ones."""
    root = str(tmp_path)

    # Seed with initial state
    _run_state("update", '{"step": "s1", "status": "active"}', root)

    # Patch adds a new field without overwriting step or status
    result = _run_state("patch", '{"operator": "ba-uc"}', root)
    assert result.returncode == 0, f"Patch failed: {result.stderr}"

    state_md = tmp_path / ".ba-ops" / "STATE.md"
    content = state_md.read_text(encoding="utf-8")
    assert "step: s1" in content, "Existing step must be preserved by patch"
    assert "status: active" in content, "Existing status must be preserved by patch"
    assert "operator: ba-uc" in content, "New operator field must be written by patch"


def test_state_advance_increments_step(tmp_path):
    """state advance increments a numeric step counter field."""
    root = str(tmp_path)

    # Seed with a numeric step
    _run_state("update", '{"step": "3", "status": "running"}', root)

    result = _run_state("advance", '{}', root)
    assert result.returncode == 0, f"Advance failed: {result.stderr}"

    state_md = tmp_path / ".ba-ops" / "STATE.md"
    content = state_md.read_text(encoding="utf-8")
    assert "step: 4" in content, "Advance must increment step from 3 to 4"
    assert "status: running" in content, "Advance must preserve non-step fields"


def test_state_advance_non_numeric_step_fails_loudly(tmp_path):
    """advance on a non-numeric step must exit 2 STEP_NOT_NUMERIC, not silently reset (CR-04)."""
    root = str(tmp_path)

    # Seed with a free-form (non-numeric) step value, as the project's own
    # workflows do (e.g. 'writer_p1').
    _run_state("update", '{"step": "writer_p1", "status": "running"}', root)

    result = _run_state("advance", "{}", root)
    assert result.returncode == 2, (
        f"advance on non-numeric step must exit 2, got {result.returncode}. "
        f"stderr={result.stderr}"
    )
    err = json.loads(result.stderr)
    assert err["ok"] is False
    codes = [f["code"] for f in err["failures"]]
    assert "STEP_NOT_NUMERIC" in codes, f"Expected STEP_NOT_NUMERIC, got {codes}"

    # The existing step must be preserved (no clobber to '1').
    state_md = tmp_path / ".ba-ops" / "STATE.md"
    content = state_md.read_text(encoding="utf-8")
    assert "step: writer_p1" in content, "Non-numeric step must be preserved on failed advance"


def test_state_advance_explicit_step_on_non_numeric(tmp_path):
    """advance with an explicit step in --data overrides even a non-numeric current step (CR-04)."""
    root = str(tmp_path)
    _run_state("update", '{"step": "writer_p1"}', root)

    result = _run_state("advance", '{"step": "5"}', root)
    assert result.returncode == 0, f"Explicit step advance failed: {result.stderr}"
    state_md = tmp_path / ".ba-ops" / "STATE.md"
    assert "step: 5" in state_md.read_text(encoding="utf-8")


def test_state_bad_data_exits_2(tmp_path):
    """Malformed --data (not valid JSON) exits 2 with BAD_DATA failure code."""
    root = str(tmp_path)
    result = _run_state("update", "{not json", root)
    assert result.returncode == 2, f"Expected exit 2 for bad JSON, got {result.returncode}"

    err = json.loads(result.stderr)
    assert err["ok"] is False
    codes = [f["code"] for f in err["failures"]]
    assert "BAD_DATA" in codes, f"Expected BAD_DATA failure, got: {codes}"


def test_state_unknown_keys_ignored(tmp_path):
    """Keys outside ALLOWED_KEYS are silently dropped (T-1-08 security contract)."""
    root = str(tmp_path)
    result = _run_state("update", '{"step": "s1", "evil_key": "injected"}', root)
    assert result.returncode == 0

    state_md = tmp_path / ".ba-ops" / "STATE.md"
    content = state_md.read_text(encoding="utf-8")
    assert "step: s1" in content
    assert "evil_key" not in content, "Unknown keys must not appear in STATE.md"


def test_state_creates_ba_ops_dir(tmp_path):
    """state update creates .ba-ops/ directory if it does not exist."""
    root = str(tmp_path)
    ba_ops = tmp_path / ".ba-ops"
    assert not ba_ops.exists(), "Precondition: .ba-ops must not exist yet"

    result = _run_state("update", '{"step": "s1"}', root)
    assert result.returncode == 0
    assert ba_ops.exists(), ".ba-ops/ must be created by state update"


def test_state_stale_lock_reclaimed(tmp_path):
    """A stale lock file (mtime > 10s) is reclaimed and the write succeeds."""
    root = str(tmp_path)
    ba_ops = tmp_path / ".ba-ops"
    ba_ops.mkdir()

    # Create a stale lock file by backdating its mtime by 20 seconds
    lock_path = ba_ops / "STATE.md.lock"
    lock_path.write_text("", encoding="utf-8")
    stale_mtime = time.time() - 20  # 20 seconds in the past
    os.utime(lock_path, (stale_mtime, stale_mtime))

    # The stale lock should be reclaimed, and the write should succeed
    result = _run_state("update", '{"step": "after_stale"}', root)
    assert result.returncode == 0, (
        f"Expected exit 0 after stale lock reclaim, got {result.returncode}. "
        f"stderr={result.stderr}"
    )
    state_md = tmp_path / ".ba-ops" / "STATE.md"
    assert state_md.exists()
    assert "after_stale" in state_md.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Concurrent-write test (TOOL-03 success criterion 3)
# ---------------------------------------------------------------------------

def _writer_worker(repo_root: str, data: str, result_queue):
    """Worker function: invoke ba-tools state update, put result on queue.

    Uses sys.executable so the correct interpreter is always selected
    (never 'python' or 'python3' per RESEARCH Anti-Patterns / CLAUDE.md).
    """
    result = subprocess.run(
        [
            sys.executable, "-m", "ba_tools",
            "--repo-root", repo_root,
            "state", "update",
            "--data", data,
        ],
        capture_output=True,
        text=True,
    )
    result_queue.put({"returncode": result.returncode, "stderr": result.stderr})


def test_concurrent_write(tmp_path):
    """Two concurrent writers: no STATE.md clobber; loser exits 2 LOCK_TIMEOUT or both succeed.

    Assertion strategy (RESEARCH Pitfall 3):
    - At least one writer must exit 0  — success criterion.
    - STATE.md on disk must contain exactly ONE writer's complete, intact content —
      the no-clobber invariant.
    - Any writer that exited non-zero must have exited 2 with ok:false and
      a LOCK_TIMEOUT failure code.
    - We do NOT assert that a specific writer wins (avoids Pitfall 3).
    """
    repo_root = str(tmp_path)

    # Each writer writes a distinct recognisable step value
    data_p1 = '{"step": "writer_p1", "status": "p1_done"}'
    data_p2 = '{"step": "writer_p2", "status": "p2_done"}'

    q: multiprocessing.Queue = multiprocessing.Queue()

    p1 = multiprocessing.Process(
        target=_writer_worker, args=(repo_root, data_p1, q)
    )
    p2 = multiprocessing.Process(
        target=_writer_worker, args=(repo_root, data_p2, q)
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

    # (a) At least one writer must succeed
    assert 0 in returncodes, (
        f"At least one writer must exit 0. Returncodes: {returncodes}. "
        f"Stderr[0]: {results[0]['stderr']!r} Stderr[1]: {results[1]['stderr']!r}"
    )

    # (b) No-clobber: STATE.md must exist and contain exactly one writer's intact content
    state_md = tmp_path / ".ba-ops" / "STATE.md"
    assert state_md.exists(), "STATE.md must exist after at least one successful write"
    content = state_md.read_text(encoding="utf-8")

    writer_p1_won = "writer_p1" in content
    writer_p2_won = "writer_p2" in content

    # Exactly one writer's step must be present (no clobber / no interleaving)
    assert writer_p1_won or writer_p2_won, (
        "STATE.md must contain one writer's step value. "
        f"Content: {content!r}"
    )
    assert not (writer_p1_won and writer_p2_won), (
        "STATE.md must contain only ONE writer's step (no-clobber violated). "
        f"Content: {content!r}"
    )

    # (c) Any non-zero writer must have exited 2 with ok:false + LOCK_TIMEOUT
    for r in results:
        if r["returncode"] != 0:
            assert r["returncode"] == 2, (
                f"Non-zero writer must exit 2, got {r['returncode']}. "
                f"stderr={r['stderr']!r}"
            )
            try:
                err = json.loads(r["stderr"])
            except json.JSONDecodeError:
                pytest.fail(
                    f"Non-zero writer stderr is not valid JSON: {r['stderr']!r}"
                )
            assert err["ok"] is False
            codes = [f["code"] for f in err.get("failures", [])]
            assert "LOCK_TIMEOUT" in codes, (
                f"Non-zero writer must report LOCK_TIMEOUT. Failures: {err['failures']}"
            )
