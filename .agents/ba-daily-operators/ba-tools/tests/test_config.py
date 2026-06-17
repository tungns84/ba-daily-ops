"""Tests for .ba-ops/config.json feature-flag defaults (TRACE-02)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement missing config flag defaults to true (TRACE-02)")
def test_missing_config_flag_defaults_to_true(tmp_ba_ops):
    """When config.json is absent, all feature flags default to True."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement present false flag is respected (TRACE-02)")
def test_explicit_false_flag_respected(tmp_ba_ops):
    """When config.json sets a flag to false, the flag is treated as disabled."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: config absence does not write defaults to disk (TRACE-02)")
def test_absent_config_not_written_to_disk(tmp_ba_ops):
    """Reading an absent config.json must not create the file on disk."""
    raise NotImplementedError
