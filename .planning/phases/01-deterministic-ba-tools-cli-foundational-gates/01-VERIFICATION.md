---
phase: 01-deterministic-ba-tools-cli-foundational-gates
verified: 2026-06-17T21:30:00Z
status: passed
score: 5/5
overrides_applied: 0
---

# Phase 01: Deterministic BA-Tools CLI — Verification Report

**Phase Goal:** A functionally complete `ba-tools` CLI exists — every command does only file/hash/command-provable work — with the `.ba-ops/` file-state spine scaffolded and the four foundational gates (byte-check, lockfile, deterministic route resolution, REQ-ID stability) operational so no later operator has to retrofit them.
**Verified:** 2026-06-17T21:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `ba-tools verify` rejects a span NOT a real ≥12-char verbatim substring in its cited section; accepts one that is; `--cite-scope document` override works | ✓ VERIFIED | `citation.py`: `len(span) < 12` → False; section-scoped extract in `extract_section`; `test_verify_pass_in_section`, `test_verify_fail_span_not_in_section`, `test_verify_cite_scope_document_override` — all pass in 142-test green run |
| 2 | `ba-tools lint-requirements` flags material statement change on renumbered-requirements fixture (REQ_ID_RENUMBERED) and flags ambiguity, atomicity, grounding, verifiability | ✓ VERIFIED | `lint.py`: `detect_reqid_issues` Pass 1 (same-ID material change) + Pass 2 (Jaccard-based renumber detection at 0.75 threshold); `lint_reqs.py` calls `detect_reqid_issues` when `--baseline` present; `test_material_change_fixture` asserts `REQ_ID_RENUMBERED severity=fail`; `test_material_change_on_existing_id` asserts `REQ_ID_MATERIAL_CHANGE` |
| 3 | `ba-tools state update|patch|advance` writes `.ba-ops/STATE.md` under FileLock; concurrent writer either waits or reclaims lock after 10s stale window; never clobbers | ✓ VERIFIED | `state_store.py`: `acquire_state_lock` returns `FileLock(str(lock_path), timeout=STALE_SECONDS)` (STALE_SECONDS=10); stale-lock reclaim via `os.remove` + `PermissionError` swallow; `state_cmd.py`: `except Timeout: raise BaToolsError(LOCK_TIMEOUT)` — never falls back to unguarded write; `test_concurrent_write` asserts ≥1 exit 0, exactly one writer's content, non-zero writer exits 2 with LOCK_TIMEOUT; `test_state_stale_lock_reclaimed` confirms stale-lock path |
| 4 | `ba-tools resolve-route <operator>` returns only static DEFAULT_ROUTE, never infers from free text; UTF-8 JSON to stdout; BaToolsError exits code 2 | ✓ VERIFIED | `resolve_route.py`: static `DEFAULT_ROUTES` dict (7 operators); no free-text inference; comment "Static table — NEVER derive from free text (DESIGN §4, T-1-04)"; live check: `resolve-route ba-mermaid` → `{"ok": true, "failures": [], "operator": "ba-mermaid", "default_route": "author"}` RC=0; `resolve-route unknown-op` → `{"ok": false, "failures": [{"code": "UNKNOWN_OPERATOR", ...}]}` RC=2 |
| 5 | CI/pre-commit byte-check fails build when any eager-loaded doc ≥ 32,768 B; all paths resolve relative to `--repo-root`; Python via `sys.executable` (no hard-coded machine paths) | ✓ VERIFIED | `byte_check.py`: `CODEX_LIMIT = 32768`; `size < limit` strict less-than; uses `resolve_under_root(raw, repo_root)` (WR-03 fix applied); `test_byte_check_rejects_path_escape` exits 2 + PATH_ESCAPE; pre-commit hook: graceful skip when `ba_tools` not importable, invokes `python -m ba_tools byte-check $STAGED_DOCS --repo-root "$REPO_ROOT"` — no drive-letter paths; `test_no_hardcoded_drive_letter_paths` scans all `ba_tools/*.py` for `[A-Za-z]:\\`; `test_no_bare_python_subprocess_calls` scans for bare `python`/`python3` in subprocesses |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ba_tools/__main__.py` | Dispatcher + BaToolsError handler + ok_json envelope | ✓ VERIFIED | 12 commands registered; BaToolsError → stderr JSON + exit 2; catch-all INTERNAL_ERROR without traceback |
| `ba_tools/citation.py` | Section-scoped citation existence check; ≥12-char span guard; level-aware heading stop | ✓ VERIFIED | `extract_section` normalizes headings, stops at same-or-higher level; `citation_exists` returns False for `len(span) < 12`; `--cite-scope document` searches whole file |
| `ba_tools/commands/verify_cmd.py` | Citation gate + lint fold + `--cite-scope` flag | ✓ VERIFIED | `cite_scope` arg parsed; `citation_exists(source_doc, span, section, cite_scope=cite_scope)` call at line 186; FAIL-class findings raise BaToolsError → exit 2; WARN-only exits 0 (D-08) |
| `ba_tools/lint.py` | REQ-ID stability (two-pass detector) + quality lint rules | ✓ VERIFIED | `detect_reqid_issues`: Pass 1 (same-ID material change) + Pass 2 (Jaccard 0.75 renumber); `_CONJUNCTION_PATTERN` requires second normative verb (WR-07 fix confirmed) |
| `ba_tools/commands/lint_reqs.py` | Calls `detect_reqid_issues` when `--baseline` provided; exits 0 always (reporter not gate) | ✓ VERIFIED | `detect_reqid_issues` invoked via `ba_tools.lint`; exits 0 on lint findings; exits 2 only on FILE_NOT_FOUND/PATH_TRAVERSAL |
| `ba_tools/state_store.py` | FileLock(timeout=10) + stale-lock reclaim + byte-idempotent `_serialize_state` | ✓ VERIFIED | `acquire_state_lock` returns `FileLock(str(lock_path), timeout=STALE_SECONDS)`; CR-01 fix at line 204: `stripped_body = body.strip("\n")`; SHA-256 determinism contract holds |
| `ba_tools/commands/state_cmd.py` | Lock acquire + Timeout handler + ok_json on success | ✓ VERIFIED | `from filelock import Timeout`; `acquire_state_lock(lock_path)` + `with lock:`; `except Timeout: raise BaToolsError(LOCK_TIMEOUT)` |
| `ba_tools/commands/resolve_route.py` | Static DEFAULT_ROUTES + UNKNOWN_OPERATOR exit 2 | ✓ VERIFIED | Live verification: RC=0 with ok envelope for known operator; RC=2 with UNKNOWN_OPERATOR for unknown operator |
| `ba_tools/commands/byte_check.py` | CODEX_LIMIT=32768; strict less-than; `resolve_under_root` | ✓ VERIFIED | `CODEX_LIMIT = 32768`; `size < limit`; `resolve_under_root` used (WR-03 fix); PATH_ESCAPE on traversal |
| `ba_tools/repo.py` | `is_within_root`, `resolve_repo_root`, `resolve_under_root` | ✓ VERIFIED | Used by all path-handling commands; WR-03/WR-04 centralization applied |
| `.agents/ba-daily-operators/hooks/pre-commit` | Byte-checks staged AGENTS.md files; graceful skip; no machine paths | ✓ VERIFIED | Graceful skip when `ba_tools` not importable; invokes via `python -m ba_tools byte-check`; no drive-letter paths |
| `pyproject.toml` | `ba-tools` entry point; `filelock` dependency; no absolute machine paths | ✓ VERIFIED | `ba-tools = "ba_tools.__main__:main"`; `filelock>=3.29.4`; no absolute paths |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `verify_cmd.py` | `citation.py` | `citation_exists(source_doc, span, section, cite_scope=...)` | ✓ WIRED | Call at line 186 with all four args including cite_scope |
| `lint_reqs.py` | `lint.py` | `detect_reqid_issues(old_reqs, new_reqs)` | ✓ WIRED | Called when `--baseline` present; results surfaced in output |
| `state_cmd.py` | `state_store.py` | `acquire_state_lock(lock_path)` + `merge_state(text, data, action)` | ✓ WIRED | Both calls present; lock wraps merge; Timeout re-raised as BaToolsError |
| `state_cmd.py` | `filelock` | `from filelock import Timeout` (direct) | ✓ WIRED | Imported directly in state_cmd (not re-exported from state_store) |
| `byte_check.py` | `repo.py` | `resolve_under_root(raw, repo_root)` | ✓ WIRED | WR-03 fix: shared helper used (was hand-rolled inline) |
| `extract_uc.py`, `scan_cmd.py`, `template_cmd.py` | `repo.py` | `resolve_under_root(raw, repo_root)` | ✓ WIRED | WR-04 fix: all three commands now use shared helper |
| `pre-commit` hook | `ba_tools` | `python -m ba_tools byte-check $STAGED_DOCS --repo-root "$REPO_ROOT"` | ✓ WIRED | Invoked for staged AGENTS.md files; graceful skip path present |
| `__main__.py` | All 12 command modules | `register(subs)` loop in `_COMMAND_MODULES` | ✓ WIRED | 12 subcommands registered and dispatched |

---

### Data-Flow Trace (Level 4)

No dynamic-data-rendering components (React/Vue/templates). All commands produce JSON stdout from file/hash/command-provable inputs. Data-flow trace N/A — all flows verified by spot-checks and test suite.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite — 142 tests pass | `python -m pytest tests/ -v --tb=short` (via subprocess bypass of RTK) | 142 passed in 29.43s, exit code 0 | ✓ PASS |
| resolve-route returns static JSON, exit 0 | `python -m ba_tools resolve-route ba-mermaid` | `{"ok": true, "failures": [], "operator": "ba-mermaid", "default_route": "author"}` | ✓ PASS |
| resolve-route unknown operator exits 2 | `python -m ba_tools resolve-route unknown-op` | `{"ok": false, "failures": [{"code": "UNKNOWN_OPERATOR", ...}]}` RC=2 | ✓ PASS |
| ba-tools --help lists all 12 subcommands | `python -m ba_tools --help` | All 12 commands shown in help text | ✓ PASS |

---

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes declared or found for this phase. Step 7c: SKIPPED (no probe scripts).

---

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| TOOL-01 | Init scaffold `.ba-ops/` | ✓ SATISFIED | `init_cmd.py` exists; registered in dispatcher |
| TOOL-02 | `resolve-route` static routing | ✓ SATISFIED | `resolve_route.py` DEFAULT_ROUTES; live verified |
| TOOL-03 | STATE.md FileLock guard | ✓ SATISFIED | `state_store.py` + `state_cmd.py`; `test_concurrent_write` passes |
| TOOL-04 | `lint-requirements` quality checks | ✓ SATISFIED | `lint_reqs.py` + `lint.py`; ambiguity/atomicity/grounding/verifiability flags |
| TOOL-05 | REQ-ID stability (renumber detection) | ✓ SATISFIED | `detect_reqid_issues` two-pass; `test_material_change_fixture` passes |
| TOOL-06 | Citation-exists gate | ✓ SATISFIED | `citation.py` + `verify_cmd.py`; section-scoped; `--cite-scope document` override; 5 verify tests pass |
| TOOL-09 | `uc-status` pipeline state read | ✓ SATISFIED | `uc_status.py` registered; reads Pipeline Steps from STATE.md body |
| TOOL-10 | `extract-uc` | ✓ SATISFIED | `extract_uc.py` registered; uses `resolve_under_root` (WR-04 fix) |
| TOOL-11 | `template` command | ✓ SATISFIED | `template_cmd.py` registered; uses `resolve_under_root` (WR-04 fix) |
| TOOL-12 | `discovery` command | ✓ SATISFIED | `discovery_cmd.py` registered |
| TOOL-13 | Flat JSON output envelope (`ok`, `failures`) | ✓ SATISFIED | `output.py`: `ok_json`; `errors.py`: `BaToolsError`; `__main__.py` handler; `test_output_contract.py` passes |
| TOOL-14 | BaToolsError exits code 2 | ✓ SATISFIED | `__main__.py`: `sys.exit(2)` on BaToolsError; catch-all INTERNAL_ERROR with no traceback (T-1-07) |
| TOOL-15 | `scan` command | ✓ SATISFIED | `scan_cmd.py` registered; uses `resolve_under_root` (WR-04 fix) |
| TRACE-01 | REQ-ID in SRS output | ✓ SATISFIED | Lint/verify gates enforce REQ-ID references in sources |
| TRACE-02 | Traceability index scaffolded | ✓ SATISFIED | `confirm_cmd.py` registered; scaffold structure in `.ba-ops/` |
| GATE-02 | `ba-tools lint-requirements` gate | ✓ SATISFIED | Operational; exits 0 (reporter mode D-08) unless FILE_NOT_FOUND |
| GATE-04 | Byte-check gate 32768 B | ✓ SATISFIED | `byte_check.py` CODEX_LIMIT=32768; `test_paths.py` traversal/relative tests pass |
| CDX-04 | Codex truncation limit enforced | ✓ SATISFIED | Same as GATE-04 — CODEX_LIMIT = 32768 |
| CDX-05 | `sys.executable`, no machine paths | ✓ SATISFIED | `test_no_hardcoded_drive_letter_paths` + `test_no_bare_python_subprocess_calls` pass; pre-commit hook uses no drive-letter paths |

Note: TOOL-07 and TOOL-08 are mapped to Phase 2 in REQUIREMENTS.md — not Phase 1 scope. All 19 Phase 1 requirement IDs verified as SATISFIED.

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `state_store.py` line 22 | `from filelock import FileLock, Timeout  # noqa: F401 — re-exported for state_cmd` | INFO | `state_cmd` imports `Timeout` directly from `filelock` — the `noqa` comment is stale but harmless |
| `lint.py` WEASEL_WORDS list | Duplicate entry "effectively" | INFO | Duplicate causes harmless double-match on that word; not a gate defect |
| `state_store.py` `merge_state` docstring | `Raises:` block documents only `ValueError`; `BaToolsError(UNKNOWN_PIPELINE_STEP)` and `BaToolsError(MISSING_PIPELINE_STATUS)` undocumented | WARNING (WR-01, deferred) | Documentation gap only — no runtime defect; both exceptions ARE raised correctly in code |
| `state_store.py` `update_pipeline_step` | `pipeline_step` directive silently no-ops when body has no Pipeline Steps section | WARNING (WR-02, deferred) | Edge case: valid step + status against STATE.md without a Pipeline Steps table returns `ok:true` with no change; does not affect success criteria |

No `TBD`, `FIXME`, or `XXX` markers found in phase-modified files. No unreferenced debt markers.

---

### Deferred Items (from Phase Review — non-blocking)

| Item | Reason Deferred | Impact on Success Criteria |
|------|-----------------|---------------------------|
| WR-01: `merge_state` docstring incomplete | Documentation gap only; no runtime defect | None |
| WR-02: `pipeline_step` silent no-op when body lacks Pipeline Steps section | Behavioral edge case; requires dedicated change + new test; does not affect any Phase 1 gate | None |
| WR-05: `is_within_root` Windows junction/non-existent-target untested | Test-hardening only; existing guard rejects normalized `..` escapes; existing PATH_ESCAPE tests pass | None |
| IN-01: Duplicate "effectively" in WEASEL_WORDS | Harmless double-match | None |
| IN-02: stale `noqa: F401` comment on Timeout import | Cosmetic | None |
| IN-03: `acquire_state_lock` docstring note about `FileLock` re-export is stale | Cosmetic | None |
| IN-04: Additional test coverage suggestions | Test hardening; all contract behaviors already tested | None |

No deferred item undermines any of the 5 success criteria.

---

### Human Verification Required

None. All 5 success criteria are verifiable programmatically and confirmed via test suite (142 passed) and live CLI spot-checks.

---

## Gaps Summary

No gaps. All 5 success criteria verified. 19 Phase 1 requirement IDs satisfied. 142 tests pass. No BLOCKERs remain after CR-01 fix (commit edc855d). Three deferred warnings (WR-01, WR-02, WR-05) are non-blocking and do not undermine any success criterion.

---

_Verified: 2026-06-17T21:30:00Z_
_Verifier: Claude (gsd-verifier)_
