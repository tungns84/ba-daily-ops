---
phase: BAOPS-01-harness-foundation
plan: 06
subsystem: state-initialization
tags: [python, jsonschema, draft-2020-12, repair, diagnostics, concurrency]

requires:
  - phase: BAOPS-01-04
    provides: Single-emission CLI, zero-network, and UTF-8 process contracts
  - phase: BAOPS-01-05
    provides: Contained paths, owner-aware workspace locking, atomic create, and quarantine
provides:
  - Three closed local Draft 2020-12 schemas for canonical workspace state
  - Mutation-free fresh, complete, partial, and invalid state classification
  - Explicit create-only init repair with complete deterministic diagnostics
  - Serialized init and repair transitions preserving invalid and existing canonical bytes
affects: [BAOPS-01-08, doctor, state-validation, workspace-repair]

tech-stack:
  added: []
  patterns:
    - All existing required files validate before transition selection or publication
    - Diagnostics sort by declared file order, JSON pointer, validator, and message
    - Repair publishes only missing packaged defaults through the existing create-only boundary

key-files:
  created:
    - packages/ba-tools/src/ba_tools/state/validation.py
    - packages/ba-tools/src/ba_tools/state/resources/schemas/config.schema.json
    - packages/ba-tools/src/ba_tools/state/resources/schemas/coverage-policy.schema.json
    - packages/ba-tools/src/ba_tools/state/resources/schemas/business-goals.schema.json
    - packages/ba-tools/tests/integration/test_init.py
    - packages/ba-tools/tests/unit/test_defaults.py
  modified:
    - packages/ba-tools/src/ba_tools/cli.py
    - packages/ba-tools/src/ba_tools/init_command.py

key-decisions:
  - "Load only allowlisted package schemas, self-check with Draft202012Validator, and reject non-local references before validation."
  - "Normalize unsupported schema versions into stable field-addressed const diagnostics inside one STATE_SCHEMA_INVALID envelope."
  - "Emit quarantine details only when evidence was quarantined, preserving the exact established fresh and no-op envelopes."

patterns-established:
  - "State transition: lock, quarantine, classify every present file, select one transition, create-only publish, then classify and read back under the same lock."
  - "Invalid-state contract: preserve canonical bytes and return every safe sorted diagnostic without inferred defaults or repair."

requirements-completed: [FOUND-04, FOUND-05, FOUND-06, NFR-04, NFR-05]

coverage:
  - id: D1
    description: "Three canonical defaults validate byte-exactly against closed, self-checked local Draft 2020-12 schemas"
    requirement: FOUND-04
    verification:
      - kind: unit
        ref: "packages/ba-tools/tests/unit/test_defaults.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fresh, complete, partial, malformed, schema-invalid, unsupported-version, duplicate, timeout, and concurrent states follow deterministic transitions"
    requirement: FOUND-04
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_init.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Schema-backed init and repair preserve containment, atomic publication, lock ownership, CLI stream, UTF-8, and zero-network contracts"
    requirement: FOUND-06
    verification:
      - kind: integration
        ref: ".ba-tools-runtime/dev/Scripts/python.exe -m pytest packages/ba-tools/tests -q -m 'not online_install' — 97 passed"
        status: pass
      - kind: other
        ref: ".ba-tools-runtime/dev/Scripts/python.exe -m ruff check packages/ba-tools/src packages/ba-tools/tests scripts — pass"
        status: pass
    human_judgment: false

duration: 19min
completed: 2026-07-21
status: complete
---

# Phase BAOPS-01 Plan 06: Schema-Backed Init and Repair Summary

**Closed local schemas now drive deterministic workspace classification, explicit create-only repair, complete stable diagnostics, and byte-preserving serialized transitions**

## Performance

- **Duration:** 19 min
- **Started:** 2026-07-21T16:19:42Z
- **Completed:** 2026-07-21T16:38:56Z
- **Tasks:** 3 completed
- **Files modified:** 8

## Accomplishments

- Added three closed, version-1 Draft 2020-12 package schemas with self-checking and remote-reference rejection.
- Classified every required target as fresh, complete, partial, or invalid without mutation and returned all diagnostics in stable declared order.
- Completed `init --repair` under the existing workspace lock so only missing files are create-only published while invalid and existing canonical bytes remain untouched.
- Preserved all prior CLI, containment, locking, atomicity, quarantine, UTF-8, and zero-network behavior across the 97-test package suite.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the RED schema-backed state-transition matrix** - `9df84a9` (test)
2. **Task 2: Implement closed local schemas and deterministic classification** - `adb0f72` (feat)
3. **Task 3: Complete locked init and explicit repair transitions** - `b82cc25` (feat)
4. **Task 3 compatibility fix: Preserve established empty init envelopes** - `ef979bc` (fix)

**Plan metadata:** committed with this summary and sequential tracking updates.

## Files Created/Modified

- `packages/ba-tools/src/ba_tools/state/validation.py` - Local schema loading, self-check, complete diagnostics, and mutation-free state classification.
- `packages/ba-tools/src/ba_tools/state/resources/schemas/config.schema.json` - Closed versioned profile schema.
- `packages/ba-tools/src/ba_tools/state/resources/schemas/coverage-policy.schema.json` - Closed versioned light-policy structure with per-REQ and waiver definitions.
- `packages/ba-tools/src/ba_tools/state/resources/schemas/business-goals.schema.json` - Closed versioned business-goal registry accepting an empty array.
- `packages/ba-tools/src/ba_tools/init_command.py` - Locked quarantine, classification, transition selection, repair publication, and read-back.
- `packages/ba-tools/src/ba_tools/cli.py` - Emission-free `init --repair` routing and conditional quarantine reporting.
- `packages/ba-tools/tests/integration/test_init.py` - D-11 through D-15 transition, preservation, duplicate, timeout, and concurrency matrix.
- `packages/ba-tools/tests/unit/test_defaults.py` - Exact default bytes, schema compatibility, empty goals, and local-reference tests.

## Decisions Made

- Schemas are loaded only by allowlisted package-resource names, checked explicitly as Draft 2020-12, and rejected if they contain non-fragment references.
- Parse and schema diagnostics contain only repo-relative path, JSON pointer, validator, and stable message fields.
- Empty quarantine results remain absent from the CLI data object to preserve Plan 01-03's exact fresh/no-op process bytes; non-empty quarantine evidence is reported deterministically.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed filesystem-enumeration ordering from the fresh-state assertion**
- **Found during:** Task 3 (Complete locked init and explicit repair transitions)
- **Issue:** The RED test compared `Path.rglob()` discovery order with declared target order even though filesystem enumeration is explicitly non-authoritative.
- **Fix:** Kept declared-order assertions on the returned `created` list and compared the discovered canonical file set without ordering.
- **Files modified:** `packages/ba-tools/tests/integration/test_init.py`
- **Verification:** Focused transition and filesystem gate passed 81 tests.
- **Committed in:** `b82cc25`

**2. [Rule 1 - Bug] Preserved the established exact empty init envelope**
- **Found during:** Overall full-package verification
- **Issue:** Always emitting `quarantined: []` changed the exact fresh and no-op bytes protected by the walking-skeleton contract.
- **Fix:** Emit deterministic quarantine records only when recovery evidence exists; fresh and no-op responses retain their established exact bytes.
- **Files modified:** `packages/ba-tools/src/ba_tools/cli.py`, `packages/ba-tools/tests/integration/test_init.py`
- **Verification:** Full package suite passed 97 tests and Ruff passed.
- **Committed in:** `ef979bc`

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes enforce deterministic ordering and backward compatibility without weakening prior tests or expanding schema/state-transition scope.

## Issues Encountered

- Context7 tooling was unavailable locally, so the exact installed `jsonschema==4.26.0` API behavior was checked against its official documentation before implementation.

## Known Stubs

None.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

- Plan 01-08 can use the classifier and stable diagnostics for ordered post-init doctor checks.
- Schema-backed init and repair are complete with no local test, lint, containment, locking, atomicity, UTF-8, or zero-network blocker.

## Self-Check: PASSED

- All eight created or modified implementation and test artifacts exist.
- Task commits `9df84a9`, `adb0f72`, `b82cc25`, and `ef979bc` exist with no tracked deletions.
- The focused init/default/contract/path/reliability gate passed 81 tests.
- The full locked-interpreter package suite passed 97 tests with current source selected through normalized `PYTHONPATH`.
- Ruff passed across package source, tests, and scripts.
- Stub scan found no production placeholder, TODO, FIXME, coming-soon, or unavailable markers.
- The authorized `.planning/config.json` change remains uncommitted.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-21*
