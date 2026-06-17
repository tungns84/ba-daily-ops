# Feature Research

**Domain:** Requirements-engineering / BA tooling — SRS/BRD generator operator suite
**Researched:** 2026-06-17
**Confidence:** HIGH (design spec + IEEE/ISO standards review + CoVe literature + Mermaid/mockup domain)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features a BA tooling suite must have. Missing any of these means the product feels broken or incomplete compared to what even basic ALM tools (Jira, Azure DevOps) already do.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Requirement atomicity enforcement** | Every serious RE methodology requires one requirement = one testable statement. Compound requirements are a primary source of sprint failures. | MEDIUM | `ba-tools lint-requirements` flags `AND`/`OR`-compound statements; agent rewrites. |
| **Ambiguity flag** | Words like "shall be fast", "user-friendly", "appropriate" are classic RE anti-patterns. BAs learn this day one. | MEDIUM | Lint pass over vague qualifiers; flag without blocking (advisory at lint, hard block at verify). |
| **Verifiability / testability check** | IEEE 830 §3.5 mandates each requirement be verifiable. A requirement without a pass/fail criterion cannot be tested. | MEDIUM | Lint for unmeasurable statements ("system should perform well"); require acceptance-criteria field in schema. |
| **SRS/BRD section structure (IEEE 830 / ISO 29148 style)** | Stakeholders recognize the standard sections; missing them breaks sign-off workflows. Sections: Introduction, Overall Description, Functional Requirements, Non-Functional Requirements, Constraints, Appendices. | LOW | Agent writes `.md` sections from template; `ba-tools template fill` scaffolds skeleton. |
| **REQ-ID assignment and registry** | Every ALM tool assigns IDs; without them cross-artifact references are prose noise. | LOW | Schema requires `req_id`; `ba-tools lint-requirements` flags missing IDs; REQUIREMENTS.md is the registry. |
| **Source-grounded requirements** | Requirements that cannot be traced to a source document are guesses. The industry term is "gold-plating". | HIGH | `source_trace.doc` + `source_trace.span` fields in requirements JSON; citation-exists check in `ba-tools verify`. |
| **Traceability matrix (RTM/INDEX)** | ISO 29148 and IEEE 830 both specify traceability. ALM tools (Perforce Helix RM, Jama, Doors) consider it non-optional. | HIGH | `ba-tools index update` rebuilds `INDEX.md`; matrix columns: REQ-ID → SRS § → mermaid → mockup → story. |
| **Gap / orphan / stale detection on the matrix** | Without automated gap detection, coverage drift is invisible until UAT. | MEDIUM | `index update` three flags: `gaps` (no artifact coverage), `orphans` (req_ids that don't exist), `stale` (source hash changed). |
| **Resumable single-UC pipeline** | BAs interrupt work constantly; a pipeline that cannot resume forces reruns from scratch. | MEDIUM | `ba-tools uc-status` returns `current_step` + `next_step`; `ba-uc --route resume` re-enters at last good gate. |
| **Deterministic CLI output (JSON stdout, exit 2 on error)** | Tooling that mixes log noise with structured output is unusable in agent loops. | LOW | Every `ba-tools` subcommand emits UTF-8 JSON; `BaToolsError` exits `2`; no prose on stdout. |
| **Mermaid inline diagram authoring** | Mermaid is the de-facto standard for diagrams-as-code in Markdown environments (GitHub, GitLab, Notion). A BA suite that requires an external tool for every diagram loses the daily loop. | MEDIUM | `ba-mermaid` default route = `author` (MD-inline, no CLI dependency); `mmdc` only for image export. |
| **UI mockup at two fidelity tiers** | BAs routinely produce both quick wireframes (stakeholder alignment) and closer-to-real HTML screens (dev handoff). A single fidelity is a forced workaround. | MEDIUM | `ba-mockup --fidelity wireframe` = annotated block layout; `--fidelity html` = interactive `.html` file. |
| **Human confirm gate before irreversible steps** | Overwriting a delivered SRS or DOCX without a checkpoint is a trust-breaking error on the first occurrence. | LOW | Confirm gate fires before file overwrites and outward-facing operations; workflow blocks until human clears. |

---

### Differentiators (Competitive Advantage)

These features distinguish BA Daily Operators from generic ALM tools, document generators, and prompt-based LLM wrappers. They directly serve the confirmed core pain: high UC volume + cross-artifact drift.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Verbatim citation-exists gate** | A stated requirement's `source_trace.span` must be a real ≥12-char substring of its source document — mechanically checked by `ba-tools verify`, not by the model's memory. This is an architectural constraint that prevents LLM confabulation at the data layer rather than catching it after the fact. | HIGH | `ba-tools verify` opens `source_trace.doc`, does substring match; fails hard if span absent. Agent cannot paper over it — the check is outside the agent boundary. Ref: GenProve provenance approach + RAG grounding literature. |
| **Chain-of-Verification (CoVe) ba-critic loop** | After `ba-srs-analyze` drafts requirements, `ba-critic` (fresh context, read-only) generates per-requirement verification questions, answers them independently from the source document, and returns revision findings (≤3 loops). This catches semantic errors the citation gate cannot: a real quote that does not actually justify the stated requirement. | HIGH | Four-stage CoVe pipeline: draft → generate Qs → independent answers → revised draft. ≤3 revision caps prevent infinite loops. ba-critic never edits; only returns findings. Ref: arXiv 2309.11495 (CoVe reduces hallucination). |
| **REQ-ID traceability spine across all artifacts** | One REQ-ID propagated through SRS → Mermaid diagram → mockup → backlog story → INDEX.md. Drift surfaces the moment it appears, not at UAT. No current free/CLI tool does this end-to-end for BA deliverables without an ALM server. | HIGH | Every downstream artifact carries `req_ids` field; `ba-tools trace write` records artifact→REQ-ID links; `index update` rebuilds matrix. Gap/orphan/stale flags are actionable on every run. |
| **Source hash drift detection** | When the source document changes after requirements were extracted, every requirement grounded to that source becomes suspect. Surfacing this automatically saves a re-review cycle. | MEDIUM | `ba-tools verify` computes SHA-256 of `source_trace.doc`; if hash differs from recorded hash, `stale` flag is set in INDEX.md. |
| **Determinism boundary (CLI vs agent hard split)** | By design, `ba-tools` does only what a file/command/hash can prove; all judgement stays with agents. This means the CLI output is reproducible and auditable independent of which LLM is running, which is a requirement for regulated BA environments. | MEDIUM | Hard architectural line in DESIGN §5. No grey area: if it requires reasoning, it stays in the agent layer. |
| **Operator conductor (ba-uc) with quality gates between steps** | A conductor that threads four operators (srs-analyze → mermaid → mockup → index) with gate checks between each step, not just at the end. Defects are caught at the step boundary, not after the full pipeline has run. | HIGH | Quality gate after srs-analyze fires `ba-tools verify` + `ba-critic` before mermaid starts. Mermaid output is gated before mockup starts. Prevents downstream work on a bad requirements set. |
| **Default-route resolution without free-text inference** | `ba-tools resolve-route <operator>` returns the canonical default route from config — the tool never guesses intent from prose. Safe-default routing without user-burden is rare in CLI tooling. | LOW | `DEFAULT_ROUTE` per operator in config; resolve-route is a pure lookup. Operators still fail loudly if route is unknown. |
| **Byte-budget-aware skill layout** | Skills designed to stay under Codex's 32,768 B truncation limit; deep knowledge loaded lazily per step. This makes the suite reliably usable inside Codex without silent instruction truncation — a real operational failure mode in agent-backed CLIs. | MEDIUM | AGENTS.md / eager refs < 32,768 B. Workflow files use lazy Read (no eager `@`-import behind conditional). |

---

### Anti-Features (Deliberately Not Built)

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| **Synthetic diagram rendering (Pillow / SVG converter / screenshot)** | Fastest path to a diagram image when CLI is unavailable. | Produces unverifiable renders. The manifest `rendered_sha256 == embedded_sha256` invariant breaks immediately. A BA cannot prove to a stakeholder which source produced which image. | Fail hard if `mmdc` / draw.io CLI not found. Inline Mermaid in MD (`ba-mermaid` default route) requires no renderer at all. |
| **GUI dashboard / standalone `.ba-ops/` viewer** | Visual matrix browsers look impressive in demos. | Adds a separate application to install, maintain, and keep in sync with `.ba-ops/` schema. Does not run inside Codex. Complexity with zero BA daily value — the matrix is already Markdown-rendered. | `INDEX.md` in Codex chat. Terse `ba-tools` JSON in tool-call stream. In-Codex rendering is the UI (DESIGN §10b). |
| **Implicit skill invocation on spine / conductor** | Convenience — user doesn't have to type `$ba-srs-analyze`. | The analysis/build path must never auto-trigger. An accidental invocation on a partial prompt could overwrite a delivered SRS. | `allow_implicit_invocation: false` on all spine + conductor skills. Explicit `$` mention required. |
| **Soft citation check ("model believes quote exists")** | Easier to implement; LLM can reason about whether a quote sounds right. | The LLM can be confidently wrong. A "sounds plausible" check is not a grounding check. | Hard substring match in `ba-tools verify` (outside agent boundary). The 12-char minimum prevents single-word false positives. |
| **DOCX / draw.io on the daily spine** | Full delivery package every run is appealing. | draw.io desktop CLI + `python-docx` media-replace is heavy machinery; blocks on render availability; adds a Safety gate to every daily loop. | DOCX/draw.io in optional plugins only (`ba-uc-delivery`, `ba-make-diagram`). Daily spine is text-first; heavy render on demand. |
| **Hard-coded machine paths in config** | Convenient during development on a single machine. | Breaks portability across machines and runtimes (Codex → Claude Code v2). Violates the "hash-provable, portable" core value. | All paths resolve relative to `--repo-root` (git root / cwd); Python via `sys.executable`. |
| **Infinite ba-critic revision loops** | Theoretically higher quality with more critique rounds. | Each loop consumes full context; diminishing returns past loop 2; risk of oscillation where the critic flips requirements back and forth. | Hard cap at ≤3 loops in ba-critic contract. |
| **Backlog grooming on the daily spine** | BAs groom backlogs daily. | SPIDR-splitting + acceptance criteria generation is a distinct context load from SRS analysis. Bundling it makes the conductor brittle and bloated. | `ba-backlog-grooming` as a separate optional operator. Off the spine. |

---

## Feature Dependencies

```
[REQ-ID assignment + registry]
    └──required by──> [Verbatim citation-exists gate]
    └──required by──> [REQ-ID traceability spine]
                          └──required by──> [Gap/orphan/stale detection]
                          └──required by──> [ba-uc conductor]

[Source-grounded requirements (source_trace schema)]
    └──required by──> [Verbatim citation-exists gate]
    └──required by──> [Source hash drift detection]

[ba-srs-analyze (requirements JSON output)]
    └──required by──> [CoVe ba-critic loop]        (critic reads same requirements JSON)
    └──required by──> [ba-mermaid]                 (diagrams cite REQ-IDs from SRS)
    └──required by──> [ba-mockup]                  (screens cite REQ-IDs from SRS)
    └──required by──> [ba-uc conductor]            (conductor starts with srs-analyze)

[ba-uc conductor]
    └──orchestrates──> [ba-srs-analyze → ba-mermaid → ba-mockup → index update]
    └──requires──> [Quality gate after srs-analyze]
                       └──requires──> [Verbatim citation-exists gate]
                       └──requires──> [CoVe ba-critic loop]

[Resumable pipeline (uc-status)]
    └──requires──> [Deterministic CLI output (state in .ba-ops/STATE.md)]

[Mermaid inline diagram authoring]
    └──independent of──> [mmdc render CLI]    (inline MD is the default; render is optional export)

[UI mockup (html fidelity)]
    └──independent of──> [UI mockup (wireframe fidelity)]   (--fidelity flag, same operator)

[Traceability matrix (INDEX.md)]
    └──requires──> [ba-tools trace write]     (each artifact records req_ids on completion)
    └──requires──> [REQ-ID traceability spine]
```

### Dependency Notes

- **Citation-exists gate requires source_trace schema:** The schema fields (`source_trace.doc`, `source_trace.span`) must be present in the requirements JSON before the gate can run. Schema definition belongs to `ba-srs-analyze`'s output contract.
- **CoVe ba-critic requires completed draft first:** The critic loop is a post-draft step; it reads the same `requirements.json` the SRS writer produced. It cannot run in parallel with drafting.
- **ba-uc conductor requires ALL three spine operators to be built:** The conductor is the last thing to build; spine operators must be independently functional first (DESIGN §10 build order).
- **Gap/orphan/stale detection requires trace records:** `ba-tools index update` reads trace records written by `ba-tools trace write`. If no downstream operators have run yet, the matrix has gaps by definition — that is the expected initial state.
- **Byte budgets enhance but do not block:** Skills that exceed byte budgets still work; they just risk silent truncation in Codex. This is an operability concern, not a correctness blocker.

---

## MVP Definition

### Launch With (v1 — the daily spine)

- [ ] **`ba-tools` CLI core** — `lint-requirements`, `verify` (incl. citation-exists), `init`, `state`, `resolve-route`, `trace`, `index`, `uc-status`, `template fill`, `extract-uc` — without this nothing else runs deterministically.
- [ ] **`ba-srs-analyze` operator** — source docs → atomic, grounded, verifiable requirements JSON + SRS `.md` — the first and most important deliverable in every UC loop.
- [ ] **Verbatim citation-exists gate** — the single highest-value differentiator; prevents confabulation at the architectural level; must ship with `ba-srs-analyze`.
- [ ] **CoVe `ba-critic` loop** — semantic quality layer on top of the mechanical gate; the two together constitute a credible quality claim.
- [ ] **`.ba-ops/` file-state spine** — `PROJECT.md`, `REQUIREMENTS.md`, `INDEX.md`, `STATE.md`, `config.json` — required for traceability and resumability.
- [ ] **`ba-mermaid` operator** — UC/requirement → Mermaid diagram inline; fast, no CLI dependency for default route.
- [ ] **`ba-mockup` operator** — requirements → UI mockup at `--fidelity html|wireframe`.
- [ ] **`ba-uc` conductor** — sequential spine loop with quality gate after srs-analyze; resumable via `uc-status`.
- [ ] **`ba-tools index update`** — gap/orphan/stale matrix rebuild; this is the "traceability spine working" validation.

### Add After Validation (v1.x)

- [ ] **`ba-backlog-grooming` operator** — trigger: confirmed demand for SPIDR-splitting in daily workflow (currently deferred as the "rare 20%").
- [ ] **`mmdc` render path in `ba-mermaid`** — trigger: stakeholders need standalone diagram images for external delivery (not just Codex chat rendering).

### Future Consideration (v2+)

- [ ] **Claude Code v2 transform** — Task-subagent spawn, slash command frontmatter, hooks install-time transform. Deferred because `ba-tools` + `.ba-ops/` are runtime-agnostic and carry forward unchanged.
- [ ] **`ba-make-diagram` draw.io BPMN plugin** — formal BPMN swimlanes for regulated process documentation. Deferred: draw.io CLI dependency + Safety gate overhead not justified for daily lightweight flows.
- [ ] **`ba-uc-delivery` DOCX plugin** — stakeholder DOCX package with embedded diagrams. Deferred: `update-docx` stub; heavy machinery not on the daily path.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `ba-tools` lint-requirements + verify (citation-exists) | HIGH | MEDIUM | P1 |
| `ba-srs-analyze` operator + SRS `.md` output | HIGH | HIGH | P1 |
| REQ-ID registry + source_trace schema | HIGH | LOW | P1 |
| CoVe `ba-critic` loop | HIGH | HIGH | P1 |
| `.ba-ops/` traceability spine (INDEX.md) | HIGH | MEDIUM | P1 |
| `ba-uc` conductor + quality gate | HIGH | HIGH | P1 |
| Resumable pipeline (`uc-status`) | MEDIUM | MEDIUM | P1 |
| `ba-mermaid` inline authoring | HIGH | MEDIUM | P1 |
| `ba-mockup` html + wireframe | MEDIUM | MEDIUM | P1 |
| Gap / orphan / stale detection | HIGH | MEDIUM | P1 |
| Source hash drift detection | MEDIUM | LOW | P1 |
| Ambiguity + atomicity lint | MEDIUM | MEDIUM | P2 |
| Verifiability / testability check | MEDIUM | MEDIUM | P2 |
| Default-route resolution (no free-text inference) | MEDIUM | LOW | P2 |
| Byte-budget-aware skill layout | MEDIUM | MEDIUM | P2 |
| `mmdc` render export | LOW | LOW | P2 |
| `ba-backlog-grooming` operator | MEDIUM | HIGH | P3 |
| `ba-make-diagram` draw.io plugin | LOW | HIGH | P3 |
| `ba-uc-delivery` DOCX plugin | LOW | HIGH | P3 |
| Claude Code v2 transform | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for v1 daily spine launch
- P2: Should have — add when spine is stable
- P3: Deferred to later milestone / v2

---

## Requirements Quality Feature Detail

### Atomicity
One requirement, one testable statement. Detection: lint for conjunctions (`AND`, `OR`, `,`) connecting independent clauses; compound subjects ("system shall A and B"). Complexity: MEDIUM — regex catches the obvious cases; semantic compound requires agent judgement in `ba-critic`.

### Ambiguity Detection
Flag vague qualifiers: "fast", "user-friendly", "appropriate", "easy", "efficient", "sufficient", "timely". Also: passive voice without a specified actor ("shall be processed" — by whom?), undefined terms used without a glossary entry. Complexity: MEDIUM — keyword list + pattern match for lint; `ba-critic` handles subtle ambiguity.

### Verifiability / Testability
A requirement is verifiable iff there exists a finite, cost-effective test with a pass/fail result (IEEE 830 §3.5). Lint check: flag requirements with no measurable criterion (no numeric threshold, no "shall return X within Y ms", no binary state). The schema should enforce an `acceptance_criteria` field; lint fails if empty. Complexity: MEDIUM.

### INVEST / SMART alignment
INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable) applies at the story level after backlog grooming, not at the SRS requirement level. At the SRS level, the relevant subset is: **Small** (atomicity), **Testable** (verifiability), and independence from other requirements where possible. Full INVEST scoring belongs to `ba-backlog-grooming`, not `ba-srs-analyze`. This keeps scope clean.

### Grounding to source
Every stated requirement must cite its source document and a verbatim span from that document (`source_trace.doc`, `source_trace.span`). The mechanical check (`ba-tools verify` substring match, ≥12 chars) proves the quote exists. The semantic check (`ba-critic` CoVe) proves the quote actually justifies the stated requirement. Both checks are required; neither alone is sufficient.

---

## SRS/BRD Structure (IEEE 830 / ISO 29148 Sections)

Standard sections the SRS `.md` must contain for stakeholder sign-off legitimacy:

| Section | IEEE 830 ref | Content |
|---------|-------------|---------|
| 1. Introduction | §2 | Purpose, scope, definitions/acronyms, references, overview |
| 2. Overall Description | §3.1–3.3 | Product perspective, product functions, user characteristics, constraints, assumptions |
| 3. Specific Functional Requirements | §3.4 | Each UC/feature: REQ-IDs, actor, trigger, main flow, alt flows, acceptance criteria |
| 4. Non-Functional Requirements | §3.5 | Performance, security, reliability, usability, maintainability — each verifiable |
| 5. Constraints | §3.5 | Regulatory, technical, interface constraints |
| 6. Appendices | §4 | Traceability matrix reference, source documents, glossary |

ISO 29148 adds: Stakeholder Requirements Specification (StRS) and System Requirements Specification (SyRS) as distinct doc types above SRS. For BA Daily Operators v1, the SRS template covers the Software Requirements Specification level (most common BA deliverable).

---

## Mermaid Diagram Types for UC / Flows

| Type | Mermaid syntax | BA use | Fidelity |
|------|---------------|--------|---------|
| **Flowchart** | `flowchart TD` | Process flow, business rules, decision trees | Medium |
| **Sequence diagram** | `sequenceDiagram` | Actor-system interactions, API flows, UC main/alt flows | High for interaction |
| **State diagram** | `stateDiagram-v2` | Object lifecycle, workflow state machines | High for state |
| **Use case** | No native UC diagram in Mermaid v10/v11 | — | Use flowchart as proxy |
| **Class diagram** | `classDiagram` | Domain model, entity relationships | Medium |
| **ER diagram** | `erDiagram` | Data model, database schema | High for data |
| **User journey** | `journey` | End-to-end user flow across touchpoints | Low-medium |

**Recommendation for `ba-mermaid`:** default to `flowchart` (process) + `sequenceDiagram` (UC interaction) + `stateDiagram-v2` (lifecycle). These three cover 90% of daily BA diagramming needs without requiring draw.io.

---

## UI Mockup Fidelity Tiers

| Tier | `--fidelity` value | Output | Use |
|------|--------------------|--------|-----|
| **Wireframe** | `wireframe` | Annotated ASCII/Markdown block layout (inline in `.md`) | Stakeholder alignment, structure validation, early feedback |
| **HTML** | `html` | `.html` file with basic CSS layout, form fields, button states | Dev handoff, interaction demonstration, sign-off before build |

**Not built (anti-feature):** mid-fidelity pixel-perfect Figma-style mockups — the BA operator is not a design tool. The two tiers map directly to the two real BA needs: "does the screen make sense?" (wireframe) and "does it demonstrate the requirement?" (html). A third tier adds design system complexity with no BA value.

---

## Sources

- [IEEE 830 / ISO 29148 SRS template (ReqView)](https://www.reqview.com/doc/iso-iec-ieee-29148-templates/)
- [Requirements Traceability Matrix — Perforce](https://www.perforce.com/resources/alm/requirements-traceability-matrix)
- [CoVe: Chain-of-Verification Reduces Hallucination — arXiv 2309.11495](https://arxiv.org/pdf/2309.11495)
- [CoVe pipeline walkthrough — LearnPrompting](https://learnprompting.org/docs/advanced/self_criticism/chain_of_verification)
- [INVEST criteria and QUS framework — arXiv 1406.4692](https://arxiv.org/pdf/1406.4692)
- [LLM agents for user story quality — arXiv 2403.09442](https://arxiv.org/pdf/2403.09442)
- [Mermaid diagram syntax reference](https://mermaid.js.org/intro/syntax-reference.html)
- [Wireframe vs mockup vs prototype fidelity tiers — UXPin](https://www.uxpin.com/studio/blog/prototypes-wireframes-mockup-difference/)
- [RAG grounding / fake citation detection — Medium](https://medium.com/@Nexumo_/rag-grounding-11-tests-that-expose-fake-citations-30d84140831a)
- DESIGN.md §2 (operators), §5 (determinism boundary / citation-exists), §6 (gates / ba-critic) — primary source

---

*Feature research for: BA Daily Operators — requirements-engineering / BA tooling*
*Researched: 2026-06-17*
