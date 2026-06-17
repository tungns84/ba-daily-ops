---
phase: 02-ba-srs-analyze-quality-gate-traceability-core
plan: "01"
subsystem: testing
tags: [ba-tools, hashing, lint, scaffold, pytest, determinism, tdd]

requires:
  - phase: 01-deterministic-ba-tools-cli-foundational-gates
    provides: ba-tools CLI (init/lint-requirements/verify/scaffold), conftest.py, pyproject.toml editable install

provides:
  - dict-aware check_grounding in lint.py (AttributeError fix for JSON source_trace)
  - .ba-ops/traces/ subdirectory created by init (scaffold.py _SUBDIRS patch)
  - shared ba_tools/hashing.py module (_sha256_file, _statement_hash, _sha256_str)
  - F9 stability-drift fixture (tests/fixtures/srs/renumbered-reqid/) + test_stability_drift
  - test_smoke.py asserting Phase-1 commands by name and --help exit-0
  - test_skill_schema.py scaffold with helpers + skipped skill-path tests ready for plan 04

affects:
  - 02-02-PLAN (verify JSON path: check_grounding no longer crashes on dict source_trace)
  - 02-03-PLAN (trace_cmd + index_cmd: import _sha256_file/_statement_hash from ba_tools.hashing)
  - 02-04-PLAN (skill files: flip test_skill_schema.py skip to live)

tech-stack:
  added: []
  patterns:
    - "isinstance(_st, dict) guard for dual-format (str / dict) source_trace in lint checks"
    - "_sha256_file uses hashlib.file_digest() (3.11+ streaming); _statement_hash normalises with re.sub(r'\\s+', ' ', text.strip()) NO case-fold (D-12)"
    - "test_smoke.py asserts by parser subparser choice names not _COMMAND_MODULES list length"
    - "pytest.mark.skip(reason=...) for skill-path tests not yet created — collects cleanly, activates in plan 04"

key-files:
  created:
    - .agents/ba-daily-operators/ba-tools/ba_tools/hashing.py
    - .agents/ba-daily-operators/ba-tools/tests/test_smoke.py
    - .agents/ba-daily-operators/ba-tools/tests/test_skill_schema.py
    - .agents/ba-daily-operators/ba-tools/tests/test_hashing.py
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/renumbered-reqid/source.md
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/renumbered-reqid/requirements.json
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/renumbered-reqid/requirements_v2.json
  modified:
    - .agents/ba-daily-operators/ba-tools/ba_tools/lint.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/scaffold.py
    - .agents/ba-daily-operators/ba-tools/tests/test_lint_reqs.py

key-decisions:
  - "check_grounding uses _st = row.get('source_trace', ''); source_trace = _st.get('doc', '').strip() if isinstance(_st, dict) else _st.strip() — mirrors check_citation_present isinstance guard"
  - "_statement_hash applies strip + re.sub(r'\\s+', ' ') but NO case-fold (D-12 spec: case-sensitive drift detection)"
  - "_sha256_file uses hashlib.file_digest() streaming (Python 3.11+ per CLAUDE.md) — zero memory overhead for large binaries"
  - "test_smoke.py asserts by subparser choices dict keys not _COMMAND_MODULES list length (Codex LOW feedback resolved)"
  - "test_skill_schema.py skill-path tests marked skip not xfail — skip is cleaner for planned-but-absent files"

patterns-established:
  - "Dual-format source_trace: isinstance(_st, dict) guard extracts .get('doc', '') for JSON path, .strip() for string Markdown path"
  - "Shared hashing module: all sha256 digest calls go through ba_tools.hashing to avoid cross-command imports"
  - "F9 fixture pattern: JSON pair (requirements.json + requirements_v2.json) with same REQ-ID and materially different statements for drift testing"

requirements-completed: [SRS-03, TRACE-03]

duration: 6min
completed: 2026-06-18
status: complete
---

# Phase 2 Plan 01: Wave-0 Prerequisites + Test Scaffolding Summary

**dict-aware check_grounding (AttributeError fix), .ba-ops/traces/ scaffold, shared hashing.py with streaming sha256, F9 stability-drift fixture, smoke/skill-schema test scaffolds**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-17T17:27:33Z
- **Completed:** 2026-06-17T17:34:06Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Fixed `lint.py::check_grounding` to handle dict `source_trace` via `isinstance(_st, dict)` guard — unblocks Wave-2 JSON verify path (plan 02)
- Added `"traces"` to `scaffold.py::_SUBDIRS` so `init` creates `.ba-ops/traces/` — unblocks plan 03 trace write
- Extracted shared `ba_tools/hashing.py` with `_sha256_file` / `_statement_hash` / `_sha256_str` — eliminates circular-import risk between plan 03 `trace_cmd` and `index_cmd`
- Created F9 fixture (`renumbered-reqid/`) + `test_stability_drift` confirming `REQ_ID_MATERIAL_CHANGE` for same REQ-ID with changed statement
- Scaffolded `test_smoke.py` (assert by command name, not list length) and `test_skill_schema.py` (skip until plan 04 skill files)

## Task Commits

Each task was committed atomically:

1. **Task 1: Patch check_grounding for dict source_trace + scaffold traces subdir** - `abd4f07` (fix)
2. **Task 2: F9 stability-drift fixture + REQ-ID stability test + smoke/skill-schema scaffolds** - `a7fbd24` (feat)
3. **Task 3: Shared ba_tools/hashing.py module + tests (cross-plan extraction)** - `c6cca67` (feat)

## Files Created/Modified

- `ba_tools/lint.py` — `check_grounding`: replaced `.strip()` with `isinstance(_st, dict)` branch; `_st.get("doc", "").strip()` for dict, `_st.strip()` for string
- `ba_tools/scaffold.py` — `_SUBDIRS` appended `"traces"` (now: srs/mermaid/mockup/backlog/plugins/traces)
- `ba_tools/hashing.py` — new module: `_sha256_file` (streaming hashlib.file_digest), `_statement_hash` (D-12 normalised), `_sha256_str` (raw UTF-8 sha256)
- `tests/test_lint_reqs.py` — added `test_grounding_dict_compat` (5 cases), `test_scaffold_creates_traces_subdir`, `test_stability_drift` (F9)
- `tests/test_smoke.py` — new: `test_commands_registered` (subparser choices), `test_command_help_exits_zero` (parametrized 12 commands)
- `tests/test_skill_schema.py` — new: frontmatter + openai.yaml helpers, 2 helper tests live, 2 skill-path tests skip
- `tests/test_hashing.py` — new: 13 tests for all three hashing functions + export contract + determinism boundary
- `tests/fixtures/srs/renumbered-reqid/source.md` — source doc for F9 fixture
- `tests/fixtures/srs/renumbered-reqid/requirements.json` — FR-001 v1 (traceability-index statement)
- `tests/fixtures/srs/renumbered-reqid/requirements_v2.json` — FR-001 v2 (materially different statement)

## Decisions Made

- `check_grounding` uses `_st.get("doc", "").strip() if isinstance(_st, dict) else _st.strip()` — mirrors the guard already in `check_citation_present`, making both functions consistent
- `_statement_hash` does NOT case-fold (D-12 spec) — drift detection is case-sensitive; `"The system"` and `"the system"` are considered materially different
- `_sha256_file` uses `hashlib.file_digest()` (Python 3.11+ streaming) per CLAUDE.md guidance — avoids loading large binaries into memory
- `test_smoke.py` asserts by `parser._subparsers._group_actions[0].choices` key set, not `_COMMAND_MODULES` list length — resilient to module list reordering
- `test_skill_schema.py` skill-path tests use `pytest.mark.skip(reason=...)` not `xfail` — skip is appropriate when files are intentionally absent (not expected-to-fail)

## Deviations from Plan

None — plan executed exactly as written. All three tasks completed in TDD RED/GREEN order (RED confirmed for each before GREEN implementation). No architectural changes required.

## Issues Encountered

None. The `detect_reqid_issues` grep guard confirmed the function exists at line 279 before the F9 test relied on it. All tests passed GREEN without iteration.

## Self-Check

Created files confirmed:

- `ba_tools/hashing.py` — exists
- `tests/test_smoke.py` — exists
- `tests/test_skill_schema.py` — exists
- `tests/test_hashing.py` — exists
- `tests/fixtures/srs/renumbered-reqid/source.md` — exists
- `tests/fixtures/srs/renumbered-reqid/requirements.json` — exists
- `tests/fixtures/srs/renumbered-reqid/requirements_v2.json` — exists

Commits confirmed:

- `abd4f07` — Task 1 (fix lint.py + scaffold.py)
- `a7fbd24` — Task 2 (F9 fixture + test scaffolds)
- `c6cca67` — Task 3 (hashing.py)

Final test count: 41 passed, 0 failed, 2 skipped (skill-path tests intentionally skipped)

## Self-Check: PASSED

## Known Stubs

None — no hardcoded placeholders or empty data flows introduced. `test_skill_schema.py` skill-path tests are skipped (not stubs), with clear `reason="skill files land in plan 04"`.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries introduced. `ba_tools/hashing.py` is a pure stdlib utility with no I/O surface beyond file-read (already covered by existing trust model).

## Next Phase Readiness

- Plan 02 (verify JSON path) is unblocked: `check_grounding` handles dict `source_trace` without crash
- Plan 03 (trace + index commands) is unblocked: `.ba-ops/traces/` scaffolded by `init`; `ba_tools/hashing.py` ready for import
- Plan 04 (skill files): `test_skill_schema.py` skip tests activate when skill files land

---
*Phase: 02-ba-srs-analyze-quality-gate-traceability-core*
*Completed: 2026-06-18*
