"""Tests for ba-tools state (TOOL-03) including concurrent-write guard."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement state update action (TOOL-03)")
def test_state_update_writes_fields(tmp_ba_ops):
    """state update writes provided JSON fields to STATE.md."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement state patch action (TOOL-03)")
def test_state_patch_merges_fields(tmp_ba_ops):
    """state patch merges new fields without overwriting existing ones."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement state advance action (TOOL-03)")
def test_state_advance_increments_step(tmp_ba_ops):
    """state advance increments a step counter field."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement concurrent-write no-clobber guard (TOOL-03)")
def test_concurrent_write_no_clobber(tmp_ba_ops):
    """Two concurrent writers: at least one succeeds; no state clobber; loser exits 2."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement stale-lock reclaim (TOOL-03)")
def test_stale_lock_reclaimed(tmp_ba_ops):
    """A stale lock file (mtime > 10s) is reclaimed and the write succeeds."""
    raise NotImplementedError
