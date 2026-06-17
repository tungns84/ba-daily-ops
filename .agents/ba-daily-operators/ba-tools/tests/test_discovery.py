"""Tests for ba-tools discovery add|list (TOOL-12)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement discovery add appends to jsonl (TOOL-12)")
def test_discovery_add_appends(tmp_ba_ops):
    """discovery add appends a new entry to .ba-ops/discoveries.jsonl."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement discovery list returns all entries (TOOL-12)")
def test_discovery_list_returns_all(tmp_ba_ops):
    """discovery list returns all previously added discoveries."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement discovery list --uc filter (TOOL-12)")
def test_discovery_list_filters_by_uc(tmp_ba_ops):
    """discovery list --uc UC-001 returns only entries for that UC."""
    raise NotImplementedError
