"""Tests for ba-tools extract-uc (TOOL-10)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement extract-uc returns UC section and identity (TOOL-10)")
def test_extract_uc_returns_section(tmp_ba_ops):
    """extract-uc returns JSON with ok:true, section text, and parsed UC identity."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement extract-uc level-aware stop on multi-heading doc (TOOL-10)")
def test_extract_uc_level_aware_stop(tmp_ba_ops):
    """extract-uc does not truncate at ### subsections inside a ## UC section."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement extract-uc unknown section exits 2 (TOOL-10)")
def test_extract_uc_not_found_exits_2(tmp_ba_ops):
    """extract-uc exits 2 when the UC heading is not found."""
    raise NotImplementedError
