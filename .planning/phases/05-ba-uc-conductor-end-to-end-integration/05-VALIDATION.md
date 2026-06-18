---
phase: 5
slug: ba-uc-conductor-end-to-end-integration
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-18
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `05-RESEARCH.md` → `## Validation Architecture`; commands lifted from each PLAN task's `<automated>` block.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (project standard — CLAUDE.md; `pyproject.toml` + `conftest.py` present) |
| **Config file** | `.agents/ba-daily-operators/ba-tools/pyproject.toml` |
| **Working dir** | `.agents/ba-daily-operators/ba-tools` (tests shell `ba-tools` via `sys.executable -m ba_tools`) |
| **Quick run command** | `python -m pytest tests/test_uc_conductor_state.py tests/test_index_gate_predicate.py tests/test_scaffold_all_four_rows.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~30 s (est. — subprocess-per-test integration style) |

*Run from the working dir above. Interpreter resolves via `sys.executable` (never a hard-coded `python` path — CLAUDE.md / DESIGN §11).*

---

## Sampling Rate

- **After every task commit:** Run the task's own `<automated>` command (per-task map below).
- **After every plan wave:** Run the full suite `python -m pytest tests/ -q`.
- **Before `/gsd-verify-work`:** Full suite green + the agent-run E2E UAT (manual table) reviewed.
- **Max feedback latency:** ~30 s (full suite; quick subset is faster).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | UC-03 | T-05-01 / T-05-02 | FileLock serializes concurrent STATE.md writes — no clobber; next_step lands on failed/in_progress (recoverable) | integration | `pytest tests/test_uc_conductor_state.py -x -q` | created by task (tdd) | ⬜ pending |
| 05-01-02 | 01 | 1 | UC-03, GATE-03 | — (integrity) | D-G2 predicate computed from `orphans`+`gaps` only (no `covered_by`); orphan detected; scaffold seeds all 4 rows | integration | `pytest tests/test_index_gate_predicate.py tests/test_scaffold_all_four_rows.py -x -q` | created by task (tdd) | ⬜ pending |
| 05-02-01 | 02 | 1 | GATE-03 | T-05-04 / T-05-05 / T-05-06 | Safety contract documents render-CLI-only + path-traversal/injection + extension defenses; spine-exempt | doc-assertion | `grep -c -i "Safety Gate Contract" .agents/ba-daily-operators/ba-core/references/gates.md && python -c "import os;assert os.path.getsize('.agents/ba-daily-operators/ba-core/references/gates.md')<32768"` | modifies existing | ⬜ pending |
| 05-03-01 | 03 | 2 | UC-01, UC-02, UC-03 | T-05-07 | `policy.allow_implicit_invocation: false` (conductor cannot self-invoke); SKILL.md name+description only | static | `pytest tests/test_uc_conductor_workflow.py::test_ba_uc_skill_frontmatter_name_description_only tests/test_uc_conductor_workflow.py::test_ba_uc_openai_yaml_policy_implicit_false -x -q` | created by 05-03-03 | ⬜ pending |
| 05-03-02 | 03 | 2 | UC-01, UC-02, UC-03 | T-05-08 / T-05-09 | Subprocess via `sys.executable`, no `shell=True`; slug derived (not raw user path); lockfile-guarded writes | static | `pytest tests/test_uc_conductor_workflow.py::test_ba_uc_workflow_frontmatter_matches_registered_routes tests/test_uc_conductor_workflow.py::test_deliver_route_drives_mermaid_full_not_author -x -q` | created by 05-03-03 | ⬜ pending |
| 05-03-03 | 03 | 2 | UC-03 | T-05-10 | Static guard: no render CLI (`mmdc`/`draw.io`) invoked on the spine (criterion 4) | static | `pytest tests/test_uc_conductor_workflow.py -x -q` | created by task | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. "created by task (tdd)" = the test file is the task's own deliverable, not a Wave 0 stub.*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — pytest, `pyproject.toml`, and
`conftest.py` are already present under `.agents/ba-daily-operators/ba-tools/` (Phase 1).
The Phase-5 test files (`test_uc_conductor_state.py`, `test_index_gate_predicate.py`,
`test_scaffold_all_four_rows.py`, `test_uc_conductor_workflow.py`) and the fixture
`tests/fixtures/uc-001-test.md` are authored by Plans 01/03 themselves (TDD), not pre-seeded.

- [x] No new framework install needed.
- [x] Shared fixtures/helpers reused from `test_uc_status.py`, `test_state.py`, `test_index.py`, `test_trace.py`, `test_workflow_contract.py`, `test_skill_schema.py` (analogs).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Agent-run E2E: real `ba-uc deliver` on `tests/fixtures/uc-001-test.md` produces SRS + mermaid + mockup + INDEX.md for one shared slug, no orphans | UC-01, UC-02 | Non-deterministic agent authoring (LLM) — cannot be scripted as a deterministic assert | Run `ba-uc --uc "uc-001-test.md: ## UC-001. <name>" --fidelity wireframe`; confirm all 4 `.ba-ops/<slug>/` artifacts exist, `ba-tools index update` reports `orphans: []`, and each artifact's req_ids resolve in INDEX.md |
| Gate-reject → resume continuity (E2E) | UC-03 | Requires a live failing gate verdict from the agent loop | Force a srs Quality-gate fail; confirm `ba-tools uc-status` `next_step` == failed step; run `resume`; confirm pipeline completes to a fully-traced UC |
| Kill mid-pipeline → recoverable (E2E) | UC-03 | Requires interrupting a live conductor run | Kill the conductor mid-step; confirm `uc-status` returns correct `next_step`; `resume` completes remaining steps |

*The deterministic halves of UC-03's resume/kill/gate-reject behavior ARE automated (05-01-01); the rows above are the live-agent E2E confirmations layered on top.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (all 6 tasks carry an automated command)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (all 6 are automated)
- [x] Wave 0 covers all MISSING references (none missing — existing infra)
- [x] No watch-mode flags (all commands are one-shot `-q`)
- [x] Feedback latency < ~30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-18
