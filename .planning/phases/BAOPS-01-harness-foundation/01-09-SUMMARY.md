---
phase: BAOPS-01-harness-foundation
plan: 09
subsystem: foundation-ci
tags: [python, github-actions, offline-smoke, powershell-5.1, portability]

requires:
  - phase: BAOPS-01-04
    provides: Single-emission, zero-network, and UTF-8 process contracts
  - phase: BAOPS-01-05
    provides: Containment, locking, atomicity, and recovery contracts
  - phase: BAOPS-01-06
    provides: Schema-backed init and repair transitions
  - phase: BAOPS-01-07
    provides: Exact-version offline installer and generated launchers
  - phase: BAOPS-01-08
    provides: Complete ordered doctor snapshots
provides:
  - Reusable offline install-to-launcher foundation smoke with redacted evidence
  - Exact supported-version and eight-category terminal-state regression suites
  - Least-privilege six-combination ordinary GitHub Actions workflow source
affects: [BAOPS-01-10, BAOPS-01-11, foundation-ci, portability-evidence]

tech-stack:
  added: []
  patterns:
    - Dependency acquisition is isolated from offline product execution
    - Workflow permissions and immutable action pins are enforced by fast source tests
    - Compatibility workflow source, remote run evidence, and exact-minimum-host evidence remain separate claims

key-files:
  created:
    - scripts/smoke_foundation.py
    - packages/ba-tools/tests/portability/test_supported_versions.py
    - packages/ba-tools/tests/portability/test_terminal_states.py
    - packages/ba-tools/tests/contract/test_foundation_workflow.py
    - .github/workflows/foundation.yml
  modified: []

key-decisions:
  - "Run product commands only through generated launchers after the offline installer completes, under a process-start network denial hook."
  - "Bind Windows py -3 discovery to the selected matrix interpreter with invocation-scoped PY_PYTHON."
  - "Treat ordinary hosted workflow source as compatibility coverage only; Plan 01-10 owns remote run evidence and Plan 01-11 owns exact-minimum-host evidence."

patterns-established:
  - "Smoke evidence: record only redacted host facts, full source/lock hashes, stable command IDs, exits, and stream classifications."
  - "CI boundary: acquire approved wheels first, then install and execute from locked local wheelhouses with read-only repository permissions."

requirements-completed: [FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06, NFR-02, NFR-03, NFR-04, NFR-05]

coverage:
  - id: D1
    description: "Offline installation from an approved wheelhouse exercises version, help, fresh/no-op/partial/repair init, and pre/post doctor only through generated launchers"
    requirement: FOUND-03
    verification:
      - kind: e2e
        ref: ".ba-tools-runtime/dev/Scripts/python.exe scripts/smoke_foundation.py --expected-platform windows — pass on current Windows host"
        status: pass
    human_judgment: false
  - id: D2
    description: "Exact OS/Python floors and all eight terminal UI categories retain complete deterministic byte and collection behavior"
    requirement: NFR-04
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/portability/test_supported_versions.py + test_terminal_states.py — 19 passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Workflow source declares read-only permissions, six ordinary combinations, full-SHA actions, locked interpreters, stock PowerShell, and offline smoke"
    requirement: NFR-02
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/contract/test_foundation_workflow.py — 8 passed"
        status: pass
    human_judgment: false
  - id: D4
    description: "Foundation additions preserve every established package, installer, launcher, CLI, state, doctor, containment, atomicity, zero-network, and UTF-8 contract"
    requirement: NFR-03
    verification:
      - kind: integration
        ref: ".ba-tools-runtime/dev/Scripts/python.exe -m pytest packages/ba-tools/tests -q -m 'not online_install' — 161 passed"
        status: pass
      - kind: other
        ref: ".ba-tools-runtime/dev/Scripts/python.exe -m ruff check packages/ba-tools/src packages/ba-tools/tests installer scripts — pass"
        status: pass
    human_judgment: false
  - id: D5
    description: "The ordinary six-job workflow actually succeeds remotely and exact Windows 10/macOS 12 hosts satisfy the support floor"
    requirement: NFR-02
    verification: []
    human_judgment: true
    rationale: "Workflow source and current-host execution cannot prove remote job conclusions or native exact-minimum hosts; Plans 01-10 and 01-11 remain blocking evidence owners."

duration: 25min
completed: 2026-07-21
status: complete
---

# Phase BAOPS-01 Plan 09: Offline Foundation Smoke and Ordinary CI Summary

**A reusable generated-launcher smoke now proves the complete foundation journey offline, while exact boundary/UI tests and a read-only six-combination workflow source prepare—but do not claim—remote compatibility evidence**

## Performance

- **Duration:** 25 min
- **Started:** 2026-07-21T18:34:41Z
- **Completed:** 2026-07-21T18:59:25Z
- **Tasks:** 2 completed
- **Files modified:** 5

## Accomplishments

- Added a deterministic smoke that copies source into a Vietnamese path with spaces, installs from an approved wheelhouse, invokes only generated launchers, exercises all required init/doctor states, denies product network access, and writes path-redacted evidence.
- Added exact Windows 10, macOS 12, and Python 3.11 floor coverage plus named integrated tests for empty, loading, error, populated, partial, overflow, zero-one-many, and long-text terminal states.
- Added a top-level `contents: read` ordinary Windows/macOS/Linux × Python 3.11/3.14 workflow with full-SHA actions, locked interpreters, explicit Windows PowerShell Desktop 5.1 checks, POSIX source checks, offline smoke, and redacted evidence upload.
- Preserved the evidence boundary: no remote job result or exact Windows 10/macOS 12 host result is asserted.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Define portability smoke contracts** - `891b4af` (test)
2. **Task 1 GREEN: Add offline foundation smoke** - `a48801f` (feat)
3. **Task 2: Add least-privilege foundation matrix** - `f9cfc40` (ci)

**Plan metadata:** committed with this summary and sequential tracking updates.

## Files Created/Modified

- `scripts/smoke_foundation.py` - Offline install-to-launcher journey, canonical JSON validation, network denial, host/hash/stream evidence, and CLI.
- `packages/ba-tools/tests/portability/test_supported_versions.py` - Exact floors, one-step-below failures, newer integer tuples, and malformed-version cases.
- `packages/ba-tools/tests/portability/test_terminal_states.py` - Eight named integrated terminal-state categories with non-TTY, `NO_COLOR`, collection, and byte assertions.
- `packages/ba-tools/tests/contract/test_foundation_workflow.py` - Fast deterministic workflow permissions, matrix, action pin, interpreter, offline-smoke, and PowerShell source contracts.
- `.github/workflows/foundation.yml` - Six ordinary hosted OS/Python combinations with isolated wheel acquisition and offline product execution.

## Decisions Made

- Product smoke commands execute only through the installer-generated root launcher; support operations such as source copy and commit hashing remain outside the product boundary.
- On Windows, `PY_PYTHON` is set only for the installer subprocess so `py -3` resolves to the exact Python selected by the matrix job.
- Workflow setup may acquire only the approved locked wheels. Development installation then uses a local wheelhouse, and product execution runs offline under its runtime guard.
- Ordinary hosted runners are not described as Windows 10 or macOS 12. Static source completion is not remote success, and local Windows execution is not three-OS evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserved the package directory during smoke source copy**
- **Found during:** Task 1 offline smoke execution
- **Issue:** A name-only ignore rule intended for a generated root launcher also excluded `packages/ba-tools`, causing the copied installer to report a missing dependency lock.
- **Fix:** Restricted copy exclusions to runtime, Git, state, and cache directories so package source and locks are preserved.
- **Files modified:** `scripts/smoke_foundation.py`
- **Verification:** The current Windows host completed the full offline smoke successfully.
- **Committed in:** `a48801f`

**2. [Rule 1 - Bug] Made synthetic macOS and overflow tests portable on Windows**
- **Found during:** Task 1 GREEN verification
- **Issue:** Windows lacks `os.uname`, and passing an oversized JSON payload through a Windows command line exceeded the process limit before the product boundary ran.
- **Fix:** Injected the synthetic `uname` attribute explicitly and validated overflow through the canonical byte serializer while retaining real subprocess coverage for long UTF-8 terminal output.
- **Files modified:** `packages/ba-tools/tests/portability/test_supported_versions.py`, `packages/ba-tools/tests/portability/test_terminal_states.py`
- **Verification:** All 19 focused portability/UI tests pass.
- **Committed in:** `a48801f`

**3. [Rule 2 - Missing Critical] Bound Windows installer discovery to the matrix Python**
- **Found during:** Task 2 workflow integration
- **Issue:** `install.ps1` correctly prefers `py -3`, but an ordinary runner may expose multiple Python 3 installations; the smoke must use the exact matrix family whose wheelhouse was prepared.
- **Fix:** Set invocation-scoped `PY_PYTHON` from the smoke interpreter before invoking stock Windows PowerShell and the installer.
- **Files modified:** `scripts/smoke_foundation.py`
- **Verification:** The final offline smoke passed with Python 3.14.6 and Windows PowerShell Desktop 5.1, and workflow tests assert exact matrix selection.
- **Committed in:** `f9cfc40`

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing critical)
**Impact on plan:** All fixes enforce the planned portability, offline, and exact-interpreter contracts without adding runtime features or weakening evidence boundaries.

## Issues Encountered

- No independent YAML parser or `actionlint` executable is installed in the locked local toolchain. The workflow's indentation, top-level sections, matrix rows, expressions, permissions, pins, commands, and prohibited claims are therefore validated by the committed eight-test source contract. Actual GitHub interpretation and job conclusions remain Plan 01-10 scope.

## Known Stubs

None. Stub scans found only typed optional defaults and intentionally empty arrays used by the tested UI contracts.

## Threat Flags

None. Workflow token privilege, third-party action immutability, dependency acquisition, product network denial, and evidence-claim boundaries are all declared in the plan threat model and source-tested.

## User Setup Required

None - no secrets, external service configuration, or persistent machine changes are required.

## Next Phase Readiness

- Plan 01-10 can run the committed `foundation` workflow at an exact commit and inspect all six remote job conclusions without changing the source contract.
- Plan 01-11 still must attach native Windows 10 with Windows PowerShell Desktop 5.1 and macOS 12 evidence before NFR-02 can be considered fully demonstrated.
- The authorized `.planning/config.json` change remains uncommitted.

## Self-Check: PASSED

- All five created plan artifacts exist, and task commits `891b4af`, `a48801f`, and `f9cfc40` exist with no tracked deletions.
- Focused portability/UI verification passes 19 tests; fast workflow-source verification passes 8 tests.
- The complete locked-interpreter package suite passes 161 tests, and Ruff passes across package source, tests, installer, and scripts.
- Current-host evidence records full commit `f9cfc40f4b0b863c8903ad8b2e9c077890bfaaa4`, exact lock hashes, Windows 10.0.26200, Python 3.14.6, and Windows PowerShell Desktop 5.1 without absolute repository, home, runtime, or interpreter paths.
- No remote CI success or exact macOS 12 host result is claimed; Plans 01-10 and 01-11 remain required.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-21*
