"""Tests for ba-tools resolve-route (TOOL-02).

Verifies static DEFAULT_ROUTES dispatch and UNKNOWN_OPERATOR exit-2 gate.
All tests invoke `python -m ba_tools resolve-route` as a subprocess to exercise
the full CLI path (TDD integration style).
"""

import json
import subprocess
import sys

# All 7 operators from DESIGN §4 and their expected default routes
EXPECTED_ROUTES = {
    "ba-uc": "deliver",
    "ba-srs-analyze": "full",
    "ba-mermaid": "author",
    "ba-mockup": "full",
    "ba-make-diagram": "diagram",
    "ba-uc-delivery": "full",
    "ba-backlog-grooming": "full",
}


def _run_resolve_route(*args):
    """Run `python -m ba_tools resolve-route <args>` and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "ba_tools", "resolve-route", *args],
        capture_output=True,
        text=True,
    )


def test_known_operator_returns_default_route():
    """resolve-route ba-mermaid returns {"ok": true, "default_route": "author"}."""
    result = _run_resolve_route("ba-mermaid")
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr={result.stderr!r}"
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["default_route"] == "author"
    assert data["operator"] == "ba-mermaid"
    assert data["failures"] == []


def test_unknown_operator_exits_2():
    """resolve-route unknown-op exits 2 with ok:false JSON on stderr."""
    result = _run_resolve_route("made-up-name")
    assert result.returncode == 2, f"Expected exit 2, got {result.returncode}"
    # Stderr must have structured JSON with UNKNOWN_OPERATOR code
    stderr_data = json.loads(result.stderr)
    assert stderr_data["ok"] is False
    failure_codes = [f["code"] for f in stderr_data["failures"]]
    assert "UNKNOWN_OPERATOR" in failure_codes, f"Expected UNKNOWN_OPERATOR in {failure_codes}"
    # Operator name must be surfaced in the failure
    failure = next(f for f in stderr_data["failures"] if f["code"] == "UNKNOWN_OPERATOR")
    assert failure.get("operator") == "made-up-name"


def test_all_operators_have_routes():
    """All 7 operators in DEFAULT_ROUTES resolve to a non-empty route string."""
    for operator, expected_route in EXPECTED_ROUTES.items():
        result = _run_resolve_route(operator)
        assert result.returncode == 0, (
            f"Operator {operator!r} returned exit {result.returncode}. stderr={result.stderr!r}"
        )
        data = json.loads(result.stdout)
        assert data["ok"] is True, f"Expected ok=true for {operator!r}"
        assert data["default_route"] == expected_route, (
            f"Operator {operator!r}: expected route {expected_route!r}, "
            f"got {data['default_route']!r}"
        )
        assert data["default_route"] != "", f"Route must be non-empty for {operator!r}"


def test_ba_uc_returns_deliver():
    """resolve-route ba-uc returns default_route == 'deliver'."""
    result = _run_resolve_route("ba-uc")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["default_route"] == "deliver"


def test_ba_srs_analyze_returns_full():
    """resolve-route ba-srs-analyze returns default_route == 'full'."""
    result = _run_resolve_route("ba-srs-analyze")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["default_route"] == "full"


def test_no_route_inferred_from_free_text():
    """An operator string that is a substring of a real operator does NOT match."""
    # 'mermaid' (without 'ba-' prefix) is not in the table
    result = _run_resolve_route("mermaid")
    assert result.returncode == 2, (
        "substring 'mermaid' must not match — route comes ONLY from exact dict key"
    )


def test_stdout_empty_on_unknown_operator():
    """Stdout must be empty when an unknown operator causes exit 2."""
    result = _run_resolve_route("nope")
    assert result.returncode == 2
    assert result.stdout.strip() == "", (
        f"Stdout must be empty on error, got: {result.stdout!r}"
    )
