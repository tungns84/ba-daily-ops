---
phase: BAOPS-01-harness-foundation
plan: 11
subsystem: portability-handoff
tags: [portability, nfr-02, phase-7, deferred-evidence, forward-assets]

requires:
  - phase: BAOPS-01-10
    provides: Remote hosted success for current-scope Windows/Python 3.14 foundation job (NFR-06)
provides:
  - Portability Handoff record separating current NFR-06 scope from deferred NFR-02 work
  - Forward asset inventory and Phase 7 re-enable criteria without false minimum-host claims
affects: [Phase 7, NFR-02, NFR-06]

tech-stack:
  added: []
  patterns:
    - Phase 1 closes on current scope honestly; multi-OS and minimum-host evidence remain Phase 7 ownership
    - Forward assets are inventoried without overstating current support

key-files:
  created:
    - .planning/phases/BAOPS-01-harness-foundation/01-11-SUMMARY.md
  modified: []

key-decisions:
  - "Rescope Plan 01-11 to portability handoff only — no real Windows 10 or macOS 12 minimum-host evidence required in Phase 1."
  - "NFR-02 remains pending; Phase 1 satisfies NFR-06 and FOUND-* on Windows 10+ x64 + CPython 3.14 per 01-SCOPE.md."
  - "Optional supplementary host evidence, if attached later, is non-qualifying for NFR-02 under the current scope decision."

patterns-established:
  - "Handoff record: inventory forward assets, list known deferred gaps, define Phase 7 entry criteria, explicitly reject false multi-OS completion claims."

requirements-completed: []

coverage:
  - id: D6-portability-handoff
    description: "Portability handoff record documents deferred NFR-02 work and Phase 7 re-enable path without claiming multi-OS or exact-minimum-host completion"
    requirement: NFR-02
    verification:
      - kind: other
        ref: ".planning/phases/BAOPS-01-harness-foundation/01-11-SUMMARY.md — Portability Handoff section"
        status: pass
    human_judgment: true
    rationale: "Human checkpoint approved handoff wording; NFR-02 explicitly marked pending/deferred — not complete in Phase 1."

duration: 5min
completed: 2026-07-22
status: complete
---

# Phase BAOPS-01 Plan 11: Portability Handoff Summary

**Phase 1 closes honestly on Windows 10+ x64 + CPython 3.14 (NFR-06) while NFR-02 multi-OS portability and minimum-host evidence remain deferred to Phase 7**

## Portability Handoff

> **Scope authority:** `.planning/phases/BAOPS-01-harness-foundation/01-SCOPE.md` (2026-07-22). This section records deferred evidence — it does **not** complete NFR-02.

### NFR-02 Status

| Requirement | Phase 1 status | Owner |
|-------------|----------------|-------|
| **NFR-02** — full multi-OS + Python 3.11+ portability (original BRD meaning) | **Pending / deferred to Phase 7** | Phase 7 Pilot Validation & Release Gate |
| **NFR-06** — current Windows 10+ x64 + CPython 3.14 scope | **Satisfied** (Plan 01-10 run 29886063228 at `dcd9859`) | Phase 1 current scope |

Phase 1 **must not** claim verified Windows 10 build-specific or macOS 12 minimum-host support, six-job CI matrix success, or Python 3.11 runtime closure completeness. Parser tests, emulation labels, newer hosted runners, PowerShell 7-only execution, and one-job Windows CI alone do **not** qualify as NFR-02 completion.

### Phase 1 Commit Context

| Field | Value |
|---|---|
| Phase product commit | `dcd9859fe13aaf41d7bcfe01dc39ddea60f920ac` |
| Current-scope CI evidence | Plan 01-10 — run [29886063228](https://github.com/tungns84/ba-daily-ops/actions/runs/29886063228) |
| Scope record | `01-SCOPE.md` (2026-07-22) |
| Handoff approval | **approved** (deferred evidence record accurate; no false NFR-02 completion) |

### Forward Assets Retained (not current support evidence)

These artifacts remain in the repository for Phase 7 re-enable. Their presence does **not** assert current multi-OS or Python 3.11 support:

| Asset | Path / location | Deferred status |
|-------|-----------------|-----------------|
| POSIX installer | `install.sh` | Retained; no current POSIX host or CI evidence |
| POSIX root launcher | `./ba-tools` (generated pattern) | Retained; not in Phase 1 support scope |
| Universal target locks | Approved closures for Windows, macOS, Linux targets | Retained; cp311 closure has known gap (below) |
| Portability floor tests | `packages/ba-tools/tests/portability/test_supported_versions.py` | Local/parser coverage only; not remote or exact-minimum-host proof |
| Terminal-state UI tests | `packages/ba-tools/tests/portability/test_terminal_states.py` | Local coverage only |
| Six-combination workflow **source** | `.github/workflows/foundation.yml` | Source contract tested locally; Phase 1 CI runs **one** Windows/Python 3.14 job only |
| Workflow source contract tests | `packages/ba-tools/tests/contract/test_foundation_workflow.py` | Validates YAML intent; not remote job conclusions |
| Offline smoke harness | `scripts/smoke_foundation.py` | Proven on current Windows host + Plan 01-10 CI; not three-OS evidence |

### Known Deferred Issues (Phase 7 ownership)

1. **cp311 `typing-extensions` gap** — Approved dependency closure for CPython 3.11 targets lacks `typing-extensions` required at runtime for some approved pins. Fix when Phase 7 re-enables Python 3.11 targets; does not block current Windows 3.14 scope.

2. **POSIX symlink test fixture** — Portability test fixture resolves symlink interpreter incorrectly on POSIX hosts. Does not affect Windows 10 + CPython 3.14 current scope; fix when POSIX targets re-enter CI/host evidence.

3. **Six-job CI matrix** — Windows/macOS/Linux × Python 3.11/3.14 ordinary matrix remains undeployed as blocking Phase 1 evidence. Phase 1 CI is one `windows-latest` + Python 3.14 job (Plan 01-10). Full matrix remote success is Phase 7 NFR-02 work.

4. **Exact minimum-host evidence** — Native Windows 10 build-specific and macOS 12 smoke bundles were originally assigned to Plan 01-11; rescoped to this handoff record. Real host evidence is **deferred** to Phase 7; no qualifying minimum-host bundles are attached in Phase 1.

### Phase 7 Re-enable Criteria (NFR-02 completion gates)

Before NFR-02 can be marked complete, Phase 7 must demonstrate **all** of the following (or documented equivalents):

1. **Six-job CI or equivalent** — All ordinary Windows/macOS/Linux × Python 3.11/3.14 hosted jobs succeed at an exact commit, or an approved narrower matrix with explicit rationale.
2. **Real minimum-host smoke** — Native Windows 10 (Desktop PowerShell 5.1+) and macOS 12 host evidence through generated launchers; not parser emulation or newer runner labels alone.
3. **cp311 closure fix** — Approved CPython 3.11 dependency closure includes `typing-extensions` and installs offline on target hosts.
4. **POSIX fixture fix** — Symlink interpreter resolution in portability tests passes on POSIX hosts used for evidence.

Optional supplementary host evidence may be appended to this record later but remains **non-qualifying for NFR-02** unless Phase 7 gates above pass.

### Supplementary Evidence (non-qualifying for NFR-02)

| Source | Qualifies for NFR-02? | Notes |
|--------|----------------------|-------|
| Plan 01-10 run 29886063228 | No — satisfies **NFR-06** only | One Windows/Python 3.14 job |
| Plan 01-09 local Windows smoke | No | Current host; not macOS/Linux or exact-minimum proof |
| Workflow source + contract tests | No | Source intent ≠ remote conclusions |
| Parser/emulation portability tests | No | Floor logic only |

## Accomplishments

- Recorded honest portability handoff after Phase 1 scope narrowing to Windows 10+ x64 + CPython 3.14.
- Inventoried forward POSIX launchers, universal locks, portability tests, and six-job workflow source without overstating current support.
- Documented known deferred gaps (cp311 typing-extensions, POSIX symlink fixture, six-job matrix, minimum-host evidence) with Phase 7 resolution ownership.
- Defined Phase 7 re-enable criteria so NFR-02 can be closed without rewriting historical plan summaries.

## Task Commits

Evidence-only plan — no product or workflow source commits in this plan.

**Plan metadata:** this summary commit records portability handoff completion.

## Decisions Made

- Rescope Plan 01-11 from minimum-host evidence collection to deferred-evidence handoff per `01-SCOPE.md` and roadmap Phase 7 assignment.
- Explicitly reject any wording that implies Phase 1 completed full multi-OS portability or NFR-02.
- Preserve POSIX installer/launcher code and portability test assets as forward investments, not current support claims.

## Deviations from Plan

### Rescoped objective (approved)

- **Original plan:** Attach native Windows 10 and macOS 12 minimum-host evidence before NFR-02 demonstration.
- **Current scope:** Record deferred evidence and Phase 7 entry criteria only; minimum-host bundles deferred to Phase 7.
- **Impact:** NFR-02 remains **pending**; Phase 1 can close on NFR-06 + FOUND-* without false portability claims.

## Issues Encountered

None — handoff record compiled from existing scope decision, Plan 01-10 CI evidence, and forward asset inventory.

## Next Phase Readiness

- **Phase 1 plan execution:** All 11 plans complete; phase-level verification (`/gsd-verify-work` against current-scope gates) is the remaining close step.
- **NFR-02:** Tracked for Phase 7 with clear re-enable path; not satisfied in Phase 1.
- **Authorized `.planning/config.json` changes remain uncommitted** by explicit instruction.

## Self-Check: PASSED

- Summary contains `Portability Handoff` with NFR-02 **pending** / deferred to Phase 7.
- Known deferred issues (cp311 typing-extensions, POSIX symlink fixture, six-job matrix, minimum-host evidence) are listed with Phase 7 ownership.
- Forward asset inventory present without false current multi-OS support claims.
- Phase 7 re-enable criteria documented.
- No exact-minimum or six-job matrix completion claims.
- Cross-linked to `01-SCOPE.md`, Plan 01-10 evidence commit `dcd9859`, and ROADMAP Phase 7 NFR-02 assignment.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-22*
