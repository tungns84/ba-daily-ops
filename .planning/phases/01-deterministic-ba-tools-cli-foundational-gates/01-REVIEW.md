---
phase: 01-deterministic-ba-tools-cli-foundational-gates
reviewed: 2026-06-17T00:00:00Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - .agents/ba-daily-operators/ba-tools/ba_tools/__main__.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/errors.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/output.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/repo.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/config.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/scaffold.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/state_store.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/lint.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/citation.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/markdown_sections.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/init_cmd.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/resolve_route.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/byte_check.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/state_cmd.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/uc_status.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/lint_reqs.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/verify_cmd.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/extract_uc.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/template_cmd.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/discovery_cmd.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/scan_cmd.py
  - .agents/ba-daily-operators/ba-tools/ba_tools/commands/confirm_cmd.py
  - .agents/ba-daily-operators/ba-tools/pyproject.toml
  - .agents/ba-daily-operators/ba-tools/tests/conftest.py
  - .agents/ba-daily-operators/ba-tools/tests/test_state.py
  - .agents/ba-daily-operators/ba-tools/tests/test_output_contract.py
  - .agents/ba-daily-operators/ba-tools/tests/test_byte_check.py
findings:
  critical: 4
  warning: 7
  info: 4
  total: 15
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-06-17
**Depth:** standard
**Files Reviewed:** 27
**Status:** issues_found

## Summary

`ba-tools` is a deterministic BA operator CLI with a strong test suite covering the
happy-path output contract, byte-check gate, path traversal, state locking, and the
lint/verify heuristics. The architecture is clean and the determinism boundary is
mostly respected (no analysis/judgement in the CLI; agents own authoring).

However, adversarial review surfaced multiple real defects, several of which break the
project's own hard contracts:

- **The CLI output/exit-code contract is violated on at least two unhappy paths** —
  a malformed `.ba-ops/config.json` and other un-wrapped `json.loads` / `read_text`
  failures escape as raw Python tracebacks with **exit code 1**, not the mandated
  JSON envelope + exit 2 (and they leak a stack trace, violating T-1-07). This was
  reproduced live.
- **The Markdown table parser misreads GFM alignment-separator rows** (`:---`,
  `:---:`), promoting the separator to the header and shifting every column key.
  This silently corrupts the lint/verify grounding, verifiability, and citation
  checks — the core traceability spine — for any table that uses alignment colons.
  Reproduced live.
- **`uc-status` parses the STATE.md body table that no command ever updates**, while
  `state advance` increments only the frontmatter `step`. The two are disconnected,
  so `next_step` is computed from the static scaffold seed forever — the spine's
  pipeline-position signal does not actually track progress.
- **Two commands (`lint-requirements`, `verify`) resolve file arguments against CWD**
  while every other path-taking command resolves against `--repo-root`. This is an
  inconsistent path contract and a latent traversal-guard weakness; the tests hide it
  by always passing absolute paths.

Note: the required-reading list references
`.agents/ba-daily-operators/ba-tools/hooks/pre-commit`, which **does not exist** on disk
(the `hooks/` directory is absent). It could not be reviewed.

## Critical Issues

### CR-01: Malformed `config.json` (and other unguarded reads) crash with a traceback and exit 1 — violates the CLI error contract and T-1-07

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/config.py:44` (called from `commands/init_cmd.py:64`)
**Issue:** `load_config` calls `json.loads(text)` with no error handling. `json.loads`
raises `json.JSONDecodeError` (a `ValueError`) — which is **not** a `BaToolsError`, so it
is not caught by the dispatcher in `__main__.py:72`. Reproduced live: with a malformed
`.ba-ops/config.json`, `ba-tools init ba-uc` prints a full Python traceback to stderr and
exits **1**. This breaks three explicit rules: (1) every error must exit 2; (2) every
error must print the `{"ok": false, "failures": [...]}` JSON envelope; (3) T-1-07 — no
stack traces in error output. The existing `test_no_stack_trace_in_error_output` only
exercises the `NO_STATE` path and misses this entirely. The same class of bug exists for
every unguarded `read_text` / `json.loads` (e.g. `init_cmd.py:70`, `uc_status.py:120`,
`extract_uc.py:80`, `citation.py:94`, `lint_reqs.py:151`/`:199`, `verify_cmd.py:95`):
a non-UTF-8 file or a path that becomes unreadable between the `exists()` check and the
read will throw an uncaught `UnicodeDecodeError`/`OSError`.

**Fix:** Wrap parse/read failures and re-raise as `BaToolsError` so the dispatcher
produces the contract envelope:
```python
# config.py
def load_config(root: Path) -> dict:
    config_path = root / ".ba-ops" / "config.json"
    if not config_path.exists():
        return {}
    try:
        text = config_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as exc:
        raise BaToolsError([{"code": "BAD_CONFIG",
                             "message": f"Could not read config.json: {exc}"}]) from exc
    if not text:
        return {}
    try:
        cfg = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise BaToolsError([{"code": "BAD_CONFIG",
                             "message": f"config.json is not valid JSON: {exc}"}]) from exc
    if not isinstance(cfg, dict):
        raise BaToolsError([{"code": "BAD_CONFIG",
                             "message": "config.json must be a JSON object"}])
    return cfg
```
Additionally, consider a top-level `except Exception` in `main()` that emits a generic
sanitized `INTERNAL_ERROR` envelope + exit 2 (without the traceback) as defense-in-depth,
so no unhandled exception can ever leak a stack trace or a non-2 exit code.

### CR-02: Markdown table parser misreads GFM alignment separators — silently corrupts lint, verify, and the traceability spine

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/lint_reqs.py:66`
(also `uc_status.py:63`, same defect)
**Issue:** The separator-row detector is `all(re.match(r'^-+$', c) for c in cells)`.
GFM alignment separators (`:---`, `---:`, `:---:`) contain colons and do **not** match
`^-+$`. Reproduced live: for a table whose separator row is `|:---|:---------:|`, the
parser treats the **separator row as the header** (`{'id': ':---', 'statement': ':---------:'}`)
and the real header row becomes the first data row. Every downstream lookup keyed on
`id`, `statement`, `status`, `source`, `span`, `section` then reads from the wrong/blank
column. Consequences: `check_grounding`, `check_verifiability`, `check_atomicity`, and
the `citation_exists` gate all silently mis-evaluate — the requirement IDs become `:---`,
real requirements are skipped (`if not req_id or not statement: continue`), and `verify`
can pass a document it should fail (false negative on a gate). `uc_status._parse_pipeline_steps`
has the analogous bug at line 63 (`^\|[-| ]+\|$` rejects `|:---|`), causing the
column-header row to be treated as a data row. This corrupts the core REQ-ID
traceability value the project is built on.
**Fix:** Accept colons and spaces in separator cells:
```python
# lint_reqs.py — replace the separator check
if all(re.match(r'^:?-+:?$', c) for c in cells):
    continue
# uc_status.py:63 — replace the separator regex
if re.match(r"^\|[\s:|-]+\|$", stripped):
```

### CR-03: `state advance` and `uc-status` operate on disconnected state — `next_step` never tracks real progress

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/uc_status.py:130-133`
(and `state_store.py:172-183`, `state_cmd.py`)
**Issue:** `uc-status` computes `next_step` by parsing the **Markdown body table**
("## Pipeline Steps") via `_parse_pipeline_steps(body)`. But no command ever writes that
body table: `merge_state` only rewrites frontmatter keys and passes `body` through
unchanged (`state_store.py:159, 188`). `state advance` increments the frontmatter `step`
integer (`state_store.py:182`) — a different field that `uc-status` never reads. The
scaffold seeds the body table with every step at `pending` (`scaffold.py:128-133`).
Net effect: after any number of `state advance`/`state update` calls, `uc-status` still
reports `next_step = "srs-analyze"` because the seeded body never changes. The pipeline
position — a determinism-critical, hash-provable signal on the spine — is effectively
frozen and misreports progress. `test_uc_status_ok_after_init` only asserts the keys
exist, never that `next_step` advances, so the suite does not catch this.
**Fix:** Make a single source of truth. Either (a) have `uc-status` derive `next_step`
from frontmatter the state commands actually write, or (b) have `state` commands update
the body Pipeline Steps table under the lock. Whichever is chosen, add a test that runs
`state` to mark a step complete and asserts `uc-status` returns the next step.

### CR-04: `state advance` silently resets the step counter to 1 when `step` is non-numeric

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/state_store.py:174-182`
**Issue:** `advance` does `int(fm.get("step", 0))` inside a `try/except (TypeError, ValueError)`
that falls back to `current = 0`. The `step` field is a free-form string in practice —
the project's own tests call `state update --data '{"step": "s1"}'` and `'{"step": "writer_p1"}'`,
and the scaffold/STATE format treats values as opaque scalars. If the current `step` is
any non-numeric string, `advance` does **not** error — it silently discards the existing
value and writes `step: 1`, losing pipeline position with no signal to the caller. For a
state machine whose entire purpose is durable, no-clobber pipeline memory, a silent reset
masquerading as an increment is a data-integrity bug.
**Fix:** Fail loudly instead of silently resetting:
```python
elif action == "advance":
    if "step" in safe_data:
        fm["step"] = safe_data.pop("step")
    else:
        try:
            current = int(fm.get("step", 0))
        except (TypeError, ValueError) as exc:
            raise BaToolsError([{
                "code": "STEP_NOT_NUMERIC",
                "message": f"Cannot advance: step is non-numeric ({fm.get('step')!r}).",
            }]) from exc
        fm["step"] = str(current + 1)
    fm.update(safe_data)
```

## Warnings

### WR-01: `lint-requirements` and `verify` resolve file args against CWD, not `--repo-root` — inconsistent path contract and traversal-guard weakness

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/lint_reqs.py:137,185`
and `.agents/ba-daily-operators/ba-tools/ba_tools/commands/verify_cmd.py:63,80`
**Issue:** These commands do `Path(args.file).resolve()` (resolved relative to the
process CWD) and then check `is_within_root(reqs_path, root)` against `--repo-root`.
Every other path-taking command (`byte_check.py:45`, `extract_uc.py:62-65`,
`scan_cmd.py:63-66`, `template_cmd.py:56-59`) resolves relative paths as
`repo_root / raw`. Reproduced live: with `--repo-root` set to a parent and the CWD in a
subdir, a relative `../reqs.md` resolves against CWD and is then rejected/accepted based
on CWD position rather than repo-root — behavior diverges from the documented
"paths resolve relative to `--repo-root`" rule (CLAUDE.md portability constraint). The
tests mask this by always passing absolute paths and setting `cwd=` explicitly. This is
both a consistency bug and a guard that depends on ambient CWD.
**Fix:** Resolve relative args under `repo_root` like the other commands:
```python
reqs_path = Path(args.file)
if not reqs_path.is_absolute():
    reqs_path = root / reqs_path
reqs_path = reqs_path.resolve()
```
Apply the same to `--baseline` (lint) and `--reqs`/`--source` (verify), and to the
per-row `source` resolution in `verify_cmd.py:143`.

### WR-02: Dead, misleading subprocess block in `resolve_repo_root`

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/repo.py:35-48`
**Issue:** The first `try` block spawns `sys.executable -c "<inline script>"`, captures
the result into `result`, and never uses it. The inline script is itself broken —
`sys.exit(...)` is called before the `print(...)`, so it could never emit the toplevel
even if the value were read. A comment then says "Simpler approach: shell out to git
directly", and the real working block follows. The dead block costs an unnecessary
subprocess spawn on every invocation that omits `--repo-root` (i.e. the common case) and
actively misleads maintainers about how root resolution works.
**Fix:** Delete lines 35-48 entirely; keep only the direct
`git rev-parse --show-toplevel` block (lines 50-61) and the `Path.cwd()` fallback.

### WR-03: `is_within_root` docstring claims `is_relative_to()` and symlink handling it does not implement

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/repo.py:66-84`
**Issue:** The docstring states it "Uses `Path.resolve().is_relative_to()`" and that
"symlinks ... are handled correctly", but the implementation uses
`candidate.resolve().relative_to(root.resolve())` in a `try/except ValueError`. The
behavior is roughly equivalent for the in/out decision, but the docstring is wrong about
the API used. More substantively, on Windows `Path.resolve()` of a path whose final
component does not exist does not always canonicalize symlinks/junctions the way the
comment implies, so the "symlinks handled correctly" claim is overstated for the
traversal-guard threat model.
**Fix:** Correct the docstring to describe `relative_to` + `ValueError`, and drop or
qualify the symlink guarantee. If symlink containment is a real requirement, add an
explicit test with a symlink/junction pointing outside the root.

### WR-04: `verify` per-row source resolution downgrades path-escape into a generic "not found"

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/verify_cmd.py:142-154`
**Issue:** When a row's `Source` column points outside the repo root, the code collapses
"outside root" and "does not exist" into a single `SOURCE_NOT_FOUND` finding
(`if is_within_root(...) and candidate.exists(): ... else: SOURCE_NOT_FOUND`). Elsewhere
the codebase distinguishes `PATH_TRAVERSAL`/`PATH_ESCAPE` from `FILE_NOT_FOUND` (e.g.
`byte_check.py`, the top-of-function checks in this same file). A row-supplied source is
attacker-influenced data (it comes from a requirements file that may be authored by an
agent or imported), so a traversal attempt should be surfaced as a distinct, auditable
code, not masked as a benign missing file.
**Fix:** Split the two conditions and emit `PATH_TRAVERSAL` when
`not is_within_root(candidate, root)`, reserving `SOURCE_NOT_FOUND` for the
within-root-but-absent case.

### WR-05: Markdown table cells split on every `|` — spans/statements containing a literal pipe are silently truncated

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/lint_reqs.py:53`
(affects `verify_cmd.py` via shared `_parse_md_table`)
**Issue:** `_parse_md_table` does `stripped.split("|")` with no handling of escaped pipes
(`\|`) or inline-code pipes. A requirement `Statement` or a citation `Span` that legitimately
contains `|` (common in CLI-tooling requirements, regexes, or table-of-options text) will be
split into extra cells, shifting all subsequent columns and corrupting the row dict. For the
`verify` citation gate this means a span with a pipe can never match (false FAIL), and for
lint it mis-assigns `source`/`status`. Determinism is preserved but the parse is incorrect.
**Fix:** At minimum document the limitation and reject/normalize escaped pipes; ideally
honor GFM `\|` escaping by splitting on unescaped pipes (e.g. `re.split(r'(?<!\\)\|', stripped)`
then unescape `\|` → `|` per cell).

### WR-06: `_parse_md_table` no-op filter is confusing dead logic

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/lint_reqs.py:55`
**Issue:** `cells = [c for c in cells if True]` is a no-op list comprehension with a
comment "keep all (head/tail may be empty)". It does nothing and obscures intent — a
reader must stop to confirm it is dead. Trivial, but in a parser that is otherwise
security-relevant, dead logic invites misreading.
**Fix:** Remove the line.

### WR-07: `check_atomicity` conjunction regex over-matches and will flag many single-clause requirements as FAIL

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/lint.py:102-105,197-213`
**Issue:** `_CONJUNCTION_PATTERN` is
`\b(shall|must|will|should)\b[^.]*?\b(and|or)\b[^.]*?\b(shall|must|will|should|[a-z]{3,})\b`.
The final alternative `[a-z]{3,}` matches *any* lowercase word ≥3 chars, so any normative
sentence containing the word "and"/"or" followed by almost any word is flagged
ATOMICITY_COMPOUND (a FAIL that gates `verify`). E.g. "The system shall log errors and
warnings." or "The system shall accept JSON or YAML input." — both single, atomic,
testable requirements — would FAIL the gate. Because atomicity is FAIL-class (D-07), this
produces false gate failures on legitimate requirements, undermining trust in the gate.
**Fix:** Tighten the pattern to require a second *normative verb* after the conjunction
(drop the `[a-z]{3,}` escape hatch), or downgrade ATOMICITY to WARN and let an agent
judge. Add tests for the "log errors and warnings" / "JSON or YAML" false-positive cases.

## Info

### IN-01: `WEASEL_WORDS` contains a duplicate entry

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/lint.py:38-39`
**Issue:** `"effectively"` appears twice consecutively in the list. Harmless (the
ambiguity check returns on first match) but indicates a copy-paste slip and inflates the
list.
**Fix:** Remove the duplicate.

### IN-02: `check_citation_present` is defined but never called

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/lint.py:243-263`
**Issue:** `check_citation_present` is exported and documented but is not invoked by
`lint_reqs.py` or `verify_cmd.py` (both call ambiguity/verifiability/atomicity/grounding
only). It is also incompatible with the actual table parser, which produces flat string
cells — `row.get("source_trace", {})` would be a string, never the `dict` the function
branches on, so even if wired up it would be a no-op. Dead/unreachable code on the
quality path.
**Fix:** Either wire it into the lint/verify loop with a parser that yields structured
`source_trace`, or remove it until that data shape exists.

### IN-03: `pyproject.toml` requires `filelock>=3.29.4` but README/CLAUDE.md spec says `filelock 3.x`

**File:** `.agents/ba-daily-operators/ba-tools/pyproject.toml:11`
**Issue:** The pin `filelock>=3.29.4` is far more specific (and newer) than the documented
`filelock 3.x` / "Python 3.8+, no sub-dependencies" guidance in CLAUDE.md. Not a bug, but
the unexplained floor version may cause needless install friction on machines with an
older-but-compatible 3.x already present. `pytest>=9.0` is also an aggressive floor.
**Fix:** Either relax to `filelock>=3,<4` or add a comment explaining why `>=3.29.4` is
required.

### IN-04: Required-reading file `hooks/pre-commit` is missing from the repo

**File:** `.agents/ba-daily-operators/ba-tools/hooks/pre-commit` (does not exist)
**Issue:** The review's required-reading list references a pre-commit hook that is not
present on disk (`hooks/` directory absent). If a pre-commit gate (e.g. running byte-check
or the test suite) is part of the phase's deliverable, it is missing; if it was descoped,
the reference should be removed from planning artifacts.
**Fix:** Confirm whether the hook is in scope. If yes, add it; if no, drop the reference.

---

_Reviewed: 2026-06-17_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
