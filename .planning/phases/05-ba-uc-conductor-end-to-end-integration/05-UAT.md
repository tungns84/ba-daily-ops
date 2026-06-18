---
status: testing
phase: 05-ba-uc-conductor-end-to-end-integration
source: [05-VERIFICATION.md]
started: 2026-06-18T20:05:00Z
updated: 2026-06-18T20:05:00Z
---

## Current Test

number: 1
name: Full E2E Delivery Run — ba-uc deliver against uc-001-test.md fixture
expected: |
  Conductor opens ba-srs-analyze.md (full route) → D-G1 Quality gate passes →
  STATE.md srs-analyze=complete → ba-mermaid.md at `## Route: full` → D-G2 passes →
  mermaid=complete → ba-mockup.md → D-G2 passes → mockup=complete →
  `ba-tools index update` → index=complete → `ba-tools uc-status` next_step=done;
  INDEX.md reflects trace records from all three artifacts.
awaiting: user response

## Tests

### 1. Full E2E Delivery Run
expected: Invoke `ba-uc deliver` on the uc-001-test.md fixture with --fidelity html. Conductor runs srs-analyze full → D-G1 gate → mermaid full (explicit route, not default author) → D-G2 gate → mockup full → D-G2 gate → index update. STATE.md pipeline steps advance to srs-analyze=complete, mermaid=complete, mockup=complete, index=complete. INDEX.md reflects all three trace records. `ba-tools uc-status` returns next_step=done.
result: [pending]

### 2. Gate Reject (D-RES1): D-G1 Hard Stop
expected: Introduce a source document that causes srs-analyze full route to emit non-convergence-escalation after 3 CoVe iterations. Conductor writes pipeline_step=srs-analyze pipeline_status=failed to STATE.md, then STOPS. mermaid/mockup/index rows remain pending. `ba-tools uc-status` returns next_step=srs-analyze.
result: [pending]

### 3. Resume Re-Entry (D-RES2)
expected: With pipeline state mermaid=failed (srs-analyze=complete, mermaid=failed, mockup=pending, index=pending), invoke `ba-uc resume`. Conductor runs uc-status, gets next_step=mermaid, re-enters deliver at Step 2 (not Step 1), runs mermaid → D-G2 → mockup → D-G2 → index, completes to next_step=done.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
