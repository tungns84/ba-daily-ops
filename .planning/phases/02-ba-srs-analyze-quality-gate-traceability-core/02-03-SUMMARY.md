---
phase: 02-ba-srs-analyze-quality-gate-traceability-core
plan: "03"
subsystem: ba-tools-traceability-spine
tags: [trace-write, index-update, gap-detection, orphan-detection, stale-detection, tdd, security]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [TOOL-07, TOOL-08, TRACE-04, TRACE-05]
  affects: [ba_tools/commands/trace_cmd.py, ba_tools/commands/index_cmd.py, ba_tools/__main__.py]
tech_stack:
  added: []
  patterns:
    - TDD RED/GREEN with per-task commits
    - D-05 trace record schema (kind/slug/artifact_path/source_doc/source_hash/req_ids)
    - D-04 uniform-input: index reads only trace records
    - D-08 valid-REQ-IDs: union of srs trace req_ids
    - Status precedence stale > gap > ok
    - FileLock(timeout=10) guard on trace writes and INDEX.md rewrite
    - T-02-07b slug/kind path-traversal block via regex + is_within_root
    - T-02-07c untrusted source_doc resolution via resolve_under_root + is_within_root
key_files:
  created:
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/trace_cmd.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/index_cmd.py
    - .agents/ba-daily-operators/ba-tools/tests/test_trace.py
    - .agents/ba-daily-operators/ba-tools/tests/test_index.py
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/gap-orphan-stale/source.md
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/gap-orphan-stale/requirements.json
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/gap-orphan-stale/traces/srs-demo.json
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/gap-orphan-stale/traces/mermaid-demo.json
    - .agents/ba-daily-operators/ba-tools/tests/fixtures/srs/non-convergence-escalate/requirements.json
  modified:
    - .agents/ba-daily-operators/ba-tools/ba_tools/__main__.py
    - .agents/ba-daily-operators/ba-tools/tests/test_smoke.py
decisions:
  - "D-04 uniform-input enforced: index_cmd globs only traces/*.json; skips files without hyphen in stem (e.g. requirements.json decoy)"
  - "Status precedence stale > gap > ok: a REQ-ID whose srs trace is stale is classified stale even if it would otherwise be gap"
  - "source_doc in trace records is UNTRUSTED: always resolved via resolve_under_root + is_within_root before re-hash; out-of-root or absent → missing in ## Stale"
  - "Slug path-traversal blocked by ^[a-z0-9][a-z0-9-]*$ regex + is_within_root re-confirmation on composed output path (belt-and-suspenders)"
  - "F10 fixtures use deliberately wrong source_hash (aaaaaa...0000) to force stale detection without touching live file hashes"
  - "mermaid-demo.json cites FR-001 (ok coverage) + ORPHAN-001 (undefined) and omits FR-002 (gap) — single fixture exercises all three bad states"
metrics:
  duration: "~90 minutes (across two sessions)"
  completed: "2026-06-18"
  tasks_completed: 2
  files_created: 9
  files_modified: 2
  tests_added: 54
status: complete
---

# Phase 02 Plan 03: Traceability Spine Core (trace write + index update) Summary

**One-liner:** `ba-tools trace write` records D-05 JSON per-artifact provenance and `ba-tools index update` rebuilds INDEX.md with gap/orphan/stale/missing classification using uniform-input (traces only), validated kind/slug, and untrusted source_doc resolution.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 RED | trace write failing tests | 39cb273 | tests/test_trace.py |
| 1 GREEN | trace write implementation + registration | 8b9126f | ba_tools/commands/trace_cmd.py, __main__.py, tests/test_smoke.py, F10 fixtures |
| 2 RED | index update failing tests + F10/F12 fixtures | 7f8e4f0 | tests/test_index.py, traces/mermaid-demo.json, non-convergence-escalate/requirements.json |
| 2 GREEN | index update implementation + F10 fixtures | c93b2e2 | ba_tools/commands/index_cmd.py, __main__.py, F10 fixture files |

## Verification Results

```
54 passed in 9.04s (tests/test_trace.py + tests/test_index.py + tests/test_smoke.py)
```

Security checks:
- `grep -rn "import openai|import anthropic" ba_tools/` → 0 matches (determinism boundary clean)
- `grep -n "from .trace_cmd import|from ba_tools.commands.trace_cmd import" index_cmd.py` → 0 matches (no circular import)
- `grep -n "def _sha256_file|def _statement_hash" index_cmd.py` → 0 matches (imports from ba_tools.hashing)
- `ba-tools trace write --slug ../../x` → exit 2 INVALID_KIND_SLUG (path-traversal blocked)
- `ba-tools index update --help` → exit 0

## Acceptance Criteria Status

| Criterion | Status |
|-----------|--------|
| trace write records D-05 record {kind,slug,artifact_path,source_doc,source_hash,req_ids} | PASS |
| --kind mermaid --req-ids FR-001,FR-002 records only the 2 ids (subset coverage) | PASS |
| --kind srs with no --req-ids records ALL requirements | PASS |
| _statement_hash("a  b") == _statement_hash(" a b ") and != _statement_hash("A B") | PASS |
| source_hash == sha256 of live source doc bytes | PASS |
| --slug ../../x exits 2 INVALID_KIND_SLUG | PASS |
| re-writing existing trace without --force exits 2 TRACE_EXISTS | PASS |
| --source-doc outside root exits 2 PATH_TRAVERSAL | PASS |
| trace command dispatchable (--help exits 0) | PASS |
| index update over F10 produces ## Gaps (FR-002), ## Orphans (ORPHAN-001), ## Stale | PASS |
| mermaid covering FR-001 only → FR-001=ok, FR-002=gap | PASS |
| source_doc path-traversal → reported missing (not hashed outside root) | PASS |
| absent source_doc → ## Stale with missing | PASS |
| stale+gap row classified stale (precedence) | PASS |
| decoy requirements.json next to traces → not parsed (D-04 uniform-input) | PASS |
| INDEX.md has ## Gaps, ## Orphans, ## Stale, Status column | PASS |
| INDEX.md rewrite guarded by INDEX.md.lock | PASS |
| index command dispatchable (--help exits 0) | PASS |
| No circular import (index_cmd does not import from trace_cmd) | PASS |
| No model-client imports | PASS |

## Deviations from Plan

None — plan executed exactly as written.

Both TDD RED and GREEN phases committed atomically per task. All security requirements from STRIDE threat register implemented (T-02-07b, T-02-07c, T-02-08b, T-02-09, T-02-10). F10 and F12 fixtures created as specified.

## Known Stubs

None — all classification logic wired to live F10 fixture data and verified by tests.

## Threat Flags

No new trust-boundary surfaces beyond those in the plan's threat model.

## Self-Check: PASSED

Files created:
- ba_tools/commands/trace_cmd.py — FOUND
- ba_tools/commands/index_cmd.py — FOUND
- tests/test_trace.py — FOUND
- tests/test_index.py — FOUND
- tests/fixtures/srs/gap-orphan-stale/source.md — FOUND
- tests/fixtures/srs/gap-orphan-stale/requirements.json — FOUND
- tests/fixtures/srs/gap-orphan-stale/traces/srs-demo.json — FOUND
- tests/fixtures/srs/gap-orphan-stale/traces/mermaid-demo.json — FOUND
- tests/fixtures/srs/non-convergence-escalate/requirements.json — FOUND

Commits:
- 39cb273 — test(02-03): RED trace write
- 8b9126f — feat(02-03): GREEN trace write
- 7f8e4f0 — test(02-03): RED index update
- c93b2e2 — feat(02-03): GREEN index update
