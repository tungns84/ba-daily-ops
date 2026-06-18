---
phase: 05-ba-uc-conductor-end-to-end-integration
audit_type: threat-mitigation-verification
register_authored_at_plan_time: true
asvs_level: 1
block_on: high
threats_total: 11
threats_closed: 11
threats_open: 0
unregistered_flags: 0
status: SECURED
audited: "2026-06-18"
---

# Phase 05 — Security Audit (Threat-Mitigation Verification)

Phase: 05 — ba-uc-conductor-end-to-end-integration
ASVS Level: 1 | block_on: high
Result: **SECURED** — 11/11 threats closed, 0 open, 0 unregistered flags.

Method: Each threat in the plan-time register (`register_authored_at_plan_time:
true`) was verified by its declared disposition against the implemented code —
grep + file:line evidence for `mitigate`, acceptance-rationale soundness for
`accept`. The two key mitigation tests cited in the register were executed and
passed. No new-threat scan was performed (per scope). Implementation files were
not modified.

## Threat Verification Table

| Threat ID | Category | Disposition | Verdict | Evidence |
|-----------|----------|-------------|---------|----------|
| T-05-01 | Tampering | mitigate | CLOSED | `acquire_state_lock` → `FileLock(str(lock_path), timeout=STALE_SECONDS)` with `STALE_SECONDS=10` (state_store.py:81, :27). Test `test_concurrent_pipeline_patch_no_clobber` uses `multiprocessing.Process` (test_uc_conductor_state.py:318, :348-352) and PASSES — both writes survive. |
| T-05-02 | Denial of Service | accept | CLOSED | Sound. 10s stale-reclaim window (state_store.py:69-81); concurrent test mirrors existing timeout-bounded `test_state.py` pattern; the no-clobber test completes in <1s (no hang observed on execution). |
| T-05-03 | Information Disclosure | accept | CLOSED | Sound. `tests/fixtures/uc-001-test.md` (763 B) is synthetic "UC-001 Test Fixture" sample data; no real/sensitive content. |
| T-05-04 | Tampering | mitigate (contract) | CLOSED | gates.md Clause 2 (gates.md:190-200) mandates `resolve_under_root` + `is_within_root` for any render-CLI path. Both functions exist and normalize `..` via `resolve()` (repo.py:50-69, :72-100). Contract-level: plugin-deferred, spine-exempt — see note below. |
| T-05-05 | Spoofing | mitigate (contract) | CLOSED | gates.md Clause 1 (gates.md:178-188) forbids Pillow/SVG-convert/screenshot/hand-pasted image; Clause 4 (gates.md:209-219) defines manifest `rendered_sha256 == embedded_sha256` (deferred to PLUG-04). Prohibition table rows present (gates.md:225-230). |
| T-05-06 | Elevation of Privilege | mitigate (contract) | CLOSED | gates.md Clause 2 injection scan `ba-tools scan` (gates.md:190-200) + Clause 3 extension allowlist `.png/.svg/.pdf`, reject-at-write-time (gates.md:202-207). |
| T-05-07 | Tampering | mitigate | CLOSED | trace_cmd.py resolves every path arg via `resolve_under_root` + `is_within_root`, raises `PATH_TRAVERSAL` exit-2 (trace_cmd.py:133-138, :146-150, :158-162, :210-214, :275-282); kind/slug validated against `^[a-z0-9][a-z0-9-]*$` (trace_cmd.py:38, :119-128). index_cmd.py re-resolves untrusted `source_doc` (index_cmd.py:117-122). Conductor passes srs-derived slug, never raw user path (ba-uc-conductor.md:31-36; ba-uc.md:56-58). |
| T-05-08 | Elevation of Privilege | mitigate | CLOSED | Conductor agent prompt + workflow instruct argument-vector invocation of ba-tools; no `shell=True` anywhere on the spine. `resolve_repo_root` uses an argv list `["git","rev-parse",...]` (repo.py:35-39), never a shell string. Conductor never string-interpolates a shell (ba-uc.md:20-30 determinism boundary; ba-uc-conductor.md:7-12). |
| T-05-09 | Tampering | mitigate | CLOSED | All STATE.md / INDEX.md / trace writes route through `acquire_state_lock`: state_cmd.py:85, index_cmd.py:231, trace_cmd.py:295. Plan-01 concurrent test proves no-clobber (see T-05-01). |
| T-05-10 | Spoofing | mitigate | CLOSED | `test_no_render_cli_invoked_on_spine` (test_uc_conductor_workflow.py:326-367) PASSES; independent grep of ba-uc.md for `mmdc|draw.io|drawio|Pillow|screenshot|svg-convert` returns ZERO matches. Conductor agent prompt: "You NEVER call a render CLI (mmdc, draw.io)" (ba-uc-conductor.md:10-12). GATE-03 Scope marks render plugin-only / spine-exempt (gates.md:169-171). |
| T-05-SC | Tampering | accept | CLOSED | Sound across all 3 plans. SUMMARY frontmatter `tech_stack.added: []` / `tech-stack.added: []` for all three plans; zero npm/pip/cargo install task in any plan; stdlib + existing ba-tools + filelock (pre-existing single dep) only. |

## Contract-Level Threats (T-05-04 / T-05-05 / T-05-06) — Explicit Note

These three threats are dispositioned `mitigate (contract)` and are correctly
plugin-deferred / spine-exempt, NOT runtime render code to be found on the spine:

1. The CONTRACT exists: gates.md carries the full "Safety Gate Contract" section
   (gates.md:167-230) with Scope, Phase-5 status, all four clauses, and a
   four-row prohibition table. Plan-02 SUMMARY records gates.md at 7,488 B,
   under the 32,768 B eager-ref budget.
2. The spine genuinely fires NO render path: independent grep of the conductor
   workflow (ba-uc.md) for any render-CLI invocation returns zero matches, and
   `test_no_render_cli_invoked_on_spine` enforces this as a passing
   deterministic guard. The conductor drives authoring routes only
   (srs `full` → mermaid `full` → mockup `full` → `index update`).
3. Enforcement of Clauses 1-4 lands in the deferred plugins (ba-make-diagram,
   ba-uc-delivery, PLUG-01..04) and is explicitly out of scope this phase.

Verdict for all three: CLOSED at the contract level — the documented mitigation
is present in gates.md and the spine is provably exempt. No runtime render-side
implementation gap exists because the spine invokes no render CLI.

## Unregistered Flags

None. All three plan SUMMARY files declare "Threat Flags: None" / no new network
endpoints, auth paths, file-access patterns, or schema changes. Phase 05 added
test files, two reference/workflow Markdown files, an agent prompt, and a CDX
skill pair (SKILL.md + openai.yaml) — zero new ba-tools source, zero new
dependencies. No new attack surface appeared during implementation that lacks a
threat mapping.

## Accepted Risks Log

| ID | Risk | Acceptance Rationale | Sound? |
|----|------|----------------------|--------|
| T-05-02 | Concurrent multiprocessing test hangs on the lock | 10s stale-reclaim window bounds the wait; test mirrors the existing timeout-bounded test_state.py pattern; observed completion <1s | Yes |
| T-05-03 | Fixture UC content disclosure | uc-001-test.md is synthetic, non-sensitive sample data committed to the repo | Yes |
| T-05-SC | npm/pip/cargo install introducing supply-chain risk | Zero new dependencies in all 3 plans — stdlib pytest + existing ba-tools (+ pre-existing filelock) only; no install task | Yes |

## Verification Evidence (commands executed)

- `pytest test_uc_conductor_state.py::test_concurrent_pipeline_patch_no_clobber` → PASSED (T-05-01)
- `pytest test_uc_conductor_workflow.py::test_no_render_cli_invoked_on_spine` → PASSED (T-05-10)
- `pytest test_uc_conductor_workflow.py::test_deliver_route_drives_mermaid_full_not_author` → PASSED (supporting T-05-10)
- grep of ba-uc.md for render-CLI patterns → 0 matches (T-05-10)
- grep of trace_cmd.py / index_cmd.py for model-client imports → 0 matches (determinism boundary, supports T-05-07/08)

## Files Inspected (read-only)

- .agents/ba-daily-operators/ba-tools/ba_tools/state_store.py
- .agents/ba-daily-operators/ba-tools/ba_tools/repo.py
- .agents/ba-daily-operators/ba-tools/ba_tools/commands/trace_cmd.py
- .agents/ba-daily-operators/ba-tools/ba_tools/commands/index_cmd.py
- .agents/ba-daily-operators/ba-tools/ba_tools/commands/state_cmd.py (lock-usage confirm)
- .agents/ba-daily-operators/ba-core/references/gates.md
- .agents/ba-daily-operators/ba-core/workflows/ba-uc.md
- .agents/ba-daily-operators/ba-core/agents/ba-uc-conductor.md
- .agents/ba-daily-operators/ba-tools/tests/test_uc_conductor_state.py
- .agents/ba-daily-operators/ba-tools/tests/test_uc_conductor_workflow.py
- .agents/ba-daily-operators/ba-tools/tests/fixtures/uc-001-test.md

No implementation file was modified during this audit.
