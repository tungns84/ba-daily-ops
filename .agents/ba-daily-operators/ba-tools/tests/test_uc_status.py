"""Tests for ba-tools uc-status (TOOL-09)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement uc-status returns pipeline state + next_step (TOOL-09)")
def test_uc_status_returns_pipeline_state(tmp_ba_ops):
    """uc-status returns JSON with ok:true, pipeline state, and next_step field."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement uc-status for unknown UC ID (TOOL-09)")
def test_uc_status_unknown_uc_exits_2(tmp_ba_ops):
    """uc-status exits 2 when the requested UC ID is not in STATE.md."""
    raise NotImplementedError
