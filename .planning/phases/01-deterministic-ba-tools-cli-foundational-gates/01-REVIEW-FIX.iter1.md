---
phase: 01-deterministic-ba-tools-cli-foundational-gates
fixed_at: 2026-06-17T00:00:00Z
review_path: .planning/phases/01-deterministic-ba-tools-cli-foundational-gates/01-REVIEW.md
iteration: 1
findings_in_scope: 11
fixed: 11
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-06-17
**Source review:** .planning/phases/01-deterministic-ba-tools-cli-foundational-gates/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope (Critical + Warning): 11
- Fixed: 11
- Skipped: 0

All fixes were applied in an isolated git worktree, each as one atomic commit,
then verified against the worktree source. Because `ba-tools` is installed as an
**editable** package pointing at the main repo, the subprocess-based tests would
otherwise exercise the main-repo source; every test run used
`PYTHONPATH=<worktree>/.agents/ba-daily-operators/ba-tools` so the worktree code
was actually exercised. Final full suite: **140 passed** (128 baseline + 12 new).

Two fixes change runtime behaviour/semantics (CR-03, WR-07) and are flagged
**fixed: requires human verification** — automated syntax + unit checks pass, but
a developer should confirm the design choice is the intended one.

## Fixed Issues

### CR-01: Malformed config.json (and unguarded reads) crash with traceback + exit 1

**Files modified:** `ba_tools/config.py`, `ba_tools/__main__.py`, `tests/test_output_contract.py`
**Commit:** 20bbad3
**Applied fix:** `load_config` now wraps the `read_text` (OSError/UnicodeDecodeError)
and `json.loads` (JSONDecodeError/ValueError) and re-raises `BaToolsError` with code
`BAD_CONFIG`; it also rejects non-object JSON. Added a top-level `except Exception`
in `main()` that emits a sanitized `INTERNAL_ERROR` envelope + exit 2 with no
exception text (defense-in-depth, T-1-07). Added tests for the malformed and
non-object config paths, asserting exit 2, `BAD_CONFIG`, and no `Traceback`.

### CR-02: Markdown table parser misreads GFM alignment separators

**Files modified:** `ba_tools/commands/lint_reqs.py`, `ba_tools/commands/uc_status.py`, `tests/test_output_contract.py`
**Commit:** fb4fcfd
**Applied fix:** `lint_reqs._parse_md_table` separator-cell check changed from
`^-+$` to `^:?-+:?$` (also fixes `verify`, which reuses this parser).
`uc_status._parse_pipeline_steps` separator regex changed from `^\|[-| ]+\|$` to
`^\|[\s:|-]+\|$`. `markdown_sections.py` was inspected — it is a heading extractor
with no separator logic, so no change was needed there. Added a test asserting a
table with `:---:` separators yields correct headers and no spurious FAIL findings.

### CR-03: state advance and uc-status operate on disconnected state — fixed: requires human verification

**Files modified:** `ba_tools/state_store.py`, `ba_tools/commands/uc_status.py`, `ba_tools/commands/state_cmd.py`, `tests/test_output_contract.py`
**Commit:** cccb912
**Applied fix:** Chose review option (b) — made the body "Pipeline Steps" table the
single source of truth. Added `state_store.update_pipeline_step(body, step, status)`
(pure, deterministic row-rewrite of the Status cell; no judgement). `merge_state`
now honors reserved `--data` keys `pipeline_step` + `pipeline_status` (for any
action) to update that row under the STATE.md lock, validating the step name
(`UNKNOWN_PIPELINE_STEP`) and a non-empty status (`MISSING_PIPELINE_STATUS`); the
reserved keys are consumed and never written into frontmatter. `PIPELINE_STEPS` now
lives in `state_store` (the writer) and `uc_status` imports it (the reader). Added a
test that marks `srs-analyze` complete via `state patch` and asserts `uc-status`
advances `next_step` to `mermaid`, plus an unknown-step error test.
**Why human verification:** this introduces a new state-write contract
(`pipeline_step`/`pipeline_status` reserved keys, used with `patch`). Confirm this is
the intended single-source-of-truth design rather than review option (a) (deriving
`next_step` from frontmatter the state commands already write).

### CR-04: state advance silently resets step to 1 when non-numeric

**Files modified:** `ba_tools/state_store.py`, `tests/test_state.py`
**Commit:** d98569a
**Applied fix:** The auto-increment branch now raises `BaToolsError` with code
`STEP_NOT_NUMERIC` (exit 2) when the current `step` is non-numeric and no explicit
`step` is supplied in `--data`; an explicit `step` still overrides. Added tests for
the loud-failure path (and verifying the existing value is preserved) and for the
explicit-override path.

### WR-01: lint-requirements and verify resolve file args against CWD

**Files modified:** `ba_tools/repo.py`, `ba_tools/commands/lint_reqs.py`, `ba_tools/commands/verify_cmd.py`, `tests/test_output_contract.py`
**Commit:** ae046cf
**Applied fix:** Added `repo.resolve_under_root(raw, root)` (absolute paths honored
as-is; relative paths joined onto `root`), matching `byte_check`/`extract_uc`/`scan`/
`template`. Applied it to `lint`'s `file` and `--baseline`, and `verify`'s `--reqs`,
`--source`, and per-row `source`. Added tests that a relative `--reqs` path resolves
under `--repo-root` even when the process CWD is a subdirectory.

### WR-02: Dead, misleading subprocess block in resolve_repo_root

**Files modified:** `ba_tools/repo.py`
**Commit:** f6489a2
**Applied fix:** Deleted the dead `sys.executable -c <inline script>` block (its
result was unused and the inline script was broken). Kept the direct
`git rev-parse --show-toplevel` block and the `Path.cwd()` fallback. Removed the now
unused `import sys`.

### WR-03: is_within_root docstring overstates API and symlink handling

**Files modified:** `ba_tools/repo.py`
**Commit:** 54fa989
**Applied fix:** Docstring now describes the real `relative_to` + `try/except
ValueError` mechanism and qualifies the Windows symlink/junction caveat. No
behavioural change.

### WR-04: verify per-row source downgrades path-escape to a generic not-found

**Files modified:** `ba_tools/commands/verify_cmd.py`, `tests/test_output_contract.py`
**Commit:** 1cda031
**Applied fix:** Split the combined condition: a row `Source` resolving outside the
root now emits a distinct `PATH_TRAVERSAL` finding (with the offending path),
reserving `SOURCE_NOT_FOUND` for the within-root-but-absent case. Added a test using
a `../` escape that asserts `PATH_TRAVERSAL` is present and `SOURCE_NOT_FOUND` is not.

### WR-05: Markdown table cells split on every pipe (escaped pipes truncated)

**Files modified:** `ba_tools/commands/lint_reqs.py`, `tests/test_output_contract.py`
**Commit:** cbc4565 (combined with WR-06 — same line region)
**Applied fix:** `_parse_md_table` now splits on unescaped pipes only via
`re.split(r"(?<!\\)\|", stripped)` and unescapes `\|` → `|` per cell, honoring GFM
escaping. Added a test with an escaped pipe inside a Statement, asserting the Source
column is not shifted (no false `GROUNDING_MISSING`).

### WR-06: _parse_md_table no-op filter is confusing dead logic

**Files modified:** `ba_tools/commands/lint_reqs.py`
**Commit:** cbc4565 (combined with WR-05)
**Applied fix:** Removed the dead `cells = [c for c in cells if True]` line. It sat
in the exact line region rewritten by WR-05, so the two fixes share one atomic
commit; both finding IDs are recorded in the commit body.

### WR-07: check_atomicity conjunction regex over-matches — fixed: requires human verification

**Files modified:** `ba_tools/lint.py`, `tests/test_lint_reqs.py`
**Commit:** afde535
**Applied fix:** Chose review option (a) — dropped the `[a-z]{3,}` escape hatch so
the conjunction pattern now requires a second normative verb
(`shall|must|will|should`) after the `and`/`or`. Single-clause requirements with
noun lists ("shall log errors and warnings", "shall accept JSON or YAML input") no
longer falsely FAIL. Updated the existing `test_compound_requirement_flagged` to a
genuine two-normative-verb compound (it relied on the old over-matching behaviour),
and added `test_atomicity_noun_list_not_flagged` for the false-positive cases.
**Why human verification:** this is a heuristic semantics change. A genuine compound
phrased with a single normative verb plus a second non-normative action verb (e.g.
"the system shall validate paths and log errors") will no longer be flagged. Confirm
this trade-off (fewer false FAILs, some genuine compounds now missed) is acceptable,
or consider review option (b) (downgrade ATOMICITY to WARN).

## Notes

- IN-04 ("hooks/pre-commit missing") was confirmed a FALSE POSITIVE per the fix
  guidance — the hook exists at `.agents/ba-daily-operators/hooks/pre-commit`; the
  reviewer was given the wrong path. No action taken.
- IN-01, IN-02, IN-03 are Info-tier and out of scope for this `critical_warning`
  run; they were not fixed.

---

_Fixed: 2026-06-17_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
