---
phase: BAOPS-01-harness-foundation
status: active
supersedes_support_claims_from: "2026-07-22"
created: 2026-07-22
---

# Phase 1 — Current Support Scope

> **Authoritative scope record.** This document supersedes prior support claims in completed plan summaries (`01-01`…`01-09`) by dated annotation and evidence linkage. Historical SUMMARY bodies are not rewritten; readers should treat this file as the current truth for release scope.

## Current Support (Phase 1 release target)

| Dimension | Supported now |
|-----------|---------------|
| **Operating system** | Windows 10+ x64 |
| **Python** | CPython 3.14 (exact pinned version per approved lock) |
| **Installer path** | PowerShell Desktop 5.1+ via `install.ps1` / `ba-tools.ps1` |
| **CI evidence** | One `windows-latest` job with Python 3.14 (Plan 01-10) |
| **Requirement** | **NFR-06** — current Windows + Python 3.14 scope |

## Deferred to Phase 7 (portability completion)

The following remain **forward assets** (code, locks, tests, launchers) but are **not current support evidence**:

| Item | Notes |
|------|-------|
| **Python 3.11** | Approved closure exists; known gap: `typing-extensions` missing in cp311 approved closure (defer fix to Phase 7 re-enable) |
| **macOS 12+** | POSIX launcher and locks retained; no current host or CI evidence |
| **Linux (manylinux x64)** | POSIX implementation retained; no current host or CI evidence |
| **Six-job CI matrix** | Windows/macOS/Linux × Python 3.11/3.14 — deferred; Phase 1 CI is one Windows/Python 3.14 job |
| **Exact minimum-host evidence** | Windows 10 build-specific and macOS 12 smoke bundles — deferred to Plan 01-11 handoff / Phase 7 |
| **Requirement** | **NFR-02** — full multi-OS + Python 3.11+ portability (original BRD meaning preserved) |

## Known Deferred Issues (do not block current scope)

1. **cp311 `typing-extensions` gap** — Approved dependency closure for CPython 3.11 targets lacks `typing-extensions` required at runtime for some approved pins. Fix when Phase 7 re-enables 3.11 targets; not in current Windows 3.14 scope.

2. **POSIX symlink test fixture** — Portability test fixture resolves symlink interpreter incorrectly on POSIX hosts. Does not affect Windows 10 + CPython 3.14 current scope; fix when POSIX targets re-enter CI/host evidence (Phase 7).

## Evidence Ownership

| Claim | Owner plan | Gate type |
|-------|------------|-----------|
| Workflow source + local suite | 01-09 | Automated (local) |
| One Windows/Python 3.14 CI run | 01-10 | External (GitHub Actions) |
| Multi-OS / 3.11 / minimum-host portability | 01-11 → Phase 7 | Deferred handoff — **does not complete NFR-02** |

## Supersedes (by reference, not rewrite)

Completed summaries through Plan 01-09 may state multi-OS, six-job CI, or Python 3.11+ as phase goals. As of **2026-07-22**, those claims apply to **deferred Phase 7 work** unless this scope record explicitly lists them under **Current Support**.

**Linked evidence:** `.planning/ROADMAP.md` (Phase 1 success criteria), `.planning/REQUIREMENTS.md` (NFR-06 / NFR-02 mapping), `.planning/phases/BAOPS-01-harness-foundation/01-VALIDATION.md` (current vs deferred gates).

---
*Scope decision recorded: 2026-07-22*
