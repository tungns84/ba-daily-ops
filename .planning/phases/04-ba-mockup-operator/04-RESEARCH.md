# Phase 4: ba-mockup Operator — Research

**Researched:** 2026-06-18
**Domain:** Codex skill operator (CDX flat layout), thin workflow, agent-prompt authoring, fidelity-branched artifact (html/wireframe), traceability via existing trace write + index update
**Confidence:** HIGH — Phase 3 is the verified template; ba-tools commands confirmed by direct code read

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** One screen per invocation. `screen` route = one artifact = one `req_ids` set.
- **D-01a:** Input is an existing SRS `--slug`. `ba-mockup` reads `.ba-ops/srs/<slug>/requirements.json`. Agent picks the REQ-ID subset. Artifacts land under `.ba-ops/mockup/<slug>/`.
- **D-02:** REQ-IDs written into the artifact; thin workflow reads them and calls `ba-tools trace write --kind mockup --slug <slug> --req-ids <list> --artifact <file> --source <srs requirements.json>`. No new ba-tools parser. Carrier: YAML frontmatter in `.md`, HTML comment first line in `.html`.
- **D-03:** `html` fidelity = single self-contained static `.html`, all CSS in `<style>` tag, zero external assets / JS / CDN / framework.
- **D-04:** `wireframe` fidelity = inline markdown-structural blocks in `.md` — headings + lists + tables describing layout regions (not ASCII box-drawing). `req_ids` in YAML frontmatter.
- **D-05:** Routes: `screen` = author-only (no CLI, no trace); `full` (default) = author → trace write → index update. No render route.
- **D-05a:** `--fidelity` required and enforced by the thin workflow (hard-rejects missing/invalid). Zero new ba-tools commands this phase.
- **D-06:** Orphan validation is downstream only — `index update` flags orphans; `trace write` records what it receives without validation.

### Claude's Discretion

- Exact mockup-author agent-prompt filename + body (`ba-core/agents/ba-mockup-author.md` suggested).
- Exact `.html` scaffold (DOCTYPE, semantic-HTML structure, minimal inline-CSS conventions) within D-03.
- Exact markdown-structural wireframe layout conventions within D-04.
- Exact regex for extracting HTML-comment `req_ids` and `.md` frontmatter `req_ids` in the workflow hand-off.
- The `--source` argument shape for `trace write --kind mockup` (reconcile with Phase-2 source_hash semantics).
- Skill/workflow physical file-layout reconciliation — confirm Codex discovery.
- `openai.yaml` `interface.*` wording + keyword-dense SKILL.md `description`.
- Test-fixture design for the 3 success criteria.

### Deferred Ideas (OUT OF SCOPE)

- Multiple screens per invocation.
- A render route / screenshot of the mockup.
- A ba-tools mockup validation command (ba-tools does NOT get a new command this phase).
- ASCII box-drawing wireframes.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MOCK-01 | `ba-mockup` turns requirements into a UI mockup at `--fidelity html\|wireframe` (fidelity required) | Workflow-level fidelity enforcement; regex extraction of req_ids by fidelity type; no new ba-tools command needed |
| MOCK-02 | Each screen cites the REQ-IDs it realizes (`req_ids`) | HTML comment or YAML frontmatter carrier; existing `trace write --kind mockup --req-ids` handles persistence |
| MOCK-03 | `html` writes a `.html` artifact; `wireframe` writes inline blocks in a `.md` | Fidelity branch in workflow + agent prompt schema per fidelity; confirmed by code read |
</phase_requirements>

---

## Summary

Phase 4 is a near-exact mirror of Phase 3 (ba-mermaid). The code base already carries every ba-tools primitive needed: `trace write` already accepts `--kind mockup`; `index_cmd.py` already renders the Mockup column; `resolve_route.py` already maps `ba-mockup → full`; `init_cmd.py` already lists `["screen", "full"]`; `scaffold.py` already creates `.ba-ops/mockup/`. The only new artifacts are: (1) `.agents/skills/ba-mockup/SKILL.md` + `agents/openai.yaml`, (2) `ba-core/workflows/ba-mockup.md`, (3) `ba-core/agents/ba-mockup-author.md`, and (4) three test files mirroring the mermaid test pattern.

The principal differences from Phase 3 are: no render route (the `.html`/wireframe artifact IS the deliverable), `--fidelity` required by the workflow (not ba-tools), fidelity-branched artifact schema (HTML comment vs YAML frontmatter for req_ids, `.html` vs `.md` output file), and the source_hash is pinned to `requirements.json` — same as mermaid (confirmed by reading trace_cmd.py and the ba-mermaid workflow Step 2 comment).

**Primary recommendation:** Copy ba-mermaid wholesale; replace route bodies and agent schema per fidelity branch; add the `--fidelity` enforcement gate in the workflow; use the mermaid trace/index tests as the direct structural template for the three mockup test files.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `--fidelity` argument validation + rejection | Workflow Layer | — | D-05a: workflow-level enforcement; ba-tools adds no new command |
| req_ids extraction from artifact | Workflow Layer | — | Thin workflow reads the artifact and calls trace write; no new ba-tools parser |
| Mockup artifact authoring (HTML/wireframe) | Agent Layer | — | Determinism boundary: ba-tools proves, agents author |
| Traceability persistence | CLI Tools Layer (trace write) | — | Existing TOOL-07; no changes |
| INDEX.md mockup column + orphan detection | CLI Tools Layer (index update) | — | Existing TOOL-08; no changes |
| File-state storage | File-State Layer (.ba-ops/mockup/) | — | Already scaffolded |

---

## Phase 3 Reuse Verification (confirmed by direct code read)

All claims below are `[VERIFIED]` by reading the exact source files listed.

| Claim | File | Evidence |
|-------|------|---------|
| `trace write` accepts `--kind mockup` | `trace_cmd.py` lines 54-55 | `help="Artifact kind, e.g. srs, mermaid, mockup, story"` |
| `trace write` requires `--req-ids` for non-srs kinds | `trace_cmd.py` lines 229-236 | `raise BaToolsError MISSING_REQ_IDS` when kind != srs and no req-ids |
| `resolve_route` already has `ba-mockup → full` | `resolve_route.py` line 17 | `"ba-mockup": "full"` in DEFAULT_ROUTES dict |
| `init` already has `ba-mockup: ["screen", "full"]` | `init_cmd.py` line 29 | `"ba-mockup": ["screen", "full"]` in OPERATOR_ROUTES dict |
| `scaffold.py` already creates `.ba-ops/mockup/` | `scaffold.py` line 157 | `_SUBDIRS = ["srs", "mermaid", "mockup", "backlog", "plugins", "traces"]` |
| `index_cmd.py` already renders Mockup column | `index_cmd.py` lines 212-213 | `"| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |"` in matrix header |
| Orphan detection works for any non-srs kind | `index_cmd.py` lines 159-167 | Iterates all records where `kind != "srs"` — mockup records are captured automatically |
| DESIGN §4 table lists `ba-mockup: screen, full, default full` | `DESIGN.md` line 203 | `"ba-mockup" \| screen, full \| full (\`--fidelity\` still required)` |

**Conclusion:** Zero ba-tools code changes required this phase. [VERIFIED: direct code read]

---

## Standard Stack

### Core (all existing — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`pathlib`, `re`, `json`) | 3.11+ | Workflow regex extraction, path ops | Already in use across all phases |
| `ba-tools` CLI (existing) | project | `trace write`, `index update`, `init`, `resolve-route` | Phase 2+3 baseline; no additions this phase |

### No new packages this phase

`[VERIFIED: CONTEXT.md D-05a]` — "Zero new ba-tools commands this phase." No Python package additions, no npm additions.

---

## Architecture Patterns

### System Architecture Diagram

```
User invokes $ba-mockup --slug <slug> --fidelity html|wireframe
       |
SKILL LAYER      .agents/skills/ba-mockup/SKILL.md
       |              (discovery: name + description frontmatter only)
       |         agents/openai.yaml (interface.* + policy.allow_implicit_invocation: false)
       |
WORKFLOW LAYER   ba-core/workflows/ba-mockup.md
       |              Step 1: ba-tools init ba-mockup → context JSON
       |              Step 2: validate --fidelity (reject missing/invalid) [WORKFLOW-ENFORCED]
       |              Step 3: dispatch on --route (screen | full)
       |
       |──── Route: screen ────────────────────────────────────────────────┐
       |              Read ba-core/agents/ba-mockup-author.md              |
       |              Pass payload (paths only): slug, fidelity,           |
       |                requirements_json path, route=screen               |
       |              Agent reads requirements.json, writes artifact        |
       |              Output: .ba-ops/mockup/<slug>/<screen-name>.<ext>    |
       |                     (.html for html fidelity, .md for wireframe)  |
       |                                                                    |
       |──── Route: full ─────────────────────────────────────────────────┘
                     Step 1: author (same as screen route)
                     Step 2: read req_ids from artifact
                             html: regex `<!-- req_ids: \[([^\]]*)\] -->`
                             md:   regex `^req_ids:\s*\[([^\]]*)\]`
                     Step 3: ba-tools trace write --kind mockup --slug <slug>
                               --artifact .ba-ops/mockup/<slug>/<file>
                               --source-doc .ba-ops/srs/<slug>/requirements.json
                               --requirements .ba-ops/srs/<slug>/requirements.json
                               --req-ids <extracted list>
                     Step 4: ba-tools index update
                             (populates INDEX.md Mockup column; flags orphans)
```

### Recommended Project Structure (new files only)

```
.agents/
├── skills/
│   └── ba-mockup/                          # NEW — mirrors ba-mermaid/
│       ├── SKILL.md                        # name + description only (CDX contract)
│       └── agents/
│           └── openai.yaml                 # interface.* + policy.*
└── ba-daily-operators/
    └── ba-core/
        ├── workflows/
        │   └── ba-mockup.md                # NEW — thin orchestrator
        └── agents/
            └── ba-mockup-author.md         # NEW — author role contract
tests/
├── fixtures/
│   └── mockup/                             # NEW — mirrors fixtures/mermaid/
│       ├── authored_html.html              # fixture: valid html artifact
│       ├── authored_wireframe.md           # fixture: valid wireframe artifact
│       └── mockup_requirements.json        # fixture: FR-001, FR-002
├── test_mockup_author.py                   # NEW — criterion 1 + fidelity-branch
├── test_mockup_trace_index.py              # NEW — criterion 2 + 3
```

---

## Claude's Discretion — Resolved Items

### 1. HTML Scaffold Conventions (D-03)

Single self-contained static `.html` file. No JS, no CDN, no framework. All CSS inline in `<style>`.

**Canonical skeleton:**

```html
<!-- req_ids: [FR-001, FR-002] -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title><Screen Name> — <Slug></title>
  <style>
    /* reset */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; font-size: 1rem; line-height: 1.5;
           background: #f9f9f9; color: #1a1a1a; padding: 1rem; }
    /* layout */
    .page { max-width: 960px; margin: 0 auto; }
    header { padding: 1rem; background: #ffffff; border-bottom: 2px solid #dee2e6; }
    nav { background: #343a40; padding: 0.5rem 1rem; }
    nav a { color: #ffffff; text-decoration: none; margin-right: 1rem; }
    main { padding: 1rem; }
    .card { background: #ffffff; border: 1px solid #dee2e6; border-radius: 4px;
            padding: 1rem; margin-bottom: 1rem; }
    footer { padding: 0.75rem; text-align: center; font-size: 0.875rem;
             color: #6c757d; border-top: 1px solid #dee2e6; }
    /* forms */
    label { display: block; margin-bottom: 0.25rem; font-weight: 500; }
    input, select, textarea { width: 100%; padding: 0.375rem 0.75rem;
                              border: 1px solid #ced4da; border-radius: 4px;
                              font-size: 1rem; }
    button { padding: 0.5rem 1rem; background: #0d6efd; color: #ffffff;
             border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
    button:hover { background: #0b5ed7; }
    /* table */
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #dee2e6; }
    th { background: #f1f3f5; font-weight: 600; }
  </style>
</head>
<body>
  <div class="page">
    <header>
      <h1><Screen Name></h1>
    </header>
    <nav>
      <!-- navigation items -->
    </nav>
    <main>
      <!-- primary content region -->
    </main>
    <footer>Mockup — <slug> | req_ids: [FR-001, FR-002]</footer>
  </div>
</body>
</html>
```

**Rules:**
- `<!-- req_ids: [...] -->` MUST be the first line of the file (before `<!DOCTYPE>`).
- All CSS lives inside the single `<style>` block in `<head>`.
- Semantic elements: `<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`, `<form>`, `<table>` as appropriate.
- No `<script>` tags, no `src=`, no `href=` pointing to external URLs.
- File extension is `.html`. Filename convention: `<screen-name>.html` (e.g. `login.html`, `order-list.html`).

### 2. Wireframe Markdown Structural Layout Conventions (D-04)

```markdown
---
req_ids: [FR-001, FR-002]
fidelity: wireframe
slug: <slug>
screen: <screen-name>
---

# <Screen Name>

> Wireframe — req_ids: [FR-001, FR-002]

## Layout

### Header

- **Logo** [left]
- **Primary nav**: Home | Orders | Reports | Settings [center]
- **User menu**: Avatar + dropdown [right]

### Main Content

#### Section: <Primary Region Name>

| Region | Type | Content |
|--------|------|---------|
| Left sidebar | nav list | Filter controls |
| Main panel | data table | Order rows (ID, Status, Date, Amount) |
| Right panel | form | Detail editor |

#### Actions

- [Primary CTA] — submits / confirms
- [Secondary CTA] — cancels / resets
- [Destructive Action] — delete (requires confirmation)

### Footer

- Status bar [left]: "N items selected"
- Pagination controls [right]: Prev | 1 2 3 | Next

## Interaction Notes

- <screen-name> is read-only until user clicks Edit.
- Form validation: required fields marked with *.
```

**Rules:**
- YAML frontmatter at top: `req_ids`, `fidelity: wireframe`, `slug`, `screen` fields.
- Headings describe regions; lists describe elements within regions; tables describe structured content areas.
- No ASCII box-drawing characters (`+`, `|` in box-drawing context, `─`, `│`).
- File extension is `.md`. Filename convention: `<screen-name>.md` (e.g. `login.md`, `order-list.md`).

### 3. Exact Regex for req_ids Extraction in the Workflow

The workflow reads the artifact after authoring and extracts `req_ids` to pass to `trace write --req-ids`.

**For `.html` artifacts (HTML comment first line):**

```python
# Pattern: <!-- req_ids: [FR-001, FR-002] -->
import re
_HTML_REQ_IDS_RE = re.compile(r'<!--\s*req_ids:\s*\[([^\]]*)\]\s*-->')

def extract_req_ids_html(text: str) -> list[str]:
    """Extract req_ids from HTML comment on the first line."""
    first_line = text.splitlines()[0] if text.strip() else ""
    m = _HTML_REQ_IDS_RE.search(first_line)
    if not m:
        return []
    return [rid.strip() for rid in m.group(1).split(",") if rid.strip()]
```

**For `.md` artifacts (YAML frontmatter):**

```python
# Pattern: req_ids: [FR-001, FR-002]  (inline YAML list, in frontmatter block)
_MD_REQ_IDS_RE = re.compile(r'^req_ids:\s*\[([^\]]*)\]', re.MULTILINE)

def extract_req_ids_md(text: str) -> list[str]:
    """Extract req_ids from YAML frontmatter inline list."""
    m = _MD_REQ_IDS_RE.search(text)
    if not m:
        return []
    return [rid.strip() for rid in m.group(1).split(",") if rid.strip()]
```

**Workflow usage (Codex agent, not Python):**

The thin workflow is a Markdown instruction file, not Python. The workflow instructs the agent to:

1. Read the artifact file.
2. For `--fidelity html`: scan the first line for `<!-- req_ids: [...] -->` and extract the bracketed list.
3. For `--fidelity wireframe`: scan the YAML frontmatter block (between `---` delimiters) for `req_ids: [...]` and extract the bracketed list.
4. Split on `,`, strip whitespace, pass as `--req-ids FR-001,FR-002`.

The regex patterns above serve as the reference specification for the workflow instruction text and for the test assertions.

### 4. `--source-doc` Argument Shape for `trace write --kind mockup`

**Resolved by reading the ba-mermaid workflow (full route Step 2) and `trace_cmd.py`:**

```
ba-tools trace write \
  --kind mockup \
  --slug <slug> \
  --artifact .ba-ops/mockup/<slug>/<screen-name>.<ext> \
  --source-doc .ba-ops/srs/<slug>/requirements.json \
  --requirements .ba-ops/srs/<slug>/requirements.json \
  --req-ids <comma-separated req_ids>
```

`--source-doc` = `requirements.json` (NOT the mockup artifact itself). This is the same resolution as mermaid Phase 3 — the comment in `ba-mermaid.md` Route: full Step 2 states: "Note: `--source-doc` is the SRS `requirements.json` — not the diagram `.md` itself. This records `source_hash` = SHA-256 of the requirements current when the diagram was authored, enabling drift detection (D-06)."

**Implication:** `source_hash` = SHA-256 of `.ba-ops/srs/<slug>/requirements.json` at authoring time. `index update` later re-hashes that file and reports `stale` if it has changed — identical semantics to mermaid. `[VERIFIED: ba-mermaid.md Route: full Step 2]`

### 5. Agent Prompt Filename and Codex Discoverable Layout

**Filename:** `ba-core/agents/ba-mockup-author.md`

Full path: `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md`

This mirrors `ba-diagrammer.md` (same `ba-core/agents/` directory, same naming convention `ba-<role>.md`).

**Codex discovery path (confirmed):**

```
.agents/skills/ba-mockup/           <- Codex recursive skill loader finds this
  SKILL.md                          <- frontmatter: name: ba-mockup + description
  agents/
    openai.yaml                     <- interface.* + policy.*
```

Workflow reference in `openai.yaml` `default_prompt` and in `SKILL.md` body comment points to:

```
.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md
```

The `ba-core/agents/ba-mockup-author.md` is READ by the workflow agent (not auto-loaded by Codex). The workflow step says "Open .agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md and follow the author role." This is the same discovery mechanism as ba-diagrammer — workflow-directed Read, not skill auto-discovery. `[VERIFIED: ba-mermaid.md Route: author Step 3]`

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| req_ids validation against SRS | Don't add a new ba-tools validator | `index update` orphan detection | D-06 / D-05a: validation is downstream only; adding a validator this phase violates the zero-new-commands constraint |
| Fidelity argument validation | Don't add a ba-tools flag | Workflow-level `if --fidelity not in [html, wireframe]: hard-reject` | D-05a: workflow enforces; ba-tools proves nothing here |
| req_ids extraction from artifact | Don't add a ba-tools parser | Workflow reads artifact; agent extracts and passes `--req-ids` | D-02: "no new ba-tools parser" |
| CSS framework for html fidelity | Don't link Tailwind / Bootstrap / CDN | Inline `<style>` block | D-03: self-contained, zero external assets |

---

## Common Pitfalls

### Pitfall 1: `<!-- req_ids: ... -->` Must Be the FIRST Line

**What goes wrong:** If the `req_ids` HTML comment is anywhere other than line 1 of the `.html` file, the workflow regex (or a future ba-tools validator) may miss it, or diff readability degrades.

**How to avoid:** `ba-mockup-author.md` must specify: "Write `<!-- req_ids: [...] -->` as the absolute first line, before `<!DOCTYPE html>`."

**Warning signs:** Test `test_html_req_ids_comment_is_first_line` fails.

### Pitfall 2: Wrong `--source-doc` Path in `trace write`

**What goes wrong:** Passing the `.html`/`.md` mockup artifact as `--source-doc` instead of `requirements.json`. The `source_hash` then tracks the artifact, not the source — drift detection becomes meaningless.

**How to avoid:** The workflow must explicitly say: "`--source-doc` is `.ba-ops/srs/<slug>/requirements.json`" (verbatim, same as ba-mermaid.md Step 2 note). Tests `test_trace_source_doc_is_requirements_json` catches this if written.

### Pitfall 3: Agent Invents REQ-IDs Not in requirements.json

**What goes wrong:** Agent writes `req_ids: [FR-099]` for an ID that does not exist. Trace write succeeds (it accepts any ID — D-06). Index update then lists FR-099 as an orphan. This is criterion 3 — it IS supposed to surface as orphan. The pitfall is writing the agent prompt without the anti-invention instruction.

**How to avoid:** `ba-mockup-author.md` must include the same `req_ids discipline` section as `ba-diagrammer.md`: "Do NOT invent REQ-IDs not present in `requirements.json`."

### Pitfall 4: `--fidelity` Enforcement Placed in Wrong Layer

**What goes wrong:** Attempting to add a ba-tools argument validator (new command) instead of enforcing at the workflow level. This violates D-05a and the zero-new-commands constraint.

**How to avoid:** The workflow hard-rejects before the agent step: "If `--fidelity` is absent or not in `[html, wireframe]`, emit an error message and stop." No ba-tools call involved.

### Pitfall 5: Wireframe Uses ASCII Box-Drawing

**What goes wrong:** Agent writes `+--------+` style wireframe. D-04 explicitly chose markdown-structural blocks over ASCII box-drawing.

**How to avoid:** `ba-mockup-author.md` must say "Use headings, lists, and tables to describe layout regions. Do NOT use ASCII box-drawing characters."

### Pitfall 6: SKILL.md Has Extra Frontmatter Fields

**What goes wrong:** Adding `routes:`, `default_route:`, or other fields to the SKILL.md frontmatter. Codex docs confirm: frontmatter carries ONLY `name` + `description`.

**How to avoid:** Copy ba-mermaid's SKILL.md exactly; only change `name` and `description` content. `test_skill_schema.py` (existing) already validates the schema.

---

## Code Examples

### Workflow: ba-mockup.md Structure (canonical)

```markdown
---
operator: ba-mockup
default_route: full
routes:
  - screen
  - full
---

# ba-mockup Workflow

...preamble (determinism boundary, sequential execution, pass paths not content)...

## Route: screen

Author the artifact only. No CLI invocation, no trace write.

**Steps:**

1. Run `ba-tools resolve-route ba-mockup` to confirm default route = `full`.
2. Validate `--fidelity`: must be `html` or `wireframe`. If absent or invalid, stop with error.
3. Run `ba-tools init ba-mockup` for scaffold context.
4. Open `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` and follow the author role.
5. Pass this payload (paths only):
   ```
   requirements_json: .ba-ops/srs/<slug>/requirements.json
   slug:              <slug>
   fidelity:          <html|wireframe>
   screen_name:       <chosen by agent from UC/requirement>
   route:             screen
   ```
6. Agent writes `.ba-ops/mockup/<slug>/<screen-name>.html` (html) or
                 `.ba-ops/mockup/<slug>/<screen-name>.md` (wireframe).

**Output:** `.ba-ops/mockup/<slug>/<screen-name>.<ext>`

---

## Route: full

End-to-end: author → trace write → index update.

### Step 1 — Author screen

Follow the **screen route** steps above (steps 1–6).

### Step 2 — Extract req_ids

Read the authored artifact.

- **html fidelity:** First line of the file contains `<!-- req_ids: [FR-001, FR-002] -->`.
  Extract the bracketed list, split on `,`, strip whitespace.
- **wireframe fidelity:** YAML frontmatter (between `---` delimiters) contains `req_ids: [FR-001, FR-002]`.
  Extract the bracketed list, split on `,`, strip whitespace.

### Step 3 — Trace write

Run:
```
ba-tools trace write \
  --kind mockup \
  --slug <slug> \
  --artifact .ba-ops/mockup/<slug>/<screen-name>.<ext> \
  --source-doc .ba-ops/srs/<slug>/requirements.json \
  --requirements .ba-ops/srs/<slug>/requirements.json \
  --req-ids <comma-separated req_ids from Step 2>
```

Note: `--source-doc` is the SRS `requirements.json` — NOT the mockup artifact itself.

### Step 4 — Index update

Run `ba-tools index update`
```

### SKILL.md: ba-mockup (canonical)

```yaml
---
name: ba-mockup
description: >
  Turn requirements into a UI mockup at a required --fidelity of html or wireframe.
  html fidelity writes a self-contained static .html file (inline CSS, no framework).
  wireframe fidelity writes markdown-structural blocks in a .md (headings + lists + tables).
  Each screen carries req_ids citing the REQ-IDs it realizes for traceability.
  Routes: screen | full (default: full). Fidelity is required — rejects missing/invalid.
  Trigger phrases: "create mockup", "ui mockup", "wireframe", "html mockup",
  "screen mockup", "$ba-mockup".
---
```

### openai.yaml: ba-mockup (canonical)

```yaml
interface:
  display_name: "BA Mockup"
  short_description: "Requirements → UI mockup .html or wireframe .md; req_ids traceability via trace write + index update."
  default_prompt: |
    Use the ba-mockup workflow on the given SRS slug with --fidelity html|wireframe.
    Run `ba-tools resolve-route ba-mockup` to confirm the default route = full.

    To start: open .agents/ba-daily-operators/ba-core/workflows/ba-mockup.md
    and follow the `full` route steps:
      1. Run `ba-tools resolve-route ba-mockup` → confirm route = full.
      2. Validate --fidelity (required: html or wireframe).
      3. Run `ba-tools init ba-mockup` for scaffold context.
      4. Open .agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md and follow the author role.
      5. After authoring: extract req_ids from artifact, run trace write --kind mockup, run index update.

    Provide the SRS slug and --fidelity. Example: slug = order-management, --fidelity html
policy:
  allow_implicit_invocation: false
```

### ba-mockup-author.md: Agent Role Structure

```markdown
# ba-mockup-author Agent Role

**Role:** Mockup-authoring agent. Read the SRS `requirements.json`, select the
REQ-ID subset the screen realizes, and write either a self-contained `.html` or
a wireframe `.md` artifact depending on `--fidelity`.

**Determinism boundary:** You author and judge. `ba-tools` handles all
file/hash/CLI-provable work. You NEVER call an LLM sub-service or any external
tool. You READ source files and WRITE the mockup artifact.

---

## Inputs (paths only — no raw content forwarded)

```
requirements_json: .ba-ops/srs/<slug>/requirements.json
slug:              <slug>
fidelity:          <html|wireframe>
screen_name:       <chosen by you from the UC/requirement context>
route:             <screen | full>
```

Read `requirements_json` yourself. No content is forwarded — only paths.

---

## Output: fidelity-determined artifact

### If fidelity = html

Write to `.ba-ops/mockup/<slug>/<screen-name>.html`

First line MUST be: `<!-- req_ids: [FR-001, FR-002] -->`
Then: `<!DOCTYPE html>` ... self-contained HTML with inline CSS only.
...

### If fidelity = wireframe

Write to `.ba-ops/mockup/<slug>/<screen-name>.md`

YAML frontmatter MUST include: `req_ids: [FR-001, FR-002]`
Then: headings + lists + tables describing layout regions.
...

## req_ids discipline

...same as ba-diagrammer.md: read from requirements.json, never invent, focused subset...
```

---

## Validation Architecture

> Nyquist validation is ENABLED. Three success criteria map to automated tests.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, `pyproject.toml` configured) |
| Config file | `.agents/ba-daily-operators/ba-tools/pyproject.toml` |
| Quick run command | `pytest tests/test_mockup_author.py tests/test_mockup_trace_index.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MOCK-01 | `ba-mockup` requires `--fidelity`; `html` → `.html` artifact; `wireframe` → `.md` artifact | unit (fixture + workflow inspection) | `pytest tests/test_mockup_author.py -x` | ❌ Wave 0 |
| MOCK-02 | Each screen carries `req_ids`; after `index update` appear in INDEX Mockup column | integration (subprocess) | `pytest tests/test_mockup_trace_index.py::TestReqIdsAppearInIndexMockupColumn -x` | ❌ Wave 0 |
| MOCK-03 | `html` fidelity writes `.html`; `wireframe` writes inline blocks | unit (fixture schema) | `pytest tests/test_mockup_author.py::test_html_artifact_has_req_ids_comment tests/test_mockup_author.py::test_wireframe_artifact_has_frontmatter -x` | ❌ Wave 0 |

### Criterion 1 — fidelity required, fidelity-branched artifacts (MOCK-01 + MOCK-03)

**Observable signal:** Fixture file `fixtures/mockup/authored_html.html` contains `<!-- req_ids: [..] -->` as first line + `<!DOCTYPE html>`; `fixtures/mockup/authored_wireframe.md` has YAML frontmatter with `req_ids:` + headings/lists. Workflow file `ba-mockup.md` screen route section contains no render CLI invocations.

**Test approach (mirrors `test_mermaid_author.py`):**

`test_mockup_author.py` (new file):

- `test_html_artifact_has_req_ids_comment`: fixture `authored_html.html` — first line matches `<!-- req_ids: [...] -->`, non-empty list.
- `test_html_artifact_has_doctype`: fixture contains `<!DOCTYPE html>`.
- `test_wireframe_artifact_has_frontmatter`: fixture `authored_wireframe.md` — YAML frontmatter has `req_ids: [...]` non-empty inline list.
- `test_wireframe_has_no_ascii_box_drawing`: fixture body contains no `+--` or box-drawing characters.
- `test_screen_route_invokes_no_render_cli`: slice `## Route: screen` section of `ba-mockup.md`; assert no `render`, no `mmdc`, no `mermaid-render`, no `drawio` in section body.
- `test_workflow_rejects_missing_fidelity`: `ba-mockup.md` `## Route: full` section contains a fidelity validation instruction (text assertion: "fidelity" + "html" + "wireframe" present in screen route preamble).

**Held-out check:** No property-based check needed — fidelity is a two-value enum; exhaustive testing via two fixture files covers the domain.

### Criterion 2 — req_ids → INDEX.md mockup column, no orphans (MOCK-02)

**Observable signal:** After `trace write --kind mockup` + `index update`, INDEX.md Matrix row for cited REQ-IDs shows `status=ok`; `## Orphans` section is `(none)`.

**Test approach (mirrors `test_mermaid_trace_index.py` directly):**

`test_mockup_trace_index.py` (new file):

- `test_req_ids_appear_in_index_mockup_column`: subprocess test in `tmp_path`. SRS trace → mockup trace `--kind mockup --req-ids FR-001` → index update → assert FR-001 row has `ok`; `## Orphans` does NOT contain FR-001.
- `test_no_orphans_for_real_ids`: same env; mockup trace `FR-001,FR-002` → index update → assert `## Orphans` is `(none)`.

**Fixture:** `fixtures/mockup/mockup_requirements.json` — copy of `fixtures/mermaid/index_requirements.json` (same schema, same FR-001/FR-002 IDs — reuse is correct; the test is kind-agnostic).

**Column header assertion:** `| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |` — verified present in `index_cmd.py` line 213. Reuse `_MATRIX_HEADER` constant from `test_mermaid_trace_index.py`.

### Criterion 3 — invented REQ-ID surfaces as orphan (MOCK-02 / D-06)

**Observable signal:** Mockup trace citing `FR-999` (absent from `requirements.json`) → `index update` → `## Orphans` lists `FR-999`.

**Test approach (mirrors `TestInventedIdSurfacesAsOrphan`):**

`test_mockup_trace_index.py`:

- `test_invented_id_surfaces_as_orphan`: same subprocess env. SRS trace (FR-001, FR-002 valid set) → mockup trace `FR-001,FR-999` → index update → assert `## Orphans` contains `FR-999`; assert `## Orphans` is NOT `(none)`; assert FR-001 NOT in orphans.

**Note:** This test consumes `trace write` + `index update` as-is. No mocking. The test proves D-06 contract: trace records what it receives; index detects orphan. Identical to the mermaid test — only `--kind mockup` and the artifact path change.

### Sampling Rate

- **Per task commit:** `pytest tests/test_mockup_author.py tests/test_mockup_trace_index.py -x`
- **Per wave merge:** `pytest` (full suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_mockup_author.py` — covers MOCK-01, MOCK-03 (fixture + workflow inspection tests)
- [ ] `tests/test_mockup_trace_index.py` — covers MOCK-02 + criterion 3
- [ ] `tests/fixtures/mockup/authored_html.html` — sample `.html` artifact fixture (html fidelity)
- [ ] `tests/fixtures/mockup/authored_wireframe.md` — sample `.md` artifact fixture (wireframe fidelity)
- [ ] `tests/fixtures/mockup/mockup_requirements.json` — requirements fixture (can copy mermaid's `index_requirements.json` verbatim)
- [ ] `.agents/skills/ba-mockup/SKILL.md` — CDX skill entry point
- [ ] `.agents/skills/ba-mockup/agents/openai.yaml` — CDX skill metadata
- [ ] `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` — thin orchestrator
- [ ] `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` — author role contract

*(No framework install needed — pytest already active from Phases 1-3)*

---

## Environment Availability

Step 2.6: Verified by code read. No external dependencies introduced this phase.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | ba-tools runtime | ✓ (existing) | 3.11+ per CLAUDE.md | — |
| pytest | test runner | ✓ (existing) | project dependency | — |
| ba-tools CLI | trace write, index update | ✓ (existing) | project editable install | — |
| mmdc / draw.io | render route | N/A — **no render route this phase** | — | — |

**Missing dependencies with no fallback:** None.

---

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | `--fidelity` workflow-level validation; path inputs via existing `resolve_under_root` + `is_within_root` in `trace_cmd.py` |
| V2 Authentication | no | — |
| V4 Access Control | no | — |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in `--artifact` / `--source-doc` | Tampering | `resolve_under_root` + `is_within_root` already in `trace_cmd.py` — no new code needed |
| Agent invents arbitrary REQ-IDs | Spoofing | Downstream orphan detection by `index update`; ba-mockup-author.md includes explicit "never invent IDs" instruction |
| Script injection in `.html` artifact | Tampering | D-03 constraint: no `<script>` tags; agent prompt explicitly forbids JS |
| Oversized artifact writing over PATH | Tampering | All paths resolved under `--repo-root` via existing `repo.py` guards |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `test_skill_schema.py` (existing) validates SKILL.md frontmatter for all skills in `.agents/skills/` — ba-mockup will be auto-picked up | Validation Architecture | Low risk: worst case, add an explicit test; the schema check is a structural scan |
| A2 | `test_workflow_contract.py` (existing) validates workflows — ba-mockup.md will be picked up automatically | Validation Architecture | Low risk: same as A1 |

All other claims were verified by direct code read this session.

---

## Open Questions

1. **Screen name convention for the artifact filename**
   - What we know: D-01 = one screen per invocation; the artifact lands under `.ba-ops/mockup/<slug>/`.
   - What's unclear: Does the user supply `--screen-name` or does the agent choose the filename?
   - Recommendation: Agent chooses based on the UC/requirement context (mirrors mermaid `diagram.md` convention). A default name `screen.html` / `screen.md` is safe if the user doesn't specify. The workflow should accept an optional `--screen-name` override analogously to mermaid's optional `--diagram-type` override. This is Claude's Discretion.

2. **`--force` flag for re-authoring a screen**
   - What we know: `trace write` has `--force` to overwrite existing trace records.
   - What's unclear: The workflow for `full` route — does it pass `--force` automatically on re-run?
   - Recommendation: Same as mermaid — the workflow does NOT pass `--force` by default. If a trace exists the user gets `TRACE_EXISTS` exit 2 and must re-run with `--force` explicitly. Document in workflow.

---

## Sources

### Primary (HIGH confidence — direct code read)

- `trace_cmd.py` (`.agents/ba-daily-operators/ba-tools/ba_tools/commands/trace_cmd.py`) — `--kind mockup` acceptance confirmed, `MISSING_REQ_IDS` guard confirmed, `--source-doc` = source_hash semantics confirmed
- `index_cmd.py` (`.agents/ba-daily-operators/ba-tools/ba_tools/commands/index_cmd.py`) — Matrix header with Mockup column confirmed, orphan detection confirmed
- `resolve_route.py` — `ba-mockup → full` confirmed in `DEFAULT_ROUTES`
- `init_cmd.py` — `ba-mockup: ["screen", "full"]` confirmed in `OPERATOR_ROUTES`
- `scaffold.py` — `mockup` in `_SUBDIRS` confirmed
- `ba-mermaid.md` (`.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md`) — `--source-doc` = `requirements.json` note confirmed; route structure confirmed
- `ba-diagrammer.md` — agent role contract structure confirmed; req_ids discipline section confirmed
- `ba-mermaid/SKILL.md` and `agents/openai.yaml` — CDX layout confirmed
- `DESIGN.md` §3, §4, §5, §8, §11 — non-negotiables, route table, determinism boundary, `.ba-ops/` layout confirmed
- `test_mermaid_author.py`, `test_mermaid_trace_index.py` — test pattern confirmed for direct reuse

### Secondary (HIGH confidence — project docs)

- `04-CONTEXT.md` — all locked decisions D-01 through D-06
- `REQUIREMENTS.md` — MOCK-01/02/03 text
- `CLAUDE.md` — project constraints

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — no new packages; all existing verified by code read
- Architecture: HIGH — direct reuse of ba-mermaid; ba-tools confirmations are line-level code reads
- Pitfalls: HIGH — derived from D-05a constraints + direct ba-diagrammer pattern read
- Validation architecture: HIGH — mirrors mermaid test files; line numbers confirmed

**Research date:** 2026-06-18
**Valid until:** 2026-07-18 (30 days — stable stack, no external dependencies)
