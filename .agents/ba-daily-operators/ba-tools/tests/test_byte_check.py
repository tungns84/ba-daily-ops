"""Tests for ba-tools byte-check (GATE-04, CDX-04)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement byte-check passes for file < 32768 B (GATE-04)")
def test_file_under_limit_passes(tmp_ba_ops):
    """byte-check exits 0 for a file smaller than 32768 bytes."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement byte-check fails for file >= 32768 B (GATE-04)")
def test_file_at_or_over_limit_fails(tmp_ba_ops):
    """byte-check exits 2 with EXCEEDS_LIMIT failure for a file >= 32768 bytes."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement byte-check FILE_NOT_FOUND error (GATE-04)")
def test_missing_file_fails(tmp_ba_ops):
    """byte-check exits 2 with FILE_NOT_FOUND failure for a non-existent path."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement byte-check --limit override (GATE-04)")
def test_custom_limit_respected(tmp_ba_ops):
    """byte-check respects --limit override."""
    raise NotImplementedError
