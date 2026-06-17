"""Tests for ba-tools scan advisory prompt-injection scanner (TOOL-15)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement scan advisory-only exit 0 (TOOL-15)")
def test_scan_clean_file_exits_0(tmp_ba_ops):
    """scan exits 0 for a file with no injection patterns."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement scan advisory WARN on injection pattern (TOOL-15)")
def test_scan_injection_pattern_warns_not_fails(tmp_ba_ops):
    """scan exits 0 even when injection patterns are found; returns WARN in output."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement scan missing file exits 2 (TOOL-15)")
def test_scan_missing_file_exits_2(tmp_ba_ops):
    """scan exits 2 with FILE_NOT_FOUND when the specified file does not exist."""
    raise NotImplementedError
