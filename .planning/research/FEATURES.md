# Feature Research

**Domain:** BA workflow harness — daily artifact loop (UC → SRS → flow → mockup → trace)
**Researched:** 2026-07-20
**Confidence:** HIGH (BRD v1.0 + PROJECT.md are authoritative; competitor/harness patterns cross-checked via industry RTM and agent-harness literature)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist in any BA daily-ops or requirements workflow product. Missing these = product feels incomplete or unusable for handoff.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **REQ-ID registry** — stable, unique IDs per requirement | Every RTM/SRS practice starts with identifiable requirements; IDs must survive edits (BRD-001, US-01) | MEDIUM | Canonical `requirements.json`; split/merge/rename only via explicit migration with history |
| **SRS from source** — atomic, testable requirements | BA daily loop begins with structured requirements, not free-form notes (US-01, BRD-006) | HIGH | Pair: `requirements.json` (canonical) + `SRS.md` (IEEE-830 derived view); Markdown must not invent IDs |
| **Citation / grounding for stated requirements** | Stakeholders and auditors expect trace to source text, not hallucinated reqs (BRD-007) | MEDIUM | `stated` reqs need `source_trace` with ≥12-char verbatim span in declared section; gate hard-fails on miss |
| **Process flow artifact** — at least lightweight diagram | BA deliverables always include “how it works”; flow is table stakes in every UC pack (BRD-008, US-02) | MEDIUM | Mermaid inline in Markdown with `req_ids` frontmatter; author path must not require render CLI |
| **UI mockup linked to requirements** | Mockups without REQ linkage are orphan visuals; dev/PO expect mapping (BRD-009, US-02) | MEDIUM | Fidelity `html` or `wireframe`; machine-readable `req_ids`; no references outside registry |
| **RTM / traceability index** | Industry standard: gap reports, coverage visibility, handoff checklist (BRD-003; Visure, DocSheets, TestCollab all lead with RTM) | HIGH | Regenerated `.ba-ops/INDEX.md` — not hand-edited source of truth; states `ok` / `gap` / `orphan` / `stale` / `waived` |
| **Cross-artifact REQ-ID spine** | Core BA pain: SRS, diagram, mockup drift silently (US-02, OBJ-2) | HIGH | Spine: SRS → flow/BPMN → mockup → (optional backlog) → INDEX; backlog column only when artifact exists |
| **End-to-end UC delivery orchestration** | Users expect “run workflow for this use case,” not memorize step order (US-03, BRD-010) | HIGH | `$ba-deliver run --uc <slug>` as single user-facing entry; internal route order enforced by runner |
| **Workflow status visibility** | Long artifact chains need “where am I?” without reading logs (BRD-011) | MEDIUM | `$ba-deliver status` — per-route, per-gate, per-artifact durable state |
| **Resume after interrupt** | Real BA work stops mid-flight; rerunning from scratch wastes time and risks overwrite (US-07, BRD-011) | HIGH | `$ba-deliver resume` continues first incomplete step; must not re-promote completed artifacts when inputs unchanged |
| **Quality gates before handoff** | “Done” must mean something inspectable; spreadsheets fail because checks are manual (BRD-016) | HIGH | Per-artifact gates: schema, trace, atomicity, ambiguity, verifiability; machine-readable gate evidence |
| **Drift / stale detection** | When source or reqs change, downstream artifacts must flag obsolescence (BRD-004, US-02) | HIGH | Hash compare source, canonical statement, gate evidence, artifacts; stale excludes valid coverage until rebuild |
| **Profile / tier ceremony control** | Small tasks vs client delivery need different weight without separate products (§5.1, BRD-028) | MEDIUM | Single control plane: `light` \| `standard` \| `strict` in `.ba-ops/config.json`; drives coverage + gates |
| **Local file-state persistence** | Chat sessions die; BA artifacts must survive restart and Git commit (BRD-021) | MEDIUM | `.ba-ops/` text/JSON state; runtime-agnostic from chat host |
| **Setup / health check** | BA is not a developer; broken env = abandonment before value (BRD-019, BRD-020) | LOW | `ba-tools doctor` + one-command portable installer; distinguishes required vs plugin deps |
| **UTF-8 Vietnamese artifact support** | Target users produce Vietnamese BA docs (NFR-008) | LOW | Artifacts, templates, CLI JSON must preserve Vietnamese; Windows UTF-8 verified |
| **Repo-relative portability** | Same project must open on another machine without path surgery (OBJ-5, NFR-003) | MEDIUM | All business paths resolve `--repo-root`; no absolute paths in committed config |

### Differentiators (Competitive Advantage)

Features that set BA Daily Ops apart from generic LLM chat, spreadsheet RTMs, and heavyweight ALM suites. Align with Core Value: **traceability spine + provable integrity**.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Golden path = exactly one user command** | ChatGPT/Jira/Visure require many clicks or prompts; adoption hinge for busy BA (US-03, NFR-002) | HIGH | `$ba-deliver run --uc <slug>` only; setup/doctor/init excluded from count; tier `light` regression-guarded |
| **Harness-first integrity (70/30 split)** | LLM wins draft speed; product wins durable file-state, hash, gates — what chat cannot retain (§1, §6) | HIGH | Position explicitly: compete on integrity, not prose latency |
| **Deterministic `ba-tools` + judgment boundary** | Auditable split: CLI proves file/hash/schema; agent owns analysis/MoSCoW (NFR-006, BRD-027) | HIGH | Zero-network CLI; JSON stdout contract; no business inference in CLI |
| **Executable workflow runner owns promotion** | Prevents LLM “I passed the gate” bypass — top failure mode R-1 | HIGH | Agent writes **candidate** only; runner alone promotes to **canonical** after gate pass; atomic promotion |
| **Coverage policy anti false-green** | Spreadsheet RTMs and lightweight tools often show green while artifacts missing (BRD-026, US-08, R-2) | HIGH | `ok` only when all required applicable artifacts current + gated; conformance corpus ≥49/50 mutations |
| **Hash-stable integrity, not byte-repro LLM** | Honest model: prove relationships and drift, not identical prose reruns (OBJ-4, NFR-005) | MEDIUM | Hash-stable after accept + freeze; sets correct stakeholder expectations |
| **Tier as single ceremony control plane** | ALM tools overload small tasks; chat has no ceremony when you need it (§5.1, BR-006) | MEDIUM | Same spine, different depth: light = verify/lint; strict = readiness + DOCX + sign-off |
| **Citation-exists gate (verbatim span)** | Cheap anti-hallucination vs semantic-only AI reviewers (BRD-007, R-7) | MEDIUM | Substring must exist in declared source section; lists violating REQ-IDs on fail |
| **Blind critic with bounded loops** | Author self-review is weak; unbounded AI review never finishes (BRD-018) | HIGH | Independent rubric critic; max 3 fix–review rounds; open issues → human |
| **Optional plugins without breaking spine** | BPMN, DOCX, backlog, Jira CSV add depth without forcing every UC (BRD-012–014) | HIGH | Plugins opt-in per tier/policy; hard-fail if renderer missing — no fake renders |
| **Official render only (Mermaid CLI, draw.io)** | Screenshot/SVG hacks break audit trust (BR-002, R-4) | MEDIUM | Export fails closed; inline Mermaid text still shippable when render not required |
| **Team mode: owner folder + read-only lead report** | Multi-BA repos need isolation without SaaS (BRD-023–025) | HIGH | Cross-owner write blocked before first byte; `report team` aggregates coverage read-only |
| **Confirmation gate on destructive ops** | Prevents accidental canonical loss during iterative BA work (BRD-015) | LOW | Overwrite, force rebuild, REQ-ID change, publish require explicit confirm |
| **Conformance mutation corpus** | Drift detection quality is invisible until regressions (§13.4) | HIGH | ≥50 seeded mutations; ≥49/50 detect rate; false-green = release blocker |
| **Skills map (`$ba-*`) over raw CLI for BA** | Hides `ba-tools` complexity; CLI remains for CI/script (§5.2, R-6) | MEDIUM | Chat-triggerable skills; golden path docs never require BA to type `ba-tools` |
| **Waived vs ok semantic honesty** | Enterprise tools often hide exceptions; leads need truth for handoff (BR-006, §16.5) | MEDIUM | `waived` never displayed as `ok`; waiver cannot mask `stale` |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem attractive but conflict with harness-first positioning, BRD scope, or proven failure modes.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **“Fastest draft” LLM competition** | Stakeholders compare to ChatGPT one-shot | Undermines 70/30 value; race to bottom on prose quality (Out of Scope §7.1) | Use external LLM for ad-hoc drafts; harness for integrity loop |
| **Byte-reproducible LLM output** | Auditors ask “same input → same document?” | Impossible for judgment prose; false promise creates distrust (OBJ-4, R-12) | Hash-stable canonical after human accept + freeze; drift detection on relationships |
| **Multi-user SaaS / shared backend v1** | IT wants central admin | Contradicts local-first, Git-native `.ba-ops/` model (Out of Scope) | Team mode via owner folders + read-only aggregate report |
| **Built-in OCR / scan ingestion** | Messy inputs arrive as PDF scans | Unreliable citations; scope explosion (Out of Scope, R-7) | OCR upstream; `doctor` warns non-extractable sources; citation gate fails closed |
| **Semantic “correctness” from gate pass** | Desire to automate sign-off | Gates prove mechanical integrity, not business truth (BR-008, R-10) | Human UAT every tier; BA Lead sign-off in `strict` manifest |
| **Agent-declared gate pass without CLI** | Faster-looking workflows in demos | False confidence; breaks audit trail (R-1, BRD-027) | Executable runner + exit code 2 on fail; skill workflow must invoke `ba-tools` |
| **Manual INDEX editing** | Quick fix for one RTM cell | Becomes stale source of truth; destroys regenerability (BRD-003) | Fix artifacts/registry; regenerate INDEX from trace |
| **Screenshot / synthetic BPMN render fallback** | draw.io install blocked on locked laptops | Non-auditable artifacts; false “rendered” state (BR-002, R-4) | Tier `light` Mermaid inline; plugin hard-fail with install guidance |
| **Auto-detect profile tier from source** | “Smart” product feel | Wrong ceremony for task; violates explicit lead choice (§12.2 assumption 6) | BA Lead sets `profile` in config; tier gates documented in matrix |
| **Universal strict pipeline for all UCs** | One standard looks simpler | Kills adoption on small tasks; golden path >1 command (R-11) | Default `light`; escalate tier per project/milestone |
| **Waiver that hides stale/gap** | Pressure to ship with known drift | Handoff incidents; false-green (BRD-026, AC-BRD-026-03) | Waivers explicit, expiring, labeled `waived`; stale always visible |
| **Real-time collaborative editing** | Google Docs expectation | Conflicts with owner-folder guard and atomic promotion (R-8) | Git + owner roots; lead read-only report |
| **Embedded cloud LLM in `ba-tools`** | Single-vendor simplicity | Breaks zero-network determinism boundary (NFR-009) | Org-chosen agent runtime; `ba-tools` stays offline |
| **Backlog as mandatory spine artifact** | Dev teams want stories always | Over-ceremony for light tier; not every UC needs Jira export (BRD-003) | Optional `$ba-backlog`; INDEX column appears only when present |
| **Rich WYSIWYG BA IDE** | Familiarity with Word/Confluence | Huge UX scope; distracts from trace spine | Markdown/HTML artifacts + optional DOCX plugin at `strict` |
| **Vanity adoption KPIs (≥90% satisfaction)** | Executive dashboards | Misleading at n≤2 pilot; hides raw counts (§13.1) | Report m/n paired baselines and conformance metrics |

## Feature Dependencies

```
[Portable repo config + .ba-ops/ file-state]
    └──requires──> [Doctor / installer]
                       └──requires──> [CLI JSON contract]

[REQ-ID registry (requirements.json)]
    └──requires──> [SRS skill + citation-exists gate]
                       └──requires──> [Source intake (text-ready)]

[Machine-readable req_ids on artifacts]
    └──requires──> [REQ-ID registry]

[Flow / mockup skills]
    └──requires──> [REQ-ID registry]
    └──requires──> [Machine-readable req_ids on artifacts]

[Drift / stale detection]
    └──requires──> [Hash trace records]
    └──requires──> [Canonical promotion (runner)]

[RTM INDEX]
    └──requires──> [REQ-ID registry]
    └──requires──> [Trace records + coverage policy]
    └──requires──> [Drift / stale detection]

[Coverage policy (anti false-green)]
    └──requires──> [Profile tier config]
    └──requires──> [RTM INDEX semantics]

[Golden path one command]
    └──requires──> [Deliver conductor]
    └──requires──> [Executable workflow runner]
    └──requires──> [Gate chain per route]
    └──requires──> [Status + resume]

[Deliver conductor]
    └──requires──> [SRS → flow → mockup route chain (tier-dependent)]
    └──requires──> [INDEX regeneration]

[Executable workflow runner]
    └──requires──> [Candidate vs canonical model]
    └──requires──> [Gate evidence store]
    └──requires──> [Journal / STATE for resume]

[Blind critic]
    └──requires──> [Standard or strict profile]
    └──enhances──> [SRS / flow / mockup quality]

[BPMN plugin]
    └──requires──> [Flow logical model + draw.io CLI]
    └──enhances──> [Process artifact depth]

[DOCX delivery plugin]
    └──requires──> [Strict readiness + current artifacts]
    └──requires──> [MANIFEST hash]

[Backlog / Jira CSV plugin]
    └──requires──> [REQ-ID registry]
    └──enhances──> [Dev handoff] (optional spine)

[Team mode owner guard]
    └──requires──> [owner_id in config]
    └──enhances──> [Multi-BA repos at strict]

[Team read-only report]
    └──requires──> [Team mode owner guard]
    └──requires──> [RTM INDEX per root]

[Conformance mutation corpus]
    └──requires──> [Drift + INDEX + coverage policy]
    └──validates──> [Anti false-green differentiator]
```

### Dependency Notes

- **REQ-ID registry requires SRS skill:** Registry is created/updated through `$ba-srs`; downstream artifacts only reference existing IDs (BRD-002 orphan detection).
- **Golden path requires executable runner:** Without runner-owned promotion, LLM can skip gates — negates core differentiator (BRD-027, R-1).
- **INDEX requires coverage policy:** Status `ok` is meaningless without tier-aware required artifact kinds (BRD-026).
- **Resume requires journal + hash snapshots:** Resume logic depends on knowing last promoted canonical hashes (AC-BRD-027-03).
- **DOCX plugin requires strict readiness chain:** Publishable bundle depends on assert-readiness + non-stale inputs (BRD-013, Appendix C.3).
- **Blind critic conflicts with light tier default:** Critic is optional at `light` by design — forcing it breaks US-04 and golden path ceremony budget (R-11).
- **Team write guard conflicts with shared-folder editing:** Any feature allowing cross-owner mutation undermines BRD-024 — use owner transfer workflow instead.

## MVP Definition

### Launch With (v1 — tier `light` pilot)

Minimum to validate harness-first value on 1–2 BA, 10 UC, golden path = 1 command.

- [ ] **REQ-ID registry + SRS pair** — spine exists; US-01 satisfied
- [ ] **Citation-exists gate** — stated reqs grounded; 0 invalid citations at handoff
- [ ] **Mermaid inline flow + mockup (html/wireframe)** — US-02 spine for light tier
- [ ] **Drift detection (stale)** — hash mismatch surfaces immediately
- [ ] **RTM INDEX with gap/orphan/stale/waived** — US-08; no false-green
- [ ] **Coverage policy for `light`** — backlog not mandatory; mockup/SRS/flow required per policy
- [ ] **`$ba-deliver run` + status + resume** — US-03, US-07; one user command
- [ ] **Executable workflow runner + candidate/canonical** — BRD-027; blocks gate bypass
- [ ] **`.ba-ops/` file-state + doctor + installer** — onboarding ≤60 min median target
- [ ] **Portable `--repo-root` paths + UTF-8 VI** — cross-machine pilot ready

### Add After Validation (v1.x — `standard` / plugins)

Once light pilot hits RTM 10/10 and conformance ≥49/50.

- [ ] **`$ba-intake` (elicit/meeting)** — US-05; analysis package for standard+
- [ ] **Blind critic (≤3 rounds)** — US-05 quality depth
- [ ] **Optional BPMN plugin** — when client needs formal notation
- [ ] **`$ba-backlog` + Jira CSV** — dev handoff acceleration; still optional in INDEX
- [ ] **Profile `standard` coverage policy** — readiness basics without full strict ceremony

### Future Consideration (v2+)

Defer until strict tier proven and team mode stable.

- [ ] **Strict DOCX publishable bundle + human sign-off manifest** — US-06; client-facing delivery
- [ ] **Team mode at scale (>5 BA)** — beyond v1 scale assumptions
- [ ] **Runtime-neutral skill host porting** — BRD footnote [^1]; not blocking v1 Cursor host
- [ ] **ISO 29148 section-level compliance mode** — only when contract demands (Appendix E)
- [ ] **Integrated test-case RTM column** — TestCollab-style bidirectional test trace; out of BA daily loop v1

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| REQ-ID registry + SRS pair | HIGH | HIGH | P1 |
| RTM INDEX + coverage policy | HIGH | HIGH | P1 |
| Golden path `$ba-deliver run` | HIGH | HIGH | P1 |
| Executable runner + candidate/canonical | HIGH | HIGH | P1 |
| Drift / stale detection | HIGH | MEDIUM | P1 |
| Citation-exists gate | HIGH | MEDIUM | P1 |
| Flow (Mermaid inline) + mockup | HIGH | MEDIUM | P1 |
| Status + resume | HIGH | MEDIUM | P1 |
| Doctor + installer + `.ba-ops/` | HIGH | MEDIUM | P1 |
| Profile tier `light` | HIGH | LOW | P1 |
| Confirmation gate | MEDIUM | LOW | P1 |
| `$ba-intake` | MEDIUM | MEDIUM | P2 |
| Blind critic | MEDIUM | HIGH | P2 |
| BPMN plugin | MEDIUM | HIGH | P2 |
| Backlog / Jira CSV | MEDIUM | MEDIUM | P2 |
| Profile `standard` | MEDIUM | MEDIUM | P2 |
| DOCX + MANIFEST strict bundle | MEDIUM | HIGH | P3 |
| Team owner guard + report | MEDIUM | HIGH | P3 |
| Profile `strict` + readiness asserts | MEDIUM | HIGH | P3 |
| Conformance mutation corpus (50+) | HIGH | HIGH | P1 (release gate, parallel to pilot) |

**Priority key:**
- P1: Must have for launch / pilot exit criteria
- P2: Should have after light tier validated
- P3: Strict / enterprise ceremony — post-PMF

## Competitor Feature Analysis

| Feature | Spreadsheet / Confluence RTM | ALM (Visure, DocSheets, Jira+plugins) | LLM chat (ChatGPT, Copilot) | BA Daily Ops approach |
|---------|------------------------------|----------------------------------------|-----------------------------|------------------------|
| RTM / coverage view | Manual matrix; stale quickly | Real-time bidirectional trace; audit exports | None persistent | Regenerated `INDEX.md` from registry + trace; anti false-green |
| SRS authoring | Manual templates | Built-in RM modules | Fast draft, no stable IDs | `requirements.json` canonical + derived `SRS.md` |
| Diagrams | Paste images | Integrated modeling | Mermaid in chat, no REQ linkage | Mermaid inline + optional BPMN via official CLI |
| Mockups | External Figma + manual map | Optional integrations | HTML in chat | REQ-tagged html/wireframe in repo |
| Drift detection | Human diff | Change impact analysis | None | Hash-based stale flags across spine |
| Workflow orchestration | Checklists | Configurable ALM workflows | User remembers prompts | One command conductor + enforced runner |
| Quality gates | Review meetings | Compliance workflows | Self-assessed | Deterministic gates + blind critic (tiered) |
| Portability | File copy | Server/cloud account | Session-bound | Git-native `.ba-ops/`, `--repo-root` |
| Speed to first draft | Slow | Slow (setup heavy) | Fastest | Accept LLM speed externally; win on integrity loop |
| Multi-BA governance | Access folders | RBAC, roles | None | Owner folder write guard + read-only team report |
| Backlog / Jira | Manual CSV | Native integrations | Ad-hoc stories | Optional `$ba-backlog` plugin; not spine-required |

## Sources

- **Authoritative:** `docs/BRD-v1.0.md` v1.0 (§5–§8, §11–§13, Appendices C–D) — BRD-001…028, US-01…08
- **Authoritative:** `.planning/PROJECT.md` — core value, tier defaults, out-of-scope boundaries
- **Industry RTM:** [Visure RTM](https://visuresolutions.com/features/requirements-traceability-matrix-software/), [DocSheets RTM](https://docsheets.com/requirements-traceability-matrix.html), [TestCollab RTM](https://testcollab.com/features/requirements-traceability-matrix) — table stakes: bidirectional trace, gap reports, impact analysis
- **BA practice:** [Requirements Traceability Matrix (Medium / Analyst's Corner)](https://medium.com/analysts-corner/ba-techniques-requirements-traceability-matrix-1e1f65d6e8d3) — REQ → deliverable mapping expectation
- **Agent harness patterns:** [Agentic Harnesses (Medium)](https://medium.com/@balajibal/agentic-harnesses-the-new-infrastructure-layer-for-ai-systems-3939c6fac1a6), [Harness Engineering (deepset)](https://www.deepset.ai/blog/harness-engineering), [PhaseDev](https://github.com/alexkorn22/phasedev-ai-framework), [Coding Agent Harness](https://github.com/LnYo-Cly/coding-agent-harness) — file-state, gates, resume, evidence-backed done
- **Standards referenced in BRD:** IEEE 830 (SRS structure), BPMN 2.0 subset, INVEST/SPIDR (backlog plugin)

---
*Feature research for: BA Daily Ops (`ba-daily-ops`)*
*Researched: 2026-07-20*
