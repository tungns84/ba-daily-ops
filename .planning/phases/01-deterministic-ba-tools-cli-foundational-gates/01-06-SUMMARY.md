---
phase: 01-deterministic-ba-tools-cli-foundational-gates
plan: "06"
subsystem: ba-tools-cli-utility-commands
tags: [python, cli, argparse, markdown-sections, extract-uc, template, discovery, scan, confirm]
dependency_graph:
  requires:
    - ba_tools package (01-01) — BaToolsError, ok_json, resolve_repo_root, is_within_root
  provides:
    - markdown_sections.extract (level-aware section extractor, reusable)
    - extract-uc command (TOOL-10)
    - template fill command (TOOL-11)
    - discovery add|list command (TOOL-12)
    - scan command (TOOL-15)
    - confirm command (GATE-02)
    - ba-core/templates/ seeded with .gitkeep + srs.md
  affects:
    - All operators that invoke extract-uc for UC section parsing
    - All operators that scaffold artifacts with template fill
    - ba-uc conductor workflow (uses confirm gate before irreversible steps)
    - Any skill that needs advisory injection scanning
tech_stack:
  added: []
  patterns:
    - Level-aware heading extraction via re.compile + splitlines (Pitfall-5 fix)
    - string.Template safe_substitute for deterministic field substitution
    - JSONL append for append-only discovery log
    - Advisory-only scan with fixed injection patterns (never blocks — D-07/D-08)
    - Pass-through gate pattern (v1 confirm exits 0, agent owns judgement)
key_files:
  created:
    - .agents/ba-daily-operators/ba-tools/ba_tools/markdown_sections.py
    - .agents/ba-daily-operators/ba-tools/ba-core/templates/.gitkeep
    - .agents/ba-daily-operators/ba-tools/ba-core/templates/srs.md
  modified:
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/extract_uc.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/template_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/discovery_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/scan_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/confirm_cmd.py
    - .agents/ba-daily-operators/ba-tools/tests/test_extract_uc.py
    - .agents/ba-daily-operators/ba-tools/tests/test_template.py
    - .agents/ba-daily-operators/ba-tools/tests/test_discovery.py
    - .agents/ba-daily-operators/ba-tools/tests/test_scan.py
    - .agents/ba-daily-operators/ba-tools/tests/test_confirm.py
    - .agents/ba-daily-operators/ba-tools/tests/test_output_contract.py
decisions:
  - "markdown_sections.extract stops only at same-or-higher heading level (Pitfall-5 fix — never truncate at ###)"
  - "template fill uses string.Template safe_substitute so unknown ${vars} remain as-is"
  - "discovery --note (not --text) per plan spec; stub used --text as placeholder"
  - "scan emits advisory WARN findings only, always exit 0 (Open Decision #2, D-07/D-08)"
  - "confirm is v1 pass-through exiting 0; --yes flag reserved for future non-interactive use"
  - "test_output_contract stub tests updated from confirm to uc-status error path (Rule 1 fix)"
metrics:
  duration: "12 minutes"
  completed: "2026-06-17T12:59:55Z"
  tasks_completed: 3
  files_created: 3
  files_modified: 11
---

# Phase 01 Plan 06: Utility Commands (extract-uc, template, discovery, scan, confirm) Summary

**One-liner:** Level-aware UC section extractor + deterministic template fill + JSONL discovery log + advisory injection scanner + v1 confirm pass-through, all backed by 27 tests.

---

## What Was Built

Five command modules completing the deterministic CLI command surface for the ba-tools spine.

**markdown_sections.py** (`extract(doc_text, heading, level=None)`):
- Iterates `splitlines(keepends=True)` matching `^(#{1,6})\s+(.*)` with `re`
- Records heading level on match, captures body until a heading at SAME or HIGHER level (fewer/equal `#`)
- Never stops at a deeper subsection — direct fix for RESEARCH Pitfall 5
- Reusable by any command needing section-scoped text

**extract-uc** (TOOL-10):
- Parses `"<file>: ## UC-NNN. <name>"` spec via `_SPEC_RE`
- Resolves source file under repo root (`is_within_root` — T-1-01)
- Calls `markdown_sections.extract(doc_text, heading_text, level=heading_level)`
- Returns `ok_json(uc_id, uc_name, section, source_file)`
- Errors: `BAD_SPEC`, `UC_NOT_FOUND`, `FILE_NOT_FOUND`

**template fill** (TOOL-11):
- Resolves template from `ba-core/templates/<name>.md`
- `--out` path guarded by `is_within_root` → `PATH_ESCAPE` error (T-1-09)
- `string.Template.safe_substitute(variables)` — unknown `${vars}` remain as-is (not an error)
- Creates output parent directories; returns `ok_json(out=<path>)`

**discovery add|list** (TOOL-12):
- `add --note <text> [--tag <id>]` appends `{"ts": ISO-8601, "note": ..., "tag": ...}` to `.ba-ops/discoveries.jsonl` (created on first write)
- `list [--uc <tag>]` reads all JSONL entries; optional tag filter; returns `ok_json(discoveries=[...])`
- Empty store returns `discoveries: []` not an error

**scan** (TOOL-15):
- 10 fixed advisory injection patterns (word-boundary anchored regex)
- Always `ok_json(findings=[...], blocked=False)` with exit 0 — never raises on content
- Only error: `FILE_NOT_FOUND` when target file is missing (exit 2)
- Findings carry `{"severity": "warn", "pattern": ..., "line": N}` (T-1-02)

**confirm** (GATE-02):
- v1 pass-through: `ok_json(confirmed=True, gate="confirm")` + exit 0
- Never reads stdin, never blocks
- `--yes` flag present for future non-interactive use; `--message` informational only

**ba-core/templates/**:
- `.gitkeep` seeds the directory in git
- `srs.md` provides a starting SRS scaffold with `${title}`, `${version}`, `${date}`, `${author}`, `${introduction}` variables

---

## Verification Results

| Check | Result |
|-------|--------|
| `pytest tests/test_extract_uc.py tests/test_template.py -v` | 12 passed |
| `pytest tests/test_discovery.py tests/test_scan.py -v` | 10 passed |
| `pytest tests/test_confirm.py -v` | 5 passed |
| Plan verification suite (all 5 test files) | 27 passed |
| Full suite `pytest tests/ -v` | 99 passed, 0 failed, 3 xfailed |
| extract-uc on multi-heading doc: `###` subsections included in body | PASS |
| extract-uc stops at next `##` (does not include UC-002) | PASS |
| template fill `--out ../escape.md` exits 2 with PATH_ESCAPE | PASS |
| scan on injection-pattern file exits 0 with WARN findings | PASS |
| confirm exits 0 with `confirmed:true, gate:confirm` | PASS |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_output_contract stub tests broken by confirm implementation**
- **Found during:** Full suite run after Task 3 commit
- **Issue:** `test_stub_command_exits_2_on_not_implemented` and `test_stub_command_stderr_is_flat_json` used `confirm` as a proxy for stub exit-2 behavior. With `confirm` now a v1 pass-through (exits 0), both tests failed.
- **Fix:** Updated both tests to use `uc-status` with no `.ba-ops/STATE.md` present — a reliable `BaToolsError(NO_STATE)` path that validates the same D-04 flat-JSON-stderr + exit-2 contract without relying on `NOT_IMPLEMENTED` stubs.
- **Files modified:** `.agents/ba-daily-operators/ba-tools/tests/test_output_contract.py`
- **Commit:** e765d59

**2. [Rule 2 - Missing] discovery --note vs --text argument name**
- **Found during:** Task 2 implementation
- **Issue:** The Wave-0 stub used `--text` but the plan and acceptance criteria specify `--note`.
- **Fix:** Implemented with `--note` per the plan specification. The stub `--text` was a placeholder.
- **Files modified:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/discovery_cmd.py`
- **No separate commit** — implemented correctly in the Task 2 commit.

---

## Known Stubs

None — all 5 commands in this plan are fully implemented. The 3 remaining xfails in the test suite (`test_output_contract.py` × 2, `test_paths.py` × 1) are pre-existing Wave-1 markers from plan 01-01, unrelated to this plan's scope.

---

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| No new surface | — | All commands are local file I/O; no network endpoints, no auth paths. T-1-01 (path traversal), T-1-09 (PATH_ESCAPE on --out), and T-1-02 (scan advisory WARN) are implemented as specified in the threat model. |

---

## Self-Check: PASSED

Files verified:
- `ba_tools/markdown_sections.py` exists: YES
- `ba_tools/commands/extract_uc.py` (not NOT_IMPLEMENTED): YES
- `ba_tools/commands/template_cmd.py` (not NOT_IMPLEMENTED): YES
- `ba_tools/commands/discovery_cmd.py` (not NOT_IMPLEMENTED): YES
- `ba_tools/commands/scan_cmd.py` (not NOT_IMPLEMENTED): YES
- `ba_tools/commands/confirm_cmd.py` (not NOT_IMPLEMENTED): YES
- `ba-core/templates/.gitkeep` exists: YES
- `tests/test_extract_uc.py` has live tests: YES
- `tests/test_template.py` has live tests: YES
- `tests/test_discovery.py` has live tests: YES
- `tests/test_scan.py` has live tests: YES
- `tests/test_confirm.py` has live tests: YES

Commits verified:
- 088a28f (Task 1 — extract-uc + markdown_sections + template fill)
- 8ccd735 (Task 2 — discovery + scan)
- 678bb95 (Task 3 — confirm)
- e765d59 (Rule 1 fix — test_output_contract stub tests)
