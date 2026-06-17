---
status: complete
phase: 01-deterministic-ba-tools-cli-foundational-gates
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md, 01-05-SUMMARY.md, 01-06-SUMMARY.md, 01-07-SUMMARY.md]
started: 2026-06-17T14:27:11Z
updated: 2026-06-17T14:48:00Z
---

## Current Test

[testing complete]

## Tests

### 1. CLI Dispatch & 12 Subcommands
expected: `python -m ba_tools --help` lists all 12 subcommands (init, resolve-route, state, lint-requirements, verify, uc-status, extract-uc, template, discovery, scan, byte-check, confirm), exit 0, no traceback.
result: pass

### 2. resolve-route — Deterministic Routing
expected: `python -m ba_tools resolve-route ba-mermaid` prints JSON `{"ok":true,...,"default_route":"author"}` exit 0. `resolve-route nope` prints flat JSON `ok:false` UNKNOWN_OPERATOR on stderr, exit 2. Same input → same output every run (no fuzzy/inference).
result: pass

### 3. byte-check — 32768 B Codex Gate
expected: A 32767-byte file passes (ok:true, exit 0); a 32768-byte file fails EXCEEDS_LIMIT exit 2 (strict less-than). `--limit 38000` lets a 37000-byte file pass. A path outside repo root (`../outside.md`) is rejected with PATH_ESCAPE exit 2.
result: pass

### 4. state — Lockfile Read-Modify-Write
expected: `--repo-root <tmp> state update --data '{"step":0}'` writes `.ba-ops/STATE.md` exit 0. `patch` merges keys; `advance` increments step. Malformed `--data` → BAD_DATA exit 2. Unknown keys silently dropped (allowlist). Concurrent writers don't clobber (loser gets LOCK_TIMEOUT or both succeed cleanly).
result: pass

### 5. init — Scaffold .ba-ops/ Spine
expected: `--repo-root <tmp> init ba-uc` creates `.ba-ops/` with 5 seed files (PROJECT.md, REQUIREMENTS.md, INDEX.md, STATE.md, config.json) + 5 subdirs (srs, mermaid, mockup, backlog, plugins), returns context JSON (operator, default_route, routes, config, state). Re-running does NOT clobber hand-edited files (idempotent). Unknown operator → exit 2.
result: pass

### 6. uc-status — Static Next-Step Resolver
expected: After init, `uc-status` reads STATE.md pipeline table and returns `next_step` = first incomplete step from [srs-analyze, mermaid, mockup, index]. All steps complete → `next_step:"done"`. Missing STATE.md → NO_STATE exit 2. Pure deterministic read, no inference.
result: pass

### 7. lint-requirements — Quality Reporter
expected: `lint-requirements <reqs.md>` reports findings (ambiguity=warn for weasel words; verifiability/atomicity/grounding=fail) and ALWAYS exits 0 (reporter, not gate). REQ-ID renumber detection flags REQ_ID_RENUMBERED when a statement keeps its text under a new ID.
result: pass

### 8. verify — Citation + Traceability GATE (core value)
expected: `verify` folds lint heuristics AND checks verbatim citations per REQ row (Source/Section/Span columns). An out-of-section span → CITATION_NOT_FOUND exit 2. `--cite-scope document` flips that span to pass. WARN-only result → exit 0. Span < 12 chars rejected. This is the REQ-ID traceability spine — a broken citation must surface as a hard FAIL.
result: pass
verified_by: claude (ran A/B/C/D paths — exit0 good, exit2 out-of-section, exit0 document-scope, exit2 <12-char span)

### 9. Utility Commands — extract-uc / template / discovery / scan / confirm
expected: `extract-uc "<file>: ## UC-001. Name"` returns the UC section (includes ### subsections, stops at next ##). `template fill` substitutes ${vars}, rejects `--out ../escape.md` with PATH_ESCAPE. `discovery add --note ...` then `discovery list` round-trips JSONL entries. `scan` emits advisory WARN findings, always exit 0. `confirm` returns confirmed:true exit 0.
result: pass
verified_by: claude (extract-uc --uc, template PATH_ESCAPE, discovery round-trip, scan WARN, confirm — all ran)

### 10. Output Contract & Path Safety (cross-cutting)
expected: Every success prints flat JSON `{"ok":true,"failures":[],...}` to stdout; every error prints flat JSON `ok:false` to stderr with exit 2 — never a Python traceback. No drive-letter/hard-coded paths in source. All file paths resolve relative to `--repo-root`. Full test suite: `pytest tests/` → 128 passed.
result: pass
verified_by: claude (pytest tests/ → 142 passed, 0 failed; flat ok:false stderr+exit2 contract observed across tests 2/4/5/8)

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
