---
status: testing
phase: 02-ba-srs-analyze-quality-gate-traceability-core
source: [02-VERIFICATION.md]
started: 2026-06-18T09:30:00Z
updated: 2026-06-18T09:30:00Z
---

## Current Test

number: 1
name: ba-srs-analyze full route end-to-end with early convergence
expected: |
  Operator is discoverable; route resolves to `full`; ba-srs-writer produces
  requirements.json; `ba-tools verify` exits 0; ba-critic runs in fresh context
  (only {source_path, requirements_json_path} — no analysis.md); CoVe converges
  on loop 1; STATE.md logs "passed early"; trace write + index update execute;
  final INDEX.md shows ok status for the slug.
awaiting: user response

## Tests

### 1. ba-srs-analyze full route end-to-end (early convergence)
expected: |
  Running the `full` route on a clean grounded source produces requirements.json,
  SRS.md, a trace record, and an updated INDEX.md. `ba-tools verify` exits 0.
  ba-critic receives ONLY {source_path, requirements_json_path} (no analysis.md),
  returns converged=true on loop 1, and STATE.md logs "passed early".
result: [pending]

### 2. CoVe convergence vocabulary + ba-critic independence
expected: |
  STATE.md convergence vocabulary is exercised: "passed early" for loop-1
  convergence (and "passed after N" path / "non-convergence-escalation" path are
  reachable per gates.md + ba-critic.md). ba-critic independence confirmed by the
  absence of analysis.md / SRS.md in the critic payload. Gate 3 (trace+index) runs
  only on convergence.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
