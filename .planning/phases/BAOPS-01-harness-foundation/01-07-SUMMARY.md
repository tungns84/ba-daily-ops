---
phase: BAOPS-01-harness-foundation
plan: 07
subsystem: project-local-installer
tags: [python, powershell-5.1, posix-sh, pip, launchers, concurrency]

requires:
  - phase: BAOPS-01-01
    provides: Human-approved exact binary-only dependency closure and artifact hashes
  - phase: BAOPS-01-04
    provides: Exact-version CLI, zero-network runtime, and UTF-8 process contracts
provides:
  - Exact ba-tools 0.1.0 project-local generation installation from the approved hash lock
  - Invocation-scoped online consent and approved zero-network offline installation
  - Repository-root PowerShell 5.1 and POSIX launchers with contained pointer validation
  - Verified idempotent and serialized activation that never exposes an unverified generation
affects: [BAOPS-01-08, BAOPS-01-09, BAOPS-01-10, BAOPS-01-11, installer, portability]

tech-stack:
  added: []
  patterns:
    - Thin host wrappers delegate package work to one shared Python bootstrap
    - Exact generation identity binds package version, lock digest, Python family, OS, architecture, and format
    - Candidate generations are verified before and during serialized atomic activation
    - Runtime launchers consume one allowlisted generation component and remain zero-network

key-files:
  created:
    - install.ps1
    - install.sh
    - installer/bootstrap.py
    - installer/launcher-templates/ba-tools
    - installer/launcher-templates/ba-tools.ps1
    - packages/ba-tools/tests/integration/test_installer.py
  modified:
    - .gitignore
    - .gitattributes

key-decisions:
  - "Keep network consent invocation-scoped and bypass the prompt only for explicit --yes or an approved offline wheelhouse."
  - "Represent active state as one allowlisted generation component and construct the interpreter only beneath .ba-tools-runtime/envs."
  - "Build unique candidates, verify every 0.1.0 surface, then reverify under the install lock before atomic pointer and launcher publication."
  - "Preserve NFR-02 remote evidence boundaries: this plan proves the current Windows host and portable source behavior, while Plans 01-09 through 01-11 own native POSIX CI and exact-minimum-host evidence."

patterns-established:
  - "Installer boundary: dependency network access exists only in the consented bootstrap; generated launchers call local ba_tools directly."
  - "Idempotency: an exact verified active generation preserves pointer and launcher mtimes and skips dependency installation."
  - "Launcher fallback: one compact LAUNCHER_NOT_READY JSON document on stderr with exit code 2 and no absolute path disclosure."

requirements-completed: [FOUND-03, NFR-02, NFR-03, NFR-04]

coverage:
  - id: D1
    description: "Exact ba-tools 0.1.0 generations bind the approved lock and activate only after metadata, module, CLI version, and help verification"
    requirement: FOUND-03
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_installer.py — 20 passed"
        status: pass
    human_judgment: false
  - id: D2
    description: "Stock Windows PowerShell Desktop 5.1 and optional PowerShell 7 execute the installer without requiring pwsh or policy changes"
    requirement: NFR-02
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_installer.py::test_windows_powershell_51_install_path"
        status: pass
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_installer.py::test_powershell7_remains_compatible"
        status: pass
    human_judgment: false
  - id: D3
    description: "POSIX sh installer and launcher preserve quoted path and argument behavior with LF source bytes"
    requirement: NFR-02
    verification:
      - kind: integration
        ref: "packages/ba-tools/tests/integration/test_installer.py::test_posix_wrapper_is_quoted_posix_sh"
        status: pass
    human_judgment: true
    rationale: "POSIX syntax and portable launcher behavior passed on the current Windows host, but a native macOS or Linux installation is intentionally deferred to remote evidence plans."
  - id: D4
    description: "Installer additions preserve every established CLI, state, containment, locking, atomicity, zero-network, and UTF-8 contract"
    requirement: NFR-03
    verification:
      - kind: integration
        ref: ".ba-tools-runtime/dev/Scripts/python.exe -m pytest packages/ba-tools/tests -q -m 'not online_install' — 117 passed"
        status: pass
      - kind: other
        ref: ".ba-tools-runtime/dev/Scripts/python.exe -m ruff check packages/ba-tools/src packages/ba-tools/tests installer scripts — pass"
        status: pass
    human_judgment: false

duration: 63min
completed: 2026-07-21
status: complete
---

# Phase BAOPS-01 Plan 07: Exact-Version Local Installer and Launchers Summary

**Exact ba-tools 0.1.0 generations now install from the approved hash lock and launch transparently through contained PowerShell 5.1 and POSIX repository-root adapters**

## Performance

- **Duration:** 63 min
- **Started:** 2026-07-21T16:52:39Z
- **Completed:** 2026-07-21T17:55:09Z
- **Tasks:** 2 completed
- **Files modified:** 8

## Accomplishments

- Added thin Windows PowerShell 5.1 and POSIX sh installers that discover compatible Python and Git without installing prerequisites or changing user/system state.
- Added one Python bootstrap that enforces default-No consent, approved offline-only arguments, exact hash-lock installation, four-surface 0.1.0 verification, unique candidates, idempotent reuse, and serialized atomic activation.
- Added transparent repository-root launchers that validate one contained generation component, force Python UTF-8 mode, preserve child streams and exit status, and fail with one safe `LAUNCHER_NOT_READY` envelope.
- Added 20 installer integration cases covering consent, exact identity, Windows host compatibility, POSIX syntax, Unicode/space paths, rollback, pointer injection, idempotency, and concurrent activation.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write RED installer, PowerShell 5.1, version, and launcher contracts** - `b47ab67` (test)
2. **Task 2: Implement verified exact-version generations and transparent launchers** - `8405a2b` (feat)

**Plan metadata:** committed with this summary and sequential tracking updates.

## Files Created/Modified

- `.gitignore` - Root-anchored generated launcher, runtime, lock, quarantine, cache, and build exclusions.
- `.gitattributes` - LF policy for Python, POSIX shell, launcher template, JSON, and schema text.
- `install.ps1` - Windows PowerShell 5.1-compatible script-root prerequisite discovery and argument-array delegation.
- `install.sh` - Quoted POSIX sh prerequisite discovery and bootstrap delegation.
- `installer/bootstrap.py` - Consent, exact generation identity, secure pip arguments, verification, idempotency, locking, and atomic activation.
- `installer/launcher-templates/ba-tools` - Transparent POSIX contained launcher.
- `installer/launcher-templates/ba-tools.ps1` - Transparent Windows PowerShell 5.1 contained launcher.
- `packages/ba-tools/tests/integration/test_installer.py` - Complete installer, host, launcher, version, mutation, rollback, and concurrency contract.

## Decisions Made

- Kept package approval and network consent separate: only `--yes` or an approved `--offline` wheelhouse authorizes dependency access for the current invocation.
- Used unique generation directories so a failed or concurrent build cannot damage the active environment; activation occurs only after exact identity and version verification.
- Reverified the candidate while holding `.ba-tools-runtime/install.lock`, then atomically published the one-component pointer and both root launchers.
- Preserved evidence boundaries: actual Windows PowerShell Desktop 5.1 and PowerShell 7 ran locally; POSIX source behavior was syntax/integration tested but not represented as a native POSIX-host execution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected GREEN-test fixture assumptions without weakening contracts**
- **Found during:** Task 2 (Implement verified exact-version generations and transparent launchers)
- **Issue:** Initial fixtures omitted candidate identity bytes and copied templates, assumed same-volume hard links, treated redirected PowerShell input as a Python TTY, and matched a candidate only by its pre-activation path.
- **Fix:** Added exact candidate markers and portable fixture copies, propagated invocation-scoped noninteractive state from wrappers, used a copied test interpreter with explicit development site packages, and asserted moved concurrent generations by allowlisted component identity.
- **Files modified:** `install.ps1`, `install.sh`, `installer/bootstrap.py`, `packages/ba-tools/tests/integration/test_installer.py`
- **Verification:** Focused installer suite passes 20 cases under the locked interpreter, including real Windows PowerShell Desktop 5.1 and PowerShell 7 execution.
- **Committed in:** `8405a2b`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The fixes make the planned cross-platform and concurrency evidence non-vacuous; no package, version, network, or architecture scope changed.

## Issues Encountered

- The first package-wide verification selected the older installed `ba_tools` package because the development environment does not automatically prioritize current source. Re-running with the established normalized `PYTHONPATH=packages/ba-tools/src` contract passed all 117 tests.

## Known Stubs

None.

## Threat Flags

None. The dependency-install, pointer, shell, consent, and supply-chain surfaces are all declared in the plan threat model and covered by the installer suite.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

- Plan 01-08 can inspect the generated exact-version environment and launcher state in ordered doctor diagnostics.
- Plans 01-09 and 01-10 remain responsible for successful native Windows/macOS/Linux CI installer evidence.
- Plan 01-11 remains responsible for exact Windows 10 and macOS 12 host evidence; this plan does not claim unavailable operating-system execution.
- NFR-02 therefore remains pending in `REQUIREMENTS.md` until the named remote and exact-minimum-host evidence plans complete.

## Self-Check: PASSED

- All eight created or modified plan artifacts exist.
- Task commits `b47ab67` and `8405a2b` exist and contain no tracked deletions.
- The focused installer suite passed 20 cases through the locked development interpreter.
- The full current-source package suite passed 117 cases, and Ruff passed across package source, tests, installer, and scripts.
- Stub scan found no production placeholder, TODO, FIXME, coming-soon, or unavailable implementation.
- No unplanned threat surface or machine-specific committed path was found.
- The authorized `.planning/config.json` change remains uncommitted.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-21*
