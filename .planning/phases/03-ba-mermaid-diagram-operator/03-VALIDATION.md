---
phase: 3
slug: ba-mermaid-diagram-operator
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-18
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing — configured in `pyproject.toml`, Phase 1/2) |
| **Config file** | `.agents/ba-daily-operators/ba-tools/pyproject.toml` (+ `tests/conftest.py`, `tests/fixtures/`) |
| **Quick run command** | `cd .agents/ba-daily-operators/ba-tools && "$(python -c 'import sys;print(sys.executable)')" -m pytest tests/test_mermaid_render_cmd.py tests/test_mermaid_author.py tests/test_mermaid_trace_index.py -x -q` |
| **Full suite command** | `cd .agents/ba-daily-operators/ba-tools && "$(python -c 'import sys;print(sys.executable)')" -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds (small suite; render tests mock `subprocess`/`shutil.which`, no real `mmdc` spawn) |

---

## Sampling Rate

- **After every task commit:** Run the **Quick run command** (the 3 phase-3 test modules)
- **After every plan wave:** Run the **Full suite command** (`tests/` — guards no Phase-1/2 regression)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | MMD-03 | T-03-01..05 | Fence-extract + path/arg handling; RED scaffold pins exit-2 + no-synthetic contract | unit | `pytest tests/test_mermaid_render_cmd.py -q` | ❌ W1 (TDD red) | ⬜ pending |
| 03-01-02 | 01 | 1 | MMD-03 | T-03-01..05 / T-03-SC | No `mmdc` resolves → `BaToolsError` exit 2 + NO image written; list-form `subprocess`, `npx -p` fixed form | unit | `pytest tests/test_mermaid_render_cmd.py -x -q` | ❌ W1 (TDD red) | ⬜ pending |
| 03-02-01 | 02 | 1 | MMD-01 | T-03-06 | SKILL.md `name`+`description` only; `policy.allow_implicit_invocation: false` | unit | `pytest tests/test_skill_schema.py -q` | ✅ (extends existing) | ⬜ pending |
| 03-02-02 | 02 | 1 | MMD-01 | T-03-07 / T-03-08 | Route contract (author/full/render); frontmatter `req_ids` → `trace write --req-ids` hand-off, no new parser | unit | `pytest tests/test_workflow_contract.py -q` | ✅ (extends existing) | ⬜ pending |
| 03-02-03 | 02 | 1 | MMD-01 | T-03-08 | `author` route invokes ZERO CLI and writes ZERO trace (no `mermaid-render`/`mmdc` in author section) | unit | `pytest tests/test_mermaid_author.py -x -q` | ❌ W1 (TDD red) | ⬜ pending |
| 03-03-01 | 03 | 2 | MMD-02 | T-03-09 / T-03-10 | `full` route req_ids → INDEX mermaid column; real IDs no-orphan, invented ID surfaced (not swallowed) | integration | `pytest tests/test_mermaid_trace_index.py -x -q` | ❌ W2 (TDD red) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*File Exists: ✅ present · ❌ Wn = created (TDD red-first) in wave n*
*T-03-SC = supply-chain threat (npx/mmdc provenance), dispositioned in each plan's `<threat_model>`.*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.* pytest is already configured (`pyproject.toml`), `tests/conftest.py` + `tests/fixtures/` are present (Phase 1/2), and collection succeeds. No framework install or shared-fixture bootstrap is needed. The three new `test_mermaid_*.py` modules are authored TDD-red inside their owning Wave-1/Wave-2 tasks, not as Wave-0 prerequisites.

---

## Manual-Only Verifications

*All phase behaviors have automated verification.* The three ROADMAP success criteria each map to an automated test: criterion 1 → `test_mermaid_author.py` (author no-CLI), criterion 2 → `test_mermaid_trace_index.py` (req_ids → INDEX, orphans), criterion 3 → `test_mermaid_render_cmd.py` (resolved `mmdc` + exit-2 hard-fail via `mock.patch("shutil.which", return_value=None)`).

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (none — existing infra)
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-18 (plan-time validation contract; final green sign-off at `/gsd-verify-work`)
