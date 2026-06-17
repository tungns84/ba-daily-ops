"""Tests for ba-tools verify citation-exists gate (TOOL-06)."""

import json
import sys
import subprocess
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_verify(tmp_path, reqs_content, source_doc_path, cite_scope=None, extra_args=None):
    """Write requirements to a temp file and invoke verify via CLI.

    Returns (returncode, stdout_parsed, stderr_parsed).
    """
    reqs_file = tmp_path / "reqs.md"
    reqs_file.write_text(reqs_content, encoding="utf-8")

    cmd = [
        sys.executable, "-m", "ba_tools",
        "--repo-root", str(tmp_path),
        "verify",
        "--reqs", str(reqs_file),
        "--source", str(source_doc_path),
    ]

    if cite_scope:
        cmd += ["--cite-scope", cite_scope]

    if extra_args:
        cmd += extra_args

    result = subprocess.run(cmd, capture_output=True, text=True)

    stdout_parsed = None
    if result.stdout.strip():
        try:
            stdout_parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass

    stderr_parsed = None
    if result.stderr.strip():
        try:
            stderr_parsed = json.loads(result.stderr)
        except json.JSONDecodeError:
            pass

    return result.returncode, stdout_parsed, stderr_parsed


# ---------------------------------------------------------------------------
# citation.py unit tests (direct import)
# ---------------------------------------------------------------------------


def test_extract_section_returns_body():
    """extract_section returns the body text under the named heading."""
    from ba_tools.citation import extract_section

    doc = """# Overview

Some intro text.

## Requirements

All requirements must be traceable to source documents.
This section has specific content about requirements.

## Background

Different section.
"""
    body = extract_section(doc, "Requirements")
    assert "traceable to source documents" in body
    assert "Different section" not in body


def test_extract_section_normalizes_heading_prefix():
    """extract_section matches section even when section_name has ## prefix (Pitfall 2)."""
    from ba_tools.citation import extract_section

    doc = """# Doc

## 2.1 Requirements

This is the requirements body with specific content here.

## Background

Other section.
"""
    # section_name stored with ## prefix, as Pitfall 2 warns
    body = extract_section(doc, "## 2.1 Requirements")
    assert "requirements body with specific content" in body, (
        f"Section not found with ##-prefixed name; body='{body}'"
    )


def test_extract_section_not_found_returns_empty():
    """extract_section returns empty string for a nonexistent section."""
    from ba_tools.citation import extract_section

    doc = "# Only One Section\n\nSome text.\n"
    body = extract_section(doc, "Nonexistent Section")
    assert body == ""


def test_citation_exists_in_section_returns_true(citation_pass_doc):
    """citation_exists returns True for a >=12-char span inside the Requirements section."""
    from ba_tools.citation import citation_exists

    # The citation_pass_doc fixture has "All requirements must be traceable to source documents."
    # inside the ## Requirements section
    result = citation_exists(citation_pass_doc, "All requirements must be traceable", "Requirements")
    assert result is True, "Expected True for span inside Requirements section"


def test_citation_exists_outside_section_returns_false(citation_fail_doc):
    """citation_exists returns False when span exists only outside the cited section."""
    from ba_tools.citation import citation_exists

    # citation_fail_doc: span is in ## Requirements (not in ## Background)
    # We test with section="Background" where it does NOT appear
    result = citation_exists(
        citation_fail_doc,
        "validates all input paths",
        "Background",
        cite_scope="section",
    )
    assert result is False, (
        "Expected False for span that exists in Requirements, not Background"
    )


def test_citation_exists_too_short_returns_false(citation_pass_doc):
    """citation_exists returns False for a span shorter than 12 chars."""
    from ba_tools.citation import citation_exists

    result = citation_exists(citation_pass_doc, "short", "Requirements")
    assert result is False, "Expected False for span < 12 chars"
    # Also test exactly 11 chars
    result_11 = citation_exists(citation_pass_doc, "requirement", "Requirements")
    assert result_11 is False, "Expected False for 11-char span"


def test_citation_exists_document_scope(citation_fail_doc):
    """citation_exists with cite_scope='document' finds span anywhere in the file."""
    from ba_tools.citation import citation_exists

    # In citation_fail_doc, 'The system validates all input paths using pathlib resolution.'
    # appears in the Requirements section. With --cite-scope document it should pass
    # regardless of which section argument is given.
    result = citation_exists(
        citation_fail_doc,
        "validates all input paths using pathlib",
        "Background",
        cite_scope="document",
    )
    assert result is True, (
        "Expected True with cite_scope='document' even though span is not in Background"
    )


def test_citation_exists_section_with_number_prefix(tmp_path):
    """extract_section matches '## 2.1 Requirements' heading when section='2.1 Requirements'."""
    from ba_tools.citation import citation_exists

    doc = tmp_path / "doc.md"
    doc.write_text(
        """# Project

## 2.1 Requirements

This is the content that shall be verifiable and traceable.

## 2.2 Background

Other content not relevant here.
""",
        encoding="utf-8",
    )
    # section name without ## prefix
    result = citation_exists(doc, "shall be verifiable and traceable", "2.1 Requirements")
    assert result is True, "Expected True when section name matches normalized heading"


# ---------------------------------------------------------------------------
# verify CLI integration tests
# ---------------------------------------------------------------------------


def test_verify_pass_in_section(tmp_path, citation_pass_doc):
    """verify exits 0 when a stated req cites a real >=12-char in-section span."""
    # citation_pass_doc has "All requirements must be traceable to source documents."
    # inside ## Requirements
    reqs = f"""# Requirements

| ID | Statement | Status | Source | Section | Span |
|----|-----------|--------|--------|---------|------|
| TOOL-01 | The system shall return a JSON response within 200ms. | stated | {citation_pass_doc} | Requirements | All requirements must be traceable to source documents. |
"""
    rc, out, err = run_verify(tmp_path, reqs, citation_pass_doc)
    assert rc == 0, f"Expected exit 0 for valid in-section span; got {rc}, err={err}"
    assert out is not None and out.get("ok") is True


def test_verify_fail_span_not_in_section(tmp_path, citation_fail_doc):
    """verify exits 2 with CITATION_NOT_FOUND when span is absent from the cited section."""
    # In citation_fail_doc, the span 'validates all input paths using pathlib resolution'
    # appears in ## Requirements, not in ## Background.
    # We cite it against ## Background -> should fail.
    reqs = f"""# Requirements

| ID | Statement | Status | Source | Section | Span |
|----|-----------|--------|--------|---------|------|
| TOOL-01 | The system shall validate all input paths. | stated | {citation_fail_doc} | Background | validates all input paths using pathlib resolution |
"""
    rc, out, err = run_verify(tmp_path, reqs, citation_fail_doc)
    assert rc == 2, f"Expected exit 2 for span outside section; got {rc}, stdout={out}"
    assert err is not None and err.get("ok") is False
    codes = [f.get("code") for f in err.get("failures", [])]
    assert "CITATION_NOT_FOUND" in codes, f"Expected CITATION_NOT_FOUND in failures; got {codes}"


def test_verify_cite_scope_document_override(tmp_path, citation_fail_doc):
    """verify --cite-scope document flips an out-of-section span to pass (Open Decision #1)."""
    reqs = f"""# Requirements

| ID | Statement | Status | Source | Section | Span |
|----|-----------|--------|--------|---------|------|
| TOOL-01 | The system shall validate all input paths. | stated | {citation_fail_doc} | Background | validates all input paths using pathlib resolution |
"""
    rc, out, err = run_verify(tmp_path, reqs, citation_fail_doc, cite_scope="document")
    assert rc == 0, (
        f"Expected exit 0 with --cite-scope document; got {rc}, err={err}"
    )
    assert out is not None and out.get("ok") is True


def test_verify_warn_only_exits_zero(tmp_path, citation_pass_doc):
    """verify exits 0 when findings are WARN-only (no FAIL) — D-08."""
    # Requirement with weasel word (WARN) but valid citation
    reqs = f"""# Requirements

| ID | Statement | Status | Source | Section | Span |
|----|-----------|--------|--------|---------|------|
| TOOL-01 | The system shall provide a flexible response within 200ms. | stated | {citation_pass_doc} | Requirements | All requirements must be traceable to source documents. |
"""
    rc, out, err = run_verify(tmp_path, reqs, citation_pass_doc)
    assert rc == 0, f"Expected exit 0 for WARN-only result; got {rc}, err={err}"
    # Output may contain warn findings but no fail
    if out:
        findings = out.get("findings", [])
        fail_findings = [f for f in findings if f.get("severity") == "fail"]
        assert len(fail_findings) == 0, f"Expected no FAIL findings; got {fail_findings}"


def test_verify_span_too_short_fails(tmp_path, citation_pass_doc):
    """verify exits 2 when cited span is shorter than 12 chars (CITATION_NOT_FOUND)."""
    reqs = f"""# Requirements

| ID | Statement | Status | Source | Section | Span |
|----|-----------|--------|--------|---------|------|
| TOOL-01 | The system shall return a JSON response. | stated | {citation_pass_doc} | Requirements | short |
"""
    rc, out, err = run_verify(tmp_path, reqs, citation_pass_doc)
    assert rc == 2, f"Expected exit 2 for span < 12 chars; got {rc}, out={out}"
    assert err is not None and err.get("ok") is False
    codes = [f.get("code") for f in err.get("failures", [])]
    assert "CITATION_NOT_FOUND" in codes, f"Expected CITATION_NOT_FOUND in failures; got {codes}"


def test_verify_no_stated_reqs_exits_zero(tmp_path, citation_pass_doc):
    """verify exits 0 with ok:true when there are no stated requirements to check."""
    reqs = """# Requirements

| ID | Statement | Status | Source |
|----|-----------|--------|--------|
"""
    rc, out, err = run_verify(tmp_path, reqs, citation_pass_doc)
    assert rc == 0, f"Expected exit 0 for empty requirements; got {rc}, err={err}"
    assert out is not None and out.get("ok") is True
