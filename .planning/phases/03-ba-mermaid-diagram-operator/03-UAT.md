---
status: complete
phase: 03-ba-mermaid-diagram-operator
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md]
started: 2026-06-18T00:00:00Z
updated: 2026-06-18T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Author route is CLI-free (MMD-01)
expected: Default `author` route produces an inline ```mermaid block in a `.md` artifact; no mmdc/mermaid-render is shelled out. Diagram frontmatter carries non-empty `req_ids`.
result: pass
evidence: tests/test_mermaid_author.py — 2 passed (incl. test_author_route_invokes_no_render_cli asserting the author section is mermaid-render/mmdc-free).

### 2. REQ-ID traceability spine (MMD-02)
expected: A diagram's cited `req_ids` flow through `ba-tools trace write --kind mermaid` + `ba-tools index update` into INDEX.md's Mermaid column. Real IDs show as covered; an invented ID (e.g. FR-999) surfaces in the Orphans section — never silently dropped.
result: pass
evidence: tests/test_mermaid_trace_index.py — 6 passed (incl. test_invented_id_surfaces_as_orphan; FR-999 surfaces as orphan).

### 3. Render hard-fails, never synthesizes (MMD-03)
expected: `ba-tools mermaid-render` with no Mermaid CLI resolvable (no `--mermaid-cli`, no `$MERMAID_CLI`, none on PATH, no npx) exits 2 with code `NO_MERMAID_CLI` and writes NO image — never a synthetic Pillow/SVG/screenshot substitute.
result: pass
evidence: tests/test_mermaid_render_cmd.py::test_no_cli_hard_fail — passed (all resolution paths patched to None → BaToolsError NO_MERMAID_CLI, no image written). No PIL/SVG-converter import in module.

### 4. Path containment on --artifact (CR-01 security fix)
expected: `ba-tools mermaid-render --artifact <path outside repo root>` exits 2 with code `PATH_TRAVERSAL` and reads no file outside the root. Matches the guard every other ba-tools command applies.
result: pass
evidence: tests/test_mermaid_render_cmd.py::test_artifact_path_traversal + test_slug_path_traversal — passed. Live: `python -m ba_tools --repo-root . mermaid-render --slug demo --artifact C:/Windows/win.ini` → {"ok": false, "code": "PATH_TRAVERSAL"}, exit 2, no file read, no dir written.

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0

## Gaps

[none]
