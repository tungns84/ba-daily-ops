"""Tests for ba-tools init (TOOL-01, TRACE-01)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement init scaffold creation (TOOL-01, TRACE-01)")
def test_init_creates_ba_ops_scaffold(tmp_ba_ops):
    """init creates .ba-ops/ with PROJECT.md, REQUIREMENTS.md, INDEX.md, STATE.md, config.json."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement init returns context JSON (TOOL-01)")
def test_init_returns_context_json(tmp_ba_ops):
    """init stdout is valid JSON with ok:true, config, routes, default_route, state keys."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement init idempotency (TOOL-01)")
def test_init_idempotent(tmp_ba_ops):
    """Running init twice on the same root does not error or duplicate files."""
    raise NotImplementedError
