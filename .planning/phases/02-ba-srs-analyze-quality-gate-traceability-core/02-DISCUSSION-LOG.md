# Phase 2: ba-srs-analyze + Quality Gate + Traceability Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-17
**Phase:** 2-ba-srs-analyze + Quality Gate + Traceability Core
**Areas discussed:** Requirements format + verify, source_trace schema, trace ↔ index data flow, Stale/source-drift baseline, REQ-ID registry + numbering, ba-critic gate authority + convergence, INDEX.md matrix format, SRS/BRD structure, Route behaviors, extract scope + source formats, slug + file naming, agent context-payload shape, statement_hash semantics

---

## Requirements format + verify (Area 1)

| Option | Description | Selected |
|--------|-------------|----------|
| JSON canonical, rework verify | requirements.json is single source of truth; verify reworked to read JSON; SRS.md rendered from it | ✓ |
| MD table canonical | Keep verify reading the Markdown table; JSON is a secondary export | |
| Dual first-class | verify accepts both JSON and MD table, both kept in sync | |

**User's choice:** JSON canonical, rework verify
**Notes:** Matches SRS-01 literal ("requirements JSON matching the schema verify gates"). SRS.md table becomes a view; no table↔JSON drift.

## source_trace schema (Area 1 cont.)

| Option | Description | Selected |
|--------|-------------|----------|
| Full: status + source_trace{doc,span,section} | {id, statement, status, source_trace:{doc,span,section}}; verify checks only stated; section null → document scope | ✓ |
| Minimal: source_trace{doc,span} only | DESIGN §5 literal; no section/status fields | |

**User's choice:** Full schema
**Notes:** Mirrors columns verify_cmd.py already reads; preserves Phase 1 section-scoping precision.

## trace ↔ index data flow (Area 2)

| Option | Description | Selected |
|--------|-------------|----------|
| trace store is the source; index reads it | Uniform JSON record per artifact in .ba-ops/traces/<kind>-<slug>.json; index reads records only | ✓ |
| index re-scans artifacts directly | index walks artifacts and reads req_ids fields directly | |
| Central append-only trace ledger | trace write appends to one .jsonl ledger | |

**User's choice:** trace store is the source; index reads it
**Notes:** Deterministic uniform input regardless of artifact type (SRS JSON / Mermaid / HTML). index never re-parses heterogeneous artifacts.

## Stale / source-drift baseline (Area 3)

| Option | Description | Selected |
|--------|-------------|----------|
| Re-hash source on disk vs record's source_hash | trace write stores source_hash; index re-hashes live source, flags stale on mismatch | ✓ |
| Baseline stored in INDEX.md | INDEX persists source hash; compare on next update | |

**Granularity sub-question:** Per source doc (per artifact) ✓ — vs Per requirement.

**User's choice:** Re-hash on disk vs record source_hash; per-artifact granularity
**Notes:** Baseline lives in the trace record (no extra storage). Whole-artifact stale flag → re-run srs-analyze.

## REQ-ID registry + numbering (Area 4)

| Option | Description | Selected |
|--------|-------------|----------|
| requirements.json union = registry; REQUIREMENTS.md rendered | Union of all requirements.json defines valid IDs; REQUIREMENTS.md is rendered view; orphan = cite without definition | ✓ |
| REQUIREMENTS.md canonical; srs-analyze registers IDs | REQUIREMENTS.md authoritative, appended to | |

**Numbering sub-question:** Semantic prefix FR-/NFR-/BR- + seq ✓ — vs flat REQ-NNN, vs per-slug <SLUG>-NNN.

**User's choice:** requirements.json union = registry; semantic FR-/NFR-/BR- numbering
**Notes:** SRS is birthplace of REQ-IDs; agent assigns prefix+seq, lint enforces stability/uniqueness (determinism boundary).

## ba-critic gate authority + convergence (Area 5)

| Option | Description | Selected |
|--------|-------------|----------|
| Blocks within the loop, escalates on non-convergence | verify hard-gates; critic findings prevent convergence; after 3 loops → Confirm checkpoint | ✓ |
| Critic hard-blocks (gate fails) | Unresolved critic FAIL → gate non-zero, no human path | |
| Critic advisory only | Critic logs only, never blocks | |

**Convergence sub-question:** Zero unresolved FAIL-severity findings ✓ — vs finding-count-stable.

**User's choice:** Blocks within loop, escalates on non-convergence; converged = zero FAIL findings
**Notes:** Critic read-only; ba-srs-writer re-drafts. "passed early" vs "passed after N" logged. WARN non-blocking.

## INDEX.md matrix format (Area 6)

| Option | Description | Selected |
|--------|-------------|----------|
| Per-row Status + aggregated drift sections | Row Status (covered/gap/stale) + dedicated Gaps/Orphans/Stale sections | ✓ |
| Inline status only (drop sections) | Everything in row Status column | |
| Sections only (scaffold as-is) | Keep sections, no per-row status vocabulary | |

**User's choice:** Per-row Status + aggregated drift sections
**Notes:** Matches Phase 1 scaffold + adds status. Gap in Phase 2 = no downstream coverage (expected until Phases 3-4).

## SRS/BRD .md structure (Area 7)

| Option | Description | Selected |
|--------|-------------|----------|
| Lean, grouped by FR/NFR/BR | Intro + grouped requirement tables + traceability stub | |
| Full IEEE-830 | Purpose/Scope/Defs, Overall Description, Specific Requirements (functional/non-functional/interface/constraints), Appendices | ✓ |
| BRD-style | Business objectives/stakeholders/scope/requirements | |

**User's choice:** Full IEEE-830
**Notes:** §3 groups FR-/NFR- prefixes; BR- gets a §3 subsection so all three prefixes have a home.

## Route behaviors (Area 8)

| Option | Description | Selected |
|--------|-------------|----------|
| Single-purpose, no implicit prerequisites | extract/draft/lint/verify each run one step against existing inputs | ✓ |
| Cumulative prefix | Each route runs its prerequisites too | |

**full/iterate sub-question:** full = whole pipeline + critic loop; iterate = re-draft folding discoveries ✓ — vs full = pipeline only (no critic).

**User's choice:** Single-purpose routes; full = extract→draft→verify→critic loop→trace; iterate = re-draft existing slug folding discoveries + findings
**Notes:** Default route is full; critic loop is part of the default Quality path.

## extract scope + source formats (Area 9)

| Option | Description | Selected |
|--------|-------------|----------|
| Arbitrary docs; extract-uc reused only when UC-shaped | Any source split via markdown_sections; UC-shaped reuses extract-uc identity | ✓ |
| UC-only (always via extract-uc) | Requires UC-formatted source | |

**Formats sub-question:** Markdown/plain text only ✓ — vs also accept .docx on spine.

**User's choice:** Arbitrary docs; .md/.txt only
**Notes:** .docx stays plugin-only (python-docx plugin-scoped); spine stays stdlib-only, zero new deps.

## slug + file path/naming convention (Area 10)

| Option | Description | Selected |
|--------|-------------|----------|
| --slug explicit, default to slugified source filename | --slug if given; else slugify filename; else UC id if UC-shaped | ✓ |
| Always UC id | slug = parsed UC id (requires UC source) | |
| Always --slug required | Force --slug every run | |

**Filenames sub-question:** requirements.json + SRS.md + analysis.md ✓ — vs requirements.json + <slug>-SRS.md.

**User's choice:** --slug explicit w/ deterministic default; requirements.json + SRS.md + analysis.md
**Notes:** ba-tools owns slug derivation; trace kind=srs.

## agent context-payload shape (Area 11)

| Option | Description | Selected |
|--------|-------------|----------|
| Paths + extracted-section manifest; agent Reads source itself | Workflow passes paths + manifest; critic gets source + requirements.json only, re-derives | ✓ |
| Pre-extracted content payload inlined | Workflow inlines source text into agent prompt | |

**User's choice:** Paths + manifest; agent Reads content
**Notes:** Keeps workflow thin (DESIGN §4); critic never reads writer's analysis.md/rationale — preserves CoVe independence.

## statement_hash semantics (Area 12)

| Option | Description | Selected |
|--------|-------------|----------|
| Per-REQ hash of normalized statement; detects requirement edits | sha256 of normalized statement; flags same-ID wording change | ✓ |
| One artifact-level hash over all statements | Single hash of concatenated statements | |
| Hash raw statement (no normalization) | Per-REQ over raw bytes; whitespace edits cause false drift | |

**User's choice:** Per-REQ hash of normalized statement
**Notes:** Normalize = strip + collapse whitespace (no case-fold). Ties to Phase 1 REQ-ID stability lint (TOOL-05). Refines trace record req_ids to [{id, statement_hash}].

---

## Claude's Discretion

- Skill/workflow file-layout reconciliation (DESIGN `.agents/skills/` + `ba-core/workflows/` vs Phase 1's nested `ba-tools/ba-core/`).
- ba-srs-writer / ba-critic agent prompt bodies + exact CoVe question-generation strategy.
- JSON→Markdown render implementation for SRS.md and REQUIREMENTS.md (likely deterministic in ba-tools).
- Exact lint fold over JSON-format requirements.
- discovery record shape consumed by iterate.
- Test-fixture design for the 5 success criteria.
- openai.yaml interface fields + keyword-dense SKILL.md description.

## Deferred Ideas

- Per-requirement source-drift (per-REQ stale) — only if one SRS cites multiple distinct source docs.
- .docx source ingestion on the spine — plugin-only.
- WARN_INJECTION promoted to hard gate for external-source stated reqs — later milestone.
- Mermaid/mockup/story INDEX columns populated in Phases 3/4/(backlog).
- Standalone .ba-ops/ viewer — out of scope (DESIGN §10b).
