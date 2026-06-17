---
phase: 01
slug: deterministic-ba-tools-cli-foundational-gates
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-17
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> **Mode:** State B (verified from PLAN/SUMMARY artifacts; register authored at plan time, treated complete).
> **Result:** SECURED — 10/10 registered threats CLOSED. Each verdict rests on concrete `file:line` evidence of the mitigating code, not documentation or intent.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| CLI arg → filesystem | User-supplied paths (`--repo-root`, `--out`, reqs/source/UC files) reach file reads/writes | Path strings (attacker-influenced); gated by `is_within_root` before any I/O |
| `--data` JSON → STATE.md | `state` command frontmatter merge | Arbitrary JSON; validated + `ALLOWED_KEYS` allowlisted |
| Operator name → route | `init` / `resolve-route` dispatch | Operator string; exact static-dict lookup only, no inference |
| Document content → scan/lint | `scan` / `lint-requirements` / `verify` read untrusted doc text | Markdown/text; advisory-only findings, linear-time regex |
| Error path → stderr | All `BaToolsError` failures | Structured `{code}` envelope; no traceback/secret leakage |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation (evidence file:line) | Status |
|-----------|----------|-----------|-------------|----------------------------------|--------|
| T-1-01 | Tampering (path traversal) | path resolution: byte_check / scaffold / extract_uc / verify | mitigate | `repo.py:96-100` `is_within_root` (resolve→relative_to in try/except); enforced before stat `commands/byte_check.py:50-57` (PATH_ESCAPE), before read `commands/extract_uc.py:63-68` & `commands/verify_cmd.py:65-70` (PATH_TRAVERSAL); scaffold writes only under `root/.ba-ops` `scaffold.py:174-189` | closed |
| T-1-02 | Tampering (prompt-injection findings) | `scan` | mitigate | `commands/scan_cmd.py:79` `severity:"warn"`, `:85` `blocked=False` always exit 0, never raises on content; findings returned as data only | closed |
| T-1-03 | Tampering (stale-lock reclaim) | `state_store.acquire_state_lock` | mitigate | `state_store.py:77-79` `os.remove` in `try/except PermissionError: pass`; `:81` `FileLock(timeout=STALE_SECONDS)` fallback; `STALE_SECONDS=10` `:27` | closed |
| T-1-04 | Spoofing/Tampering (operator inference) | `resolve_route` / `init` | mitigate | `commands/resolve_route.py:13-21` static `DEFAULT_ROUTES`; `:35-40` unknown → `UNKNOWN_OPERATOR` exit 2 (exact key lookup, zero free-text); same gate `commands/init_cmd.py:51-56` | closed |
| T-1-07 | Information Disclosure (error output) | `BaToolsError` handler | mitigate (accepted 01-02/01-07) | `errors.py:20-24` no traceback; `output.py:36-38` structured stderr+exit 2; `__main__.py:80-98` catch-all emits generic `INTERNAL_ERROR` without exception text | closed |
| T-1-08 | Tampering (arbitrary STATE.md via --data) | `merge_state` | mitigate | `commands/state_cmd.py:62-82` `json.loads`→`BAD_DATA`, non-dict rejected; `state_store.py:31-49` `ALLOWED_KEYS` frozenset, `:268` allowlist filter drops unknown keys | closed |
| T-1-09 | Tampering (--out / citation read escape) | `template_cmd` / `verify_cmd` / `citation` | mitigate | `commands/template_cmd.py:58-63` `--out`→`PATH_ESCAPE` before write; `commands/verify_cmd.py:82-87,149-157` source/row-source→`PATH_TRAVERSAL` before read; `citation.py:86-94` reads only validated path | closed |
| T-1-10 | Tampering (implicit config default persisted) | `config.flag` / `load_config` | mitigate | `config.py:90` `flag()` `cfg.get(name,True)` pure lookup; `:47-48` `load_config` returns `{}` on absence, never writes `config.json` | closed |
| T-1-11 | Denial of Service (regex on hostile input) | `lint` heuristics | mitigate | `lint.py:170` `\b`+`re.escape` literals; `:82-94` `\b`-anchored; `:109-112` `[^.]*?` sentence-bounded — no catastrophic backtracking; span match plain `in` `citation.py:98,106` | closed |
| T-1-12 | Tampering (hard-coded machine path in source) | `test_paths.py` / pre-commit hook | mitigate | `tests/test_paths.py:127-146` drive-letter scan, `:149-220` bare-python scan; hook `.agents/ba-daily-operators/hooks/pre-commit:23` uses `git rev-parse --show-toplevel`, enforces byte-check (GATE-04 layer 2) | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|

No accepted risks. All registered threats with disposition `mitigate` were verified CLOSED in code.

---

## Auditor Notes

- **Register completeness:** `register_authored_at_plan_time = TRUE`. The 10-row register was treated as the complete attack-surface inventory; no blind vulnerability scan performed.
- **All entry points checked (not single-grep):** T-1-01 verified at every path-taking entry point — byte_check, extract_uc, verify_cmd (reqs + default source + per-row source), template_cmd `--out`, scaffold.
- **Path-of-record correction:** pre-commit hook lives at `.agents/ba-daily-operators/hooks/pre-commit` (one level above `ba-tools/`). Mitigation present; cited path was off by one directory. Not a gap.
- **Symlink caveat (informational, out of ASVS-1 scope):** `repo.py:80-86` documents that on Windows, `resolve()` of a non-existent final component does not always canonicalise junctions/symlinks, so hard symlink containment is not guaranteed by `is_within_root` alone. Documented residual limitation, not a regression. Flag if symlink containment enters scope in a future phase.
- **Runtime corroboration:** UAT (01-UAT.md, status complete) exercised PATH_ESCAPE, BAD_DATA, scan-advisory, and no-traceback paths at runtime; full pytest suite 142 passed / 0 failed. Corroborates but is not the basis for the CLOSED verdicts.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-17 | 10 | 10 | 0 | gsd-security-auditor (opus) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log (none)
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-17
