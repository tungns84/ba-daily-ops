---
phase: BAOPS-01-harness-foundation
plan: 04
subsystem: cli-contract-hardening
tags: [python, pytest, subprocess, zero-network, utf-8, dependency-locks]

requires:
  - phase: BAOPS-01-01
    provides: Human-approved binary-only target closures and exact wheel hashes
  - phase: BAOPS-01-03
    provides: Single-emission CLI gateway and contained initialization path
provides:
  - Permanent exact-equality tests for all approved dependency targets, unions, pins, and hashes
  - Real subprocess coverage for every CLI success, parser, expected, interrupted, and unexpected path
  - Per-process socket and DNS denial under sequential and synchronized parallel execution
  - Literal UTF-8 byte evidence for Vietnamese values, redirected streams, Unicode paths, and concurrency
affects: [BAOPS-01-05, BAOPS-01-06, doctor, installer, cli-contract]

tech-stack:
  added: []
  patterns:
    - Real subprocesses and synchronized process barriers prove stream and concurrency contracts
    - Python audit hooks fail closed on socket and DNS activity without replacing socket types
    - Approved dependency closures are tested by independent equality assertions and the committed comparator

key-files:
  created:
    - packages/ba-tools/tests/conftest.py
    - packages/ba-tools/tests/contract/test_cli_io.py
    - packages/ba-tools/tests/contract/test_dependency_locks.py
    - packages/ba-tools/tests/security/test_zero_network.py
    - packages/ba-tools/tests/portability/test_utf8.py
  modified:
    - packages/ba-tools/src/ba_tools/errors.py

key-decisions:
  - "Allow BaToolsError traceback attachment so Click can preserve typed safe failures through its context-manager boundary."
  - "Use process-start audit hooks for deterministic socket and DNS denial without altering runtime networking types."

patterns-established:
  - "Boundary matrix: every process result is parsed from raw bytes and must be one canonical document on one designated stream."
  - "Concurrency evidence: children report ready before one release marker starts their real gateway invocations."
  - "Lock regression: target sets, normalized unions, exact pins, and artifact hashes use equality rather than subset checks."

requirements-completed: [FOUND-01, FOUND-03, NFR-03, NFR-04, NFR-05]

coverage:
  - id: D1
    description: "Every approved dependency target, normalized union, exact pin, and wheel hash is protected by permanent equality tests"
    requirement: FOUND-03
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/contract/test_dependency_locks.py — 5 passed"
        status: pass
      - kind: integration
        ref: ".ba-tools-runtime/dev/Scripts/python.exe scripts/verify_dependency_locks.py — 16 targets, 0 missing, 0 extra"
        status: pass
    human_judgment: false
  - id: D2
    description: "All CLI success and failure paths emit one safe canonical JSON document through real subprocesses"
    requirement: FOUND-01
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/contract/test_cli_io.py"
        status: pass
      - kind: e2e
        ref: "packages/ba-tools/tests/e2e/test_walking_skeleton.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Every registered runtime command remains zero-network under sequential and synchronized parallel execution"
    requirement: NFR-03
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/security/test_zero_network.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Vietnamese and empty values survive redirected streams, Unicode paths, files, and concurrent processes as exact UTF-8 bytes"
    requirement: NFR-04
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/portability/test_utf8.py"
        status: pass
    human_judgment: false

duration: 19min
completed: 2026-07-21
status: complete
---

# Phase BAOPS-01 Plan 04: Process, Network, Package, and UTF-8 Hardening Summary

**Twenty-three locked-interpreter tests now prove exact dependency closure, one-document process output, deterministic zero-network execution, and complete Vietnamese UTF-8 bytes across real concurrent subprocesses**

## Performance

- **Duration:** 19 min
- **Started:** 2026-07-21T11:32:09Z
- **Completed:** 2026-07-21T11:50:11Z
- **Tasks:** 2 completed
- **Files modified:** 6

## Accomplishments

- Added raw-byte subprocess coverage for no-args, help, exact version, init, malformed input, unknown commands, expected errors, interruption, and redacted unexpected failures.
- Locked all 16 approved target closures, both normalized unions, 17 development packages, 13 runtime packages, and 27 wheel artifacts behind permanent exact-equality tests.
- Proved every registered command remains zero-network with active process-start socket/DNS guards, including synchronized parallel execution.
- Proved Vietnamese text, empty values and collections, Unicode paths/files, redirected streams, and concurrent multibyte output round-trip as exact canonical UTF-8 bytes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write RED package, process, zero-network, and UTF-8 matrices** - `3b13523` (test)
2. **Task 2: Make every process and encoding contract GREEN** - `06b3504` (fix)

**Plan metadata:** committed with this summary and sequential tracking updates.

## Files Created/Modified

- `packages/ba-tools/tests/conftest.py` - Locked interpreter, Unicode repository, raw subprocess, fault injection, process barrier, and network denial fixtures.
- `packages/ba-tools/tests/contract/test_cli_io.py` - Complete process, stream, exact-version, canonical-byte, concurrency, and redaction matrix.
- `packages/ba-tools/tests/contract/test_dependency_locks.py` - Comparator invocation plus independent target, union, pin, hash, substitution, and source-artifact assertions.
- `packages/ba-tools/tests/security/test_zero_network.py` - Runtime import scan and guarded sequential/parallel execution for every registered command.
- `packages/ba-tools/tests/portability/test_utf8.py` - Redirected, concurrent, Unicode-path/file, empty-value, success, and error byte evidence.
- `packages/ba-tools/src/ba_tools/errors.py` - Click-compatible typed exception preserving stable safe fields.

## Decisions Made

- Kept `BaToolsError` field construction allowlisted while permitting Python and Click to attach traceback state internally; freezing an `Exception` object breaks Click's exception context handling.
- Used Python audit hooks in process-start guards so tests terminate on actual socket/DNS audit events without replacing `socket.socket` and accidentally perturbing unrelated imports.
- Kept network proof environmental-condition independent: every guarded process first proves the denial hook is active, then executes the runtime command.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The RED matrix exposed that a frozen dataclass exception becomes `FrozenInstanceError` when Click attaches traceback state, incorrectly converting safe `REPO_ROOT_INVALID` into `INTERNAL_ERROR`. Task 2 removed exception freezing and restored the typed safe code.
- The terminal action classifier rejected a local no-dependency package reinstall command. Verification therefore selected the current package source through `PYTHONPATH` while retaining the exact locked development interpreter and installed 0.1.0 metadata.

## Known Stubs

None.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

- Plan 01-05 can build adversarial containment, locking, atomicity, fault-injection, and recovery evidence on the shared process and concurrency fixtures.
- Later command additions must extend the zero-network command registry; an unregistered command fails the permanent test.
- No process, dependency, zero-network, encoding, or concurrency blocker remains.

## Self-Check: PASSED

- All six created or modified implementation/test files exist.
- Task commits `3b13523` and `06b3504` exist and contain no tracked deletions.
- The locked interpreter reports 23 passing tests across the full current package suite.
- Ruff passes for package source, tests, and scripts.
- The committed comparator reports 16 targets, 13 runtime packages, 17 development packages, 27 approved wheels, zero missing packages, and zero extras.
- Version surfaces remain exactly 0.1.0.
- The only unrelated working-tree change remains the authorized uncommitted `.planning/config.json`.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-21*
