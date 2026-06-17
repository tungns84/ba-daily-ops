---
phase: 01-deterministic-ba-tools-cli-foundational-gates
plan: "05"
subsystem: ba-tools-quality-engine
tags: [python, lint, citation, requirements, tdd, jaccard, regex, heuristics]
dependency_graph:
  requires:
    - 01-01 (BaToolsError, ok_json, resolve_repo_root, is_within_root, command stubs)
    - 01-01 (conftest.py fixtures: renumbered_reqs, citation_pass_doc, citation_fail_doc)
  provides:
    - ba_tools.lint (WEASEL_WORDS, normalize_statement, is_material_change, detect_reqid_issues, check_* heuristics)
    - ba_tools.citation (extract_section, citation_exists)
    - lint-requirements CLI subcommand (TOOL-04, TOOL-05)
    - verify CLI subcommand (TOOL-06)
  affects:
    - Phase 2 ba-critic integration (consumes lint findings as structured data)
    - Any agent invoking ba-tools verify as a quality gate
tech_stack:
  added:
    - No new dependencies (stdlib re, pathlib only)
  patterns:
    - TDD RED/GREEN cycle for both tasks
    - Jaccard word-set similarity for REQ-ID material-change detection (MATERIAL_CHANGE_THRESHOLD=0.75)
    - Two-pass REQ-ID stability: pass 1 (same ID, changed statement) + pass 2 (new ID, same statement = renumber)
    - word-boundary \b anchors for weasel-word matching (Pitfall 4 avoidance)
    - Level-aware Markdown section stop (Pitfall 5 avoidance)
    - Heading normalization lstrip('#').strip() on both sides (Pitfall 2 avoidance)
    - Lint as reporter (exits 0); verify as gate (exits 2 on FAIL)
key_files:
  created:
    - .agents/ba-daily-operators/ba-tools/ba_tools/lint.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/citation.py
  modified:
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/lint_reqs.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/verify_cmd.py
    - .agents/ba-daily-operators/ba-tools/tests/test_lint_reqs.py
    - .agents/ba-daily-operators/ba-tools/tests/test_verify.py
decisions:
  - "lint-requirements exits 0 always (reporter not gate); verify owns gating per D-08"
  - "verify reads Source/Section/Span columns from Markdown table rows for per-req citation"
  - "check_verifiability is permissive (any integer, any normative verb = verifiable) to avoid over-flagging"
  - "--repo-root passed to CLI invocations in tests to satisfy is_within_root path-safety (T-1-01)"
  - "citation_exists returns False for spans < 12 chars regardless of scope"
metrics:
  duration: "8 minutes"
  completed: "2026-06-17T12:45:51Z"
  tasks_completed: 2
  files_created: 2
  files_modified: 4
---

# Phase 01 Plan 05: Quality Engine (lint-requirements + verify) Summary

**One-liner:** Deterministic quality engine with regex/Jaccard lint heuristics (grounding/verifiability/atomicity/ambiguity/REQ-ID stability) and a section-scoped verbatim citation-exists gate folded into the verify command.

---

## What Was Built

The verification core for the ba-tools spine (DESIGN §5/§6). Two modules and two CLI commands:

### ba_tools/lint.py

The deterministic lint heuristics module (TOOL-04, TOOL-05). Zero ML/NLP dependencies — all checks are `re` patterns or word-set operations.

**Exports:**
- `WEASEL_WORDS` — 46-word ambiguity signal list (tunable constant, A2)
- `normalize_statement(text) -> set[str]` — lowercase `re.findall(r'\b[a-z]{2,}\b', ...)` word-set
- `MATERIAL_CHANGE_THRESHOLD = 0.75` — Jaccard threshold (tunable constant, A1)
- `is_material_change(old, new) -> bool` — Jaccard similarity below threshold
- `check_ambiguity(req_id, statement)` — weasel-word match with `\b` anchors → `severity="warn"` (D-07)
- `check_verifiability(req_id, statement)` — no measurable cue → `severity="fail"` (D-07)
- `check_atomicity(req_id, statement)` — `shall ... and/or ... verb` pattern → `severity="fail"`
- `check_grounding(req_id, row)` — `stated` req missing source → `severity="fail"`
- `detect_reqid_issues(old_reqs, new_reqs)` — two-pass stability check → FAIL findings

**Two-pass REQ-ID stability (TOOL-05, RESEARCH Pitfall 6):**
- Pass 1: each ID present in both old/new → flag if `is_material_change` (REQ_ID_MATERIAL_CHANGE)
- Pass 2: each new-only ID → compare normalized statement to every old statement; similarity >= threshold → REQ_ID_RENUMBERED

### ba_tools/citation.py

The section-scoped citation verification module (TOOL-06).

**Exports:**
- `extract_section(doc_text, section_name) -> str` — iterates `splitlines`, matches `^(#{1,6})\s+(.*)`, normalizes heading title via `.lstrip('#').strip().lower()` (Pitfall 2), captures body until same-or-higher-level heading (Pitfall 5 level-aware stop)
- `citation_exists(source_doc, span, section, cite_scope="section") -> bool` — returns False if `len(span) < 12`; with `cite_scope="document"` searches whole file; with `cite_scope="section"` calls `extract_section` and checks `span in section_text`

### ba_tools/commands/lint_reqs.py (filled)

- `_parse_md_table(text)` — Markdown pipe table parser returning list of row dicts
- `_extract_reqs_dict(text)` — extracts `{req_id: statement}` for stability check
- `run(args)` — reads requirements, runs all heuristics, outputs `ok_json(findings=[...], checked=N)`
- Always exits 0 (lint = reporter, D-08); exits 2 only if file not found/path traversal

### ba_tools/commands/verify_cmd.py (filled)

- Folds all lint heuristics per row
- For each `stated` req with a `span` column: calls `citation_exists` with the row's `source` and `section` columns
- Aggregates findings; any FAIL → `BaToolsError(fail_findings)` (exit 2)
- WARN-only or empty → `ok_json(findings=[...], checked=N)` (exit 0, D-08)

---

## Verification Results

| Check | Result |
|-------|--------|
| `pytest tests/test_lint_reqs.py -v` — 9 passed | PASS |
| `pytest tests/test_verify.py -v` — 14 passed | PASS |
| `pytest tests/ -v` — 72 passed, 0 failed, 17 xfailed | PASS (no regressions) |
| renumbered_reqs fixture produces REQ_ID_RENUMBERED (pass 2) | PASS |
| No ML/NLP imports in lint.py | PASS |
| MATERIAL_CHANGE_THRESHOLD = 0.75 | PASS |
| Ambiguity findings carry severity="warn" | PASS |
| Grounding/verifiability/atomicity carry severity="fail" | PASS |
| verify exits 2 with CITATION_NOT_FOUND for out-of-section span | PASS |
| verify exits 0 for WARN-only result | PASS |
| --cite-scope document flips out-of-section span to pass | PASS |
| Span < 12 chars rejected (citation_exists returns False) | PASS |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] Added --repo-root to test CLI invocations**
- **Found during:** Task 1 GREEN (first test run)
- **Issue:** Tests used `tmp_path` (OS temp dir) which is outside the git repo root. `is_within_root` correctly blocked this, but tests needed `--repo-root tmp_path` to exercise the CLI against their own temp directory.
- **Fix:** All `run_lint()` and `run_verify()` helper functions pass `--repo-root str(tmp_path)` to the CLI invocation.
- **Files modified:** `tests/test_lint_reqs.py`, `tests/test_verify.py`
- **Commit:** 959c970 (lint tests), 94ae545 (verify tests)

**2. [Rule 2 - Missing] check_verifiability uses permissive pattern set**
- **Found during:** Task 1 implementation
- **Issue:** The plan specifies "no measurable/verifiable cue" but a strict implementation would over-flag requirements with normative verbs like `shall` + action verbs. RESEARCH Pitfall 4 spirit applies to verifiability too.
- **Fix:** Added normative verbs (`shall`, `must`, backtick identifiers, action verbs like `return`, `validate`, `log`) as positive verifiability cues alongside numeric thresholds.
- **Impact:** Fewer false positives for concrete requirements that use normative language without explicit numbers.

### Plan Adaptation Notes

- The plan's `verify_cmd` description mentions `--requirements`/`--config` arguments. The existing stub used `--reqs`/`--source`. The tests were written for `--reqs`/`--source` (matching the stub), so those names were kept.
- The plan says verify reads `source_trace.doc`/`source_trace.span` — the Markdown table format uses `Source`/`Section`/`Span` columns for the same data (flat table representation of source_trace).

---

## Known Stubs

None — both tasks produced fully functioning implementations. No placeholder data flows to output.

---

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| T-1-01 mitigated | verify_cmd.py | source_doc path validated via is_within_root before read_text (T-1-09) |
| T-1-01 mitigated | lint_reqs.py | requirements + baseline paths validated via is_within_root before read |
| T-1-11 mitigated | lint.py | All regex patterns are linear-time: \b-anchored word matches, fixed conjunction pattern, no catastrophic backtracking; span check uses plain `in` operator |

No new threat surface beyond the plan's threat model (T-1-01, T-1-09, T-1-11 all implemented).

---

## Self-Check: PASSED

Files created/verified:
- `.agents/ba-daily-operators/ba-tools/ba_tools/lint.py` — exists, contains `is_material_change`, `WEASEL_WORDS`, `detect_reqid_issues`
- `.agents/ba-daily-operators/ba-tools/ba_tools/citation.py` — exists, contains `extract_section`, `citation_exists`
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/lint_reqs.py` — filled (no longer raises NOT_IMPLEMENTED)
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/verify_cmd.py` — filled (no longer raises NOT_IMPLEMENTED)
- `.agents/ba-daily-operators/ba-tools/tests/test_lint_reqs.py` — 9 test functions
- `.agents/ba-daily-operators/ba-tools/tests/test_verify.py` — 14 test functions

Commits verified:
- f3d3100 (test(01-05): RED phase lint-requirements tests)
- 959c970 (feat(01-05): lint.py + lint_reqs.py GREEN)
- cf34e78 (test(01-05): RED phase citation + verify tests)
- 94ae545 (feat(01-05): citation.py + verify_cmd.py GREEN)
