"""Tests for ba-tools lint-requirements (TOOL-04, TOOL-05)."""

import pytest


@pytest.mark.xfail(reason="Wave 1: implement grounding FAIL detection (TOOL-04)")
def test_ungrounded_requirement_flagged(sample_reqs, tmp_ba_ops):
    """lint-requirements flags a requirement with no source citation as grounding FAIL."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement verifiability FAIL detection (TOOL-04)")
def test_unverifiable_requirement_flagged(tmp_ba_ops):
    """lint-requirements flags a vague requirement as verifiability FAIL."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement atomicity FAIL detection (TOOL-04)")
def test_compound_requirement_flagged(tmp_ba_ops):
    """lint-requirements flags a requirement with 'and'/'or' as atomicity FAIL."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement ambiguity WARN detection (TOOL-04, D-07)")
def test_weasel_word_triggers_warn(tmp_ba_ops):
    """lint-requirements returns WARN (not FAIL) for weasel-word ambiguity."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement REQ-ID stability material-change check (TOOL-05)")
def test_material_change_fixture(renumbered_reqs, tmp_ba_ops):
    """lint-requirements flags TOOL-03->TOOL-04 renumbering with unchanged statement as FAIL."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: implement clean requirements return ok:true (TOOL-04)")
def test_clean_requirements_pass(tmp_ba_ops):
    """lint-requirements returns ok:true with empty failures for a well-formed document."""
    raise NotImplementedError
