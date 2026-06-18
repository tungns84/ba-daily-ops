---
phase: 4
slug: ba-mockup-operator
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-18
validated: 2026-06-18
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

> Keyed by requirement + the concrete test that proves it. All Wave-0 test files
> now exist and pass (Plan 01 created the foundation; Plan 02 the operator under test;
> Plan 03 ran the full suite green: 283 passed).

| Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01/02 | 1 | MOCK-01 | T-4-01 (V5 input) | `--fidelity` missing/invalid → workflow hard-rejects (no artifact, no trace) | unit | `pytest tests/test_mockup_author.py::test_workflow_rejects_missing_fidelity -x` | ✅ | ✅ green |
| 04-01/02 | 1 | MOCK-03 | — | `html` → first line `<!-- req_ids: [..] -->` + `<!DOCTYPE html>` | unit | `pytest tests/test_mockup_author.py::test_html_artifact_has_req_ids_comment tests/test_mockup_author.py::test_html_artifact_has_doctype -x` | ✅ | ✅ green |
| 04-01/02 | 1 | MOCK-03 | — | `wireframe` → YAML frontmatter `req_ids:` + headings/lists, no ASCII box-drawing | unit | `pytest tests/test_mockup_author.py::test_wireframe_artifact_has_frontmatter tests/test_mockup_author.py::test_wireframe_has_no_ascii_box_drawing -x` | ✅ | ✅ green |
| 04-01/02 | 1 | MOCK-01 / D-05 | T-4-06 (synthetic render) | screen route invokes NO render CLI (mmdc/drawio/screenshot/Route: render) — DESIGN §11 | unit | `pytest tests/test_mockup_author.py::test_screen_route_invokes_no_render_cli -x` | ✅ | ✅ green |
| 04-01 | 1 | MOCK-02 | — | After `trace write --kind mockup` + `index update`, cited REQ-IDs show in INDEX Mockup column, `## Orphans` = `(none)` | integration | `pytest "tests/test_mockup_trace_index.py::TestReqIdsAppearInIndexMockupColumn" "tests/test_mockup_trace_index.py::TestNoOrphansForRealIds" -x` | ✅ | ✅ green |
| 04-01 | 1 | MOCK-03 / D-06 | T-4-02 (spoofed ID) | Mockup citing `FR-999` (absent from registry) → `index update` lists `FR-999` under `## Orphans` | integration | `pytest "tests/test_mockup_trace_index.py::TestInventedIdSurfacesAsOrphan::test_invented_id_surfaces_as_orphan" -x` | ✅ | ✅ green |
| 04-01 | 1 | MOCK-02 (structure) | — | INDEX matrix header + `## Orphans` marker present in `index_cmd`; fixture carries required IDs | unit | `pytest "tests/test_mockup_trace_index.py::TestIndexMdStructure" -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Coverage:** MOCK-01 ✅ · MOCK-02 ✅ · MOCK-03 ✅ — all three success criteria map to a green automated assertion. 12/12 mockup-pair tests pass; full suite 283 passed.

---

## Wave 0 Requirements

- [x] `tests/test_mockup_author.py` — MOCK-01, MOCK-03 (fixture + workflow-inspection assertions) — 6 tests green
- [x] `tests/test_mockup_trace_index.py` — MOCK-02 + criterion 3 (subprocess trace/index) — 6 tests green
- [x] `tests/fixtures/mockup/authored_html.html` — valid `.html` fixture (`<!-- req_ids -->` first line, `<!DOCTYPE html>`, inline `<style>`, no `<script>`)
- [x] `tests/fixtures/mockup/authored_wireframe.md` — valid wireframe `.md` fixture (YAML frontmatter `req_ids:`, headings/lists/tables, no box-drawing)
- [x] `tests/fixtures/mockup/mockup_requirements.json` — requirements fixture (FR-001/FR-002)

*Framework already installed — pytest active since Phase 1. No install task needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Outcome |
|----------|-------------|------------|-------------------|---------|
| Authored mockup reads as a usable screen | MOCK-03 (quality) | No automated assertion can judge visual/structural usability of a runtime-authored screen | Open `authored_html.html` in a browser (recognizable screen, no JS/broken assets); open `authored_wireframe.md` in MD preview (layout sketch, no box-drawing); confirm workflow rejects missing/invalid `--fidelity` | ✅ PASSED (Plan 03 Task 2 human-verify — approved) |

*All three machine-checkable success criteria have automated verification. The one inherently-subjective check (does an authored screen read as usable) was covered by the Plan-03 blocking human-verify checkpoint.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (2026-06-18)

---

## Validation Audit 2026-06-18

| Metric | Count |
|--------|-------|
| Requirements | 3 (MOCK-01, MOCK-02, MOCK-03) |
| Covered (green automated) | 3 |
| Partial | 0 |
| Missing | 0 |
| Manual-only | 1 (subjective screen-usability — covered by Plan-03 human-verify) |

No gaps — auditor spawn skipped per workflow Step 3 (all requirements COVERED with green tests). Full suite: 283 passed.
