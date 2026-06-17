"""Tests for ba-tools extract-uc (TOOL-10)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ba_tools.markdown_sections import extract


# ---------------------------------------------------------------------------
# Unit tests for markdown_sections.extract (level-aware stop — Pitfall 5)
# ---------------------------------------------------------------------------

MULTI_HEADING_DOC = """\
# Document Title

Some intro text.

## UC-001. Login Flow

This is the overview of the login flow.
Users authenticate using username and password.

### Steps

1. User navigates to login page.
2. User enters credentials.
3. System validates credentials.

### Error Handling

- Invalid credentials shows an error message.

## UC-002. Registration

This is a different UC and should NOT appear in UC-001 extraction.
"""


def test_extract_level_aware_includes_subsections():
    """extract() does NOT stop at a ### subsection inside a ## UC section (Pitfall 5)."""
    body = extract(MULTI_HEADING_DOC, "UC-001. Login Flow", level=2)
    assert body is not None, "expected extract to find the section"
    # Subsections must be included
    assert "### Steps" in body
    assert "### Error Handling" in body
    # The next same-level heading must NOT be included
    assert "UC-002" not in body


def test_extract_stops_at_same_level():
    """extract() stops when it hits a heading at the same level (##)."""
    body = extract(MULTI_HEADING_DOC, "UC-001. Login Flow", level=2)
    assert body is not None
    assert "Registration" not in body


def test_extract_returns_none_for_missing_heading():
    """extract() returns None when the heading is not found."""
    result = extract(MULTI_HEADING_DOC, "UC-999. Missing", level=2)
    assert result is None


def test_extract_case_insensitive_heading():
    """extract() matches headings case-insensitively."""
    body = extract(MULTI_HEADING_DOC, "uc-001. login flow", level=2)
    assert body is not None
    assert "authenticate" in body


# ---------------------------------------------------------------------------
# CLI integration tests for extract-uc
# ---------------------------------------------------------------------------

def _run_extract_uc(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "ba_tools"] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


def test_extract_uc_returns_section(tmp_ba_ops):
    """extract-uc returns JSON with ok:true, section text, and parsed UC identity."""
    doc = tmp_ba_ops / "uc_doc.md"
    doc.write_text(MULTI_HEADING_DOC, encoding="utf-8")

    result = _run_extract_uc(
        ["--repo-root", str(tmp_ba_ops), "extract-uc", "--uc",
         f"{doc}: ## UC-001. Login Flow"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["uc_id"] == "UC-001"
    assert data["uc_name"] == "Login Flow"
    assert "authenticate" in data["section"]


def test_extract_uc_level_aware_stop(tmp_ba_ops):
    """extract-uc does not truncate at ### subsections inside a ## UC section."""
    doc = tmp_ba_ops / "uc_doc.md"
    doc.write_text(MULTI_HEADING_DOC, encoding="utf-8")

    result = _run_extract_uc(
        ["--repo-root", str(tmp_ba_ops), "extract-uc", "--uc",
         f"{doc}: ## UC-001. Login Flow"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    # Subsections must be present (Pitfall 5 — level-aware stop)
    assert "### Steps" in data["section"]
    assert "### Error Handling" in data["section"]
    # The next UC must NOT be in the section
    assert "UC-002" not in data["section"]


def test_extract_uc_not_found_exits_2(tmp_ba_ops):
    """extract-uc exits 2 when the UC heading is not found."""
    doc = tmp_ba_ops / "uc_doc.md"
    doc.write_text(MULTI_HEADING_DOC, encoding="utf-8")

    result = _run_extract_uc(
        ["--repo-root", str(tmp_ba_ops), "extract-uc", "--uc",
         f"{doc}: ## UC-999. Does Not Exist"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 2
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert any(f["code"] == "UC_NOT_FOUND" for f in err_data["failures"])


def test_extract_uc_bad_spec_exits_2(tmp_ba_ops):
    """extract-uc exits 2 with BAD_SPEC for a malformed spec string."""
    result = _run_extract_uc(
        ["--repo-root", str(tmp_ba_ops), "extract-uc", "--uc", "not-a-valid-spec"],
        cwd=tmp_ba_ops,
    )
    assert result.returncode == 2
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert any(f["code"] == "BAD_SPEC" for f in err_data["failures"])
