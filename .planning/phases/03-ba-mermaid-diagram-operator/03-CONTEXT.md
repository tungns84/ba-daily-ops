# Phase 3: ba-mermaid Diagram Operator - Context

**Gathered:** 2026-06-18
**Status:** Ready for planning

<domain>
## Phase Boundary

A use case or requirement becomes a **Mermaid diagram authored MD-inline** (a
```mermaid block inside a `.md` artifact, **no Mermaid CLI on the default
route**). Each diagram cites the **REQ-IDs it depicts** (`req_ids`) so those IDs
appear in the INDEX.md traceability matrix under the mermaid column. `mmdc`
export is an **optional** route that **hard-fails rather than synthesizing**
when the CLI is missing.

**Phase 3 requirements (3):** MMD-01 (UC/requirement → Mermaid, MD-inline first),
MMD-02 (each diagram cites `req_ids`), MMD-03 (`mmdc` render optional;
default route `author` has no CLI dependency; export hard-fails if CLI missing).

**Components delivered this phase:**
1. `ba-mermaid` skill (CDX pattern) — flat `.agents/skills/ba-mermaid/` SKILL.md
   (`name`+`description` only) + `agents/openai.yaml` (`interface.*`,
   `policy.allow_implicit_invocation: false`), copying the Phase-2
   `ba-srs-analyze` layout.
2. `ba-mermaid` thin workflow — resolves route → workflow file → follows it.
   Routes `author` (default) / `render` / `full`.
3. A diagram-author agent prompt (`ba-core/agents/`) — judges diagram type and
   the REQ-ID subset, writes the inline ```mermaid `.md` artifact.
4. `ba-tools mermaid-render` — NEW deterministic CLI command: extract the
   inline block → `.mmd` → resolve + invoke `mmdc` → emit image; hard-fail
   exit 2 when no CLI resolves.
5. Reuse of the existing `trace write --kind mermaid` + `index update`
   contract (Phase 2 D-04/D-05/D-13) — no schema change to the trace store.

**Explicitly NOT this phase:** `ba-mockup` (Phase 4), `ba-uc` conductor +
Safety gate GATE-03 (Phase 5), the `ba-make-diagram` formal-BPMN/draw.io plugin
(deferred v2), DOCX media-replace (deferred plugin). The mockup/story INDEX
columns stay empty until their phases.

</domain>

<decisions>
## Implementation Decisions

### Input contract + which REQ-IDs a diagram depicts (Area 1)
- **D-01:** Input is an **existing SRS `--slug`**. `ba-mermaid` reads
  `.ba-ops/srs/<slug>/requirements.json` (the Phase-2 canonical REQ-ID source,
  D-01/D-08) and the **agent picks the subset** of REQ-IDs the diagram depicts —
  a single UC flow rarely spans every requirement. The mermaid slug **ties to
  the srs slug** (artifacts land under `.ba-ops/mermaid/<slug>/`).
- **D-01a:** Subset selection is **agent judgement** (determinism boundary:
  ba-tools never infers which reqs to depict). The agent reads the canonical
  `requirements.json`; it does not invent REQ-IDs (any invented/unknown ID
  surfaces as an orphan downstream — see D-05).

### Diagram type selection + count (Area 2)
- **D-02:** **One diagram per invocation** by default; the **agent chooses the
  fitting Mermaid type** (flowchart / sequence / state / ER / class) from the
  UC/requirement shape. Type choice is judgement, honoring the determinism
  boundary.
- **D-02a:** Optional **`--diagram-type` flag** overrides the agent's choice
  (caller forces a specific type). Multiple-diagrams-per-invocation is **out of
  scope** for v1 (deferred — keeps `req_ids` carriage simple, one block → one
  `req_ids` set).

### req_ids carriage on the artifact (Area 3)
- **D-03:** The agent writes the depicted REQ-IDs into the **`.md` YAML
  frontmatter** (`req_ids: [FR-001, FR-002]`) — human-visible **and**
  machine-readable. The **thin workflow reads the frontmatter** and calls
  `ba-tools trace write --kind mermaid --slug <slug> --req-ids <list>
  --artifact <md> --source <srs requirements.json or source>`.
- **D-03a:** **No new ba-tools parser** — uses the existing explicit
  `--req-ids` flag on `trace write` (Phase 2 already requires explicit req-ids
  for non-srs kinds). The workflow does the frontmatter→flag hand-off; ba-tools
  receives an explicit list. Frontmatter is the single human-visible record of
  what the diagram claims to depict.

### Routes + default + what `full` does (Area 4)
- **D-04:** Routes are `author` (default) / `render` / `full`.
  `ba-tools resolve-route ba-mermaid` returns **`author`** (matches Phase 1
  static `DEFAULT_ROUTES`, ROADMAP criterion 1 "no Mermaid CLI invoked").
  - **`author`** — write the inline ```mermaid `.md` artifact only. **No CLI,
    no trace** (pure authoring; trace happens in `full`).
  - **`full`** — `author → trace write → index update`. **No render step** —
    the Mermaid CLI dependency stays out of the default-ish path.
  - **`render`** — export-only: run `mmdc` from an **existing** diagram `.md`
    (separate opt-in; never auto-invoked by `author`/`full`).

### mermaid-render command + output (Area 5)
- **D-05cmd:** Add a **new `ba-tools` command** (`mermaid-render`, exact name
  planner's call) — CLI invocation is file/command/hash-provable work, so it
  **belongs in ba-tools**, not an agent shell-out (determinism boundary,
  DESIGN §5/§11; no synthetic render path per §11 non-negotiables).
  - Extracts the ```mermaid block from the artifact `.md` → writes `.mmd`.
  - **Resolution chain:** `--mermaid-cli` flag → `$MERMAID_CLI` env → PATH
    `mmdc` → `npx -p @mermaid-js/mermaid-cli mmdc` (the `-p` flag is REQUIRED —
    package name ≠ binary name, per CLAUDE.md verified flag).
  - **No CLI resolves → `BaToolsError` exit 2.** Never produces a synthetic
    image (no Pillow/SVG-convert/screenshot — DESIGN §11).
- **D-05fmt:** Default output format **SVG** (text-based, diff-able, fits the
  text-first spine); `--format png|svg` override. Outputs land under
  `.ba-ops/mermaid/<slug>/`: `diagram.mmd` + `diagram.svg` (or `.png`).

### Orphan handling (Area 6)
- **D-05:** Cited REQ-IDs are validated **downstream by `index update`** — it
  flags an orphan when a mermaid trace cites a REQ-ID absent from the union of
  `requirements.json` (existing Phase 2 D-13 behavior). `trace write` records
  what it is given; **no change to `trace_cmd.py`**. Criterion 2 ("no orphans
  introduced") is met because a correct agent depicts only real IDs read from
  `requirements.json`; any slip is surfaced (not silently swallowed) by the
  INDEX Orphans section.

### Claude's Discretion (researcher / planner own these)
- Exact agent-prompt filename + body (suggest `ba-core/agents/ba-diagrammer.md`
  by analogy to `ba-srs-writer.md`); diagram-type heuristics within D-02.
- Exact `mermaid-render` subcommand name + flag spelling, and the inline-block
  extraction implementation (regex over the ```mermaid fence).
- The `--source` argument shape passed to `trace write` for kind=mermaid
  (the srs `requirements.json` path vs the source doc) — reconcile with the
  trace record schema (D-05/D-06 source_hash semantics from Phase 2).
- Skill/workflow physical file-layout reconciliation (same open item flagged in
  Phase 2: skills at `.agents/skills/ba-mermaid/`, workflow at
  `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md`, agent prompt at
  `ba-core/agents/`) — confirm Codex discovery.
- `openai.yaml` `interface.*` wording + keyword-dense SKILL.md `description`.
- Whether `mermaid-render` reuses Phase 2 `render_cmd.py` dispatch or is a new
  command module (it is a different render target — mmdc image, not JSON→MD).
- Test-fixture design for the 3 success criteria (author-without-CLI, req_ids→
  INDEX mermaid column no-orphan, render hard-fail when CLI absent).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture spec (source of truth)
- `DESIGN.md` — repo root. Most relevant Phase-3 sections: §3 (SKILL.md +
  `openai.yaml` flat-layout contract), §4 (thin-orchestrator pattern, route
  table — `ba-mermaid` → `author`; "pass paths not content"), §5 (determinism
  boundary, render backends, "run mmdc and capture exact command + exit code"),
  the **render-backend resolution** block (mermaid: `--mermaid-cli` →
  `$MERMAID_CLI` → PATH `mmdc` → `npx @mermaid-js/mermaid-cli`), §6 (gates;
  Safety gate is plugin-only but the no-synthetic-render rule applies),
  §8 (`.ba-ops/` spine — `mermaid/<slug>/`, INDEX.md mermaid column),
  §11 (non-negotiables: real render CLIs only, no synthetic image, no
  hard-coded paths). §10 "DONE" markers are aspirational, not current state.

### Requirements & scope
- `.planning/REQUIREMENTS.md` — REQ-ID registry; Phase-3 requirement text
  MMD-01/02/03 + resolved Open Decisions table.
- `.planning/ROADMAP.md` — Phase 3 goal + 3 success criteria (TRUE-conditions
  the verifier checks: author-no-CLI, req_ids→INDEX mermaid column no-orphan,
  render hard-fail when CLI missing).
- `.planning/PROJECT.md` — v1 daily spine; determinism boundary; "two render
  backends never crossed" (`ba-mermaid` daily vs `ba-make-diagram` plugin).

### Phase 2 outputs to build ON (read the code + the contract, not just docs)
- `.planning/phases/02-ba-srs-analyze-quality-gate-traceability-core/02-CONTEXT.md`
  — the trace/index contract this phase consumes: D-04 (uniform trace record →
  index reads only records), **D-05 trace record schema** (`kind`, `slug`,
  `req_ids: [{id, statement_hash}]`, `source_hash`), D-08 (orphan definition),
  D-13/D-13a (INDEX status + Gaps/Orphans sections; gap = no downstream
  coverage). **This is the contract ba-mermaid writes to.**
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/trace_cmd.py` — already
  supports `--kind mermaid` with explicit `--req-ids`/`--req-ids-file`; validates
  kind/slug regex `^[a-z0-9][a-z0-9-]*$`; FileLock(timeout=10). **Reuse as-is.**
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/index_cmd.py` — orphan/
  gap/stale detection over trace records (D-05 orphan flagging). **Reuse as-is.**
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/render_cmd.py` — Phase 2
  JSON→IEEE-830 render (a DIFFERENT target). Reference for command-module shape;
  `mermaid-render` is a new render target (mmdc image).
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/resolve_route.py` +
  the `DEFAULT_ROUTES` dict — register `ba-mermaid → author`.
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/init_cmd.py`
  (`OPERATOR_ROUTES`) — register `ba-mermaid` full route list
  (`author|render|full`).
- `.agents/ba-daily-operators/ba-tools/ba_tools/__main__.py` — argparse
  dispatcher; register the new `mermaid-render` subcommand here.
- `.agents/ba-daily-operators/ba-tools/ba_tools/repo.py` — `resolve_under_root` /
  `is_within_root` path-traversal safety; reuse for all new path inputs.
- `.agents/ba-daily-operators/ba-tools/ba_tools/output.py` (`ok_json`) +
  `errors.py` (`BaToolsError`, exit 2) — the flat envelope / hard-fail contract
  the `mermaid-render` command must follow.
- `.agents/skills/ba-srs-analyze/SKILL.md` + `.../agents/openai.yaml` +
  `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` +
  `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md` — **the exact
  layout `ba-mermaid` copies** (skill frontmatter, openai.yaml nesting, thin
  per-route workflow body, agent role-contract prompt).
- `.agents/ba-daily-operators/ba-core/references/gates.md` — gate contract;
  Safety-gate render rules (CLI-only, no synthetic) inform `mermaid-render`.

### Tech stack (verified research)
- `CLAUDE.md` (repo root) — verified stack: Python 3.11+ stdlib-first,
  `sys.executable`, paths under `--repo-root`; **`mmdc` resolution chain +
  `npx -p @mermaid-js/mermaid-cli mmdc` (`-p` required)**; draw.io/mermaid CLI
  invocation flags (`mmdc -i in.mmd -o out.svg`); Codex skill contract; byte
  budgets (AGENTS.md/eager refs < 32,768 B).

### Referenced-but-confirm
- `.ba-ops/mermaid/<slug>/` — the artifact home. The `.ba-ops/mermaid/` parent
  is already scaffolded (Phase 1 `scaffold.py`); confirm per-slug subdir creation.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`trace_cmd.py`** — already accepts `--kind mermaid` + explicit `--req-ids`;
  no change needed. The mermaid→INDEX wiring is essentially free (Phase 2 built
  the contract to carry mermaid/mockup/story kinds — 02-CONTEXT integration note).
- **`index_cmd.py`** — orphan/gap/stale detection already populates the mermaid
  column from trace records; reuse as-is (D-05 orphan path).
- **`resolve_route.py` / `init_cmd.py`** — register `ba-mermaid` route table +
  default `author` (small additive change, mirrors how ba-srs-analyze was added).
- **`output.py::ok_json` + `errors.py::BaToolsError`** — flat envelope / exit-2
  for the new `mermaid-render` command.
- **`repo.py` path-safety** — reuse for `--mermaid-cli`, artifact path, and
  output path inputs (path-traversal guard).
- **ba-srs-analyze skill + workflow + agent prompt** — the template `ba-mermaid`
  copies wholesale (only the route bodies + agent role differ).

### Established Patterns
- Subcommands register via `register(subparsers)` in `ba_tools/commands/*.py`,
  wired in `__main__.py` — follow for `mermaid_render_cmd.py`.
- Skill = flat `.agents/skills/<op>/` (SKILL.md `name`+`description` only) +
  `agents/openai.yaml` (`interface.*`, `policy.allow_implicit_invocation:false`)
  + thin workflow `ba-core/workflows/<op>.md` resolving route→steps + agent
  prompt `ba-core/agents/<role>.md`.
- "Pass paths, not content" — the workflow hands the agent the slug +
  `requirements.json` path; the agent Reads it and writes the diagram `.md`.
- Render CLI invocation = ba-tools (deterministic, capture exact command +
  exit code); agents never shell out to `mmdc`.

### Integration Points
- Consumes the Phase-2 traceability spine: reads `.ba-ops/srs/<slug>/
  requirements.json` (REQ-ID source), writes `.ba-ops/mermaid/<slug>/` artifacts,
  calls `trace write --kind mermaid` + `index update` to populate the INDEX
  mermaid column.
- First **render-capable spine route** — establishes the `mmdc` resolution +
  hard-fail pattern that Phase 4 (`ba-mockup` html) and the deferred render
  plugins will mirror.

</code_context>

<specifics>
## Specific Ideas

- Default route `author` must invoke **zero** CLI — the diagram is just an inline
  ```mermaid fence in a `.md`. This is the daily-loop happy path; render is the
  exception you opt into.
- `req_ids` in YAML frontmatter is the **single human-visible claim** of what the
  diagram depicts — readable in the Codex chat, and the workflow's source for
  `trace write --req-ids`.
- The traceability spine is the core value: a mermaid diagram's REQ-IDs must show
  up in INDEX.md under the mermaid column with no orphans — that is what
  criterion 2 proves.
- No synthetic render, ever — `mermaid-render` hard-fails (exit 2) rather than
  faking an image when no `mmdc` resolves (DESIGN §11 non-negotiable).

</specifics>

<deferred>
## Deferred Ideas

- **Multiple diagrams per invocation** (several ```mermaid blocks in one `.md`,
  each with its own `req_ids`) — out of scope v1; one diagram → one req_ids set
  keeps carriage simple (D-02a).
- **Pre-validating REQ-IDs at `trace write`** (block orphans at write time with a
  registry check) — chosen the Phase-2 downstream `index update` detection
  instead (D-05); promote to a hard write-time gate only if orphans prove common.
- **`full` running render** — deliberately excluded; render stays a separate
  opt-in route so the CLI dependency never enters the default path (D-04).
- **Formal BPMN / draw.io diagrams** (`ba-make-diagram`) and the render manifest
  / hash-provable embedded media — deferred v2 plugin (PROJECT.md "two render
  backends never crossed").

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 3-ba-mermaid Diagram Operator*
*Context gathered: 2026-06-18*
