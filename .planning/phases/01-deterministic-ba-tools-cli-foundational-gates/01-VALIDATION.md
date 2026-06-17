---
phase: 1
slug: deterministic-ba-tools-cli-foundational-gates
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-17
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `01-RESEARCH.md` → Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 (confirmed installed) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — **Wave 0 installs** |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds (concurrent-write test dominates: ~10s lock window) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

> Task IDs assigned by the planner. Rows below are requirement-scoped; each maps to
> one or more plan tasks. `❌ W0` = test file is a Wave 0 dependency (does not yet exist).

| Task ID | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | 0 | — | — | conftest + fixtures (renumbered-reqs, citation pass/fail, tmp_ba_ops) | infra | `python -m pytest tests/ --collect-only` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-13, CDX-05 | T-1-07 | Errors → stderr + exit 2; no stack traces; flat envelope | integration | `pytest tests/test_output_contract.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-14 | T-1-01 | Paths resolve under `--repo-root`; `sys.executable`; no traversal | unit | `pytest tests/test_paths.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-02 | — | Static DEFAULT_ROUTE only; unknown operator → exit 2 | unit | `pytest tests/test_resolve_route.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | GATE-04, CDX-04 | — | `byte-check` exit 2 at ≥ 32768 B; passes < limit | unit | `pytest tests/test_byte_check.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-03 | T-1-03 | Two concurrent writers: no clobber; loser → LOCK_TIMEOUT exit 2 | integration (multiprocessing) | `pytest tests/test_state.py::test_concurrent_write -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-01, TRACE-01 | — | `init` creates `.ba-ops/` scaffold (5 files) + returns context JSON | integration | `pytest tests/test_init.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TRACE-02 | — | Missing config flag = `true`; present `false` respected (no write-on-absence) | unit | `pytest tests/test_config.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-06 | — | Rejects span not in cited section; accepts real ≥12-char span; `--cite-scope document` override | unit | `pytest tests/test_verify.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-04 | — | Flags grounding / verifiability / atomicity / citation (FAIL); ambiguity (WARN) | unit | `pytest tests/test_lint_reqs.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-05 | — | Flags material statement change on renumbered-requirements fixture (always FAIL) | unit | `pytest tests/test_lint_reqs.py::test_material_change_fixture -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-09 | — | `uc-status` returns pipeline state + `next_step` | unit | `pytest tests/test_uc_status.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-10 | — | `extract-uc` returns correct section for multi-heading doc (level-aware stop) | unit | `pytest tests/test_extract_uc.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-11 | T-1-09 | `template fill` writes scaffold; `--out` validated under repo root | unit | `pytest tests/test_template.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-12 | — | `discovery add` appends; `list` returns all | unit | `pytest tests/test_discovery.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | TOOL-15 | T-1-02 | `scan` advisory only — WARN, never blocks, exit 0 | unit | `pytest tests/test_scan.py -x` | ❌ W0 | ⬜ pending |
| TBD | 1 | GATE-02 | — | `confirm` pass-through exit 0 in v1 | unit | `pytest tests/test_confirm.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pip install "filelock>=3.29.4"` — **single runtime dependency, not yet installed** (blocks all `state` tests)
- [ ] `pyproject.toml` — pytest config + `[project.scripts] ba-tools = "ba_tools.__main__:main"`
- [ ] `tests/conftest.py` — shared fixtures: `tmp_ba_ops`, sample requirements, renumbered-requirements fixture, citation pass/fail fixtures
- [ ] Test stub files for every requirement row above (one per command, plus `test_output_contract.py` spot-checking the envelope shape)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AGENTS.md / eager-ref real-size check | CDX-04 | No AGENTS.md authored in Phase 1 (Codex skill layer is later); GATE-04 logic is unit-tested, but the live-doc enforcement is manual until docs exist | Run `python -m ba_tools byte-check AGENTS.md --repo-root .` once AGENTS.md exists; expect exit 0 while < 32768 B |
| git pre-commit hook (GATE-04 layer 2) | GATE-04, D-05/D-06 | Repo git-init state may be incomplete; hook activates only under git. Subcommand is the source of truth and is auto-tested | Once under git: stage an oversized eager doc, attempt commit, confirm hook blocks via `ba-tools byte-check` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (filelock install + 16 test files + conftest)
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
