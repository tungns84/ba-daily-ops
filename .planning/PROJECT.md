# BA Daily Operators

## What This Is

A GSD-grade operator suite for Business Analysts that turns each repeated daily
deliverable loop (use case → requirements/SRS → process diagram → UI mockup →
traceability index) into a reproducible **operator**: a skill backed by a
deterministic CLI and verified by gates. Output is hash-provable, inspectable,
and portable across machines and runtimes. Built CodexApp-first (v1), with a
Claude Code transform on the v2 roadmap.

## Core Value

**REQ-ID traceability across artifacts** — one requirement seen consistently
across SRS, diagram, mockup, and backlog, so drift surfaces the moment it
appears. If everything else fails, the traceability spine must work.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- [x] Determinism boundary enforced: CLI only does what a file/command/hash can prove; agents own all judgement — *Validated in Phase 1*
- [x] Verbatim citation-exists check: a `stated` requirement's `source_trace.span` must be a real ≥12-char substring of its source doc (section-scoped, `--cite-scope document` override) — *Validated in Phase 1*
- [x] Default-route resolution: `--route` optional, falls back to operator's `DEFAULT_ROUTE` via `resolve-route` (never infer route from free text) — *Validated in Phase 1*
- [x] Byte budgets enforced by gate: pre-commit/CI byte-check fails when an eager-loaded doc ≥ 32,768 B — *Validated in Phase 1*
- [x] Terse, scannable `ba-tools` JSON output: every success prints UTF-8 JSON to stdout, every `BaToolsError` exits 2 (no traceback leaks) — *Validated in Phase 1*
- [x] `ba-mermaid` operator: UC/requirement → Mermaid diagram authored MD-inline (default route invokes no CLI); each diagram cites REQ-IDs into the traceability matrix; optional `mmdc` render hard-fails (never synthesizes a substitute image) — *Validated in Phase 3 (MMD-01, MMD-02, MMD-03)*
- [x] `ba-mockup` operator: requirements → UI mockup at a required `--fidelity html|wireframe` (workflow hard-rejects missing/invalid fidelity before authoring; html→`.html`, wireframe→inline `.md` blocks); each screen cites REQ-IDs into the traceability matrix; no render route / synthetic-render path (DESIGN §11); zero new ba-tools commands — *Validated in Phase 4 (MOCK-01, MOCK-02, MOCK-03)*

### Active

<!-- v1 milestone scope: the daily spine. Building toward these. -->

- [ ] `ba-tools` deterministic Python CLI (init, state, resolve-route, lint-requirements, verify, trace, index, uc-status, discovery, template fill, extract-uc) — *core commands shipped Phase 1; `trace`/`index` land in Phase 2*
- [ ] `ba-srs-analyze` operator: sources → atomic, grounded, verifiable requirements (JSON) + SRS/BRD `.md`
- [ ] `ba-critic` agent: fresh-context Chain-of-Verification self-critique loop (≤3 revisions, read-only)
- [ ] `ba-uc` conductor: deliver ONE use case end-to-end (srs-analyze → mermaid → mockup → index) as a sequential agent loop, Quality gate between steps, resumable via `uc-status`
- [ ] `.ba-ops/` file-state spine: PROJECT.md, REQUIREMENTS.md, INDEX.md traceability matrix, STATE.md (lockfile-guarded), config.json (absent = enabled) — *spine scaffold + lockfile-guarded STATE shipped Phase 1; INDEX.md matrix in Phase 2*
- [ ] `ba-tools index update`: rebuild INDEX.md, flag gaps (missing coverage), orphans (bad req_ids), stale (source-hash drift)
- [ ] Three verification gates: Confirm (irreversible/outward), Quality (verify + ba-critic), Safety (render/embed, plugins only)
- [ ] Codex skill layout: flat `.agents/skills/ba-*/SKILL.md` + `agents/openai.yaml`, `allow_implicit_invocation: false` on spine/conductor

### Out of Scope

<!-- Explicit boundaries for the v1 milestone. -->

- Optional plugins (`ba-make-diagram` draw.io BPMN, `ba-uc-delivery` DOCX, `ba-backlog-grooming`) — the rare ~20%; deferred to a later milestone (off the daily spine)
- Claude Code v2 transform (Task-subagent spawn, command frontmatter, hooks, install-time transform) — roadmap v2; `ba-tools` + `.ba-ops/` ship into v2 unchanged
- Bespoke GUI / standalone web dashboard / `.ba-ops/` viewer — UI is in-Codex chat only (DECIDED); effectiveness over looks
- Synthetic diagram rendering (Pillow / SVG converter / screenshot / hand-pasted) — forbidden; real render CLIs only
- DOCX `update-docx` media-replace — lives in the deferred plugin (still a stub in DESIGN)

## Context

- **Standard mirrored:** GSD Core's five-layer model (Command/Skill → Workflow → Agent → CLI Tools → File-State), adapted for BA work per `FIS_GSARCHITECTURE.md`.
- **Source of truth:** `DESIGN.md` v0.2.2 in repo root — the architecture spec this build aligns to. Its "DONE" build-order markers are forward-looking targets, not current state; this workspace is a fresh greenfield build.
- **Daily workload shape:** high UC volume + real cross-artifact traceability pain (confirmed) — drives the traceability-first core value and the conductor.
- **Two render backends, never crossed:** `ba-mermaid` (daily, MD-inline, lightweight flows) vs `ba-make-diagram` (formal BPMN, draw.io — plugin, deferred).
- **Codex caveat:** Codex has no autonomous cross-skill spawn, so `ba-uc` runs specialists as one sequential agent loop, not true fresh-context subagents. The independence that matters (`ba-critic` re-deriving from source) is preserved by instruction. True fresh-context spawn is the v2 Claude/Task model.

## Constraints

- **Runtime**: CodexApp-first (v1) — author Codex-native (`.agents/skills/`, AGENTS.md Read-by-skills not root-auto-loaded, `agents/openai.yaml`). Claude Code is v2 roadmap. — DESIGN §9 ordering, confirmed.
- **Tech stack**: `ba-tools` in **Python** (`python-docx`, Markdown extraction, hashing already Python in the harness); resolve Python via `sys.executable`. Render shells out to draw.io desktop CLI + `mmdc` (plugins/optional only in v1).
- **Determinism boundary**: `ba-tools` does ONLY file/command/hash-provable work; agents own all analysis/authoring/judgement. Hard line — DESIGN §5.
- **Byte budgets**: AGENTS.md/eager refs < 32,768 B (Codex truncates beyond); DEFAULT workflow < 38,000 B; LARGE < 54,000 B.
- **Portability**: no hard-coded machine paths in committed config; all paths resolve relative to `--repo-root` (git root / cwd).
- **Determinism of CLI output**: every success prints UTF-8 JSON to stdout; every `BaToolsError` exits `2`.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Full greenfield build aligned to DESIGN.md | Workspace empty; DESIGN "DONE" markers are aspirational targets, not existing code | — Pending |
| v1 milestone = daily spine only (conductor + 3 spine ops + ba-tools + .ba-ops) | Spine carries the daily value and blast-radius control; plugins are the rare ~20% | — Pending |
| Plugins deferred to a later milestone | Off the daily spine (draw.io/DOCX machinery); avoids front-loading rare work | — Pending |
| Codex-first runtime per DESIGN §9 | Honor the documented v1 ordering; ba-tools + .ba-ops are runtime-agnostic and carry into v2 unchanged | — Pending |
| `ba-tools` in Python | Heavy verifiable work (DOCX, extraction, hashing) already Python in the harness | — Pending |
| Traceability is the core value, not artifact volume | High UC volume + cross-artifact drift is the confirmed real pain | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-18 — Phase 4 complete (`ba-mockup` operator; MOCK-01/02/03 validated, fidelity-gated html/wireframe authoring joins the REQ-ID traceability matrix, zero new ba-tools commands, no synthetic render, 283 tests green)*
