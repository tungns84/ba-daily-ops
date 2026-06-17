---
phase: 01-deterministic-ba-tools-cli-foundational-gates
plan: "01"
subsystem: ba-tools-cli-foundation
tags: [python, cli, argparse, filelock, pytest, scaffold]
dependency_graph:
  requires: []
  provides:
    - ba_tools package (importable, dispatchable via python -m ba_tools)
    - BaToolsError class with failures list
    - ok_json / fail_json flat-envelope helpers (D-03, D-04)
    - resolve_repo_root / is_within_root path-safety helpers (TOOL-14, T-1-01)
    - 12 command stubs (register + run each)
    - conftest.py with 5 shared fixtures
    - 15 test_*.py stubs (xfail Wave 1)
  affects:
    - All Wave-1 plans (fill in command bodies against these contracts)
    - Phase 1 Nyquist sampling (pyproject.toml pytest config now active)
tech_stack:
  added:
    - filelock 3.29.4 (single runtime dependency)
    - setuptools build_meta (editable install)
  patterns:
    - argparse subcommand dispatch via set_defaults(func=run)
    - BaToolsError -> stderr JSON + exit 2 handler (D-04)
    - Flat output envelope {"ok": bool, "failures": [], ...fields} (D-03)
    - Path-traversal guard via Path.resolve().is_relative_to() (T-1-01)
    - resolve_repo_root: --repo-root arg > git toplevel > cwd fallback
key_files:
  created:
    - .agents/ba-daily-operators/ba-tools/pyproject.toml
    - .agents/ba-daily-operators/ba-tools/ba_tools/__init__.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/__main__.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/errors.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/output.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/repo.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/__init__.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/init_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/resolve_route.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/state_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/lint_reqs.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/verify_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/uc_status.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/extract_uc.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/template_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/discovery_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/scan_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/byte_check.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/confirm_cmd.py
    - .agents/ba-daily-operators/ba-tools/tests/conftest.py
    - .agents/ba-daily-operators/ba-tools/tests/test_resolve_route.py
    - .agents/ba-daily-operators/ba-tools/tests/test_byte_check.py
    - .agents/ba-daily-operators/ba-tools/tests/test_state.py
    - .agents/ba-daily-operators/ba-tools/tests/test_init.py
    - .agents/ba-daily-operators/ba-tools/tests/test_config.py
    - .agents/ba-daily-operators/ba-tools/tests/test_uc_status.py
    - .agents/ba-daily-operators/ba-tools/tests/test_lint_reqs.py
    - .agents/ba-daily-operators/ba-tools/tests/test_verify.py
    - .agents/ba-daily-operators/ba-tools/tests/test_extract_uc.py
    - .agents/ba-daily-operators/ba-tools/tests/test_template.py
    - .agents/ba-daily-operators/ba-tools/tests/test_discovery.py
    - .agents/ba-daily-operators/ba-tools/tests/test_scan.py
    - .agents/ba-daily-operators/ba-tools/tests/test_confirm.py
    - .agents/ba-daily-operators/ba-tools/tests/test_output_contract.py
    - .agents/ba-daily-operators/ba-tools/tests/test_paths.py
    - .agents/ba-daily-operators/ba-tools/.gitignore
  modified: []
decisions:
  - "pyproject.toml build-backend set to setuptools.build_meta (not setuptools.backends.legacy:build which requires newer setuptools)"
  - "Package installed in editable mode (pip install -e .[test]) so tests can import ba_tools without path manipulation"
  - "15 test_*.py files created (plan frontmatter lists 15; the '17' in plan text refers to 15 test files + conftest + pyproject items)"
metrics:
  duration: "9 minutes"
  completed: "2026-06-17T12:02:37Z"
  tasks_completed: 3
  files_created: 36
---

# Phase 01 Plan 01: ba-tools Wave-0 Foundation Summary

**One-liner:** Python package skeleton with argparse dispatcher, BaToolsError/ok_json/fail_json flat-envelope contracts, path-traversal guard, 12 command stubs, and 15 xfail test stubs installed via editable pyproject.toml.

---

## What Was Built

Wave-0 foundation for the `ba-tools` CLI. Every subsequent Wave-1 plan builds command implementations against these contracts.

**Package structure:**
- `ba_tools/__init__.py` — package marker
- `ba_tools/__main__.py` — argparse dispatcher; loops over 12 command modules calling `mod.register(subs)`; catches `BaToolsError` → stderr JSON + exit 2; catches `KeyboardInterrupt` → exit 130
- `ba_tools/errors.py` — `BaToolsError(failures: list[dict])` — terse message, structured failures, no traceback content (T-1-07)
- `ba_tools/output.py` — `ok_json(**fields)` flat envelope to stdout; `fail_json(failures)` to stderr + sys.exit(2) (D-03, D-04)
- `ba_tools/repo.py` — `resolve_repo_root(arg)` with git-toplevel fallback; `is_within_root()` path-traversal guard via `Path.resolve().is_relative_to()` (T-1-01)
- `ba_tools/commands/__init__.py` — package marker
- 12 command stubs — each exposes `register(subparsers)` + `run(args)` raising `NOT_IMPLEMENTED` until Wave 1

**Subcommand names (from DESIGN §5, hyphenated):**
init, resolve-route, state, lint-requirements, verify, uc-status, extract-uc, template, discovery, scan, byte-check, confirm

**Test scaffold:**
- `tests/conftest.py` — 5 shared fixtures: `tmp_ba_ops`, `sample_reqs`, `renumbered_reqs`, `citation_pass_doc`, `citation_fail_doc`
- 15 `tests/test_*.py` stub files — all xfail Wave 1 except `test_paths.py` (6 live passing tests) and `test_output_contract.py` (2 live passing tests)
- `pyproject.toml` — `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `addopts = "-q"`

---

## Verification Results

| Check | Result |
|-------|--------|
| `python -c "import filelock; print(filelock.__version__)"` | 3.29.4 |
| `python -m ba_tools --help` lists all 12 subcommands | PASS |
| `python -m ba_tools resolve-route ba-mermaid` exits 2, stderr JSON `ok:false` | PASS |
| `python -m pytest tests/ -v` — 8 passed, 47 xfailed, exit 0 | PASS |
| No hard-coded absolute paths in any .py or .toml file | PASS |
| All 12 command modules define `register` and `run` | PASS |
| `is_within_root(child, root)` returns True; `is_within_root(parent, root)` returns False | PASS |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pyproject.toml build-backend corrected**
- **Found during:** Task 3 verification (editable install attempt)
- **Issue:** `setuptools.backends.legacy:build` is not available in the installed setuptools version (pip raised `BackendUnavailable`)
- **Fix:** Changed `build-backend` to `setuptools.build_meta` (standard setuptools entry point, universally available)
- **Files modified:** `.agents/ba-daily-operators/ba-tools/pyproject.toml`
- **Commit:** a20d1bd (included in Task 3 commit)

**2. [Rule 2 - Missing] Added .gitignore for ba-tools package**
- **Found during:** Post-commit untracked file check after editable install
- **Issue:** `__pycache__/`, `*.egg-info/`, `.pytest_cache/` were untracked generated files that would clutter git status
- **Fix:** Created `.agents/ba-daily-operators/ba-tools/.gitignore` listing standard Python generated outputs
- **Files modified:** `.agents/ba-daily-operators/ba-tools/.gitignore`
- **Commit:** 0d21890

### Plan Count Clarification (non-deviation)

The PLAN.md text says "17 test files" but the frontmatter `files_modified` lists 15 `test_*.py` files. The "17" in RESEARCH.md Wave 0 Gaps includes `conftest.py` (fixture file, not collected as test) and `pyproject.toml`. The 15 actual `test_*.py` files collect 55 test items, satisfying the ">= 17 collected test items" acceptance criterion.

---

## Known Stubs

All 12 command modules raise `BaToolsError(NOT_IMPLEMENTED)` — this is intentional Wave-0 design. Each stub is marked for Wave-1 implementation via xfail test annotations. No stubs block the plan's goal (Wave-0 scaffold).

---

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| No new threat surface | — | All files are local CLI; no network endpoints, no auth paths, no new schema changes beyond what the plan's threat model covers (T-1-01, T-1-07, T-1-SC) |

---

## Self-Check: PASSED

Files created and verified:
- `ba_tools/__init__.py` exists
- `ba_tools/__main__.py` exists
- `ba_tools/errors.py` exists
- `ba_tools/output.py` exists
- `ba_tools/repo.py` exists
- `ba_tools/commands/__init__.py` exists
- 12 command stubs exist
- `tests/conftest.py` exists
- 15 test files exist

Commits verified:
- 359c8ce (Task 1 — filelock + package skeleton)
- 71c510b (Task 2 — errors.py, output.py, repo.py)
- a20d1bd (Task 3 — __main__.py + stubs + tests)
- 0d21890 (chore — .gitignore)
