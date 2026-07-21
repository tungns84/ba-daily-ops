---
phase: BAOPS-01-harness-foundation
plan: 03
subsystem: cli-state-foundation
tags: [python, click, filelock, atomic-write, utf-8, path-containment]

requires:
  - phase: BAOPS-01-02
    provides: Exact ba-tools 0.1.0 package, locked Python 3.14.6 interpreter, canonical defaults, and RED walking-skeleton tests
provides:
  - Single-emission JSON CLI boundary for help, version, init, parser errors, interruptions, and unexpected failures
  - Repo-root and canonical business-path capabilities with traversal, symlink, and reparse rejection
  - Bounded native workspace locking with same-directory synced create-only publication and exact read-back
  - Fresh and byte-preserving idempotent initialization of the three canonical .ba-ops files
affects: [BAOPS-01-04, BAOPS-01-05, BAOPS-01-06, cli-contract, state-initialization]

tech-stack:
  added: []
  patterns:
    - Click callbacks return data while entrypoint alone selects a stream and emits canonical JSON
    - Filesystem services receive resolved capabilities instead of unchecked business-path strings
    - One native workspace lock encloses classification, publication, and read-back
    - Atomic create uses a synced same-directory temp plus create-only hard-link publication

key-files:
  created:
    - packages/ba-tools/src/ba_tools/cli.py
    - packages/ba-tools/src/ba_tools/contracts.py
    - packages/ba-tools/src/ba_tools/errors.py
    - packages/ba-tools/src/ba_tools/paths.py
    - packages/ba-tools/src/ba_tools/init_command.py
    - packages/ba-tools/src/ba_tools/state/__init__.py
    - packages/ba-tools/src/ba_tools/state/atomic.py
    - packages/ba-tools/src/ba_tools/state/locking.py
  modified:
    - packages/ba-tools/src/ba_tools/__main__.py
    - packages/ba-tools/tests/e2e/test_walking_skeleton.py

key-decisions:
  - "Keep all command callbacks emission-free; entrypoint is the only process stream and exit boundary."
  - "Key the native lock by resolved repository identity in private runtime storage so durable workspace enumeration remains exactly the three canonical files without unsafe lock-file deletion."
  - "Treat exact packaged bytes as the validity contract for this walking skeleton; schema-backed classification remains Plan 01-06 scope."

patterns-established:
  - "CLI boundary: invoke Click with standalone_mode=False and map every result or failure to one canonical UTF-8 envelope."
  - "State boundary: parse canonical relative identities, resolve beneath one root capability, reject redirects, lock once, create-only publish, then read back exact bytes."

requirements-completed: [FOUND-01, FOUND-04, FOUND-05, FOUND-06, NFR-03, NFR-04, NFR-05]

coverage:
  - id: D1
    description: "No-args, help, exact version, and parser paths emit one compact UTF-8 JSON document on the designated stream"
    requirement: FOUND-01
    verification:
      - kind: e2e
        ref: "packages/ba-tools/tests/e2e/test_walking_skeleton.py::test_cli_version_is_exactly_0_1_0"
        status: pass
      - kind: integration
        ref: "locked-interpreter subprocess matrix for no-args, --help, --version, and invalid option"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fresh init from an external CWD and Unicode repository creates exactly the three packaged canonical state files"
    requirement: FOUND-04
    verification:
      - kind: e2e
        ref: "packages/ba-tools/tests/e2e/test_walking_skeleton.py::test_repo_root_init_walking_skeleton"
        status: pass
    human_judgment: false
  - id: D3
    description: "Repeated init follows the contained native-lock, create-only atomic, exact read-back path and preserves bytes and mtimes"
    requirement: FOUND-06
    verification:
      - kind: e2e
        ref: "packages/ba-tools/tests/e2e/test_walking_skeleton.py::test_repo_root_init_is_idempotent"
        status: pass
      - kind: integration
        ref: "locked-interpreter native FileLock and 5.0-second timeout assertion"
        status: pass
    human_judgment: false

duration: 24min
completed: 2026-07-21
status: complete
---

# Phase BAOPS-01 Plan 03: CLI-to-Contained-State Walking Skeleton Summary

**A real ba-tools 0.1.0 process now routes compact UTF-8 JSON through contained path capabilities, a bounded native lock, create-only atomic publication, and exact idempotent read-back**

## Performance

- **Duration:** 24 min
- **Started:** 2026-07-21T10:58:17Z
- **Completed:** 2026-07-21T11:22:09Z
- **Tasks:** 2 completed
- **Files modified:** 10

## Accomplishments

- Replaced the import-only RED seam with one non-bypassable Click-to-JSON process boundary for help, exact version, initialization, and safe failures.
- Created the three canonical `.ba-ops` files from exact packaged UTF-8 bytes through resolved path capabilities, one native lock, same-directory fsync, create-only publication, and read-back.
- Turned all three Plan 01-02 walking-skeleton tests green while preserving exact bytes and mtimes on a repeated initialization.

## Task Commits

Each task was committed atomically:

1. **Task 1: Complete the exact-version single-emission CLI boundary** - `97fa29d` (feat)
2. **Task 2: Make contained locked initialization GREEN** - `3e3e352` (feat)

**Plan metadata:** committed with this summary and sequential tracking updates.

## Files Created/Modified

- `packages/ba-tools/src/ba_tools/__main__.py` - Sole stream selection, error mapping, emission, and process exit boundary.
- `packages/ba-tools/src/ba_tools/cli.py` - Emission-free Click routing for help, version, and init.
- `packages/ba-tools/src/ba_tools/contracts.py` - Canonical UTF-8 serializer and stable success/error envelopes.
- `packages/ba-tools/src/ba_tools/errors.py` - Typed allowlisted expected failures.
- `packages/ba-tools/src/ba_tools/paths.py` - Resolved root/business-path capabilities and redirect rejection.
- `packages/ba-tools/src/ba_tools/init_command.py` - Fresh, exact-rerun, fixed-order initialization orchestration.
- `packages/ba-tools/src/ba_tools/state/atomic.py` - Synced same-directory temporary files and create-only publication.
- `packages/ba-tools/src/ba_tools/state/locking.py` - Five-second native per-workspace lock.
- `packages/ba-tools/src/ba_tools/state/__init__.py` - Explicit state-boundary exports.
- `packages/ba-tools/tests/e2e/test_walking_skeleton.py` - Correct repo-relative file identity assertion.

## Decisions Made

- Kept command handlers pure and centralized every product-output side effect in `entrypoint()`.
- Used a resolved-root digest for a private runtime lock identity. This keeps the workspace's durable file set exact on both Windows and POSIX without deleting a persistent Unix lock file and risking split-lock races.
- Limited this walking-skeleton validity check to exact packaged bytes. Partial repair and schema-backed invalid-state diagnostics remain explicitly assigned to Plan 01-06.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected absolute-versus-relative file identity in the RED test**
- **Found during:** Task 2 (Make contained locked initialization GREEN)
- **Issue:** `Path.rglob()` returns absolute paths, but the assertion compared `path.as_posix()` directly with repo-relative state names. The implementation reached this previously unreachable assertion after initialization became functional.
- **Fix:** Compared each discovered file through `path.relative_to(repo_root).as_posix()` while preserving the exact expected three-file set and every byte assertion.
- **Files modified:** `packages/ba-tools/tests/e2e/test_walking_skeleton.py`
- **Verification:** All three original behavioral scenarios pass through the locked interpreter.
- **Committed in:** `3e3e352`

**2. [Rule 1 - Bug] Avoided unsafe persistent lock-file pollution on POSIX**
- **Found during:** Task 2 (Make contained locked initialization GREEN)
- **Issue:** Native `filelock` backends have different lock-file lifecycles: Windows removes its lock path on release while POSIX intentionally retains it. A repository-root `.ba-ops.lock` would violate the exact three-file workspace contract on POSIX, while deleting it could split mutual exclusion across waiting processes.
- **Fix:** Kept the required native five-second lock but keyed its private runtime path by the resolved repository identity outside durable business state.
- **Files modified:** `packages/ba-tools/src/ba_tools/state/locking.py`
- **Verification:** The installed backend is native, timeout is exactly 5.0 seconds, and the cross-process walking skeleton leaves exactly the three canonical workspace files.
- **Committed in:** `3e3e352`

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both changes preserve the intended security and observable contracts without adding product scope or weakening tests.

## Issues Encountered

- The first GREEN run exposed the latent absolute-versus-relative assertion bug described above; initialization itself had already emitted the expected envelope and exact files.
- One transient command-classification rejection occurred while combining local reinstall, tests, and lint. Running the same verified operations separately succeeded; it did not affect source or repository state.

## Known Stubs

None.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

- Plan 01-04 can harden the process, dependency, zero-network, and UTF-8 matrices against the working CLI boundary.
- Plan 01-05 can expand adversarial path, contention, fault-injection, and recovery evidence around the established capabilities and storage primitives.
- Plan 01-06 remains responsible for schema-backed complete/partial/invalid classification and explicit repair behavior.

## Self-Check: PASSED

- All 10 created or modified implementation/test files exist.
- Task commits `97fa29d` and `3e3e352` exist and contain no tracked deletions.
- `.ba-tools-runtime/dev/Scripts/python.exe -m pytest packages/ba-tools/tests -q -m "not online_install"` passes with 3 tests.
- `.ba-tools-runtime/dev/Scripts/python.exe -m ruff check packages/ba-tools/src packages/ba-tools/tests scripts` passes.
- The only unrelated working-tree change remains the authorized uncommitted `.planning/config.json`.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-21*
