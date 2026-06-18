# Phase 4: ba-mockup Operator - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-18
**Phase:** 4-ba-mockup Operator
**Areas discussed:** Screen → req_ids carriage, HTML fidelity output shape, Wireframe block format, Fidelity flag + routes

---

## Screen unit (Area 1)

| Option | Description | Selected |
|--------|-------------|----------|
| One screen per invocation | Mirrors mermaid: one screen = one artifact = one req_ids set; route name `screen` fits; multi-screen = multiple invocations | ✓ |
| Multiple screens per artifact | One invocation emits N screens, each with own req_ids, workflow unions for one trace write | |

**User's choice:** One screen per invocation
**Notes:** Keeps req_ids carriage simple (one artifact → one set); Phase-5 conductor loops for multi-screen UCs.

## req_ids location (Area 1)

| Option | Description | Selected |
|--------|-------------|----------|
| YAML frontmatter (mirror mermaid D-03) | Artifact carries req_ids in frontmatter; workflow reads → trace write --req-ids; no new parser | ✓ |
| You decide | Defer carriage mechanism within frontmatter→flag pattern | |

**User's choice:** YAML frontmatter (mirror mermaid D-03)
**Notes:** HTML fidelity can't hold YAML frontmatter — carrier resolved in HTML area (top HTML comment).

## HTML shape (Area 2)

| Option | Description | Selected |
|--------|-------------|----------|
| Self-contained static .html, inline CSS | Single file, CSS in `<style>`, zero external assets/JS/CDN/framework; portable, diff-able | ✓ |
| Static .html + external CSS file | screen.html + style.css; cleaner separation but two files + relative dependency | |
| You decide | Defer scaffold within "self-contained static, no framework" | |

**User's choice:** Self-contained static .html, inline CSS
**Notes:** Matches no-framework + "effectiveness over looks" + text-first constraints.

## HTML req_ids carrier (Area 2)

| Option | Description | Selected |
|--------|-------------|----------|
| HTML comment block at top | `<!-- req_ids: [...] -->` first line; human-visible, regex-extractable; no sidecar | ✓ |
| `<meta>` tag in `<head>` | Structured but less visible than a top comment | |
| Sidecar screen.md with frontmatter | .html + companion .md; uniform with wireframe but two files | |

**User's choice:** HTML comment block at top
**Notes:** Mirrors frontmatter intent in HTML's native comment syntax; single human-visible claim.

## Wireframe format (Area 3)

| Option | Description | Selected |
|--------|-------------|----------|
| ASCII box-drawing in a fenced block | +---+ boxes in ```text fence; classic low-fi, monospace | |
| Markdown-structural | Headings + lists + tables describing layout regions | ✓ |
| You decide | Defer notation within "text-first, monospace, human-readable" | |

**User's choice:** Markdown-structural
**Notes:** Headings/lists/tables describing layout regions; req_ids in .md YAML frontmatter.

## Routes (Area 3)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — mirror mermaid route semantics | `screen` = author-only (no trace); `full` (default) = author+trace+index; no render route | ✓ |
| You decide | Defer per-route step lists within Phase-1 screen/full table | |

**User's choice:** Yes — mirror mermaid route semantics
**Notes:** No render route — HTML/wireframe artifact is the deliverable; no synthetic render.

## Fidelity enforcement + ba-tools surface (Area 4)

| Option | Description | Selected |
|--------|-------------|----------|
| Workflow enforces; zero new ba-tools commands | Workflow hard-rejects missing/invalid --fidelity; reuses trace write + index update entirely | ✓ |
| Add a ba-tools mockup validation command | Deterministic CLI validates fidelity / .html extension | |
| You decide | Defer enforcement locus | |

**User's choice:** Workflow enforces; zero new ba-tools commands
**Notes:** Smallest surface — no mockup-specific CLI (contrast mermaid's mermaid-render).

## Orphan handling (Area 4)

| Option | Description | Selected |
|--------|-------------|----------|
| Carry forward — downstream index update | index update flags req_ids absent from requirements.json; no change to trace_cmd/index_cmd | ✓ |
| You decide | Defer within existing orphan contract | |

**User's choice:** Carry forward — downstream index update
**Notes:** Existing Phase-2 D-13 behavior; criterion 3 met by INDEX Orphans section.

---

## Claude's Discretion

- Mockup-author agent prompt filename + body (suggest `ba-mockup-author.md`).
- Exact `.html` scaffold + markdown-structural wireframe layout conventions.
- Regex for extracting HTML-comment / frontmatter req_ids in the workflow.
- `--source` arg shape for `trace write --kind mockup`.
- Skill/workflow file-layout reconciliation + Codex discovery.
- `openai.yaml` `interface.*` wording + SKILL.md `description`.
- Test-fixture design for the 3 success criteria.

## Deferred Ideas

- Multiple screens per invocation (out of scope v1).
- A `render` route / screenshot of the mockup (forbidden — no synthetic render).
- A ba-tools mockup validation command (chose workflow-level enforcement).
- ASCII box-drawing wireframes (chose markdown-structural).
