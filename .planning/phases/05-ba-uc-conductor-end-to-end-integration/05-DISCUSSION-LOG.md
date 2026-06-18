# Phase 5: ba-uc Conductor + End-to-End Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-18
**Phase:** 5-ba-uc Conductor + End-to-End Integration
**Areas discussed:** Per-step gate semantics, Step invocation + routes + slug threading, Resume / fail-stop / kill-recovery, Integration test + GATE-03 Safety contract

---

## Per-step gate semantics

### Q1 — What gate runs after mermaid/mockup steps?

| Option | Description | Selected |
|--------|-------------|----------|
| Index-integrity check | `index update` + assert no new orphan & step's req_ids landed in INDEX column; reuses existing machinery | ✓ |
| Full verify+ba-critic every step | Re-run verify+ba-critic after mermaid/mockup; needs new agent contracts; heavier, off determinism boundary | |
| No gate after mermaid/mockup | Quality gate only after srs (matches DESIGN §2); contradicts ROADMAP "after each step" | |

**User's choice:** Index-integrity check (Recommended) → **D-G1**
**Notes:** Reconciles DESIGN §2 ("gate after srs-analyze") with ROADMAP criterion 1 ("after each step") — non-SRS steps get the strongest *applicable* provable check.

### Q2 — What condition FAILs the index-integrity gate?

| Option | Description | Selected |
|--------|-------------|----------|
| Orphan OR missing self-coverage | FAIL on orphan introduced OR step's req_ids absent from its INDEX column; gaps in other columns ignored | ✓ |
| Orphan only | FAIL only on bad REQ-ID; don't assert self-coverage; looser | |
| You decide | Let planner pick within "orphan=always fail, gap=never fail mid-pipeline" | |

**User's choice:** Orphan OR missing self-coverage (Recommended) → **D-G2**
**Notes:** Gaps are expected mid-pipeline (mockup column empty until mockup step), so a gap can never be a stop condition.

---

## Step invocation + routes + slug threading

### Q1 — How does the conductor run each spine operator?

| Option | Description | Selected |
|--------|-------------|----------|
| Read sub-workflow, drive specific routes | Conductor reads each sub-workflow inline, runs sequentially, owns only gate+state between steps | ✓ |
| Drive every op's `full` route uniformly | srs/mermaid/mockup all `full` + per-step gate + final index update; redundant but idempotent | |
| You decide | Capture principle; planner picks exact route per step | |

**User's choice:** Read sub-workflow, drive specific routes (Recommended) → **D-INV**
**Notes:** Codex v1 — one sequential agent loop, no subagent spawn; independence by instruction.

### Q2 — Input contract + slug/fidelity threading?

| Option | Description | Selected |
|--------|-------------|----------|
| --uc spec; srs derives slug; --fidelity flag on ba-uc | srs runs first → derives slug → threaded to mermaid/mockup/index; --fidelity required, forwarded to mockup | ✓ |
| --slug required up front | Caller passes --slug; forced on every step; bypasses srs's own derivation | |
| You decide | Principle: one shared slug from srs step; --fidelity reaches mockup | |

**User's choice:** --uc spec; srs derives slug; --fidelity flag on ba-uc (Recommended) → **D-IN**

---

## Resume / fail-stop / kill-recovery

### Q1 — How is a failed/killed step's status recorded?

| Option | Description | Selected |
|--------|-------------|----------|
| Mark complete only after gate passes; else non-complete | `complete` after gate pass; FAIL→`failed`; kill→pending; next_step lands on it | ✓ |
| Only 'complete' vs 'pending' (no 'failed') | Never mark complete on fail; loses failed-vs-never-reached signal | |
| You decide | Principle: complete strictly after gate; let planner pick status string + reason surface | |

**User's choice:** Mark complete only after gate passes; else non-complete (Recommended) → **D-RES1**

### Q2 — Resume entry point + the missing `index` pipeline row?

| Option | Description | Selected |
|--------|-------------|----------|
| Resume re-runs next_step fully; conductor ensures all 4 rows exist | Resume re-runs first non-complete step from scratch then proceeds; guarantee `index` row exists (closes WR-02) | ✓ |
| Resume continues AFTER next_step | Treats next_step as attempted; risks skipping a failed step; contradicts criterion 2 | |
| You decide | Principle: resume re-runs first non-complete step; `index` must be representable | |

**User's choice:** Resume re-runs next_step fully; conductor ensures all 4 rows exist (Recommended) → **D-RES2, D-RES3**
**Notes:** Scaffold seeds only srs-analyze/mermaid/mockup rows, not `index`; `pipeline_step` silently no-ops when row absent (tech-debt WR-02). Planner picks fix: patch scaffold.py vs conductor self-seed.

---

## Integration test + GATE-03 Safety contract

### Q1 — pytest vs agent-UAT split?

| Option | Description | Selected |
|--------|-------------|----------|
| pytest the ba-tools spine state-machine + agent UAT for the full run | Deterministic pytest: state/uc-status/resume/gate-reject/concurrent-write/index integrity; agent loop = UAT | ✓ |
| Full automated E2E only | Script whole conductor incl. agent steps; non-deterministic; heavy mocking doesn't prove real loop | |
| You decide | Principle: hash/state-provable → pytest; agent loop → UAT | |

**User's choice:** pytest the ba-tools spine state-machine + agent UAT for the full run (Recommended) → **D-TEST**

### Q2 — Where does the GATE-03 Safety contract live?

| Option | Description | Selected |
|--------|-------------|----------|
| New Safety section in references/ (gates.md or sibling) | Standalone discoverable contract; render-CLI-only, path/injection scan, .png/.svg, plugin-enforced/spine-exempt | ✓ |
| Inline in the ba-uc workflow only | Buries a cross-cutting plugin contract in conductor-specific file | |
| You decide | Principle: standalone discoverable doc per DESIGN §6, plugin-enforced | |

**User's choice:** New Safety section in references/ (Recommended) → **D-SAFE**

---

## Claude's Discretion

- Exact route driven per spine step inside `deliver` (within D-INV).
- Whether the conductor needs any new ba-tools surface (expected: none).
- The `iterate` route body for the conductor.
- The `failed` status string + how the failure reason surfaces.
- WR-02 fix mechanism (scaffold.py seed vs conductor self-seed).
- GATE-03 doc location (extend gates.md vs new safety-gate.md) + wording.
- Conductor workflow byte budget / LARGE-tier extraction.
- `openai.yaml` `interface.*` wording + SKILL.md `description`.
- Integration test fixture design.

## Deferred Ideas

- Actual Safety-gate enforcement (lives in deferred plugins; GATE-03 is contract-only here).
- True fresh-context subagent spawn (v2 Claude/Task; V2-02).
- Multi-UC batch delivery (v1 = one UC per `deliver`).
- Promoting the index-integrity gate to a ba-tools `gate` command.
- A `--diagram-type` surface on the conductor.
