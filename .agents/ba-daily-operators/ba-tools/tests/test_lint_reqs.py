"""Tests for ba-tools lint-requirements (TOOL-04, TOOL-05)."""

import json
import re
import sys
import subprocess
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_lint(tmp_path, reqs_content, baseline_content=None, extra_args=None):
    """Write requirements to a temp file and invoke lint-requirements via CLI.

    Returns (returncode, stdout_parsed, stderr_parsed).
    stdout_parsed is None if stdout is empty / not valid JSON.
    """
    reqs_file = tmp_path / "reqs.md"
    reqs_file.write_text(reqs_content, encoding="utf-8")

    # Pass --repo-root so path-safety check uses tmp_path as root (T-1-01)
    cmd = [
        sys.executable, "-m", "ba_tools",
        "--repo-root", str(tmp_path),
        "lint-requirements", str(reqs_file),
    ]

    if baseline_content is not None:
        baseline_file = tmp_path / "baseline.md"
        baseline_file.write_text(baseline_content, encoding="utf-8")
        cmd += ["--baseline", str(baseline_file)]

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


def findings_with_code(parsed_output, code):
    """Return all findings matching the given code from ok_json output."""
    if parsed_output is None:
        return []
    findings = parsed_output.get("findings", [])
    return [f for f in findings if f.get("code") == code]


# ---------------------------------------------------------------------------
# Task 1 tests — heuristic checks (TOOL-04)
# ---------------------------------------------------------------------------


def test_ungrounded_requirement_flagged(tmp_path):
    """lint-requirements flags a 'stated' req missing source_trace as grounding FAIL."""
    reqs = """# Requirements

| ID | Statement | Status | Source |
|----|-----------|--------|--------|
| TOOL-01 | The system shall return a JSON response on success. | stated | |
"""
    rc, out, err = run_lint(tmp_path, reqs)
    assert rc == 0, f"Expected exit 0 (lint is reporter not gate); got {rc}, err={err}"
    assert out is not None and out.get("ok") is True
    grounding_findings = findings_with_code(out, "GROUNDING_MISSING")
    assert len(grounding_findings) >= 1, (
        f"Expected at least one GROUNDING_MISSING finding; got findings={out.get('findings')}"
    )
    assert all(f["severity"] == "fail" for f in grounding_findings), (
        "Grounding findings must have severity=fail (D-07)"
    )


def test_unverifiable_requirement_flagged(tmp_path):
    """lint-requirements flags a vague requirement lacking measurable cue as verifiability FAIL."""
    reqs = """# Requirements

| ID | Statement | Status | Source |
|----|-----------|--------|--------|
| TOOL-01 | The system should handle requests well. | stated | SRS §1 |
"""
    rc, out, err = run_lint(tmp_path, reqs)
    assert rc == 0
    assert out is not None and out.get("ok") is True
    v_findings = findings_with_code(out, "VERIFIABILITY_MISSING")
    assert len(v_findings) >= 1, (
        f"Expected VERIFIABILITY_MISSING; got findings={out.get('findings')}"
    )
    assert all(f["severity"] == "fail" for f in v_findings)


def test_compound_requirement_flagged(tmp_path):
    """lint-requirements flags a requirement with AND/OR conjunction as atomicity FAIL."""
    reqs = """# Requirements

| ID | Statement | Status | Source |
|----|-----------|--------|--------|
| TOOL-01 | The system shall validate input paths and log all errors within 5 seconds. | stated | SRS §2 |
"""
    rc, out, err = run_lint(tmp_path, reqs)
    assert rc == 0
    assert out is not None and out.get("ok") is True
    a_findings = findings_with_code(out, "ATOMICITY_COMPOUND")
    assert len(a_findings) >= 1, (
        f"Expected ATOMICITY_COMPOUND; got findings={out.get('findings')}"
    )
    assert all(f["severity"] == "fail" for f in a_findings)


def test_weasel_word_triggers_warn(tmp_path):
    """lint-requirements returns WARN (not FAIL) for weasel-word ambiguity (D-07)."""
    reqs = """# Requirements

| ID | Statement | Status | Source |
|----|-----------|--------|--------|
| TOOL-01 | The system shall provide a user-friendly interface that responds within 200ms. | stated | SRS §3 |
"""
    rc, out, err = run_lint(tmp_path, reqs)
    assert rc == 0
    assert out is not None and out.get("ok") is True
    a_findings = findings_with_code(out, "AMBIGUITY_WEASEL")
    assert len(a_findings) >= 1, (
        f"Expected AMBIGUITY_WEASEL finding; got findings={out.get('findings')}"
    )
    # Ambiguity must be WARN, never FAIL (D-07)
    assert all(f["severity"] == "warn" for f in a_findings), (
        "Ambiguity findings must have severity=warn (D-07)"
    )


def test_severity_mapping_fail_vs_warn(tmp_path):
    """grounding/verifiability/atomicity carry severity=fail; ambiguity carries severity=warn."""
    reqs = """# Requirements

| ID | Statement | Status | Source |
|----|-----------|--------|--------|
| TOOL-01 | The system shall provide a flexible experience. | stated | |
"""
    rc, out, err = run_lint(tmp_path, reqs)
    assert rc == 0
    assert out is not None
    findings = out.get("findings", [])
    fail_findings = [f for f in findings if f["severity"] == "fail"]
    warn_findings = [f for f in findings if f["severity"] == "warn"]
    # Ungrounded (no source) -> fail; weasel word "flexible" -> warn
    assert len(fail_findings) >= 1, "Expected at least one FAIL finding (grounding)"
    assert len(warn_findings) >= 1, "Expected at least one WARN finding (ambiguity)"


def test_clean_requirements_pass(tmp_path):
    """lint-requirements returns ok:true with no failures for a well-formed document."""
    reqs = """# Requirements

| ID | Statement | Status | Source |
|----|-----------|--------|--------|
| TOOL-01 | The system shall return a JSON response with an `ok` field within 200ms. | stated | SRS §3.1 |
"""
    rc, out, err = run_lint(tmp_path, reqs)
    assert rc == 0
    assert out is not None and out.get("ok") is True
    # A clean requirement may still have no FAIL findings
    findings = out.get("findings", [])
    fail_findings = [f for f in findings if f["severity"] == "fail"]
    assert len(fail_findings) == 0, (
        f"Expected no FAIL findings for a clean requirement; got {fail_findings}"
    )


# ---------------------------------------------------------------------------
# Task 1 tests — REQ-ID stability (TOOL-05)
# ---------------------------------------------------------------------------


def test_material_change_fixture(renumbered_reqs, tmp_path):
    """Two-pass TOOL-05: flags both material-change on existing ID and renumbered ID (Pitfall 6).

    old_doc has TOOL-01, TOOL-02, TOOL-03.
    new_doc has TOOL-01, TOOL-02, TOOL-04 (TOOL-03 renumbered; statement unchanged).
    Expected:
    - REQ_ID_RENUMBERED finding for TOOL-04 (pass 2: new ID whose statement matches old one).
    """
    rc, out, err = run_lint(
        tmp_path,
        renumbered_reqs["new_doc"],
        baseline_content=renumbered_reqs["old_doc"],
    )
    assert rc == 0, f"Expected exit 0; got {rc}, err={err}"
    assert out is not None and out.get("ok") is True

    renumbered = findings_with_code(out, "REQ_ID_RENUMBERED")
    assert len(renumbered) >= 1, (
        f"Expected REQ_ID_RENUMBERED finding (Pitfall 6 pass 2); got findings={out.get('findings')}"
    )
    assert all(f["severity"] == "fail" for f in renumbered), (
        "REQ_ID_RENUMBERED must be severity=fail (D-07: REQ-ID material-change is always FAIL)"
    )


def test_material_change_on_existing_id(tmp_path):
    """Pass 1: lint flags a materially changed statement on an existing REQ-ID as FAIL."""
    old_doc = """# Requirements

| ID | Statement |
|----|-----------|
| TOOL-01 | The system shall guard STATE.md writes with a cross-platform file lock. |
"""
    new_doc = """# Requirements

| ID | Statement |
|----|-----------|
| TOOL-01 | The CLI shall display a completely different capability unrelated to previous statement. |
"""
    rc, out, err = run_lint(tmp_path, new_doc, baseline_content=old_doc)
    assert rc == 0
    assert out is not None

    material_change = findings_with_code(out, "REQ_ID_MATERIAL_CHANGE")
    assert len(material_change) >= 1, (
        f"Expected REQ_ID_MATERIAL_CHANGE for modified TOOL-01; got findings={out.get('findings')}"
    )
    assert all(f["severity"] == "fail" for f in material_change)


def test_no_baseline_skips_stability_check(tmp_path):
    """Without --baseline, no REQ-ID stability findings are emitted."""
    reqs = """# Requirements

| ID | Statement | Status | Source |
|----|-----------|--------|--------|
| TOOL-01 | The system shall return a JSON response within 200ms. | stated | SRS §1 |
"""
    rc, out, err = run_lint(tmp_path, reqs)
    assert rc == 0
    assert out is not None
    findings = out.get("findings", [])
    stability_findings = [
        f for f in findings
        if f.get("code") in {"REQ_ID_MATERIAL_CHANGE", "REQ_ID_RENUMBERED"}
    ]
    assert len(stability_findings) == 0, (
        f"Expected no stability findings without --baseline; got {stability_findings}"
    )
