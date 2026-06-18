---
phase: 4
slug: ba-mockup-operator
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-18
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: 04-RESEARCH.md `## Validation Architecture`. Mirrors the Phase 3
> (ba-mermaid) test pattern — `test_mermaid_author.py` + `test_mermaid_trace_index.py`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing — configured Phases 1–3) |
| **Config file** | `.agents/ba-daily-operators/ba-tools/pyproject.toml` |
| **Quick run command** | `pytest tests/test_mockup_author.py tests/test_mockup_trace_index.py -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~15 seconds (subprocess integration tests dominate) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_mockup_author.py tests/test_mockup_trace_index.py -x`
- **After every plan wave:** Run `pytest` (full suite)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

> Task IDs (`4-NN-NN`) populate once PLAN.md files exist; rows below are keyed by
> requirement + the concrete test that proves it. Wave 0 creates the test files first.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD post-plan | — | 0 | MOCK-01 | T-4-01 (V5 input) | `--fidelity` missing/invalid → workflow hard-rejects (no artifact, no trace) | unit | `pytest tests/test_mockup_author.py::test_workflow_rejects_missing_fidelity -x` | ❌ W0 | ⬜ pending |
| TBD post-plan | — | 0 | MOCK-03 | — | `html` → first line `<!-- req_ids: [..] -->` + `<!DOCTYPE html>`; `wireframe` → YAML frontmatter `req_ids:` + headings/lists, no ASCII box-drawing | unit | `pytest tests/test_mockup_author.py -x` | ❌ W0 | ⬜ pending |
| TBD post-plan | — | 0 | MOCK-02 | — | After `trace write --kind mockup` + `index update`, cited REQ-IDs show in INDEX Mockup column, `## Orphans` = `(none)` | integration | `pytest tests/test_mockup_trace_index.py::TestReqIdsAppearInIndexMockupColumn -x` | ❌ W0 | ⬜ pending |
| TBD post-plan | — | 0 | MOCK-02 / D-06 | T-4-02 (spoofed ID) | Mockup citing `FR-999` (absent from registry) → `index update` lists `FR-999` under `## Orphans` | integration | `pytest tests/test_mockup_trace_index.py::test_invented_id_surfaces_as_orphan -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mockup_author.py` — stubs for MOCK-01, MOCK-03 (fixture + workflow-inspection assertions)
- [ ] `tests/test_mockup_trace_index.py` — stubs for MOCK-02 + criterion 3 (subprocess trace/index)
- [ ] `tests/fixtures/mockup/authored_html.html` — valid `.html` artifact fixture (`<!-- req_ids -->` first line, `<!DOCTYPE html>`, inline `<style>`)
- [ ] `tests/fixtures/mockup/authored_wireframe.md` — valid wireframe `.md` fixture (YAML frontmatter `req_ids:`, headings/lists/tables)
- [ ] `tests/fixtures/mockup/mockup_requirements.json` — requirements fixture (FR-001/FR-002; may copy `fixtures/mermaid/index_requirements.json` verbatim — schema is kind-agnostic)

*Framework already installed — pytest active since Phase 1. No install task needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| — | — | — | — |

*All phase behaviors have automated verification — the three success criteria each map to an automated pytest assertion (research §Validation Architecture).*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
