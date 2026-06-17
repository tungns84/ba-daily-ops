---
phase: 02
slug: ba-srs-analyze-quality-gate-traceability-core
status: secured
threats_open: 0
asvs_level: 1
created: 2026-06-18
---

# SECURITY.md — Phase 02: ba-srs-analyze, Quality Gate, Traceability Core

**Audit type:** Retroactive threat-mitigation verification (gsd-secure-phase)
**ASVS Level:** 1
**block_on:** high
**Audited:** 2026-06-18
**Result:** SECURED — all 24 register entries resolved (21 mitigate verified present, 3 accept documented). 0 open.

The register was authored at plan time across the four `02-0{1..4}-PLAN.md`
`<threat_model>` blocks. Each `mitigate` threat was verified by locating the
declared mitigation in the implemented code (file:line) AND confirming the cited
mitigation test exists and passes. Each `accept` threat is documented below with
its rationale held against the implementation.

Implementation files were NOT modified. Only this file was written.

---

## Threat Verification — mitigate (21)

| Threat | Category | Evidence (file:line) | Test |
|--------|----------|----------------------|------|
| T-02-01 | Tampering | `lint.py:234-235` — `_st = row.get("source_trace", "")`; `isinstance(_st, dict)` branch extracts `.get("doc","")` else `.strip()` — no `AttributeError` on dict | `test_lint_reqs.py:300 test_grounding_dict_compat` |
| T-02-03 | Tampering/Info Disc | `verify_cmd.py:250-256` (`--reqs`), `:267-273` (`--source`); `render_cmd.py:135-144` (`--slug`) — `resolve_under_root` + `is_within_root` → `PATH_TRAVERSAL` | `test_render.py` PATH_TRAVERSAL slug; `test_verify.py` |
| T-02-04 | Tampering | `verify_cmd.py:183-189` `json.loads` try/except → `MALFORMED_JSON`; `:55-150 _validate_reqs_schema` → `SCHEMA_INVALID`/`INVALID_REQUIREMENT`; all via `BaToolsError` (exit 2) | `test_verify.py:511 test_malformed_json`, `:539 test_schema_invalid_shapes` |
| T-02-04b | Tampering/Info Disc | `verify_cmd.py:330-344` — per-row `source_trace.doc` resolved via `resolve_under_root` + `is_within_root` → `PATH_TRAVERSAL` before read; gate uses `row["source"]`(=doc), not CLI `--source` | `test_verify.py:483 test_source_trace_doc_mismatch` |
| T-02-05 | Tampering | grep of `ba_tools/` for `import openai\|anthropic\|model_client\|langchain\|litellm\|genai\|cohere\|mistralai\|ollama` → 0 matches; `verify_cmd.py`/`render_cmd.py`/`srs_render.py` stdlib + filelock only | determinism-boundary grep (G4) |
| T-02-06 | Tampering | `render_cmd.py:135-144` — slug-derived `slug_dir` resolved + `is_within_root` guard before any write → `PATH_TRAVERSAL` | `test_render.py` (slug `../../../../evil`) |
| T-02-07 | Tampering/Info Disc | `trace_cmd.py:133-167` — `--artifact`/`--source-doc`/`--requirements` each `resolve_under_root`+`is_within_root` → `PATH_TRAVERSAL` | `test_trace.py` path-traversal cases |
| T-02-07b | Tampering (write-path) | `trace_cmd.py:38 _SLUG_RE`; `:119-128` `re.fullmatch` on kind+slug → `INVALID_KIND_SLUG`; `:274-282` `is_within_root(out_path)` re-check | `test_trace.py:350 test_trace_slug_rejected_dotdot`, `:377` kind-slash, `:396` uppercase |
| T-02-07c | Tampering/Info Disc (read-path) | `index_cmd.py:117-126` — each record `source_doc` via `resolve_under_root`+`is_within_root`; out-of-root OR absent → `"missing"`, never `root / trace[...]` directly | `test_index.py:251 test_out_of_root_source_doc_is_missing` |
| T-02-08 | Tampering | `trace_cmd.py:170-189` and `index_cmd.py:85-91` — `json.loads` try/except → `MALFORMED_JSON` exit 2 (never 1) in both commands | covered in `test_trace.py`/`test_index.py` |
| T-02-08b | Tampering (no-clobber) | `trace_cmd.py:284-291` — `out_path.exists() and not args.force` → `TRACE_EXISTS` exit 2 | `test_trace.py:438 test_overwrite_without_force_fails`, `:451 test_overwrite_with_force_succeeds` |
| T-02-09 | Tampering (concurrency) | `trace_cmd.py:294-310` `acquire_state_lock` + `Timeout`→`LOCK_TIMEOUT`; `index_cmd.py:231-242` same on `INDEX.md.lock`; `render_cmd.py:54-76` `FileLock(timeout=10)` | `test_trace.py` lockfile; `test_index.py` lockfile |
| T-02-10 | Tampering | grep of `ba_tools/` → 0 model-client imports; `index_cmd.py:32` imports `_sha256_file` from `ba_tools.hashing` (not `trace_cmd`); no artifact-parser import | determinism-boundary grep; no-circular-import grep |
| T-02-13 | Repudiation/Info Disc | `ba-critic.md:7-12,18-29,147-153` — payload is `{source_path, requirements_json_path}` only; prompt forbids `analysis.md`/`SRS.md`. `ba-srs-analyze.md:184-191` critic payload block excludes analysis.md. F11 fixture present (`critic-independence/{requirements.json,analysis.md}` with `WRITER_RATIONALE_MARKER`) | `test_workflow_contract.py:207 test_critic_payload_excludes_analysis` |
| T-02-14 | Elevation of Privilege | `openai.yaml:16-17` — `policy.allow_implicit_invocation: false` (nested under `policy`, not top-level); default route is static `full` | `test_skill_schema.py:149 test_openai_yaml_nesting_structure` |
| T-02-15 | DoS | SKILL.md = 728 B, workflow = 10,211 B — both < 32,768 B eager limit and < 38,000 B DEFAULT tier | byte-check (acceptance); measured this audit |
| T-02-16 | Tampering | `ba-srs-analyze.md:224-233` — loop-3 non-convergence logs `"non-convergence-escalation"`, runs `ba-tools confirm`, STOPs before Step 6 (trace+index); `:227-228` never proceed with open FAILs. `gates.md:75-77,141-163` documents escalation + G2 "never converged with open FAILs" | F12 `non-convergence-escalate/` fixture present |
| T-02-17 | Tampering | `ba-srs-analyze.md:1-11` frontmatter `default_route: full` + 6 routes; matched against Phase-1 `resolve_route.DEFAULT_ROUTES`/`init_cmd.OPERATOR_ROUTES` | `test_workflow_contract.py:135 test_resolve_route_full`, `:169 test_workflow_routes_match_registration`, `:100 test_workflow_frontmatter_schema` |
| T-02-18 | Repudiation | `openai.yaml:4-12` — `default_prompt` uses skill-native wording referencing real `ba-tools resolve-route ba-srs-analyze`; no `ba-srs-analyze --route` fake-CLI literal | `test_skill_schema.py:189 test_openai_yaml_default_prompt_no_fake_cli` |
| T-02-SC | Tampering (supply chain) | `pyproject.toml:10-12` runtime deps = `filelock>=3.29.4` only (unchanged); `pytest` is test-only. Zero new runtime dependency this phase (D-18) | all four SUMMARY.md `tech_stack.added: []` |
| T-02-02 *(see accept)* | DoS | — | — |

> Note: T-02-02, T-02-11, T-02-12 are `accept` disposition — see Accepted Risks.

### Determinism-boundary primitives (shared, underpin T-02-03/04b/06/07/07c)
- `repo.py:50-69 resolve_under_root` — relative paths joined onto `root` before `resolve()`.
- `repo.py:72-100 is_within_root` — `candidate.resolve().relative_to(root.resolve())` in try/except; `..` normalised by `resolve()`.
- `hashing.py:34-47 _sha256_file` (streaming), `:50-70 _statement_hash` (strip+collapse whitespace, NO case-fold), `:73-86 _sha256_str` — shared by `trace_cmd` + `index_cmd`, no cross-command import.

**Symlink caveat (documented, not a gap at ASVS-1):** `repo.py:80-86` notes that on
Windows `resolve()` of a non-existent final component does not always canonicalise
junctions/symlinks, so hard symlink containment is not guaranteed by `is_within_root`
alone. All Phase-2 read/write paths additionally require the target to `exist()`
(verify/trace/index/render), which forces canonicalisation, so the documented gap
is not reachable on the Phase-2 entry points. Flagged for any future caller that
acts on a non-existent target via a junction.

---

## Accepted Risks (accept — 3)

| Threat | Category | Rationale (verified to hold) |
|--------|----------|------------------------------|
| T-02-02 | DoS | `scaffold.py:157 _SUBDIRS = ["srs","mermaid","mockup","backlog","plugins","traces"]` are static string literals; `scaffold.py:178-179` `(ba_ops / subdir).mkdir` joins only those literals — no user-controlled path reaches dir creation. Rationale holds. |
| T-02-11 | Spoofing | `statement_hash`/`source_hash` use stdlib `hashlib.sha256` (`hashing.py:47,70,86`). SHA-256 collision is computationally infeasible; stdlib is the correct primitive. No second-preimage exposure in the integrity model. Rationale holds. |
| T-02-12 | Tampering (prompt-injection in external source text) | Advisory in v1 (Open Decision #2). `ba-tools scan` flags but does not block; verbatim-span discipline + `ba-tools verify` gate constrain what untrusted source text can assert into a `stated` requirement. Promote to hard gate for external `stated` reqs in a later milestone. Accepted for v1. |

---

## Unregistered Flags

None. All four `02-0{1..4}-SUMMARY.md` `## Threat Flags` sections report
"None / no new trust-boundary surfaces." No new attack surface appeared during
implementation that lacks a register mapping. Cross-checked against the audited
diff: the only new entry points are `trace write`, `index update`, `render`,
JSON `verify`, and the skill/workflow — all carry register entries.

---

## Test Verification

Full `ba-tools` suite re-run during this audit: **258 passed, 0 failed**
(`python -m pytest tests/`). The security-relevant subset
(`test_trace.py`, `test_index.py`, `test_verify.py`, `test_workflow_contract.py`,
`test_skill_schema.py`) passes with zero failures. Every mitigation test cited in
the register is present and asserts the claimed behavior:

- Path traversal (write): `test_trace_slug_rejected_dotdot` + kind-slash + uppercase.
- Path traversal (read): `test_out_of_root_source_doc_is_missing`.
- No-clobber: `test_overwrite_without_force_fails` / `_with_force_succeeds`.
- Missing/stale: `test_missing_source_reported_in_stale`, `test_stale_detection`, `test_stale_beats_gap` (precedence).
- Schema/malformed: `test_malformed_json`, `test_schema_invalid_shapes`.
- Doc plumbing: `test_source_trace_doc_mismatch`, `test_section_null_document_scope`.
- Critic independence: `test_critic_payload_excludes_analysis` (F11).
- Operator runnability: `test_resolve_route_full`, `test_workflow_routes_match_registration`.
- No-fake-CLI: `test_openai_yaml_default_prompt_no_fake_cli`.
- Determinism boundary: grep over `ba_tools/` returns 0 model-client imports.
