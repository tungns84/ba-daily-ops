# Project Research Summary

**Project:** BA Daily Ops (`ba-daily-ops`)
**Domain:** Harness-first BA daily-ops — deterministic CLI + agent skills for SRS/traceability workflow
**Researched:** 2026-07-20
**Confidence:** HIGH

## Executive Summary

BA Daily Ops is a **local-first harness** that wraps the BA artifact loop (use case → SRS → flow → mockup → RTM index) in a provable, resumable workflow. Experts build this class of product by separating probabilistic authoring (agent skills) from deterministic integrity (CLI gates, hashes, schema validation) — the same Plan-Execute-Verify pattern used in production agent systems. The product does not compete on LLM draft speed; it wins on **REQ-ID trace spine**, anti-false-green coverage, and durable `.ba-ops/` file-state that survives chat session death and Git commits.

The recommended approach is a **four-layer architecture**: Cursor Agent Skills (`$ba-*`) for judgment and UX; `ba-tools` (Python 3.12 + Typer) for provable operations with zero network; `.ba-ops/` JSON/Markdown file-state as single source of truth; and an **executable workflow runner** as the sole control plane for route order, gate orchestration, and candidate→canonical promotion. The golden path is exactly one user command — `$ba-deliver run --uc <slug>` — with default profile `light` for pilot adoption. Stack choices are conservative and BRD-aligned: stdlib JSON/hash, jsonschema for registry validation, filelock for atomic writes, subprocess git (not GitPython), and official renderers only (mmdc, draw.io) with hard-fail when missing.

The dominant risks are **architectural, not technological**: LLM gate bypass (prose-as-proof), false-green RTM, and candidate files counted as canonical. Mitigation is structural — runner-owned promotion, coverage policy engine before INDEX semantics, staging under `runs/<id>/candidates/`, and a ≥50-mutation conformance corpus as release blocker. Secondary risks include Windows/UTF-8 pilot friction, ceremony creep into `light` tier, and stakeholder confusion between hash integrity and semantic correctness. Foundation (doctor, installer, CLI contract) and runner must land before any skill claims end-to-end delivery.

## Key Findings

### Recommended Stack

Python-centric deterministic CLI with optional Node/draw.io render toolchain, managed by uv for reproducible CI across Win/macOS/Linux. No databases, no web framework, no LLM frameworks inside `ba-tools` — file-state in `.ba-ops/` is the persistence layer.

**Core technologies:**
- **Python 3.12.x** (min 3.11+): Run `ba-tools` harness — `hashlib.file_digest()` for streaming SHA-256 (NFR-005)
- **Typer 0.27.0**: Multi-command CLI surface (`doctor`, `init`, `verify`, `index`, runner) with typed subcommands and Rich stderr UX
- **jsonschema 4.26.0**: Validate `.ba-ops/` JSON against Draft 2020-12 schemas — structural proof stays in CLI, judgment stays in agent
- **filelock ≥3.20.3**: Cross-platform atomic writes and crash-safe promotion (NFR-010); CVE floor mandatory
- **Cursor Agent Skills**: Chat runtime for `$ba-*` skills; runtime-neutral SKILL.md contract for future porting
- **Node 22.x LTS + @mermaid-js/mermaid-cli 11.16.0**: Official Mermaid render (optional at `light`; required for PNG/SVG export)
- **draw.io Desktop 30.3.14+**: Official BPMN/DOCX diagram export (plugin opt-in; hard-fail if missing when enabled)
- **uv + hatchling + ruff + pytest**: Reproducible deps, packaging, lint, and conformance corpus testing

**Critical version constraints:** filelock ≥3.20.3 (security); no GitPython (subprocess git only); no orjson for canonical hash (stdlib `sort_keys=True`); Pydantic for CLI envelopes only, not business gates.

### Expected Features

**Must have (table stakes):**
- REQ-ID registry (`requirements.json`) with stable IDs — every RTM practice starts here
- SRS pair: canonical JSON + derived IEEE-830 `SRS.md` — no ID invention in Markdown
- Citation-exists gate with ≥12-char verbatim span — anti-hallucination for stated reqs
- Process flow (Mermaid inline) and UI mockup with machine-readable `req_ids` — linked artifacts, not orphan visuals
- RTM INDEX regenerated from registry + trace — `ok` / `gap` / `orphan` / `stale` / `waived` semantics
- End-to-end UC delivery via one command + status + resume — real BA work interrupts mid-flight
- Quality gates with machine-readable evidence — "done" must be inspectable
- Drift/stale detection via hash compare — downstream artifacts flag when source changes
- Profile tier (`light` | `standard` | `strict`) as single ceremony control plane
- Local `.ba-ops/` file-state + doctor + portable installer — chat sessions die, artifacts survive

**Should have (competitive differentiators):**
- Executable workflow runner owns promotion — agent writes candidates only; runner promotes after gate pass (R-1 prevention)
- Coverage policy anti false-green — `ok` only when all required artifacts current + gated; conformance ≥49/50 mutations
- Determinism boundary — zero-network CLI; JSON stdout contract; no business inference in `ba-tools`
- Blind critic with ≤3 fix-review rounds — independent rubric at `standard`+
- Optional plugins (BPMN, backlog/Jira CSV, DOCX) without breaking spine — hard-fail if renderer missing
- Team mode: owner folder + read-only lead report — multi-BA without SaaS
- Skills map (`$ba-*`) over raw CLI for BA UX — golden path docs never require typing `ba-tools`

**Defer (v2+):**
- Strict DOCX publishable bundle + human sign-off manifest — post-PMF client delivery
- Team mode at scale (>5 BA) — beyond v1 assumptions
- Runtime-neutral skill host porting — Cursor is v1 host; contract is portable
- ISO 29148 section-level compliance mode — only when contract demands
- Integrated test-case RTM column — out of BA daily loop v1

### Architecture Approach

Four-layer harness: BA user → Skill layer (judgment, candidates) → `ba-tools` deterministic layer (gates, hash, promote) → `.ba-ops/` file-state (Git-committed). The executable workflow runner is the control plane — not the LLM — and is the only component that marks routes complete and promotes candidate→canonical.

**Major components:**
1. **`$ba-*` skills** — Domain authoring (SRS prose, diagrams, mockups); invoke `ba-tools` per workflow step; never own route order or promotion
2. **`$ba-deliver` conductor** — User-facing golden path entry; delegates to runner + child skills
3. **Executable workflow runner** — Route selection/order, gate orchestration, resume, sole promoter of canonical artifacts
4. **`ba-tools` core** — Provable ops: schema, hash, verify, render, trace, index, path containment, atomic write
5. **`.ba-ops/` file-state** — Config, registry, trace records, derived INDEX, runs/journal, candidates staging

**Key patterns:** Candidate → Gate → Promote on every mutating route; derived views (`SRS.md`, `INDEX.md`) from canonical registries; profile tier drives coverage policy; REQ-ID trace spine from registry through artifact metadata to INDEX rows.

### Critical Pitfalls

1. **LLM gate bypass (prose-as-proof)** — Agent declares "passed" without invoking `ba-tools`. Prevent: runner-only promotion; skill workflows must parse exit code + JSON; gate evidence in `journal.jsonl`, not chat.
2. **False-green RTM** — INDEX shows `ok` when artifacts missing, stale, or un-promoted. Prevent: machine-readable coverage policy; candidate exclusion (BR-007); conformance corpus ≥50 mutations as release blocker.
3. **Markdown-only SRS drift** — Direct `SRS.md` edits break registry spine. Prevent: `requirements.json` canonical; SRS.md render-only; gate fails on orphan REQ-IDs in Markdown.
4. **Candidate treated as canonical** — Skills write to final paths, INDEX counts before gate. Prevent: staging under `runs/<id>/candidates/`; atomic promotion; INDEX updates post-promote only.
5. **Ceremony sneak-back into `light` tier** — Golden path grows beyond 1 command. Prevent: profile-gated features; CI regression on light command count = 1; Appendix D matrix is normative.

## Implications for Roadmap

Based on combined research, recommend **7 vertical-slice phases** — each delivers end-to-end capability for one spine segment before adding ceremony tiers. Do not build DOCX/BPMN/critic/team mode until runner + promote pattern is proven.

### Phase 1: Harness Foundation
**Rationale:** Nothing else can enforce gates without CLI I/O contract, portable paths, and preflight. Doctor/installer must exist before pilot (Windows UTF-8 friction kills adoption).
**Delivers:** `ba-tools` skeleton (Typer CLI, JSON stdout/stderr contract, exit 2 errors); `--repo-root` path containment; `doctor` + `init`; `.ba-ops/` schema layout (`config.json`, `coverage-policy.json`, `business-goals.json`); atomic write + filelock; PowerShell + POSIX installer stubs; doc-vs-help CI hook.
**Addresses:** Setup/health check, local file-state persistence, repo-relative portability, UTF-8 Vietnamese support (table stakes)
**Avoids:** Doc–code–help drift (P6), Windows/UTF-8 friction (P8)
**Uses:** Python 3.12, Typer, filelock, uv/hatchling, rich (stderr only)

### Phase 2: REQ-ID Spine & SRS Pair
**Rationale:** Core product value starts at registry + citation gate. Downstream flow/mockup/INDEX all depend on stable REQ-ID spine.
**Delivers:** `$ba-srs` skill; `requirements.json` schema + jsonschema validation; citation-exists gate (≥12-char verbatim span); Jinja2 SRS render (`SRS.md` derived view); `$ba-srs` workflow with render-after-gate ordering.
**Addresses:** REQ-ID registry, SRS from source, citation/grounding (P1 table stakes)
**Avoids:** Markdown-only SRS drift (P3), unreadable source / fabricated citations (P9)
**Uses:** jsonschema, Jinja2, python-frontmatter (for downstream prep)

### Phase 3: Executable Runner & Conductor
**Rationale:** Highest architectural risk — gate bypass and candidate/canonical bugs force rewrite if bolted on later. Must land before any skill claims end-to-end delivery.
**Delivers:** Executable workflow runner (`ba-tools run`); candidate staging under `runs/<id>/candidates/`; atomic promotion; `STATE.md` + `journal.jsonl`; `$ba-deliver` skill (run/status/resume skeleton); confirmation gate on destructive ops.
**Addresses:** Executable runner + candidate/canonical, resume after interrupt (P1 differentiators)
**Avoids:** LLM gate bypass (P1), candidate treated as canonical (P5)
**Implements:** Runner as sole sequencer; Candidate → Gate → Promote pattern

### Phase 4: Golden Path Artifacts (Light Tier)
**Rationale:** Completes light-tier artifact chain (SRS → flow → mockup → index route) once runner exists. Lock `light` profile behavior when conductor ships.
**Delivers:** `$ba-flow` (Mermaid inline + `req_ids` frontmatter); `$ba-mockup` (html/wireframe + metadata); artifact gates (req_ids resolve to registry); runner route chain for `light` profile; golden path regression test (exactly 1 user command).
**Addresses:** Process flow artifact, UI mockup linked to reqs, golden path one command, profile tier `light`
**Avoids:** Ceremony sneak-back into `light` (P7)
**Uses:** python-frontmatter, beautifulsoup4 (html mockup metadata)

### Phase 5: Coverage Policy & Drift Detection
**Rationale:** False-green destroys trust faster than missing mockup plugin. INDEX logic must not ship before coverage policy engine.
**Delivers:** Hash/trace utilities; trace write + compare; stale detection; `ba-tools index` (INDEX.md generator); coverage policy engine (`ok` vs `gap`/`orphan`/`stale`/`waived`); `$ba-deliver status` with actionable blockers; conformance mutation corpus (≥50 seeded, parallel build).
**Addresses:** RTM/traceability index, cross-artifact REQ-ID spine, drift/stale detection, coverage policy anti false-green
**Avoids:** False-green RTM (P2)
**Implements:** Derived views pattern; REQ-ID trace spine; coverage flow

### Phase 6: Plugins, Standard/Strict Tier & Team Mode
**Rationale:** Optional complexity that depends on spine + coverage being correct. Plugins opt-in per tier; hard-fail if renderer missing.
**Delivers:** `$ba-intake` (elicit/meeting); blind critic (≤3 rounds, `standard`+); `$ba-bpmn` (draw.io CLI); `$ba-backlog` + Jira CSV; `$ba-docx` + MANIFEST (strict); profile `standard`/`strict` coverage matrices; team mode owner guard + read-only `report team`.
**Addresses:** Optional plugins, blind critic, tier extensions, team mode (P2/P3 features)
**Avoids:** Fake render / screenshot fallback (P11), parallel BA state corruption (P10)
**Uses:** Node 22 + mmdc, draw.io Desktop CLI, python-docx

### Phase 7: Pilot Validation & Release Gate
**Rationale:** Set stakeholder expectations; measure rework not just mechanical green; block release on conformance.
**Delivers:** Full installer polish (Windows primary); 3-OS CI matrix; pilot KPI instrumentation (golden path count, RTM completeness, citation integrity); stakeholder readout on hash vs semantic correctness; release gate checklist (≥49/50 mutations, doc-vs-help, false-green = 0).
**Addresses:** Conformance mutation corpus as release blocker; pilot exit criteria
**Avoids:** Hash = correctness fallacy (P4), byte-reproducible LLM expectation mismatch (P12)

### Phase Ordering Rationale

- **Foundation before skills** — doctor, CLI contract, and config portability prevent Windows and doc drift from poisoning everything downstream
- **Spine before conductor** — registry + citation gate must exist before `$ba-deliver` orchestrates routes
- **Runner before golden path completion** — gate bypass and candidate/canonical bugs are architectural; bolting runner on later forces rewrite
- **Artifacts before coverage engine** — need canonical artifacts to trace before INDEX semantics matter
- **Coverage before pilot claims** — false-green destroys trust faster than missing DOCX plugin
- **Plugins and team mode last** — strict deliverables depend on spine + coverage already correct
- **Critical path:** 1 → 2 → 3 → 5 → 7; Phase 4 (flow/mockup) can parallel Phase 5 only if trace schema is stable

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 6 (Plugins):** draw.io headless CI on Linux (`xvfb-run` wrapper), DOCX rId/placeholder replacement specifics, mmdc Puppeteer install footprint on corporate Windows
- **Phase 6 (Team mode):** Owner transfer workflow edge cases, stale filelock recovery after crash
- **Phase 4 (Mockup):** HTML fidelity gate rules vs wireframe Markdown — exact metadata extraction contract

Phases with standard patterns (skip research-phase):
- **Phase 1:** Typer CLI + JSON stdout contract — well-documented Python patterns
- **Phase 2:** jsonschema + Jinja2 render — established; SRS-SPEC is normative
- **Phase 3:** File staging + atomic promote — standard harness pattern (PEV loops)
- **Phase 5:** SHA-256 hash compare + derived view generation — BRD specifies behavior

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Typer/jsonschema/filelock verified on PyPI; BRD-mandated render toolchain; versions checked 2026-07-20 |
| Features | HIGH | BRD v1.0 + PROJECT.md authoritative; competitor/harness patterns cross-checked |
| Architecture | HIGH | Normative BRD/SRS-SPEC; four-layer harness aligns with production agent system literature |
| Pitfalls | HIGH | Grounded in BRD §14 risks R-1…R-12 with acceptance criteria and recovery strategies |

**Overall confidence:** HIGH

### Gaps to Address

- **Cursor Skills host API evolution (R-9):** SKILL.md contract is portable but host invocation details may change — validate during Phase 3 skill integration; keep `.ba-ops/` runtime-agnostic
- **draw.io Desktop on locked corporate laptops:** Plugin hard-fail is correct but pilot may need tier `light` fallback path documented clearly — confirm with pilot BA machines during Phase 1 doctor testing
- **Conformance corpus seed quality:** ≥50 mutations must cover false-green scenarios specifically — plan mutation taxonomy during Phase 5 planning, not ad-hoc
- **Semantic vs mechanical "done" messaging:** Pilot readout materials need explicit OBJ-4 framing — draft during Phase 7 planning to avoid stakeholder expectation mismatch

## Sources

### Primary (HIGH confidence)
- `docs/BRD-v1.0.md` v1.0 — Product intent, BRD-001…028, NFR-001…010, §14 risks, Appendix D tier matrix
- `docs/SRS-SPEC.md` v1.0 — Canonical vs derived SRS, gate ordering (Part D.3)
- `.planning/PROJECT.md` — Core value, tier defaults, out-of-scope boundaries
- `.planning/research/STACK.md` — Technology versions and rationale
- `.planning/research/FEATURES.md` — Table stakes, differentiators, MVP definition
- `.planning/research/ARCHITECTURE.md` — Four-layer harness, build order, patterns
- `.planning/research/PITFALLS.md` — R-1…R-12 prevention strategies, phase mapping

### Secondary (MEDIUM confidence)
- [Harness Engineering for AI Coding Agents (Augment Code)](https://www.augmentcode.com/guides/harness-engineering-ai-coding-agents) — PEV loops, deterministic gates
- [Agentic Harnesses (Medium)](https://medium.com/@balajibal/agentic-harnesses-the-new-infrastructure-layer-for-ai-systems-3939c6fac1a6) — File-state, gates, resume patterns
- [Visure / DocSheets / TestCollab RTM features](https://visuresolutions.com/features/requirements-traceability-matrix-software/) — Industry table stakes for traceability
- [Cursor Agent Skills docs](https://cursor.com/help/customization/skills) — Skill vs script determinism split

### Tertiary (LOW confidence)
- Atlan agent harness anti-patterns — "looks done" outputs; generalized to BA domain from coding-agent literature — validate during Phase 7 pilot

---
*Research completed: 2026-07-20*
*Ready for roadmap: yes*
