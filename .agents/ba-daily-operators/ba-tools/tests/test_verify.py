"""Tests for ba-tools verify citation-exists gate (TOOL-06)."""

import json
import sys
import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures directory helper
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "srs"


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


# ---------------------------------------------------------------------------
# Helper: run verify CLI with a requirements JSON file
# ---------------------------------------------------------------------------


def run_verify_json(repo_root, reqs_json_path, source_path=None, cite_scope=None, extra_args=None):
    """Invoke verify via CLI with a JSON requirements file.

    Returns (returncode, stdout_parsed, stderr_parsed).
    """
    cmd = [
        sys.executable, "-m", "ba_tools",
        "--repo-root", str(repo_root),
        "verify",
        "--reqs", str(reqs_json_path),
    ]

    if source_path:
        cmd += ["--source", str(source_path)]

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
# Task 1 JSON verify tests (F1–F4 + doc-mismatch + section-null + schema validation)
# ---------------------------------------------------------------------------


def test_clean_grounded_passes(tmp_path):
    """F1: verify on a requirements.json with all verbatim stated spans exits 0."""
    # Build fixture paths relative to repo root (tmp_path)
    # We copy the fixture into tmp_path so source_trace.doc paths resolve correctly.
    repo_root = tmp_path
    fixture_dir = FIXTURES_DIR / "clean-uc-grounded"

    # Recreate the fixture structure under tmp_path so paths in source_trace.doc resolve
    src_dir = repo_root / "tests" / "fixtures" / "srs" / "clean-uc-grounded"
    src_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy(fixture_dir / "source.md", src_dir / "source.md")
    shutil.copy(fixture_dir / "requirements.json", src_dir / "requirements.json")

    reqs_json = src_dir / "requirements.json"
    rc, out, err = run_verify_json(repo_root, reqs_json)
    assert rc == 0, f"F1: expected exit 0 for all grounded spans; got {rc}, err={err}"
    assert out is not None and out.get("ok") is True, f"F1: expected ok:true; got {out}"


def test_citation_not_found_json(tmp_path):
    """F2: an invented span in requirements.json → exit 2 with CITATION_NOT_FOUND."""
    repo_root = tmp_path
    fixture_dir = FIXTURES_DIR / "ungrounded-span"

    src_dir = repo_root / "tests" / "fixtures" / "srs" / "ungrounded-span"
    src_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy(fixture_dir / "source.md", src_dir / "source.md")
    shutil.copy(fixture_dir / "requirements.json", src_dir / "requirements.json")

    reqs_json = src_dir / "requirements.json"
    rc, out, err = run_verify_json(repo_root, reqs_json)
    assert rc == 2, f"F2: expected exit 2 for invented span; got {rc}, stdout={out}"
    assert err is not None, "F2: expected stderr JSON"
    codes = [f.get("code") for f in (err.get("failures") or [])]
    assert "CITATION_NOT_FOUND" in codes, f"F2: expected CITATION_NOT_FOUND; got {codes}"


def test_paraphrased_span(tmp_path):
    """F3: a paraphrased (non-verbatim) span in requirements.json → exit 2, CITATION_NOT_FOUND."""
    repo_root = tmp_path
    fixture_dir = FIXTURES_DIR / "paraphrased-span"

    src_dir = repo_root / "tests" / "fixtures" / "srs" / "paraphrased-span"
    src_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy(fixture_dir / "source.md", src_dir / "source.md")
    shutil.copy(fixture_dir / "requirements.json", src_dir / "requirements.json")

    reqs_json = src_dir / "requirements.json"
    rc, out, err = run_verify_json(repo_root, reqs_json)
    assert rc == 2, f"F3: expected exit 2 for paraphrased span; got {rc}"
    codes = [f.get("code") for f in (err.get("failures") or [])] if err else []
    assert "CITATION_NOT_FOUND" in codes, f"F3: expected CITATION_NOT_FOUND; got {codes}"


def test_wrong_section_span_default_fails(tmp_path):
    """F4 (default): a verbatim span under a sibling section → exit 2 by default."""
    repo_root = tmp_path
    fixture_dir = FIXTURES_DIR / "wrong-section-span"

    src_dir = repo_root / "tests" / "fixtures" / "srs" / "wrong-section-span"
    src_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy(fixture_dir / "source.md", src_dir / "source.md")
    shutil.copy(fixture_dir / "requirements.json", src_dir / "requirements.json")

    reqs_json = src_dir / "requirements.json"
    rc, out, err = run_verify_json(repo_root, reqs_json)
    assert rc == 2, f"F4-default: expected exit 2 for wrong-section span; got {rc}"
    codes = [f.get("code") for f in (err.get("failures") or [])] if err else []
    assert "CITATION_NOT_FOUND" in codes, f"F4-default: expected CITATION_NOT_FOUND; got {codes}"


def test_wrong_section_span_document_scope_passes(tmp_path):
    """F4 (--cite-scope document): same verbatim span with document scope → exit 0."""
    repo_root = tmp_path
    fixture_dir = FIXTURES_DIR / "wrong-section-span"

    src_dir = repo_root / "tests" / "fixtures" / "srs" / "wrong-section-span"
    src_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy(fixture_dir / "source.md", src_dir / "source.md")
    shutil.copy(fixture_dir / "requirements.json", src_dir / "requirements.json")

    reqs_json = src_dir / "requirements.json"
    rc, out, err = run_verify_json(repo_root, reqs_json, cite_scope="document")
    assert rc == 0, f"F4-document: expected exit 0 with --cite-scope document; got {rc}, err={err}"
    assert out is not None and out.get("ok") is True


def test_section_null_document_scope(tmp_path):
    """D-03: a stated requirement with section:null is searched document-scope → exits 0."""
    repo_root = tmp_path
    fixture_dir = FIXTURES_DIR / "section-null-doc-scope"

    src_dir = repo_root / "tests" / "fixtures" / "srs" / "section-null-doc-scope"
    src_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy(fixture_dir / "source.md", src_dir / "source.md")
    shutil.copy(fixture_dir / "requirements.json", src_dir / "requirements.json")

    reqs_json = src_dir / "requirements.json"
    rc, out, err = run_verify_json(repo_root, reqs_json)
    assert rc == 0, f"section:null doc-scope: expected exit 0; got {rc}, err={err}"
    assert out is not None and out.get("ok") is True


def test_source_trace_doc_used(tmp_path):
    """verify resolves cited doc from source_trace.doc even when --source is omitted."""
    repo_root = tmp_path
    fixture_dir = FIXTURES_DIR / "clean-uc-grounded"

    src_dir = repo_root / "tests" / "fixtures" / "srs" / "clean-uc-grounded"
    src_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy(fixture_dir / "source.md", src_dir / "source.md")
    shutil.copy(fixture_dir / "requirements.json", src_dir / "requirements.json")

    reqs_json = src_dir / "requirements.json"
    # No --source argument — must resolve from source_trace.doc
    rc, out, err = run_verify_json(repo_root, reqs_json, source_path=None)
    assert rc == 0, (
        f"test_source_trace_doc_used: expected exit 0 without --source; got {rc}, err={err}"
    )
    assert out is not None and out.get("ok") is True


def test_source_trace_doc_mismatch(tmp_path):
    """When --source is source_a.md but source_trace.doc points at source_b.md,
    the gate is evaluated against source_b.md (where the span actually exists)."""
    repo_root = tmp_path
    fixture_dir = FIXTURES_DIR / "doc-mismatch"

    src_dir = repo_root / "tests" / "fixtures" / "srs" / "doc-mismatch"
    src_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy(fixture_dir / "source_a.md", src_dir / "source_a.md")
    shutil.copy(fixture_dir / "source_b.md", src_dir / "source_b.md")
    shutil.copy(fixture_dir / "requirements.json", src_dir / "requirements.json")

    reqs_json = src_dir / "requirements.json"
    source_a = src_dir / "source_a.md"

    # --source points at source_a (which does NOT have the span),
    # but source_trace.doc points at source_b (which DOES have the span).
    # The gate must use source_trace.doc → should pass.
    rc, out, err = run_verify_json(repo_root, reqs_json, source_path=source_a)
    assert rc == 0, (
        f"test_source_trace_doc_mismatch: expected exit 0 because source_trace.doc "
        f"(source_b) has the span, not --source (source_a); got {rc}, err={err}"
    )
    assert out is not None and out.get("ok") is True


def test_malformed_json(tmp_path):
    """A non-parseable .json requirements file → exit 2 with MALFORMED_JSON (never exit 1)."""
    repo_root = tmp_path
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not valid json{{", encoding="utf-8")

    rc, out, err = run_verify_json(repo_root, bad_json)
    assert rc == 2, f"test_malformed_json: expected exit 2; got {rc}"
    codes = [f.get("code") for f in (err.get("failures") or [])] if err else []
    assert "MALFORMED_JSON" in codes, f"test_malformed_json: expected MALFORMED_JSON; got {codes}"


@pytest.mark.parametrize("bad_payload,expected_code", [
    # Non-list, non-dict payload
    ('"just a string"', "SCHEMA_INVALID"),
    # Dict with no requirements key
    ('{"other": []}', "SCHEMA_INVALID"),
    # Dict with non-list requirements
    ('{"requirements": "not a list"}', "SCHEMA_INVALID"),
    # Missing id field
    ('{"requirements": [{"statement": "desc", "status": "stated", "source_trace": {"doc": "x.md", "span": "long enough span text", "section": "S1"}}]}', "INVALID_REQUIREMENT"),
    # Missing statement field
    ('{"requirements": [{"id": "R-01", "status": "stated", "source_trace": {"doc": "x.md", "span": "long enough span text", "section": "S1"}}]}', "INVALID_REQUIREMENT"),
    # Invalid status value
    ('{"requirements": [{"id": "R-01", "statement": "desc", "status": "unknown", "source_trace": {"doc": "x.md", "span": "long enough span text", "section": "S1"}}]}', "INVALID_REQUIREMENT"),
    # stated requirement missing source_trace.span
    ('{"requirements": [{"id": "R-01", "statement": "desc", "status": "stated", "source_trace": {"doc": "x.md", "section": "S1"}}]}', "INVALID_REQUIREMENT"),
])
def test_schema_invalid_shapes(tmp_path, bad_payload, expected_code):
    """Each schema-invalid shape exits 2 with SCHEMA_INVALID or INVALID_REQUIREMENT."""
    bad_json = tmp_path / "schema_bad.json"
    bad_json.write_text(bad_payload, encoding="utf-8")

    rc, out, err = run_verify_json(tmp_path, bad_json)
    assert rc == 2, (
        f"test_schema_invalid_shapes: expected exit 2 for payload={bad_payload!r}; got {rc}"
    )
    codes = [f.get("code") for f in (err.get("failures") or [])] if err else []
    assert expected_code in codes, (
        f"test_schema_invalid_shapes: expected {expected_code} for payload={bad_payload!r}; got codes={codes}"
    )


def test_reqs_format_md_backward_compat(tmp_path, citation_pass_doc):
    """Existing Markdown reqs file still verifies via _parse_md_table (backward compat)."""
    reqs_md = tmp_path / "reqs.md"
    reqs_md.write_text(
        f"""# Requirements

| ID | Statement | Status | Source | Section | Span |
|----|-----------|--------|--------|---------|------|
| FR-001 | The system shall return a JSON response. | stated | {citation_pass_doc} | Requirements | All requirements must be traceable to source documents. |
""",
        encoding="utf-8",
    )
    cmd = [
        sys.executable, "-m", "ba_tools",
        "--repo-root", str(tmp_path),
        "verify",
        "--reqs", str(reqs_md),
        "--source", str(citation_pass_doc),
        "--reqs-format", "md",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"test_reqs_format_md_backward_compat: expected exit 0; got {result.returncode}, "
        f"stderr={result.stderr}"
    )


def test_parse_reqs_json_preserves_source_trace_dict(tmp_path):
    """Unit test: _parse_reqs on a json string preserves source_trace dict in output row."""
    from ba_tools.commands.verify_cmd import _parse_reqs

    reqs_text = json.dumps({
        "requirements": [{
            "id": "FR-001",
            "statement": "The system shall do something important.",
            "status": "stated",
            "source_trace": {
                "doc": "path/to/source.md",
                "span": "something important span text here",
                "section": "Section 1"
            }
        }]
    })

    reqs_path = tmp_path / "reqs.json"
    rows = _parse_reqs(reqs_text, reqs_path, "json")

    assert len(rows) == 1
    row = rows[0]
    assert row.get("id") == "FR-001"
    assert isinstance(row.get("source_trace"), dict), (
        f"Expected source_trace to be dict; got {type(row.get('source_trace'))}"
    )
    assert row["source_trace"]["doc"] == "path/to/source.md", (
        f"Expected source_trace.doc preserved; got {row['source_trace']}"
    )
