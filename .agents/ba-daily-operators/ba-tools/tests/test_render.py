"""Tests for srs_render.py + render_cmd.py (Task 2, plan 02-02).

TDD RED phase: all tests expected to FAIL before implementation exists.

Tests cover:
  - render_srs: pure function over requirements.json doc → IEEE-830 Markdown
  - render_registry: pure function over list of docs → REQUIREMENTS.md table (UNION, D-08)
  - CLI: ba-tools render srs --slug / ba-tools render registry
  - Determinism: same input → byte-identical output
  - PATH_TRAVERSAL guard on --slug
  - Registry union: two slugs, REQUIREMENTS.md contains both slugs' ids (D-08 review HIGH)
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PYTHON = sys.executable

# ---------------------------------------------------------------------------
# Minimal reqs_doc fixtures
# ---------------------------------------------------------------------------

REQS_DOC_SIMPLE = {
    "requirements": [
        {
            "id": "FR-001",
            "statement": "The system shall allow users to log in with username and password.",
            "status": "stated",
            "source_trace": {"doc": "source.md", "span": "...", "section": "§2"},
        },
        {
            "id": "NFR-001",
            "statement": "Response time shall be under 200ms for 95th percentile.",
            "status": "derived",
            "source_trace": {},
        },
        {
            "id": "BR-001",
            "statement": "The system must comply with GDPR data retention policies.",
            "status": "derived",
            "source_trace": {},
        },
    ]
}

REQS_DOC_ALPHA = {
    "requirements": [
        {
            "id": "FR-001",
            "statement": "Alpha feature: users can register an account.",
            "status": "stated",
            "source_trace": {"doc": "alpha.md", "span": "users can register", "section": "§1"},
        },
    ]
}

REQS_DOC_BETA = {
    "requirements": [
        {
            "id": "FR-100",
            "statement": "Beta feature: users can export data as CSV.",
            "status": "derived",
            "source_trace": {},
        },
    ]
}

SRS_TEMPLATE_MIN = """# SRS: ${title}

## 1. Introduction

### 1.1 Purpose

${purpose}

### 1.2 Scope

${scope}

### 1.3 Definitions

${definitions}

## 2. Overall Description

${overall_description}

## 3. Specific Requirements

### 3.1 Functional Requirements

${functional_requirements}

### 3.2 Non-Functional Requirements

${nonfunctional_requirements}

### 3.3 Business Rules

${business_rules}

### 3.4 External Interfaces

${external_interfaces}

### 3.5 Constraints

${constraints}

## 4. Appendices

${appendices}

## 5. Traceability

${traceability}
"""


# ---------------------------------------------------------------------------
# Unit tests for render_srs pure function
# ---------------------------------------------------------------------------


def test_render_srs_contains_ieee830_headings():
    """render_srs output must contain §1-§5 headings."""
    from ba_tools.srs_render import render_srs

    result = render_srs(REQS_DOC_SIMPLE, SRS_TEMPLATE_MIN)

    assert "## 1. Introduction" in result, "Missing §1 Introduction"
    assert "## 2. Overall Description" in result, "Missing §2 Overall Description"
    assert "## 3. Specific Requirements" in result, "Missing §3 Specific Requirements"
    assert "## 4. Appendices" in result, "Missing §4 Appendices"
    assert "## 5. Traceability" in result, "Missing §5 Traceability"


def test_render_srs_fr_under_31():
    """FR-001 must appear under §3.1 Functional Requirements."""
    from ba_tools.srs_render import render_srs

    result = render_srs(REQS_DOC_SIMPLE, SRS_TEMPLATE_MIN)

    # Find the 3.1 section and confirm FR-001 is there
    idx_31 = result.find("### 3.1 Functional Requirements")
    idx_32 = result.find("### 3.2 Non-Functional Requirements")
    assert idx_31 != -1, "§3.1 Functional Requirements heading not found"
    assert idx_32 != -1, "§3.2 Non-Functional Requirements heading not found"

    section_31 = result[idx_31:idx_32]
    assert "FR-001" in section_31, f"FR-001 not under §3.1. Section content:\n{section_31}"


def test_render_srs_nfr_under_32():
    """NFR-001 must appear under §3.2 Non-Functional Requirements."""
    from ba_tools.srs_render import render_srs

    result = render_srs(REQS_DOC_SIMPLE, SRS_TEMPLATE_MIN)

    idx_32 = result.find("### 3.2 Non-Functional Requirements")
    idx_33 = result.find("### 3.3 Business Rules")
    assert idx_32 != -1, "§3.2 Non-Functional Requirements heading not found"
    assert idx_33 != -1, "§3.3 Business Rules heading not found"

    section_32 = result[idx_32:idx_33]
    assert "NFR-001" in section_32, f"NFR-001 not under §3.2. Section content:\n{section_32}"


def test_render_srs_br_under_33():
    """BR-001 must appear under §3.3 Business Rules."""
    from ba_tools.srs_render import render_srs

    result = render_srs(REQS_DOC_SIMPLE, SRS_TEMPLATE_MIN)

    idx_33 = result.find("### 3.3 Business Rules")
    idx_34 = result.find("### 3.4 External Interfaces")
    assert idx_33 != -1, "§3.3 Business Rules heading not found"
    assert idx_34 != -1, "§3.4 External Interfaces heading not found"

    section_33 = result[idx_33:idx_34]
    assert "BR-001" in section_33, f"BR-001 not under §3.3. Section content:\n{section_33}"


def test_render_srs_contains_statements():
    """Each requirement's statement must appear in the rendered output."""
    from ba_tools.srs_render import render_srs

    result = render_srs(REQS_DOC_SIMPLE, SRS_TEMPLATE_MIN)

    for req in REQS_DOC_SIMPLE["requirements"]:
        assert req["statement"] in result, (
            f"Statement for {req['id']} not found in rendered SRS"
        )


def test_render_srs_deterministic():
    """Rendering the same doc twice must produce byte-identical output."""
    from ba_tools.srs_render import render_srs

    result1 = render_srs(REQS_DOC_SIMPLE, SRS_TEMPLATE_MIN)
    result2 = render_srs(REQS_DOC_SIMPLE, SRS_TEMPLATE_MIN)

    assert result1 == result2, "render_srs is not deterministic"


# ---------------------------------------------------------------------------
# Unit tests for render_registry pure function
# ---------------------------------------------------------------------------


def test_render_registry_contains_all_ids():
    """render_registry over [alpha_doc, beta_doc] must contain both FR-001 and FR-100."""
    from ba_tools.srs_render import render_registry

    result = render_registry([REQS_DOC_ALPHA, REQS_DOC_BETA])

    assert "FR-001" in result, "FR-001 missing from registry union"
    assert "FR-100" in result, "FR-100 missing from registry union"


def test_render_registry_deterministic():
    """render_registry called twice must produce byte-identical output."""
    from ba_tools.srs_render import render_registry

    r1 = render_registry([REQS_DOC_ALPHA, REQS_DOC_BETA])
    r2 = render_registry([REQS_DOC_ALPHA, REQS_DOC_BETA])

    assert r1 == r2, "render_registry is not deterministic"


def test_render_registry_union_order_independent():
    """render_registry must contain the same ids regardless of input list order."""
    from ba_tools.srs_render import render_registry

    r_ab = render_registry([REQS_DOC_ALPHA, REQS_DOC_BETA])
    r_ba = render_registry([REQS_DOC_BETA, REQS_DOC_ALPHA])

    assert "FR-001" in r_ab and "FR-100" in r_ab
    assert "FR-001" in r_ba and "FR-100" in r_ba


def test_render_registry_single_doc_not_dropped():
    """registry rendered after only alpha then re-rendered with both must never drop FR-001 (D-08)."""
    from ba_tools.srs_render import render_registry

    # Render after only alpha
    r_alpha_only = render_registry([REQS_DOC_ALPHA])
    assert "FR-001" in r_alpha_only, "FR-001 missing after alpha-only render"

    # Re-render with both slugs
    r_both = render_registry([REQS_DOC_ALPHA, REQS_DOC_BETA])
    assert "FR-001" in r_both, "FR-001 dropped when adding beta slug (D-08 violation)"
    assert "FR-100" in r_both, "FR-100 missing after union render"


# ---------------------------------------------------------------------------
# CLI integration tests for render command
# ---------------------------------------------------------------------------


def _run_render(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, "-m", "ba_tools"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_render_help_succeeds(tmp_path):
    """ba-tools render --help must exit 0 (command is registered)."""
    result = _run_render(["--repo-root", str(tmp_path), "render", "--help"], cwd=tmp_path)
    assert result.returncode == 0, (
        f"ba-tools render --help failed: {result.stderr}"
    )


def test_render_srs_writes_srs_md(tmp_path):
    """ba-tools render srs --slug demo writes .ba-ops/srs/demo/SRS.md."""
    slug = "demo"
    slug_dir = tmp_path / ".ba-ops" / "srs" / slug
    slug_dir.mkdir(parents=True)

    # Write a valid requirements.json
    reqs_path = slug_dir / "requirements.json"
    reqs_path.write_text(json.dumps(REQS_DOC_SIMPLE), encoding="utf-8")

    result = _run_render(
        ["--repo-root", str(tmp_path), "render", "srs", "--slug", slug],
        cwd=tmp_path,
    )
    assert result.returncode == 0, (
        f"render srs failed: rc={result.returncode}, stderr={result.stderr}"
    )

    srs_out = slug_dir / "SRS.md"
    assert srs_out.exists(), f"SRS.md not written at {srs_out}"
    content = srs_out.read_text(encoding="utf-8")
    assert "FR-001" in content, "FR-001 missing from SRS.md"
    assert "NFR-001" in content, "NFR-001 missing from SRS.md"
    assert "BR-001" in content, "BR-001 missing from SRS.md"


def test_render_srs_byte_identical_twice(tmp_path):
    """Rendering the same slug twice produces byte-identical SRS.md (determinism gate)."""
    slug = "det-test"
    slug_dir = tmp_path / ".ba-ops" / "srs" / slug
    slug_dir.mkdir(parents=True)

    reqs_path = slug_dir / "requirements.json"
    reqs_path.write_text(json.dumps(REQS_DOC_SIMPLE), encoding="utf-8")

    _run_render(
        ["--repo-root", str(tmp_path), "render", "srs", "--slug", slug],
        cwd=tmp_path,
    )
    content1 = (slug_dir / "SRS.md").read_text(encoding="utf-8")

    _run_render(
        ["--repo-root", str(tmp_path), "render", "srs", "--slug", slug],
        cwd=tmp_path,
    )
    content2 = (slug_dir / "SRS.md").read_text(encoding="utf-8")

    assert content1 == content2, "render srs not deterministic: two renders differ"


def test_render_registry_writes_requirements_md(tmp_path):
    """ba-tools render registry writes .ba-ops/REQUIREMENTS.md with union of all slugs."""
    # Set up two slugs
    for slug, doc in [("alpha", REQS_DOC_ALPHA), ("beta", REQS_DOC_BETA)]:
        d = tmp_path / ".ba-ops" / "srs" / slug
        d.mkdir(parents=True)
        (d / "requirements.json").write_text(json.dumps(doc), encoding="utf-8")

    result = _run_render(
        ["--repo-root", str(tmp_path), "render", "registry"],
        cwd=tmp_path,
    )
    assert result.returncode == 0, (
        f"render registry failed: rc={result.returncode}, stderr={result.stderr}"
    )

    reg_path = tmp_path / ".ba-ops" / "REQUIREMENTS.md"
    assert reg_path.exists(), f"REQUIREMENTS.md not written at {reg_path}"
    content = reg_path.read_text(encoding="utf-8")
    assert "FR-001" in content, "FR-001 missing from REQUIREMENTS.md union"
    assert "FR-100" in content, "FR-100 missing from REQUIREMENTS.md union"


def test_registry_union_all_slugs(tmp_path):
    """D-08 / review HIGH: registry union with alpha+beta contains both ids.

    Simulates: render after only alpha, then re-render with both.
    REQUIREMENTS.md must never drop FR-001 when beta is added.
    """
    # Phase 1: only alpha
    alpha_dir = tmp_path / ".ba-ops" / "srs" / "alpha"
    alpha_dir.mkdir(parents=True)
    (alpha_dir / "requirements.json").write_text(json.dumps(REQS_DOC_ALPHA), encoding="utf-8")

    r1 = _run_render(
        ["--repo-root", str(tmp_path), "render", "registry"],
        cwd=tmp_path,
    )
    assert r1.returncode == 0
    content1 = (tmp_path / ".ba-ops" / "REQUIREMENTS.md").read_text(encoding="utf-8")
    assert "FR-001" in content1, "FR-001 missing from registry (alpha-only phase)"

    # Phase 2: add beta, re-render
    beta_dir = tmp_path / ".ba-ops" / "srs" / "beta"
    beta_dir.mkdir(parents=True)
    (beta_dir / "requirements.json").write_text(json.dumps(REQS_DOC_BETA), encoding="utf-8")

    r2 = _run_render(
        ["--repo-root", str(tmp_path), "render", "registry"],
        cwd=tmp_path,
    )
    assert r2.returncode == 0
    content2 = (tmp_path / ".ba-ops" / "REQUIREMENTS.md").read_text(encoding="utf-8")
    assert "FR-001" in content2, "FR-001 dropped from REQUIREMENTS.md after adding beta (D-08)"
    assert "FR-100" in content2, "FR-100 missing from REQUIREMENTS.md after union"


def test_render_srs_slug_path_traversal(tmp_path):
    """A --slug containing '..' that escapes repo root must exit 2 with PATH_TRAVERSAL."""
    result = _run_render(
        ["--repo-root", str(tmp_path), "render", "srs", "--slug", "../../evil"],
        cwd=tmp_path,
    )
    assert result.returncode == 2, (
        f"Expected exit 2 for path traversal slug; got {result.returncode}"
    )
    err = json.loads(result.stderr)
    codes = [f.get("code") for f in err.get("failures", [])]
    assert "PATH_TRAVERSAL" in codes, f"Expected PATH_TRAVERSAL in failures; got {codes}"


def test_render_srs_missing_reqs_json(tmp_path):
    """render srs on a slug with no requirements.json exits 2 with FILE_NOT_FOUND."""
    slug_dir = tmp_path / ".ba-ops" / "srs" / "no-reqs"
    slug_dir.mkdir(parents=True)
    # Do NOT write requirements.json

    result = _run_render(
        ["--repo-root", str(tmp_path), "render", "srs", "--slug", "no-reqs"],
        cwd=tmp_path,
    )
    assert result.returncode == 2, (
        f"Expected exit 2 for missing requirements.json; got {result.returncode}"
    )
    err = json.loads(result.stderr)
    codes = [f.get("code") for f in err.get("failures", [])]
    assert "FILE_NOT_FOUND" in codes, f"Expected FILE_NOT_FOUND in failures; got {codes}"


def test_render_registry_empty_is_ok(tmp_path):
    """render registry with no slugs (empty .ba-ops/srs/) exits 0, writes empty registry."""
    srs_dir = tmp_path / ".ba-ops" / "srs"
    srs_dir.mkdir(parents=True)

    result = _run_render(
        ["--repo-root", str(tmp_path), "render", "registry"],
        cwd=tmp_path,
    )
    assert result.returncode == 0, (
        f"render registry with empty srs/ should exit 0; got {result.returncode}, "
        f"stderr={result.stderr}"
    )
