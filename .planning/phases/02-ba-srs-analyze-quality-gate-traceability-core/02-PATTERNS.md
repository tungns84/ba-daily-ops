# Phase 2: ba-srs-analyze + Quality Gate + Traceability Core - Pattern Map

**Mapped:** 2026-06-17
**Files analyzed:** 12 (new/modified)
**Analogs found:** 8 / 12 (4 are greenfield with no codebase analog)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `ba_tools/commands/trace_cmd.py` | command | file-I/O + CRUD | `ba_tools/commands/state_cmd.py` | role-match (same lockfile+write pattern) |
| `ba_tools/commands/index_cmd.py` | command | batch + file-I/O | `ba_tools/commands/state_cmd.py` + `scaffold.py` INDEX seed | partial (batch read + write markdown) |
| `ba_tools/commands/verify_cmd.py` (MODIFY) | command | request-response | self (existing file, extend JSON branch) | exact |
| `ba_tools/lint.py` (MODIFY `check_grounding`) | utility | transform | self (existing, 3-line patch at line 234) | exact |
| `ba_tools/scaffold.py` (MODIFY `_SUBDIRS`) | config | transform | self (existing, one-word patch at line 157) | exact |
| `ba_tools/__main__.py` (MODIFY imports + `_COMMAND_MODULES`) | config | request-response | self (existing, add two entries) | exact |
| `.agents/skills/ba-srs-analyze/SKILL.md` | config | — | none (no `.agents/skills/` dir exists) | greenfield |
| `.agents/skills/ba-srs-analyze/agents/openai.yaml` | config | — | none (no existing openai.yaml in repo) | greenfield |
| `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` | workflow | event-driven | none (no `ba-core/` at this level exists) | greenfield |
| `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md` | agent-prompt | — | none | greenfield |
| `.agents/ba-daily-operators/ba-core/agents/ba-critic.md` | agent-prompt | — | none | greenfield |
| `.agents/ba-daily-operators/ba-tools/ba-core/templates/srs.md` (EVOLVE) | config/template | — | self (existing minimal template at this path) | exact |

---

## Pattern Assignments

### `ba_tools/commands/trace_cmd.py` (command, file-I/O + CRUD)

**Analog:** `ba_tools/commands/state_cmd.py`

**Imports pattern** (`state_cmd.py` lines 1–17):
```python
import json
from pathlib import Path

from filelock import Timeout

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import resolve_repo_root
from ba_tools.state_store import acquire_state_lock, merge_state
```
For `trace_cmd.py` replace `merge_state` import with `hashlib`, `re`, and add `resolve_under_root`, `is_within_root`.

**register() pattern** (`state_cmd.py` lines 20–39):
```python
def register(subparsers) -> None:
    p = subparsers.add_parser(
        "state",
        help="Update .ba-ops/STATE.md (guarded by FileLock, timeout=10s)",
    )
    p.add_argument("action", choices=["update", "patch", "advance"], ...)
    p.add_argument("--data", required=True, ...)
    p.set_defaults(func=run)
```
For `trace_cmd.py`:
- Parser name = `"trace"`, add subcommand `"write"` as positional or `p.add_argument("action", choices=["write"])`
- Arguments: `--kind`, `--slug`, `--artifact`, `--source-doc`, `--requirements`
- `p.set_defaults(func=run)` — identical pattern

**Lockfile write pattern** (`state_cmd.py` lines 84–110):
```python
lock = acquire_state_lock(lock_path)
try:
    with lock:
        existing = state_path.read_text(encoding="utf-8") if state_path.exists() else ""
        new_text = merge_state(existing, data, args.action)
        state_path.write_text(new_text, encoding="utf-8")
except Timeout:
    raise BaToolsError([{
        "code": "LOCK_TIMEOUT",
        "message": "STATE.md.lock held for >10s; another writer may be active. No write was performed.",
    }])
ok_json(action=args.action)
```
For `trace_cmd.py` — replace `merge_state` call with `json.dumps(record, indent=2, ensure_ascii=False)` write; lock file is `out_path.with_suffix(".json.lock")`.

**Path resolution + traversal guard pattern** (`verify_cmd.py` lines 60–76):
```python
root = resolve_repo_root(getattr(args, "repo_root", None))
reqs_path = resolve_under_root(args.reqs, root)
if not is_within_root(reqs_path, root):
    raise BaToolsError([{
        "code": "PATH_TRAVERSAL",
        "path": str(args.reqs),
        "message": "Requirements file path resolves outside repo root.",
    }])
if not reqs_path.exists():
    raise BaToolsError([{
        "code": "FILE_NOT_FOUND",
        "path": str(args.reqs),
        "message": f"Requirements file not found: {args.reqs}",
    }])
```
Apply to every path argument in `trace_cmd.py`: `--artifact`, `--source-doc`, `--requirements`.

**D-12 statement_hash helper** (stdlib only — no analog; from locked decision):
```python
import re, hashlib

def _statement_hash(statement: str) -> str:
    """sha256 of normalized statement: strip + collapse internal whitespace, no case-fold (D-12)."""
    normalized = re.sub(r'\s+', ' ', statement.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
```

**D-06 file hash helper** (stdlib only):
```python
def _sha256_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()  # Python 3.11+ (CLAUDE.md minimum)
```

**ok_json success output** (`output.py` lines 14–25):
```python
ok_json(trace=str(out_path.relative_to(root)), kind=args.kind, slug=args.slug)
# emits: {"ok": true, "failures": [], "trace": "...", "kind": "srs", "slug": "..."}
```

---

### `ba_tools/commands/index_cmd.py` (command, batch + file-I/O)

**Analog:** `ba_tools/commands/state_cmd.py` (lockfile+write) + `scaffold.py` INDEX seed (markdown structure)

**register() pattern** — identical shape to `state_cmd.py` lines 20–39:
```python
def register(subparsers) -> None:
    p = subparsers.add_parser(
        "index",
        help="Rebuild .ba-ops/INDEX.md matrix with gap/orphan/stale detection (TOOL-08)",
    )
    p.add_argument("action", choices=["update"], ...)
    p.set_defaults(func=run)
```

**Batch read pattern** (no direct codebase analog — from D-04/D-08 locked decisions):
```python
traces_dir = root / ".ba-ops" / "traces"
all_traces = [
    json.loads(p.read_text("utf-8"))
    for p in sorted(traces_dir.glob("*.json"))
]
```

**INDEX.md scaffold shape to preserve** (`scaffold.py` lines 78–100 — the seed written by `ba-tools init`):
```
## Matrix
| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |
|--------|-------|---------|--------|-------|--------|

## Gaps
(none)

## Orphans
(none)
```
Phase 2 `index update` MUST add `## Stale` section (D-13 / RESEARCH open question 3) and populate `Status` column with `gap | orphan | stale | ok`.

**Lockfile write pattern** — identical to `state_cmd.py` lines 84–110 (shown above). Lock file: `(root / ".ba-ops" / "INDEX.md.lock")`.

**Error envelope** — `BaToolsError` + `ok_json` identical to all other commands.

---

### `ba_tools/commands/verify_cmd.py` (MODIFY — add JSON branch)

**Analog:** self (extend existing file)

**Current input parsing call** (line 97 — the line to branch on):
```python
reqs_text = reqs_path.read_text(encoding="utf-8")
rows = _parse_md_table(reqs_text)
```

**New `_parse_reqs()` dispatcher to insert** (replaces direct `_parse_md_table` call):
```python
def _parse_reqs(reqs_text: str, reqs_path: Path, reqs_format: str) -> list[dict]:
    fmt = reqs_format
    if fmt == "auto":
        fmt = "json" if reqs_path.suffix.lower() == ".json" else "md"
    if fmt == "json":
        import json as _json
        data = _json.loads(reqs_text)
        reqs = data if isinstance(data, list) else data.get("requirements", [])
        rows = []
        for req in reqs:
            st = req.get("source_trace") or {}
            rows.append({
                "id":           req.get("id", ""),
                "statement":    req.get("statement", ""),
                "status":       req.get("status", "stated"),
                "source_trace": st,
                "span":         st.get("span", "")    if isinstance(st, dict) else "",
                "section":      st.get("section", "") if isinstance(st, dict) else "",
                "source":       st.get("doc", "")     if isinstance(st, dict) else "",
            })
        return rows
    else:
        return _parse_md_table(reqs_text)
```

**New `--reqs-format` argument** to add in `register()` (after existing `--reqs` at line 33):
```python
p.add_argument(
    "--reqs-format",
    choices=["auto", "md", "json"],
    default="auto",
    help="Requirements file format (default: auto-detect by extension).",
)
```

**run() call site change** (line 97, replace the existing `rows = _parse_md_table(reqs_text)` call):
```python
reqs_format = getattr(args, "reqs_format", "auto")
rows = _parse_reqs(reqs_text, reqs_path, reqs_format)
```

All downstream logic (lines 99–205) is unchanged — the row dict shape is preserved by the normalizer.

---

### `ba_tools/lint.py` (MODIFY `check_grounding` — 3-line patch)

**Analog:** self (existing file)

**Current buggy lines** (lines 234–235 — the dict incompatibility, RESEARCH Pitfall 1):
```python
source_trace = row.get("source_trace", "").strip()   # BUG: fails when source_trace is dict
source = row.get("source", "").strip()
```

**Patched replacement** (3 lines replace 1):
```python
_st = row.get("source_trace", "")
source_trace = _st.get("doc", "").strip() if isinstance(_st, dict) else _st.strip()
source = row.get("source", "").strip()
```

**Note:** `check_citation_present` at lines 250–268 is already dict-aware and can be used as a reference for the dict-path approach. The patch above mirrors its `isinstance(source_trace, dict)` guard.

---

### `ba_tools/scaffold.py` (MODIFY `_SUBDIRS` — one-word patch)

**Analog:** self (existing file)

**Current line 157:**
```python
_SUBDIRS: list[str] = ["srs", "mermaid", "mockup", "backlog", "plugins"]
```

**Patched line 157:**
```python
_SUBDIRS: list[str] = ["srs", "mermaid", "mockup", "backlog", "plugins", "traces"]
```

---

### `ba_tools/__main__.py` (MODIFY — register trace + index)

**Analog:** self (existing file)

**Current import block** (lines 17–30) and `_COMMAND_MODULES` list (lines 32–45). Add two entries:

**Import additions** (after `confirm_cmd` import at line 29):
```python
from ba_tools.commands import (
    ...
    confirm_cmd,
    trace_cmd,   # NEW — TOOL-07
    index_cmd,   # NEW — TOOL-08
)
```

**`_COMMAND_MODULES` additions** (lines 32–45, append two entries):
```python
_COMMAND_MODULES = [
    init_cmd, resolve_route, state_cmd, lint_reqs, verify_cmd,
    uc_status, extract_uc, template_cmd, discovery_cmd, scan_cmd,
    byte_check, confirm_cmd,
    trace_cmd,   # NEW — TOOL-07
    index_cmd,   # NEW — TOOL-08
]
```

---

### `.agents/skills/ba-srs-analyze/SKILL.md` (GREENFIELD)

**No analog exists.** `.agents/skills/` directory does not exist in this repo (confirmed: `ls .agents/` shows only `ba-daily-operators/` and `hooks/`).

**Pattern source:** DESIGN §3 + official Codex docs (confirmed in CONTEXT.md locked decisions CDX-01/02). Only two frontmatter fields are permitted.

**Exact structure to copy:**
```yaml
---
name: ba-srs-analyze
description: >
  Analyze a source document (use case, meeting notes, or brief) and produce
  a grounded, verified requirements.json (IEEE-830 SRS) with source_trace
  citations on every stated requirement. Routes: full, verify-only, iterate.
---

<!-- Workflow file: .agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md -->
<!-- No body content required — SKILL.md is a discovery index only -->
```

**Critical constraint:** NO other frontmatter fields (version, author, tags, etc.) — Codex truncates or rejects extra fields.

---

### `.agents/skills/ba-srs-analyze/agents/openai.yaml` (GREENFIELD)

**No analog exists.** No `openai.yaml` file exists anywhere in this repo (confirmed via `Glob("**/*.yaml", ".agents/")` returned empty).

**Pattern source:** DESIGN §3 + CONTEXT.md CDX-02. Nesting confirmed: `interface.*` and `policy.allow_implicit_invocation`.

**Exact structure:**
```yaml
interface:
  display_name: BA SRS Analyze
  short_description: Extract grounded requirements from a source document
  default_prompt: |
    Run ba-srs-analyze with --route full --source <source_doc> --slug <slug>
    to extract and verify requirements from the source document.
policy:
  allow_implicit_invocation: false
```

**Critical constraint:** `allow_implicit_invocation` MUST be nested under `policy:`, not at root level (CONTEXT.md CDX-02 note — DESIGN §3 shows it flat, which is wrong per official docs).

---

### `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` (GREENFIELD)

**No analog exists.** No `ba-core/` directory exists at `.agents/ba-daily-operators/` level (confirmed: only `ba-tools/` and `hooks/` present).

**Pattern source:** DESIGN §4 (thin orchestrator pattern) + CONTEXT.md D-15/D-16/D-21.

**Structure to follow** (from DESIGN §4 "pass paths not content" + route table D-15):
- Frontmatter: route table mapping `full | verify-only | iterate` → steps
- Body: ordered step list per route, each step either calls a `ba-tools` command or hands off to an agent with a payload of file paths (never raw content)
- Writer payload shape (D-21): `{source_path, sections_dir, slug, route}`
- Critic payload shape (D-21): `{source_path, requirements_json_path}` — `analysis.md` explicitly excluded

---

### `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md` (GREENFIELD)

**No analog exists.** No agent prompt files exist in this repo.

**Pattern source:** CONTEXT.md D-14 (IEEE-830 structure), D-21 (writer payload), D-03 (requirement schema), D-09 (REQ-ID prefixes FR-/NFR-/BR-).

**Key constraints to encode in prompt:**
- Output: `requirements.json` (list of `{id, statement, status, source_trace}`) + `SRS.md` (IEEE-830) + `analysis.md` (rationale, never sent to critic)
- REQ-ID assignment is the writer's judgement (FR-/NFR-/BR- prefix + 3-digit sequence)
- Every `status: stated` requirement MUST have `source_trace.span` = ≥12-char verbatim substring from `source_trace.doc`

---

### `.agents/ba-daily-operators/ba-core/agents/ba-critic.md` (GREENFIELD)

**No analog exists.**

**Pattern source:** CONTEXT.md D-10/D-11 (convergence), D-21 (critic payload), RESEARCH Pitfall 3 (CoVe independence).

**Key constraints to encode in prompt:**
- Input: `{source_path, requirements_json_path}` ONLY — no `analysis.md`, no writer rationale
- Task: re-derive requirements independently from source; compare to provided `requirements.json`; emit FAIL/WARN findings
- Convergence signal: "zero new FAIL-severity findings" = converged; emit `{"converged": true}` or `{"converged": false, "findings": [...]}`

---

### `.agents/ba-daily-operators/ba-tools/ba-core/templates/srs.md` (EVOLVE)

**Analog:** self (existing minimal template at this path, read above)

**Current structure** (lines 1–22 — minimal 3-section template):
```markdown
# Software Requirements Specification: ${title}
**Version:** ${version}  **Date:** ${date}  **Author:** ${author}
## 1. Introduction / ## 2. Requirements (table) / ## 3. Traceability
```

**Target structure** (D-14 — full IEEE-830):
Evolve to add: `§1` Introduction (Purpose/Scope/Definitions), `§2` Overall Description, `§3` Specific Requirements (3.1 `FR-*`, 3.2 `NFR-*`, 3.3 `BR-*`, 3.4 External Interfaces, 3.5 Constraints), `§4` Appendices, `§5` Traceability (filled by `index update`). Use `${...}` placeholder tokens matching the existing convention.

---

## Shared Patterns

### Path Resolution + Traversal Guard
**Source:** `ba_tools/repo.py` lines 50–100; applied in `verify_cmd.py` lines 60–94
**Apply to:** ALL new command files (`trace_cmd.py`, `index_cmd.py`) for every path argument
```python
root = resolve_repo_root(getattr(args, "repo_root", None))
candidate = resolve_under_root(args.some_path, root)
if not is_within_root(candidate, root):
    raise BaToolsError([{"code": "PATH_TRAVERSAL", "path": args.some_path, "message": "..."}])
if not candidate.exists():
    raise BaToolsError([{"code": "FILE_NOT_FOUND", "path": args.some_path, "message": "..."}])
```

### BaToolsError + ok_json Envelope
**Source:** `ba_tools/errors.py` lines 1–24; `ba_tools/output.py` lines 14–38
**Apply to:** ALL new and modified command files
```python
# Success:
ok_json(key=value, ...)   # → stdout: {"ok": true, "failures": [], "key": "value"}
# Failure:
raise BaToolsError([{"code": "CODE", "message": "...", ...}])   # → stderr + exit 2
```

### FileLock Acquire + Write Pattern
**Source:** `ba_tools/state_store.py` lines 52–81; applied in `state_cmd.py` lines 84–110
**Apply to:** `trace_cmd.py` (write per-artifact `.json`), `index_cmd.py` (rewrite `INDEX.md`)
```python
from ba_tools.state_store import acquire_state_lock
from filelock import Timeout

lock = acquire_state_lock(target_path.with_suffix(target_path.suffix + ".lock"))
try:
    with lock:
        target_path.write_text(content, encoding="utf-8")
except Timeout:
    raise BaToolsError([{"code": "LOCK_TIMEOUT", "message": "Lock held >10s; no write performed."}])
```

### register(subparsers) + run(args) Module Contract
**Source:** `ba_tools/__main__.py` lines 61–62 (dispatch loop); `state_cmd.py` lines 20–39 (register pattern)
**Apply to:** ALL new command modules (`trace_cmd.py`, `index_cmd.py`)
```python
def register(subparsers) -> None:
    p = subparsers.add_parser("name", help="...")
    p.add_argument(...)
    p.set_defaults(func=run)

def run(args) -> None:
    ...
```
Every module in `_COMMAND_MODULES` must expose both `register` and `run` at module level.

### Malformed JSON Input Guard
**Source:** `state_cmd.py` lines 62–82 (JSON parse error → `BaToolsError`)
**Apply to:** `trace_cmd.py` (parsing `--requirements` file), `index_cmd.py` (parsing each trace record)
```python
try:
    data = json.loads(raw_text)
except (json.JSONDecodeError, ValueError) as exc:
    raise BaToolsError([{"code": "MALFORMED_JSON", "message": f"Invalid JSON: {exc}"}]) from exc
```

---

## No Analog Found (Greenfield)

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.agents/skills/ba-srs-analyze/SKILL.md` | config | — | No `.agents/skills/` directory exists; first skill in repo |
| `.agents/skills/ba-srs-analyze/agents/openai.yaml` | config | — | No `openai.yaml` anywhere in repo (confirmed glob) |
| `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` | workflow | event-driven | No `ba-core/` at this level; no workflow files exist |
| `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md` | agent-prompt | — | No agent prompts exist in repo |
| `.agents/ba-daily-operators/ba-core/agents/ba-critic.md` | agent-prompt | — | No agent prompts exist in repo |

Planner must use CONTEXT.md locked decisions (CDX-01/02/03, D-10/D-11/D-21) and RESEARCH.md Patterns 3/4 as the specification source for these files.

---

## Key Live Findings (Planner Must Act On)

1. **`check_grounding` dict bug confirmed at line 234** — `lint.py` line 234 calls `.strip()` on the return value of `row.get("source_trace", "")`. When `source_trace` is a dict (JSON path), this raises `AttributeError`. The 3-line patch in the `lint.py` section above is the exact fix.

2. **`_SUBDIRS` at line 157 confirmed** — `scaffold.py` line 157 does NOT include `"traces"`. One-word addition required.

3. **`_COMMAND_MODULES` at lines 32–45 confirmed** — `__main__.py` has 12 entries; `trace_cmd` and `index_cmd` are absent. Two entries to add.

4. **No `.agents/skills/` directory** — Phase 2 creates it. The planner must include a mkdir step before creating skill files.

5. **No `ba-core/` at `.agents/ba-daily-operators/`** — Phase 2 creates `.agents/ba-daily-operators/ba-core/workflows/` and `.agents/ba-daily-operators/ba-core/agents/`. The existing `ba-tools/ba-core/templates/` is unaffected.

6. **`check_citation_present` at lines 250–268 is already dict-aware** — Use it as the model for the `check_grounding` patch. Its `isinstance(source_trace, dict)` guard is the exact pattern to mirror.

7. **INDEX.md scaffold has `## Gaps` and `## Orphans` but NO `## Stale` section** — `index_cmd.py` must add `## Stale` when rewriting `INDEX.md` (RESEARCH open question 3 / D-13).

---

## Metadata

**Analog search scope:** `ba_tools/commands/`, `ba_tools/*.py`, `.agents/`, `ba-core/templates/`
**Files scanned:** 11 source files read
**Pattern extraction date:** 2026-06-17
