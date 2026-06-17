# Roadmap: BA Daily Operators

## Overview

This roadmap builds the v1 daily spine of a CodexApp-first BA operator suite, in
the dependency order all four researchers and DESIGN §10 confirm: a fully
functional deterministic `ba-tools` CLI first (with the foundational gates baked
in, not retrofitted), then `ba-srs-analyze` together with the REQ-ID
traceability core (so REQ-ID coupling is validated before more operators consume
it), then the two independent spine operators `ba-mermaid` and `ba-mockup`, and
finally the `ba-uc` conductor that drives the whole spine end-to-end and doubles
as the integration test. Every phase preserves the core value — REQ-ID
traceability across artifacts — and the determinism boundary (CLI proves;
agents judge). Plugins and the Claude v2 transform are explicitly out of this
milestone.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Deterministic ba-tools CLI + Foundational Gates** - Full file/hash/command-provable CLI, `.ba-ops/` scaffold, lockfile state, REQ-ID stability lint, citation-exists verify, and the CI byte-check gate
- [x] **Phase 2: ba-srs-analyze + Quality Gate + Traceability Core** - Sources become atomic grounded requirements with a `source_trace` schema, gated by `ba-tools verify` + the fresh-context `ba-critic` CoVe loop, with the INDEX.md matrix and gap/orphan/stale drift detection (completed 2026-06-17)
- [ ] **Phase 3: ba-mermaid Diagram Operator** - UC/requirement becomes an MD-inline Mermaid diagram that cites the REQ-IDs it depicts, with optional `mmdc` export
- [ ] **Phase 4: ba-mockup Operator** - Requirements become a UI mockup at `--fidelity html|wireframe`, each screen citing the REQ-IDs it realizes
- [ ] **Phase 5: ba-uc Conductor + End-to-End Integration** - One use case delivered end-to-end (srs-analyze → mermaid → mockup → index) as a resumable sequential loop with a Quality gate between steps; the spine's integration test

## Phase Details

### Phase 1: Deterministic ba-tools CLI + Foundational Gates

**Goal**: A functionally complete `ba-tools` CLI exists — every command does only file/hash/command-provable work — with the `.ba-ops/` file-state spine scaffolded and the four foundational gates (byte-check, lockfile, deterministic route resolution, REQ-ID stability) operational so no later operator has to retrofit them.
**Depends on**: Nothing (first phase)
**Requirements**: TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-05, TOOL-06, TOOL-09, TOOL-10, TOOL-11, TOOL-12, TOOL-13, TOOL-14, TOOL-15, TRACE-01, TRACE-02, GATE-02, GATE-04, CDX-04, CDX-05
**Success Criteria** (what must be TRUE):

  1. `ba-tools verify` rejects a `stated` requirement whose `source_trace.span` is not a real ≥12-char verbatim substring of its source doc within the cited section, and accepts one that is (section-scoped, with `--cite-scope document` override)
  2. `ba-tools lint-requirements` flags a material statement change on an existing REQ-ID against a renumbered-requirements fixture instead of silently renumbering, and also flags ambiguity, atomicity, grounding, and verifiability issues
  3. `ba-tools state update|patch|advance` writes `.ba-ops/STATE.md` under a lockfile and a second concurrent writer either waits or reclaims the lock only after the 10s stale window — never clobbers
  4. `ba-tools resolve-route <operator>` returns only the static `DEFAULT_ROUTE` (e.g. `ba-mermaid`→`author`) and never produces a route inferred from free text; every success prints UTF-8 JSON to stdout and every `BaToolsError` exits with code 2
  5. A CI/pre-commit byte-check fails the build when any eager-loaded doc (AGENTS.md / refs) is ≥ 32,768 B, and all paths resolve relative to `--repo-root` with Python resolved via `sys.executable` (no hard-coded machine paths)

**Plans**: 7 plans (3 waves)Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Wave 0: package skeleton, shared infra (errors/output/repo), argparse dispatcher, pyproject + filelock install, conftest + 17 test stubs
- [x] 01-02-PLAN.md — Wave 1: foundational gates — resolve-route (static DEFAULT_ROUTES) + byte-check (32768 B limit)
- [x] 01-03-PLAN.md — Wave 1: state + lockfile (FileLock(timeout=10), Windows stale reclaim, concurrent-write no-clobber test)
- [x] 01-04-PLAN.md — Wave 1: init + .ba-ops/ scaffold + config (absent=enabled) + uc-status
- [x] 01-05-PLAN.md — Wave 1: quality engine — lint-requirements (heuristics + two-pass REQ-ID stability) + verify (section-scoped citation-exists)
- [x] 01-06-PLAN.md — Wave 1: extract-uc + template fill + discovery + scan (advisory) + confirm (pass-through)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-07-PLAN.md — Wave 2: cross-command output-contract + path-safety tests + git pre-commit byte-check hook

### Phase 2: ba-srs-analyze + Quality Gate + Traceability Core

**Goal**: The highest-value differentiator works end-to-end: sources become atomic, grounded, verifiable requirements (JSON) plus an SRS/BRD `.md`, every `stated` requirement carries a verifiable `source_trace`, the artifact is gated by `ba-tools verify` plus the independent fresh-context `ba-critic` Chain-of-Verification loop, and the `.ba-ops/` traceability matrix (INDEX.md) is rebuilt with gap/orphan/stale detection so REQ-ID coupling is validated before any other operator consumes REQ-IDs.
**Depends on**: Phase 1
**Requirements**: SRS-01, SRS-02, SRS-03, SRS-04, SRS-05, SRS-06, GATE-01, TRACE-03, TRACE-04, TRACE-05, TOOL-07, TOOL-08, CDX-01, CDX-02, CDX-03
**Success Criteria** (what must be TRUE):

  1. Running `ba-srs-analyze` (default route `full`; routes extract/draft/lint/verify/full/iterate) on a source document produces a requirements JSON of atomic, grounded, verifiable requirements plus an SRS/BRD `.md`, where every `stated` requirement carries a `source_trace` `{doc, span}` matching the schema `ba-tools verify` gates
  2. The Quality gate runs `ba-tools verify` then `ba-critic`, and `ba-critic` produces findings by generating per-requirement questions and answering them from the source independently of the draft (never editing), running ≤3 revision loops with early-exit-on-convergence logged ("passed early" vs "passed after N")
  3. `ba-tools trace write` records an artifact→REQ-ID mapping plus a statement hash, and `ba-tools index update` rebuilds INDEX.md as a REQ-ID → SRS § → mermaid → mockup → story matrix
  4. INDEX.md flags gaps (REQ-IDs with no coverage), orphans (`req_ids` that don't exist in the registry), and stale entries (source hash changed → re-run needed) against a fixture exercising all three
  5. The `ba-srs-analyze` skill ships as flat `.agents/skills/ba-srs-analyze/SKILL.md` (frontmatter `name`+`description` only) with `agents/openai.yaml` carrying `interface.*` fields and `policy.allow_implicit_invocation: false`, and its thin workflow resolves route → workflow file → follows it

**Plans**: 4/4 plans complete
Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Wave 1: Wave-0 prereqs — check_grounding dict-fix + scaffold traces subdir + test scaffolds (smoke/skill-schema) + F9 stability fixture

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Wave 2: verify JSON branch (--reqs-format) + deterministic JSON→IEEE-830 render command + F1-F4 verify fixtures

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-03-PLAN.md — Wave 3: trace write (D-05 record + source/statement hash, lockfile) + index update (gap/orphan/stale from traces only) + F10/F12 fixtures

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02-04-PLAN.md — Wave 4: ba-srs-analyze Codex skill + thin workflow (6 routes, CoVe loop) + ba-srs-writer/ba-critic prompts + gates.md + F11 fixture

### Phase 3: ba-mermaid Diagram Operator

**Goal**: A use case or requirement becomes a Mermaid diagram authored MD-inline (no CLI dependency on the default route), each diagram cites the REQ-IDs it depicts so it appears in the traceability matrix, and `mmdc` export is available as an optional route that hard-fails rather than synthesizing when the CLI is missing.
**Depends on**: Phase 2
**Requirements**: MMD-01, MMD-02, MMD-03
**Success Criteria** (what must be TRUE):

  1. Running `ba-mermaid` on a UC/requirement (default route `author`) produces an inline ```mermaid block in a `.md` artifact with no Mermaid CLI invoked
  2. Each produced diagram carries a `req_ids` field, and after `ba-tools index update` those REQ-IDs appear in INDEX.md under the mermaid column (no orphans introduced)
  3. The optional `render` route invokes `mmdc` (resolved `--mermaid-cli` → `$MERMAID_CLI` → PATH → `npx -p @mermaid-js/mermaid-cli mmdc`) to emit `.mmd`/PNG, and hard-fails with a `BaToolsError` (exit 2) when no CLI is found — never producing a synthetic image

**Plans**: TBD
**UI hint**: yes

### Phase 4: ba-mockup Operator

**Goal**: Requirements become a UI mockup at a required `--fidelity` of `html` or `wireframe`, each screen cites the REQ-IDs it realizes so it joins the traceability matrix, and the chosen fidelity determines the artifact form (`.html` file vs inline wireframe blocks).
**Depends on**: Phase 2
**Requirements**: MOCK-01, MOCK-02, MOCK-03
**Success Criteria** (what must be TRUE):

  1. `ba-mockup` requires `--fidelity` and rejects invocation without it; given `--fidelity html` it writes a `.html` artifact and given `--fidelity wireframe` it writes inline wireframe blocks
  2. Each mockup screen carries a `req_ids` field, and after `ba-tools index update` those REQ-IDs appear in INDEX.md under the mockup column (no orphans introduced)
  3. A mockup citing a REQ-ID that does not exist in the registry is surfaced as an orphan by INDEX.md drift detection

**Plans**: TBD
**UI hint**: yes

### Phase 5: ba-uc Conductor + End-to-End Integration

**Goal**: One use case is delivered end-to-end by the `ba-uc` conductor running the three spine operators as a single sequential agent loop (srs-analyze → mermaid → mockup → index) with a Quality gate between steps and full resumability via `uc-status`; this phase doubles as the spine's integration test (resume-from-step, gate-reject, concurrent-write).
**Depends on**: Phase 3, Phase 4
**Requirements**: UC-01, UC-02, UC-03, GATE-03
**Success Criteria** (what must be TRUE):

  1. `ba-uc` (default route `deliver`; routes deliver/resume/status/iterate) takes one use case and produces SRS, mermaid, and mockup artifacts plus an updated INDEX.md in a single sequential loop, with a Quality gate run after each step
  2. When a step's Quality gate fails, the conductor stops at that step and `ba-tools uc-status` reports the failed step as `next_step`; re-running the `resume` route continues from that step rather than restarting the pipeline
  3. Killing the conductor mid-pipeline leaves recoverable state — `ba-tools uc-status` returns the correct single-UC pipeline state and `next_step`, and `resume` completes the remaining steps to a fully traced UC
  4. The Safety gate contract for render/embed steps is defined (render CLI only, path-traversal + injection scan, `.png`/`.svg` extension check) and documented as enforced by the deferred plugins, with no synthetic render path on the spine

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Deterministic ba-tools CLI + Foundational Gates | 7/7 | Complete    | 2026-06-17 |
| 2. ba-srs-analyze + Quality Gate + Traceability Core | 4/4 | Complete    | 2026-06-17 |
| 3. ba-mermaid Diagram Operator | 0/TBD | Not started | - |
| 4. ba-mockup Operator | 0/TBD | Not started | - |
| 5. ba-uc Conductor + End-to-End Integration | 0/TBD | Not started | - |
