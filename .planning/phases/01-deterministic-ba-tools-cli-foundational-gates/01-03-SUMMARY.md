---
phase: 01-deterministic-ba-tools-cli-foundational-gates
plan: "03"
subsystem: ba-tools-state-lockfile
tags: [python, filelock, concurrency, state-machine, lockfile, pytest]
dependency_graph:
  requires:
    - ba_tools package (01-01)
    - BaToolsError / ok_json / resolve_repo_root (01-01)
    - filelock 3.29.4 installed (01-01)
  provides:
    - state_store.acquire_state_lock() — FileLock(timeout=10) + Windows stale reclaim
    - state_store.merge_state() — update/patch/advance with ALLOWED_KEYS allowlist
    - state_store.STALE_SECONDS = 10
    - state_cmd fully implemented (update/patch/advance exits 0; BAD_DATA/LOCK_TIMEOUT exits 2)
    - 8 passing tests in test_state.py (including test_concurrent_write)
  affects:
    - All later operator state writes ride on acquire_state_lock()
    - TOOL-03 success criterion 3 (no-clobber) proven by test_concurrent_write
tech_stack:
  added:
    - filelock.FileLock / filelock.Timeout (already installed in 01-01)
    - multiprocessing.Queue + multiprocessing.Process (stdlib, for concurrent test)
  patterns:
    - acquire_state_lock(): FileLock(timeout=10) + mtime stale check + os.remove with except PermissionError (RESEARCH Pattern 2 / Pitfall 1)
    - merge_state(): YAML frontmatter parse/serialize + ALLOWED_KEYS filter (T-1-08)
    - Timeout -> BaToolsError(LOCK_TIMEOUT) — no unguarded fallback write (RESEARCH Anti-Patterns)
    - json.loads(args.data) validation before lock acquire (BAD_DATA on failure)
    - Concurrent test: multiprocessing.Process workers + subprocess.run([sys.executable, ...]) (RESEARCH Pitfall 3)
key_files:
  created:
    - .agents/ba-daily-operators/ba-tools/ba_tools/state_store.py
  modified:
    - .agents/ba-daily-operators/ba-tools/ba_tools/commands/state_cmd.py
    - .agents/ba-daily-operators/ba-tools/tests/test_state.py
decisions:
  - "STATE.md format: YAML frontmatter (--- key: val ---) + optional Markdown body — matches .planning/STATE.md convention for human readability in Codex chat"
  - "advance action: int(fm.get('step', 0)) + 1; non-numeric step silently resets to 1 (safe default for string steps like 's1')"
  - "acquire_state_lock() returns FileLock but caller must use it as context manager — this pattern keeps stale-reclaim + lock construction in one unit"
  - "ALLOWED_KEYS frozenset defined in state_store.py (single source of truth); state_cmd imports it indirectly via merge_state()"
  - "test_concurrent_write and remaining tests co-implemented with state_store.py in one atomic commit (both tasks satisfied in one commit)"
metrics:
  duration: "5 minutes"
  completed: "2026-06-17T12:23:34Z"
  tasks_completed: 2
  files_created: 1
  files_modified: 2
---

# Phase 01 Plan 03: State Lockfile Gate Summary

**One-liner:** FileLock(timeout=10)-guarded STATE.md writes with Windows-safe stale reclaim, YAML frontmatter merge (update/patch/advance), ALLOWED_KEYS security filter, and a multiprocessing concurrent-write no-clobber test.

---

## What Was Built

The TOOL-03 lockfile gate — the spine's concurrency-safety guarantee. Every `.ba-ops/STATE.md` write in all later operators rides on the lock pattern established here.

**`ba_tools/state_store.py`** (new module):
- `STALE_SECONDS = 10` — shared constant for lock timeout and stale-lock age threshold
- `ALLOWED_KEYS: frozenset` — 15 allowlisted STATE.md frontmatter keys (T-1-08 security contract); unknown keys from `--data` are silently dropped
- `acquire_state_lock(lock_path: Path) -> FileLock` — checks mtime age > STALE_SECONDS, attempts `os.remove(lock_path)` inside `try/except PermissionError: pass` (live-lock sentinel on Windows), returns `FileLock(str(lock_path), timeout=STALE_SECONDS)` (RESEARCH Pattern 2 + Pitfall 1)
- `_parse_state(text)` — parses YAML frontmatter block (`--- ... ---`) + body; returns `(dict, str)` tuple
- `_serialize_state(fm, body)` — re-serializes frontmatter dict + body back to STATE.md text
- `merge_state(existing_text, data, action)` — applies `update` (replace frontmatter), `patch` (shallow-merge), or `advance` (increment step counter) using only allowlisted keys

**`ba_tools/commands/state_cmd.py`** (fully implemented):
- `register()`: `state` subparser with `action` choices `[update, patch, advance]` and required `--data` JSON string
- `run()`: resolve repo root → ensure `.ba-ops/` → `json.loads(args.data)` (raises `BaToolsError(BAD_DATA)` on failure) → `acquire_state_lock()` → `with lock:` read-modify-write STATE.md → `except Timeout: raise BaToolsError(LOCK_TIMEOUT)` — no unguarded fallback write

**`tests/test_state.py`** (fully implemented, 8 tests):
- `test_state_update_writes_fields` — update exits 0, STATE.md contains written fields
- `test_state_patch_merges_fields` — patch adds keys without overwriting existing ones
- `test_state_advance_increments_step` — advance increments numeric step
- `test_state_bad_data_exits_2` — malformed JSON → BAD_DATA exit 2
- `test_state_unknown_keys_ignored` — T-1-08: unknown keys silently dropped
- `test_state_creates_ba_ops_dir` — creates `.ba-ops/` if absent
- `test_state_stale_lock_reclaimed` — backdated lock file (mtime −20s) is reclaimed; write succeeds
- `test_concurrent_write` — two `multiprocessing.Process` workers race; no-clobber verified; loser exits 2 LOCK_TIMEOUT or both succeed; uses `sys.executable` (not `python3`)

---

## Verification Results

| Check | Result |
|-------|--------|
| `pytest tests/test_state.py -v` (8 tests) | 8 passed |
| `pytest tests/test_state.py::test_concurrent_write -v` | PASSED |
| `python -m ba_tools --repo-root <tmp> state update --data '{"step":"s1"}'` exits 0, STATE.md exists | PASS |
| Malformed `--data` (`'{not json'`) exits 2 BAD_DATA | PASS |
| `state_store.py` contains `FileLock(` | PASS |
| `state_store.py` contains `except PermissionError` around `os.remove` | PASS |
| Timeout branch raises `BaToolsError(LOCK_TIMEOUT)`, no unguarded write | PASS |
| Full suite `pytest tests/ -v` — 31 passed, 35 xfailed, 0 failures | PASS |
| Unknown key `evil_key` dropped from STATE.md (T-1-08 allowlist) | PASS |

---

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Implementation Notes (non-deviations)

**1. Both tasks implemented in one commit**
- Task 1 (state_store.py + state_cmd.py) and Task 2 (test_concurrent_write) were co-developed and committed in a single atomic unit (70cb12a). The test file needed the implementation to exist before it could be verified, and verifying the concurrent test required the full implementation. Both tasks' acceptance criteria are satisfied by the single commit.

**2. advance action with non-numeric step**
- When `step` is a non-numeric string (e.g., `"s1"` from prior `update`), `int("s1")` raises `ValueError`, which is caught and resets the counter to `0 + 1 = 1`. This is correct "safe default" behavior — advance is designed for numeric counters.

---

## Known Stubs

None — `state_cmd.py` is fully implemented. No placeholder values in STATE.md output.

---

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| No new threat surface | — | Threats T-1-03, T-1-08, T-1-07 are all mitigated per the plan's threat model. No new network endpoints, auth paths, or schema changes beyond what the plan covers. |

**T-1-03 (stale lock reclaim):** `os.remove` with `except PermissionError: pass` — live-lock PermissionError is the sentinel, swallowed safely.
**T-1-08 (arbitrary STATE.md content via --data):** `json.loads(args.data)` validates structure (BAD_DATA on failure); `ALLOWED_KEYS` frozenset filters all writes.
**T-1-07 (timeout/merge errors):** All errors surface as `{code: LOCK_TIMEOUT|BAD_DATA}` to stderr + exit 2; no traceback (inherited from 01-01 BaToolsError handler).

---

## Self-Check: PASSED

Files verified:
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/ba_tools/state_store.py` — exists
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/ba_tools/commands/state_cmd.py` — exists, fully implemented
- `D:/projects/harness/ba-daily-ops/.agents/ba-daily-operators/ba-tools/tests/test_state.py` — exists, 8 tests

Commits verified:
- 70cb12a — feat(01-03): implement state_store.py + state_cmd update/patch/advance (TOOL-03)
