---
phase: 05-ba-uc-conductor-end-to-end-integration
plan: "02"
subsystem: ba-core/references
tags: [gate-contract, safety-gate, documentation, GATE-03]
requires: []
provides: [GATE-03-contract]
affects: [ba-make-diagram, ba-uc-delivery]
tech_stack:
  added: []
  patterns: [append-only gate section, prohibition table]
key_files:
  modified:
    - .agents/ba-daily-operators/ba-core/references/gates.md
decisions:
  - "Extend gates.md (single canonical gate reference) rather than create a sibling safety-gate.md — keeps all gate contracts co-located; aligns with RESEARCH Q5 recommendation"
  - "Four clauses: Clause 1 render-CLI-only, Clause 2 path-traversal+injection, Clause 3 media-extension, Clause 4 hash-manifest (PLUG-04 deferred) — exact wording from RESEARCH Q5"
  - "Scope marker: spine invokes no render CLI, conductor never fires Safety gate — explicitly stated in both the Scope block and the prohibition table"
  - "Phase-5 status line added: enforcement deferred to PLUG-01..04 plugin implementations"
metrics:
  duration: "8 minutes"
  completed: "2026-06-18"
  tasks_completed: 1
  tasks_total: 1
  files_changed: 1
status: complete
requirements: [GATE-03]
---

# Phase 05 Plan 02: Safety Gate Contract (GATE-03) Summary

## One-liner

GATE-03 Safety Gate Contract appended to gates.md — four clauses (render-CLI-only, path-traversal+injection scan, media extension check, hash manifest deferred) scoped plugin-enforced/spine-exempt, under the 32,768 B eager-ref budget.

## What Was Built

Extended `.agents/ba-daily-operators/ba-core/references/gates.md` with the GATE-03 Safety Gate Contract section. This is a documentation-only plan (zero new ba-tools commands, zero new files, zero installs) that defines the authoritative safety contract the deferred plugins (`ba-make-diagram`, `ba-uc-delivery`) must enforce.

### Section structure appended

- `## Safety Gate Contract` — heading with Scope block and Phase-5 status marker
- `### Clause 1 — Render CLI only` — draw.io/mmdc mandatory; Pillow/SVG-converter/screenshot forbidden (DESIGN §6, §11)
- `### Clause 2 — Path-traversal and injection scan` — `resolve_under_root` + `is_within_root` + `ba-tools scan` (TOOL-15, advisory)
- `### Clause 3 — Media extension check` — `.png`/`.svg` (`.pdf` export-only); reject other extensions at write time
- `### Clause 4 — Hash manifest (PLUG-04, deferred)` — `{rendered_sha256, embedded_sha256}` manifest; enforced when PLUG-04 ships
- `## Safety Gate — Prohibition summary` — four-row table matching existing Quality-gate prohibition table format

## Verification Results

| Check | Result |
|-------|--------|
| `grep -c "Safety Gate Contract"` | 1 (present) |
| `os.path.getsize(gates.md) < 32768` | PASS — 7,488 B |
| Append-only diff | PASS — 0 lines deleted, 67 inserted |
| Existing Gate 1/2/3 + escalation + WARN intact | PASS |
| Scope text states spine fires no render | PASS |
| Prohibition table has 4 rows | PASS |

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1: Append Safety Gate Contract | bc41b9f | feat(05-02): append GATE-03 Safety Gate Contract to gates.md |

## Deviations from Plan

None — plan executed exactly as written. Single append-only edit to gates.md following the PATTERNS.md section heading + clause format + prohibition table format pattern.

## Known Stubs

None. This is a documentation-only plan; no data sources or stub implementations are involved.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. This plan only extends a reference documentation file. The threat model in the plan (T-05-04, T-05-05, T-05-06, T-05-SC) is fully addressed by the contract text itself — mitigations are documented as clauses (Clause 1, 2, 3) and deferred manifest check (Clause 4/PLUG-04). T-05-SC (accept) is correctly scoped: zero installs, zero new dependencies.

## Self-Check: PASSED

- [x] `.agents/ba-daily-operators/ba-core/references/gates.md` exists and is modified
- [x] Commit `bc41b9f` exists in git log
- [x] gates.md byte size 7,488 B < 32,768 B budget
- [x] `Safety Gate Contract` heading present (grep count = 1)
- [x] All four clauses present
- [x] Prohibition table present with four rows
- [x] Existing Quality-gate sections (Gate 1/2/3, escalation, WARN, Prohibition summary) unchanged
