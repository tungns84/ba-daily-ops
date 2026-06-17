"""
Shared pytest fixtures for ba-tools test suite.

Fixtures provided:
- tmp_ba_ops(tmp_path): a repo root with an empty .ba-ops/ directory
- sample_reqs: small requirements document string (grounded + ungrounded entries)
- renumbered_reqs: dict with old_doc and new_doc where TOOL-03 is renumbered to TOOL-04
  with an unchanged statement (TOOL-05 fixture per RESEARCH Pitfall 6)
- citation_pass_doc: Markdown source with a section whose body contains a >=12-char span
- citation_fail_doc: Markdown source where the span exists only outside the cited section
"""

import pytest


@pytest.fixture()
def tmp_ba_ops(tmp_path):
    """Return a repo root Path with an empty .ba-ops/ directory pre-created."""
    ba_ops = tmp_path / ".ba-ops"
    ba_ops.mkdir()
    return tmp_path


@pytest.fixture()
def sample_reqs():
    """Return a small requirements document string.

    Contains:
    - One grounded, verifiable, atomic requirement (should pass all checks)
    - One ungrounded requirement (should trigger grounding FAIL)
    - One ambiguous requirement using a weasel word (should trigger WARN)
    """
    return """# Requirements

## Functional Requirements

| ID | Statement | Source |
|----|-----------|--------|
| TOOL-01 | The system shall return a JSON response with an `ok` field set to `true` when the `ba-tools init` command completes successfully. | SRS §3.1 |
| TOOL-02 | The system should handle requests efficiently. | |
| TOOL-03 | The CLI shall validate all input paths to ensure they resolve within the project root directory. | DESIGN §11 |
"""


@pytest.fixture()
def renumbered_reqs():
    """Return old and new requirement docs where one ID is renumbered but statement unchanged.

    TOOL-03 in old_doc → TOOL-04 in new_doc with identical statement text.
    This is the TOOL-05 renumbering fixture (RESEARCH Pitfall 6).
    """
    old_doc = """# Requirements

| ID | Statement |
|----|-----------|
| TOOL-01 | The system shall return a JSON response with an `ok` field set to `true` on success. |
| TOOL-02 | The CLI shall validate input paths to ensure they resolve within the project root. |
| TOOL-03 | The system shall guard STATE.md writes with a cross-platform file lock. |
"""
    new_doc = """# Requirements

| ID | Statement |
|----|-----------|
| TOOL-01 | The system shall return a JSON response with an `ok` field set to `true` on success. |
| TOOL-02 | The CLI shall validate input paths to ensure they resolve within the project root. |
| TOOL-04 | The system shall guard STATE.md writes with a cross-platform file lock. |
"""
    return {"old_doc": old_doc, "new_doc": new_doc, "renumbered_id": "TOOL-03",
            "new_id": "TOOL-04"}


@pytest.fixture()
def citation_pass_doc(tmp_path):
    """Return a Path to a Markdown doc containing a >=12-char span inside a cited section."""
    doc = tmp_path / "source.md"
    doc.write_text(
        """# Project Overview

## Background

This document describes the deterministic BA operator suite.
The system validates all input paths using pathlib resolution.

## Requirements

All requirements must be traceable to source documents.
""",
        encoding="utf-8",
    )
    return doc


@pytest.fixture()
def citation_fail_doc(tmp_path):
    """Return a Path to a Markdown doc where the span exists OUTSIDE the cited section."""
    doc = tmp_path / "source_fail.md"
    doc.write_text(
        """# Project Overview

## Background

This section does not contain the cited span at all.

## Requirements

All requirements must be traceable to source documents.
The system validates all input paths using pathlib resolution.
""",
        encoding="utf-8",
    )
    return doc
