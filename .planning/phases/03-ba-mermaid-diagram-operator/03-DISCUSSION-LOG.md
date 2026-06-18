# Phase 3: ba-mermaid Diagram Operator - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-18
**Phase:** 3-ba-mermaid Diagram Operator
**Areas discussed:** Input & REQ-IDs, Diagram type, req_ids carriage, Render route (command), Routes, Orphan guard, Render output

---

## Input & REQ-IDs

| Option | Description | Selected |
|--------|-------------|----------|
| SRS slug + agent subset | Input is an existing srs `--slug`; agent reads `requirements.json` and picks the subset of REQ-IDs the diagram depicts | ✓ |
| Explicit --req-ids | Caller passes `--req-ids FR-001,FR-002`; agent diagrams exactly those | |
| Raw source doc | Input is a UC/source `.md`; agent diagrams from prose and self-assigns REQ-IDs (orphan risk) | |

**User's choice:** SRS slug + agent subset
**Notes:** Ties the mermaid slug to the srs slug; canonical REQ-ID source is the Phase-2 `requirements.json`. Subset selection is agent judgement (determinism boundary).

---

## Diagram type

| Option | Description | Selected |
|--------|-------------|----------|
| Agent discretion, one default | Agent picks fitting type (flowchart/sequence/state/ER/class); one diagram/invocation; `--diagram-type` override | ✓ |
| Required --diagram-type flag | Caller must specify type; agent only renders | |
| Agent, multiple allowed | Agent may emit several diagrams in one `.md`, each with its own req_ids | |

**User's choice:** Agent discretion, one default
**Notes:** Multiple-diagrams deferred to keep `req_ids` carriage simple (one block → one set).

---

## req_ids carriage

| Option | Description | Selected |
|--------|-------------|----------|
| YAML frontmatter, workflow passes --req-ids | Agent writes req_ids into `.md` frontmatter; workflow reads them and calls `trace write --req-ids` | ✓ |
| New ba-tools parser | Add a command that parses req_ids out of the diagram `.md` | |
| --req-ids-file JSON | Agent emits a `req_ids.json`; workflow passes `--req-ids-file` | |

**User's choice:** YAML frontmatter, workflow passes --req-ids
**Notes:** No new ba-tools parsing — uses the existing explicit `--req-ids` flag. Frontmatter is the human-visible claim.

---

## Render route (command)

| Option | Description | Selected |
|--------|-------------|----------|
| New ba-tools render command | `ba-tools mermaid-render`: extract block → `.mmd` → resolve+invoke `mmdc` → image; hard-fail exit 2 if none | ✓ |
| Agent shells out directly | Workflow/agent runs `mmdc` itself (non-deterministic shell-out, weaker provenance) | |

**User's choice:** New ba-tools render command
**Notes:** CLI invocation = file/command-provable = belongs in ba-tools (determinism boundary, DESIGN §5/§11). No synthetic render path.

---

## Routes (default + `full`)

| Option | Description | Selected |
|--------|-------------|----------|
| author default; full = author+trace+index | `full` does NOT render; render stays a separate opt-in route | ✓ |
| author default; full includes render | `full` runs the render step at the end (pulls CLI into full) | |

**User's choice:** author default; full = author+trace+index (A)
**Notes:** `resolve-route ba-mermaid → author`; CLI dependency stays out of the default-ish path.

---

## Orphan guard

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-validate in trace write | `trace write` checks each REQ-ID exists in registry; unknown → exit 2 | |
| Detect downstream in index update | `trace write` records as-given; `index update` flags orphans (Phase 2 D-13) | ✓ |
| Both | Workflow check + index update flag | |

**User's choice:** Detect downstream in index update (B)
**Notes:** Matches Phase 2 design; no change to `trace_cmd.py`. Orphan surfaces in INDEX Orphans section.

---

## Render output

| Option | Description | Selected |
|--------|-------------|----------|
| SVG default, --format png\|svg | Default SVG (text-based, diff-able, fits text-first spine) | ✓ |
| PNG default, --format png\|svg | Default PNG (matches DESIGN render examples) | |
| Required --format | No default; caller must pass `--format` | |

**User's choice:** SVG default, --format png|svg (A)
**Notes:** Outputs `.ba-ops/mermaid/<slug>/diagram.mmd` + `diagram.svg` (or `.png`).

---

## Claude's Discretion

- Agent-prompt filename + body (suggest `ba-core/agents/ba-diagrammer.md`); diagram-type heuristics.
- Exact `mermaid-render` subcommand name + flag spelling; inline-block extraction implementation.
- `--source` argument shape for `trace write --kind mermaid` (reconcile with D-05/D-06 source_hash semantics).
- Skill/workflow physical file-layout reconciliation; Codex discovery confirmation.
- `openai.yaml` `interface.*` wording + keyword-dense SKILL.md `description`.
- Whether `mermaid-render` reuses `render_cmd.py` dispatch or is a new module.
- Test-fixture design for the 3 success criteria.

## Deferred Ideas

- Multiple diagrams per invocation (one block → one req_ids set chosen for v1).
- Pre-validating REQ-IDs at `trace write` (chose downstream `index update` detection).
- `full` running render (render stays separate opt-in).
- Formal BPMN / draw.io (`ba-make-diagram`) + render manifest / hash-provable embedded media — deferred v2 plugin.
