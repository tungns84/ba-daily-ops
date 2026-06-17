"""Tests for ba-tools resolve-route (TOOL-02)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement resolve-route static dispatch table (TOOL-02)")
def test_known_operator_returns_default_route():
    """resolve-route ba-mermaid returns {"ok": true, "default_route": "author"}."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement resolve-route unknown operator -> exit 2 (TOOL-02)")
def test_unknown_operator_exits_2():
    """resolve-route unknown-op exits 2 with ok:false JSON on stderr."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement resolve-route for all 7 operators (TOOL-02)")
def test_all_operators_have_routes():
    """All 7 operators in DEFAULT_ROUTES resolve to a non-empty route string."""
    raise NotImplementedError
