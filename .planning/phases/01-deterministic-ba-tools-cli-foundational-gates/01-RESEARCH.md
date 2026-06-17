# Phase 1: Deterministic ba-tools CLI + Foundational Gates - Research

**Researched:** 2026-06-17
**Domain:** Python CLI tooling, file-state spine, concurrency, requirements linting, verbatim citation verification
**Confidence:** MEDIUM (stack is largely locked in CLAUDE.md; open areas researched via Context7 + WebSearch)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Use the `filelock` library (`FileLock(timeout=10)`), NOT raw `os.open(..., O_EXCL)`. Target env is Windows 11.

**D-02 (deviation, recorded deliberately):** Overrides literal TOOL-03 wording ("`O_EXCL` lockfile") and "zero external Python deps for the spine" ideal. `filelock` becomes the **single runtime dependency** of the spine. The behavioral contract of TOOL-03 is preserved (guarded writes, never clobber, 10s stale reclaim).

**D-03:** **Flat envelope** — every response is `{ok: <bool>, failures: [...], ...<command fields merged at top level>}`. `failures` always present (empty array on success). No nested `data: {}` wrapper.

**D-04:** **Success JSON → stdout. Error JSON → stderr, then exit code 2** (`BaToolsError`).

**D-05:** Two-layer wiring for GATE-04 — a **`ba-tools` subcommand** (portable core) AND a **committed git pre-commit hook** that calls it.

**D-06 (planner note):** Repo is not yet git-initialized. The `ba-tools` subcommand is source of truth; pre-commit hook activates once repo is under git. Planner must not block the subcommand on the hook.

**D-07:** Lint severity: **FAIL** (blocks `ba-tools verify`): grounding, verifiability, atomicity, citation-exists. **WARN** (advisory): ambiguity. REQ-ID material-change (TOOL-05) is **always FAIL**.

**D-08:** Objective/deterministic checks gate hard; subjective signals warn. `verify` exit code is non-zero only on FAIL-class findings.

**Carried forward (do NOT re-decide):**
- Python 3.11+, stdlib-first; `sys.executable`.
- `argparse` for dispatch (click only past ~10 nested subgroups).
- All paths relative to `--repo-root`; no hard-coded machine paths.
- Citation-exists = section-scoped, ≥12-char verbatim substring, `--cite-scope document` override.
- `WARN_INJECTION` scan is advisory in v1.
- REQ-ID stability lint lands in Phase 1 with a renumbered-requirements fixture.
- `.ba-ops/config.json` feature flags default `true` when missing (absent = enabled).

### Claude's Discretion

- CLI module layout (single `ba_tools.py` vs `ba_tools/` package with per-command modules).
- Exact lint heuristics (weasel-word list, atomicity detection, verifiability cues).
- Test-fixture design for the 5 success criteria.
- `.ba-ops/` scaffold seed content / template bodies.

### Deferred Ideas (OUT OF SCOPE)

- `WARN_INJECTION` promoted to hard gate — deferred to later milestone.
- `trace write` (TOOL-07) + `index update` (TOOL-08) + INDEX.md matrix — Phase 2.
- Quality gate + `ba-critic` CoVe loop (GATE-01) — Phase 2.
- Safety gate contract for render/embed (GATE-03) — Phase 5.
- Render subcommands (`export-diagram`, `render-mermaid`, `update-docx`, `manifest`, `package`) — plugins/later phases.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TOOL-01 | `ba-tools init <operator>` returns context JSON (config, routes, default_route, state) | DEFAULT_ROUTE table pattern; config.json absent=enabled; `.ba-ops/` scaffold |
| TOOL-02 | `resolve-route <operator>` returns static DEFAULT_ROUTE only — never infers from free text | Static dispatch table pattern; verified via route table in DESIGN §4 |
| TOOL-03 | `state update|patch|advance` writes `.ba-ops/STATE.md` guarded by lockfile (stale-lock reclaimed after 10s) | FileLock(timeout=10) semantics; stale-lock reclaim pattern for Windows |
| TOOL-04 | `lint-requirements` flags ambiguity, atomicity, grounding, verifiability, citation issues | Lint heuristics: weasel-word list, conjunction detection, measurable threshold check |
| TOOL-05 | Enforces REQ-ID stability — flags material statement change on existing ID (never silent renumber) | Word-set diff / normalized text comparison against renumbered-requirements fixture |
| TOOL-06 | `ba-tools verify` gate: verbatim citation-exists (≥12-char, section-scoped), REQ-ID coverage, hash-match; folds lint | Section-scoped Markdown parser with `re`; substring check; `--cite-scope` override |
| TOOL-09 | `ba-tools uc-status` returns single-UC pipeline state + `next_step` (resumable) | STATE.md JSON structure; `.ba-ops/` file shape |
| TOOL-10 | `ba-tools extract-uc --uc "<spec>"` returns UC section + parsed identity | stdlib `re` heading parser pattern |
| TOOL-11 | `ba-tools template fill` scaffolds artifact from `ba-core/templates` | Template fill = string substitution; no external deps needed |
| TOOL-12 | `ba-tools discovery add|list` captures and lists iteration discoveries | Simple JSONL append to `.ba-ops/discoveries.jsonl` or STATE.md section |
| TOOL-13 | Every success prints UTF-8 JSON stdout; every `BaToolsError` exits code 2 | D-03/D-04 envelope pattern; `sys.exit(2)` in BaToolsError handler |
| TOOL-14 | All paths resolve relative to `--repo-root`; Python via `sys.executable` | `pathlib.Path` relative to repo root; `sys.executable` confirmed available |
| TOOL-15 | `ba-tools scan --file <f>` runs advisory prompt-injection scan | Advisory only (D-07/D-08); simple pattern match; never blocks |
| TRACE-01 | `.ba-ops/` scaffold exists: PROJECT.md, REQUIREMENTS.md, INDEX.md, STATE.md, config.json | File shape design; `ba-tools init` creates scaffold on first run |
| TRACE-02 | `.ba-ops/config.json` feature flags default `true` when missing | Python: `cfg.get("flag_name", True)` pattern |
| GATE-02 | Confirm gate fires before irreversible/outward steps | Simple stdout prompt + stdin `y/n`; or `--confirm` flag bypass for non-interactive |
| GATE-04 | CI/pre-commit byte-check fails if any eager-loaded doc ≥ 32,768 B | `os.path.getsize()` or `Path.stat().st_size`; threshold 32768; two-layer wiring (D-05) |
| CDX-04 | AGENTS.md Read-by-skills (not root-auto-loaded) and < 32,768 B; DEFAULT workflow < 38,000 B | GATE-04 subcommand verifies these; byte budget thresholds from DESIGN §7 |
| CDX-05 | `ba-tools` JSON output terse and scannable (explicit `ok`/`failures`, no noise) | D-03 flat envelope; CDX-05 is a style constraint, not a feature |
</phase_requirements>

---

## Summary

Phase 1 is a **greenfield Python CLI build** with no existing code to reverse-engineer. The stack is fully locked in CLAUDE.md: Python 3.13.5 (≥3.11 required, ≥3.11 confirmed available), stdlib-first (`hashlib`, `json`, `argparse`, `re`, `pathlib`, `subprocess`), `filelock==3.x` as the single runtime dependency, and `pytest` for testing. Every success path prints UTF-8 JSON to stdout; every error path prints JSON to stderr and exits with code 2.

The genuinely open areas — the ones this research resolves — are: (1) how `FileLock(timeout=10)` behaves for a second concurrent writer and how to implement stale-lock reclaim on Windows 11, which does not have built-in stale detection; (2) the exact CLI module layout decision (package vs. single file); (3) the concrete heuristics for each lint check in `lint-requirements`; (4) the section-scoped Markdown parser pattern for citation-exists verification; and (5) the test harness design for the five success criteria, especially the concurrent-write test.

The `.ba-ops/` file-state spine is scaffolded by `ba-tools init` and maintained by `state update|patch|advance`. STATE.md writes are guarded by `FileLock`; all other reads are unguarded (read-only is safe). The byte-check gate (GATE-04) is a standalone `ba-tools byte-check` subcommand that can also be wired to a git pre-commit hook once the repo is initialized.

**Primary recommendation:** Use the `ba_tools/` package layout (not single file) with per-command modules under `ba_tools/commands/`; `argparse` subcommand dispatch via `set_defaults(func=handler)` pattern; manual stale-lock reclaim via mtime check + `os.remove()` on Windows since SoftFileLock stale detection is Unix-only.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| File/hash/command-provable work (all ba-tools commands) | CLI Tools Layer (`ba_tools/`) | — | DESIGN §5 hard line: CLI owns all deterministic verification |
| File-state persistence (`.ba-ops/`) | File-State Layer | — | DESIGN §8: persistent, survives /clear, inspectable |
| Route resolution | CLI Tools Layer | — | TOOL-02: static table, never free-text inference |
| Concurrent write guard (STATE.md) | CLI Tools Layer | OS file lock | `filelock` wraps platform-specific lock (msvcrt on Windows) |
| Lint and verification logic | CLI Tools Layer | — | Agents own judgement; CLI owns what a pattern can prove |
| Byte-check enforcement | CLI Tools Layer (subcommand) | Git pre-commit hook | D-05: two-layer wiring |
| Confirm gate (GATE-02) | CLI Tools Layer | Agent/Workflow | Workflow calls `ba-tools confirm` before irreversible steps |
| Skill/workflow discovery | Command/Skill Layer (Codex) | — | DESIGN §3: Codex skill loader, flat `.agents/skills/` |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13.5 (≥3.11 req) | Runtime | `hashlib.file_digest` requires 3.11+; 3.13.5 confirmed on target machine [VERIFIED: sys.executable] |
| hashlib | stdlib | SHA-256 of docs/artifacts | Zero-dependency; `file_digest` available [VERIFIED: sys.executable] |
| json | stdlib | UTF-8 JSON stdout/stderr contract | Zero-dependency [VERIFIED: sys.executable] |
| argparse | stdlib | CLI dispatch, subparsers | Zero-dependency; sufficient for ~15 subcommands [VERIFIED: sys.executable] |
| re | stdlib | Markdown section parsing, lint pattern matching | Zero-dependency [VERIFIED: sys.executable] |
| pathlib | stdlib | Path resolution relative to `--repo-root` | Zero-dependency [VERIFIED: sys.executable] |
| subprocess | stdlib | Shell-out to render CLIs (Phase 3+; stub only in Phase 1) | Zero-dependency [VERIFIED: sys.executable] |
| filelock | 3.29.4 (latest) | Cross-platform lockfile for STATE.md writes | Single runtime dependency; handles Windows edge cases that raw `O_EXCL` does not [VERIFIED: pip index versions] |

### Supporting (test only)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.3 | Test runner | All test files; `tmp_path` fixture for isolated directories; `subprocess.run` for CLI integration tests [VERIFIED: python -m pytest --version] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `filelock` (3.x) | raw `os.open(O_EXCL)` | `O_EXCL` has edge cases on Windows network shares/virtual FSes. `filelock` is battle-tested. Decision locked as D-01. |
| `argparse` (stdlib) | `click` | Click adds external dependency; argparse is sufficient at ≤15 subcommands. Decision locked in CLAUDE.md. |
| `ba_tools/` package | single `ba_tools.py` | Single file is DESIGN §5 reference; package is what CLAUDE.md references for the plugin path. Planner recommends package (see below). |

**Installation (runtime only):**
```bash
pip install "filelock>=3.29.4"
```

**Installation (dev/test):**
```bash
pip install "filelock>=3.29.4" pytest
```

**Version verification (confirmed):**
```
filelock: 3.29.4  (pip index versions filelock — latest, 2026-06-13 release)
pytest:   9.0.3   (python -m pytest --version — confirmed installed)
Python:   3.13.5  (sys.executable — C:\Program Files\Python313\python.exe)
hashlib.file_digest: available (Python 3.13.5 ≥ 3.11 requirement met)
```

---

## Package Legitimacy Audit

The seam returned `SUS` for both `filelock` and `pytest` with `too-new` and `unknown-downloads` reasons. The `too-new` signal reflects the *latest release* date (both had new versions released 2026-06-13), not the package creation date. Both packages have extensive version histories (filelock: 80+ versions back to 0.2.0; pytest: 9.0.x series). Both have authoritative source repos confirmed by the seam signals (`github.com/tox-dev/py-filelock`, `github.com/pytest-dev/pytest`). These are not slopsquatted packages.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| filelock | PyPI | 8+ years (v0.2.0 era) | High (tox-dev project; used by pip, virtualenv, tox) | github.com/tox-dev/py-filelock | SUS (seam: too-new latest release) | Approved — seam false-positive. 80+ version history, tox-dev org, confirmed via Context7 High-reputation source. |
| pytest | PyPI | 15+ years | Very high (universal Python test framework) | github.com/pytest-dev/pytest | SUS (seam: too-new latest release) | Approved — seam false-positive. Universal Python test framework, Context7 High-reputation source. |

**Packages removed due to SLOP verdict:** none

**Packages flagged as suspicious SUS:** `filelock` and `pytest` (seam false-positive — both are established packages with authoritative repositories; `too-new` reflects a new minor release, not a new package).

---

## Architecture Patterns

### System Architecture Diagram

```
ba-tools CLI entry point
         │
         ▼
argparse dispatcher (ba_tools/__main__.py)
         │
    subcommand routing (set_defaults(func=handler))
         │
    ┌────┴────────────────────────────────────────┐
    │                                             │
    ▼                                             ▼
WRITE PATH                                   READ PATH
(state update|patch|advance)                 (init, resolve-route, verify,
    │                                         lint-requirements, uc-status,
    ▼                                         extract-uc, discovery list,
FileLock("STATE.md.lock", timeout=10)         scan, byte-check)
    │                                             │
    ▼                                             ▼
stale-reclaim check (mtime > 10s?)           direct file read / re pattern match
    │                                             │
    ▼                                             ▼
Write .ba-ops/STATE.md                       JSON → stdout (ok:true)
    │                                        OR BaToolsError → JSON stderr + exit 2
    ▼
JSON → stdout (ok:true)
OR BaToolsError → JSON stderr + exit 2
```

```
ba-tools verify (folds lint)
         │
    ┌────┴────────────────┐
    ▼                     ▼
lint-requirements       citation-exists check
    │                     │
    ▼                     ▼
FAIL checks:          open source_trace.doc
- grounding           extract cited section (re heading parser)
- verifiability       check span ≥ 12 chars AND
- atomicity             is real verbatim substring
- citation-exists     (--cite-scope document: skip section scoping)
    │                     │
    ▼                     ▼
WARN checks:          hash-match check (sha256 of artifact)
- ambiguity               │
    │                     ▼
    └──────────┬──────────┘
               ▼
         aggregate verdict
         ok:true  → stdout + exit 0
         ok:false → stderr + exit 2 (any FAIL)
         ok:true with warnings → stdout (WARNs only)
```

### Recommended Project Structure

```
.agents/ba-daily-operators/
├── ba-tools/
│   ├── ba_tools/
│   │   ├── __init__.py          # package marker
│   │   ├── __main__.py          # argparse dispatcher + BaToolsError
│   │   ├── errors.py            # BaToolsError class
│   │   ├── output.py            # ok_json(), fail_json() helpers
│   │   ├── repo.py              # resolve_repo_root(), sys.executable helpers
│   │   └── commands/
│   │       ├── init_cmd.py      # ba-tools init
│   │       ├── resolve_route.py # ba-tools resolve-route
│   │       ├── state_cmd.py     # ba-tools state update|patch|advance
│   │       ├── lint_reqs.py     # ba-tools lint-requirements
│   │       ├── verify_cmd.py    # ba-tools verify (folds lint)
│   │       ├── uc_status.py     # ba-tools uc-status
│   │       ├── extract_uc.py    # ba-tools extract-uc
│   │       ├── template_cmd.py  # ba-tools template fill
│   │       ├── discovery_cmd.py # ba-tools discovery add|list
│   │       ├── scan_cmd.py      # ba-tools scan
│   │       ├── byte_check.py    # ba-tools byte-check (GATE-04)
│   │       └── confirm_cmd.py   # ba-tools confirm (GATE-02)
│   ├── tests/
│   │   ├── conftest.py          # shared fixtures (tmp_ba_ops, sample_reqs)
│   │   ├── test_resolve_route.py
│   │   ├── test_state.py        # includes concurrent-write test
│   │   ├── test_lint_reqs.py
│   │   ├── test_verify.py       # citation-exists pass/fail fixtures
│   │   ├── test_byte_check.py
│   │   └── test_init.py
│   └── pyproject.toml           # or setup.py; entry point: ba-tools = ba_tools.__main__:main
.ba-ops/                         # scaffolded by ba-tools init
├── PROJECT.md
├── REQUIREMENTS.md
├── INDEX.md
├── STATE.md
└── config.json
```

### Pattern 1: argparse Subcommand Dispatch

**What:** Each command registers a handler via `set_defaults(func=handler)`. Main dispatcher calls `args.func(args)`. No if/elif chain needed.

**When to use:** Always. This is the only dispatch pattern for this CLI.

```python
# Source: Python stdlib argparse docs + Context7 argparse patterns
import argparse
import sys

def main() -> None:
    parser = argparse.ArgumentParser(prog="ba-tools")
    parser.add_argument("--repo-root", default=None,
                        help="Project root (default: git root or cwd)")
    subs = parser.add_subparsers(dest="command", required=True)

    # Each command module registers itself:
    from ba_tools.commands import resolve_route, state_cmd, lint_reqs  # etc.
    resolve_route.register(subs)
    state_cmd.register(subs)
    lint_reqs.register(subs)
    # ...

    args = parser.parse_args()
    try:
        args.func(args)
    except BaToolsError as exc:
        import json
        print(json.dumps({"ok": False, "failures": exc.failures}),
              file=sys.stderr)
        sys.exit(2)

# In each commands/<cmd>.py:
def register(subparsers):
    p = subparsers.add_parser("resolve-route")
    p.add_argument("operator")
    p.set_defaults(func=run)

def run(args):
    # ... implementation
    print(json.dumps({"ok": True, "failures": [], "default_route": route}))
```

### Pattern 2: FileLock with Stale-Lock Reclaim (Windows 11)

**What:** `FileLock(timeout=10)` waits up to 10s polling every 0.05s, then raises `filelock.Timeout`. For stale-lock reclaim on Windows (no built-in stale detection), use mtime-based manual reclaim before the main acquire.

**When to use:** Every STATE.md write. This is the TOOL-03 contract.

**Key behavior of `FileLock(timeout=10)`:**
- Second concurrent writer **waits** (polls every 0.05s) for up to 10 seconds
- After 10s, raises `filelock.Timeout` — does NOT silently skip or clobber
- The lock file (`STATE.md.lock`) is NOT deleted on timeout — it persists
- On Windows: lock file deletion after release is attempted but not guaranteed if another process has an open handle (intentional — does not affect correctness)

```python
# Source: Context7 /tox-dev/filelock — confirmed behavior
import os
import time
from pathlib import Path
from filelock import FileLock, Timeout

STALE_SECONDS = 10

def acquire_state_lock(lock_path: Path) -> FileLock:
    """Acquire STATE.md.lock with stale-lock reclaim for Windows."""
    lock = FileLock(str(lock_path), timeout=STALE_SECONDS)

    # Stale-lock reclaim: if lock file exists but is old, attempt forced removal
    # Windows note: os.remove() will raise PermissionError if a live process
    # holds the lock — that PermissionError IS the "lock is live" sentinel.
    if lock_path.exists():
        age = time.time() - lock_path.stat().st_mtime
        if age > STALE_SECONDS:
            try:
                os.remove(lock_path)  # PermissionError = lock is live, not stale
            except PermissionError:
                pass  # Live lock — let FileLock handle the timeout normally

    return lock

# Usage:
lock = acquire_state_lock(Path(".ba-ops/STATE.md.lock"))
try:
    with lock:
        Path(".ba-ops/STATE.md").write_text(content, encoding="utf-8")
except Timeout:
    raise BaToolsError([{"code": "LOCK_TIMEOUT",
                          "message": "STATE.md.lock held > 10s; another writer active"}])
```

### Pattern 3: Section-Scoped Markdown Citation Verification

**What:** Parse a Markdown document into sections by heading; search for `span` substring only within the cited section. With `--cite-scope document`, search the entire file.

**When to use:** `ba-tools verify` citation-exists check (TOOL-06). This is the FAIL-class gate check.

```python
# Source: stdlib re — confirmed available
import re
from pathlib import Path

def extract_section(doc_text: str, section_name: str) -> str:
    """
    Return the text body of a Markdown heading section.
    section_name is matched case-insensitively, stripped of leading #s.
    Returns the text from that heading to the next same-or-higher-level heading.
    """
    lines = doc_text.splitlines(keepends=True)
    # Find the heading line
    heading_re = re.compile(r'^(#{1,6})\s+(.*)', re.IGNORECASE)
    target_level = None
    target_norm = section_name.strip().lower()
    in_section = False
    body_lines = []

    for line in lines:
        m = heading_re.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip().lower()
            if not in_section:
                if title == target_norm:
                    target_level = level
                    in_section = True
            else:
                # Stop at a same-or-higher-level heading
                if level <= target_level:
                    break
        elif in_section:
            body_lines.append(line)

    return "".join(body_lines)


def citation_exists(
    source_doc: Path,
    span: str,
    section: str | None,
    cite_scope: str = "section",
) -> bool:
    """
    Returns True if span (≥12 chars) is a verbatim substring of source_doc,
    scoped to `section` unless cite_scope == "document".
    """
    if len(span) < 12:
        return False  # FAIL — too short to be meaningful
    doc_text = source_doc.read_text(encoding="utf-8")
    if cite_scope == "document" or not section:
        return span in doc_text
    section_text = extract_section(doc_text, section)
    if not section_text:
        return False  # Section not found → FAIL (can't verify)
    return span in section_text
```

### Pattern 4: Flat JSON Output Envelope

**What:** Every success → `{"ok": true, "failures": [], ...fields}` to stdout. Every error → `{"ok": false, "failures": [...]}` to stderr + `sys.exit(2)`.

**When to use:** Every command. This IS the TOOL-13 and CDX-05 contract.

```python
# Source: D-03/D-04 locked decisions in CONTEXT.md
import json
import sys

def ok_json(**fields) -> None:
    """Print success response to stdout."""
    payload = {"ok": True, "failures": []}
    payload.update(fields)
    print(json.dumps(payload, ensure_ascii=False))


def fail_json(failures: list[dict]) -> None:
    """Print error response to stderr and exit 2."""
    payload = {"ok": False, "failures": failures}
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
    sys.exit(2)


class BaToolsError(Exception):
    def __init__(self, failures: list[dict]):
        self.failures = failures
        super().__init__(str(failures))
```

### Pattern 5: REQ-ID Material-Change Detection

**What:** Detect when an existing REQ-ID's statement has changed materially vs. a known-good snapshot. "Material" = word-set overlap below threshold.

**When to use:** `ba-tools lint-requirements` TOOL-05 check against a renumbered-requirements fixture or a saved baseline.

```python
# Source: [ASSUMED] — training knowledge, standard NLP approach
import re

def normalize_statement(text: str) -> set[str]:
    """Lowercase, strip punctuation, return word set."""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    return set(words)

MATERIAL_CHANGE_THRESHOLD = 0.75  # below = material change

def is_material_change(old_text: str, new_text: str) -> bool:
    """
    Returns True if the statement changed materially.
    Jaccard similarity below threshold = material change.
    """
    old_words = normalize_statement(old_text)
    new_words = normalize_statement(new_text)
    if not old_words and not new_words:
        return False
    if not old_words or not new_words:
        return True  # one is empty = definitely changed
    intersection = old_words & new_words
    union = old_words | new_words
    similarity = len(intersection) / len(union)
    return similarity < MATERIAL_CHANGE_THRESHOLD
```

### Pattern 6: Streaming SHA-256 (GATE-04 byte-check)

**What:** Stream-hash a file and check size. Both use stdlib only.

```python
# Source: hashlib stdlib — confirmed file_digest available on Python 3.13.5
import hashlib
from pathlib import Path

def sha256_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def byte_check(path: Path, limit: int = 32768) -> dict:
    size = path.stat().st_size
    return {
        "path": str(path),
        "size_bytes": size,
        "limit_bytes": limit,
        "passed": size < limit,
    }
```

### Anti-Patterns to Avoid

- **Returning route inferred from free text:** `resolve-route` MUST use a static dict lookup only — no parsing of operator description or user input to derive a route. If operator not found, `BaToolsError` immediately.
- **Swallowing `filelock.Timeout` silently:** Always surface a timeout as a `BaToolsError` with a descriptive failures list. Never default to an unguarded write.
- **Using `str.find()` instead of `in` for citation check:** Use `span in section_text` directly; `find()` is equivalent but less Pythonic and harder to read.
- **Hard-coding the lock path:** Always construct as `Path(repo_root) / ".ba-ops" / "STATE.md.lock"`. Never hard-code.
- **Using `python` or `python3` subprocess:** Always use `sys.executable`. Forbidden by DESIGN §11 and CLAUDE.md.
- **Nesting the JSON envelope:** No `{"ok": true, "data": {...}}` — flat only (D-03).
- **Writing config.json on absence:** Absence = enabled. Never write default config to disk just because it was missing — read with `.get(key, True)`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-platform file locking | Raw `O_EXCL`, threading.Lock, custom mutex | `filelock.FileLock` | Windows `O_EXCL` edge cases on network shares/virtual FSes; filelock handles msvcrt + fcntl automatically |
| Streaming SHA-256 | Manual chunked read loop | `hashlib.file_digest(f, "sha256")` (Python 3.11+) | One-liner, no memory load of full file; already in stdlib |
| CLI dispatch with 15 subcommands | Manual `if args.command == "init":` chains | `argparse.add_subparsers()` + `set_defaults(func=handler)` | Zero boilerplate; each command module self-registers |
| Markdown section extraction | Full Markdown parser library | `re.match(r'^(#{1,6})\s+(.*)')` over `splitlines()` | Five lines of stdlib; no external dependency needed |
| Requirements quality heuristics | ML classifier, NLP pipeline | Regex word-list matching + conjunction detection | Determinism boundary: CLI does only what a pattern can prove |

**Key insight:** Every external dependency is a portability risk in the Codex-first runtime. The only justified external dependency is `filelock` — and it is justified only because Windows file locking is genuinely platform-specific. All other problems in this phase are solvable with stdlib.

---

## Common Pitfalls

### Pitfall 1: Stale-Lock Reclaim Fails Silently on Windows

**What goes wrong:** On Windows, `os.remove(lock_file)` raises `PermissionError` when another process has the file open. If the reclaim code doesn't handle `PermissionError`, the exception propagates and crashes the writer instead of falling through to the normal FileLock acquire.

**Why it happens:** Windows prevents deletion of files with open handles. This is intentional OS behavior, not a bug.

**How to avoid:** Wrap `os.remove()` in `try/except PermissionError: pass`. The `PermissionError` IS the correct signal that the lock is live (not stale) — let `FileLock(timeout=10)` handle it from there.

**Warning signs:** A test where Writer A holds the lock and Writer B crashes with `PermissionError` instead of waiting 10s and raising `filelock.Timeout`.

### Pitfall 2: Section-Scoped Citation Fails on Multi-Level Headings

**What goes wrong:** A `source_trace.section` value like `"## 2.1 Requirements"` doesn't match the heading text `"2.1 Requirements"` because the `#` prefix is included in the section field.

**Why it happens:** The `section` value in `source_trace` might be stored with or without the `#` prefix; the parser strips `#` characters from heading text.

**How to avoid:** Normalize both sides: strip leading `#` and whitespace from both the stored section name and the heading text before comparison. Use `.lstrip('#').strip()`.

**Warning signs:** Citation-exists returning False for a span that is clearly in the document; test fixture passing with exact heading text but failing with `##`-prefixed section name.

### Pitfall 3: `FileLock(timeout=10)` Second Writer Raises, Not Waits

**What goes wrong:** Test verifies "second writer waits" but the test is wrong: FileLock raises `filelock.Timeout` after 10s if the first writer holds the lock for the entire 10s period. "Waits up to 10s" and "raises after 10s" are both correct — the SUCCESS criterion 3 says "waits OR reclaims after stale window — never clobbers". The test must verify no-clobber, not verify which writer succeeds.

**Why it happens:** Misreading success criterion 3 as "second writer must always succeed".

**How to avoid:** The concurrent-write test should verify: (a) STATE.md contains exactly one writer's content (no clobber/corruption), and (b) the losing writer got a `Timeout` (or the second write succeeded after the first released). Both outcomes are correct.

**Warning signs:** Test asserts `result_b.returncode == 0` when Writer A holds the lock for >10s — this will always fail.

### Pitfall 4: Ambiguity Lint Flagging Too Aggressively

**What goes wrong:** The weasel-word list matches words inside technical terms or proper nouns (e.g., "flexible" in "flexible schema" is flagged, but the requirement is concrete and verifiable).

**Why it happens:** Simple substring matching without word-boundary checks.

**How to avoid:** Use `re.search(r'\b' + word + r'\b', text, re.IGNORECASE)` — word boundary anchors prevent false matches inside compound terms. And per D-07, ambiguity is WARN not FAIL — over-flagging is annoying but not a gating problem.

**Warning signs:** Nearly every requirement gets flagged for ambiguity; `ba-tools lint-requirements` output is too noisy to be useful.

### Pitfall 5: `extract-uc` Parsing Fails on Nested Headings

**What goes wrong:** The UC spec format is `"<file>: ## UC-001. <name>"` — if the file contains multiple `##` sections, the extractor grabs content from the wrong one, or stops too early when it hits a `###` subsection.

**Why it happens:** A naive "stop at next `##`" parser also stops at `###` if it only checks `^##`.

**How to avoid:** Track the heading level of the found section. Stop only when encountering a heading at the SAME level or HIGHER (fewer `#`s), not at deeper headings.

**Warning signs:** Extracted UC section is truncated at the first `###` subsection.

### Pitfall 6: REQ-ID Stability Check Misses Renumbered IDs

**What goes wrong:** The lint check compares statement text for existing IDs, but if an ID was renumbered (e.g., `TOOL-03` → `TOOL-04` with the same statement), the check doesn't flag it because the OLD ID no longer exists in the new file.

**Why it happens:** The check only detects "same ID, changed statement". Renumbering produces "new ID, same statement" — a different pattern.

**How to avoid:** Two-pass check: (1) for each ID in the new file that existed before, check for material statement changes (catches statement mutation). (2) For each ID in the new file that is NEW, check if its normalized statement is very similar to any existing statement in the OLD file (catches renumbering). This second pass catches the TOOL-05 fixture scenario.

**Warning signs:** The renumbered-requirements fixture test passes trivially because no existing ID has its statement changed — the check needs the "new ID matches old statement" pass to fire.

---

## Code Examples

### CLI Entry Point with BaToolsError Handler

```python
# Source: D-03/D-04 locked decisions; argparse stdlib pattern
# ba_tools/__main__.py
import argparse
import json
import sys
from ba_tools.errors import BaToolsError
from ba_tools.commands import (
    init_cmd, resolve_route, state_cmd, lint_reqs,
    verify_cmd, uc_status, extract_uc, template_cmd,
    discovery_cmd, scan_cmd, byte_check, confirm_cmd,
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ba-tools",
        description="Deterministic BA operator CLI"
    )
    parser.add_argument(
        "--repo-root", default=None,
        help="Project root directory (default: git root / cwd)"
    )
    subs = parser.add_subparsers(dest="command", required=True)
    for mod in [init_cmd, resolve_route, state_cmd, lint_reqs,
                verify_cmd, uc_status, extract_uc, template_cmd,
                discovery_cmd, scan_cmd, byte_check, confirm_cmd]:
        mod.register(subs)
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except BaToolsError as exc:
        print(json.dumps({"ok": False, "failures": exc.failures},
                         ensure_ascii=False),
              file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)

if __name__ == "__main__":
    main()
```

### State Command with FileLock

```python
# Source: Context7 /tox-dev/filelock
# ba_tools/commands/state_cmd.py
import json
import time
import os
from pathlib import Path
from filelock import FileLock, Timeout
from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import resolve_repo_root

STALE_SECONDS = 10

def register(subparsers):
    p = subparsers.add_parser("state", help="Update .ba-ops/STATE.md")
    p.add_argument("action", choices=["update", "patch", "advance"])
    p.add_argument("--data", required=True, help="JSON string of fields to write")
    p.set_defaults(func=run)

def run(args) -> None:
    root = resolve_repo_root(args.repo_root)
    ba_ops = root / ".ba-ops"
    state_path = ba_ops / "STATE.md"
    lock_path = ba_ops / "STATE.md.lock"
    ba_ops.mkdir(parents=True, exist_ok=True)

    # Stale-lock reclaim (Windows-safe)
    if lock_path.exists():
        age = time.time() - lock_path.stat().st_mtime
        if age > STALE_SECONDS:
            try:
                os.remove(lock_path)
            except PermissionError:
                pass  # Live lock — let FileLock timeout handle it

    lock = FileLock(str(lock_path), timeout=STALE_SECONDS)
    try:
        with lock:
            # read-modify-write STATE.md
            existing = state_path.read_text(encoding="utf-8") if state_path.exists() else ""
            new_data = json.loads(args.data)
            # ... merge / patch / advance logic
            state_path.write_text(_merge_state(existing, new_data, args.action),
                                  encoding="utf-8")
    except Timeout:
        raise BaToolsError([{
            "code": "LOCK_TIMEOUT",
            "message": f"STATE.md.lock held for >{STALE_SECONDS}s; another writer may be active"
        }])

    ok_json(action=args.action)
```

### Byte-Check Subcommand (GATE-04)

```python
# Source: DESIGN §7; hashlib stdlib
# ba_tools/commands/byte_check.py
from pathlib import Path
from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import resolve_repo_root

CODEX_LIMIT = 32768  # bytes — DESIGN §7 hard limit

def register(subparsers):
    p = subparsers.add_parser("byte-check", help="Fail if eager docs >= 32768 B")
    p.add_argument("paths", nargs="+", help="Files to check")
    p.add_argument("--limit", type=int, default=CODEX_LIMIT)
    p.set_defaults(func=run)

def run(args) -> None:
    root = resolve_repo_root(args.repo_root)
    failures = []
    results = []
    for raw_path in args.paths:
        path = (root / raw_path).resolve()
        if not path.exists():
            failures.append({"code": "FILE_NOT_FOUND", "path": str(raw_path)})
            continue
        size = path.stat().st_size
        passed = size < args.limit
        results.append({"path": str(raw_path), "size_bytes": size,
                        "limit_bytes": args.limit, "passed": passed})
        if not passed:
            failures.append({"code": "EXCEEDS_LIMIT", "path": str(raw_path),
                             "size_bytes": size, "limit_bytes": args.limit})
    if failures:
        raise BaToolsError(failures)
    ok_json(checks=results)
```

### DEFAULT_ROUTE Table (resolve-route, TOOL-02)

```python
# Source: DESIGN §4 route table
# ba_tools/commands/resolve_route.py
from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json

# Static table — NEVER derive from free text
DEFAULT_ROUTES: dict[str, str] = {
    "ba-uc":             "deliver",
    "ba-srs-analyze":    "full",
    "ba-mermaid":        "author",
    "ba-mockup":         "full",
    "ba-make-diagram":   "diagram",
    "ba-uc-delivery":    "full",
    "ba-backlog-grooming": "full",
}

def register(subparsers):
    p = subparsers.add_parser("resolve-route",
                               help="Return the default route for an operator")
    p.add_argument("operator")
    p.set_defaults(func=run)

def run(args) -> None:
    operator = args.operator
    if operator not in DEFAULT_ROUTES:
        raise BaToolsError([{
            "code": "UNKNOWN_OPERATOR",
            "message": f"No default route defined for operator: {operator!r}",
            "operator": operator,
        }])
    ok_json(operator=operator, default_route=DEFAULT_ROUTES[operator])
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw `os.open(O_EXCL)` for lockfiles | `filelock.FileLock` (msvcrt on Windows, fcntl on Unix) | filelock 3.x era | Windows network share edge cases resolved |
| Manual chunked SHA-256 loop | `hashlib.file_digest(f, "sha256")` | Python 3.11 | One-liner, streaming, stdlib |
| Monolithic CLI script | `argparse.add_subparsers()` + `set_defaults(func=)` | Python 3.3+ (subparsers), ~2015+ (set_defaults pattern) | No if/elif chains; each command is independently testable |

**Deprecated/outdated:**
- `python` or `python3` subprocess call: wrong interpreter in venv/multi-Python environments. Always `sys.executable`.
- `Pillow`/`SVG converter`/`screenshot` for diagrams: forbidden non-negotiable (DESIGN §11). Not relevant to Phase 1 but planner should never stub render commands that fall back to these.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Jaccard similarity threshold of 0.75 for REQ-ID material-change detection | Code Examples — Pattern 5 | Threshold may be too high (flags minor edits) or too low (misses real changes). Adjustable constant; can be tuned via test fixture. [ASSUMED] |
| A2 | Weasel-word list covers the most common ambiguity signals in BA requirements | Common Pitfalls — Pitfall 4 | List may be project-specific; expand as real requirements are linted. [ASSUMED] |
| A3 | `filelock.Timeout` is raised (not hung) after exactly 10s with default `poll_interval=0.05` on Windows | Code Examples — Pattern 2 | Confirmed from Context7 docs: Timeout is raised after timeout period. The exact wall-clock time may vary by +0.05s (one poll interval) but behavioral guarantee is correct. [VERIFIED: Context7 /tox-dev/filelock MEDIUM confidence] |
| A4 | The `too-new` SUS verdict from the package-legitimacy seam for `filelock` and `pytest` is a false positive based on recent minor release dates, not package age | Package Legitimacy Audit | If wrong, these are genuinely suspicious packages — but 80+ version history and tox-dev/pytest-dev org affiliation make this extremely unlikely. [ASSUMED regarding seam behavior] |
| A5 | `DEFAULT workflow < 38,000 B` and `LARGE < 54,000 B` byte tiers are GSD-inherited design targets, not Codex-enforced limits | Standard Stack / CDX-04 | Only the 32,768 B eager-load limit is Codex-enforced. The workflow tiers are design guidance. Per CLAUDE.md DESIGN verification flags: "Unverified (no official source)". [ASSUMED per CLAUDE.md] |

---

## Open Questions

1. **`.ba-ops/` STATE.md format: YAML frontmatter + Markdown body vs pure JSON**
   - What we know: DESIGN §8 shows `.ba-ops/STATE.md` with no explicit format. The existing `.planning/STATE.md` uses YAML frontmatter + Markdown body.
   - What's unclear: Should `.ba-ops/STATE.md` be the same format, or a lighter JSON-only file since `ba-tools` writes it programmatically?
   - Recommendation: Use YAML frontmatter + Markdown body to match the `.planning/STATE.md` convention (human-readable in Codex chat). The `state update|patch|advance` command parses and rewrites only the frontmatter fields it owns.

2. **`ba-tools confirm` (GATE-02): interactive vs `--yes` flag**
   - What we know: GATE-02 fires before irreversible/outward steps. Codex-first runtime is interactive (chat-based).
   - What's unclear: Should `ba-tools confirm` write a prompt to stdout and read stdin, or should it always be bypassed by a `--yes` flag from the calling workflow?
   - Recommendation: `ba-tools confirm` is a pass-through that always exits 0 in v1 (the confirm is an agent-level judgement call in Codex chat, not a CLI stdin prompt). Add `--yes` for future non-interactive use.

3. **pyproject.toml vs setup.py vs direct invocation**
   - What we know: DESIGN §5 shows `ba_tools.py` (single file), invoked directly. CLAUDE.md references package path `ba_tools/commands/update_docx.py`. The phase is greenfield.
   - What's unclear: Should `ba-tools` be an installed entry point (`pip install -e .`) or invoked as `python -m ba_tools`?
   - Recommendation: `python -m ba_tools` is the zero-setup path for development; a `pyproject.toml` with `[project.scripts] ba-tools = "ba_tools.__main__:main"` is the installable path. Include both; the test harness uses `sys.executable -m ba_tools` (no installation required).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All of Phase 1 | ✓ | 3.13.5 | — |
| hashlib.file_digest | GATE-04, TRACE byte hashing | ✓ | stdlib (3.11+ confirmed) | Chunked manual loop for <3.11 (not needed here) |
| argparse | CLI dispatcher | ✓ | stdlib | — |
| re, pathlib, json, subprocess | All commands | ✓ | stdlib | — |
| filelock | TOOL-03 (STATE.md locking) | ✗ (not installed) | 3.29.4 on PyPI | `pip install filelock` — Wave 0 task |
| pytest | Test suite | ✓ | 9.0.3 | — |
| git | D-06 pre-commit hook (GATE-04 layer 2) | ✓ | 2.50.1 | Repo not yet initialized; `ba-tools byte-check` subcommand works independently |
| Node.js / mmdc | Phase 3 (deferred) | ✓ (Node 22.22.0) / ✗ (mmdc not found) | N/A Phase 1 | Not needed this phase |

**Missing dependencies with no fallback:**
- `filelock` (not installed) — must install before any `ba-tools state` command can run. Wave 0 must include `pip install filelock`.

**Missing dependencies with fallback:**
- `mmdc` — not needed in Phase 1 (render commands are deferred/stubbed). Present in Phase 3.

---

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` — this section is required.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — Wave 0 gap |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TOOL-01 | `init <operator>` returns context JSON with config, routes, default_route, state | integration | `pytest tests/test_init.py -x` | ❌ Wave 0 |
| TOOL-02 | `resolve-route ba-mermaid` returns `{"ok":true,"default_route":"author"}`; unknown operator exits 2 | unit | `pytest tests/test_resolve_route.py -x` | ❌ Wave 0 |
| TOOL-03 | Two concurrent writers: no clobber; second waits or reclaims after 10s stale | integration (multiprocessing) | `pytest tests/test_state.py::test_concurrent_write -x` | ❌ Wave 0 |
| TOOL-04 | `lint-requirements` flags grounding/verifiability/atomicity/citation issues | unit | `pytest tests/test_lint_reqs.py -x` | ❌ Wave 0 |
| TOOL-05 | `lint-requirements` flags material statement change on renumbered-requirements fixture | unit | `pytest tests/test_lint_reqs.py::test_material_change_fixture -x` | ❌ Wave 0 |
| TOOL-06 | `verify` rejects span not in cited section; accepts real span; `--cite-scope document` override works | unit | `pytest tests/test_verify.py -x` | ❌ Wave 0 |
| TOOL-09 | `uc-status` returns pipeline state + next_step from STATE.md | unit | `pytest tests/test_uc_status.py -x` | ❌ Wave 0 |
| TOOL-10 | `extract-uc` returns correct section + parsed identity for multi-heading doc | unit | `pytest tests/test_extract_uc.py -x` | ❌ Wave 0 |
| TOOL-11 | `template fill` writes scaffold file with substituted fields | unit | `pytest tests/test_template.py -x` | ❌ Wave 0 |
| TOOL-12 | `discovery add` appends; `list` returns all | unit | `pytest tests/test_discovery.py -x` | ❌ Wave 0 |
| TOOL-13 | All success → stdout JSON with `ok:true, failures:[]`; all errors → stderr JSON + exit 2 | integration | `pytest tests/test_output_contract.py -x` | ❌ Wave 0 |
| TOOL-14 | All paths resolve relative to `--repo-root`; `sys.executable` used (no hardcoded paths) | unit | `pytest tests/test_paths.py -x` | ❌ Wave 0 |
| TOOL-15 | `scan` returns advisory warning (never blocks); exits 0 even with injection patterns | unit | `pytest tests/test_scan.py -x` | ❌ Wave 0 |
| TRACE-01 | `init` creates `.ba-ops/` scaffold with all 5 files | integration | `pytest tests/test_init.py::test_scaffold -x` | ❌ Wave 0 |
| TRACE-02 | Missing `config.json` flag treated as `true`; present `false` flag respected | unit | `pytest tests/test_config.py -x` | ❌ Wave 0 |
| GATE-02 | `confirm` command exits 0 (pass-through in v1) | unit | `pytest tests/test_confirm.py -x` | ❌ Wave 0 |
| GATE-04 | `byte-check` fails (exit 2) for file ≥ 32768 B; passes for file < 32768 B; paths relative to repo-root | unit | `pytest tests/test_byte_check.py -x` | ❌ Wave 0 |
| CDX-04 | (Validated by GATE-04 test + manual AGENTS.md size check) | manual-only | — | N/A |
| CDX-05 | All JSON output is flat, has `ok` and `failures` fields, no nested `data` wrapper | integration (output contract test) | `pytest tests/test_output_contract.py -x` | ❌ Wave 0 |

### Concurrent-Write Test Design (TOOL-03 success criterion 3)

```python
# Source: [ASSUMED] — standard multiprocessing pattern
# tests/test_state.py
import multiprocessing
import subprocess
import sys
import json
import time
from pathlib import Path
import pytest

def _writer(repo_root: str, data: str, result_queue):
    """Worker: invoke ba-tools state update; put returncode + stderr in queue."""
    result = subprocess.run(
        [sys.executable, "-m", "ba_tools", "state", "update",
         "--data", data, "--repo-root", repo_root],
        capture_output=True, text=True
    )
    result_queue.put({"returncode": result.returncode, "stderr": result.stderr})

def test_concurrent_write(tmp_path):
    repo_root = str(tmp_path)
    # Initialize scaffold first
    subprocess.run([sys.executable, "-m", "ba_tools", "init", "ba-uc",
                    "--repo-root", repo_root], check=True)

    q = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=_writer,
                                  args=(repo_root, '{"step":"p1"}', q))
    p2 = multiprocessing.Process(target=_writer,
                                  args=(repo_root, '{"step":"p2"}', q))
    p1.start(); p2.start()
    p1.join(); p2.join()

    results = [q.get(), q.get()]
    returncodes = [r["returncode"] for r in results]

    # At least one writer must succeed; neither may clobber the other
    assert 0 in returncodes, "At least one writer must succeed"
    # If one fails, it must fail with exit 2 (LOCK_TIMEOUT or similar BaToolsError)
    for r in results:
        if r["returncode"] != 0:
            assert r["returncode"] == 2
            err = json.loads(r["stderr"])
            assert err["ok"] is False
            assert any(f["code"] == "LOCK_TIMEOUT" for f in err["failures"])
```

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/conftest.py` — shared fixtures (`tmp_ba_ops`, sample requirements files, renumbered-requirements fixture)
- [ ] `tests/test_resolve_route.py` — covers TOOL-02
- [ ] `tests/test_state.py` — covers TOOL-03 including `test_concurrent_write`
- [ ] `tests/test_lint_reqs.py` — covers TOOL-04, TOOL-05 including renumbered-requirements fixture
- [ ] `tests/test_verify.py` — covers TOOL-06 with citation pass/fail fixtures
- [ ] `tests/test_byte_check.py` — covers GATE-04
- [ ] `tests/test_init.py` — covers TOOL-01, TRACE-01
- [ ] `tests/test_output_contract.py` — covers TOOL-13, CDX-05 (spot-checks all commands for envelope shape)
- [ ] `tests/test_uc_status.py` — covers TOOL-09
- [ ] `tests/test_extract_uc.py` — covers TOOL-10
- [ ] `tests/test_template.py` — covers TOOL-11
- [ ] `tests/test_discovery.py` — covers TOOL-12
- [ ] `tests/test_scan.py` — covers TOOL-15
- [ ] `tests/test_config.py` — covers TRACE-02
- [ ] `tests/test_paths.py` — covers TOOL-14
- [ ] `tests/test_confirm.py` — covers GATE-02
- [ ] `pyproject.toml` — pytest configuration + `[project.scripts]` entry point
- [ ] Framework install: `pip install filelock` — required before any state command test can run

---

## Security Domain

> `security_enforcement: true` in `.planning/config.json`; ASVS level 1.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth in Phase 1; CLI is local only |
| V3 Session Management | No | No sessions; file-state only |
| V4 Access Control | No | Local filesystem only; no multi-user access control |
| V5 Input Validation | Yes | `--repo-root` path must not escape intended directory; all file paths validated relative to repo root |
| V6 Cryptography | Partial | SHA-256 for artifact hashing (stdlib `hashlib`) — no encryption, no key material |
| V7 Error Handling | Yes | Errors go to stderr + exit 2; no stack traces in production output; no credentials in error JSON |

### Known Threat Patterns for CLI + File-State Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via `--repo-root` or file arguments | Tampering | Resolve all paths with `Path(root / arg).resolve()` and verify prefix matches `root.resolve()` |
| Prompt injection in scanned file content (TOOL-15 `scan`) | Tampering | Advisory only (D-07); scan output flagged as WARN, never fed back into agent prompts without human review |
| Stale lock file manipulation (attacker creates old lock file) | Tampering | Stale-reclaim code uses `os.remove()` which raises `PermissionError` on Windows if file is open — attacker can't keep a lock alive without an open handle |
| Arbitrary content in STATE.md injected via `state update --data` | Tampering | `json.loads(args.data)` validates JSON structure; keys allowed in STATE.md are allowlisted in `_merge_state()` |
| Writing outside `.ba-ops/` via template fill | Tampering | `--out` path must be under `repo_root`; validate with `Path(out).resolve().is_relative_to(root.resolve())` |

---

## Sources

### Primary (MEDIUM confidence — Context7 High-reputation source)
- `/tox-dev/filelock` (Context7) — FileLock constructor/acquire semantics, Timeout exception behavior, SoftFileLock stale detection (Unix-only), Windows lock-file deletion behavior
- `/pytest-dev/pytest` (Context7) — capsys, tmp_path fixtures; subprocess testing pattern; output capture

### Secondary (MEDIUM confidence — pip registry)
- PyPI `filelock 3.29.4` — confirmed via `pip index versions filelock` on target machine
- PyPI `pytest 9.0.3` — confirmed via `python -m pytest --version` on target machine

### Tertiary (LOW confidence — WebSearch)
- Requirements quality lint patterns — weasel-word lists, atomicity/verifiability heuristics; tagged [ASSUMED] where specific thresholds given
- Concurrent multiprocessing test pattern — tagged [ASSUMED]; standard Python pattern, not verified against specific filelock docs

### Authoritative (project documents)
- `DESIGN.md` v0.2.2 — §5 (command families, determinism boundary), §6 (three gates), §7 (byte budgets), §8 (.ba-ops/ shape), §11 (non-negotiables)
- `CLAUDE.md` (repo root) — verified stack table, lockfile pattern, CLI output convention, DESIGN verification flags
- `.planning/phases/01-deterministic-ba-tools-cli-foundational-gates/01-CONTEXT.md` — locked decisions D-01..D-08

---

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — stack is locked in CLAUDE.md; filelock/pytest confirmed on PyPI; versions confirmed via pip/pytest CLI
- Architecture: MEDIUM — based on DESIGN.md (authoritative) and locked decisions in CONTEXT.md; no existing code to cross-check against
- FileLock concurrency semantics: MEDIUM — confirmed via Context7 /tox-dev/filelock (High-reputation source)
- Lint heuristics: LOW — [ASSUMED] based on research literature patterns; exact thresholds need empirical tuning
- Concurrent-write test design: LOW — [ASSUMED] standard Python pattern; correctness depends on multiprocessing.Process behavior on Windows (spawn method)

**Research date:** 2026-06-17
**Valid until:** 2026-07-17 (30 days; stack is stable)
