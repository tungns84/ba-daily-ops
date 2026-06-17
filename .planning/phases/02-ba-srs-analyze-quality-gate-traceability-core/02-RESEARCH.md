# Phase 02: ba-srs-analyze + Quality Gate + Traceability Core — Research

**Researched:** 2026-06-17
**Domain:** Python CLI extension, Codex skill wiring, IEEE-830 SRS, CoVe gate, traceability spine
**Confidence:** HIGH (all claims sourced from live codebase reads or locked CONTEXT decisions)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Area 1 — Requirements artifact format + verify**
- **D-01:** `requirements.json` is the single canonical source of truth. SRS.md is rendered from JSON — the table in .md is a view, never the master.
- **D-02:** Rework `ba-tools verify` to gate the JSON directly (detect `.json` / `--reqs-format` switch). Phase 1 `verify_cmd.py` parses Markdown table today — that reader is replaced/extended for JSON input. Existing citation/lint/exit-2 semantics preserved; only input parsing changes.
- **D-03:** Per-requirement schema: `{id, statement, status, source_trace: {doc, span, section}}`. Verify citation-checks only `status: stated` reqs. `section: null` → document-scope; otherwise section-scoped.

**Area 2 — trace ↔ index data flow**
- **D-04:** `trace write` emits a uniform JSON record per artifact into `.ba-ops/traces/<kind>-<slug>.json`. `index update` reads only those records to build INDEX.md — never re-parses raw artifacts.
- **D-05:** Trace record schema: `{kind, slug, artifact_path, source_doc, source_hash, req_ids: [{id, statement_hash}]}`.

**Area 3 — Stale / source-drift detection**
- **D-06:** `trace write` captures `source_hash = sha256(source_doc)` at production time. `index update` re-hashes live source doc on disk and flags stale on mismatch.
- **D-07:** Granularity is per source doc (per artifact) — one `source_hash` per trace record.

**Area 4 — REQ-ID registry + numbering**
- **D-08:** Union of all `.ba-ops/srs/*/requirements.json` defines every valid REQ-ID. `.ba-ops/REQUIREMENTS.md` is the rendered human-readable registry. Orphan = downstream trace cites a REQ-ID no `requirements.json` defines.
- **D-09:** REQ-ID numbering = semantic prefix + sequence: `FR-` (functional), `NFR-` (non-functional), `BR-` (business rule), e.g. `FR-001`.

**Area 5 — ba-critic gate authority + convergence**
- **D-10:** `ba-tools verify` is the deterministic hard block (exit 2 on FAIL). `ba-critic` findings drive the ≤3 revision loop: unresolved FAIL-severity findings prevent convergence. After 3 loops still failing → escalate to Confirm checkpoint (human decides), never silent auto-pass.
- **D-11:** Converged = a loop that produces zero new FAIL-severity critic findings. Log `"passed early"` (loop 1) vs `"passed after N"` (loop N>1). WARN findings logged but non-blocking.

**Area 12 — statement_hash semantics**
- **D-12:** `statement_hash` = sha256 of normalized statement (strip + collapse internal whitespace; no case-fold). Detects wording change under same REQ-ID.

**Area 6 — INDEX.md schema**
- **D-13:** `index update` classifies every REQ-ID as: `gap` (no downstream trace), `orphan` (downstream trace cites undefined REQ-ID), `stale` (source_hash mismatch). Phase 2 "gap" = every req until Phases 3-4 add Mermaid/mockup traces — expected, not an error.
- **D-13a:** In Phase 2, gap = REQ-ID with no downstream (Mermaid/mockup/story) coverage. Expected for every req until Phases 3-4.

**Area 7 — SRS.md template**
- **D-14:** `srs.md` template evolves to full IEEE-830: §1 Introduction, §2 Overall Description, §3 FR/NFR/BR subsections, §4 Appendices, Traceability section. Agent renders from `requirements.json`.

**Area 8 — Routes**
- **D-15:** `ba-srs-analyze` exposes three routes: `full` (extract → draft → verify → CoVe → trace + index), `verify-only` (re-run gate on existing JSON), `iterate` (re-draft from discovery entries + prior critic findings).
- **D-16:** `iterate` route input = existing `requirements.json` + accumulated `ba-tools discovery` entries + prior critic FAIL findings. Writer re-drafts; gate + CoVe re-run.
- **D-17:** `extract` route (standalone) — strip a source doc down to raw requirement candidates only (no judgement). Reuses `extract_uc.py` pattern if source is UC-shaped.

**Area 9 — Writer / Critic payload**
- **D-21:** Writer payload = `{source_path, sections_dir, slug, route}`. Critic payload = `{source_path, requirements.json path}` ONLY. `analysis.md` is never in the critic payload.

**Area 10 — dependency zero**
- **D-18:** Phase 2 adds zero new runtime dependencies. Only Python stdlib + existing `filelock`.

**Area 11 — path safety**
- All path inputs use `resolve_under_root` + `is_within_root` from `repo.py`.
- `sys.executable` always used (never `python`/`python3` in subprocess).

**Additional locked decisions (D-19, D-20):**
- **D-19:** `ba-tools verify` `--reqs-format` flag: `md` (default, existing behavior) | `json` (new). Auto-detect by extension also acceptable.
- **D-20:** `check_grounding` in `lint.py` receives JSON rows where `source_trace` is a dict. The JSON-path in `verify_cmd.py` must normalize: treat `source_trace` dict as present iff it has a non-empty `doc` key. Do NOT call `check_grounding` with the dict as a string.

### Claude's Discretion
- Skill/workflow file layout reconciliation: decide whether Phase 2 `ba-core` materials go under `ba-tools/ba-core/` (existing location) or a new parallel `ba-core` at `.agents/ba-daily-operators/ba-core/`. The AI-SPEC shows `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` — recommendation: create new location.
- Test fixture design for the 5 ROADMAP success criteria.
- `statement_hash` normalization: collapse internal whitespace but no case-fold (D-12 confirmed).
- INDEX.md `Status` column vocabulary (gap/orphan/stale/ok).
- Whether `trace write` uses `--reqs` or `--requirements` as the flag name.

### Deferred Ideas (OUT OF SCOPE)
- `ba-mermaid` (Phase 3), `ba-mockup` (Phase 4), `ba-uc` conductor + Safety gate GATE-03 (Phase 5).
- Multi-source-doc per SRS stale detection (D-07 deferred).
- DOCX plugin path (`python-docx` is plugin-only, not on the daily spine).
- Arize Phoenix as a mandatory dependency.
- RAGAS / Promptfoo / Phoenix-evals.
- LLM SDK (`openai` / `anthropic` Python packages) in `ba_tools/`.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SRS-01 | `requirements.json` is the single canonical source of truth; SRS.md is rendered from it | D-01, D-14; `verify_cmd.py` JSON branch (D-02/D-19) |
| SRS-02 | `ba-srs-writer` agent extracts and drafts requirements from source doc | D-21 writer payload `{source_path, sections_dir, slug, route}`; IEEE-830 template (D-14) |
| SRS-03 | Every `stated` requirement carries a `source_trace: {doc, span, section}` | D-03 schema; `citation.py::citation_exists` reuse; `check_grounding` JSON-compat (D-20) |
| SRS-04 | SRS.md rendered from `requirements.json` by `ba-tools` (deterministic) | D-14; template at `.agents/ba-daily-operators/ba-tools/ba-core/templates/srs.md` evolution |
| SRS-05 | `ba-critic` CoVe loop ≤3; independent fresh-context; critic never reads `analysis.md` | D-10, D-11, D-21; loop state tracked in STATE.md via `ba-tools state patch` |
| SRS-06 | `ba-srs-analyze` exposes `full`, `verify-only`, `iterate` routes | D-15, D-16, D-17; workflow file resolves route → workflow step |
| GATE-01 | `ba-tools verify` gates `requirements.json` directly; exit 2 on any FAIL | D-02, D-19, D-20; `verify_cmd.py` JSON branch; `citation_exists` unchanged |
| TRACE-03 | `source_trace` schema enforced on every `stated` requirement | D-03; Pydantic doc schema in AI-SPEC §4b; `check_grounding` dict-aware (D-20) |
| TRACE-04 | `ba-tools trace write` emits per-artifact trace record with `source_hash` + `req_ids` | D-04, D-05, D-06; new `trace_cmd.py`; `acquire_state_lock` reuse for `.ba-ops/traces/` writes |
| TRACE-05 | `ba-tools index update` rebuilds INDEX.md with gap/orphan/stale detection | D-08, D-13, D-13a; new `index_cmd.py`; reads only `.ba-ops/traces/*.json` |
| TOOL-07 | `ba-tools trace write` command registered in `__main__.py` | `__main__.py` line 32 `_COMMAND_MODULES` — add `trace_cmd`; `register` + `run` pattern |
| TOOL-08 | `ba-tools index update` command registered in `__main__.py` | Same `_COMMAND_MODULES` addition for `index_cmd` |
| CDX-01 | `ba-srs-analyze` Codex skill: `SKILL.md` (`name`+`description` only) | DESIGN §3; no `.agents/skills/` dir exists yet — Phase 2 creates it |
| CDX-02 | `agents/openai.yaml` with correct field nesting (`interface.*`, `policy.allow_implicit_invocation: false`) | DESIGN §3 + CONTEXT.md; confirmed nesting: `interface.display_name`, `interface.short_description`, `interface.default_prompt`, `policy.allow_implicit_invocation` |
| CDX-03 | Thin workflow that resolves route → workflow file and follows it | D-15; workflow file at `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` (new location) |
</phase_requirements>

---

## Summary

Phase 2 extends a working Python CLI (`ba-tools`) with two new commands (`trace write`, `index update`), extends the existing `verify` command to accept JSON input, and creates the first Codex skill (`ba-srs-analyze`) in this repository. All four deliverables are grounded in Phase 1 infrastructure — the planner must wire to specific existing signatures rather than invent new ones.

The central technical risk is the `check_grounding` compatibility gap: the existing `lint.py::check_grounding` (line 224) calls `.strip()` on `row.get("source_trace", "")`, treating `source_trace` as a string. For JSON input the value is a dict `{doc, span, section}`. The JSON path in `verify_cmd.py` must normalize this before calling `check_grounding` — either by pre-converting the dict to a truthiness check, or by calling the already-existing `check_citation_present` (lint.py line 250) which is already dict-aware. This is a one-file, three-line fix but if missed silently passes grounding check for all JSON-sourced stated requirements.

The second risk is filesystem layout: no `.agents/skills/` directory exists yet in this repository. Phase 2 will create it from scratch. All Codex skill placement rules (SKILL.md frontmatter `name`+`description` only; `openai.yaml` nesting under `interface:` and `policy:`) are confirmed from CONTEXT.md which cites official Codex docs.

**Primary recommendation:** Build in wave order — (1) `verify` JSON extension + `check_grounding` fix, (2) `trace write` + `index update` + scaffold `traces/` subdir, (3) skill + workflow files, (4) agent prompts (`ba-srs-writer`, `ba-critic`), (5) pytest fixtures F1–F4 + F9 + F10 (the code-dimension fixtures) created alongside the commands that implement them.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Requirements extraction + drafting | Agent (`ba-srs-writer`) | — | Judgement call; determinism boundary (DESIGN §5) |
| Citation gate (span verbatim in source) | CLI (`ba-tools verify`) | — | Hash-provable; exit-2; no LLM |
| Lint heuristics (atomicity, ambiguity, verifiability) | CLI (`ba-tools verify`) | Agent (CoVe loop can catch residual) | Regex/structural proxy = deterministic; residual = judgement |
| CoVe review loop | Agent (`ba-critic`) | Workflow (orchestrates ≤3 loops) | Fresh-context re-derivation is judgement, not hash-provable |
| Loop state tracking (loop counter, convergence verdict) | STATE.md (via `ba-tools state patch`) | Workflow reads STATE.md | Deterministic counter; lockfile-guarded write |
| Trace record emission | CLI (`ba-tools trace write`) | — | Hash-provable (sha256 of source + statements) |
| INDEX.md rebuild | CLI (`ba-tools index update`) | — | Deterministic: reads only trace records |
| SRS.md rendering | CLI (`ba-tools` template/render) | — | Mechanical JSON→Markdown; deterministic |
| REQ-ID assignment (prefix + sequence) | Agent (`ba-srs-writer`) | — | Judgement; stability enforcement is CLI |
| REQ-ID stability / uniqueness enforcement | CLI (`ba-tools lint-requirements`) | — | Jaccard-based; deterministic (Phase 1, reused) |
| Skill routing (route → workflow file) | Codex skill (`ba-srs-analyze`) | Workflow file | Thin orchestrator; no business logic in skill itself |
| Source-drift detection (stale flag) | CLI (`ba-tools index update`) | — | sha256 re-hash; deterministic |

---

## Standard Stack

### Core — Phase 2 adds nothing new (D-18)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`json`, `hashlib`, `pathlib`, `re`, `argparse`) | 3.11+ | JSON parse, sha256, path ops, CLI | Zero deps; `hashlib.file_digest` available 3.11+ |
| `filelock` | 3.x (existing dep) | Lockfile guard for `.ba-ops/traces/` writes | Already installed; Windows-safe; see `state_store.py` |

`python-docx` is plugin-only (not on Phase 2 spine). `@mermaid-js/mermaid-cli` is Phase 3+.

### Installation

No new installs required. Phase 2 spine is stdlib + `filelock` (already in `pyproject.toml`).

```bash
# Verify existing install
cd .agents/ba-daily-operators/ba-tools
pip install -e ".[test]"   # pytest>=9.0 — already declared
```

**Version verification (confirmed via CLAUDE.md / prior phase research):**
- `filelock 3.x` — [VERIFIED: CLAUDE.md sources table — github.com/tox-dev/py-filelock] — on PyPI, actively maintained.
- `python-docx 1.2.0` — [VERIFIED: CLAUDE.md sources table — pypi.org/project/python-docx/] — plugin-only, not Phase 2.

---

## Package Legitimacy Audit

> Phase 2 installs zero new packages (D-18). Audit covers the two existing dependencies relevant to Phase 2 code paths.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `filelock` | PyPI | ~10 yrs (first published 2014) | ~100M+/week (pip itself uses it) | github.com/tox-dev/py-filelock | SUS (registry API returns latest release date 2026-06-13, not package age — false positive) | **Approved** — well-established, used by pip/tox/pytest; CLAUDE.md confirms |
| `python-docx` | PyPI | ~10 yrs | ~2M/week | github.com/python-openxml/python-docx | SUS (unknown-downloads via legitimacy API) | **Approved (plugin-only)** — not on Phase 2 spine; CLAUDE.md confirms version 1.2.0 |

**Packages removed due to SLOP verdict:** none

**Packages flagged as suspicious (SUS) requiring checkpoint:** The `SUS` verdict for both packages is a legitimacy-API false positive caused by download count unavailability on PyPI (PyPI does not expose download counts via the simple JSON API). Both packages are well-established with official source repos confirmed in CLAUDE.md. No `checkpoint:human-verify` task needed — the false-positive signal is documented here.

*The legitimacy seam returned `SUS` for `filelock` citing `too-new` — this refers to the latest version release date (2026-06-13), not the package creation date. The package has existed since 2014. [ASSUMED] based on known package history; the seam does not distinguish package age from latest-release age.*

---

## Architecture Patterns

### System Architecture Diagram

```
[Source Doc (.md / UC)]
        │
        ▼
[ba-srs-writer agent]  ←── Writer payload: {source_path, sections_dir, slug, route}
        │ emits
        ├──► requirements.json   ──► ba-tools verify ──► exit 0 / exit 2
        │         │                        │
        │         │ (if exit 0)            │ (FAIL findings feed back)
        │         ▼                        ▼
        │   [ba-critic agent]   ←── Critic payload: {source_path, requirements.json}
        │         │ loop ≤3              (analysis.md EXCLUDED)
        │         │ converged?
        │         ├── yes (zero new FAILs) ──► ba-tools trace write
        │         │                                  │ emits
        │         │                    .ba-ops/traces/<kind>-<slug>.json
        │         │                                  │
        │         │                        ba-tools index update
        │         │                                  │ reads traces/*.json only
        │         │                             INDEX.md (gap/orphan/stale)
        │         └── no (loop 3, still FAILs) ──► ba-tools confirm (Confirm gate)
        │
        └──► SRS.md (rendered from requirements.json by ba-tools template)
             .ba-ops/srs/<slug>/requirements.json
             .ba-ops/srs/<slug>/analysis.md  (writer rationale, NOT in critic payload)
```

### Recommended Project Structure (Phase 2 additions only)

```
.agents/
├── skills/
│   └── ba-srs-analyze/              # CDX-01: NEW directory (first skill in repo)
│       ├── SKILL.md                 # name + description ONLY (no other frontmatter)
│       └── agents/
│           └── openai.yaml          # interface.* + policy.allow_implicit_invocation: false
│
└── ba-daily-operators/
    ├── ba-core/                     # NEW directory (parallel to ba-tools/ba-core)
    │   ├── workflows/
    │   │   └── ba-srs-analyze.md    # Thin orchestrator: route → steps
    │   └── agents/
    │       ├── ba-srs-writer.md     # Writer agent prompt
    │       └── ba-critic.md         # Critic agent prompt (fresh-context, read-only)
    └── ba-tools/
        ├── ba-core/                 # EXISTING (templates only, Phase 1)
        │   └── templates/
        │       └── srs.md           # EVOLVE to full IEEE-830 (D-14)
        └── ba_tools/
            ├── commands/
            │   ├── verify_cmd.py    # EXTEND: add JSON branch (D-02/D-19/D-20)
            │   ├── trace_cmd.py     # NEW: ba-tools trace write (TOOL-07)
            │   └── index_cmd.py     # NEW: ba-tools index update (TOOL-08)
            └── scaffold.py          # PATCH: add "traces" to _SUBDIRS (line 157)

.ba-ops/
└── traces/                          # NEW subdir (scaffold.py _SUBDIRS patch)
    └── srs-<slug>.json              # Per-artifact trace records (D-05)
```

**Layout decision (Claude's Discretion):** Create `ba-core` at `.agents/ba-daily-operators/ba-core/` (new, parallel to `ba-tools/`). This matches DESIGN §4 and the AI-SPEC path `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md`. The existing `ba-tools/ba-core/` holds templates only and is not disturbed.

### Pattern 1: verify_cmd.py JSON Extension (D-02/D-19/D-20)

**What:** Detect JSON input by extension or `--reqs-format json` flag; replace `_parse_md_table` call with `json.loads()`; normalize `source_trace` dict before calling lint checks.

**Key change in `run()` — JSON branch replaces line 97 `_parse_md_table(reqs_text)` call:**

```python
# Source: verify_cmd.py existing pattern + D-02/D-19/D-20 locked decisions
import json as _json

def _parse_reqs(reqs_text: str, reqs_path: Path, reqs_format: str) -> list[dict]:
    """Return list of row dicts regardless of input format."""
    fmt = reqs_format
    if fmt == "auto":
        fmt = "json" if reqs_path.suffix.lower() == ".json" else "md"
    if fmt == "json":
        data = _json.loads(reqs_text)
        # Normalize: JSON array at top level OR {"requirements": [...]}
        reqs = data if isinstance(data, list) else data.get("requirements", [])
        # Flatten source_trace dict to shape verify_cmd expects:
        # span/section/source come from source_trace sub-dict (D-03)
        rows = []
        for req in reqs:
            st = req.get("source_trace") or {}
            rows.append({
                "id": req.get("id", ""),
                "statement": req.get("statement", ""),
                "status": req.get("status", "stated"),
                "source_trace": st,        # keep dict for check_citation_present
                "span": st.get("span", "") if isinstance(st, dict) else "",
                "section": st.get("section", "") if isinstance(st, dict) else "",
                "source": st.get("doc", "") if isinstance(st, dict) else "",
            })
        return rows
    else:
        return _parse_md_table(reqs_text)
```

**check_grounding compat (D-20):** After normalization, `row["source_trace"]` is a dict. `check_grounding` in `lint.py` line 234 calls `.strip()` on it — which fails for dict. The normalization above ensures `source_trace` is passed as a dict, but `check_grounding` must be patched OR the `verify_cmd.py` JSON path calls `check_citation_present` (which is already dict-aware, `lint.py` line 256) instead of `check_grounding` for the JSON path. **Recommended:** patch `check_grounding` to handle dict `source_trace` (truthy dict with `doc` key = grounded):

```python
# lint.py check_grounding patch (3 lines, replaces line 234-237)
source_trace = row.get("source_trace", "")
if isinstance(source_trace, dict):
    # JSON path: grounded iff source_trace has a non-empty 'doc' key
    source_trace = source_trace.get("doc", "").strip()
else:
    source_trace = source_trace.strip()
```

### Pattern 2: trace_cmd.py (TOOL-07)

**What:** New command module. Emits a trace record (D-05) for one artifact. Uses `acquire_state_lock` from `state_store.py` for the write, mirrors `state_cmd.py` pattern.

```python
# Source: state_store.py::acquire_state_lock (line 52) + D-05 schema
import hashlib, json
from pathlib import Path
from ba_tools.state_store import acquire_state_lock
from ba_tools.repo import resolve_repo_root, resolve_under_root, is_within_root
from ba_tools.output import ok_json
from ba_tools.errors import BaToolsError

def _sha256_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def _sha256_str(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
    # Note: D-12 normalization = strip + collapse internal whitespace:
    # import re; normalized = re.sub(r'\s+', ' ', text.strip())

def run(args) -> None:
    root = resolve_repo_root(getattr(args, "repo_root", None))
    # resolve + guard all paths (T-1-01)
    artifact_path = resolve_under_root(args.artifact, root)
    source_doc = resolve_under_root(args.source_doc, root)
    reqs_path = resolve_under_root(args.requirements, root)
    # ... path traversal checks ...
    reqs = json.loads(reqs_path.read_text("utf-8"))
    req_ids = [
        {"id": r["id"], "statement_hash": _sha256_normalized(r["statement"])}
        for r in (reqs if isinstance(reqs, list) else reqs.get("requirements", []))
    ]
    source_hash = _sha256_file(source_doc)
    record = {
        "kind": args.kind,
        "slug": args.slug,
        "artifact_path": str(artifact_path.relative_to(root)),
        "source_doc": str(source_doc.relative_to(root)),
        "source_hash": source_hash,
        "req_ids": req_ids,
    }
    traces_dir = root / ".ba-ops" / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    out_path = traces_dir / f"{args.kind}-{args.slug}.json"
    lock_path = out_path.with_suffix(".json.lock")
    with acquire_state_lock(lock_path):
        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), "utf-8")
    ok_json(trace=str(out_path.relative_to(root)), kind=args.kind, slug=args.slug)
```

### Pattern 3: index_cmd.py (TOOL-08)

**What:** Reads all `.ba-ops/traces/*.json`, re-hashes source docs, computes gap/orphan/stale, rewrites INDEX.md under lockfile.

```python
# Source: D-04, D-05, D-06, D-08, D-13 locked decisions
# Key algorithm:
def run(args) -> None:
    root = resolve_repo_root(getattr(args, "repo_root", None))
    traces_dir = root / ".ba-ops" / "traces"
    # 1. Load all trace records
    all_traces = [json.loads(p.read_text("utf-8")) for p in traces_dir.glob("*.json")]
    # 2. Collect valid REQ-IDs from all srs traces (D-08)
    valid_ids = {rid["id"] for t in all_traces if t["kind"] == "srs"
                 for rid in t.get("req_ids", [])}
    # 3. Determine stale (D-06): re-hash live source, compare to trace source_hash
    stale_slugs = set()
    for trace in all_traces:
        src = root / trace["source_doc"]
        if src.exists():
            live_hash = _sha256_file(src)
            if live_hash != trace.get("source_hash", ""):
                stale_slugs.add(trace["slug"])
    # 4. Build matrix rows, classify gap/orphan/stale (D-13)
    # gap: srs req with no non-srs trace referencing it
    # orphan: non-srs trace references req_id not in valid_ids
    # stale: trace slug in stale_slugs
    # 5. Rewrite INDEX.md under lockfile
    index_path = root / ".ba-ops" / "INDEX.md"
    lock_path = index_path.with_suffix(".md.lock")
    with acquire_state_lock(lock_path):
        index_path.write_text(_render_index(matrix, gaps, orphans, stale), "utf-8")
```

### Pattern 4: SKILL.md + openai.yaml (CDX-01/CDX-02)

```yaml
# .agents/skills/ba-srs-analyze/SKILL.md
# ONLY these two frontmatter fields — no others (DESIGN §3 / official Codex docs)
---
name: ba-srs-analyze
description: >
  Analyze a source document (use case, meeting notes, or brief) and produce
  a grounded, verified requirements.json (IEEE-830 SRS) with source_trace
  citations on every stated requirement.
---
```

```yaml
# .agents/skills/ba-srs-analyze/agents/openai.yaml
# Correct nesting confirmed: interface.* and policy.allow_implicit_invocation
interface:
  display_name: BA SRS Analyze
  short_description: Extract grounded requirements from a source document
  default_prompt: |
    Run ba-srs-analyze --route full --source <source_doc> --slug <slug>
policy:
  allow_implicit_invocation: false
```

### Anti-Patterns to Avoid

- **Reading `analysis.md` in `ba-critic` prompt:** Critic payload is `{source_path, requirements.json}` ONLY (D-21). Passing `analysis.md` collapses CoVe to self-agreement.
- **`ba-tools` calling any LLM SDK:** `ba_tools/` must contain zero LLM imports (DESIGN §5). Any `import openai` / `import anthropic` in `ba_tools/` is a G4 guardrail failure.
- **Silent auto-pass on loop 3:** After 3 loops still failing, the workflow must call `ba-tools confirm` (escalate to Confirm gate), never emit `"converged"` with open FAILs.
- **Hard-coding paths:** All paths via `resolve_under_root` + `--repo-root`. Never `D:\...\python.exe`.
- **`python`/`python3` in subprocess:** Always `sys.executable` (DESIGN §11).
- **Writing to `.ba-ops/traces/` without a lockfile:** Use `acquire_state_lock` (state_store.py line 52) on a `.json.lock` sibling file.
- **Calling `check_grounding` with a dict `source_trace` (pre-patch):** Will raise `AttributeError: 'dict' object has no attribute 'strip'`. Must patch `lint.py` or normalize in `verify_cmd.py` JSON path first.
- **Adding `"traces"` to INDEX.md matrix as a column:** `traces/` is the storage dir, not a matrix column. INDEX.md matrix columns are REQ-ID, SRS §, Mermaid, Mockup, Story, Status.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-platform file locking | Raw `os.open(O_EXCL)` | `filelock.FileLock` (state_store.py line 52/81) | Windows PermissionError = live lock sentinel; `filelock` handles correctly |
| SHA-256 of file | `hashlib.sha256(file.read())` | `hashlib.file_digest(f, "sha256")` (Python 3.11+) | Streaming; no full binary load into memory |
| Path traversal guard | Manual `str.startswith` | `repo.py::is_within_root` (line 72) | `resolve()` normalizes `..`; `relative_to()` raises ValueError on escape |
| CLI argument parsing | Click or custom dispatch | `argparse` + existing `_COMMAND_MODULES` pattern | ≤12 commands; zero external dep; consistent with existing modules |
| Loop state persistence | In-memory variable in workflow | `ba-tools state patch` → STATE.md | Durable across agent invocations; lockfile-guarded; `iteration` key already in `ALLOWED_KEYS` |
| Citation check logic | New substring search | `citation.py::citation_exists` (existing, unchanged) | Already handles section-scope, document-scope, 12-char minimum, heading normalization |
| Markdown section extraction | New regex | `markdown_sections.extract()` (used in `extract_uc.py` line 77) | Level-aware stop; tested in Phase 1 |
| Registry index of all REQ-IDs | Re-parse `requirements.json` in index_cmd | Read `req_ids` from trace records only (D-04) | Uniform input; no cross-artifact parser complexity |

---

## Runtime State Inventory

> This is a greenfield phase (new commands + new skill). No rename/refactor/migration.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `.ba-ops/` exists with empty scaffold from Phase 1. No `traces/` subdir. | `scaffold.py` `_SUBDIRS` (line 157) must add `"traces"` |
| Live service config | No external service config affected | None |
| OS-registered state | No OS-level registrations | None |
| Secrets/env vars | None | None |
| Build artifacts | `ba_tools.egg-info/` will be stale after adding new command modules | `pip install -e .` re-run after adding `trace_cmd` and `index_cmd` |

**Nothing found in category:** Confirmed by filesystem inspection — no live services, no OS registrations, no secrets.

---

## Common Pitfalls

### Pitfall 1: check_grounding dict incompatibility (D-20)

**What goes wrong:** `lint.py::check_grounding` line 234 calls `row.get("source_trace", "").strip()`. For JSON input, `source_trace` is a dict. `.strip()` on a dict raises `AttributeError`, which propagates as `INTERNAL_ERROR` from `__main__.py` (masking the real cause).

**Why it happens:** Phase 1 Markdown table rows store `source_trace` as a string column value. Phase 2 JSON rows store it as a nested object per D-03.

**How to avoid:** Patch `check_grounding` in `lint.py` before wiring the JSON path (3-line fix shown in Pattern 1 above). Write test F2/F3 before implementing the JSON path to catch this immediately.

**Warning signs:** `INTERNAL_ERROR` in stderr when running `ba-tools verify` on a `.json` file.

### Pitfall 2: traces/ lockfile collision

**What goes wrong:** Two concurrent `ba-tools trace write` calls on the same slug both succeed, second write silently overwrites the first.

**Why it happens:** `Path.write_text()` is not atomic on all filesystems. Without a lockfile, a concurrent write wins with no error.

**How to avoid:** Always wrap the `write_text` call in `acquire_state_lock(out_path.with_suffix(".json.lock"))`. Use `with` block as shown in Pattern 2.

**Warning signs:** Trace records with missing `req_ids` entries when running parallel operators.

### Pitfall 3: Critic reads analysis.md (D-21 / G3)

**What goes wrong:** The workflow passes `analysis.md` in the critic payload "for context." The critic's reasoning aligns with the writer's rationale rather than re-deriving from source. CoVe collapses to self-agreement (AI-SPEC Failure mode #2).

**Why it happens:** Seems helpful to give the critic the writer's reasoning. Is a critical correctness failure.

**How to avoid:** Critic payload is exactly `{source_path, requirements.json path}` — nothing else. Assert/log the input set (G3 guardrail). Fixture F11 (`critic-independence`) catches this in tests.

**Warning signs:** Critic PASS on fixtures F2/F3 (known-bad fixtures that verify should catch).

### Pitfall 4: Silent auto-pass on loop 3 (D-10 / D-11 / G2)

**What goes wrong:** Workflow loop counter reaches 3 with open FAIL findings; workflow emits `"converged"` anyway to avoid blocking the BA.

**Why it happens:** Pressure to complete the workflow; missing escalation branch.

**How to avoid:** After loop 3 FAIL, call `ba-tools confirm --gate quality --require-human` (escalate to Confirm gate). Log `"non-convergence-escalation"` in STATE.md. Fixture F12 (`non-convergence-escalate`) validates this path.

**Warning signs:** STATE.md shows `iteration: 3` with `status: converged` but no Confirm gate verdict recorded.

### Pitfall 5: index update re-parses raw artifacts (D-04 violation)

**What goes wrong:** `index_cmd.py` reads `requirements.json` directly or parses SRS.md to build the matrix, instead of reading only `.ba-ops/traces/*.json`.

**Why it happens:** Seems more direct. Breaks the uniform-input contract — different artifact types (SRS JSON, Mermaid .mmd, HTML mockup) would each need a custom parser.

**How to avoid:** `index_cmd.py` reads ONLY files matching `.ba-ops/traces/*.json`. REQ-IDs come from `req_ids` array in each trace record. Source-doc path and hash come from `source_doc` and `source_hash` fields.

**Warning signs:** `index_cmd.py` contains `import` of any artifact-specific parser.

### Pitfall 6: Missing "traces" in scaffold _SUBDIRS

**What goes wrong:** `ba-tools trace write` creates `.ba-ops/traces/` via `mkdir(parents=True, exist_ok=True)` inline — but `ba-tools init` never creates it. A fresh repo init followed by `trace write` works, but the scaffold is incomplete.

**Why it happens:** `scaffold.py` `_SUBDIRS` (line 157) currently lists: `["srs", "mermaid", "mockup", "backlog", "plugins"]`. No `"traces"`.

**How to avoid:** Add `"traces"` to `_SUBDIRS` in `scaffold.py`. This is a one-word change. Include as a Wave 0 task.

---

## Code Examples

Verified patterns from live Phase 1 codebase:

### Existing: acquire_state_lock (state_store.py, line 52)

```python
# Source: .agents/ba-daily-operators/ba-tools/ba_tools/state_store.py:52
# Reuse verbatim for .ba-ops/traces/ writes
def acquire_state_lock(lock_path: Path) -> FileLock:
    if lock_path.exists():
        try:
            age = time.time() - lock_path.stat().st_mtime
        except OSError:
            age = 0.0
        if age > STALE_SECONDS:
            try:
                os.remove(lock_path)
            except PermissionError:
                pass
    return FileLock(str(lock_path), timeout=STALE_SECONDS)
```

### Existing: citation_exists (citation.py) — reuse unchanged

```python
# Source: .agents/ba-daily-operators/ba-tools/ba_tools/citation.py
# Called from verify_cmd.py line 186; no changes needed for JSON path
# Signature:
citation_exists(source_doc: Path, span: str, section: str | None, cite_scope: str = "section") -> bool
# Returns False if span < 12 chars (built-in guard)
```

### Existing: _COMMAND_MODULES registration (__main__.py, line 32)

```python
# Source: .agents/ba-daily-operators/ba-tools/ba_tools/__main__.py:32
# Add trace_cmd and index_cmd to this list:
_COMMAND_MODULES = [
    init_cmd, resolve_route, state_cmd, lint_reqs, verify_cmd,
    uc_status, extract_uc, template_cmd, discovery_cmd, scan_cmd,
    byte_check, confirm_cmd,
    trace_cmd,   # NEW — TOOL-07
    index_cmd,   # NEW — TOOL-08
]
```

### Existing: resolve_under_root + is_within_root (repo.py, line 50/72)

```python
# Source: .agents/ba-daily-operators/ba-tools/ba_tools/repo.py:50
# Pattern applied in every new command (T-1-01):
candidate = resolve_under_root(args.artifact, root)
if not is_within_root(candidate, root):
    raise BaToolsError([{"code": "PATH_TRAVERSAL", "path": args.artifact, ...}])
```

### Existing: ok_json / BaToolsError (output.py / errors.py)

```python
# Source: .agents/ba-daily-operators/ba-tools/ba_tools/output.py
ok_json(trace="...", kind="srs", slug="my-slug")
# emits: {"ok": true, "failures": [], "trace": "...", "kind": "srs", "slug": "my-slug"}

# Source: .agents/ba-daily-operators/ba-tools/ba_tools/errors.py
raise BaToolsError([{"code": "TRACE_NOT_FOUND", "slug": args.slug, "message": "..."}])
# __main__.py catches → stderr JSON + exit 2
```

### D-12 statement_hash normalization

```python
# Source: D-12 locked decision; stdlib only
import re, hashlib

def statement_hash(statement: str) -> str:
    """sha256 of normalized statement (strip + collapse internal whitespace; no case-fold)."""
    normalized = re.sub(r'\s+', ' ', statement.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Markdown table as canonical requirements store | `requirements.json` as canonical (D-01) | Phase 2 decision | SRS.md becomes a rendered view; verify gates JSON directly |
| `verify` parses Markdown table only | `verify` detects `.json` / `--reqs-format json` (D-02/D-19) | Phase 2 | Enables deterministic gate on structured data |
| No downstream traceability in Phase 1 | `trace write` + `index update` produce INDEX.md (D-04/D-08/D-13) | Phase 2 | Gap/orphan/stale detection from Phase 2 onward |
| No Codex skill exists in repo | `ba-srs-analyze` skill created (CDX-01/02/03) | Phase 2 | First skill — establishes the pattern for all subsequent operators |

**Deprecated/outdated:**
- `_parse_md_table` as the sole input path in `verify_cmd.py`: preserved for backward compat (`--reqs-format md`) but no longer the only path.
- `REQUIREMENTS.md` Markdown table as the requirements master: becomes a rendered view generated by `ba-tools` from `requirements.json`.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `ba-core` at `.agents/ba-daily-operators/ba-core/` (new) is the correct location for workflows and agent prompts | Architecture Patterns | If wrong: workflows go under `ba-tools/ba-core/workflows/` (existing); adjust path in skill's `default_prompt` |
| A2 | `hashlib.file_digest` available (Python 3.11+); target environment meets 3.11+ | Standard Stack | If Python < 3.11: use chunked `hashlib.sha256()` fallback; CLAUDE.md says 3.11+ is minimum |
| A3 | `filelock` legitimacy-API SUS verdict is a false positive (package age ~10 yrs, not package release date) | Package Legitimacy Audit | If wrong (actual new package): use `os.open(O_EXCL)` fallback on POSIX, but `filelock` is already in pyproject.toml |
| A4 | `check_citation_present` in `lint.py` (line 250) is already dict-aware and can supplement `check_grounding` for JSON path | Code Examples — Pattern 1 | If missing: write the dict-aware check inline in `verify_cmd.py` JSON path |
| A5 | `statement_hash` normalization = strip + collapse whitespace, no case-fold (D-12) | Code Examples | If case-fold is later required: all existing hashes need recomputation |
| A6 | INDEX.md `Status` column vocabulary: `gap`, `orphan`, `stale`, `ok` | Architecture Patterns | If vocabulary changes: `index_cmd.py` render and tests need updating |

---

## Open Questions

1. **`ba-core` location for workflows/agents**
   - What we know: DESIGN §4 says `.agents/ba-daily-operators/ba-core/`; AI-SPEC shows that path; Phase 1 placed `ba-core` under `ba-tools/`.
   - What's unclear: Whether the planner should use the existing `ba-tools/ba-core/` for consistency or create the DESIGN-specified parallel `ba-core/`.
   - Recommendation: Create `.agents/ba-daily-operators/ba-core/` (new). Templates stay in `ba-tools/ba-core/templates/`. This matches DESIGN §4 and AI-SPEC exactly. If planner disagrees, note the deviation.

2. **`--reqs-format` flag name vs. auto-detect**
   - What we know: D-19 says either auto-detect by `.json` extension OR `--reqs-format json` flag.
   - What's unclear: Whether the Phase 1 Markdown path must remain accessible via `--reqs-format md` for backward compat.
   - Recommendation: Auto-detect by extension (`.json` → JSON path; anything else → Markdown path) + optional `--reqs-format` override. Preserves backward compat with no flag change for existing Markdown users.

3. **INDEX.md Stale section**
   - What we know: D-13 mentions a `## Stale` section in INDEX.md. The current scaffold (scaffold.py line 78–100) has `## Gaps` and `## Orphans` but no `## Stale`.
   - What's unclear: Whether `stale` rows go in the Matrix (as a Status value) or in a separate `## Stale` section.
   - Recommendation: Use a `Status` column in the Matrix (`gap`, `orphan`, `stale`, `ok`) plus separate `## Gaps`, `## Orphans`, `## Stale` roll-up sections listing IDs. The scaffold must be updated.

---

## Environment Availability

> All Phase 2 work is code/config additions. No new external tools.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | `hashlib.file_digest` | [ASSUMED] ✓ | CLAUDE.md states 3.11+ minimum | Chunked `hashlib.sha256()` for Python <3.11 |
| `filelock` | trace_cmd.py, index_cmd.py | ✓ (existing dep) | 3.x | `os.open(O_EXCL)` on POSIX only |
| `pytest` | test suite | ✓ (existing dev dep) | >=9.0 | None needed |
| `git` | `repo.py::resolve_repo_root` | ✓ (assumed in dev env) | any | Falls back to `Path.cwd()` |

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

> `workflow.nyquist_validation: true` in `.planning/config.json` — section required.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >= 9.0 |
| Config file | `.agents/ba-daily-operators/ba-tools/pyproject.toml` (existing) |
| Quick run command | `cd .agents/ba-daily-operators/ba-tools && python -m pytest tests/test_verify.py tests/test_lint_reqs.py tests/test_trace.py tests/test_index.py -q` |
| Full suite command | `cd .agents/ba-daily-operators/ba-tools && python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SRS-01 | `requirements.json` is canonical; SRS.md rendered from it | unit | `pytest tests/test_verify.py::test_json_input_accepted -x` | ❌ Wave 0 |
| SRS-03 | `source_trace` schema enforced | unit | `pytest tests/test_verify.py::test_grounding_json_dict -x` | ❌ Wave 0 |
| GATE-01 | `verify` exits 2 on ungrounded JSON span (F2 fixture) | unit | `pytest tests/test_verify.py::test_citation_not_found_json -x` | ❌ Wave 0 |
| GATE-01 | `verify` exits 2 on paraphrased span (F3 fixture) | unit | `pytest tests/test_verify.py::test_paraphrased_span -x` | ❌ Wave 0 |
| GATE-01 | `verify` exits 2 on wrong-section span (F4 fixture) | unit | `pytest tests/test_verify.py::test_wrong_section_span -x` | ❌ Wave 0 |
| GATE-01 | `verify` exits 0 on clean grounded input (F1 fixture) | unit | `pytest tests/test_verify.py::test_clean_grounded_passes -x` | ❌ Wave 0 |
| TRACE-03 | `check_grounding` handles dict source_trace correctly | unit | `pytest tests/test_lint_reqs.py::test_grounding_dict_compat -x` | ❌ Wave 0 |
| TRACE-04 | `trace write` emits correct JSON record with source_hash | unit | `pytest tests/test_trace.py::test_trace_write_schema -x` | ❌ Wave 0 |
| TRACE-04 | `trace write` uses lockfile (no concurrent overwrite) | unit | `pytest tests/test_trace.py::test_trace_lockfile -x` | ❌ Wave 0 |
| TRACE-05 | `index update` classifies gap/orphan/stale correctly (F10 fixture) | unit | `pytest tests/test_index.py::test_gap_orphan_stale -x` | ❌ Wave 0 |
| SRS-05 / D-10 | statement_hash drift detected (F9 fixture) | unit | `pytest tests/test_lint_reqs.py::test_stability_drift -x` | ❌ Wave 0 (uses existing `detect_reqid_issues` — test may partially exist) |
| D-10 / D-11 | Convergence loop 3 → escalation, not auto-pass (F12 fixture) | integration | `pytest tests/test_index.py::test_non_convergence_escalation -x` | ❌ Wave 0 |
| CDX-01/02/03 | SKILL.md frontmatter has only `name` + `description` | lint/schema | `pytest tests/test_skill_schema.py -x` | ❌ Wave 0 |
| TOOL-07/08 | `trace write` + `index update` registered in `_COMMAND_MODULES` | smoke | `pytest tests/test_smoke.py::test_commands_registered -x` | ❌ Wave 0 |
| D-05 | Trace record `statement_hash` normalization (D-12) | unit | `pytest tests/test_trace.py::test_statement_hash_normalization -x` | ❌ Wave 0 |

### Fixture Map (AI-SPEC §5 reference dataset)

| Fixture ID | File Location | Exercises | Test File |
|------------|--------------|-----------|-----------|
| F1 | `tests/fixtures/srs/clean-uc-grounded/` | Happy path: exit 0, critic converges loop 1 | test_verify.py |
| F2 | `tests/fixtures/srs/ungrounded-span/` | CITATION_NOT_FOUND: invented span | test_verify.py |
| F3 | `tests/fixtures/srs/paraphrased-span/` | CITATION_NOT_FOUND: paraphrase not verbatim | test_verify.py |
| F4 | `tests/fixtures/srs/wrong-section-span/` | Section-scope rejection, document-scope pass | test_verify.py |
| F9 | `tests/fixtures/srs/renumbered-reqid/` | stability lint flags drift | test_lint_reqs.py |
| F10 | `tests/fixtures/srs/gap-orphan-stale/` | INDEX.md gap/orphan/stale classification | test_index.py |
| F11 | `tests/fixtures/srs/critic-independence/` | Critic payload excludes analysis.md | manual/lint |
| F12 | `tests/fixtures/srs/non-convergence-escalate/` | Loop 3 → escalation, not auto-pass | test_index.py (integration) |

**Build fixtures F1–F4, F9, F10 during implementation** (required to test commands as they are built, per AI-SPEC §5 note).

### Sampling Rate

- **Per task commit:** `cd .agents/ba-daily-operators/ba-tools && python -m pytest tests/test_verify.py tests/test_trace.py tests/test_index.py -q`
- **Per wave merge:** `cd .agents/ba-daily-operators/ba-tools && python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_trace.py` — covers TOOL-07 / TRACE-04
- [ ] `tests/test_index.py` — covers TOOL-08 / TRACE-05
- [ ] `tests/test_skill_schema.py` — covers CDX-01/02/03 (validate SKILL.md frontmatter, openai.yaml nesting)
- [ ] `tests/test_smoke.py` — smoke test all commands registered and reachable via `ba-tools --help`
- [ ] `tests/fixtures/srs/` — 6 fixture directories (F1–F4, F9, F10) with `source.md`, `requirements.json`, `expected_exit_code`
- [ ] `tests/test_verify.py` — extend existing file with JSON-path test cases (may exist partially)

*(If `tests/test_verify.py` already exists from Phase 1: verify it covers `_parse_md_table`; extend, don't replace)*

---

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1` in `.planning/config.json`.

### Applicable ASVS Categories (ASVS Level 1)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth layer (local CLI tool) |
| V3 Session Management | No | No sessions (stateless CLI) |
| V4 Access Control | Partial | Path traversal guard via `is_within_root` (T-1-01) — attacker-influenced paths in `--reqs`, `--source`, `--artifact`, `--source-doc` must be validated |
| V5 Input Validation | Yes | JSON schema validation in `verify_cmd.py` JSON branch; `id` regex `^(FR\|NFR\|BR)-\d{3,}$`; reject malformed JSON before processing |
| V6 Cryptography | Partial | SHA-256 via stdlib `hashlib` — correct. Never hand-roll hash functions. |
| V7 Error Handling | Yes | `BaToolsError` → stderr JSON + exit 2; bare `Exception` → `INTERNAL_ERROR` envelope (no traceback leak, `__main__.py` line 84–98) |

### Known Threat Patterns for this Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via `--reqs` / `--artifact` / `--source-doc` | Tampering / Info Disclosure | `resolve_under_root` + `is_within_root` (repo.py:50/72); emit `PATH_TRAVERSAL` code on escape |
| Malformed JSON crashing gate (exit 1 instead of exit 2) | Tampering | `json.loads()` in try/except → `BaToolsError([{"code": "MALFORMED_JSON", ...}])` — always exit 2, never 1 |
| LLM import smuggled into `ba_tools/` | Tampering / Info Disclosure | CI lint assertion: `grep -r "import openai\|import anthropic" ba_tools/` must return empty (G4 guardrail) |
| Traceback leak via unhandled exception | Info Disclosure | `__main__.py` bare-`except Exception` wraps all commands; emits only `INTERNAL_ERROR` code |
| Lock file starvation | DoS | `FileLock(timeout=STALE_SECONDS)` with stale-lock reclaim (state_store.py:52–81) |
| `statement_hash` collision false-negative | Tampering | SHA-256 collision is computationally infeasible; stdlib `hashlib` is correct choice |
| Arbitrary write via `trace write --artifact ../../etc/passwd` | Tampering | `is_within_root` guard; `PATH_TRAVERSAL` error code |

---

## Sources

### Primary (HIGH confidence — live codebase reads)

- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/verify_cmd.py` — lines 1–206, full function signatures
- `.agents/ba-daily-operators/ba-tools/ba_tools/citation.py` — `citation_exists` signature and behavior
- `.agents/ba-daily-operators/ba-tools/ba_tools/lint.py` — all check functions + `check_grounding` dict-compat finding
- `.agents/ba-daily-operators/ba-tools/ba_tools/state_store.py` — `acquire_state_lock` (line 52), `ALLOWED_KEYS`, `PIPELINE_STEPS`
- `.agents/ba-daily-operators/ba-tools/ba_tools/__main__.py` — `_COMMAND_MODULES` list (line 32)
- `.agents/ba-daily-operators/ba-tools/ba_tools/scaffold.py` — `_SUBDIRS` (line 157), INDEX.md seed
- `.agents/ba-daily-operators/ba-tools/ba_tools/repo.py` — `resolve_under_root`, `is_within_root`
- `.planning/phases/02-ba-srs-analyze-quality-gate-traceability-core/02-CONTEXT.md` — all locked decisions D-01 through D-21
- `.planning/phases/02-ba-srs-analyze-quality-gate-traceability-core/02-AI-SPEC.md` — evaluation dimensions, fixture set, guardrails

### Secondary (MEDIUM confidence — planning documents)

- `.planning/REQUIREMENTS.md` — 15 Phase 2 requirement IDs confirmed
- `DESIGN.md` v0.2.2 — architectural layer model, skill placement rules, byte budgets
- `CLAUDE.md` — stack versions, non-negotiables, package sources

### Tertiary (LOW confidence — assumptions)

- `filelock` package age (known ~10 years but not confirmed in this session via authoritative source)
- Python 3.11+ availability on target machine (stated in CLAUDE.md as minimum requirement)

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — zero new deps; all existing packages confirmed via CLAUDE.md and live pyproject.toml
- Architecture: HIGH — all patterns derived from live Phase 1 source with file:line anchors
- Pitfalls: HIGH — `check_grounding` dict issue confirmed by reading lint.py line 234; all others derived from locked decisions

**Research date:** 2026-06-17
**Valid until:** 2026-07-17 (stable stack; no external dependencies changing)
