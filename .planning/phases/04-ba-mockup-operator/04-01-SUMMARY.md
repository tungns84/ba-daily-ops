---
phase: 04-ba-mockup-operator
plan: "01"
subsystem: testing
tags: [pytest, ba-mockup, fixtures, integration-tests, nyquist, trace-index, html-fidelity, wireframe-fidelity]

requires:
  - phase: 03-ba-mermaid-operator
    provides: trace write --kind mermaid, index update, test file structure (test_mermaid_author.py + test_mermaid_trace_index.py used as analogs)

provides:
  - "3 mockup test fixtures: authored_html.html, authored_wireframe.md, mockup_requirements.json"
  - "test_mockup_author.py: 6 tests pinning MOCK-01 (fidelity shape) + MOCK-03 (D-03/D-04 contracts) + Plan 02 RED gates"
  - "test_mockup_trace_index.py: 6 tests pinning MOCK-02 (trace→index) + criterion-3 (D-06 orphan detection)"

affects: [04-02-ba-mockup-workflow, 04-03-ba-mockup-cli]

tech-stack:
  added: []
  patterns:
    - "Nyquist Wave 0: test fixtures + pytest files committed before operator implementation; integration tests pass immediately by consuming existing ba-tools CLI"
    - "Workflow-inspection RED gate: test asserts on _WORKFLOW_PATH.exists() rather than xfail, so failure message names the creating plan"
    - "D-06 orphan coverage pattern: trace write accepts invented IDs without error; index update is sole reconciliation point"
    - "test_mockup_trace_index.py mirrors test_mermaid_trace_index.py file-for-file: _FIXTURE_DIR, _INDEX_REQS_FIXTURE, helpers, fixture, 3 test classes + TestIndexMdStructure"

key-files:
  created:
    - ".agents/ba-daily-operators/ba-tools/tests/fixtures/mockup/mockup_requirements.json"
    - ".agents/ba-daily-operators/ba-tools/tests/fixtures/mockup/authored_html.html"
    - ".agents/ba-daily-operators/ba-tools/tests/fixtures/mockup/authored_wireframe.md"
    - ".agents/ba-daily-operators/ba-tools/tests/test_mockup_author.py"
    - ".agents/ba-daily-operators/ba-tools/tests/test_mockup_trace_index.py"
  modified: []

key-decisions:
  - "Workflow-inspection tests assert explicitly on file existence (not xfail) — produces named error message pointing to Plan 02 as the responsible plan"
  - "--source-doc for mockup trace = requirements.json (not the mockup artifact) — matches ba-mermaid pattern, pins source_hash to SRS for drift detection"
  - "authored_html.html first line = HTML req_ids comment before DOCTYPE — matches D-03 canonical contract verified in RESEARCH.md"
  - "authored_wireframe.md uses YAML frontmatter + headings + table — zero ASCII box-drawing per D-04"

patterns-established:
  - "Nyquist Wave 0 test pattern: create tests first, tests pass immediately on existing CLI, implementation operator added by later plans"
  - "Mockup fixture shape: HTML fidelity = comment-first, wireframe fidelity = YAML-frontmatter-first"

requirements-completed: [MOCK-01, MOCK-02, MOCK-03]

duration: 45min
completed: 2026-06-18
status: complete
---

# Phase 4 Plan 01: ba-mockup Nyquist Test Foundation Summary

**Three mockup test fixtures + two pytest files pinning MOCK-01/MOCK-02/MOCK-03 via D-03/D-04/D-06 contracts; all trace-index integration tests pass immediately against existing ba-tools CLI; two workflow-inspection tests are RED (Plan 02 creates ba-mockup.md)**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-06-18T08:00:00Z
- **Completed:** 2026-06-18T09:21:00Z
- **Tasks:** 3 of 3
- **Files created:** 5

## Accomplishments

- Created 3 mockup test fixtures matching D-03/D-04 artifact contracts and the mermaid fixture structure
- Created `test_mockup_author.py` with 4 passing fixture-based tests (MOCK-01/MOCK-03 fidelity) + 2 RED workflow-inspection tests (assert on ba-mockup.md existence, go green in Plan 02)
- Created `test_mockup_trace_index.py` with 6 passing integration tests: req_ids → INDEX Mockup column (MOCK-02), no-orphan criterion, D-06 orphan surface; all run against live ba-tools CLI with zero ba_tools/ edits

## Task Commits

1. **Task 1: Create 3 mockup test fixtures** - `205894e` (feat)
2. **Task 2: Create test_mockup_author.py** - `4865ca4` (feat)
3. **Task 3: Create test_mockup_trace_index.py** - `7cdecd7` (test)

## Files Created/Modified

- `.agents/ba-daily-operators/ba-tools/tests/fixtures/mockup/mockup_requirements.json` - FR-001 + FR-002 requirements fixture (byte-identical to mermaid analog)
- `.agents/ba-daily-operators/ba-tools/tests/fixtures/mockup/authored_html.html` - HTML-fidelity mockup: req_ids comment line 1, DOCTYPE line 2, inline CSS only, no script, no external src
- `.agents/ba-daily-operators/ba-tools/tests/fixtures/mockup/authored_wireframe.md` - Wireframe-fidelity mockup: YAML frontmatter, headings/lists/table, zero ASCII box-drawing
- `.agents/ba-daily-operators/ba-tools/tests/test_mockup_author.py` - 6 tests: HTML req_ids comment, DOCTYPE, wireframe frontmatter, no ASCII box-drawing, screen-route no-render (RED), fidelity enforcement text (RED)
- `.agents/ba-daily-operators/ba-tools/tests/test_mockup_trace_index.py` - 6 tests: req_ids→INDEX Mockup column ok, no-orphans for real IDs, invented ID surfaces as orphan, matrix header sync, orphans marker sync, fixture IDs check

## Decisions Made

- Workflow-inspection tests (tests 5+6 in `test_mockup_author.py`) use explicit `assert _WORKFLOW_PATH.exists()` rather than `pytest.mark.xfail` — failure message names the creating plan, making the RED state transparent and guiding the Plan 02 executor
- `--source-doc` for `trace write --kind mockup` points to `requirements.json` (SRS file), not the mockup artifact — consistent with ba-mermaid pattern; pins `source_hash` to SRS for drift detection per RESEARCH.md
- `authored_html.html` comment is absolute first line (before DOCTYPE) — matches `_HTML_REQ_IDS_RE` pattern from `mockup_cmd.py` and D-03 canonical contract
- Fixture `authored_wireframe.md` uses standard markdown tables with pipe-and-dash separators (not ASCII box-drawing) — satisfies D-04 `+--` prohibition

## Deviations from Plan

None — plan executed exactly as written. All 5 files created per spec. Test count (4 pass + 2 RED for Task 2; 6 pass for Task 3) matches plan acceptance criteria. `git status --porcelain ba_tools/` is empty.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 02 (ba-mockup-workflow): creates `ba-mockup.md` in `.agents/ba-daily-operators/ba-core/workflows/` — this makes the 2 RED tests in `test_mockup_author.py` go green
- Plan 03 (ba-mockup-cli): implements `ba-tools mockup` CLI routes (`screen`, `full`) — all trace-index tests in `test_mockup_trace_index.py` already pass; Plan 03 integration tests will extend coverage

---
*Phase: 04-ba-mockup-operator*
*Completed: 2026-06-18*

## Self-Check: PASSED

All 5 created files verified on disk. All 3 task commits (205894e, 4865ca4, 7cdecd7) verified in git log.
