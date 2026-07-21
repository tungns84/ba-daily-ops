# Roadmap: BA Daily Ops

## Overview

BA Daily Ops ships as a harness-first vertical MVP: deterministic `ba-tools` + `.ba-ops/` file-state + executable workflow runner + `$ba-*` skills. Seven phases follow the REQ-ID trace spine from portable foundation through SRS pair, runner/conductor, light-tier artifacts, coverage/drift integrity, tier/plugin extension readiness, and pilot release gate. Each phase delivers end-to-end capability before adding ceremony.

## Phases

- [ ] **Phase 1: Harness Foundation** - Portable CLI, doctor, installer, and `.ba-ops/` file-state
- [ ] **Phase 2: REQ-ID Spine & SRS Pair** - Canonical registry, citation gate, derived SRS
- [ ] **Phase 3: Executable Runner & Conductor** - Runner-owned promotion, `$ba-deliver` run/status/resume
- [ ] **Phase 4: Golden Path Artifacts (Light Tier)** - Flow, mockup, skills, one-command golden path
- [ ] **Phase 5: Coverage Policy & Drift Detection** - INDEX semantics, stale detection, anti false-green
- [ ] **Phase 6: Plugins, Standard/Strict & Team Mode** - Tier extension points and v2 plugin scaffolding
- [ ] **Phase 7: Pilot Validation & Release Gate** - Conformance corpus, performance gate, pilot exit

## Phase Details

### Phase 1: Harness Foundation

**Goal**: BA can bootstrap a portable, healthy harness workspace on any supported OS
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06, NFR-02, NFR-03, NFR-04, NFR-05
**Success Criteria** (what must be TRUE):

  1. BA runs one-command installer (PowerShell or POSIX) without machine-specific paths and gets a working `ba-tools` on PATH
  2. `ba-tools doctor` reports pass/fail for Python, UTF-8, repo layout, and optional dependencies with actionable fixes
  3. `ba-tools init` creates `.ba-ops/` with `config.json`, `coverage-policy.json`, and `business-goals.json`
  4. Every successful `ba-tools` command emits exactly one JSON object on stdout; errors emit JSON on stderr with exit code 2
  5. Vietnamese UTF-8 text round-trips through CLI I/O; all business paths resolve under `--repo-root` with traversal blocked

**Plans**: 2/11 plans executed

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Approve binary-only dependency closures for every supported target

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Create exact package version, target-aware locks, locked dev interpreter, and RED skeleton

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-03-PLAN.md — Make the CLI-to-contained-state walking skeleton green

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 01-04-PLAN.md — Harden dependency, process, zero-network, and UTF-8 contracts
- [ ] 01-05-PLAN.md — Prove path containment, native locking, atomicity, and recovery

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 01-06-PLAN.md — Complete schema-backed init, repair, and invalid-state preservation
- [ ] 01-07-PLAN.md — Install exact-version local generations through PowerShell 5.1 and POSIX launchers

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 01-08-PLAN.md — Report complete ordered pre/post-init doctor diagnostics

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 01-09-PLAN.md — Build offline smoke and least-privilege ordinary CI workflow

**Wave 8** *(blocked on Wave 7 completion)*

- [ ] 01-10-PLAN.md — Verify an actual successful exact-commit six-job CI run

**Wave 9** *(blocked on Wave 8 completion)*

- [ ] 01-11-PLAN.md — Verify exact Windows 10/PowerShell 5.1 and macOS 12 hosts

### Phase 2: REQ-ID Spine & SRS Pair

**Goal**: BA can author a canonical requirements registry with grounded SRS derived view
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: TRACE-01, TRACE-02, SRS-01, SRS-02, SRS-03, SRS-04
**Success Criteria** (what must be TRUE):

  1. BA invokes `$ba-srs` and produces `requirements.json` with stable, unique REQ-IDs tied to use case source
  2. `SRS.md` regenerates from registry only — no REQ-ID invented or edited directly in Markdown
  3. Citation-exists gate rejects stated REQs lacking a ≥12-character verbatim span in declared source section
  4. `ba-tools verify` and `lint-requirements` pass on a valid registry and fail with schema/grounding errors on invalid input
  5. Re-rendering `SRS.md` from the same registry input yields byte-identical output

**Plans**: TBD

### Phase 3: Executable Runner & Conductor

**Goal**: BA can start, inspect, and resume a gated delivery route without LLM bypass of promotion
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: RUN-01, RUN-02, RUN-03, RUN-04, RUN-05, RUN-06
**Success Criteria** (what must be TRUE):

  1. Executable workflow runner owns route order, gate orchestration, and sole candidate→canonical promotion
  2. Skill output lands under `runs/<id>/candidates/` until gates pass; candidates never count toward coverage
  3. `$ba-deliver run --uc <slug>` orchestrates srs → flow → mockup → index and stops at first gate failure without promoting failed artifacts
  4. `$ba-deliver status` shows verifiable route, gate, and artifact state a human can audit
  5. `$ba-deliver resume` continues from the first incomplete step without re-promoting completed artifacts; destructive ops require confirmation

**Plans**: TBD

### Phase 4: Golden Path Artifacts (Light Tier)

**Goal**: BA completes light-tier UC delivery through skills with one user-facing command
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: ART-01, ART-02, ART-03, SKILL-01, SKILL-02, SKILL-03
**Success Criteria** (what must be TRUE):

  1. `$ba-flow` produces Mermaid inline Markdown with machine-readable `req_ids` frontmatter resolving to registry
  2. `$ba-mockup` produces html or wireframe with machine-readable REQ-ID metadata linked to registry
  3. Artifact gates reject orphan `req_ids` not present in canonical registry
  4. Golden path docs guide BA through `$ba-deliver`, `$ba-srs`, `$ba-flow`, `$ba-mockup` without typing `ba-tools` directly
  5. Default profile is `light`; delivering a UC requires exactly one user command (`$ba-deliver run --uc <slug>`, excluding doctor/init)

**Plans**: TBD
**UI hint**: yes

### Phase 5: Coverage Policy & Drift Detection

**Goal**: BA sees truthful RTM status — drift and gaps surface immediately, never hidden as ok
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: TRACE-03, TRACE-04, COV-01, COV-02
**Success Criteria** (what must be TRUE):

  1. `.ba-ops/INDEX.md` regenerates from registry + trace with ok/gap/orphan/stale/waived per REQ
  2. A REQ shows `ok` only when all profile-required artifacts exist, are current, and passed gates
  3. Hash drift on source or artifact marks downstream entries `stale` and excludes them from ok coverage
  4. `waived` displays distinctly from `ok`; a waiver never masks stale or missing artifacts
  5. `$ba-deliver status` lists actionable blockers (gap, orphan, stale) with enough context to fix

**Plans**: TBD

### Phase 6: Plugins, Standard/Strict & Team Mode

**Goal**: Harness exposes tier and plugin extension points without breaking light-tier golden path
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: (none — v2 tier/plugin/team requirements deferred; see REQUIREMENTS.md v2)
**Success Criteria** (what must be TRUE):

  1. Profile tier matrix documents light vs standard vs strict ceremony deltas aligned with BRD Appendix D
  2. Plugin registration hooks exist for BPMN, backlog, DOCX, and intake with hard-fail when enabled renderer is missing
  3. Standard/strict coverage policy extensions load without altering default `light` golden path command count
  4. Team mode owner-guard and read-only report interfaces are stubbed with clear v2 activation path
  5. Light-tier pilot workflow remains fully functional with zero v2 plugins enabled

**Plans**: TBD

### Phase 7: Pilot Validation & Release Gate

**Goal**: Pilot BA can ship a UC handoff meeting conformance, performance, and stakeholder expectations
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: COV-03, NFR-01
**Success Criteria** (what must be TRUE):

  1. Conformance mutation corpus (≥50 seeded cases) detects ≥49/50 injected defects with zero false-green blockers
  2. `ba-tools verify`, trace, and index complete in ≤3s at 200 REQs without invoking renderer or LLM
  3. Full installer and 3-OS CI matrix pass on Windows (primary), macOS, and Linux
  4. Pilot KPI instrumentation reports golden path command count, RTM completeness, and citation integrity per UC
  5. Stakeholder readout distinguishes hash/trace integrity from semantic correctness — human sign-off expectations are explicit

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Harness Foundation | 2/11 | In Progress|  |
| 2. REQ-ID Spine & SRS Pair | 0/TBD | Not started | - |
| 3. Executable Runner & Conductor | 0/TBD | Not started | - |
| 4. Golden Path Artifacts (Light Tier) | 0/TBD | Not started | - |
| 5. Coverage Policy & Drift Detection | 0/TBD | Not started | - |
| 6. Plugins, Standard/Strict & Team Mode | 0/TBD | Not started | - |
| 7. Pilot Validation & Release Gate | 0/TBD | Not started | - |
