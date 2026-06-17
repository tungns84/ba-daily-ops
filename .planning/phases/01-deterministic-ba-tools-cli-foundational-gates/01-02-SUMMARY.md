---
phase: 01-deterministic-ba-tools-cli-foundational-gates
plan: "02"
subsystem: ba-tools-cli-gates
tags: [python, cli, argparse, tdd, resolve-route, byte-check, security]
dependency_graph:
  requires:
    - ba_tools package (01-01)
    - BaToolsError / ok_json / resolve_repo_root / is_within_root (01-01)
  provides:
    - resolve-route subcommand with static DEFAULT_ROUTES (TOOL-02)
    - byte-check subcommand enforcing 32768 B Codex limit (GATE-04, CDX-04)
    - DEFAULT_ROUTES dict (7 operators: ba-uc, ba-srs-analyze, ba-mermaid, ba-mockup, ba-make-diagram, ba-uc-delivery, ba-backlog-grooming)
    - CODEX_LIMIT = 32768 constant with strict less-than semantics
  affects:
    - All Wave-1 plans that invoke ba-mermaid routing
    - All operators that use the byte-check gate for eager-loaded docs
tech_stack:
  added: []
  patterns:
    - Static dict key lookup only — no free-text inference (DESIGN §11, T-1-04)
    - Path-traversal guard via is_within_root for every byte-check path (T-1-01)
    - Strict less-than limit: size < limit (files at exactly 32768 bytes fail)
    - TDD RED/GREEN per task — test commit followed by implementation commit
key_files:
  created: []
  modified:
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/resolve_route.py
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/byte_check.py
    - .agents/ba-daily-operators/ba-tools/tests/test_resolve_route.py
    - .agents/ba-daily-operators/ba-tools/tests/test_byte_check.py
    - .agents/ba-daily-operators/ba-tools/tests/test_output_contract.py
decisions:
  - "resolve-route: static DEFAULT_ROUTES dict with exact key lookup — no normalization, fuzzy matching, or inference (DESIGN §11)"
  - "byte-check: strict less-than semantics (size < limit) — files at exactly 32768 bytes FAIL (Codex truncates at the limit)"
  - "byte-check --repo-root is the global parser argument (before subcommand), not subcommand-level"
  - "test_output_contract.py updated to use confirm stub after resolve-route was implemented"
metrics:
  duration: "5 minutes"
  completed: "2026-06-17T12:14:53Z"
  tasks_completed: 2
  files_created: 0
  files_modified: 5
---

# Phase 01 Plan 02: resolve-route and byte-check Gates Summary

**One-liner:** Static DEFAULT_ROUTES dispatch (7 operators) and 32768 B Codex-limit gate with path-traversal guard, implemented via TDD RED/GREEN cycles with 15 passing tests.

---

## What Was Built

Two foundational gates required by all subsequent Wave-1 operator plans.

### resolve-route (TOOL-02)

`ba_tools/commands/resolve_route.py` — deterministic route resolution via static dict:

```python
DEFAULT_ROUTES: dict[str, str] = {
    "ba-uc":               "deliver",
    "ba-srs-analyze":      "full",
    "ba-mermaid":          "author",
    "ba-mockup":           "full",
    "ba-make-diagram":     "diagram",
    "ba-uc-delivery":      "full",
    "ba-backlog-grooming": "full",
}
```

- Exact dict key lookup only — zero free-text inference (DESIGN §11, T-1-04)
- Unknown operator raises `BaToolsError([{"code": "UNKNOWN_OPERATOR", "operator": ...}])` -> exit 2
- Output: `{"ok": true, "failures": [], "operator": "ba-mermaid", "default_route": "author"}`

### byte-check (GATE-04, CDX-04)

`ba_tools/commands/byte_check.py` — enforces Codex 32768 B silent-truncation limit:

- `CODEX_LIMIT = 32768` — strict less-than: `size < limit` (file at exactly 32768 bytes FAILS)
- `--limit` override for workflow tier checks (CDX-04: DEFAULT < 38000 B)
- Path resolution via `resolve_repo_root(args.repo_root)` (global `--repo-root` argument)
- Every path checked via `is_within_root(resolved, repo_root)` before stat (T-1-01)
- Failure codes: `FILE_NOT_FOUND`, `PATH_ESCAPE`, `EXCEEDS_LIMIT`
- Success output: `{"ok": true, "failures": [], "checks": [{path, size_bytes, limit_bytes, passed}]}`

---

## Verification Results

| Check | Result |
|-------|--------|
| `pytest tests/test_resolve_route.py -v` — 7 passed | PASS |
| `pytest tests/test_byte_check.py -v` — 8 passed | PASS |
| `python -m ba_tools resolve-route ba-mermaid` -> `default_route:"author"`, exit 0 | PASS |
| `python -m ba_tools resolve-route nope` -> UNKNOWN_OPERATOR on stderr, exit 2 | PASS |
| 32768-byte file -> `EXCEEDS_LIMIT`, exit 2 | PASS |
| 32767-byte file -> ok:true, exit 0 | PASS |
| `../outside.md` -> `PATH_ESCAPE`, exit 2 (T-1-01) | PASS |
| `--limit 38000` on 37000-byte file -> exit 0 (CDX-04) | PASS |
| `pytest tests/ -v` — 23 passed, 0 failed, 40 xfailed | PASS |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_output_contract.py used resolve-route as stub fixture**
- **Found during:** Overall verification (all-tests run)
- **Issue:** `test_stub_command_exits_2_on_not_implemented` and `test_stub_command_stderr_is_flat_json` invoked `resolve-route ba-mermaid`, which now correctly exits 0 — causing 2 test failures
- **Fix:** Switched both tests to use `confirm` (still a Wave-1 stub with no required args)
- **Files modified:** `.agents/ba-daily-operators/ba-tools/tests/test_output_contract.py`
- **Commit:** 7666885

---

## Known Stubs

None introduced by this plan. The 10 remaining xfailed tests are from Wave-0 stubs in other command files — these are intentional Wave-1 work items, not regressions.

---

## Threat Surface Scan

No new threat surface introduced. Both gates address existing STRIDE threats:

| Threat ID | Status |
|-----------|--------|
| T-1-04 (resolve-route free-text inference) | Mitigated — static dict only, unknown operator exits 2 |
| T-1-01 (byte-check path traversal) | Mitigated — is_within_root check before every stat call |
| T-1-07 (error info disclosure) | Inherited from 01-01 handler — no stack traces surfaced |

---

## Self-Check: PASSED

Files verified:
- `ba_tools/commands/resolve_route.py` — contains `DEFAULT_ROUTES` dict
- `ba_tools/commands/byte_check.py` — contains `32768` constant
- `tests/test_resolve_route.py` — 7 test cases
- `tests/test_byte_check.py` — 8 test cases

Commits verified:
- b5bf904 (test 01-02: RED resolve-route)
- 36ef1e5 (feat 01-02: GREEN resolve-route)
- 7681447 (test 01-02: RED byte-check)
- 29a87e9 (feat 01-02: GREEN byte-check)
- 7666885 (fix 01-02: output_contract stub fixture)
- 59a0c76 (docs 01-02: metadata commit)
