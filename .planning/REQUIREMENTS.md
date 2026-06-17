# Requirements: BA Daily Operators

**Defined:** 2026-06-17
**Core Value:** REQ-ID traceability across artifacts — one requirement seen consistently across SRS, diagram, mockup, and backlog, so drift surfaces immediately.

## v1 Requirements

v1 milestone = the daily spine (CodexApp-first). Each maps to a roadmap phase.

### ba-tools CLI (TOOL)

- [x] **TOOL-01**: `ba-tools init <operator>` returns context JSON (config, routes, default_route, state)
- [x] **TOOL-02**: `ba-tools resolve-route <operator>` returns the static DEFAULT_ROUTE only — never infers route from free text
- [x] **TOOL-03**: `ba-tools state update|patch|advance` writes `.ba-ops/STATE.md` guarded by an `O_EXCL` lockfile (stale-lock reclaimed after 10s)
- [x] **TOOL-04**: `ba-tools lint-requirements` flags ambiguity, atomicity, grounding, verifiability, and citation issues
- [x] **TOOL-05**: `lint-requirements` enforces REQ-ID stability — IDs are permanent; it flags a material statement change on an existing ID (never silent renumber)
- [x] **TOOL-06**: `ba-tools verify` gate checks: verbatim citation-exists (≥12-char real substring, **section-scoped**), REQ-ID coverage, hash-match; folds the lint result
- [ ] **TOOL-07**: `ba-tools trace write` records an artifact→REQ-ID mapping plus a statement hash
- [ ] **TOOL-08**: `ba-tools index update` rebuilds `.ba-ops/INDEX.md` and flags gaps, orphans, and stale (source-hash drift)
- [x] **TOOL-09**: `ba-tools uc-status` returns single-UC pipeline state + `next_step` (resumable)
- [x] **TOOL-10**: `ba-tools extract-uc --uc "<spec>"` returns the UC section + parsed identity
- [x] **TOOL-11**: `ba-tools template fill` scaffolds an artifact from `ba-core/templates`
- [x] **TOOL-12**: `ba-tools discovery add|list` captures and lists iteration discoveries
- [x] **TOOL-13**: every success prints UTF-8 JSON to stdout; every `BaToolsError` exits with code 2
- [x] **TOOL-14**: all paths resolve relative to `--repo-root` (git root / cwd) — no hard-coded machine paths; Python resolved via `sys.executable`
- [x] **TOOL-15**: `ba-tools scan --file <f>` runs an advisory prompt-injection scan

### Verification Gates (GATE)

- [ ] **GATE-01**: Quality gate runs `ba-tools verify` + `ba-critic` judgement after an agent produces an artifact
- [x] **GATE-02**: Confirm gate fires before any irreversible/outward step (e.g. overwriting a delivered SRS)
- [ ] **GATE-03**: Safety gate contract defined for render/embed steps (enforced by deferred plugins): render CLI only, path-traversal + injection scan, `.png`/`.svg` extension check
- [x] **GATE-04**: A CI/pre-commit byte-check gate fails if any eager-loaded doc (AGENTS.md / refs) is ≥ 32,768 B (Codex truncates silently)

### SRS Analysis (SRS)

- [ ] **SRS-01**: `ba-srs-analyze` turns sources into atomic, grounded, verifiable requirements (JSON)
- [ ] **SRS-02**: `ba-srs-analyze` emits an SRS/BRD `.md`
- [x] **SRS-03**: every `stated` requirement carries a `source_trace` `{doc, span}`
- [ ] **SRS-04**: `ba-srs-writer` emits the quality-contract schema that `ba-tools verify` gates
- [ ] **SRS-05**: `ba-critic` runs a fresh-context Chain-of-Verification loop (generate per-requirement questions → answer from source independently of the draft → return findings), ≤3 revisions, early-exit on convergence, read-only (never edits)
- [ ] **SRS-06**: `ba-srs-analyze` supports routes extract/draft/lint/verify/full/iterate (default `full`)

### Traceability State (TRACE)

- [x] **TRACE-01**: `.ba-ops/` scaffold exists: PROJECT.md, REQUIREMENTS.md (the REQ-ID registry), INDEX.md, STATE.md, config.json
- [x] **TRACE-02**: `.ba-ops/config.json` feature flags default `true` when missing (absent = enabled)
- [x] **TRACE-03**: every downstream artifact carries a `req_ids` field
- [ ] **TRACE-04**: `INDEX.md` is a traceability matrix: REQ-ID → SRS § → mermaid → mockup → story
- [ ] **TRACE-05**: INDEX flags gaps (missing coverage), orphans (req_ids that don't exist), and stale (source hash changed → re-run needed)

### Diagram — Mermaid (MMD)

- [ ] **MMD-01**: `ba-mermaid` turns a UC/requirement into a Mermaid diagram, MD-inline first
- [ ] **MMD-02**: each diagram cites the REQ-IDs it depicts (`req_ids`)
- [ ] **MMD-03**: `mmdc` render is optional (`.mmd`/PNG); default route `author` has no CLI dependency; export hard-fails if the CLI is missing

### Mockup (MOCK)

- [ ] **MOCK-01**: `ba-mockup` turns requirements into a UI mockup at `--fidelity html|wireframe` (fidelity required)
- [ ] **MOCK-02**: each screen cites the REQ-IDs it realizes (`req_ids`)
- [ ] **MOCK-03**: `html` fidelity writes a `.html` artifact; `wireframe` writes inline blocks

### Conductor (UC)

- [ ] **UC-01**: `ba-uc` delivers ONE use case end-to-end: srs-analyze → mermaid → mockup → index
- [ ] **UC-02**: `ba-uc` runs as a single sequential agent loop with a Quality gate between steps
- [ ] **UC-03**: `ba-uc` is resumable via `uc-status`; routes deliver/resume/status/iterate (default `deliver`)

### Codex Packaging (CDX)

- [ ] **CDX-01**: flat `.agents/skills/ba-*/SKILL.md` layout; frontmatter is `name` + `description` only
- [ ] **CDX-02**: each operator has `agents/openai.yaml` with `interface.*` fields and `policy.allow_implicit_invocation: false` on the conductor and spine
- [ ] **CDX-03**: thin workflows under `ba-core/workflows` resolve route → workflow file → follow it
- [x] **CDX-04**: `AGENTS.md` is Read-by-skills (not root-auto-loaded) and < 32,768 B; DEFAULT workflow < 38,000 B
- [x] **CDX-05**: `ba-tools` JSON output is terse and scannable (explicit `ok`/`failures`, no noise)

## v2 Requirements

Deferred. Tracked, not in the current roadmap.

### Optional Plugins (PLUG)

- **PLUG-01**: `ba-make-diagram` produces a formal BPMN swimlane via draw.io CLI (`.drawio` + PNG)
- **PLUG-02**: `ba-uc-delivery` assembles a stakeholder DOCX with media-replacement (direct OOXML blip `rId` surgery — no native `replace_image()`) + hash-manifest
- **PLUG-03**: `ba-backlog-grooming` splits epics via SPIDR into `stories.json` traced to REQ-IDs
- **PLUG-04**: render/build writes a manifest JSON; pass condition `rendered_sha256 == embedded_sha256`

### Claude Code Transform (V2)

- **V2-01**: install-time transform from Codex-native source to Claude commands/skills
- **V2-02**: Task-subagent spawn wiring (true fresh-context specialists)
- **V2-03**: Claude command frontmatter (`allowed-tools`) + settings.json hooks

## Out of Scope

| Feature | Reason |
|---------|--------|
| Synthetic diagram rendering (Pillow / SVG convert / screenshot / hand-paste) | Forbidden non-negotiable (DESIGN §11); only real render CLIs |
| Bespoke GUI / web dashboard / `.ba-ops/` viewer | UI is in-Codex chat only (DECIDED); effectiveness over looks |
| Implicit invocation on the spine/conductor | Analysis/build path must never auto-trigger; `allow_implicit_invocation: false` |
| DOCX / draw.io machinery on the daily spine | Plugin-only; the daily path is text-first |
| Append-instead-of-replace media in DOCX | Forbidden non-negotiable; must media-replace the placeholder |

## Traceability

Each v1 requirement maps to exactly one phase. Phases derive from the confirmed
build order (DESIGN §10): ba-tools (full) → srs-analyze + traceability core →
mermaid / mockup (independent) → uc conductor.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TOOL-01 | Phase 1 | Complete |
| TOOL-02 | Phase 1 | Complete |
| TOOL-03 | Phase 1 | Complete |
| TOOL-04 | Phase 1 | Complete |
| TOOL-05 | Phase 1 | Complete |
| TOOL-06 | Phase 1 | Complete |
| TOOL-07 | Phase 2 | Pending |
| TOOL-08 | Phase 2 | Pending |
| TOOL-09 | Phase 1 | Complete |
| TOOL-10 | Phase 1 | Complete |
| TOOL-11 | Phase 1 | Complete |
| TOOL-12 | Phase 1 | Complete |
| TOOL-13 | Phase 1 | Complete |
| TOOL-14 | Phase 1 | Complete |
| TOOL-15 | Phase 1 | Complete |
| GATE-01 | Phase 2 | Pending |
| GATE-02 | Phase 1 | Complete |
| GATE-03 | Phase 5 | Pending |
| GATE-04 | Phase 1 | Complete |
| SRS-01 | Phase 2 | Pending |
| SRS-02 | Phase 2 | Pending |
| SRS-03 | Phase 2 | Complete |
| SRS-04 | Phase 2 | Pending |
| SRS-05 | Phase 2 | Pending |
| SRS-06 | Phase 2 | Pending |
| TRACE-01 | Phase 1 | Complete |
| TRACE-02 | Phase 1 | Complete |
| TRACE-03 | Phase 2 | Complete |
| TRACE-04 | Phase 2 | Pending |
| TRACE-05 | Phase 2 | Pending |
| MMD-01 | Phase 3 | Pending |
| MMD-02 | Phase 3 | Pending |
| MMD-03 | Phase 3 | Pending |
| MOCK-01 | Phase 4 | Pending |
| MOCK-02 | Phase 4 | Pending |
| MOCK-03 | Phase 4 | Pending |
| UC-01 | Phase 5 | Pending |
| UC-02 | Phase 5 | Pending |
| UC-03 | Phase 5 | Pending |
| CDX-01 | Phase 2 | Pending |
| CDX-02 | Phase 2 | Pending |
| CDX-03 | Phase 2 | Pending |
| CDX-04 | Phase 1 | Complete |
| CDX-05 | Phase 1 | Complete |

**Coverage:**

- v1 requirements: 44 total (registry actual count; the prior "35" header figure was a stale estimate — corrected here)
- Mapped to phases: 44 ✓
- Unmapped: 0 ✓
- Per phase: Phase 1 = 19, Phase 2 = 15, Phase 3 = 3, Phase 4 = 3, Phase 5 = 4

## Open Decisions (resolved with recommended defaults; revisit in phase discussion)

| # | Decision | Default applied | Where |
|---|----------|-----------------|-------|
| 1 | Citation-exists match scope | **Section-scoped** (closes boilerplate-gaming gap); `--cite-scope section\|document` override | TOOL-06 |
| 2 | `WARN_INJECTION` advisory vs hard gate | **Advisory in v1**; promote to hard gate later for external-source `stated` reqs | TOOL-15 / GATE-01 |
| 3 | `ba-critic` loop termination | **Early-exit on convergence**, logged ("passed early" vs "passed after N") | SRS-05 |
| 4 | REQ-ID stability lint phase | **Phase 1** (with a renumbered-requirements fixture) | TOOL-05 |

---
*Requirements defined: 2026-06-17*
*Last updated: 2026-06-17 after roadmap creation (traceability mapped, coverage corrected to 44)*
