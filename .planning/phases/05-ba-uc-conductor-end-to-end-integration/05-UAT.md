---
status: complete
phase: 05-ba-uc-conductor-end-to-end-integration
source: [05-VERIFICATION.md]
started: 2026-06-18T20:05:00Z
updated: 2026-06-18T20:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Full E2E Delivery Run
expected: Invoke `ba-uc deliver` on the uc-001-test.md fixture with --fidelity html. Conductor runs srs-analyze full → D-G1 gate → mermaid full (explicit route, not default author) → D-G2 gate → mockup full → D-G2 gate → index update. STATE.md pipeline steps advance to srs-analyze=complete, mermaid=complete, mockup=complete, index=complete. INDEX.md reflects all three trace records. `ba-tools uc-status` returns next_step=done.
result: pass
evidence: |
  Live conductor run against docs/uc-001-test.md (isolated --repo-root scratch). Sequence executed via real ba-tools CLI:
  - resolve-route ba-uc → default_route=deliver
  - init ba-uc → scaffold seeded all 4 pipeline rows pending; uc-status next_step=srs-analyze
  - Step 1 srs-analyze: verify (D-G1) ok:true, 3 checked, 0 findings → trace write srs (FR-001,FR-002,NFR-001) → state patch srs-analyze=complete → next_step=mermaid
  - Step 2 mermaid (full): trace write mermaid → index update gaps=[] orphans=[] stale=[] (D-G2 PASS) → state patch mermaid=complete → next_step=mockup
  - Step 3 mockup (full, fidelity=html): trace write mockup → index update gaps=[] orphans=[] (D-G2 PASS) → state patch mockup=complete
  - Step 4 index: canonical rebuild → state patch index=complete
  - FINAL uc-status: all four steps complete, next_step=done
  - INDEX.md Matrix: FR-001/FR-002/NFR-001 all status=ok; Gaps (none); Orphans (none); Stale (none) — full REQ-ID traceability across SRS→Mermaid→Mockup.

### 2. Gate Reject (D-RES1): D-G1 Hard Stop
expected: Introduce a source document that causes srs-analyze full route to emit non-convergence-escalation after 3 CoVe iterations. Conductor writes pipeline_step=srs-analyze pipeline_status=failed to STATE.md, then STOPS. mermaid/mockup/index rows remain pending. `ba-tools uc-status` returns next_step=srs-analyze.
result: pass
evidence: |
  Live run with an ungrounded `stated` requirement (span absent from source). D-G1 verify returned ok:false CITATION_NOT_FOUND (exit 2) — models a CoVe loop that never converges → non-convergence-escalation. Conductor patched srs-analyze=failed and STOPPED.
  - uc-status: srs-analyze=failed, mermaid=pending, mockup=pending, index=pending, next_step=srs-analyze
  - 0 trace files written; no .ba-ops/diagrams or .ba-ops/mockups dirs created — conductor did not fall through to Step 2. STOP invariant honored.

### 3. Resume Re-Entry (D-RES2)
expected: With pipeline state mermaid=failed (srs-analyze=complete, mermaid=failed, mockup=pending, index=pending), invoke `ba-uc resume`. Conductor runs uc-status, gets next_step=mermaid, re-enters deliver at Step 2 (not Step 1), runs mermaid → D-G2 → mockup → D-G2 → index, completes to next_step=done.
result: pass
evidence: |
  Staged state srs-analyze=complete, mermaid=failed, mockup=pending, index=pending (srs trace present from a prior complete run). Resume route:
  - uc-status → next_step=mermaid (re-entry point; NOT srs-analyze)
  - Conductor re-entered at Step 2: mermaid trace → index (D-G2 clean) → mermaid=complete; mockup trace → index (D-G2 clean) → mockup=complete; final index → index=complete
  - FINAL uc-status: all complete, next_step=done
  - srs trace file mtime UNCHANGED across the resume → srs-analyze was NOT re-executed. Resume re-entered at next_step, not from the start (D-RES2 confirmed).

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

(none)
