---
status: complete
phase: 04-ba-mockup-operator
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md]
started: 2026-06-18T10:20:11Z
updated: 2026-06-18T10:20:11Z
---

## Current Test

[testing complete]

## Tests

### 1. Fidelity is required, and fidelity chooses the artifact form (MOCK-01)
expected: |
  Invoking ba-mockup without `--fidelity` (or with an invalid value) is rejected
  BEFORE any artifact is written, with the error "`--fidelity` is required and must
  be `html` or `wireframe`". `--fidelity html` yields a self-contained `.html`
  (`<!DOCTYPE html>` + inline `<style>`, no framework); `--fidelity wireframe` yields
  a `.md` with YAML frontmatter + headings/lists, no ASCII box-drawing.
result: pass
evidence: |
  pytest tests/test_mockup_author.py::test_workflow_rejects_missing_fidelity
  ::test_html_artifact_has_req_ids_comment ::test_html_artifact_has_doctype
  ::test_wireframe_artifact_has_frontmatter ::test_wireframe_has_no_ascii_box_drawing
  → 5 passed. Workflow ba-mockup.md Route:screen Step 2 hard-rejects before authoring.

### 2. Mockup REQ-IDs join the traceability matrix (MOCK-02)
expected: |
  A mockup carrying `req_ids` (FR-001, FR-002), after `ba-tools trace write --kind
  mockup` + `ba-tools index update`, shows those REQ-IDs in INDEX.md under the Mockup
  column with `## Orphans` = (none) — no new orphans introduced.
result: pass
evidence: |
  pytest TestReqIdsAppearInIndexMockupColumn + TestNoOrphansForRealIds → 2 passed
  (real ba-tools CLI invoked over subprocess against a tmp repo root).

### 3. A mockup citing a non-existent REQ-ID is surfaced as an orphan (MOCK-03 / D-06)
expected: |
  A mockup citing FR-999 (absent from requirements.json) is listed under INDEX.md
  `## Orphans` after `index update`; a real ID (FR-001) is not.
result: pass
evidence: |
  pytest TestInventedIdSurfacesAsOrphan::test_invented_id_surfaces_as_orphan → 1 passed.

### 4. ba-mockup is a discoverable Codex operator with no synthetic-render path (DESIGN §11)
expected: |
  The operator ships as a Codex skill: SKILL.md (frontmatter = name + description only),
  openai.yaml with `policy.allow_implicit_invocation: false`, a thin workflow
  (ba-mockup.md), and an author prompt (ba-mockup-author.md). Routes are only
  `screen` + `full` — no render route, and zero render-invocation tokens
  (mmdc/mermaid-render/drawio/screenshot) anywhere in the 4 operator files.
result: pass
evidence: |
  SKILL.md frontmatter = name + description only; openai.yaml:18 allow_implicit_invocation: false
  under policy:; ba-mockup.md routes = screen, full; pytest test_screen_route_invokes_no_render_cli
  → 1 passed; repo-wide grep of the 4 operator files = 0 render tokens.

### 5. An authored mockup reads as a usable screen (MOCK-03 quality — human-verify)
expected: |
  The html fixture renders a recognizable Login screen (header → form → footer) with
  no JavaScript and no broken external assets; the wireframe fixture reads as a layout
  sketch (headings/lists/tables) with no ASCII box-drawing.
result: pass
evidence: |
  authored_html.html: `<!-- req_ids: [FR-001, FR-002] -->` line 1, self-contained inline
  CSS, zero `<script>`, zero external asset refs, recognizable Login screen.
  authored_wireframe.md: frontmatter req_ids, Header/Main/Footer + Interaction Notes,
  zero box-drawing chars (U+2500–U+257F grep = 0). Plan-03 Task 2 human-verify: approved.

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Gaps

[none]
