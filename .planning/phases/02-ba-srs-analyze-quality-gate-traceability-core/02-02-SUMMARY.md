---
phase: 02-ba-srs-analyze-quality-gate-traceability-core
plan: "02"
subsystem: ba-tools
tags: [verify, render, json-schema, ieee-830, determinism, tdd, traceability]
dependency_graph:
  requires: [02-01]
  provides: [verify-json-gate, srs-render, requirements-registry]
  affects: [ba_tools/commands/verify_cmd.py, ba_tools/srs_render.py, ba_tools/commands/render_cmd.py, ba_tools/__main__.py, ba-core/templates/srs.md]
tech_stack:
  added: []
  patterns:
    - JSON→Markdown deterministic rendering via string.Template.safe_substitute
    - _parse_reqs dispatcher (auto/md/json) with source_trace dict preservation
    - _validate_reqs_schema early-exit gate before citation pipeline
    - render_registry union-all-slugs pattern (D-08)
    - lockfile-guarded file writes (FileLock timeout=10s)
key_files:
  created:
    - .agents/ba-daily-operators/ba-tools/ba_tools/srs_render.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/render_cmd.py
    - .agents/ba-daily-operators/ba-tools/tests/test_render.py
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/clean-uc-grounded/
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/ungrounded-span/
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/paraphrased-span/
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/wrong-section-span/
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/section-null-doc-scope/
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/doc-mismatch/
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/registry-union/
  modified:
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/verify_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/__main__.py
    - .agents/ba-daily-operators/ba-tools/ba-core/templates/srs.md
    - .agents/ba-daily-operators/ba-tools/tests/test_verify.py
decisions:
  - "source_trace.doc drives citation lookup, not CLI --source; rows always carry source_trace dict for dict-aware check_grounding (plan 02-01 contract)"
  - "section:null in requirements.json → None in row dict → document-scope citation search (D-03)"
  - "_validate_reqs_schema gates before citation pipeline: missing id/statement/bad status/stated-without-span all exit 2 with SCHEMA_INVALID/INVALID_REQUIREMENT"
  - "render_registry always takes list of ALL slugs' docs (never single-slug); CLI globs .ba-ops/srs/*/requirements.json sorted deterministically (D-08)"
  - "render_cmd resolves template from repo_root/.agents/.../ba-core/templates/srs.md (consistent with template_cmd.py _templates_dir convention)"
  - "test fixture: _setup_template() copies real srs.md into tmp_path to avoid TEMPLATE_NOT_FOUND in CLI integration tests"
metrics:
  duration: "continuation session ~45 min"
  completed: "2026-06-17T17:56:57Z"
  tasks_completed: 2
  files_created: 14
  files_modified: 4
  tests_added: 32
  tests_total: 209
status: complete
---

# Phase 02 Plan 02: JSON-aware verify gate + deterministic IEEE-830 renderer Summary

JSON-aware `ba-tools verify` (auto-detects `.json`, validates schema, preserves `source_trace` dict) and deterministic IEEE-830 renderer (`srs_render.py` + `render` command) turning `requirements.json` into SRS.md and REQUIREMENTS.md registry union.

## What Was Built

### Task 1: JSON verify branch

Extended `verify_cmd.py` to be format-aware:

- `--reqs-format auto|md|json` argument (default: auto, detects `.json` by extension)
- `_parse_reqs(text, path, fmt)` dispatcher: routes to `_parse_md_table` (existing Markdown path) or new JSON branch
- `_validate_reqs_schema(payload)` early gate: rejects non-list/missing-requirements, missing id/statement, bad status, stated-without-span via `BaToolsError` exit 2
- JSON rows: flattened `span/section/source` from `source_trace` subdict; original `source_trace` dict KEPT on row for dict-aware `check_grounding` (plan 02-01 contract)
- `source_trace.doc` drives citation lookup (not CLI `--source`); `section:null` → `None` → document-scope search (D-03)
- PATH_TRAVERSAL guard on each `source_trace.doc` path (T-02-04b)

Fixtures created:
- `clean-uc-grounded/` (F1): 3-req doc with verbatim stated spans in correct sections → exits 0
- `ungrounded-span/` (F2): invented span → exits 2 CITATION_NOT_FOUND
- `paraphrased-span/` (F3): paraphrase not verbatim → exits 2 CITATION_NOT_FOUND
- `wrong-section-span/` (F4): span under sibling section → exits 2 default; exits 0 with --cite-scope document
- `section-null-doc-scope/`: `section:null` requirement → document-scope search passes
- `doc-mismatch/`: `source_trace.doc` = source_b, `--source` = source_a → gate uses source_b

### Task 2: Deterministic renderer + render command

Created `srs_render.py`:
- `render_srs(reqs_doc, template_text) -> str`: pure fn, groups FR/NFR/BR into §3.1/§3.2/§3.3, builds traceability table, substitutes into IEEE-830 template via `string.Template.safe_substitute`
- `render_registry(reqs_docs: list[dict]) -> str`: pure fn, unions ALL slugs' requirements, sorted by id, emits REQUIREMENTS.md table (D-08; single-slug call would drop other slugs' reqs)

Created `render_cmd.py`:
- `render srs --slug <slug>`: reads `.ba-ops/srs/<slug>/requirements.json`, renders via `render_srs`, writes `.ba-ops/srs/<slug>/SRS.md` under FileLock (SRS.md.lock)
- `render registry`: globs all `.ba-ops/srs/*/requirements.json` sorted, loads all, calls `render_registry(all_docs)`, writes `.ba-ops/REQUIREMENTS.md` under FileLock (REQUIREMENTS.md.lock)
- PATH_TRAVERSAL guard on slug-derived paths (T-02-06)
- FILE_NOT_FOUND when requirements.json absent

Evolved `ba-core/templates/srs.md` to full IEEE-830 §1-§5 with `${...}` tokens (§1.1 Purpose, §1.2 Scope, §1.3 Definitions, §2 Overall Description, §3.1-§3.5, §4 Appendices, §5 Traceability).

Registered `render_cmd` in `__main__.py` `_COMMAND_MODULES` (13 commands total).

## TDD Gate Compliance

Both tasks followed RED → GREEN → REFACTOR order per plan `tdd="true"`:

| Task | RED commit | GREEN commit | Tests |
|------|-----------|-------------|-------|
| Task 1 | e84dbcf | 276f1a7 | 14 new tests (32 total verify) |
| Task 2 | 3c7fcd5 | 87fff16 | 18 new tests (50 verify+render) |

Final suite: **209 passed, 2 skipped** (pre-existing skips unrelated to this plan).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Test fixture: template resolution in CLI tests**
- **Found during:** Task 2 GREEN phase (3 test failures)
- **Issue:** `render_cmd._read_srs_template()` resolves template relative to `--repo-root`, which in CLI integration tests is `tmp_path`. Template only exists in the real repo, not in tmp_path.
- **Fix:** Added `_setup_template(tmp_path)` helper to `test_render.py` that copies the real `srs.md` into `tmp_path/.agents/ba-daily-operators/ba-tools/ba-core/templates/srs.md` before CLI tests that invoke `render srs`.
- **Files modified:** `tests/test_render.py`

**2. [Rule 3 - Blocking] PATH_TRAVERSAL test: slug depth insufficient**
- **Found during:** Task 2 GREEN phase
- **Issue:** Test used `../../evil` which resolves to `root/.ba-ops/evil` (inside root — not actually a traversal).
- **Fix:** Changed to `../../../../evil` which resolves above root and correctly triggers PATH_TRAVERSAL guard.
- **Files modified:** `tests/test_render.py`

### No other deviations. Plan executed as written.

## Threat Surface Scan

New network endpoints: none. New auth paths: none. New file access patterns:
- `render_cmd.py` reads `.ba-ops/srs/*/requirements.json` (glob-bounded, guarded by `is_within_root`)
- `render_cmd.py` writes `.ba-ops/srs/<slug>/SRS.md` and `.ba-ops/REQUIREMENTS.md` (both lockfile-guarded, slug path validated before write)

All new file access patterns are within the plan's threat model (T-02-06 covered).

## Self-Check: PASSED

Files exist:
- `ba_tools/srs_render.py` — FOUND
- `ba_tools/commands/render_cmd.py` — FOUND
- `tests/test_render.py` — FOUND
- `ba-core/templates/srs.md` (evolved) — FOUND

Commits exist:
- `e84dbcf` (test 02-02: RED Task 1) — FOUND
- `276f1a7` (feat 02-02: GREEN Task 1) — FOUND
- `3c7fcd5` (test 02-02: RED Task 2) — FOUND
- `87fff16` (feat 02-02: GREEN Task 2) — FOUND
