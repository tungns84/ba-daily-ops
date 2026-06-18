---
phase: 05-ba-uc-conductor-end-to-end-integration
plan: "03"
subsystem: ba-core/workflows + ba-core/agents + ba-tools/tests
tags: [conductor, workflow, skill, openai-yaml, test, CDX-02, D-G1, D-G2, GATE-03]
requires:
  - phase: 05-ba-uc-conductor-end-to-end-integration
    provides: [integration test suite (05-01), GATE-03 Safety Gate Contract (05-02)]
provides:
  - ba-uc CDX skill discovery (SKILL.md + openai.yaml)
  - ba-uc conductor workflow (ba-uc.md) with 4 routes
  - ba-uc-conductor agent prompt
  - 5 static workflow-contract tests (test_uc_conductor_workflow.py)
affects: [ba-make-diagram, ba-uc-delivery, phase-06-future]
tech-stack:
  added: []
  patterns:
    - conductor-reads-sub-workflow-inline (D-INV)
    - pipeline-status-write-via-state-patch
    - index-integrity-gate-from-json-output (D-G2)
    - explicit-full-route-mermaid (not default author)
key-files:
  created:
    - .agents/skills/ba-uc/SKILL.md
    - .agents/skills/ba-uc/agents/openai.yaml
    - .agents/ba-daily-operators/ba-core/workflows/ba-uc.md
    - .agents/ba-daily-operators/ba-core/agents/ba-uc-conductor.md
    - .agents/ba-daily-operators/ba-tools/tests/test_uc_conductor_workflow.py
  modified: []
key-decisions:
  - "ba-mermaid default route is 'author' — conductor must explicitly drive 'full' route (trace+index not in author); validated by test_deliver_route_drives_mermaid_full_not_author"
  - "D-G2 covered_by NOT emitted by index update JSON; self-coverage predicate uses step_trace_req_ids vs gaps list (RESEARCH Q2 workable resolution)"
  - "GATE-03 spine-exempt rule surfaced in both ba-uc-conductor.md (determinism boundary) and test_no_render_cli_invoked_on_spine assertion"
  - "Task sequencing: test file created first (needed for Task 1+2 verification runs), then workflow+agent, then three atomic commits in order"
  - "Byte budgets: SKILL.md 1,060 B < 32,768 B; ba-uc.md 8,134 B < 38,000 B; ba-uc-conductor.md 3,356 B < 38,000 B"
requirements-completed: [UC-01, UC-02, UC-03]
duration: ~35min
completed: "2026-06-18"
status: complete
---

# Phase 05 Plan 03: ba-uc Conductor Operator Summary

**ba-uc CDX skill + 4-route conductor workflow (deliver/resume/status/iterate): srs-analyze(full) → mermaid(full, explicit not default author) → mockup(full) → index; D-G1 Quality gate + D-G2 index-integrity gate; 5-test static contract suite green across full 300+ test suite**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-06-18T19:16:55Z
- **Completed:** 2026-06-18
- **Tasks:** 3
- **Files created:** 5

## Accomplishments

- CDX-compliant ba-uc skill discovery pair: SKILL.md (name+description only) + openai.yaml (interface+policy nesting, allow_implicit_invocation: false CDX-02)
- ba-uc.md conductor workflow: 4 routes; deliver route drives srs-analyze `full` → mermaid `full` (explicit, not default author) → mockup `full` → final index update; D-G1 Quality gate after srs; D-G2 index-integrity gate (orphans + step req_ids vs gaps) after mermaid+mockup; pipeline_status written via `ba-tools state patch`
- ba-uc-conductor.md agent prompt: slug threading rule, gate verdict discipline, mermaid route discipline, fidelity forwarding, status semantics, GATE-03 spine-exempt
- 5 static tests in test_uc_conductor_workflow.py: frontmatter schema, CDX constraint, policy nesting, mermaid full explicit, no render CLI on spine
- Full suite: 300+ tests pass (0 failures)

## Task Commits

1. **Task 1: CDX skill files** - `1b661c8` (feat)
2. **Task 2: Workflow + agent prompt** - `bdaa1e2` (feat)
3. **Task 3: Workflow-contract tests** - `75bf629` (test)

## Files Created/Modified

- `.agents/skills/ba-uc/SKILL.md` — CDX skill index: name=ba-uc, description (block scalar `>`), workflow pointer comment
- `.agents/skills/ba-uc/agents/openai.yaml` — CDX contract: interface block (display_name "BA UC Conductor", short_description, 4-step default_prompt) + policy block (allow_implicit_invocation: false)
- `.agents/ba-daily-operators/ba-core/workflows/ba-uc.md` — 4-route conductor workflow (8,134 B < 38,000 B budget)
- `.agents/ba-daily-operators/ba-core/agents/ba-uc-conductor.md` — agent prompt: 6 conductor-specific rules
- `.agents/ba-daily-operators/ba-tools/tests/test_uc_conductor_workflow.py` — 5 static contract tests

## Decisions Made

1. **ba-mermaid full route explicit** — Default is `author` (skips trace+index). Conductor must navigate to `## Route: full` explicitly. Validated by RESEARCH Q1 MISMATCH FLAG and enforced by test assertion (500-char proximity check for "full" near ba-mermaid.md reference + NOT-the-default marker).

2. **D-G2 covered_by gap workaround** — `index update` JSON does NOT emit `covered_by` dict. Self-coverage predicate uses: `any(rid in gaps for rid in step_trace_req_ids)`. Step captures req_ids it passed to trace write; checks none appear in `gaps` after index update. No new ba-tools command needed.

3. **GATE-03 spine-exempt** — Conductor never fires Safety gate; determinism boundary paragraph in ba-uc-conductor.md explicitly states no render CLI. Static test `test_no_render_cli_invoked_on_spine` asserts no mmdc/draw.io invocation patterns in ba-uc.md.

4. **Step-4 index update** — Final standalone `ba-tools index update` after mockup is idempotent full-rebuild (index_cmd.py confirms). Mermaid+mockup full routes each already run index update; the conductor's Step 4 is the canonical end-state rebuild ensuring consistency across all three trace writes.

5. **Task sequencing** — Test file (Task 3) created before Tasks 1 and 2 were committed, so verification test runs could work. Three atomic commits made in order: Task 1 → Task 2 → Task 3.

## Deviations from Plan

None — plan executed exactly as written. The pre-planned RESEARCH Q1 MISMATCH FLAG (mermaid default=author) was already accounted for in plan must_haves and PATTERNS.md adapt instructions. Test file creation sequencing was a process optimization (test first so verification works), not a plan deviation.

## Known Stubs

None. All workflow files are authoritative contracts referencing real ba-tools CLI surface. No placeholder text or TODO markers.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. Five new files are workflow/config/test only:
- SKILL.md + openai.yaml: static config, no code execution
- ba-uc.md + ba-uc-conductor.md: workflow documentation, no runtime code
- test_uc_conductor_workflow.py: read-only file assertions, no network, no external writes

Threat model items T-05-07 through T-05-10 and T-05-SC are addressed by:
- T-05-07/08 (slug/fidelity injection): conductor workflow validates both inputs at Step 0 pre-flight
- T-05-09 (pipeline state clobber): addressed by FileLock pattern (05-01 tests)
- T-05-10 (mermaid route mismatch): mitigated by explicit `## Route: full` instruction + test assertion
- T-05-SC (GATE-03 scope): spine-exempt stated in conductor prompt + test assertion

## Self-Check: PASSED

- [x] `.agents/skills/ba-uc/SKILL.md` exists (1,060 B < 32,768 B)
- [x] `.agents/skills/ba-uc/agents/openai.yaml` exists (policy.allow_implicit_invocation: false)
- [x] `.agents/ba-daily-operators/ba-core/workflows/ba-uc.md` exists (8,134 B < 38,000 B)
- [x] `.agents/ba-daily-operators/ba-core/agents/ba-uc-conductor.md` exists
- [x] `.agents/ba-daily-operators/ba-tools/tests/test_uc_conductor_workflow.py` exists
- [x] Commit 1b661c8 exists (Task 1)
- [x] Commit bdaa1e2 exists (Task 2)
- [x] Commit 75bf629 exists (Task 3)
- [x] Full test suite: 300+ tests pass, 0 failures
- [x] All 5 new tests pass
- [x] Byte budgets within limits
