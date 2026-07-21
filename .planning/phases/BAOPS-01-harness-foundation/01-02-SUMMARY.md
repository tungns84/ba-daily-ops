---
phase: BAOPS-01-harness-foundation
plan: 02
subsystem: python-foundation
tags: [python, dependency-locks, pytest, hatchling, utf-8]

requires:
  - phase: BAOPS-01-01
    provides: Human-approved binary-only dependency closures, wheel artifacts, and SHA-256 values
provides:
  - Exact ba-tools 0.1.0 metadata and synchronized installed/version surfaces
  - Universal runtime and development locks verified across all 16 approved targets
  - Canonical Python 3.14.6 development interpreter at .ba-tools-runtime/dev
  - Canonical packaged light-profile defaults and a behavior-first RED walking skeleton
affects: [BAOPS-01-03, installer, cli-contract, state-initialization]

tech-stack:
  added: [Python 3.14.6, click 8.4.2, filelock 3.29.6, jsonschema 4.26.0, hatchling 1.29.0, pytest 9.1.1, ruff 0.15.22]
  patterns:
    - Approved hash locks are verified before creating or using the development environment
    - Every local Python verification uses the project-local locked interpreter
    - Packaged JSON defaults are canonical UTF-8 with LF line endings

key-files:
  created:
    - packages/ba-tools/pyproject.toml
    - packages/ba-tools/requirements.lock
    - packages/ba-tools/requirements-dev.lock
    - scripts/verify_dependency_locks.py
    - packages/ba-tools/src/ba_tools/__init__.py
    - packages/ba-tools/src/ba_tools/__main__.py
    - packages/ba-tools/src/ba_tools/state/resources/defaults/config.json
    - packages/ba-tools/src/ba_tools/state/resources/defaults/coverage-policy.json
    - packages/ba-tools/src/ba_tools/state/resources/defaults/business-goals.json
    - packages/ba-tools/tests/e2e/test_walking_skeleton.py
    - .gitignore
    - .gitattributes
  modified: []

key-decisions:
  - "Created the canonical development environment with the approved CPython 3.14.6 interpreter."
  - "Kept the application entrypoint importable but behaviorally RED until Plan 01-03 implements the CLI-to-state path."
  - "Enforced LF checkout semantics for packaged defaults so Windows cannot alter their canonical bytes."

patterns-established:
  - "DEV_PYTHON: all later local Python commands use .ba-tools-runtime/dev/Scripts/python.exe on Windows or .ba-tools-runtime/dev/bin/python on POSIX."
  - "RED skeleton: subprocess tests start successfully through the installed package and fail only at missing command/state behavior."

requirements-completed: [FOUND-01, FOUND-03, FOUND-04, NFR-03, NFR-04, NFR-05]

coverage:
  - id: D1
    description: "Approved runtime and development locks exactly reproduce every target closure, union, and wheel hash"
    requirement: FOUND-03
    verification:
      - kind: integration
        ref: ".ba-tools-runtime/dev/Scripts/python.exe scripts/verify_dependency_locks.py --approval .planning/phases/BAOPS-01-harness-foundation/01-01-SUMMARY.md --runtime-lock packages/ba-tools/requirements.lock --dev-lock packages/ba-tools/requirements-dev.lock"
        status: pass
    human_judgment: false
  - id: D2
    description: "Python 3.14.6 locked interpreter exposes package, installed metadata, and project version 0.1.0"
    requirement: FOUND-03
    verification:
      - kind: integration
        ref: ".ba-tools-runtime/dev/Scripts/python.exe -c version/import acceptance"
        status: pass
    human_judgment: false
  - id: D3
    description: "Three light-profile defaults are installed as exact canonical UTF-8 JSON resources"
    requirement: FOUND-04
    verification:
      - kind: integration
        ref: "importlib.resources installed-byte comparison and UTF-8/LF byte assertions"
        status: pass
    human_judgment: false
  - id: D4
    description: "Walking-skeleton tests collect and reach the intended RED CLI/state assertions from Unicode paths outside the repository"
    requirement: FOUND-01
    verification:
      - kind: e2e
        ref: "packages/ba-tools/tests/e2e/test_walking_skeleton.py — expected RED: 3 behavioral failures"
        status: pass
    human_judgment: false

duration: 1h 17m
completed: 2026-07-21
status: complete
---

# Phase BAOPS-01 Plan 02: Locked Python Foundation and RED Skeleton Summary

**Exact approved hash locks drive a Python 3.14.6 project-local environment, synchronized ba-tools 0.1.0 identity, canonical light-profile defaults, and three intentional behavioral RED tests**

## Performance

- **Duration:** 1h 17m, including the blocking human-action wait for an approved Python interpreter
- **Started:** 2026-07-21T09:26:00Z
- **Completed:** 2026-07-21T10:43:26Z
- **Tasks:** 3 completed
- **Files modified:** 12 tracked project files plus the ignored development environment

## Accomplishments

- Reproduced all 16 approved target closures, 13-package runtime union, 17-package development union, and 27 approved wheel hashes with zero missing or extra packages.
- Built `.ba-tools-runtime/dev` with CPython 3.14.6, installed only the hash-locked binary development closure, and installed `ba-tools==0.1.0` without dependency resolution or build isolation.
- Added exact canonical packaged defaults and three subprocess tests that collect successfully and fail only because `init`, idempotency, and version envelope behavior remain intentionally unimplemented.

## Task Commits

Each task was committed atomically:

1. **Task 1: Generate approved universal locks and exact project metadata** - `9b74c66` (chore)
2. **Task 2: Synchronize package version surfaces and create the locked interpreter** - `980a63b` (feat)
3. **Task 3: Establish exact defaults and the RED walking-skeleton path** - `fe2dfca` (test)

**Plan metadata:** committed with this summary and sequential tracking updates.

## Files Created/Modified

- `packages/ba-tools/pyproject.toml` - Exact 0.1.0 project, dependency, build, pytest, Ruff, entry-point, and resource metadata.
- `packages/ba-tools/requirements.lock` - Universal approved runtime/bootstrap lock.
- `packages/ba-tools/requirements-dev.lock` - Universal approved development lock.
- `scripts/verify_dependency_locks.py` - Standard-library exact target, union, marker, pin, and hash comparator.
- `packages/ba-tools/src/ba_tools/__init__.py` - Literal `__version__ = "0.1.0"`.
- `packages/ba-tools/src/ba_tools/__main__.py` - Importable process boundary retained for Plan 01-03.
- `packages/ba-tools/src/ba_tools/state/resources/defaults/*.json` - Three canonical D-15 light-profile defaults.
- `packages/ba-tools/tests/e2e/test_walking_skeleton.py` - Init, idempotency, UTF-8 path, byte-stream, and exact-version RED contracts.
- `.gitignore` - Excludes local runtime, cache, build, and package metadata output.
- `.gitattributes` - Preserves LF bytes for packaged defaults on Windows.

## Decisions Made

- Used the manually installed CPython 3.14.6 because its exact Windows wheel artifacts were included in the approved closure; Python 3.13 remained ineligible.
- Left `entrypoint` as an importable exit-2 seam so subprocess startup is healthy while Plan 01-03 remains responsible for CLI/state behavior.
- Added path-scoped Git LF enforcement for packaged defaults to make the canonical byte contract survive Windows checkouts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Enforced canonical LF resource bytes on Windows**
- **Found during:** Task 3 (Establish exact defaults and the RED walking-skeleton path)
- **Issue:** Windows working-tree conversion produced CRLF resources, violating the required one trailing LF canonical byte contract.
- **Fix:** Added a path-scoped `.gitattributes` rule and normalized all three packaged defaults to UTF-8 without BOM and LF-only line endings.
- **Files modified:** `.gitattributes`, `packages/ba-tools/src/ba_tools/state/resources/defaults/*.json`
- **Verification:** Source and installed resource byte checks reject CR, BOM, missing LF, and duplicate trailing LF.
- **Committed in:** `fe2dfca`

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** The adjustment is required for the explicit cross-platform canonical-byte acceptance criterion and adds no product scope.

## Issues Encountered

- The first execution paused because only Python 3.13 was available and its `rpds-py` artifact was outside the approved CPython 3.11/3.14 contract. After the user installed Python 3.14.6, environment creation and hash verification succeeded.
- The walking-skeleton command exits with three failures by design: all tests start through the installed package and fail at the explicit missing `init`, idempotency, or version behavior assertion with empty process streams. Plan 01-03 turns this RED contract GREEN.

## Known Stubs

- `packages/ba-tools/src/ba_tools/__main__.py:6-10` - `entrypoint` currently returns exit code 2 without command behavior. This is intentional for the Plan 01-02 RED contract and is resolved by Plan 01-03.

## User Setup Required

None - the Python 3.14.6 prerequisite was completed during the human-action checkpoint, and no external service configuration is required.

## Next Phase Readiness

- Plan 01-03 can implement the single-emission CLI boundary and contained state initialization directly against the committed RED tests.
- All later local Python verification must use `.ba-tools-runtime/dev/Scripts/python.exe` on Windows or `.ba-tools-runtime/dev/bin/python` on POSIX.
- No dependency, version, package-import, fixture, or subprocess-startup blocker remains.

## Self-Check: PASSED

- All 12 tracked project artifacts and this summary exist.
- Task commits `9b74c66`, `980a63b`, and `fe2dfca` are valid commits.
- Coverage metadata classifies all four deliverables with passing automated evidence.
- Lock equality, Python 3.14.6/version imports, Ruff, canonical resource bytes, and the intended three-test RED result were reverified.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-21*
