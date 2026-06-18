---
phase: 04-ba-mockup-operator
asvs_level: 1
threats_total: 6
threats_closed: 6
threats_open: 0
block_on: high
register_authored_at_plan_time: true
audited: 2026-06-18
status: SECURED
---

# Phase 04 — ba-mockup-operator — Security Audit

Retroactive verification of the plan-time STRIDE threat register against the
implemented code. Every declared mitigation was confirmed present by grep/read of
the cited files (not by trusting SUMMARY claims). Implementation files were not
modified — only this SECURITY.md was written.

**Result: SECURED — 6/6 threats closed, 0 open. No blockers.**

## Threat Verification

| Threat ID | Category | Disposition | Status | Evidence (file:line) |
|-----------|----------|-------------|--------|----------------------|
| T-4-01 | Tampering (V5 Input) — `--fidelity` argument | mitigate | CLOSED | `ba-mockup.md:35-37` — Route:screen Step 2 hard-rejects missing/invalid fidelity ("must be `html` or `wireframe`", "Do NOT proceed to authoring") BEFORE `ba-tools init` (step 3) and authoring (step 4). Proven by `test_mockup_author.py:225-249` (`test_workflow_rejects_missing_fidelity`, green per 04-03-SUMMARY). |
| T-4-02 | Spoofing — agent invents a REQ-ID | mitigate | CLOSED | `ba-mockup-author.md:141-142` — explicit "Do NOT invent REQ-IDs not present in `requirements.json`" rule. Downstream orphan detection proven by `test_mockup_trace_index.py:311-345` (`test_invented_id_surfaces_as_orphan`): writes `FR-001,FR-999`, asserts FR-999 under `## Orphans` and FR-001 not orphan. |
| T-4-03 | Tampering — path traversal in `--artifact`/`--source-doc` | accept | CLOSED | Documented accepted risk (existing guards consumed as-is, no new code). Verified guards present and wired: `repo.py:50` `resolve_under_root`, `repo.py:72` `is_within_root` (`..` normalized via `resolve()`, T-1-01). Actively called at every path entry point in `trace_cmd.py`: `--artifact` (133-134), `--source-doc` (145-146), `--requirements` (157-158), `--req-ids` file (209-210), output path (275) — each rejects out-of-root with exit-2 PATH_TRAVERSAL. See accepted-risk log below. |
| T-4-04 | Tampering — `<script>`/JS injection in `.html` artifact | mitigate | CLOSED | `ba-mockup-author.md:48-50` — HTML rules forbid `<script>` and external `src=`/`href=` URL (no CDN/framework). Fixture `authored_html.html` confirmed: no `<script>`, no external `src=`/`href=` (footer is text-only). Asserted by `test_mockup_author.py` D-03 fixture tests (green per 04-03-SUMMARY). |
| T-4-05 | Information Disclosure / Tampering — implicit auto-invocation of build path | mitigate | CLOSED | `openai.yaml:17-18` — `policy.allow_implicit_invocation: false` nested under `policy:` (CDX-02). |
| T-4-06 | Tampering — synthetic-render path slips into operator | mitigate | CLOSED | Independent grep over all 4 operator files (`ba-mockup.md`, `ba-mockup-author.md`, `SKILL.md`, `openai.yaml`) for `mmdc`/`mermaid-render`/`drawio`/`screenshot`/`Route: render`/bare `render` = 0 matches. No render route exists. Screen-route slice enforced by `test_mockup_author.py:164-217` (`test_screen_route_invokes_no_render_cli`, green). The lone repo match is in `ba-mermaid/SKILL.md` (out of scope, different operator). |
| T-4-SC | Tampering — npm/pip/cargo installs | accept | CLOSED | Documented accepted risk. Verified: `git diff --stat HEAD~3 HEAD -- ba_tools/` empty (no package-source change); no dependency manifest (`requirements*.txt`/`pyproject.toml`/`setup.py`/`package.json`/`Cargo.toml`) changed across the phase. Zero new dependencies; no install performed. See accepted-risk log below. |

## Accepted Risks Log

| Threat ID | Risk | Justification (verified) | Residual |
|-----------|------|--------------------------|----------|
| T-4-03 | Path traversal via `--artifact`/`--source-doc`/`--requirements` | This phase adds zero ba-tools code. Path inputs are guarded by the pre-existing `repo.py` `resolve_under_root` + `is_within_root` pair (introduced/covered under T-1-01/T-02-07), confirmed wired at all five path entry points in `trace_cmd.py`, each rejecting out-of-root paths with exit 2. The mockup operator consumes this CLI unchanged. | Windows symlink/junction containment of a non-existent target is not guaranteed by `is_within_root` (documented caveat at `repo.py:80-86`). Out of scope for this phase; pre-existing behavior, not introduced here. |
| T-4-SC | Supply-chain via package install | No `npm`/`pip`/`cargo` install occurs in this phase. pytest already active since Phase 1. `git diff` confirms zero package-source and zero dependency-manifest changes across the three phase commits. | None for this phase. Any future dependency addition must re-trigger a supply-chain legitimacy checkpoint. |

## Unregistered Flags

None. The three SUMMARY files (04-01, 04-02, 04-03) contain "Threat Surface Scan"
sections, each reporting **no new network endpoints, auth paths, file-access
patterns, or schema changes** beyond what the plan-time register documents. No
`## Threat Flags` section was present and no new attack surface appeared during
implementation that lacks a threat mapping.

## Disposition Reconciliation

- **T-4-01** is listed `accept` in 04-01-PLAN (test-only plan, no flag) but `mitigate`
  in 04-02-PLAN (the workflow gate). Strongest disposition wins → verified as
  `mitigate`; the workflow gate is present and the gate-text test is green.
- **T-4-03** and **T-4-SC** are documented accepted risks; both justifications were
  re-verified to still hold (existing guard present and wired; zero installs / zero
  dependency-manifest changes).

## Audit Constraints Honored

- Verification by declared disposition only (mitigate / accept) — no blind scan for
  new vulnerabilities.
- No implementation file modified. Only `04-SECURITY.md` created.
- Each `mitigate` mitigation confirmed by a located control in the cited file (not by
  documentation/intent). Each `accept` justification re-verified against the codebase.
