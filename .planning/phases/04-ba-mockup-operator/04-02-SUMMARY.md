---
phase: 04-ba-mockup-operator
plan: "02"
subsystem: operator
tags: [ba-mockup, workflow, agent-prompt, skill, codex, fidelity, html, wireframe, traceability]

requires:
  - phase: 04-ba-mockup-operator
    plan: "01"
    provides: "test_mockup_author.py (6 tests including 2 RED workflow-inspection gates), test_mockup_trace_index.py (6 tests), 3 fixtures"

provides:
  - ".agents/ba-daily-operators/ba-core/workflows/ba-mockup.md — thin orchestrator with screen/full routes, fidelity gate"
  - ".agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md — author role contract with fidelity-branched output schema"
  - ".agents/skills/ba-mockup/SKILL.md — CDX skill discovery index (name+description only)"
  - ".agents/skills/ba-mockup/agents/openai.yaml — Codex skill metadata (interface.* + policy.allow_implicit_invocation: false)"

affects: [04-03-ba-mockup-cli]

tech-stack:
  added: []
  patterns:
    - "ba-mockup operator mirrors ba-mermaid structure: thin workflow + author role + skill discovery files, no new ba-tools commands"
    - "Fidelity gate at workflow layer (D-05a): hard-reject before authoring — workflow-enforced, not ba-tools-enforced"
    - "Fidelity-branched req_ids carrier: HTML comment first line (.html), YAML frontmatter (.md)"
    - "CDX skill contract: SKILL.md frontmatter = name+description only; openai.yaml interface.* + policy.allow_implicit_invocation: false nested under policy:"

key-files:
  created:
    - ".agents/ba-daily-operators/ba-core/workflows/ba-mockup.md"
    - ".agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md"
    - ".agents/skills/ba-mockup/SKILL.md"
    - ".agents/skills/ba-mockup/agents/openai.yaml"
  modified: []

key-decisions:
  - "Fidelity gate in workflow step 2 of screen route — hard-reject with explicit error message before any authoring (D-05a / T-4-01 mitigation)"
  - "--source-doc for trace write --kind mockup = requirements.json (SRS file, not the mockup artifact) — matches ba-mermaid pattern, pins source_hash to SRS for drift detection (D-06)"
  - "ba-mockup-author.md names script and box-drawing in do-NOT-use rules — these references in the prompt are correct and do not trip artifact-level test gates (tests scan authored artifacts, not the prompt file)"
  - "allow_implicit_invocation: false nested under policy: top-level key (CDX-02 mandatory nesting per CLAUDE.md)"

patterns-established:
  - "ba-mockup operator: SKILL.md + openai.yaml in .agents/skills/ba-mockup/, workflow in ba-core/workflows/, agent in ba-core/agents/"
  - "Fidelity-branched route body pattern: screen route steps 1-6 (validate fidelity before authoring), full route references screen route then adds extract/trace/index steps"

requirements-completed: [MOCK-01, MOCK-02, MOCK-03]

duration: ~5min
completed: 2026-06-18
status: complete
---

# Phase 4 Plan 02: ba-mockup Operator (Workflow + Agent + Skill) Summary

**ba-mockup operator files created: thin workflow with fidelity gate + screen/full routes, author role contract with fidelity-branched output schema, and CDX skill discovery files; all 17 plan-scoped tests green, zero ba_tools/ files touched**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-18T09:25:07Z
- **Completed:** 2026-06-18T09:30:00Z
- **Tasks:** 3 of 3
- **Files created:** 4

## Accomplishments

- Created `ba-mockup.md` workflow: operator frontmatter (ba-mockup / full / screen+full routes), preamble (determinism boundary / sequential execution / pass-paths-not-content), screen route with fidelity gate (step 2 hard-rejects missing/invalid before authoring), full route (author → extract req_ids by fidelity → trace write --kind mockup → index update), no render route and zero mmdc/drawio tokens anywhere
- Created `ba-mockup-author.md` agent role: fidelity-branched output schema (html = req_ids comment absolute first line + self-contained HTML5 with inline CSS + no script/no external src; wireframe = YAML frontmatter + headings+lists+tables + no ASCII box-drawing), req_ids discipline (never invent, focused subset, honor explicit --req-ids), dropped mermaid-specific sections
- Created `ba-mockup/SKILL.md`: name+description only (no extra frontmatter keys), description covers html/wireframe fidelity, req_ids traceability, routes, trigger phrases, workflow comment pointing to ba-mockup.md
- Created `ba-mockup/agents/openai.yaml`: interface.display_name BA Mockup, interface.default_prompt with full route + fidelity step + workflow/agent paths, policy.allow_implicit_invocation: false nested under policy:
- Plan 01 RED gates (test_screen_route_invokes_no_render_cli, test_workflow_rejects_missing_fidelity) now green — 2 previously failing tests now pass
- Full test suite: 17 tests green (6 test_mockup_author + 6 test_mockup_trace_index + 5 test_skill_schema)

## Task Commits

1. **Task 1: ba-mockup thin workflow** - `a5395a8` (feat)
2. **Task 2: ba-mockup-author agent role contract** - `45ea273` (feat)
3. **Task 3: ba-mockup skill discovery files** - `f3ede1a` (feat)

## Files Created/Modified

- `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` — thin orchestrator: frontmatter operator/default_route/routes, preamble, screen route (fidelity gate step 2), full route (4 steps: author/extract/trace/index)
- `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` — author role: inputs payload (fidelity+screen_name), fidelity-branched output (html: first-line comment + HTML5 skeleton; wireframe: YAML frontmatter + structural markdown), req_ids discipline
- `.agents/skills/ba-mockup/SKILL.md` — CDX skill index: name+description only (CDX contract)
- `.agents/skills/ba-mockup/agents/openai.yaml` — skill metadata: interface.* + policy.allow_implicit_invocation: false

## Decisions Made

- Fidelity gate placed in screen route step 2 (before ba-tools init, before authoring) — ensures no CLI calls are made for invalid input (D-05a, T-4-01 mitigation)
- `--source-doc` for `trace write --kind mockup` explicitly documented as `requirements.json` (not the mockup artifact) — identical semantics to ba-mermaid, pins source_hash to SRS version at authoring time
- The `ba-mockup-author.md` prompt file names `<script>` and `+--` box-drawing in prohibition rules — tests scan the authored artifacts (authored_html.html, authored_wireframe.md), not the prompt file, so these references are correct and expected
- `policy.allow_implicit_invocation: false` nested under `policy:` (not flat) — CDX-02 mandatory nesting confirmed in CLAUDE.md

## Deviations from Plan

None — plan executed exactly as written. All 4 files created per spec. 17 tests green. Zero ba_tools/ files touched (`git status --porcelain .agents/ba-daily-operators/ba-tools/ba_tools/` is empty).

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes beyond what the plan's threat model documents. All four STRIDE mitigations (T-4-01 through T-4-05) realized:

- T-4-01 (fidelity tampering): workflow screen route step 2 hard-rejects before authoring
- T-4-02 (agent invents REQ-IDs): ba-mockup-author.md carries explicit "Do NOT invent REQ-IDs" rule
- T-4-04 (script injection): ba-mockup-author.md HTML rules forbid `<script>` and external src
- T-4-05 (auto-invocation): policy.allow_implicit_invocation: false in openai.yaml

## Self-Check: PASSED

All 4 created files verified on disk:
- `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` — FOUND
- `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` — FOUND
- `.agents/skills/ba-mockup/SKILL.md` — FOUND
- `.agents/skills/ba-mockup/agents/openai.yaml` — FOUND

All 3 task commits verified in git log: a5395a8, 45ea273, f3ede1a
