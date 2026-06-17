---
phase: 2
reviewers: [codex, opencode]
attempted_but_failed: [gemini]   # gemini CLI present but no auth (GEMINI_API_KEY / Vertex / GCA unset)
skipped: [claude]                # self — review ran inside Claude Code, skipped for independence
reviewed_at: 2026-06-17T16:52:28Z
plans_reviewed: [02-01-PLAN.md, 02-02-PLAN.md, 02-03-PLAN.md, 02-04-PLAN.md]
---

# Cross-AI Plan Review — Phase 2

> Reviewers invoked: **Codex**, **OpenCode**. Gemini was detected but failed (no auth
> method configured — set `GEMINI_API_KEY` to include it). Claude was skipped because
> this review executed inside Claude Code (self-review excluded for independence).

## Codex Review

## Overall Summary

The wave structure is sound and mostly follows the phase's dependency graph: unblock JSON grounding, make JSON canonical, add trace/index, then wire the Codex skill. The biggest risks are not sequencing, but contract mismatches: `trace write` cannot yet express downstream partial coverage/orphans, `render` may overwrite the global registry from one SRS, and the `ba-srs-analyze` invocation/route contract is still mostly documentation rather than an executable or testable operator path.

### 02-01-PLAN.md

**Strengths**

- Good first wave: fixes the known `source_trace` dict crash before JSON verify lands.
- Adds `.ba-ops/traces/` scaffolding before trace/index commands depend on it.
- Keeps changes deterministic and dependency-free.
- Adds test scaffolds early so later waves extend existing files.

**Concerns**

- **LOW:** `test_smoke.py` asserting `_COMMAND_MODULES` length may be brittle. Presence-by-command/module is safer.
- **LOW:** `check_grounding` treats a dict as grounded when only `doc` exists. That is acceptable as a grounding precheck, but schema validation for `span`/`section` must be explicit in plan 02.
- **LOW:** Scaffold testing inside `test_lint_reqs.py` mixes domains; not wrong, but harder to navigate.

**Suggestions**

- Assert smoke by command names/help output, not module-list length.
- Add a small helper in tests for loading fixture `requirements.json` so plan 02/03 reuse the same pattern.
- Make the `check_grounding` docstring explicit: dict mode checks only "has source doc"; citation/schema checks happen elsewhere.

**Risk Assessment: LOW.** This is a small prerequisite wave with clear scope and good tests. The main risk is brittle test shape, not implementation correctness.

### 02-02-PLAN.md

**Strengths**

- Correctly moves the hard gate onto canonical `requirements.json`.
- Preserves Markdown backward compatibility via `--reqs-format`.
- F1-F4 fixtures cover the important citation cases: clean, invented, paraphrased, wrong section.
- Deterministic SRS rendering belongs in `ba-tools`; that respects the judgement boundary.

**Concerns**

- **HIGH:** `render_registry` appears to write `.ba-ops/REQUIREMENTS.md` from one slug's `requirements.json`. D-08 says the registry is the union of all `.ba-ops/srs/*/requirements.json`. A single-slug render can silently drop existing requirements.
- **HIGH:** Verify may still rely on CLI `--source` rather than each requirement's `source_trace.doc`. The schema says `{doc, span, section}` is gated; tests should prove `doc` is actually used.
- **MEDIUM:** JSON schema validation is underspecified. Malformed JSON is covered, but invalid shapes should fail cleanly too: missing `requirements`, non-list, missing `id`, missing `statement`, invalid `status`, stated requirement without `source_trace.span`.
- **MEDIUM:** `section: null -> document scope` is a locked decision, but no explicit test covers it.
- **LOW:** Adding a new `render` command is useful, but it is extra CLI surface not listed in the original active command list. That is fine if treated as required support for SRS-04.

**Suggestions**

- Change registry rendering to aggregate all `.ba-ops/srs/*/requirements.json`, or split it into `render srs` and `render registry`.
- Add tests proving `source_trace.doc` is resolved and used, including a mismatch between `--source` and `source_trace.doc`.
- Add `SCHEMA_INVALID` / `INVALID_REQUIREMENT` failures for bad JSON shapes, always via `BaToolsError` exit 2.
- Add tests for `derived` requirements with no `source_trace`, and for `status` outside `stated|derived`.

**Risk Assessment: MEDIUM.** The core direction is right, but the global registry and per-requirement source-doc semantics need tightening or the phase can pass tests while violating the traceability contract.

### 02-03-PLAN.md

**Strengths**

- Correctly centralizes trace records under `.ba-ops/traces/`.
- Uses deterministic `source_hash` and normalized `statement_hash`.
- `index update` reading only trace records is the right long-term architecture.
- F10 directly exercises the phase's key value: gap/orphan/stale.

**Concerns**

- **HIGH:** `trace write` only derives `req_ids` from the full `requirements.json`. That cannot represent downstream artifacts covering a subset of requirements, and cannot create real orphan traces. Mermaid/mockup/story artifacts need to pass their own cited `req_ids`; `requirements.json` should be used for statement-hash lookup, not as the mapping itself.
- **HIGH:** `kind` and `slug` are used to form `.ba-ops/traces/<kind>-<slug>.json`, but the plan does not require strict validation or resolving the output path under `traces/`. A malicious slug like `../../x` is a write-path risk.
- **HIGH:** `index update` must treat `source_doc` from trace JSON as untrusted. The plan should require `resolve_under_root` / `is_within_root` before hashing.
- **MEDIUM:** Missing source docs are "skipped gracefully." That can hide stale/unverifiable traces. Missing source should be a stale/unavailable finding or a structured failure.
- **MEDIUM:** Locking serializes writes but does not prevent last-writer-wins overwrite of the same `kind-slug`. If overwrite is allowed, require `--force`; otherwise fail on existing record.
- **MEDIUM:** Status precedence is unclear when a row is both stale and gap. Deterministic precedence should be specified.

**Suggestions**

- Redesign `trace write` flags to support downstream mappings, e.g. `--req-ids FR-001,FR-002` or `--req-ids-file`, plus `--requirements` for statement-hash lookup. For `kind=srs`, default to all requirements.
- Validate `kind` and `slug` with a conservative regex such as `^[a-z0-9][a-z0-9-]*$`.
- Resolve every path read from trace records under repo root before use.
- Define status precedence, likely `stale > gap > ok`; keep orphans only in the orphan section.
- Add a test that a downstream trace covers only one of two SRS requirements, producing one `ok` and one `gap`.

**Risk Assessment: HIGH.** This is the phase's core spine, and the current CLI design cannot faithfully record artifact-to-REQ-ID mappings for downstream artifacts. Fixing this before implementation will avoid reworking Phase 3/4 trace contracts.

### 02-04-PLAN.md

**Strengths**

- Correct flat skill layout and `openai.yaml` policy nesting.
- Good emphasis on paths-only payloads and keeping `analysis.md` out of critic context.
- Captures the ≤3 CoVe loop, early pass logging, and Confirm escalation.
- Establishes reusable conventions for later operators.

**Concerns**

- **HIGH:** The default prompt says `Run ba-srs-analyze --route full --source <path>`, but no executable `ba-srs-analyze` command is created. If this is a Codex skill invocation, the prompt should not look like a nonexistent shell command.
- **HIGH:** Route resolution via Phase 1 `resolve-route` is mentioned, but no plan adds a `ba-srs-analyze` route/default registration or operator config. The "default full" contract may not actually resolve.
- **MEDIUM:** The workflow says "spawn" writer/critic agents, but project context says Codex v1 lacks autonomous cross-skill spawn. The plan should phrase this as sequential workflow sections with enforced context discipline.
- **MEDIUM:** The `extract` route depends on generic Markdown section splitting, but no `ba-tools` command exposes generic extraction. Either add/extend a CLI command or make the agent-owned behavior explicit.
- **MEDIUM:** F11 mostly validates by prose/grep. It should also statically assert the workflow's critic payload excludes `analysis.md`.

**Suggestions**

- Replace the default prompt with skill-native wording: "Use the ba-srs-analyze workflow with route full…"
- Add route metadata/config so `ba-tools resolve-route ba-srs-analyze` returns `full`.
- Add static tests for the workflow route table, critic payload shape, and "trace/index only after convergence."
- Clarify Codex v1 execution as one sequential agent loop, not true subagent spawning.
- Decide whether generic `extract` is a CLI command now; if yes, add it to plan 02 or 04.

**Risk Assessment: MEDIUM-HIGH.** The skill packaging is well specified, but the actual operator invocation and route plumbing are underdefined. Without that, the phase may ship good documents but not a reliably runnable operator.

---

## OpenCode Review

### Overall Assessment
The four plans form a coherent, well-sequenced execution strategy that correctly identifies the critical path dependencies (Plan 01 → 02 → 03 → 04). The plans demonstrate strong alignment with the DESIGN.md architecture, deterministic CLI boundaries, and Codex skill contract. The TDD-first approach with explicit fixtures is excellent.

### Plan 01 (Wave 1): Prerequisites & Test Scaffolding

**Strengths**
- Correctly identifies the two blocking issues (`check_grounding` dict crash, missing `traces` subdir) that unblock all downstream plans
- TDD-first with concrete test cases for dict/string compatibility and stability drift
- Creates test infrastructure scaffolds (`test_smoke.py`, `test_skill_schema.py`) that later plans extend
- Explicitly prohibits LLM imports in modified modules (determinism boundary respected)

**Concerns**

| Issue | Severity | Details |
|-------|----------|---------|
| `detect_reqid_issues` stability test may not exist | MEDIUM | The plan assumes `lint.py:278-340` has a two-pass stability detector. If this doesn't exist or has a different API, the F9 fixture test will fail. Verify the actual function signature before implementing. |
| Scaffold test for `.ba-ops/traces/` creation | LOW | The test asserts directory creation but `scaffold.py`'s seed routine may not be invoked by `init` automatically. Verify the actual call chain. |
| Skill schema test marked `skip` | LOW | Acceptable since skill files don't exist yet, but ensure the skip condition is clean (not `@pytest.mark.xfail` which would show as failed). |

**Suggestions**
1. Add a quick verification step: `grep -n "def detect_reqid_issues" ba_tools/lint.py` to confirm the function exists and its signature before writing the test.
2. Consider adding a `test_scaffold_creates_traces_dir` that explicitly calls the scaffold function used by `init`.

**Risk: LOW** — Straightforward infrastructure with clear, testable deliverables.

### Plan 02 (Wave 2): JSON Verify + Deterministic Renderer

**Strengths**
- Clear separation: JSON input parsing (`_parse_reqs`) isolated from existing lint/citation pipeline
- Preserves all Phase 1 semantics (≥12-char verbatim, section-scoped, exit 2)
- Comprehensive fixtures (F1-F4) covering citation pass, invented span, paraphrase, section-scope vs document-scope
- Deterministic renderer as pure functions (`render_srs`, `render_registry`) — correct placement in `ba_tools/`
- Lockfile-guarded writes for SRS.md and REQUIREMENTS.md
- Auto-detect by extension + `--reqs-format` override preserves backward compatibility

**Concerns**

| Issue | Severity | Details |
|-------|----------|---------|
| `_parse_reqs` flattening logic complexity | MEDIUM | The plan flattens `source_trace.{doc,span,section}` into row keys `source`,`span`,`section` while also keeping the original dict. Ensure downstream citation logic reads the correct fields (it currently expects `row['source']`, `row['span']`, `row['section']`). |
| `citation_exists` section-scope behavior with flattened data | MEDIUM | Confirm `citation.py::citation_exists` receives `section` from the row dict correctly. The JSON branch passes `section` but the markdown path may derive it differently. |
| IEEE-830 template placeholders | LOW | The `${...}` tokens must match exactly what `string.Template.safe_substitute` expects. No validation test for template completeness is specified. |

**Suggestions**
1. Add `test_parse_reqs_preserves_source_trace_dict` asserting the original `source_trace` dict remains on the row for `check_grounding`.
2. Verify `citation_exists` signature ensures the JSON branch passes `section` correctly (may be empty string for document-scope).
3. Add `test_template_placeholders_covered` that renders a known JSON and asserts no `${...}` tokens remain.

**Risk: MEDIUM** — `_parse_reqs` normalization is the critical integration point; a subtle field-name mismatch would silently break citation gating.

### Plan 03 (Wave 3): Trace Write + Index Update

**Strengths**
- Uniform-input contract (D-04) correctly enforced — `index_cmd.py` reads ONLY `.ba-ops/traces/*.json`
- Per-artifact stale detection (D-07) is pragmatic for v1; per-REQ deferred appropriately
- Lockfile-guarded writes for both trace records and INDEX.md using existing `acquire_state_lock`
- F10 fixture exercises all three classifications (gap, orphan, stale) with concrete trace records
- `test_index_reads_traces_only` with decoy artifact is an excellent contract test

**Concerns**

| Issue | Severity | Details |
|-------|----------|---------|
| `index_cmd.py` imports `_sha256_file` from `trace_cmd.py` | MEDIUM | Creates a circular/dependency risk if both are imported in `__main__.py`. Better: extract hashing helpers to a shared `ba_tools/hashing.py` module used by both. |
| `source_doc` path resolution in index update | MEDIUM | The trace record stores `source_doc` as relative path. `index_cmd.py` must resolve it against `root` before re-hashing. Ensure `resolve_under_root` is used, not just `root / trace['source_doc']`. |
| Stale detection when source file is missing | LOW | Plan says "skip stale-marking gracefully" — define what this means (log warning? mark as `missing`?). Should be explicit in acceptance criteria. |
| Concurrent trace write test | LOW | "writing under a held lock raises LOCK_TIMEOUT OR serializes" — pick one behavior and test it. `FileLock(timeout=10)` will raise on timeout; test should assert the exception path. |

**Suggestions**
1. Create `ba_tools/hashing.py` with `_sha256_file`, `_statement_hash`, `_sha256_str` — import in both `trace_cmd.py` and `index_cmd.py`.
2. Make `index_cmd.py` re-hashing explicit: `source_path = resolve_under_root(trace['source_doc'], root)` before `hashlib.file_digest`.
3. Add acceptance criterion: missing source file → entry in `## Stale` with status `missing` rather than silent skip.

**Risk: MEDIUM** — The shared hashing dependency and source path resolution are integration points that could cause subtle bugs if not aligned.

### Plan 04 (Wave 4): Codex Skill + Workflow + Agent Prompts

**Strengths**
- Correctly implements Codex skill contract: SKILL.md frontmatter = `{name, description}` ONLY
- `openai.yaml` nesting verified: `interface.*` + `policy.allow_implicit_invocation: false`
- Thin workflow (< 38KB) with explicit route table — follows DESIGN §4
- Critic payload explicitly excludes `analysis.md` with prohibition text — enforces CoVe independence
- Escalation to Confirm gate on non-convergence (never silent auto-pass) — correct per D-10/D-11
- F11 fixture validates critic independence (planted rationale in `analysis.md`)

**Concerns**

| Issue | Severity | Details |
|-------|----------|---------|
| Workflow file format unspecified | HIGH | The plan describes a "route table mapping routes to steps" but doesn't specify the workflow file format (YAML? Markdown? custom DSL?). This is the primary integration surface between skill and CLI — needs a concrete schema. |
| `ba-critic.md` prompt detail | MEDIUM | "Generate one verification question per requirement" — specify the output format (JSON? structured text?) so the workflow can parse findings and count FAIL severity. |
| `ba-srs-writer.md` exemplars | MEDIUM | Three inline exemplars are mentioned but not specified. Critical for few-shot grounding quality. |
| Byte budget for workflow | LOW | Plan asserts `< 38,000 B` but doesn't specify how to measure. Use `ba-tools byte-check` as specified. |

**Suggestions**
1. Define the workflow file format explicitly (recommend: Markdown with YAML frontmatter + structured step list, matching AI-SPEC §3 pattern).
2. Specify critic output schema in `ba-critic.md`: JSON array of findings with `req_id`, `severity` (fail|warn), `question`, `answer`, `verdict`.
3. Add exemplars to `ba-srs-writer.md`: one stated+span, one derived, one rejected paraphrase.
4. Ensure `gates.md` documents the exact Confirm gate invocation: `ba-tools confirm --gate quality --require-human`.

**Risk: HIGH** — The workflow format and agent prompt quality directly determine whether the Quality gate works end-to-end. The most subjective/least deterministic part of Phase 2.

### Cross-Plan Integration Risks

| Risk | Plans Affected | Mitigation |
|------|----------------|------------|
| `check_grounding` fix (P01) not compatible with `_parse_reqs` row shape (P02) | 01, 02 | Integration test in P02 that runs full verify on F1 JSON |
| `trace_cmd.py` hashing helpers not shared with `index_cmd.py` | 03 | Extract to `hashing.py` before P03 Task 1 |
| Workflow (P04) calls `ba-tools verify --reqs-format json` but P02 flag is `--reqs-format` | 02, 04 | Verify flag name consistency in P04 workflow step |
| Skill `default_prompt` invokes `--route full` but P02/P03 commands must be registered | 02, 03, 04 | Smoke test in P04 should verify full command chain |
| F10 fixture trace records must match D-05 schema from P03 | 03, 04 | Build F10 *after* P03 trace_cmd is working, not before |

### Phase 2 Success Criteria Coverage

| ROADMAP SC | Covered By | Status |
|------------|------------|--------|
| SC-1: `ba-srs-analyze` produces JSON + SRS.md, `source_trace` gated by verify | P02 | ✅ |
| SC-2: Quality gate runs verify → critic CoVe ≤3, early-exit logged | P04 | ✅ (depends on workflow format) |
| SC-3: `trace write` records artifact→REQ-ID + statement hash | P03 Task 1 | ✅ |
| SC-4: `index update` rebuilds INDEX.md with gap/orphan/stale (F10) | P03 Task 2 | ✅ |
| SC-5: Skill ships flat with verified frontmatter/openai.yaml | P04 Task 1 | ✅ |

**Recommendations**
1. Before Plan 01: verify `detect_reqid_issues` exists in `lint.py` with expected signature.
2. Before Plan 02: confirm `citation_exists` signature and that row shape matches downstream lint.
3. In Plan 03: extract hashing utilities to a shared module.

---

## Consensus Summary

Both reviewers agree the **wave sequencing and dependency graph are correct** and the deterministic-CLI / judgement boundary is well respected. They also agree the **weakest, highest-risk areas are Plan 03 (trace spine) and Plan 04 (skill/workflow plumbing)** — not because of ordering, but because of under-specified contracts.

### Agreed Strengths
- Dependency ordering (P01 → P02 → P03 → P04) is sound; Wave 1 correctly unblocks the `check_grounding` dict crash + `.ba-ops/traces/` scaffold first. *(both)*
- Determinism boundary respected — renderer/hashing live in `ba-tools`, LLM imports prohibited in modified modules. *(both)*
- TDD-first with concrete fixtures (F1–F4 citation cases, F10 gap/orphan/stale, F11 critic independence) is excellent. *(both)*
- Flat Codex skill layout + verified `openai.yaml` nesting (`interface.*`, `policy.allow_implicit_invocation: false`). *(both)*
- `index update` reading **only** trace records is the right long-term architecture; decoy-artifact contract test is strong. *(both)*

### Agreed Concerns (highest priority — raised by both)
1. **Plan 03 — source-doc path resolution must treat trace `source_doc` as untrusted.** Resolve via `resolve_under_root` before hashing, never `root / trace['source_doc']`. *(codex HIGH, opencode MEDIUM)*
2. **Plan 02 — `source_trace`/`_parse_reqs` field plumbing is the silent-failure risk.** Prove `source_trace.doc` is actually used (not CLI `--source`) and that the flattened row preserves the original dict for `check_grounding`. Add a test. *(both MEDIUM)*
3. **Plan 04 — the operator is documentation, not yet runnable.** Workflow file format is unspecified and there is no executable/route registration making `--route full` resolve. Pin the workflow schema and route metadata, and specify the critic output schema. *(codex HIGH, opencode HIGH)*

### Divergent / single-reviewer concerns (worth investigating)
- **Codex only — Plan 02 `render_registry` may drop the union (D-08).** A single-slug render overwriting `.ba-ops/REQUIREMENTS.md` could silently discard requirements from other SRS slugs. Aggregate all `.ba-ops/srs/*/requirements.json`, or split `render srs` vs `render registry`. *(HIGH — not raised by opencode)*
- **Codex only — Plan 03 `trace write` cannot represent subset/orphan coverage.** Deriving `req_ids` solely from the full `requirements.json` blocks real downstream mappings (mermaid/mockup/story). Add `--req-ids` / `--req-ids-file`; use `requirements.json` only for statement-hash lookup. *(HIGH — architectural; affects Phase 3/4 contracts)*
- **Codex only — slug path-injection.** Validate `kind`/`slug` with `^[a-z0-9][a-z0-9-]*$` so a slug like `../../x` can't escape `traces/`. *(HIGH security)*
- **OpenCode only — extract shared `ba_tools/hashing.py`.** Avoid `index_cmd.py` importing `_sha256_file` from `trace_cmd.py` (circular-import risk). *(MEDIUM)*
- **Both, differing emphasis — overwrite / missing-source semantics in Plan 03.** Define `--force`-vs-fail on existing `kind-slug`, status precedence (`stale > gap > ok`), and explicit handling for missing source (mark `missing`/stale, not silent skip).

### Top 3 actions before execution
1. **Plan 03 redesign** `trace write` to accept caller-supplied `req_ids` + validate `kind`/`slug` + resolve all trace paths under root. (Highest-leverage — fixes the spine and the security issue together.)
2. **Plan 04** pin the workflow file format + route registration so the operator is runnable and testable, not just documented.
3. **Plan 02** add tests proving `source_trace.doc` resolution and registry-union behavior; tighten JSON schema-invalid failure modes (exit 2).
