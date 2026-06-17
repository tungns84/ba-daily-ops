---
phase: 02-ba-srs-analyze-quality-gate-traceability-core
verified: 2026-06-18T09:00:00Z
status: human_needed
score: 4/5
behavior_unverified: 1
overrides_applied: 0
human_verification:
  - test: "Run ba-srs-analyze full route on a real source document end-to-end in Codex"
    expected: "Operator is Codex-discoverable; workflow routes to full; ba-srs-writer produces requirements.json; ba-tools verify exits 0; ba-critic runs independently; trace write + index update execute; final INDEX.md shows ok status for the slug. CoVe convergence vocabulary logged to STATE.md."
    why_human: "ba-critic is an agent workflow prompt (Markdown), not Python. The CoVe loop's independence contract, convergence logging, and early-exit behavior require a live Codex session to exercise. No Python unit test can verify the multi-step agent sequence."
behavior_unverified_items:
  - truth: "Quality gate runs ba-tools verify then ba-critic CoVe with <=3 revision loops; early-exit-on-convergence logged 'passed early' vs 'passed after N'"
    test: "Run ba-srs-analyze full route in Codex with a source doc that converges on loop 1, then with a source that requires a revision"
    expected: "STATE.md contains 'passed early' for loop-1 convergence; 'passed after 2' for a 2-loop convergence; ba-critic independence confirmed by absence of analysis.md in critic payload; non-convergence after 3 loops surfaces ba-tools confirm"
    why_human: "The CoVe loop is a Markdown agent workflow, not Python. Symbol presence (gates.md, ba-critic.md wording) is VERIFIED; runtime loop behavior and STATE.md logging are not exercised by unit tests."
---

# Phase 02: ba-srs-analyze Quality Gate + Traceability Core Verification Report

**Phase Goal:** Running ba-srs-analyze (routes extract/draft/lint/verify/full/iterate) on a source document produces requirements JSON with source_trace {doc, span} per stated req + SRS/BRD .md, gated by ba-tools verify; quality gate runs ba-tools verify then ba-critic CoVe (<=3 revision loops, early-exit-on-convergence); ba-tools trace write records artifact->REQ-ID mapping + statement hash; ba-tools index update rebuilds INDEX.md flagging gaps, orphans, and stale; ba-srs-analyze skill ships as flat .agents/skills/ba-srs-analyze/SKILL.md with Codex-compliant frontmatter.
**Verified:** 2026-06-18T09:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | ba-srs-analyze routes (extract/draft/lint/verify/full/iterate) registered and resolve-route returns `full` as default | VERIFIED | `python -m ba_tools resolve-route ba-srs-analyze` returns `{"ok":true,"operator":"ba-srs-analyze","default_route":"full"}`. Workflow frontmatter `routes: [extract,draft,lint,verify,full,iterate]` parsed — all 6 `## Route:` sections present. |
| 2 | ba-tools verify on requirements JSON with source_trace {doc, span} exits 0 for grounded, exits 2 for invented span | VERIFIED | F1 (clean-uc-grounded): exit 0, `{"ok":true,"checked":3}`. F2 (ungrounded-span): exit 2, CITATION_NOT_FOUND on FR-010 invented span. --reqs-format json, _validate_reqs_schema, source_trace.doc-driven citation pipeline all substantively implemented. |
| 3 | Quality gate runs ba-tools verify then ba-critic CoVe with <=3 revision loops; early-exit-on-convergence logged "passed early" vs "passed after N" | PRESENT_BEHAVIOR_UNVERIFIED | ba-critic.md, gates.md, ba-srs-analyze.md (full route Step 5) all specify the CoVe contract in full. Convergence vocabulary defined. Independence contract encoded (analysis.md explicitly excluded from critic payload in two places). No Python unit test exercises the multi-step loop; ba-critic is an agent workflow, not Python. |
| 4 | ba-tools trace write records D-05 record {kind,slug,artifact_path,source_doc,source_hash,req_ids with statement_hash}; ba-tools index update rebuilds INDEX.md with gaps, orphans, stale | VERIFIED | trace_cmd.py: full D-05 record, regex kind/slug validation, FileLock, PATH_TRAVERSAL guard. index_cmd.py: uniform-input (D-04, hyphen stem filter), srs req_id union (D-08), stale>gap>ok precedence, ## Gaps/Orphans/Stale sections. test_index.py TestGapOrphanStale: 14 tests pass (gap_detection, orphan_detection, stale_detection, sections_present). Full suite: 258 passed. |
| 5 | ba-srs-analyze skill ships as .agents/skills/ba-srs-analyze/SKILL.md with frontmatter keys {name,description} only; openai.yaml has interface.* and policy.allow_implicit_invocation: false | VERIFIED | SKILL.md frontmatter keys: ['name', 'description'] — exactly two keys, no extras. openai.yaml top-level: ['interface','policy']. interface keys: ['display_name','short_description','default_prompt']. policy.allow_implicit_invocation: False. default_prompt references `ba-tools resolve-route ba-srs-analyze` — no fake `ba-srs-analyze --route` CLI. |

**Score:** 4/5 truths verified (1 present, behavior-unverified)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ba_tools/hashing.py` | Shared SHA-256 module (_sha256_file, _statement_hash, _sha256_str) | VERIFIED | 3.0K, stdlib-only. D-12 compliant: strip+collapse whitespace, no case-fold. `hashlib.file_digest` streaming (3.11+). |
| `ba_tools/lint.py` | dict-aware check_grounding guard | VERIFIED | Line 235: `_st.get("doc","").strip() if isinstance(_st, dict) else _st.strip()` — unblocks JSON verify path. |
| `ba_tools/scaffold.py` | "traces" in _SUBDIRS | VERIFIED | Line 157: `["srs","mermaid","mockup","backlog","plugins","traces"]` — .ba-ops/traces/ created on init. |
| `ba_tools/commands/verify_cmd.py` | --reqs-format auto/md/json; _validate_reqs_schema; source_trace.doc drives citation; section:null = doc scope | VERIFIED | 14.4K. --reqs-format arg at line 37-41. _validate_reqs_schema gates stated-without-span, missing id/statement, bad status. JSON path row preserves source_trace dict for dict-aware check_grounding. section:null → None → document-scope (D-03). PATH_TRAVERSAL guard per source_trace.doc. |
| `ba_tools/srs_render.py` | Pure render_srs + render_registry; no LLM imports | VERIFIED | 8.7K. Groups FR/NFR/BR into IEEE-830 §3.1/3.2/3.3. render_registry takes all-slugs list (D-08 union). string.Template.safe_substitute. No model-client import confirmed (grep 0 matches). |
| `ba_tools/commands/render_cmd.py` | render srs + render registry; FileLock; PATH_TRAVERSAL | VERIFIED | 7.1K. Registered in __main__.py. `render {srs,registry}` dispatch confirmed via --help. |
| `ba_tools/commands/trace_cmd.py` | D-05 record write; kind/slug regex; FileLock; PATH_TRAVERSAL | VERIFIED | 11.2K. _SLUG_RE = `^[a-z0-9][a-z0-9-]*$`. Belt-and-suspenders: regex + is_within_root on composed path. FileLock(timeout=10). Imports _sha256_file/_statement_hash from ba_tools.hashing (no redefinition). |
| `ba_tools/commands/index_cmd.py` | D-04 uniform-input; D-08 registry union; gap/orphan/stale; no circular import | VERIFIED | 8.7K. Hyphen-stem filter (D-04). srs_req_ids union. stale>gap>ok precedence. Does NOT import from trace_cmd (grep 0 matches). Imports _sha256_file from ba_tools.hashing only. |
| `.agents/skills/ba-srs-analyze/SKILL.md` | Codex SKILL.md: name+description only | VERIFIED | 728B. Frontmatter keys ['name','description'] — no extra keys. YAML block scalar `>` for description. |
| `.agents/skills/ba-srs-analyze/agents/openai.yaml` | interface.* nesting; policy.allow_implicit_invocation:false | VERIFIED | Top-level ['interface','policy']. Correct nesting confirmed via yaml.safe_load. allow_implicit_invocation: False. |
| `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` | YAML frontmatter operator/default_route/routes; 6 ## Route: sections | VERIFIED | 10.2K. Frontmatter: operator=ba-srs-analyze, default_route=full, routes=[extract,draft,lint,verify,full,iterate]. All 6 route sections confirmed. |
| `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md` | FR/NFR/BR prefixes; verbatim span discipline; 3 exemplars; no LLM imports | VERIFIED | Full schema: id, statement, classification, status, source_trace.{section,doc,span}. Verbatim span rule stated twice. Exemplars 1-3 present including rejected-paraphrase exemplar 3. Markdown — no Python imports. |
| `.agents/ba-daily-operators/ba-core/agents/ba-critic.md` | Independence contract; output schema {converged,findings[]}; no analysis.md | VERIFIED | Independence contract explicitly stated twice. Output schema confirmed: `{converged:bool, findings:[{req_id,severity,question,answer,verdict}]}`. converged=true iff zero fail findings. Verdict vocabulary table present. |
| `.agents/ba-daily-operators/ba-core/references/gates.md` | Gate sequence verify->CoVe->trace; escalation protocol; WARN non-blocking | VERIFIED | Full gate sequence documented. Loop n=1..3 pseudocode. Convergence vocabulary: passed early / passed after N / non-convergence-escalation. WARN semantics: advisory, non-blocking. Escalation protocol on loop-3 non-convergence. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `trace_cmd.py` | `ba_tools/hashing.py` | `from ba_tools.hashing import _sha256_file, _statement_hash` | WIRED | Line 31 of trace_cmd.py. No redefinition — eliminates circular-import risk. |
| `index_cmd.py` | `ba_tools/hashing.py` | `from ba_tools.hashing import _sha256_file` | WIRED | Line 33 of index_cmd.py. NOT imported from trace_cmd (confirmed 0 matches). |
| `verify_cmd.py` JSON path | `ba_tools/lint.py` dict-guard | dict-aware check_grounding called on JSON rows | WIRED | JSON rows carry original source_trace dict (line 227); check_grounding uses isinstance guard (lint.py line 235). |
| `render_cmd.py` | `srs_render.py` | `render_srs` / `render_registry` called from render_cmd | WIRED | Registered in __main__.py at position 13. `render {srs,registry}` dispatch verified via --help. |
| `ba-srs-analyze.md` full route | `ba-critic.md` | Step 5: critic payload = {source_path, requirements_json_path} only | WIRED | Workflow Step 5 text: "The critic receives ONLY these two paths. Do NOT pass analysis.md" — stated in payload block AND post-step reminder. gates.md repeats prohibition. |
| `__main__.py` | `trace_cmd`, `index_cmd` | import + _COMMAND_MODULES list | WIRED | Both modules in _COMMAND_MODULES list (lines 47-50). `ba-tools trace write --help` exit 0; `ba-tools index update --help` exit 0 confirmed. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `verify_cmd.py` citation pipeline | `rows` list from `_parse_reqs` | JSON `requirements.json` via `_validate_reqs_schema` then loop | Yes — reads live file, builds real row dicts | FLOWING |
| `index_cmd.py` INDEX.md matrix | `srs_req_ids`, `req_status`, `orphan_ids` | `.ba-ops/traces/*.json` glob (D-04 filter) | Yes — reads trace records, computes live source_hash | FLOWING |
| `trace_cmd.py` D-05 record | `req_ids_records`, `source_hash` | live requirements JSON + `_sha256_file(source_doc)` | Yes — reads real files, computes real hashes | FLOWING |
| `srs_render.py` SRS.md | `groups` dict from `_group_requirements` | `requirements.json` list (not hardcoded) | Yes — pure fn receives real parsed requirements | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| resolve-route returns default_route:full | `python -m ba_tools resolve-route ba-srs-analyze` | `{"ok":true,"operator":"ba-srs-analyze","default_route":"full"}` | PASS |
| verify grounded JSON exits 0 | `ba_tools --repo-root . verify --reqs tests/fixtures/srs/clean-uc-grounded/requirements.json --reqs-format json` | `{"ok":true,"failures":[],"findings":[],"checked":3}` | PASS |
| verify invented span exits 2 CITATION_NOT_FOUND | `ba_tools --repo-root . verify --reqs tests/fixtures/srs/ungrounded-span/requirements.json --reqs-format json` | exit 2, CITATION_NOT_FOUND on FR-010 | PASS |
| trace subcommand dispatchable | `python -m ba_tools trace --help` | help text printed, exit 0 | PASS |
| index subcommand dispatchable | `python -m ba_tools index --help` | `{update}` action listed, exit 0 | PASS |
| byte-check SKILL.md and workflow within 32,768B limit | `ba_tools byte-check .agents/skills/ba-srs-analyze/SKILL.md .agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` | SKILL.md=728B, workflow=10211B, both passed | PASS |
| Full test suite | `python -m pytest tests/ -v` (from ba-tools dir) | 258 passed, 0 failed | PASS |
| CoVe loop behavior in live Codex session | N/A — ba-critic is agent workflow | Not runnable without Codex session | SKIP |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| SRS-01 | 02-02 | ba-srs-analyze turns sources into atomic, grounded, verifiable requirements (JSON) | SATISFIED | ba-srs-writer.md defines schema; ba-tools verify gates grounding; workflow full route end-to-end |
| SRS-02 | 02-04 | ba-srs-analyze emits an SRS/BRD .md | SATISFIED | srs_render.py render_srs; render_cmd `render srs` → SRS.md; render_cmd `render registry` → REQUIREMENTS.md |
| SRS-03 | 02-01 | every stated requirement carries source_trace {doc, span} | SATISFIED | verify_cmd.py _validate_reqs_schema enforces stated-without-span as exit 2; F1 fixture has doc+span; F2 exits 2 on missing span |
| SRS-04 | 02-02 | ba-srs-writer emits the quality-contract schema that ba-tools verify gates | SATISFIED | ba-srs-writer.md defines the schema; verify_cmd.py enforces it; test_verify.py 32 tests |
| SRS-05 | 02-04 | ba-critic runs fresh-context CoVe loop (<=3 revisions, early-exit on convergence, read-only) | SATISFIED (code) / UNVERIFIED (runtime) | ba-critic.md, gates.md, ba-srs-analyze.md full Step 5 fully specify contract. Runtime behavior unverified (agent workflow). |
| SRS-06 | 02-04 | ba-srs-analyze supports routes extract/draft/lint/verify/full/iterate (default full) | SATISFIED | 6 route sections in workflow; frontmatter routes array matches; resolve-route returns full |
| GATE-01 | 02-02, 02-04 | Quality gate runs ba-tools verify + ba-critic judgement | SATISFIED (CLI gate) / UNVERIFIED (runtime) | ba-tools verify hard gate fully implemented. ba-critic CoVe specified in gates.md + workflow. Runtime unverified. |
| TRACE-03 | 02-01, 02-02, 02-03 | every downstream artifact carries req_ids field | SATISFIED | D-05 record schema has req_ids[]. trace_cmd.py validates and writes them. |
| TRACE-04 | 02-03 | INDEX.md is a traceability matrix: REQ-ID -> SRS -> mermaid -> mockup -> story | SATISFIED | index_cmd.py renders Matrix table with REQ-ID/SRS/Mermaid/Mockup/Story/Status columns. |
| TRACE-05 | 02-03 | INDEX flags gaps, orphans, stale | SATISFIED | index_cmd.py ## Gaps/Orphans/Stale sections. test_index.py TestGapOrphanStale 14 tests pass. stale>gap>ok precedence implemented. |
| TOOL-07 | 02-03 | ba-tools trace write records artifact->REQ-ID mapping + statement hash | SATISFIED | trace_cmd.py full D-05 implementation. 25 tests pass. |
| TOOL-08 | 02-03 | ba-tools index update rebuilds INDEX.md with gaps, orphans, stale | SATISFIED | index_cmd.py D-04 uniform-input, D-08 registry union, stale detection. 14 tests pass. |
| CDX-01 | 02-04 | flat .agents/skills/ba-*/SKILL.md; frontmatter name+description only | SATISFIED | Keys ['name','description'] verified via yaml parse. 728B file. |
| CDX-02 | 02-04 | each operator has agents/openai.yaml with interface.* and policy.allow_implicit_invocation:false | SATISFIED | Nesting confirmed: interface.[display_name,short_description,default_prompt], policy.allow_implicit_invocation=False. |
| CDX-03 | 02-04 | thin workflows under ba-core/workflows resolve route -> workflow file -> follow it | SATISFIED | ba-srs-analyze.md in ba-core/workflows/. resolve-route returns full. Workflow has all 6 route sections with complete step sequences. |

**Coverage:** 15/15 Phase 2 requirements satisfied (SRS-05 and GATE-01 runtime behavior deferred to human verification).

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | | | | No TBD/FIXME/XXX markers in any modified file. No stub returns. No model-client imports. No circular imports. |

**Determinism boundary clean:** `grep -rn "import openai\|import anthropic"` in ba_tools/ → 0 matches. `grep -n "from .trace_cmd import"` in index_cmd.py → 0 matches.

---

### Human Verification Required

#### 1. CoVe Loop Runtime Behavior (SRS-05, GATE-01)

**Test:** Run `ba-srs-analyze` full route in a Codex session using a real source document (e.g., a meeting notes .md). First, use a source that ba-srs-writer can ground all requirements correctly in one pass. Then use a source that requires one revision loop.

**Expected:**
- First run: STATE.md records `passed early` after one critic loop with no FAIL findings.
- Second run (with deliberate grounding issue introduced): STATE.md records `passed after 2` after the writer revises and the second critic loop converges.
- ba-critic receives ONLY `{source_path, requirements_json_path}` in both cases — analysis.md is absent from critic context.
- ba-tools verify exits 0 before the CoVe loop starts.
- trace write + index update execute only after convergence.

**Why human:** ba-critic is an agent prompt workflow (Markdown), not Python. The CoVe loop is a multi-step sequential agent sequence in Codex. Unit tests confirm the workflow file's structure and that ba-tools CLI commands function correctly, but the actual agent loop execution, STATE.md convergence logging, and independence contract (no analysis.md passed to critic) must be observed in a live Codex session.

---

## Gaps Summary

No gaps. All 5 must-have truths are either VERIFIED (4) or PRESENT_BEHAVIOR_UNVERIFIED (1). The one unverified truth (CoVe loop runtime behavior) is a deliberate design constraint: ba-critic is a Markdown agent prompt, not Python code, and its runtime behavior cannot be exercised by a Python test. All Python-layer gates (ba-tools verify, trace write, index update, resolve-route, byte-check) function correctly as confirmed by 258 passing tests and 7 behavioral spot-checks.

The phase goal is substantially achieved. The remaining human verification item is the agent-workflow component of the quality gate (ba-critic CoVe), which is inherently unverifiable by static analysis or Python unit tests.

---

_Verified: 2026-06-18T09:00:00Z_
_Verifier: Claude (gsd-verifier)_
