# Phase 4: ba-mockup Operator - Context

**Gathered:** 2026-06-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Requirements become a **UI mockup at a required `--fidelity` of `html` or
`wireframe`**. Each mockup **screen cites the REQ-IDs it realizes** (`req_ids`)
so those IDs appear in the INDEX.md traceability matrix under the **mockup
column**. The chosen fidelity determines the artifact form: **`html` → a
self-contained static `.html` file**; **`wireframe` → inline markdown-structural
blocks in a `.md`**. No render/screenshot step — the artifact IS the deliverable.

**Phase 4 requirements (3):** MOCK-01 (requirements → UI mockup at
`--fidelity html|wireframe`, fidelity required), MOCK-02 (each screen cites
`req_ids`), MOCK-03 (`html` writes a `.html` artifact; `wireframe` writes inline
blocks).

**Components delivered this phase:**
1. `ba-mockup` skill (CDX pattern) — flat `.agents/skills/ba-mockup/` SKILL.md
   (`name`+`description` only) + `agents/openai.yaml` (`interface.*`,
   `policy.allow_implicit_invocation: false`), copying the Phase-3 `ba-mermaid` /
   Phase-2 `ba-srs-analyze` layout.
2. `ba-mockup` thin workflow — resolves route → workflow file → follows it.
   Routes `screen` / `full` (default `full`, both Phase-1-locked). The workflow
   **enforces `--fidelity`** (rejects missing/invalid; must be `html|wireframe`).
3. A mockup-author agent prompt (`ba-core/agents/`) — judges screen content and
   the REQ-ID subset, writes the `.html` or wireframe `.md` artifact.
4. Reuse of the existing `trace write --kind mockup` + `index update` contract
   (Phase 2 D-04/D-05/D-13) — **no schema change, no new ba-tools command.**

**Explicitly NOT this phase:** `ba-uc` conductor + Safety gate GATE-03
(Phase 5), any render/screenshot of the mockup (forbidden — no synthetic
render), multi-screen-per-invocation (one screen per invocation — see D-01),
the DOCX/draw.io plugins (deferred v2). The story INDEX column stays empty.

</domain>

<decisions>
## Implementation Decisions

### Screen unit + which REQ-IDs a screen realizes (Area 1)
- **D-01:** **One screen per invocation** (mirrors mermaid's one-diagram-per-
  invocation). The Phase-1-locked route name `screen` fits: one screen = one
  artifact = one `req_ids` set. Multi-screen flows are produced by **multiple
  invocations** (one trace each); the Phase-5 `ba-uc` conductor loops if a UC
  needs several screens. Keeps `req_ids` carriage simple — one artifact → one
  `req_ids` set → one `trace write`.
- **D-01a:** Input is an **existing SRS `--slug`** (mirrors mermaid D-01).
  `ba-mockup` reads `.ba-ops/srs/<slug>/requirements.json` (the Phase-2
  canonical REQ-ID source) and the **agent picks the subset** of REQ-IDs the
  screen realizes (agent judgement — determinism boundary; ba-tools never infers
  which reqs a screen depicts). The mockup slug ties to the srs slug; artifacts
  land under `.ba-ops/mockup/<slug>/`. The agent does not invent REQ-IDs (any
  slip surfaces as an orphan downstream — see D-06).

### req_ids carriage on the artifact (Area 1)
- **D-02:** REQ-IDs the screen realizes are written into the artifact and the
  **thin workflow reads them → calls `ba-tools trace write --kind mockup --slug
  <slug> --req-ids <list> --artifact <file> --source <srs requirements.json>`**.
  Mirrors mermaid D-03/D-03a — **no new ba-tools parser**, uses the existing
  explicit `--req-ids` flag. Carrier differs by fidelity:
  - **wireframe (`.md`):** `req_ids` in **YAML frontmatter** (`req_ids: [FR-001,
    FR-002]`) — markdown-native, human-visible in Codex chat (mirror mermaid D-03).
  - **html (`.html`):** `req_ids` in an **HTML comment block as the first line**
    (`<!-- req_ids: [FR-001, FR-002] -->`) — YAML frontmatter is markdown-only;
    the comment is human-visible in source and trivially regex-extractable by the
    workflow. Same frontmatter→flag hand-off, expressed in HTML's native comment
    syntax.

### HTML fidelity output shape (Area 2)
- **D-03:** `html` fidelity writes a **single self-contained static `.html`**
  with **all CSS inline in a `<style>` tag** — **zero external assets / JS / CDN /
  framework**. Portable, diff-able, opens anywhere; matches the no-bespoke-GUI /
  no-framework / "effectiveness over looks" constraints (REQUIREMENTS Out of
  Scope) and the text-first spine. Lands under `.ba-ops/mockup/<slug>/`.

### Wireframe fidelity format (Area 3)
- **D-04:** `wireframe` fidelity writes **inline markdown-structural blocks** in
  a `.md` artifact — headings + lists + tables describing layout regions
  (chosen over ASCII box-drawing). Human-readable in Codex chat, text-first, no
  rendering step. `req_ids` in the `.md` YAML frontmatter (D-02).

### Routes + fidelity enforcement (Areas 3 & 4)
- **D-05:** Routes mirror mermaid semantics (table Phase-1-locked):
  - **`screen`** — author the artifact only. **No CLI, no trace** (pure
    authoring; trace happens in `full`). Mirrors mermaid `author`.
  - **`full`** (default — `resolve-route ba-mockup` → `full`) — `author →
    trace write --kind mockup → index update`.
  - **No `render` route** — the `.html`/wireframe artifact IS the deliverable;
    there is no `mmdc`-equivalent and **no synthetic render path** (DESIGN §11).
- **D-05a:** `--fidelity` is **required and enforced by the thin workflow** —
  it hard-rejects a missing or invalid value (must be `html|wireframe`) before
  authoring (MOCK-01 criterion 1). **Zero new ba-tools commands** this phase —
  fidelity/argument validation is workflow-level; the deterministic surface is
  fully covered by the existing `trace write` + `index update` (unlike mermaid,
  which needed a new `mermaid-render` command for the CLI render target).

### Orphan handling (Area 4)
- **D-06:** Cited REQ-IDs are validated **downstream by `index update`** — it
  flags an orphan when a mockup trace cites a REQ-ID absent from
  `requirements.json` (existing Phase-2 D-13 behavior; mermaid D-05). `trace
  write` records what it is given; **no change to `trace_cmd.py` /
  `index_cmd.py`**. Criterion 3 ("mockup citing a non-existent REQ-ID surfaced
  as orphan") is met by the INDEX Orphans section.

### Claude's Discretion (researcher / planner own these)
- Exact mockup-author agent-prompt filename + body (suggest
  `ba-core/agents/ba-mockup-author.md` by analogy to `ba-diagrammer.md` /
  `ba-srs-writer.md`); screen-content heuristics.
- Exact `.html` scaffold (DOCTYPE, semantic-HTML structure, minimal inline-CSS
  conventions) within "self-contained static, no framework" (D-03).
- Exact markdown-structural wireframe layout conventions within D-04.
- Exact regex for extracting the HTML-comment `req_ids` and the `.md`
  frontmatter `req_ids` in the workflow hand-off.
- The `--source` argument shape passed to `trace write` for kind=mockup
  (reconcile with the Phase-2 source_hash semantics — same open item resolved
  for mermaid in Phase 3).
- Skill/workflow physical file-layout reconciliation (skills at
  `.agents/skills/ba-mockup/`, workflow at
  `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md`, agent prompt at
  `ba-core/agents/`) — confirm Codex discovery (same as Phase 3).
- `openai.yaml` `interface.*` wording + keyword-dense SKILL.md `description`.
- Test-fixture design for the 3 success criteria (fidelity-required rejection +
  html→`.html` / wireframe→inline; req_ids→INDEX mockup column no-orphan;
  invented-ID orphan surfaced).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture spec (source of truth)
- `DESIGN.md` — repo root. Most relevant Phase-4 sections: §3 (SKILL.md +
  `openai.yaml` flat-layout contract), §4 (thin-orchestrator pattern, route
  table; "pass paths not content"), §5 (determinism boundary — agents author,
  ba-tools proves; **no synthetic render**), §6 (gates), §8 (`.ba-ops/` spine —
  `mockup/<slug>/`, INDEX.md mockup column), §11 (non-negotiables: no synthetic
  render, no hard-coded paths, paths under `--repo-root`). §10 "DONE" markers
  are aspirational, not current state.

### Requirements & scope
- `.planning/REQUIREMENTS.md` — REQ-ID registry; Phase-4 requirement text
  MOCK-01/02/03; Out-of-Scope table (no bespoke GUI/dashboard, no synthetic
  render, UI is in-Codex-chat only).
- `.planning/ROADMAP.md` — Phase 4 goal + 3 success criteria (the TRUE-conditions
  the verifier checks: fidelity-required + html→`.html`/wireframe→inline;
  req_ids→INDEX mockup column no-orphan; invented-ID orphan surfaced).
- `.planning/PROJECT.md` — v1 daily spine; determinism boundary; core value =
  REQ-ID traceability across artifacts.

### Phase 3 — the direct template to copy (ba-mockup mirrors ba-mermaid)
- `.planning/phases/03-ba-mermaid-diagram-operator/03-CONTEXT.md` — the sibling
  spine-operator decisions this phase parallels: D-01 (input = SRS slug, agent
  picks subset), D-03/D-03a (req_ids frontmatter → `trace write --req-ids`, no
  new parser), D-04 (route semantics: author-only vs full), D-05 (downstream
  orphan handling). **Read this first — Phase 4 reuses its structure wholesale.**
- `.agents/skills/ba-mermaid/SKILL.md` + `.../agents/openai.yaml` +
  `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` +
  `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md` — **the exact
  layout `ba-mockup` copies** (skill frontmatter, openai.yaml nesting, thin
  per-route workflow body, agent role-contract prompt).

### Phase 2 outputs to build ON (read the code + the contract, not just docs)
- `.planning/phases/02-ba-srs-analyze-quality-gate-traceability-core/02-CONTEXT.md`
  — the trace/index contract this phase consumes: D-04 (uniform trace record →
  index reads only records), **D-05 trace record schema** (`kind`, `slug`,
  `req_ids`, `source_hash`), D-08 (orphan definition), D-13/D-13a (INDEX status +
  Gaps/Orphans sections). **This is the contract ba-mockup writes to.**
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/trace_cmd.py` — already
  accepts `--kind mockup` with explicit `--req-ids`/`--req-ids-file`; validates
  kind/slug regex `^[a-z0-9][a-z0-9-]*$`; FileLock(timeout=10). **Reuse as-is.**
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/index_cmd.py` — orphan/
  gap/stale detection; already renders the **Mockup column** (lines ~208-213).
  **Reuse as-is** (D-06 orphan path).
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/resolve_route.py`
  (`DEFAULT_ROUTES`) — `ba-mockup → full` **already registered** (Phase 1).
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/init_cmd.py`
  (`OPERATOR_ROUTES`) — `ba-mockup: ["screen", "full"]` **already registered**.
- `.agents/ba-daily-operators/ba-tools/ba_tools/scaffold.py` — `.ba-ops/mockup/`
  parent **already scaffolded** (`_SUBDIRS`); confirm per-slug subdir creation.
- `.agents/ba-daily-operators/ba-tools/ba_tools/repo.py` — `resolve_under_root` /
  `is_within_root` path-traversal safety; reuse for all new path inputs.
- `.agents/ba-daily-operators/ba-tools/ba_tools/output.py` (`ok_json`) +
  `errors.py` (`BaToolsError`, exit 2) — output / hard-fail contract.

### Tech stack (verified research)
- `CLAUDE.md` (repo root) — verified stack: Python 3.11+ stdlib-first,
  `sys.executable`, paths under `--repo-root`; Codex skill contract (SKILL.md
  `name`+`description` only; `openai.yaml` `interface.*` + `policy.*` nesting);
  byte budgets (AGENTS.md/eager refs < 32,768 B; DEFAULT workflow < 38,000 B).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`trace_cmd.py`** — accepts `--kind mockup` + explicit `--req-ids` already;
  no change. The mockup→INDEX wiring is free (Phase 2 built the contract to
  carry the mockup kind).
- **`index_cmd.py`** — orphan/gap/stale detection already populates the **Mockup
  column** from trace records; reuse as-is (D-06).
- **`resolve_route.py` / `init_cmd.py`** — `ba-mockup` route table (`screen`,
  `full`) + default `full` **already registered in Phase 1** — no additive
  change needed (unlike mermaid, which had to be added in Phase 3).
- **`scaffold.py`** — `.ba-ops/mockup/` parent dir already created.
- **`output.py::ok_json` + `errors.py::BaToolsError`** — only relevant if any
  new command were added; this phase adds none.
- **`repo.py` path-safety** — reuse for artifact + output path inputs.
- **ba-mermaid skill + workflow + agent prompt** — the template `ba-mockup`
  copies wholesale (only route bodies + agent role + fidelity branching differ).

### Established Patterns
- Skill = flat `.agents/skills/<op>/` (SKILL.md `name`+`description` only) +
  `agents/openai.yaml` (`interface.*`, `policy.allow_implicit_invocation:false`)
  + thin workflow `ba-core/workflows/<op>.md` resolving route→steps + agent
  prompt `ba-core/agents/<role>.md`.
- "Pass paths, not content" — the workflow hands the agent the slug +
  `requirements.json` path; the agent Reads it and writes the artifact.
- ba-tools proves (trace/index); agents author. **This phase adds no new
  ba-tools command** — the deterministic surface is fully covered.

### Integration Points
- Consumes the Phase-2 traceability spine: reads `.ba-ops/srs/<slug>/
  requirements.json`, writes `.ba-ops/mockup/<slug>/` artifacts, calls
  `trace write --kind mockup` + `index update` to populate the INDEX mockup
  column.
- One of the two independent spine operators (parallel to `ba-mermaid`);
  feeds the Phase-5 `ba-uc` conductor (srs-analyze → mermaid → mockup → index).
- Unlike mermaid, **no render CLI** — establishes the "artifact IS the
  deliverable, no synthetic render" shape for a fidelity-branched operator.

</code_context>

<specifics>
## Specific Ideas

- Default route `full` invokes **zero external CLI** — mockup has no
  render-CLI dependency (the `.html`/wireframe file is the artifact), so `full`
  is a safe default (contrast mermaid, whose default `author` avoids `mmdc`).
- HTML mockup must be a **single self-contained static file** (inline CSS, no
  JS/CDN/framework) — opens anywhere, diff-able, portable; "effectiveness over
  looks".
- The `req_ids` carrier is human-visible in both fidelities: YAML frontmatter
  in the wireframe `.md`, a top-of-file HTML comment in the `.html` — the single
  human-visible claim of what the screen realizes, and the workflow's source for
  `trace write --req-ids`.
- The traceability spine is the core value: a mockup screen's REQ-IDs must show
  up in INDEX.md under the mockup column with no orphans — criterion 2.
- No synthetic render, ever — there is no render route for mockup (DESIGN §11).

</specifics>

<deferred>
## Deferred Ideas

- **Multiple screens per invocation** (one artifact carrying N screens, each with
  its own `req_ids`) — out of scope v1; one screen → one artifact → one `req_ids`
  set keeps carriage simple (D-01). Multi-screen UCs use multiple invocations or
  the Phase-5 conductor loop.
- **A `render` route / screenshot of the mockup** — deliberately excluded; the
  `.html`/wireframe file is the deliverable and synthetic render is a
  non-negotiable forbidden (DESIGN §11).
- **A ba-tools mockup validation command** (deterministic `.html`-extension /
  fidelity check) — chose workflow-level enforcement instead (D-05a); promote to
  a CLI command only if argument validation proves to need hash-provable rigor.
- **ASCII box-drawing wireframes** — chose markdown-structural blocks instead
  (D-04); revisit if structural blocks read too weakly as a UI sketch.

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-ba-mockup Operator*
*Context gathered: 2026-06-18*
