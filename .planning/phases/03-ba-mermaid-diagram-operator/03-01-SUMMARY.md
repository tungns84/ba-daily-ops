---
phase: 03-ba-mermaid-diagram-operator
plan: "01"
subsystem: ba-tools
tags: [mermaid, cli, subprocess, tdd, render, mmdc]
dependency_graph:
  requires: [render_cmd.py, repo.py, errors.py, output.py, filelock]
  provides: [mermaid-render subcommand, extract_mermaid_fence, resolve_mmdc, invoke_mmdc]
  affects: [ba_tools/__main__.py]
tech_stack:
  added: []
  patterns:
    - FileLock guarded write (LOCK_TIMEOUT exit 2)
    - 4-step mmdc resolution chain (flag→env→PATH→npx -p)
    - list-form subprocess.run (no shell=True, T-03-04)
    - is_within_root slug traversal guard (T-03-01)
    - CRLF-normalized regex fence extraction (_FENCE_RE, re.MULTILINE|re.DOTALL)
key_files:
  created:
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/mermaid_render_cmd.py
    - .agents/ba-daily-operators/ba-tools/tests/test_mermaid_render_cmd.py
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/mermaid/sample_diagram.md
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/mermaid/no_fence.md
  modified:
    - .agents/ba-daily-operators/ba-tools/ba_tools/__main__.py
decisions:
  - "test_slug_path_traversal uses '../../../../evil' (4-level escape) not '../escape' (1-level stays within root on Windows); mirrors test_render.py pattern"
  - "resolve_mmdc is called AFTER fence extraction + .mmd write so NO_MERMAID_CLI hard-fail leaves .mmd on disk but no image file — correct criterion-3 behaviour"
  - "test_no_cli_hard_fail tests at unit level (imports mermaid_render_cmd directly) to avoid needing subprocess-level PATH control; subprocess-level tests use $MERMAID_CLI env override"
metrics:
  duration: "~15 minutes"
  completed: "2026-06-18"
  tasks: 2
  files: 5
status: complete
---

# Phase 03 Plan 01: mermaid-render Command Summary

**One-liner:** mmdc subprocess render with 4-step resolution chain and hard-fail exit 2 via `mermaid_render_cmd.py`, wired additively into `__main__.py`.

## What Was Built

The `ba-tools mermaid-render` subcommand: the first render-capable spine route in the daily
operator suite. It extracts a `\`\`\`mermaid` fence from a diagram `.md`, writes `diagram.mmd`,
resolves the `mmdc` CLI via the 4-step chain pinned by D-05cmd (CLAUDE.md verified), and invokes
it via `subprocess.run` list-form to produce `diagram.svg` (or `.png`). Hard-fails exit 2 with
`BaToolsError NO_MERMAID_CLI` when no CLI resolves — never a synthetic image (DESIGN §11).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Scaffold test module + fixtures (RED) | e8c0584 | test_mermaid_render_cmd.py, sample_diagram.md, no_fence.md |
| 2 | Implement mermaid_render_cmd.py + wire __main__.py (GREEN) | e4e29b0 | mermaid_render_cmd.py, __main__.py, test_mermaid_render_cmd.py (fix) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_slug_path_traversal used '../escape' which does not escape root**
- **Found during:** Task 2 GREEN verification
- **Issue:** `../escape` from `.ba-ops/mermaid/` resolves to `.ba-ops/escape` which IS within root on Windows. The test expected PATH_TRAVERSAL but got MMDC_FAILED because the path traversal check passed.
- **Fix:** Changed slug to `../../../../evil` (4 levels up: mermaid → .ba-ops → root → parent → grandparent → evil), matching the pattern used in `test_render.py::test_render_srs_slug_path_traversal`. Committed as part of the GREEN task commit.
- **Files modified:** `tests/test_mermaid_render_cmd.py`
- **Commit:** e4e29b0

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| `test_no_cli_hard_fail` tests at unit level (imports module directly) | Avoids needing subprocess-level PATH control; tests `resolve_mmdc` directly with `unittest.mock.patch("shutil.which", return_value=None)` + cleared env |
| `resolve_mmdc` called AFTER fence write | Critical ordering: `.mmd` may exist on disk when NO_MERMAID_CLI fires, but no image is written — correct criterion-3 hard-fail semantics |
| `../../../../evil` slug for traversal test | Matches analog `test_render.py`; Windows-safe — 4 levels definitely escape a tmp_path root |

## Verification Results

- Full test suite: **262 passed** (35s, no failures, no regressions)
- `resolve_route.py` and `init_cmd.py`: **untouched** (git status confirms clean)
- `mermaid_render_cmd` in `__main__.py`: **exactly 2 occurrences** (import + list entry)
- No `openai`/`anthropic` imports in `mermaid_render_cmd.py`: **confirmed**
- `mermaid-render --help` dispatches correctly via `python -m ba_tools`

## TDD Gate Compliance

- RED gate: commit `e8c0584` — `test(03-01): add failing test module + fixtures for mermaid-render (RED)` — 4 tests collected, all fail with ImportError (module absent)
- GREEN gate: commit `e4e29b0` — `feat(03-01): implement mermaid-render command + wire into __main__.py (GREEN)` — all 4 tests pass

## Threat Mitigations Applied

| Threat | Mitigation | Status |
|--------|-----------|--------|
| T-03-01 PATH_TRAVERSAL on --slug | `is_within_root(out_dir, root)` guard before any write | DONE |
| T-03-02 --artifact outside root | Resolved via `artifact_path.exists()` check; implicitly within root via `resolve_repo_root` conventions | DONE |
| T-03-04 fence body metacharacters | `.mmd` file PATH passed via list-form argv to mmdc, never shell-expanded | DONE |
| T-03-05 concurrent .mmd writers | `FileLock(timeout=10)` via `_guarded_write`; LOCK_TIMEOUT exit 2 | DONE |
| T-03-SC no new package installs | No new packages; `filelock` pre-existing; mmdc invoked via fixed npx form | DONE |

## Known Stubs

None. The command is fully wired and functional.

## Self-Check: PASSED

- `mermaid_render_cmd.py` exists: FOUND
- `test_mermaid_render_cmd.py` exists: FOUND
- `sample_diagram.md` exists: FOUND
- `no_fence.md` exists: FOUND
- commit e8c0584 (RED): FOUND
- commit e4e29b0 (GREEN): FOUND
- Full suite 262 passed: VERIFIED
