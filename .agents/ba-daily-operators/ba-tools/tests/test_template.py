"""Tests for ba-tools template fill (TOOL-11)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement template fill scaffold write (TOOL-11)")
def test_template_fill_creates_file(tmp_ba_ops):
    """template fill writes a scaffold file with substituted variables."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement template fill --out path traversal guard (TOOL-11, T-1-09)")
def test_template_fill_out_traversal_guard(tmp_ba_ops):
    """template fill rejects --out paths outside the repo root."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement template fill unknown template name exits 2 (TOOL-11)")
def test_template_fill_unknown_name_exits_2(tmp_ba_ops):
    """template fill exits 2 for an unknown template name."""
    raise NotImplementedError
