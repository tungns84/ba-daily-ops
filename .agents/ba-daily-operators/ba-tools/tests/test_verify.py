"""Tests for ba-tools verify citation-exists gate (TOOL-06)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement citation-exists pass for real span in section (TOOL-06)")
def test_citation_exists_pass(citation_pass_doc, tmp_ba_ops):
    """verify returns ok:true when a >=12-char span is found in the cited section."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement citation-exists fail for span outside section (TOOL-06)")
def test_citation_exists_fail_wrong_section(citation_fail_doc, tmp_ba_ops):
    """verify exits 2 when span exists in document but not in the cited section."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement cite-scope document override (TOOL-06)")
def test_cite_scope_document_override(citation_fail_doc, tmp_ba_ops):
    """verify --cite-scope document finds span anywhere in doc (not section-scoped)."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement span too short rejection (TOOL-06)")
def test_span_too_short_fails():
    """verify rejects a span shorter than 12 characters."""
    raise NotImplementedError
