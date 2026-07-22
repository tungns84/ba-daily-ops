---
phase: BAOPS-01-harness-foundation
depth: standard
reviewed_at: 2026-07-22T06:55:00Z
file_count: 47
verdict: PASS
files_reviewed: 47
files_reviewed_list:
  - .gitattributes
  - .github/workflows/foundation.yml
  - .gitignore
  - install.ps1
  - install.sh
  - installer/bootstrap.py
  - installer/launcher-templates/ba-tools
  - installer/launcher-templates/ba-tools.ps1
  - packages/ba-tools/pyproject.toml
  - packages/ba-tools/requirements-dev.lock
  - packages/ba-tools/requirements.lock
  - packages/ba-tools/src/ba_tools/__init__.py
  - packages/ba-tools/src/ba_tools/__main__.py
  - packages/ba-tools/src/ba_tools/cli.py
  - packages/ba-tools/src/ba_tools/contracts.py
  - packages/ba-tools/src/ba_tools/doctor.py
  - packages/ba-tools/src/ba_tools/errors.py
  - packages/ba-tools/src/ba_tools/init_command.py
  - packages/ba-tools/src/ba_tools/paths.py
  - packages/ba-tools/src/ba_tools/state/__init__.py
  - packages/ba-tools/src/ba_tools/state/atomic.py
  - packages/ba-tools/src/ba_tools/state/locking.py
  - packages/ba-tools/src/ba_tools/state/resources/defaults/business-goals.json
  - packages/ba-tools/src/ba_tools/state/resources/defaults/config.json
  - packages/ba-tools/src/ba_tools/state/resources/defaults/coverage-policy.json
  - packages/ba-tools/src/ba_tools/state/resources/schemas/business-goals.schema.json
  - packages/ba-tools/src/ba_tools/state/resources/schemas/config.schema.json
  - packages/ba-tools/src/ba_tools/state/resources/schemas/coverage-policy.schema.json
  - packages/ba-tools/src/ba_tools/state/validation.py
  - packages/ba-tools/tests/conftest.py
  - packages/ba-tools/tests/contract/test_cli_io.py
  - packages/ba-tools/tests/contract/test_dependency_locks.py
  - packages/ba-tools/tests/contract/test_foundation_workflow.py
  - packages/ba-tools/tests/e2e/test_walking_skeleton.py
  - packages/ba-tools/tests/integration/test_doctor.py
  - packages/ba-tools/tests/integration/test_init.py
  - packages/ba-tools/tests/integration/test_installer.py
  - packages/ba-tools/tests/portability/test_supported_versions.py
  - packages/ba-tools/tests/portability/test_terminal_states.py
  - packages/ba-tools/tests/portability/test_utf8.py
  - packages/ba-tools/tests/reliability/test_atomic_write.py
  - packages/ba-tools/tests/reliability/test_locking.py
  - packages/ba-tools/tests/security/test_path_containment.py
  - packages/ba-tools/tests/security/test_zero_network.py
  - packages/ba-tools/tests/unit/test_defaults.py
  - scripts/smoke_foundation.py
  - scripts/verify_dependency_locks.py
findings:
  critical: 0
  warning: 0
  info: 2
  total: 2
status: clean
---

# Phase BAOPS-01: Code Review Report

**Reviewed:** 2026-07-22T05:01:00Z  
**Re-reviewed:** 2026-07-22T06:55:00Z  
**Depth:** standard  
**Files Reviewed:** 47  
**Verdict:** PASS  
**Status:** clean

## Summary

Reviewed the full Phase 1 foundation surface: `ba_tools` CLI/state/doctor modules, installer bootstrap and wrappers, smoke script, CI workflow, and associated tests. Core path containment, workspace locking, atomic publication, JSON envelope contracts, and hash-pinned offline install paths are well implemented and heavily tested.

**Original review (2026-07-22T05:01:00Z):** One Critical installer locking defect and three Warnings (Windows version gating, POSIX launcher containment, CLI command identity). Verdict was BLOCK.

**Fix iteration 1 (2026-07-22T06:55:00Z):** All four Critical/Warning findings were fixed and verified. Re-review of changed files found no remaining Critical or Warning issues. Two Info items (IN-01, IN-02) remain as non-blocking follow-ups.

**Recommendation:** Phase 1 foundation is merge-ready from a code-review perspective. Optional: address IN-01/IN-02 in a later pass.

## Critical Issues

_All Critical issues resolved in fix iteration 1. See `01-REVIEW-FIX.md`._

## Warnings

_All Warning issues resolved in fix iteration 1. See `01-REVIEW-FIX.md`._

## Info

### IN-01: `CheckDefinition.timeout` is never enforced

**File:** `packages/ba-tools/src/ba_tools/doctor.py:238-257`  
**Issue:** Each check declares a `timeout`, but `run_probe()` ignores it; subprocess probes hard-code their own timeouts (e.g. 5.0s in `_git_probe`). Registry metadata is misleading for future probes.

**Fix:** Pass `definition.timeout` into `_command_output` and add a watchdog for non-subprocess probes.

### IN-02: `atomic_replace` is implemented but unused in production paths

**File:** `packages/ba-tools/src/ba_tools/state/atomic.py:154-169`  
**Issue:** Only reliability tests call `atomic_replace`; production init uses create-only publication. Not a defect today, but the unused surface increases maintenance burden.

**Fix:** Either wire it into a future repair/replace path or narrow exports until needed.

---

_Reviewed: 2026-07-22T05:01:00Z_  
_Re-reviewed: 2026-07-22T06:55:00Z_  
_Reviewer: Claude (gsd-code-reviewer / gsd-code-fixer)_  
_Depth: standard_
