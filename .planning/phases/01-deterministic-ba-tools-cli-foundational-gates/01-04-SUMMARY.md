---
phase: 01-deterministic-ba-tools-cli-foundational-gates
plan: "04"
subsystem: ba-tools-scaffold-config-init-uc-status
tags: [python, cli, scaffold, config, state, traceability, pytest]
dependency_graph:
  requires:
    - ba_tools package (01-01)
    - BaToolsError / ok_json / resolve_repo_root (01-01)
    - state_store._parse_state / ALLOWED_KEYS (01-03)
    - DEFAULT_ROUTES table (01-01 stub, filled in 01-02)
  provides:
    - scaffold.ensure_scaffold(root) — idempotent .ba-ops/ creation with 5 seed files + 5 subdirs
    - config.load_config(root) — reads .ba-ops/config.json, never writes on absence
    - config.flag(cfg, name) — absent=true semantics (TRACE-02)
    - init_cmd fully implemented — validates operator, scaffolds, returns context JSON (TOOL-01, TRACE-01)
    - uc_status fully implemented — reads STATE.md, computes next_step statically (TOOL-09)
    - OPERATOR_ROUTES dict (init_cmd.py) — full route lists per operator
    - 18 passing tests across test_init.py (5), test_config.py (6), test_uc_status.py (7)
  affects:
    - All later operators call ba-tools init first (context entry point)
    - uc-status is the Phase 5 conductor's resumability primitive
    - .ba-ops/ shape established here is the traceability spine for all subsequent phases
tech_stack:
  added:
    - ba_tools/scaffold.py (new module)
    - ba_tools/config.py (new module)
  patterns:
    - ensure_scaffold(): path-safe idempotent writes under root/.ba-ops/ (T-1-01)
    - flag(): cfg.get(name, True) — absent=enabled, no disk write on absence (TRACE-02)
    - init_cmd validates operator against DEFAULT_ROUTES before any filesystem action (T-1-04)
    - uc_status: static PIPELINE_STEPS list drives next_step — no inference, no agent calls
    - STATE.md seed uses unquoted YAML scalars to match _parse_state() simple key:value parser
key_files:
  created:
    - .agents/ba-daily-operators/ba-tools/ba_tools/scaffold.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/config.py
  modified:
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/init_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/uc_status.py
    - .agents/ba-daily-operators/ba-tools/tests/test_init.py
    - .agents/ba-daily-operators/ba-tools/tests/test_config.py
    - .agents/ba-daily-operators/ba-tools/tests/test_uc_status.py
decisions:
  - "STATE.md seed file uses unquoted YAML scalars (step: 0 not step: \"0\") to match state_store._parse_state() simple key:value parser that does not strip quotes"
  - "--repo-root is a top-level argparse argument (before subcommand) — tests invoke python -m ba_tools --repo-root <path> init <op>, not init <op> --repo-root <path>"
  - "OPERATOR_ROUTES dict in init_cmd.py is the canonical full-route-list source (DEFAULT_ROUTES in resolve_route.py carries default only)"
  - "uc-status --uc arg takes precedence over STATE.md uc_id; empty string normalized to None"
  - "Pipeline Steps table parsed from STATE.md body via simple regex; missing steps default to 'pending'"
  - "_complete_statuses frozenset: complete, completed, done — case-insensitive next_step skip"
metrics:
  duration: "7 minutes"
  completed: "2026-06-17T12:33:16Z"
  tasks_completed: 2
  files_created: 2
  files_modified: 5
---

# Phase 01 Plan 04: Scaffold + Config + Init + UC-Status Summary

**One-liner:** Idempotent `.ba-ops/` scaffold (5 files + 5 subdirs), absent=enabled config loader, `init <operator>` context-JSON entry point, and `uc-status` static next-step resolver — the traceability spine and resumability primitive.

---

## What Was Built

The `.ba-ops/` file-state spine and the two commands every later operator workflow relies on.

**`ba_tools/scaffold.py`** (new module):
- `ensure_scaffold(root)` — creates `.ba-ops/` and writes 5 seed files + 5 subdirectory stubs
  idempotently (never overwrites existing files, so hand-edited content is preserved)
- Seed files: `PROJECT.md` (engagement header), `REQUIREMENTS.md` (REQ-ID registry),
  `INDEX.md` (traceability matrix header), `STATE.md` (YAML frontmatter + pipeline table),
  `config.json` (empty `{}` — absent flags default true per TRACE-02)
- Subdirs: `srs/`, `mermaid/`, `mockup/`, `backlog/`, `plugins/`

**`ba_tools/config.py`** (new module):
- `load_config(root)` — reads `.ba-ops/config.json` if present, returns `{}` otherwise;
  never creates or modifies the file (TRACE-02 anti-pattern guard)
- `flag(cfg, name)` — returns `cfg.get(name, True)` — absent key → `True` (enabled),
  `False` value → `False` (disabled)

**`ba_tools/commands/init_cmd.py`** (fully implemented, was stub):
- `register()` / `run()`: validates operator against `DEFAULT_ROUTES` (T-1-04: unknown → exit 2),
  calls `ensure_scaffold(root)`, loads config, parses STATE.md frontmatter summary
- Returns flat context JSON: `{ok, operator, default_route, routes, config, state, scaffold}`
- `OPERATOR_ROUTES` dict — canonical full route list per operator (all 7 operators from DESIGN §4)

**`ba_tools/commands/uc_status.py`** (fully implemented, was stub):
- `register()` / `run()`: resolves root, reads `.ba-ops/STATE.md` (missing → NO_STATE exit 2),
  parses Pipeline Steps table from Markdown body, computes `next_step` from static
  `PIPELINE_STEPS = ["srs-analyze", "mermaid", "mockup", "index"]` — pure deterministic read
- Returns: `{ok, uc, steps, next_step}` where `next_step` is first incomplete step or `"done"`

**Test files** (all passing, xfail markers removed):
- `tests/test_init.py` — 5 tests: scaffold creation, context JSON shape, idempotency,
  unknown operator exit 2, subdirectory creation
- `tests/test_config.py` — 6 tests: absent=true, explicit false, no disk write on absence,
  explicit true, empty config, no mutation on absent flag read
- `tests/test_uc_status.py` — 7 tests: pipeline state return, partial pipeline next_step,
  fully complete next_step='done', missing STATE.md exit 2, all-pending, steps dict
  completeness, --uc arg passthrough

---

## Verification Results

| Check | Result |
|-------|--------|
| `pytest tests/test_init.py tests/test_config.py tests/test_uc_status.py -v` | 18 passed |
| `pytest tests/ -v` — full suite | 49 passed, 27 xfailed, 0 failures |
| `python -m ba_tools --repo-root <tmp> init ba-uc` creates 5 files, returns context JSON | PASS |
| `flag({}, "render_enabled") is True` | PASS |
| `flag({"render_enabled": False}, "render_enabled") is False` | PASS |
| `init` twice does not clobber edited scaffold file | PASS |
| `config.py` uses `.get(` with True default, no config.json write on absence | PASS |
| Missing STATE.md → uc-status exits 2, NO_STATE code | PASS |
| srs-analyze complete → next_step == "mermaid" | PASS |
| All steps complete → next_step == "done" | PASS |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] STATE.md seed quoted YAML values**
- **Found during:** Task 1 behavioral verification (init command integration test)
- **Issue:** Initial STATE.md seed used quoted YAML scalars (`step: "0"`) but
  `state_store._parse_state()` is a simple `key: value` parser that does not strip quotes —
  resulting in state values like `"0"` (the string `"0"` with embedded quotes) in the JSON output
- **Fix:** Changed STATE.md seed to unquoted scalars (`step: 0`) which parse cleanly
- **Files modified:** `ba_tools/scaffold.py`
- **Commit:** 1cb0553

**2. [Rule 1 - Bug] Test helper used wrong argument order for --repo-root**
- **Found during:** Task 1 test run (first iteration)
- **Issue:** `--repo-root` is a top-level argparse argument — it must appear before the
  subcommand (`python -m ba_tools --repo-root <path> init <op>`), not after
  (`python -m ba_tools init <op> --repo-root <path>`)
- **Fix:** Updated `_run_init()` helper in test_init.py to place `--repo-root` before subcommand
- **Files modified:** `tests/test_init.py`
- **Commit:** 1cb0553

---

## Known Stubs

None — `init_cmd.py` and `uc_status.py` are fully implemented. All 5 seed files in the
scaffold have substantive content (no placeholder-only bodies). The scaffold seed is intentional
minimal content — each file documents itself and prompts the BA to fill in the real engagement
data.

---

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| No new threat surface | — | T-1-04 mitigated (operator validated against static DEFAULT_ROUTES table before filesystem action). T-1-01 mitigated (scaffold writes under root/.ba-ops/ derived from resolve_repo_root). T-1-10 mitigated (flag() uses cfg.get(name, True), no disk write on absence). No new network endpoints, auth paths, or schema changes beyond the plan's threat model. |

---

## Self-Check: PASSED

Files verified:
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/ba_tools/scaffold.py` — exists
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/ba_tools/config.py` — exists
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/ba_tools/commands/init_cmd.py` — exists, fully implemented
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/ba_tools/commands/uc_status.py` — exists, fully implemented
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/tests/test_init.py` — exists, 5 passing tests
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/tests/test_config.py` — exists, 6 passing tests
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/tests/test_uc_status.py` — exists, 7 passing tests

Commits verified:
- 1cb0553 — feat(01-04): scaffold.py + config.py + init command (TOOL-01, TRACE-01, TRACE-02)
- 8398d14 — feat(01-04): uc-status command — pipeline state + next_step (TOOL-09)
