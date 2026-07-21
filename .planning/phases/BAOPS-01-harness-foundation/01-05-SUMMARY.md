---
phase: BAOPS-01-harness-foundation
plan: 05
subsystem: filesystem-reliability
tags: [python, pathlib, filelock, atomic-write, quarantine, concurrency]

requires:
  - phase: BAOPS-01-03
    provides: Contained path capabilities, native workspace lock, and create-only publication skeleton
  - phase: BAOPS-01-04
    provides: Process barriers, zero-network guard, and UTF-8 regression coverage
provides:
  - Strict POSIX-relative path grammar with resolved ancestry and real symlink/junction/reparse rejection
  - Native workspace ownership metadata with bounded contention and fail-closed stale-owner recovery
  - Distinct create/replace durability boundaries and byte-preserving abandoned-temp quarantine
affects: [BAOPS-01-06, state-initialization, repair, doctor, filesystem-boundary]

tech-stack:
  added: []
  patterns:
    - Validated path capabilities are rechecked immediately before filesystem publication
    - Native ownership sidecars exist only while the corresponding kernel lock is held
    - Atomic failures preserve prior canonical bytes and recognizable temporary evidence

key-files:
  created:
    - packages/ba-tools/tests/security/test_path_containment.py
    - packages/ba-tools/tests/reliability/test_atomic_write.py
    - packages/ba-tools/tests/reliability/test_locking.py
  modified:
    - packages/ba-tools/src/ba_tools/paths.py
    - packages/ba-tools/src/ba_tools/state/atomic.py
    - packages/ba-tools/src/ba_tools/state/locking.py

key-decisions:
  - "Keep the workspace lock in private runtime storage keyed by resolved repository identity, with a persistent native lock path and adjacent owner sidecar."
  - "Recover owner metadata only after native acquisition and proof that a same-host PID is dead; every ambiguous state remains byte-identical."
  - "Preserve abandoned temporary bytes in quarantine and never use them as canonical input."

patterns-established:
  - "Containment: reject unsafe grammar before candidate access, then check redirect components before and after resolved ancestry."
  - "Publication: sync a same-directory temp before separate create-only link or atomic replace operations."
  - "Recovery: sort recognizable temps, hard-link without overwrite into repo-local quarantine, then remove only the source evidence."

requirements-completed: [FOUND-05, FOUND-06, NFR-04]

coverage:
  - id: D1
    description: "Null, empty, absolute, drive, UNC, separator, traversal, sibling-prefix, Unicode, symlink, junction, reparse, and concurrent paths obey strict repository containment"
    requirement: FOUND-05
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/security/test_path_containment.py — 19 passed"
        status: pass
    human_judgment: false
  - id: D2
    description: "One native workspace lock serializes writers with a five-second timeout, crash release, owner lifecycle, and fail-closed ambiguity"
    requirement: FOUND-06
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/reliability/test_locking.py — 12 passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Create, replace, fsync, cleanup, parent-sync, and quarantine faults never expose partial canonical bytes or destroy recovery evidence"
    requirement: FOUND-06
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/reliability/test_atomic_write.py — 28 passed"
        status: pass
    human_judgment: false
  - id: D4
    description: "Filesystem hardening preserves every established CLI, process, zero-network, and UTF-8 contract"
    requirement: NFR-04
    verification:
      - kind: integration
        ref: ".ba-tools-runtime/dev/Scripts/python.exe -m pytest packages/ba-tools/tests -q -m 'not online_install' — 82 passed"
        status: pass
      - kind: other
        ref: ".ba-tools-runtime/dev/Scripts/python.exe -m ruff check packages/ba-tools/src packages/ba-tools/tests scripts — pass"
        status: pass
    human_judgment: false

duration: 24min
completed: 2026-07-21
status: complete
---

# Phase BAOPS-01 Plan 05: Filesystem Reliability Boundary Summary

**Strict path capabilities, native owner-aware locking, complete-only atomic publication, and byte-preserving quarantine are proven by 59 adversarial, multiprocessing, and fault-injection cases**

## Performance

- **Duration:** 24 min
- **Started:** 2026-07-21T11:56:24Z
- **Completed:** 2026-07-21T12:19:56Z
- **Tasks:** 2 completed
- **Files modified:** 6

## Accomplishments

- Rejected every unsafe business-path grammar before candidate access and proved real symbolic-link or Windows junction/reparse redirects cannot escape the resolved repository root.
- Added a persistent native lock identity with canonical owner metadata, deterministic five-second timeout, crash release, and same-host dead-PID-only recovery.
- Split create-only and replacement publication, injected every durability boundary, and quarantined abandoned same-directory temps without overwrite or promotion.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write RED containment, lock-owner, and durability matrices** - `52e8291` (test)
2. **Task 2: Harden containment, native ownership, publication, and quarantine** - `7d4b090` (feat)

**Plan metadata:** committed with this summary and sequential tracking updates.

## Files Created/Modified

- `packages/ba-tools/src/ba_tools/paths.py` - Strict path policy, ancestry assertion, repeated redirect inspection, and canonical capability identity.
- `packages/ba-tools/src/ba_tools/state/atomic.py` - Fault-addressable durable temps, create/replace publication, and collision-safe quarantine.
- `packages/ba-tools/src/ba_tools/state/locking.py` - Native lock lifecycle, owner schema, OS-local hostname/PID liveness, and stale recovery.
- `packages/ba-tools/tests/security/test_path_containment.py` - Ordinary, Unicode, redirect, reparse, sibling-prefix, and concurrent containment matrix.
- `packages/ba-tools/tests/reliability/test_atomic_write.py` - Canonical byte/hash/mtime, durability fault, repeated publication, and quarantine evidence.
- `packages/ba-tools/tests/reliability/test_locking.py` - Synchronized contention, timeout, crash, interruption, and ambiguous-owner evidence.

## Decisions Made

- Retained Plan 01-03's private runtime lock identity so persistent native lock files do not pollute durable `.ba-ops/` state.
- Wrote the owner sidecar only after native acquisition and removed it before release; a crash may leave evidence, but only a dead same-host PID permits recovery.
- Used operating-system local host APIs rather than `socket` so ownership proof does not weaken the permanent zero-network boundary.
- Kept create-only linking and replacement as separate operations; neither quarantine nor stale temporary bytes can become canonical input.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserved the zero-network runtime while recording host ownership**
- **Found during:** Task 2 (Harden containment, native ownership, publication, and quarantine)
- **Issue:** Importing `socket` for `gethostname()` violated the established runtime import and audit-hook zero-network contract.
- **Fix:** Used `GetComputerNameW` on Windows and `os.uname().nodename` on POSIX, with fail-closed host-identity errors.
- **Files modified:** `packages/ba-tools/src/ba_tools/state/locking.py`
- **Verification:** Full 82-test suite, including sequential and parallel zero-network guards, passes.
- **Committed in:** `7d4b090`

**2. [Rule 1 - Bug] Made temporary-evidence assertions non-vacuous**
- **Found during:** Task 2 (Harden containment, native ownership, publication, and quarantine)
- **Issue:** Initial fault assertions validated temporary bytes only if a temp existed, so premature cleanup could evade the intended D-18 evidence check.
- **Fix:** Required recognizable temps at every pre-publication/pre-cleanup fault and required no leak after successful cleanup.
- **Files modified:** `packages/ba-tools/tests/reliability/test_atomic_write.py`, `packages/ba-tools/tests/reliability/test_locking.py`
- **Verification:** All 28 atomic and 12 locking cases pass with deterministic synchronization.
- **Committed in:** `7d4b090`

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes enforce existing security and reliability contracts; no schema or state-transition scope was added.

## Issues Encountered

- The phase-wide Ruff template names the future `installer/` directory, which does not exist until a later plan. Ruff passes across every existing Python source, test, and script path.

## Known Stubs

None.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

- Plan 01-06 can integrate schema-backed classification and repair with validated path capabilities, one workspace lock, abandoned-temp quarantine, and separate create-only/replace publication.
- No containment, locking, atomicity, recovery, zero-network, UTF-8, or regression blocker remains.

## Self-Check: PASSED

- All six created or modified implementation/test files exist.
- Task commits `52e8291` and `7d4b090` exist and contain no tracked deletions.
- The focused containment/reliability gate passes all 59 cases through the locked interpreter.
- The complete local gate passes all 82 tests, and Ruff passes across every existing Python path.
- No placeholder or known-stub pattern exists in the six plan files.
- The only unrelated working-tree change remains the authorized uncommitted `.planning/config.json`.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-21*
