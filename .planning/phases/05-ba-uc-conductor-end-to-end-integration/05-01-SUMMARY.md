---
phase: "05"
plan: "01"
subsystem: ba-uc-conductor
plan_type: tdd
requirements: [UC-03, GATE-03]
tags: [tdd, state-machine, pipeline, index-gate, scaffold, regression-guard]
dependency_graph:
  requires: []
  provides:
    - state-machine contract tests (UC-03)
    - D-G2 index-integrity predicate tests (GATE-03)
    - WR-02 scaffold regression guard
  affects:
    - ba-tools/tests/test_uc_conductor_state.py
    - ba-tools/tests/test_index_gate_predicate.py
    - ba-tools/tests/test_scaffold_all_four_rows.py
tech_stack:
  added: []
  patterns:
    - multiprocessing.Process + Queue for concurrent write tests
    - inline helper copying (no cross-module imports)
    - subprocess-based integration tests via sys.executable -m ba_tools
key_files:
  created:
    - .agents/ba-daily-operators/ba-tools/tests/test_uc_conductor_state.py
    - .agents/ba-daily-operators/ba-tools/tests/test_index_gate_predicate.py
    - .agents/ba-daily-operators/ba-tools/tests/test_scaffold_all_four_rows.py
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/uc-001-test.md
  modified: []
decisions:
  - TDD plan type — tests describe existing SUT behavior (no SUT edits)
  - D-G2 predicate reads only orphans+gaps from index update JSON (covered_by not emitted)
  - multiprocessing.Process (not threading) for concurrent patch workers; module-level function for pickling compatibility
  - WR-02 defect confirmed absent — scaffold.py already seeds all four rows
metrics:
  duration: "~25 minutes"
  completed: "2026-06-18"
  tasks: 2
  files: 4
status: complete
---

# Phase 05 Plan 01: TDD State-Machine and Gate Contract Tests Summary

TDD tests covering the ba-uc conductor state-machine contract (UC-03) and D-G2 index-integrity gate predicate (GATE-03) using `ba-tools` subprocess integration tests with no SUT edits.

## What Was Built

Two test modules and one fixture file that form the verification spine for the ba-uc conductor:

1. **`test_uc_conductor_state.py`** (415 lines, 6 functions) — proves the pipeline state-machine contract: failed/in_progress steps are non-complete, gate-fail state is not clobbered, resume entry is deterministic, `state patch` pipeline_step round-trips via `uc-status`, and concurrent `multiprocessing.Process` workers patching different steps both survive with no clobber.

2. **`test_index_gate_predicate.py`** (7 test functions) — encodes the exact D-G2 predicate from RESEARCH Q2: FAIL iff `len(orphans)>0 OR any(rid in gaps for rid in step_req_ids)`. Tests cover: no orphans after valid mermaid trace, orphan detected for XX-999, self-coverage predicate fail path (step req_ids in gaps), and predicate pass path.

3. **`test_scaffold_all_four_rows.py`** (4 test functions) — WR-02 regression guard. Calls `ensure_scaffold(tmp_path)` directly, then asserts via `uc-status` that all four canonical rows (srs-analyze, mermaid, mockup, index) are present and pending, with `next_step == 'srs-analyze'`. Also asserts `ensure_scaffold` is idempotent.

4. **`tests/fixtures/uc-001-test.md`** — minimal UC-001 fixture with FR-001 and FR-002 requirement statements for use by future integration tests.

## Task Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Pipeline state-machine tests (6 functions) | `989d304` |
| 2 | D-G2 index-integrity tests + scaffold guard + fixture | `6ccf761` |

## Verification Results

Full suite passed on first run:

```
collected 17 items
tests/test_uc_conductor_state.py ......
tests/test_index_gate_predicate.py .......
tests/test_scaffold_all_four_rows.py ....
17 passed in 3.42s
```

## Decisions Made

1. **TDD type — no SUT edits**: All tests describe existing SUT behavior. No `ba_tools` source files were modified. Tests pass against the existing implementation, proving behavioral contracts.

2. **D-G2 reads only `orphans` + `gaps`**: `covered_by` is computed internally by `index_cmd.py` but NOT emitted in `ok_json`. Tests encode the predicate using only the documented output fields.

3. **`multiprocessing.Process` for concurrent test**: Threading was rejected (GIL-aware systems may serialize writes, masking clobber). `multiprocessing.Process` + `Queue` gives true concurrency. Module-level `_pipeline_patch_worker` function required for `pickle` compatibility (inner functions cannot be pickled).

4. **WR-02 confirmed non-existent**: `scaffold.py` `_STATE_MD` template already seeds all four rows. The regression guard proves this and prevents future regression.

5. **Inline helpers — no cross-module imports**: `_make_state_md`, `_run_uc_status`, `_run_state` copied into `test_uc_conductor_state.py` per the test-module isolation convention in this repo (existing `test_state.py` / `test_uc_status.py` pattern).

6. **`_d_g2_passes` predicate helper**: Encoded as a standalone Python function alongside the tests, making the exact predicate logic explicit and independently testable for both PASS and FAIL branches.

## Deviations from Plan

None. Plan executed exactly as written. WR-02 investigation confirmed the defect description was already resolved — scaffold.py seeds all four rows. The test module acts as the regression guard as specified.

## Known Stubs

None. All test assertions are concrete and drive real CLI subprocess calls against real ba-tools state.

## Threat Flags

None. Test files only — no new network endpoints, auth paths, file-access patterns, or schema changes introduced.

## Self-Check: PASSED

Files confirmed present:
- `.agents/ba-daily-operators/ba-tools/tests/test_uc_conductor_state.py` FOUND
- `.agents/ba-daily-operators/ba-tools/tests/test_index_gate_predicate.py` FOUND
- `.agents/ba-daily-operators/ba-tools/tests/test_scaffold_all_four_rows.py` FOUND
- `.agents/ba-daily-operators/ba-tools/tests/fixtures/uc-001-test.md` FOUND

Commits confirmed:
- `989d304` FOUND (Task 1)
- `6ccf761` FOUND (Task 2)
