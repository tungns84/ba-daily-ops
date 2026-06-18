---
phase: 03-ba-mermaid-diagram-operator
plan: "02"
subsystem: ba-mermaid-skill
tags: [skill, workflow, agent, mermaid, traceability, tdd]
status: complete

dependency_graph:
  requires:
    - 03-01 (mermaid-render command — render route consumes it)
  provides:
    - ba-mermaid Codex skill (discovery + openai.yaml)
    - ba-mermaid workflow (author/render/full routes)
    - ba-diagrammer agent role contract
    - author-route no-CLI proof tests (criterion 1)
  affects:
    - .agents/skills/ (new ba-mermaid skill)
    - .agents/ba-daily-operators/ba-core/workflows/ (new ba-mermaid workflow)
    - .agents/ba-daily-operators/ba-core/agents/ (new ba-diagrammer prompt)

tech_stack:
  added: []
  patterns:
    - "Codex skill contract: SKILL.md name+description frontmatter only"
    - "openai.yaml nesting: interface.* + policy.allow_implicit_invocation"
    - "Workflow route sections: ## Route: author/render/full"
    - "determinism boundary: agent authors, ba-tools CLI-only"
    - "D-06 drift detection: --source-doc = requirements.json (not diagram .md)"
    - "TDD: fixture-based proof test for author-route CLI-free invariant"

key_files:
  created:
    - .agents/skills/ba-mermaid/SKILL.md
    - .agents/skills/ba-mermaid/agents/openai.yaml
    - .agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md
    - .agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md
    - .agents/ba-daily-operators/ba-tools/tests/test_mermaid_author.py
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/mermaid/authored_diagram.md
  modified: []

decisions:
  - "D-06 applied: full route --source-doc = .ba-ops/srs/<slug>/requirements.json so source_hash tracks the depicted SRS state, not the diagram artifact itself"
  - "Codex skill contract: SKILL.md frontmatter contains only name + description (no other keys); body is HTML comment pointing to workflow"
  - "openai.yaml nesting: allow_implicit_invocation under policy: (not flat) — corrects DESIGN §3 description"
  - "Author route is strictly no-CLI; render route is opt-in only and never auto-invoked by author or full"
  - "req_ids discipline: agent selects depicted subset from requirements.json; never invents IDs; orphans surface via index update"

metrics:
  duration: "~25 minutes (session split across context boundary)"
  completed: "2026-06-18"
  tasks_completed: 3
  tasks_total: 3
  files_created: 6
  files_modified: 0

requirements: [MMD-01]
---

# Phase 03 Plan 02: ba-mermaid Skill + Workflow + Agent Summary

**One-liner:** ba-mermaid Codex skill with author/render/full routes, ba-diagrammer role contract, req_ids traceability hand-off, and author-route no-CLI proof test (ROADMAP criterion 1).

---

## What Was Built

Six files create the agent-owned half of the ba-mermaid operator:

| File | Purpose |
|------|---------|
| `.agents/skills/ba-mermaid/SKILL.md` | Codex skill discovery index (name + keyword-dense description) |
| `.agents/skills/ba-mermaid/agents/openai.yaml` | Skill config: interface.* + policy.allow_implicit_invocation: false |
| `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` | Thin workflow: author/render/full route steps with determinism-boundary block |
| `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md` | Diagram-author agent role contract: type selection table + req_ids discipline |
| `tests/test_mermaid_author.py` | TDD proof: author fixture has inline fence + req_ids; author section has no render CLI |
| `tests/fixtures/mermaid/authored_diagram.md` | Fixture representing ba-diagrammer author-route output |

### Route design

- **author** (default): agent writes `.ba-ops/mermaid/<slug>/diagram.md` (inline mermaid fence + req_ids frontmatter). No CLI invoked. No trace write.
- **full**: author → `trace write --kind mermaid` (with `--source-doc .ba-ops/srs/<slug>/requirements.json`) → `index update`.
- **render**: opt-in `ba-tools mermaid-render`; hard-fails exit 2 when mmdc absent; never auto-invoked by author or full.

---

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | ba-mermaid skill + openai.yaml | 951952a | SKILL.md, openai.yaml |
| 2 | ba-mermaid workflow + ba-diagrammer | a5e66e3 | ba-mermaid.md, ba-diagrammer.md |
| 3 | TDD author-route proof test + fixture | 1017c33 | test_mermaid_author.py, authored_diagram.md |

---

## Verification Results

All tests green:

| Test module | Tests | Result |
|-------------|-------|--------|
| `test_skill_schema.py` | 5/5 | PASSED (ba-mermaid added to skill suite) |
| `test_workflow_contract.py` | 5/5 | PASSED (existing contracts unaffected) |
| `test_mermaid_author.py` | 2/2 | PASSED (author-route criterion 1 proof) |

Byte budget check — all 4 skill/workflow/agent files under 32,768 bytes:

| File | Size |
|------|------|
| SKILL.md | 682 B |
| openai.yaml | 958 B |
| ba-mermaid.md | 3,405 B |
| ba-diagrammer.md | 3,194 B |

---

## Decisions Made

1. **D-06 semantics for `--source-doc`:** The full route passes `--source-doc .ba-ops/srs/<slug>/requirements.json` (the depicted SRS), not the diagram `.md` itself. This records `source_hash` = SHA-256 of the SRS state when the diagram was authored, enabling drift detection when requirements change post-diagram.

2. **SKILL.md body = HTML comment only:** No prose body in the skill index — body is a single HTML comment pointing at the workflow file. Codex skill discovery reads only the frontmatter; the body avoids inflating the eager-load budget.

3. **openai.yaml nesting fix:** `allow_implicit_invocation: false` nested under `policy:` (not flat), correcting DESIGN §3 description where the field appeared at the top level.

4. **Author route strict no-CLI invariant:** The `## Route: author` section contains zero CLI invocations. The TDD test `test_author_route_invokes_no_render_cli` mechanically enforces this by slicing the section and asserting `mermaid-render` and `mmdc` are absent — making the invariant regression-proof.

5. **req_ids discipline encoded in agent prompt:** The ba-diagrammer is explicitly instructed to read all IDs from `requirements.json`, select the depicted subset, and never invent IDs. Invented IDs are flagged downstream as orphans by `index update` (D-05 detection).

---

## Deviations from Plan

None. Plan executed exactly as written.

- All 3 tasks completed in order.
- SKILL.md frontmatter contains exactly `{name, description}` — no extra keys.
- openai.yaml nesting matches confirmed Codex contract (CLAUDE.md verified patterns).
- Full route `--source-doc` = requirements.json per Pattern 3 in RESEARCH.md.
- TDD cycle: fixture created first (GREEN prerequisite), tests written, both passed on first run.

---

## TDD Gate Compliance

Plan type is `execute` with `tdd="true"` on Task 3 only (not a full TDD plan). Task 3 followed the TDD cycle:

- **GREEN**: fixture `authored_diagram.md` created before test; tests written against it; both passed 2/2 on first pytest run.
- No RED phase artificially forced (fixture is the "implementation" — the test validates fixture + workflow contract rather than code under test). This is correct for a structural proof test.

---

## Known Stubs

None. All files are fully wired:
- Workflow routes reference real ba-tools commands (resolve-route, init, trace write, index update, mermaid-render).
- ba-diagrammer output path `.ba-ops/mermaid/<slug>/diagram.md` is concrete.
- Test fixture contains real mermaid syntax, real frontmatter values.

---

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries introduced.

Threat T-03-07 mitigated: `test_author_route_invokes_no_render_cli` proves the author route section is mermaid-render/mmdc-free.

---

## Self-Check: PASSED

Files exist:
- `.agents/skills/ba-mermaid/SKILL.md` — FOUND
- `.agents/skills/ba-mermaid/agents/openai.yaml` — FOUND
- `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` — FOUND
- `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md` — FOUND
- `tests/test_mermaid_author.py` — FOUND
- `tests/fixtures/mermaid/authored_diagram.md` — FOUND

Commits verified: 951952a, a5e66e3, 1017c33 — all in git log.
