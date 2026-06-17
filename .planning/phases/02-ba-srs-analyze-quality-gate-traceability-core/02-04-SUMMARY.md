---
phase: 02-ba-srs-analyze-quality-gate-traceability-core
plan: "04"
subsystem: ba-srs-analyze operator skill
tags: [codex-skill, workflow, operator, ba-critic, cove, quality-gate, traceability]
dependency_graph:
  requires: [02-01, 02-02, 02-03]
  provides: [ba-srs-analyze-skill, ba-srs-analyze-workflow, ba-critic-cove-loop, quality-gate-contract]
  affects: [phase-03-mermaid, phase-04-mockup, phase-05-uc-conductor]
tech_stack:
  added: []
  patterns:
    - CoVe (Chain-of-Verification) loop <=3 with ba-critic independence contract
    - YAML frontmatter + Markdown body pinned workflow format
    - Codex skill SKILL.md frontmatter (name+description only)
    - agents/openai.yaml interface/policy nesting contract
    - F11 fixture pattern (planted WRITER_RATIONALE_MARKER for independence gate test)
key_files:
  created:
    - .agents/skills/ba-srs-analyze/SKILL.md
    - .agents/skills/ba-srs-analyze/agents/openai.yaml
    - .agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md
    - .agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md
    - .agents/ba-daily-operators/ba-core/agents/ba-critic.md
    - .agents/ba-daily-operators/ba-core/references/gates.md
    - .agents/ba-daily-operators/ba-tools/tests/test_workflow_contract.py
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/critic-independence/requirements.json
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/critic-independence/analysis.md
  modified:
    - .agents/ba-daily-operators/ba-tools/tests/test_skill_schema.py
decisions:
  - "[02-04] Workflow pinned format: YAML frontmatter (operator/default_route/routes) + Markdown body with ## Route: <name> sections; parsed by test_workflow_frontmatter_schema"
  - "[02-04] test_critic_payload_excludes_analysis scans fenced code blocks near ba-critic steps (not prohibition prose) — prevents false positives from Do NOT pass analysis.md wording"
  - "[02-04] test_no_fake_subagent_spawn uses regex negation lookaheads to exclude prohibitive phrasing (there is no autonomous parallel subagent spawn) from the forbidden-pattern check"
  - "[02-04] ba-srs-writer exemplar 3 explicitly demonstrates rejected paraphrase to prevent CITATION_NOT_FOUND failures from verbatim-span discipline"
metrics:
  duration: "~90 minutes (cross-session)"
  completed: "2026-06-18"
  tasks_completed: 2
  files_created: 9
  files_modified: 1
  tests_added: 5
  tests_total: 258
status: complete
---

# Phase 02 Plan 04: ba-srs-analyze Operator Skill Summary

First complete Codex operator skill in the repository — Codex-discoverable SKILL.md + pinned workflow + agent prompts + quality gate contract + 10 contract tests.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Codex skill files + live schema tests + byte-check | 80e33fa | SKILL.md, openai.yaml, test_skill_schema.py (rewritten) |
| 2 | Workflow + agent prompts + gates.md + contract tests + F11 fixture | 34f2be6 | ba-srs-analyze.md, ba-srs-writer.md, ba-critic.md, gates.md, test_workflow_contract.py, 2 fixtures |

---

## What Was Built

### Task 1 — Codex skill discovery files

**SKILL.md** (`.agents/skills/ba-srs-analyze/SKILL.md`, 728 bytes):
- Frontmatter contains EXACTLY `{name, description}` — no extra keys (CLAUDE.md contract verified from openai/skills official repo).
- `description` uses YAML `>` block scalar; block-scalar-aware parser added to `test_skill_schema.py` to handle continuation lines correctly.

**agents/openai.yaml** (`.agents/skills/ba-srs-analyze/agents/openai.yaml`):
- `interface.display_name`, `interface.short_description`, `interface.default_prompt` correctly nested under `interface:`.
- `policy.allow_implicit_invocation: false` nested under `policy:` (not flat top level — the structural note in CLAUDE.md flags DESIGN §3 shows it at flat level incorrectly).
- `default_prompt` uses skill-native wording referencing `ba-tools resolve-route ba-srs-analyze` — NOT the fake CLI literal `ba-srs-analyze --route` (no such binary exists).

**test_skill_schema.py** — rewritten with 5 live tests (no `@pytest.mark.skip`):
- `test_skill_md_frontmatter_keys_only_name_description`
- `test_openai_yaml_nesting_structure`
- `test_openai_yaml_default_prompt_no_fake_cli`
- `test_parse_skill_md_frontmatter_helper`
- `test_parse_skill_md_frontmatter_no_frontmatter_raises`

### Task 2 — Workflow, agent prompts, gate contract, tests

**ba-srs-analyze.md** (`.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md`, 10,211 bytes):
- YAML frontmatter: `operator: ba-srs-analyze`, `default_route: full`, `routes: [extract, draft, lint, verify, full, iterate]` — exactly matches Phase-1 `OPERATOR_ROUTES` registration.
- 6 route sections (`## Route: <name>`), each with ordered numbered steps.
- `full` route: Step 1 (resolve+scaffold) → Step 2 (extract) → Step 3 (ba-srs-writer draft) → Step 4 (verify hard gate) → Step 5 (CoVe loop ≤3) → Step 6 (trace+index, convergence only).
- CoVe loop is sequential — no parallel subagent spawn. Convergence vocabulary defined: `passed early`, `passed after <n>`, `non-convergence-escalation`.
- Critic payload explicitly limited to `{source_path, requirements_json_path}` — `analysis.md` exclusion stated twice (payload block + end of step).

**ba-srs-writer.md** (`.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md`):
- `requirements.json` schema: `id`, `statement`, `classification`, `status`, `source_trace.{section, doc, span}`.
- FR-/NFR-/BR- prefixes (D-09 compliant).
- Verbatim span discipline: ≥12 chars, no paraphrase, no ellipsis.
- 3 inline exemplars: (1) stated + correct span, (2) derived requirement, (3) rejected paraphrase (explicitly shows what NOT to do to prevent CITATION_NOT_FOUND).
- `iterate` route addendum: REQ-ID stability (do not renumber stable requirements).

**ba-critic.md** (`.agents/ba-daily-operators/ba-core/agents/ba-critic.md`):
- Independence contract: receives ONLY `{source_path, requirements_json_path}`. Explicitly forbidden from reading `analysis.md`, `SRS.md`, or writer working notes.
- Re-derivation is independent — critic's value comes from NOT having seen writer's rationale.
- Output schema: `{converged: bool, findings: [{req_id, severity, question, answer, verdict}]}`.
- `converged: true` IFF zero `fail`-severity findings (D-11). WARN findings non-blocking.
- Verdict vocabulary table: `grounded`, `ungrounded`, `missing`, `non-atomic`, `misclassified`, `weak-statement`, `warn-only`.

**gates.md** (`.agents/ba-daily-operators/ba-core/references/gates.md`):
- Authoritative gate sequence: `ba-tools verify → ba-critic CoVe (≤3) → trace+index`.
- Gate 1 (verify): hard block, exit 2 → fold back to writer.
- Gate 2 (CoVe): sequential loop n=1..3; convergence rule; escalation protocol on loop-3 non-convergence.
- Gate 3 (trace+index): only on convergence; never on open FAILs (false provenance prohibition).
- WARN semantics: advisory, non-blocking, logged.
- Prohibition table.

**test_workflow_contract.py** — 5 live tests:
1. `test_workflow_frontmatter_schema` — operator/default_route/routes present and correct.
2. `test_resolve_route_full` — live CLI: `python -m ba_tools resolve-route ba-srs-analyze` returns `default_route: full`.
3. `test_workflow_routes_match_registration` — workflow routes exactly match `OPERATOR_ROUTES["ba-srs-analyze"]`.
4. `test_critic_payload_excludes_analysis` — F11 fixture: `WRITER_RATIONALE_MARKER` in analysis.md, not in requirements.json; fenced code blocks near ba-critic steps contain no `analysis.md`.
5. `test_no_fake_subagent_spawn` — regex negation lookaheads detect prescriptive parallel-spawn language; prohibition prose passes.

**F11 fixtures** (`.agents/ba-daily-operators/ba-tools/tests/fixtures/srs/critic-independence/`):
- `requirements.json` — 3 requirements (FR-001 stated, FR-002 stated, NFR-001 derived).
- `analysis.md` — writer working notes with planted `WRITER_RATIONALE_MARKER` sentinel for independence gate verification.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_critic_payload_excludes_analysis false positive**
- **Found during:** Task 2 test run
- **Issue:** Original test regex matched `analysis.md` anywhere within 20 lines of "ba-critic", including the correct prohibition line "Do NOT pass `analysis.md`". Caused false positive failure.
- **Fix:** Changed to scan only fenced code blocks (``` ... ```) near critic steps. Prohibition prose outside code blocks is now ignored.
- **Files modified:** `test_workflow_contract.py`

**2. [Rule 1 - Bug] test_no_fake_subagent_spawn false positive**
- **Found during:** Task 2 test run
- **Issue:** Plain string match on "parallel subagent" and "parallel spawn" triggered on workflow's own prohibition prose: "there is no autonomous parallel subagent spawn" and "not a parallel spawn".
- **Fix:** Replaced string matching with regex negation lookaheads (`(?<!no )(?<!not a )(?<!do not )...`) to detect only prescriptive (instructional) spawn language.
- **Files modified:** `test_workflow_contract.py`

---

## Known Stubs

None — the workflow is fully specified. All routes have complete step sequences.
The `ba-tools trace write`, `ba-tools index update`, and `ba-tools state advance`
commands are implemented in Phase-02 Plans 02/03 (committed prior to this plan).

---

## Threat Flags

None — this plan creates Markdown/YAML documentation and Python test files only.
No new network endpoints, auth paths, file access patterns, or schema changes.

---

## Self-Check: PASSED

All 10 key files exist on disk. Both task commits present in git log:
- `80e33fa` — feat(02-04): ba-srs-analyze skill files + test_skill_schema live
- `34f2be6` — feat(02-04): workflow + agent prompts + contract tests + F11 fixture

Full test suite: 258 passed, 0 failed.
