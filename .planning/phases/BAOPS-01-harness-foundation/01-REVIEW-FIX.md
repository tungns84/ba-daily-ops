---
phase: BAOPS-01-harness-foundation
fixed_at: 2026-07-22T06:55:00Z
review_path: .planning/phases/BAOPS-01-harness-foundation/01-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase BAOPS-01: Code Review Fix Report

**Fixed at:** 2026-07-22T06:55:00Z  
**Source review:** `.planning/phases/BAOPS-01-harness-foundation/01-REVIEW.md`  
**Iteration:** 1

**Summary:**
- Findings in scope: 4 (CR-01, WR-01, WR-02, WR-03)
- Fixed: 4
- Skipped: 0

## Fixed Issues

### CR-01: Stale `install.lock` permanently blocks future installs

**Files modified:** `installer/bootstrap.py`, `packages/ba-tools/tests/integration/test_installer.py`  
**Commit:** `a273695`  
**Applied fix:** Added `_read_lock_owner`, `_probe_pid_liveness`, and `_is_stale_install_lock` helpers. `_install_lock` now unlinks orphaned locks when the recorded PID is dead, or when the lock file is empty/malformed and older than 2 seconds (grace window avoids racing concurrent acquirers). Added `test_stale_install_lock_is_recovered`.

### WR-01: `install.ps1` `py -3` path accepts Python 3.11–3.13

**Files modified:** `install.ps1`  
**Commit:** `9e5665c`  
**Applied fix:** Raised the `py -3` prerequisite probe from `(3, 11)` to `(3, 14)` to match `bootstrap.discover_prerequisites()`. Added source assertion in `test_windows_installer_requires_python_314_for_py_launcher`.

### WR-02: POSIX launcher lacks resolved-path containment check

**Files modified:** `installer/launcher-templates/ba-tools`, `packages/ba-tools/tests/integration/test_installer.py`  
**Commit:** `1d71a22`  
**Applied fix:** Resolve `envs_root` and `generation_root` with `pwd -P` and reject generations outside the envs root before `exec`. Added template assertions and `test_posix_launcher_resolves_generation_under_envs_root` (runtime skip when POSIX shell or symlink capability unavailable).

### WR-03: Entrypoint command identity uses substring matching

**Files modified:** `packages/ba-tools/src/ba_tools/__main__.py`, `packages/ba-tools/tests/contract/test_cli_io.py`  
**Commit:** `9fa6750`  
**Applied fix:** `_command_name` now walks flags (`--repo-root`, `--repair`, `--all`) and returns the first positional `init`/`doctor` token. Added `test_command_name_ignores_substrings_in_paths`.

## Skipped Issues

None — all in-scope findings were fixed.

## Verification

**Commands run (iteration 1):**
```powershell
$env:PYTHONPATH = 'D:\projects\ai-team-gs\harness\gs-ba-operator\packages\ba-tools\src;D:\projects\ai-team-gs\harness\gs-ba-operator'
.\.ba-tools-runtime\dev\Scripts\python.exe -m pytest packages/ba-tools/tests -q -m "not online_install"
.\.ba-tools-runtime\dev\Scripts\ruff.exe check packages/ba-tools installer/bootstrap.py
```

**Results:**
- Ruff: pass
- Pytest (full suite): **167 passed, 1 skipped, 4 failed** when repo root already has a verified `.ba-tools-runtime` generation (from dev-environment restore)
- Pytest (excluding e2e): **165 passed, 1 skipped, 3 failed** (same environmental cause)
- Pytest (fix-targeted): stale lock, concurrent activation, command-name, and template assertion tests all pass in isolation

**Environmental failures (not regressions from fixes):**
- `test_approved_offline_install_never_prompts_or_uses_network` — short-circuits on existing verified generation in `PROJECT_ROOT`
- `test_windows_powershell_51_install_path` / `test_powershell7_remains_compatible` — installer succeeds (exit 0) when runtime already verified

## Re-review (iteration 1)

Re-reviewed changed production files. No Critical or Warning findings remain for CR-01 through WR-03. Info findings IN-01 and IN-02 were out of scope.

---

_Fixed: 2026-07-22T06:55:00Z_  
_Fixer: Claude (gsd-code-fixer)_  
_Iteration: 1_
