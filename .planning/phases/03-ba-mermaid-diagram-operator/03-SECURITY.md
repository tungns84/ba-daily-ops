---
phase: 03-ba-mermaid-diagram-operator
audited: 2026-06-18T00:00:00Z
auditor: gsd-security-auditor
asvs_level: default
register_authored_at_plan_time: true
threats_total: 11
threats_closed: 11
threats_open: 0
status: SECURED
---

# Phase 03: Security Audit — Threat Mitigation Verification

**Phase:** 03 — ba-mermaid-diagram-operator
**Threats Closed:** 11/11 (9 mitigate, 2 accept)
**Threats Open:** 0
**ASVS Level:** default (block_on: default)

The threat register was authored at plan time across three plans (03-01/02/03).
Each declared mitigation was verified against the implemented code by locating the
actual control (not documentation/intent). Test-based mitigations were confirmed by
running the affected test modules: **13 passed, 0 failed**.

> Note on the stale SUMMARY claim: 03-01-SUMMARY.md line 94 asserted T-03-02 was
> mitigated "implicitly within root via resolve_repo_root conventions." That was
> FALSE at the time — code review CR-01 caught the real gap. The audit below
> verifies the **real** guard added in commit `a90f495`, NOT the stale SUMMARY text.

---

## Threat Verification

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-03-01 | Tampering | mitigate | CLOSED | `mermaid_render_cmd.py:236-246` — `out_dir = (root/".ba-ops"/"mermaid"/slug).resolve()` then `if not is_within_root(out_dir, root): raise PATH_TRAVERSAL`. Test `test_slug_path_traversal` (test_mermaid_render_cmd.py:149) drives `--slug ../../../../evil` → exit 2 `PATH_TRAVERSAL`. PASS. |
| T-03-02 | Tampering | mitigate | CLOSED | `mermaid_render_cmd.py:248-255` — `artifact_path = resolve_under_root(args.artifact, root)` then `if not is_within_root(artifact_path, root): raise PATH_TRAVERSAL` **before** `read_text` (line 262). The CR-01/WR-01 fix (commit `a90f495`). Regression test `test_artifact_path_traversal` (test_mermaid_render_cmd.py:185) places artifact outside root → exit 2 `PATH_TRAVERSAL`. PASS. |
| T-03-03 | Elevation of Privilege | accept | CLOSED-accepted | `--mermaid-cli` is operator-supplied argv at the same trust level as the subprocess the operator already controls. No remote/untrusted source supplies this flag. Rationale holds (single-author local CLI tool; the flag is honored verbatim at `mermaid_render_cmd.py:97-98`). Recorded below. |
| T-03-04 | Tampering | mitigate | CLOSED | `invoke_mmdc` (`mermaid_render_cmd.py:142-143`) builds list-form argv `mmdc_argv + ["-i", mmd_path, "-o", out_path]` and calls `subprocess.run(argv, capture_output=True)` — never `shell=True` (grep confirms zero `shell=True` calls; only docstring/comment mentions). The fence body is written to a `.mmd` file and reaches mmdc only as a file PATH, never as a shell string. |
| T-03-05 | Denial of Service | mitigate | CLOSED | `_guarded_write` (`mermaid_render_cmd.py:155-177`) wraps the `diagram.mmd` write in `FileLock(str(lock_path), timeout=_LOCK_TIMEOUT)` with `_LOCK_TIMEOUT = 10`; `Timeout` → `BaToolsError LOCK_TIMEOUT` (exit 2, no write performed). Invoked at `run()` line 269. |
| T-03-06 | Spoofing | mitigate | CLOSED | ba-diagrammer req_ids discipline forbids invented IDs (`ba-diagrammer.md:77-86`, "Do NOT invent REQ-IDs … surfaces as an orphan in INDEX.md (D-05)"). Downstream surfacing verified by T-03-09 test. |
| T-03-07 | Information Disclosure | mitigate | CLOSED | Author route is CLI-free: `ba-mermaid.md` `## Route: author` (lines 29-49) contains no `mermaid-render`/`mmdc` invocation. Test `test_author_route_invokes_no_render_cli` (test_mermaid_author.py:109) slices the author section and asserts both tokens absent. PASS. |
| T-03-08 | Tampering | accept | CLOSED-accepted | Malformed `req_ids` frontmatter → `--req-ids` hand-off. Single-author, no untrusted external supplier; `trace write` records the explicit list, and `index update` flags any orphan downstream (verified by T-03-09). Low-risk rationale holds. Recorded below. |
| T-03-09 | Spoofing | mitigate | CLOSED | `index_cmd.py:159-167` collects orphans (`rid not in srs_req_ids`) and renders them under `## Orphans` (lines 189-193). Test `test_invented_id_surfaces_as_orphan` (test_mermaid_trace_index.py:312) cites FR-999 → appears in `## Orphans`; FR-001 does not. PASS. |
| T-03-10 | Repudiation | mitigate | CLOSED | `trace_cmd.py:258` `source_hash = _sha256_file(source_doc)` is written into every trace record (line 265). The `full` route passes `--source-doc .ba-ops/srs/<slug>/requirements.json` (`ba-mermaid.md:73-80`), so source_hash anchors the depicted SRS state (D-06). Exercised by all three integration tests (every `_write_*_trace` call supplies `--source-doc`). PASS. |
| T-03-SC | Tampering | mitigate | CLOSED | `resolve_mmdc` (`mermaid_render_cmd.py:111-113`) invokes mmdc only via the fixed `[npx, "-p", "@mermaid-js/mermaid-cli", "mmdc"]` list-form — `npx -p` runs an already-resolvable package, not an install. No `pip install`/`npm install`/`cargo` is ever executed (the lone `npm install` string is an error-message hint at line 120, not a call). No package added this phase (`tech_stack.added: []` across all three SUMMARYs; `filelock` pre-existing). |

---

## Accepted Risks Log

### T-03-03 — `--mermaid-cli` arbitrary executable (Elevation of Privilege)
**Disposition:** accept. **Status:** CLOSED-accepted.
The `--mermaid-cli` flag points `mermaid-render` at an explicit mmdc binary and is
honored verbatim (`mermaid_render_cmd.py:97-98`). This is operator-supplied argv at
the same trust level as the subprocess argv the operator already controls in a local
CLI tool. No remote or untrusted source supplies this flag. The rationale documented
at plan time (03-01-PLAN.md threat register) holds against the implementation: there
is no network ingress path, no config-file injection path, and no agent-supplied path
reaching this flag — the workflow render route hard-codes the invocation without it
(`ba-mermaid.md:101-106`). Accepted as residual risk.

### T-03-08 — malformed `req_ids` frontmatter into `--req-ids` hand-off (Tampering)
**Disposition:** accept. **Status:** CLOSED-accepted.
The `full` route reads the `req_ids:` list the agent itself wrote into the diagram
frontmatter and forwards it as the explicit `--req-ids` flag (`ba-mermaid.md:65-75`).
This is a single-author loop with no untrusted external supplier of the frontmatter.
`trace write` validates kind/slug against `^[a-z0-9][a-z0-9-]*$` (`trace_cmd.py:38`,
119-128) and records the explicit list without ID validation (by design, D-05); any
malformed or unknown ID is surfaced — not swallowed — as an orphan by `index update`
(verified by T-03-09 test). Low-risk rationale holds. Accepted as residual risk.

---

## Threat Flags (from SUMMARYs)

| Source | Flag | Mapping | Resolution |
|--------|------|---------|------------|
| 03-01-SUMMARY `## Threat Mitigations Applied` | T-03-02 "implicitly within root" | T-03-02 (existing register ID) | **STALE / superseded.** This claim was false; CR-01 caught the real gap and `a90f495` added the real `resolve_under_root` + `is_within_root` guard. The real guard is verified CLOSED above. Informational only — not a new unregistered flag. |
| 03-02-SUMMARY `## Threat Flags` | "None." | n/a | No new attack surface declared. |
| 03-03-SUMMARY `## Threat Mitigations Verified` | T-03-09, T-03-10, T-03-SC | existing register IDs | All map to existing register threats; verified CLOSED above. |

**Unregistered flags:** none. No new attack surface (network endpoint, auth path,
new file-access pattern, or trust-boundary schema change) appeared during
implementation that lacks a mapped threat ID.

---

## Determinism-Boundary Integrity Check (DESIGN §5)

Per the audit constraint, ba-tools must do only file/command/hash-provable work — no
judgement/LLM logic in the CLI.

- `mermaid_render_cmd.py`, `trace_cmd.py`, `index_cmd.py`: grep for
  `import openai|anthropic` across `ba_tools/commands/` returns **no matches**.
- All analysis/authoring (diagram-type selection, REQ-ID subset) is agent-owned in
  `ba-diagrammer.md`; the CLI only extracts the fence, hashes, locks, and shells out.

No integrity concern found. The determinism boundary holds.

---

## Verification Evidence

- Test run: `pytest tests/test_mermaid_render_cmd.py tests/test_mermaid_author.py tests/test_mermaid_trace_index.py` → **13 passed, 0 failed** (1.95s).
- Commit `a90f495` (T-03-02 / CR-01 / WR-01 fix) present in `git log`.
- Commit `75dee00` (CR-02 patch-target + traversal regression) present in `git log`.
- No implementation files modified by this audit (read-only audit; only this SECURITY.md written).

_Audited: 2026-06-18 — gsd-security-auditor_
