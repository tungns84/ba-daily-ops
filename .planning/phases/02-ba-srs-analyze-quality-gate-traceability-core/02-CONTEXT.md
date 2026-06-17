# Phase 2: ba-srs-analyze + Quality Gate + Traceability Core - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning

<domain>
## Phase Boundary

The highest-value differentiator works end-to-end: a source document becomes
atomic, grounded, verifiable requirements (canonical **JSON**) plus a rendered
IEEE-830 SRS/BRD `.md`, every `stated` requirement carries a verifiable
`source_trace`, the artifact is gated by `ba-tools verify` **plus** the
independent fresh-context `ba-critic` Chain-of-Verification loop, and the
`.ba-ops/` traceability matrix (INDEX.md) is rebuilt with gap/orphan/stale
detection so REQ-ID coupling is validated before any other operator consumes
REQ-IDs.

**Phase 2 requirements (15):** SRS-01, SRS-02, SRS-03, SRS-04, SRS-05, SRS-06,
GATE-01, TRACE-03, TRACE-04, TRACE-05, TOOL-07, TOOL-08, CDX-01, CDX-02, CDX-03.

**Components delivered this phase:**
1. `ba-srs-analyze` skill (CDX-01/02/03) — flat `.agents/skills/ba-srs-analyze/`
   SKILL.md (`name`+`description` only) + `agents/openai.yaml`
   (`interface.*`, `policy.allow_implicit_invocation: false`) + thin workflow
   resolving route → workflow file → follow it.
2. `ba-srs-writer` agent — emits `requirements.json` (the quality-contract
   schema verify gates) + renders the SRS `.md` (SRS-01/02/03/04).
3. `ba-critic` agent — fresh-context CoVe loop, ≤3 revisions, read-only (SRS-05).
4. `ba-tools trace write` (TOOL-07) — per-artifact trace record + statement hash.
5. `ba-tools index update` (TOOL-08, TRACE-04/05) — rebuild INDEX.md matrix with
   gap/orphan/stale detection.
6. `source_trace` schema + `req_ids` on artifacts (SRS-03, TRACE-03).

**Explicitly NOT this phase:** `ba-mermaid` (Phase 3), `ba-mockup` (Phase 4),
`ba-uc` conductor + Safety gate contract GATE-03 (Phase 5). The Mermaid/mockup
INDEX columns exist but stay empty until those phases.

</domain>

<decisions>
## Implementation Decisions

### Requirements artifact format + verify (Area 1)
- **D-01:** `requirements.json` is the **single canonical source of truth**
  (SRS-01 literal). The SRS/BRD `.md` is **rendered from** the JSON — the table
  in the `.md` is a view, never the master. No table↔JSON drift.
- **D-02:** Rework `ba-tools verify` to **gate the JSON directly** (detect
  `.json` / a `--reqs-format` switch). Phase 1's `verify_cmd.py` parses a
  Markdown table today — that reader is replaced/extended for JSON input. The
  existing citation/lint/exit-2 semantics are preserved; only the input parsing
  changes.
- **D-03:** Per-requirement schema is:
  ```json
  {
    "id": "FR-001",
    "statement": "...",
    "status": "stated",            // or "derived"
    "source_trace": { "doc": "path/to/source.md", "span": ">=12 char verbatim", "section": "2.1 Login" }
  }
  ```
  `verify` citation-checks **only** `status: stated` reqs. `section: null` →
  document-scope search; otherwise section-scoped (the Phase 1 default). This
  mirrors the columns `verify_cmd.py` already reads (id/statement/status/
  source/section/span), now as JSON fields.

### trace ↔ index data flow (Area 2)
- **D-04:** `trace write` emits a **uniform JSON record per artifact** into a
  central store: `.ba-ops/traces/<kind>-<slug>.json`. `index update` reads
  **only** those records to build INDEX.md — it **never** re-parses raw
  heterogeneous artifacts (SRS JSON / inline Mermaid / HTML mockup). Uniform
  input regardless of artifact type.
- **D-05:** Trace record schema:
  ```json
  {
    "kind": "srs", "slug": "<slug>", "artifact_path": "...",
    "source_doc": "...", "source_hash": "sha256...",
    "req_ids": [ { "id": "FR-001", "statement_hash": "sha256..." }, ... ]
  }
  ```
  Note `req_ids` is a list of `{id, statement_hash}` objects, **not** bare
  strings (refined by Area 12 / D-12).

### Stale / source-drift detection (Area 3)
- **D-06:** `trace write` captures `source_hash = sha256(source_doc)` at
  production time into the record. `index update` re-hashes the **live** source
  doc on disk and flags **stale** on mismatch (→ re-run `ba-srs-analyze`). No
  extra storage — the baseline lives in the trace record (D-05). Hash-provable,
  deterministic.
- **D-07:** Granularity is **per source doc (per artifact)** — one
  `source_hash` per trace record. A stale flag marks the whole artifact and its
  REQ-IDs as needs-rerun. (Not per-requirement; only matters if one SRS cites
  multiple distinct source docs — deferred.)

### REQ-ID registry + numbering (Area 4)
- **D-08:** The **union of all `.ba-ops/srs/*/requirements.json`** defines every
  valid REQ-ID — SRS is the **birthplace** of requirements. `.ba-ops/
  REQUIREMENTS.md` is the **rendered, human-readable registry** (like the SRS
  `.md`). **Orphan** = a downstream (Mermaid/mockup) trace cites a REQ-ID that
  **no** `requirements.json` defines. Consistent with D-01 (JSON canonical).
- **D-09:** REQ-ID numbering = **semantic prefix + sequence**, industry-standard
  SRS: `FR-` (functional), `NFR-` (non-functional), `BR-` (business rule), e.g.
  `FR-001`. The `ba-srs-writer` agent **assigns** prefix+seq (judgement); Phase
  1's `lint-requirements` enforces **uniqueness + stability** (determinism
  boundary respected — ID choice is judgement, stability is deterministic).

### ba-critic gate authority + convergence (Area 5)
- **D-10:** `ba-tools verify` is the **deterministic hard block** (exit 2 on
  FAIL). `ba-critic` findings drive the **≤3 revision loop**: unresolved
  FAIL-severity critic findings **prevent convergence**. After 3 loops still
  failing → **escalate to a Confirm checkpoint** (human decides), never silent
  auto-pass. `ba-critic` is read-only; `ba-srs-writer` re-drafts between loops.
- **D-11:** **Converged** = a loop that produces **zero** new FAIL-severity
  critic findings. Log `"passed early"` (loop 1) vs `"passed after N"` (loop
  N>1). WARN findings are logged but **non-blocking** (mirrors the verify
  FAIL/WARN model, Phase 1 D-07).

### statement_hash semantics (Area 12)
- **D-12:** `statement_hash` is **per-REQ**, = `sha256` of the **normalized**
  statement (strip + collapse internal whitespace; no case-fold). Job: detect
  when a requirement's **wording changes** under the same REQ-ID, so INDEX /
  downstream artifacts citing it can be flagged for re-check. Complements Phase
  1's REQ-ID stability lint (TOOL-05: same ID, changed statement). Distinct from
  `source_hash` (D-06, which tracks the upstream source doc).

### INDEX.md matrix format (Area 6)
- **D-13:** INDEX.md keeps the matrix row **Status** column
  (`covered | gap | stale`) **AND** dedicated **Gaps / Orphans / Stale**
  sections as the scannable roll-up. Row = detail, sections = summary. Orphans
  live only in their section (they have no valid REQ-ID row). Matches the Phase
  1 scaffold, adds status vocabulary.
- **D-13a:** In Phase 2, a **gap** = a REQ-ID with no **downstream**
  (Mermaid/mockup/story) coverage — expected for every req until Phases 3–4. The
  success-criteria fixture still exercises gap/orphan/stale (criterion 4).

### SRS/BRD `.md` structure (Area 7)
- **D-14:** `ba-srs-writer` renders a **full IEEE-830** structure: §1
  Introduction (Purpose/Scope/Definitions), §2 Overall Description, §3 Specific
  Requirements (3.1 Functional `FR-*`, 3.2 Non-Functional `NFR-*`, a §3
  subsection for Business Rules `BR-*` so all three prefixes have a home, plus
  External Interfaces / Constraints), §4 Appendices, and a Traceability section
  `index update` fills.

### Route behaviors (Area 8)
- **D-15:** Single-purpose routes, **no implicit prerequisites**:
  - `extract` — source → `.ba-ops/srs/<slug>/` sections
  - `draft` — sections → `requirements.json` + `SRS.md` (`ba-srs-writer`)
  - `lint` — `lint-requirements` report (advisory, exit 0)
  - `verify` — the hard gate (citation/coverage/hash)
  Each assumes prior outputs exist; the user chains manually or uses `full`.
- **D-16:** `full` (default) = `extract → draft → verify → ba-critic CoVe loop`
  (≤3) end-to-end with the Quality gate, then `trace write`. `iterate` = on an
  **existing** slug, re-run `draft → verify → critic` folding accumulated
  `ba-tools discovery` entries + prior critic findings, then re-trace.

### extract scope + accepted source formats (Area 9)
- **D-17:** `extract` accepts **arbitrary** source docs and splits them via the
  existing `markdown_sections` logic. If the source **is** UC-shaped, reuse
  Phase 1's `extract-uc` to also parse UC identity; otherwise treat as a generic
  doc (a source isn't always a UC — meeting notes, briefs, specs).
- **D-18:** Spine ingests **`.md` / `.txt` only**. `.docx` stays **plugin-only**
  (`python-docx` is plugin-scoped per CLAUDE.md; the spine is stdlib-only).
  Phase 2 adds **zero** new runtime dependencies.

### slug + file path/naming convention (Area 10)
- **D-19:** `<slug>` derivation (ba-tools owns it, deterministic): `--slug`
  explicit if given; else slugify the source filename (lowercase, hyphenated);
  else if UC-shaped, prefer the UC id (e.g. `uc-001`).
- **D-20:** Files inside `.ba-ops/srs/<slug>/`: `requirements.json` (canonical),
  `SRS.md` (rendered IEEE-830), `analysis.md` (`ba-srs-writer` working notes).
  Trace record `kind = "srs"`, `slug = <slug>` (DESIGN §8).

### agent context-payload shape (Area 11)
- **D-21:** The workflow passes **file paths + a small manifest**, not raw
  content (DESIGN §4). To `ba-srs-writer`: `{source_path, sections_dir, slug,
  route}`. To `ba-critic`: `{source_path, requirements.json path}` **only** —
  the critic reads the **source** + the bare statements and **re-derives**
  independently; it is told **not** to read the writer's `analysis.md` /
  rationale. This preserves CoVe independence. Agents Read the content they
  need; the workflow stays thin.

### Carried forward (already locked — do NOT re-decide)
- Citation-exists = **section-scoped**, ≥12-char real verbatim substring,
  `--cite-scope document` override (Phase 1, TOOL-06, Open Decision #1).
- `ba-critic` early-exits on convergence, logged; ≤3 loops; read-only
  (Open Decision #3).
- `WARN_INJECTION` scan **advisory** in v1 (Open Decision #2).
- Flat JSON envelope `{ok, failures, ...}`; success→stdout, error→stderr exit 2
  (Phase 1 D-03/D-04).
- `filelock` (`FileLock(timeout=10)`) is the single spine runtime dep; STATE.md
  writes lockfile-guarded (Phase 1 D-01/D-02). `.ba-ops/traces/` writes that
  share state should respect the same guard where concurrent.
- Skill layout **flat** `.agents/skills/ba-*/`, frontmatter `name`+`description`
  only, `policy.allow_implicit_invocation: false` (DESIGN §3, CDX-01/02).
- Python 3.11+, stdlib-first, resolve interpreter via `sys.executable`; all
  paths relative to `--repo-root` (TOOL-14, DESIGN §11).
- `.ba-ops/config.json` feature flags default `true` when missing (TRACE-02).

### Claude's Discretion (researcher / planner own these)
- **Skill/workflow file-layout reconciliation.** DESIGN §3 says skills live at
  `.agents/skills/ba-*/` and workflows at
  `.agents/ba-daily-operators/ba-core/workflows/`, but Phase 1 nested `ba-core`
  under `.agents/ba-daily-operators/ba-tools/ba-core/`. Planner reconciles the
  actual paths (where SKILL.md, `agents/openai.yaml`, workflows, and the
  `ba-core/agents/*.md` agent prompts physically land) and confirms Codex
  discovery still works.
- `ba-srs-writer` / `ba-critic` agent prompt bodies and exact CoVe
  question-generation strategy (within the D-10/D-11 contract).
- The JSON→Markdown render implementation for `SRS.md` and `REQUIREMENTS.md`
  (deterministic in ba-tools vs agent-authored) — pick per the determinism
  boundary; rendering a known schema is mechanical and likely ba-tools.
- Exact `lint` fold for JSON-format reqs (reusing Phase 1 heuristics over the
  JSON statements).
- `discovery` record shape consumed by `iterate`.
- Test-fixture design for the 5 success criteria (gap/orphan/stale fixture,
  citation pass/fail JSON fixture, ≤3-loop critic convergence fixture).
- `openai.yaml` `interface.display_name` / `short_description` /
  `default_prompt` wording and the keyword-dense SKILL.md `description`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture spec (source of truth)
- `DESIGN.md` — v0.2.2, repo root. Most relevant Phase-2 sections: §3 (SKILL.md
  + `openai.yaml` contract, flat layout), §4 (workflow thin-orchestrator pattern,
  route table, "pass paths not content"), §5 (determinism boundary, command
  families incl. `trace write` / `index update`, the citation-exists definition
  `source_trace.doc`/`span`), §6 (three gates, the `ba-critic` CoVe definition),
  §8 (`.ba-ops/` spine layout — `srs/<slug>/requirements.json`+`analysis.md`,
  INDEX.md matrix, gaps/orphans/stale), §11 (non-negotiables). §10 "DONE"
  markers are aspirational targets, not current state — greenfield build.

### Requirements & scope
- `.planning/REQUIREMENTS.md` — REQ-ID registry; Phase-2 requirement text
  (SRS-01..06, GATE-01, TRACE-03..05, TOOL-07/08, CDX-01..03) + the resolved
  Open Decisions table.
- `.planning/ROADMAP.md` — Phase 2 goal + 5 success criteria (the TRUE-conditions
  the verifier checks).
- `.planning/PROJECT.md` — v1 = daily spine only; determinism boundary; UI
  in-Codex-chat only; key decisions.

### Phase 1 outputs to build on (read the code, not just the doc)
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/verify_cmd.py` — the
  citation/lint gate to **rework for JSON input** (D-02). Currently parses a
  Markdown table.
- `.agents/ba-daily-operators/ba-tools/ba_tools/citation.py` — `citation_exists`
  (section-scoped, ≥12-char) — reuse verbatim for `source_trace`.
- `.agents/ba-daily-operators/ba-tools/ba_tools/lint.py` +
  `ba_tools/commands/lint_reqs.py` — lint heuristics + REQ-ID stability (TOOL-05)
  to fold over JSON statements (D-09, D-12 tie-in).
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/extract_uc.py` — reuse
  for UC-shaped sources (D-17).
- `.agents/ba-daily-operators/ba-tools/ba_tools/markdown_sections.py` — section
  splitter for arbitrary sources (D-17).
- `.agents/ba-daily-operators/ba-tools/ba_tools/state_store.py` /
  `commands/state_cmd.py` — lockfile pattern + `ALLOWED_KEYS`; reuse for
  `.ba-ops/traces/` if concurrent.
- `.agents/ba-daily-operators/ba-tools/ba_tools/scaffold.py` — `.ba-ops/`
  seeding; INDEX.md / REQUIREMENTS.md scaffold shapes already exist.
- `.agents/ba-daily-operators/ba-tools/.ba-ops/INDEX.md` — current matrix
  scaffold (columns + Gaps/Orphans sections) D-13 extends.
- `.agents/ba-daily-operators/ba-tools/ba-core/templates/srs.md` — minimal SRS
  template to evolve into the IEEE-830 structure (D-14).
- `.agents/ba-daily-operators/ba-tools/ba_tools/__main__.py` — argparse
  dispatcher to register `trace` / `index` subcommands.

### Tech stack (verified research)
- `CLAUDE.md` (repo root) — verified stack (Python 3.11+, stdlib-first,
  `filelock`, `hashlib.file_digest`), CLI output convention, Codex skill
  contract (frontmatter `name`+`description`; `openai.yaml` nesting
  `interface.*` / `policy.allow_implicit_invocation`), byte budgets.

### Referenced-but-absent (planner: confirm before relying on)
- `.agents/ba-daily-operators/ba-core/references/gates.md` and
  `.agents/ba-daily-operators/ba-core/workflows/<operator>.md` — referenced by
  DESIGN §4/§6 but **not yet created**; these are Phase-2 build targets, not
  inputs. `ba-core/agents/*.md` (ba-srs-writer, ba-critic prompts) likewise.
- `FIS_GSARCHITECTURE.md` — cited by DESIGN/PROJECT but NOT in repo; treat its
  standard as already distilled into DESIGN.md.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`citation.py::citation_exists`** — drop-in for the JSON `source_trace`
  gate; already section-scoped + ≥12-char + `--cite-scope`.
- **`lint.py` heuristics + `lint_reqs.py` REQ-ID stability** — fold over JSON
  statements; stability lint (TOOL-05) directly backs D-09/D-12.
- **`extract_uc.py` + `markdown_sections.py`** — back the `extract` route (D-17).
- **`state_store.py` lockfile pattern** (`FileLock(timeout=10)`, `ALLOWED_KEYS`)
  — template for guarded `.ba-ops/traces/` and STATE updates.
- **`scaffold.py` + existing `.ba-ops/INDEX.md` / `REQUIREMENTS.md` scaffolds**
  — INDEX matrix columns + Gaps/Orphans sections already shaped (D-13).
- **`output.py::ok_json` + `errors.py::BaToolsError`** — the flat envelope /
  exit-2 contract for the new `trace` / `index` commands.

### Established Patterns
- Flat JSON envelope `{ok, failures, ...}`; success→stdout, error→stderr exit 2.
- Subcommands register via `register(subparsers)` in `ba_tools/commands/*.py`,
  wired in `__main__.py` — follow this for `trace_cmd.py` / `index_cmd.py`.
- Paths resolve under `--repo-root` via `repo.py` (`resolve_under_root`,
  `is_within_root`) — reuse for all new path inputs (path-traversal safety).

### Integration Points
- `.ba-ops/` is the persistent spine. Phase 2 adds `srs/<slug>/`,
  `traces/<kind>-<slug>.json`, and fills INDEX.md. The trace-record schema (D-05)
  is the **contract** Phases 3–5 (`ba-mermaid`, `ba-mockup`, `ba-uc`) write to
  when they `trace write` — design it to carry Mermaid/mockup/story kinds.
- `ba-srs-analyze` is the **first operator skill** — it establishes the
  SKILL.md / `openai.yaml` / workflow / agent-prompt layout the later operators
  copy.

</code_context>

<specifics>
## Specific Ideas

- `requirements.json` is the master; everything human-readable (`SRS.md`,
  `REQUIREMENTS.md` registry) is **rendered from it** — no hand-maintained
  parallel copy.
- Keep `ba-tools` JSON terse and scannable (DESIGN §10b — read by a human in the
  Codex chat). The `trace`/`index` output should make gap/orphan/stale obvious
  at a glance.
- The `ba-critic` independence that matters is **re-deriving from the source**,
  never reading the writer's rationale (D-21) — this is the CoVe guarantee
  carried over from PROJECT.md's Codex caveat.
- This phase **proves the traceability spine** — the core value. If everything
  else slips, REQ-ID → source_trace → INDEX coupling must work.

</specifics>

<deferred>
## Deferred Ideas

- **Per-requirement source-drift** (hash each `source_trace.doc` independently,
  per-REQ stale flag) — only needed if one SRS cites multiple distinct source
  docs; per-artifact granularity chosen for v1 (D-07).
- **`.docx` source ingestion on the spine** — plugin-only (`ba-uc-delivery`);
  spine stays `.md`/`.txt` stdlib-only (D-18).
- `WARN_INJECTION` promoted from advisory to a hard gate for external-source
  `stated` requirements — Open Decision #2, later milestone.
- Mermaid / mockup / story INDEX columns are scaffolded but populated only in
  Phases 3 / 4 / (backlog plugin, deferred).
- A standalone viewer over `.ba-ops/` — out of scope (DESIGN §10b).

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-ba-srs-analyze + Quality Gate + Traceability Core*
*Context gathered: 2026-06-17*
