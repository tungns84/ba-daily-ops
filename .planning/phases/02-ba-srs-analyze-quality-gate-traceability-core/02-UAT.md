---
status: complete
phase: 02-ba-srs-analyze-quality-gate-traceability-core
source: [02-VERIFICATION.md]
started: 2026-06-18T09:30:00Z
updated: 2026-06-18T10:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. ba-srs-analyze full route end-to-end
expected: |
  Running the `full` route on a clean grounded source produces requirements.json,
  SRS.md, a trace record, and an updated INDEX.md. `ba-tools verify` exits 0.
  ba-critic receives ONLY {source_path, requirements_json_path} (no analysis.md),
  and the CoVe loop converges; trace write + index update execute on convergence.
result: pass
evidence: |
  Executed the `full` route end-to-end in an isolated scratch repo-root (agent
  acting as the ba-srs-writer/ba-critic runtime, which is the v1 operator design):
  - resolve-route ba-srs-analyze → {"ok":true,"default_route":"full"}
  - init ba-srs-analyze → scaffolded .ba-ops/ incl traces/
  - writer → .ba-ops/srs/demo/requirements.json + analysis.md (writer notes)
  - render srs --slug demo → SRS.md (exit 0)
  - verify --reqs-format json --source source.md → {"ok":true,"checked":5} exit 0
  - ba-critic ran in a FRESH subagent with ONLY {source_path, requirements_json_path}
    (analysis.md + SRS.md withheld — independence contract D-21/G3 honored)
  - on convergence: trace write (srs-demo.json, 5 req_ids) + index update both exit 0
  Note: convergence occurred after one revision ("passed after 2"), not loop-1
  early-exit — see Test 2. This is the full revision loop working, a stronger
  result than a trivial early-exit.

### 2. CoVe convergence vocabulary + ba-critic independence
expected: |
  STATE.md convergence vocabulary is exercised; ba-critic independence confirmed
  (no analysis.md/SRS.md in the critic payload); Gate 3 (trace+index) runs only on
  convergence; gap/orphan/stale detection works against a fixture.
result: pass
evidence: |
  - Loop 1 (fresh critic, paths only): returned converged=false with two fail
    findings the deterministic verify gate structurally cannot catch — NFR-001
    ungrounded (empty span + "delivery pipeline" paraphrase of source's "CI/CD
    pipeline"; verify skipped it as status=derived) and a MISSING coverage gap
    ("Each requirement must reference the originating section..."). This is the
    independent critic catching what verify misses — the reason CoVe exists.
  - Writer re-draft folded both fails (FR-004 grounded verbatim + FR-005 added);
    verify re-ran → {"ok":true,"checked":5} exit 0.
  - Loop 2 (fresh critic, no memory of loop 1): converged=true (one non-blocking
    warn on FR-004 classification). Convergence rule honored (converged iff zero
    fail-severity findings).
  - STATE.md logged the convergence verdict: `note: passed after 2` (via
    `state advance`), status=converged, last_action=cove-gate.
  - Gate 3 ran ONLY after convergence (trace write + index update).
  - INDEX matrix transitions all exercised live: gap (SRS-only, no downstream) →
    ok (FR-001 once a mermaid trace covered it) → orphan (FR-999 cited by the
    mermaid trace but absent from the SRS registry) → stale (all req_ids after the
    source hash changed; both srs-demo + mermaid-demo traces flagged stale).
  - Independence confirmed: critic was handed only the two payload paths; the
    writer's analysis.md was never in the critic payload.

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
