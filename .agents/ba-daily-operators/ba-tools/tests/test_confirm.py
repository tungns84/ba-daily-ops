"""Tests for ba-tools confirm gate (GATE-02)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement confirm pass-through exit 0 (GATE-02)")
def test_confirm_exits_0():
    """confirm always exits 0 in v1 (pass-through gate)."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement confirm --yes flag (GATE-02)")
def test_confirm_with_yes_flag_exits_0():
    """confirm --yes exits 0 (non-interactive bypass)."""
    raise NotImplementedError
