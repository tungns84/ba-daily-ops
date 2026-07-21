---
phase: BAOPS-01-harness-foundation
plan: 08
subsystem: doctor-diagnostics
tags: [python, diagnostics, dependency-dag, zero-network, launchers]

requires:
  - phase: BAOPS-01-06
    provides: Closed local schemas and deterministic workspace-state diagnostics
  - phase: BAOPS-01-07
    provides: Exact-version local generations and generated repository-root launchers
provides:
  - Ordered validated doctor registry with core, initialized-state, and optional checks
  - Dependency-aware continuation with descendant-only skips and aggregate severity
  - Complete safe DOCTOR_FAILED snapshots and warning-success envelopes
  - Read-only zero-network sequential, parallel, and generated-launcher evidence
affects: [BAOPS-01-09, BAOPS-01-10, BAOPS-01-11, portability, foundation-ci]

tech-stack:
  added: []
  patterns:
    - Immutable check definitions are validated before any probe executes
    - Registry declaration order is the sole result order across status and platform outcomes
    - Local executable probes use fixed argument vectors, shell=False, bounded time, and redacted output
    - Independent state and host probes continue while only failed descendants are skipped

key-files:
  created:
    - packages/ba-tools/src/ba_tools/doctor.py
    - packages/ba-tools/tests/integration/test_doctor.py
  modified:
    - packages/ba-tools/src/ba_tools/cli.py
    - packages/ba-tools/src/ba_tools/__main__.py
    - packages/ba-tools/tests/security/test_zero_network.py

key-decisions:
  - "Validate non-empty core membership, global ID uniqueness, unique known prerequisites, declaration-order dependencies, and acyclicity before probing."
  - "Treat the current interpreter as installed only when it is the contained active-generation interpreter and both metadata and module versions equal 0.1.0."
  - "Run initialized-state validation independently of Git/install findings so malformed durable state still returns direct diagnostics."
  - "Keep NFR-02 project status pending because this Windows host cannot provide native POSIX or exact-minimum-host evidence."

patterns-established:
  - "Doctor DAG: every selected definition yields exactly one CheckResult in declaration order."
  - "Failure envelope: DOCTOR_FAILED carries the complete DoctorResult as one safe detail object."
  - "Optional policy: disabled optional tools warn under --all and do not change exit zero."

requirements-completed: [FOUND-02, NFR-02, NFR-03, NFR-04]

coverage:
  - id: D1
    description: "Core, initialized-state, and optional doctor checks are selected and returned in exact declared order"
    requirement: FOUND-02
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_doctor.py::test_default_and_all_scopes_are_ordered"
        status: pass
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_doctor.py::test_pre_and_post_init_scopes_are_exact"
        status: pass
    human_judgment: false
  - id: D2
    description: "Required failures, optional warnings, dependency skips, and complete remediation use the required streams and exits"
    requirement: FOUND-02
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_doctor.py::test_required_failure_exits_two"
        status: pass
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_doctor.py::test_failed_prerequisites_skip_only_descendants"
        status: pass
    human_judgment: false
  - id: D3
    description: "Doctor remains byte-preserving and zero-network under synchronized parallel snapshots"
    requirement: NFR-03
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_doctor.py::test_doctor_is_read_only_and_zero_network"
        status: pass
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_doctor.py::test_parallel_doctor_snapshots_are_independent"
        status: pass
      - kind: integration
        ref: "packages/ba-tools/tests/security/test_zero_network.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "A generated repository-root launcher returns the complete doctor --all snapshot from a Unicode path"
    requirement: NFR-04
    verification:
      - kind: e2e
        ref: "packages/ba-tools/tests/integration/test_doctor.py::test_generated_launcher_exposes_complete_doctor_snapshot"
        status: pass
    human_judgment: false
  - id: D5
    description: "Doctor source and launcher behavior remain portable to supported POSIX hosts"
    requirement: NFR-02
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_doctor.py — current Windows host"
        status: pass
    human_judgment: true
    rationale: "Native POSIX and exact Windows 10/macOS 12 execution evidence remains assigned to Plans 01-09 through 01-11; this plan does not claim unavailable host evidence."

duration: 18min
completed: 2026-07-21
status: complete
---

# Phase BAOPS-01 Plan 08: Ordered Doctor Snapshot Summary

**A validated dependency-aware doctor registry now returns complete ordered pre/post-init snapshots through direct and generated-launcher execution without network access or workspace mutation**

## Performance

- **Duration:** 18 min
- **Started:** 2026-07-21T18:07:18Z
- **Completed:** 2026-07-21T18:24:31Z
- **Tasks:** 2 completed
- **Files modified:** 5 implementation and test files

## Accomplishments

- Added nine ordered core checks, six initialized-state checks, and three known optional checks with strict registry validation before execution.
- Added aggregate pass/warning/fail behavior, complete `DOCTOR_FAILED` snapshots, descendant-only skips, and independent continuation after unrelated failures.
- Proved read-only, zero-network, byte-stable sequential and synchronized parallel snapshots with safe untruncated diagnostics.
- Generated and exercised a repository-root launcher from a Unicode path; `doctor --all` returned the complete ordered success/warning snapshot.
- Preserved all 134 package tests and a clean Ruff gate.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the RED doctor registry and snapshot contract** - `9108b13` (test)
2. **Task 2: Implement ordered local doctor diagnostics** - `05c5aa7` (feat)

**Plan metadata:** committed with this summary and sequential tracking updates.

## Files Created/Modified

- `packages/ba-tools/src/ba_tools/doctor.py` - Frozen registry/result models, validation, selection, dependency execution, local probes, aggregation, and snapshot service.
- `packages/ba-tools/src/ba_tools/cli.py` - Emission-free `doctor` and `doctor --all` routing with warning and failure envelopes.
- `packages/ba-tools/src/ba_tools/__main__.py` - Stable `doctor` command identity on every error path.
- `packages/ba-tools/tests/integration/test_doctor.py` - D-07 through D-10 registry, scope, severity, diagnostics, safety, concurrency, and generated-launcher evidence.
- `packages/ba-tools/tests/security/test_zero_network.py` - Doctor coverage in sequential and parallel runtime command-denial matrices.

## Decisions Made

- Registry validity is fail-fast and side-effect free: core membership, IDs, prerequisites, order, timeout, and cycles are checked before any probe.
- Declared registry order remains authoritative; result status never reorders checks.
- A prerequisite with any non-pass result blocks only its declared descendants, while unrelated probes continue.
- Installed-version health requires the current process to be the active contained interpreter and both installed metadata and module identity to equal `0.1.0`.
- Initialized-state checks do not depend on Git/install health, preserving direct malformed-state findings in mixed-failure snapshots.
- NFR-02 remains pending at project level; no native POSIX or exact-minimum-host evidence is claimed from this Windows execution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserved doctor command identity on failure**
- **Found during:** Task 2
- **Issue:** The existing process boundary recognized only `init`; a doctor failure would otherwise be labeled `unknown`.
- **Fix:** Added `doctor` to the sole process command-name resolver.
- **Files modified:** `packages/ba-tools/src/ba_tools/__main__.py`
- **Verification:** Required doctor failure returns one `command: doctor` error envelope with exit 2.
- **Committed in:** `05c5aa7`

**2. [Rule 2 - Missing Critical] Extended permanent zero-network command coverage**
- **Found during:** Task 2
- **Issue:** Adding a CLI command without registering it in the permanent runtime command matrix intentionally fails the security suite.
- **Fix:** Added default/`--all` doctor execution to sequential and synchronized parallel socket/DNS denial tests.
- **Files modified:** `packages/ba-tools/tests/security/test_zero_network.py`
- **Verification:** All guarded doctor processes avoid denial exit 97; the full security suite passes.
- **Committed in:** `05c5aa7`

**3. [Rule 1 - Bug] Avoided hostname-related network audit events**
- **Found during:** Task 2 focused zero-network verification
- **Issue:** High-level platform discovery reached a socket audit event under the fail-closed network guard.
- **Fix:** Read Windows version from `sys.getwindowsversion()` and POSIX kernel facts from `os.uname()`.
- **Files modified:** `packages/ba-tools/src/ba_tools/doctor.py`
- **Verification:** Doctor passes sequential and parallel socket/DNS denial.
- **Committed in:** `05c5aa7`

**4. [Rule 1 - Bug] Kept state diagnostics independent from repository metadata**
- **Found during:** Task 2 malformed-state verification
- **Issue:** State checks initially depended on `repo.root`, hiding direct malformed-state diagnostics in an explicit non-Git test root.
- **Fix:** Removed the unnecessary dependency while retaining containment on every state read.
- **Files modified:** `packages/ba-tools/src/ba_tools/doctor.py`
- **Verification:** `state.config` reports the complete parse diagnostic while unrelated install findings fail or skip independently.
- **Committed in:** `05c5aa7`

---

**Total deviations:** 4 auto-fixed (3 bugs, 1 missing critical)
**Impact on plan:** All changes enforce the existing stream, zero-network, continuation, and complete-diagnostic contracts without adding product scope.

## Issues Encountered

- The current repository does not retain generated launcher/runtime files in Git. Launcher behavior was therefore generated and exercised in an isolated Unicode repository fixture from the committed installer templates, active pointer contract, approved lock identity, and locked interpreter.
- The optional draw.io executable is unavailable on this host; `doctor --all` reports the planned warning and exits zero when all required checks pass.

## Known Stubs

None.

## Threat Flags

None. Local process output, filesystem state, launcher identity, and zero-network surfaces were declared in the plan threat model and are covered by automated tests.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

- Plan 01-09 can consume the complete doctor snapshot in offline smoke and ordinary CI jobs.
- Plans 01-09 through 01-11 still own native POSIX, remote CI, and exact-minimum-host evidence; this plan makes no claim for unavailable host execution.
- No local doctor, CLI contract, zero-network, UTF-8, launcher, test, or lint blocker remains.

## Self-Check: PASSED

- All five created or modified implementation and test artifacts exist.
- Task commits `9108b13` and `05c5aa7` exist with no tracked deletions.
- The complete locked-interpreter package suite passes 134 tests.
- Ruff passes across package source, tests, installer, and scripts.
- The generated repository-root launcher doctor test passes from a Unicode path with a complete ordered `--all` snapshot.
- Coverage metadata classifies four deliverables as automated pass and keeps NFR-02 routed to human/external evidence.
- Stub and threat scans found no implementation placeholder or undeclared security surface.
- The authorized `.planning/config.json` change remains uncommitted.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-21*
