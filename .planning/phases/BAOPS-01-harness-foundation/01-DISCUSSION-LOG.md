# Phase 1: Harness Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-20
**Phase:** 1-Harness Foundation
**Areas discussed:** Installer and PATH, Doctor policy, Init and re-init behavior, Locking and recovery

---

## Installer and PATH

| Decision | Options considered | Selected |
|----------|--------------------|----------|
| Installation scope | Per-user without admin; project-local; system-wide; Claude decides | Project-local |
| Invocation | Repo-root launcher; activate environment then call `ba-tools`; add repo `.venv` to user `PATH` | Repo-root launcher |
| Missing prerequisites | Fail with guidance; auto-install system prerequisites; fully offline bundle; Claude decides | Fail early with actionable guidance |
| Version policy | Exact per-repo pin; always latest; compatible range; Claude decides | Exact per-repo pin |

**User's choices:** Install into each repository; invoke through `.\ba-tools.ps1` or `./ba-tools` without activation or persistent `PATH` changes; do not auto-install Python/Git; require consent before dependency downloads; synchronize exact locked versions and make upgrades explicit.

**Notes:** The repo-local launcher intentionally refines the roadmap's literal “on PATH” wording. Acceptance tests should verify direct execution from the repository root instead of testing persistent `PATH` modification.

---

## Doctor Policy

| Decision | Options considered | Selected |
|----------|--------------------|----------|
| Dependency severity | Core fail/plugin warning; every missing dependency fails; informational only; Claude decides | Core fail/plugin warning |
| Default scope | Core plus active profile/plugins; all known dependencies; core only; Claude decides | Core plus active profile/plugins |
| Before initialization | Automatic pre/post-init modes; require init first; host checks only; Claude decides | Automatic pre/post-init modes |
| Behavior after failure | Continue independent checks; fail-fast; run all checks despite dependencies; Claude decides | Continue independent checks |

**User's choices:** Core failures return exit 2; inactive plugin dependencies are warnings. Default checks follow current configuration, while `doctor --all` checks optional tooling. Pre-init validates host/repo; post-init also validates file-state. Independent checks continue and blocked dependents are reported as skipped.

**Notes:** The exact check identifiers and JSON envelope remain implementation details.

---

## Init and Re-init Behavior

| Decision | Options considered | Selected |
|----------|--------------------|----------|
| Existing valid state | Idempotent no-op; fail; regenerate defaults; Claude decides | Idempotent no-op |
| Missing required files | Fail and recommend `init --repair`; auto-add; require delete/re-init; Claude decides | Explicit repair |
| Existing invalid file | Preserve and fail; back up and replace; replace automatically; Claude decides | Preserve and fail |
| Default content | Minimal valid state; interactive questions; sample data; Claude decides | Minimal valid state |

**User's choices:** Valid re-init returns success with `changed: false`. Plain init does not silently repair partial state. `init --repair` only creates missing files and never replaces existing invalid files. Defaults are `profile: light`, the standard light policy, and an empty valid business-goals registry.

**Notes:** No business data may be inferred or seeded during deterministic initialization.

---

## Locking and Recovery

| Decision | Options considered | Selected |
|----------|--------------------|----------|
| Active lock contention | Bounded wait then fail; immediate failure; indefinite wait; Claude decides | Bounded wait then fail |
| Stale lock recovery | Auto-recover only when proven stale; always require explicit recovery; delete by age; Claude decides | Recover only when proven stale |
| Orphan atomic-write temp | Keep canonical and quarantine temp; delete temp; complete pending write; Claude decides | Keep canonical and quarantine temp |
| Lock scope | One workspace write lock; per-file locks; resource-group locks; Claude decides | One workspace write lock |

**User's choices:** Writers wait for a finite timeout and then return structured retry guidance. Stale locks may be removed automatically only when the owner is conclusively gone. Crash remnants are quarantined and never promoted automatically. All v1 `.ba-ops/` mutations share one workspace lock.

**Notes:** Exact timeout, stale threshold/proof, metadata format, and quarantine paths are left to planning.

---

## Claude's Discretion

The user did not select “Claude decides” for any discussed decision. Downstream agents retain freedom only over lower-level details that preserve the locked behavior in `01-CONTEXT.md`.

## Deferred Ideas

None.
