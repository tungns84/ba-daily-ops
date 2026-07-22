---
phase: BAOPS-01-harness-foundation
plan: 10
subsystem: foundation-ci-evidence
tags: [github-actions, remote-evidence, windows, python-3.14, nfr-06]

requires:
  - phase: BAOPS-01-09
    provides: Least-privilege foundation workflow source and local offline smoke contracts
provides:
  - Remote hosted success for the single current-scope Windows/Python 3.14 foundation job
  - Foundation CI Run Evidence bound to exact commit, run URL, job identity, and required steps
affects: [BAOPS-01-11, NFR-02, NFR-06]

tech-stack:
  added: []
  patterns:
    - Remote CI conclusions are recorded separately from workflow source and local pytest success
    - Current-scope evidence is one windows-latest + Python 3.14 job; multi-OS and Python 3.11 matrix remain deferred

key-files:
  created:
    - .planning/phases/BAOPS-01-harness-foundation/01-10-SUMMARY.md
  modified: []

key-decisions:
  - "Treat run 29886063228 at headSha dcd9859 as the blocking NFR-06 remote evidence for Phase 1 current scope only."
  - "Do not infer six-job, macOS, Linux, or Python 3.11 success from this single-job run; NFR-02 remains Phase 7 scope per 01-SCOPE.md."

patterns-established:
  - "Evidence record: bind run ID, URL, event, branch, headSha, workflow blob hash, job name, step conclusions, and redacted host shell facts."

requirements-completed: [NFR-06]

coverage:
  - id: D5-remote-current-scope
    description: "The ordinary foundation workflow succeeded remotely for windows-latest + Python 3.14 at the phase commit"
    requirement: NFR-06
    verification:
      - kind: other
        ref: "https://github.com/tungns84/ba-daily-ops/actions/runs/29886063228 — job windows / Python 3.14 success"
        status: pass
    human_judgment: true
    rationale: "Human checkpoint verified gh run metadata, step names, and log excerpts for Ruff, full non-online pytest, and offline smoke."

duration: 2min
completed: 2026-07-22
status: complete
---

# Phase BAOPS-01 Plan 10: Remote Foundation CI Evidence Summary

**Hosted GitHub Actions now proves the current-scope Windows/Python 3.14 foundation job passed at commit `dcd9859`, without claiming multi-OS or six-job matrix success**

## Foundation CI Run Evidence

| Field | Value |
|---|---|
| Run ID | 29886063228 |
| Run URL | https://github.com/tungns84/ba-daily-ops/actions/runs/29886063228 |
| Workflow | `foundation` |
| Event | `push` |
| Branch | `baops-harness-foundation` |
| Head SHA | `dcd9859fe13aaf41d7bcfe01dc39ddea60f920ac` |
| Workflow blob (`.github/workflows/foundation.yml` at head SHA) | `c8f84c6703636c3d6b766c05ef61b8084bf4b083` |
| Started (UTC) | 2026-07-22T02:31:50Z |
| Completed (UTC) | 2026-07-22T02:33:20Z |
| Overall conclusion | **success** |
| Required job | `windows / Python 3.14` — **success** |
| Job URL | https://github.com/tungns84/ba-daily-ops/actions/runs/29886063228/job/88816740113 |
| Approval | **approved** (run matches phase commit; required steps succeeded) |

### Required job steps (all success)

1. **Acquire approved wheels on Windows** — locked dev/runtime wheelhouse download only.
2. **Run locked quality gates on Windows** — `ruff check` (All checks passed); pytest non-online suite (**168 passed**).
3. **Run offline smoke with Windows PowerShell** — workflow uses `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.EXE`; step asserts `PSEdition=Desktop` and version ≥ 5.1 via `powershell.exe`; runs `scripts/smoke_foundation.py` with local wheelhouse and generated launchers.
4. **Upload redacted source evidence** — artifact upload after smoke.

Workflow permissions at run start: **Contents: read** (read-only token scope).

### Scope narrowing (not claimed by this plan)

Per `01-SCOPE.md` and Plan 01-09 boundaries, this evidence **does not** demonstrate:

- macOS or Linux hosted jobs
- Python 3.11 matrix rows
- A full six-combination ordinary matrix (NFR-02 — deferred to Phase 7)
- Native exact-minimum Windows 10 or macOS 12 hosts (Plan 01-11)

## Accomplishments

- Verified the `foundation` workflow run on remote `tungns84/ba-daily-ops` for the exact pushed Phase 1 commit.
- Recorded single-job success with lint, full locked suite, offline smoke, and evidence upload — not YAML or local-only proof.
- Preserved honest compatibility boundaries: current platform remote success (NFR-06) is satisfied; broader matrix and exact-minimum OS evidence remain open.

## Task Commits

Evidence-only plan — no product or workflow source commits in this plan.

**Plan metadata:** this summary commit records remote CI evidence completion.

## Decisions Made

- Bind NFR-06 remote proof to run **29886063228** and head SHA **dcd9859** only; stale, pending, or other-commit runs are rejected.
- Windows PowerShell Desktop 5.1+ requirement is satisfied by workflow shell selection and explicit pre-smoke checks in job logs, not by `pwsh`-only execution.

## Deviations from Plan

None.

## Issues Encountered

None — run completed successfully on first inspection after push.

## Next Phase Readiness

- **Plan 01-11** should attach native exact-minimum host evidence (Windows 10 + Desktop PowerShell 5.1, macOS 12) before NFR-02 can be fully demonstrated.
- **Phase 7 / NFR-02** remains responsible for multi-OS and six-job matrix remote success if still in roadmap scope.
- Authorized `.planning/config.json` changes remain **uncommitted** by explicit instruction.

## Self-Check: PASSED

- Run URL and head SHA match the pushed evidence commit `dcd9859fe13aaf41d7bcfe01dc39ddea60f920ac`.
- Exactly one required matrix job (`windows / Python 3.14`) concluded success with Ruff, 168 pytest passes, and offline smoke step success.
- Summary contains no secrets or absolute runner home paths.
- Multi-OS / six-job matrix success is explicitly deferred.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-22*
