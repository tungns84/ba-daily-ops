# Phase 3: ba-mermaid Diagram Operator - Pattern Map

**Mapped:** 2026-06-18
**Files analyzed:** 7 (5 new, 1 additive edit, 1 test suite — 3 new test modules)
**Analogs found:** 7 / 7

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `ba_tools/commands/mermaid_render_cmd.py` | command (CLI) | file-I/O + subprocess | `ba_tools/commands/render_cmd.py` | role-match (different render target) |
| `ba_tools/__main__.py` (EDIT — additive) | dispatcher | request-response | itself (existing `_COMMAND_MODULES`) | exact |
| `.agents/skills/ba-mermaid/SKILL.md` | skill index | N/A | `.agents/skills/ba-srs-analyze/SKILL.md` | exact |
| `.agents/skills/ba-mermaid/agents/openai.yaml` | skill config | N/A | `.agents/skills/ba-srs-analyze/agents/openai.yaml` | exact |
| `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` | thin workflow | request-response | `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` | exact (simpler routes) |
| `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md` | agent prompt | N/A | `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md` | role-match |
| `tests/test_mermaid_render_cmd.py` + `test_mermaid_author.py` + `test_mermaid_trace_index.py` | tests | N/A | `tests/test_render.py` + `tests/test_trace.py` | role-match |

**Reuse-as-is (no edits planned):** `trace_cmd.py`, `index_cmd.py`, `resolve_route.py`, `init_cmd.py`, `repo.py`, `output.py`, `errors.py`

---

## Pattern Assignments

### `ba_tools/commands/mermaid_render_cmd.py` (new command, file-I/O + subprocess)

**Analog:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/render_cmd.py`

**Imports pattern** (render_cmd.py lines 1-32):
```python
"""ba-tools mermaid-render — extract ```mermaid fence → .mmd → invoke mmdc → emit image.

Determinism boundary (D-05):
    NO import of openai, anthropic, or any model client.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

from filelock import FileLock, Timeout

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root

_LOCK_TIMEOUT = 10  # matches STATE.md convention (render_cmd.py line 34)
```

**register() pattern** (render_cmd.py lines 79-108 — adapt for mermaid-render):
```python
def register(subparsers) -> None:
    """Register the mermaid-render subcommand."""
    p = subparsers.add_parser(
        "mermaid-render",
        help="Extract ```mermaid fence from a diagram .md → write .mmd → invoke mmdc → emit image",
    )
    p.add_argument("--slug",         required=True,  help="Mermaid slug (subdirectory under .ba-ops/mermaid/)")
    p.add_argument("--artifact",     required=True,  help="Path to the diagram .md containing the ```mermaid block")
    p.add_argument("--format",       default="svg",  choices=["svg", "png"], help="Output format (default: svg)")
    p.add_argument("--mermaid-cli",  default=None,   help="Explicit path to mmdc binary (overrides env + PATH)")
    p.set_defaults(func=run)
```

**run() / path-safety pattern** (render_cmd.py lines 126-144 — slug traversal guard):
```python
def run(args) -> None:
    root = resolve_repo_root(getattr(args, "repo_root", None))
    slug = args.slug

    # T-02-03/T-02-06: slug-derived output path guarded under root
    out_dir = (root / ".ba-ops" / "mermaid" / slug).resolve()
    if not is_within_root(out_dir, root):
        raise BaToolsError([{
            "code": "PATH_TRAVERSAL",
            "slug": slug,
            "message": (
                f"--slug '{slug}' resolves outside repo root. "
                "Slugs must not contain path traversal sequences."
            ),
        }])
    out_dir.mkdir(parents=True, exist_ok=True)
    # ... fence extraction, mmdc resolution, invocation ...
    ok_json(slug=slug, mmd=str(mmd_path), image=str(image_path), argv=invocation["argv"])
```

**ok_json envelope** (render_cmd.py lines 173, 208):
```python
ok_json(slug=slug, out=str(srs_out))          # Phase-2 shape — adapt field names
ok_json(slug=slug, mmd=str(...), image=str(...), argv=[...])  # mermaid-render shape
```

**FileLock write guard** (render_cmd.py lines 54-76 — copy _guarded_write pattern):
```python
def _guarded_write(file_path: Path, content: str, lock_name: str) -> None:
    lock_path = file_path.parent / lock_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_path), timeout=_LOCK_TIMEOUT)
    try:
        with lock:
            file_path.write_text(content, encoding="utf-8")
    except Timeout:
        raise BaToolsError([{
            "code": "LOCK_TIMEOUT",
            "lock": str(lock_path),
            "message": f"{lock_name} held for >{_LOCK_TIMEOUT}s; another writer may be active.",
        }])
```

**Fence extraction + mmdc resolution** (from RESEARCH.md Patterns 1 and 2 — authoritative):
```python
_FENCE_RE = re.compile(
    r"^(?P<indent>\s{0,3})(?P<fence>`{3,})[ \t]*mermaid[ \t]*\r?\n"
    r"(?P<body>.*?)"
    r"^(?P=indent)(?P=fence)[ \t]*(?:\r?\n|$)",
    re.MULTILINE | re.DOTALL,
)

def extract_mermaid_fence(md_text: str) -> str:
    m = _FENCE_RE.search(md_text)
    if not m:
        raise BaToolsError([{"code": "NO_MERMAID_FENCE",
                              "message": "No ```mermaid fenced block found in artifact."}])
    return m.group("body")

def resolve_mmdc(cli_flag: str | None) -> list[str]:
    if cli_flag:
        return [cli_flag]
    env_cli = os.environ.get("MERMAID_CLI")
    if env_cli:
        return [env_cli]
    path_mmdc = shutil.which("mmdc")
    if path_mmdc:
        return [path_mmdc]
    npx = shutil.which("npx")
    if npx:
        return [npx, "-p", "@mermaid-js/mermaid-cli", "mmdc"]
    raise BaToolsError([{
        "code": "NO_MERMAID_CLI",
        "message": (
            "No mmdc CLI found. Tried: --mermaid-cli flag, $MERMAID_CLI env, "
            "PATH mmdc, npx -p @mermaid-js/mermaid-cli mmdc. "
            "Install with: npm install -g @mermaid-js/mermaid-cli"
        ),
    }])
```

---

### `ba_tools/__main__.py` (EDIT — additive only)

**Analog:** itself, lines 17-51

**Registration pattern to copy** (lines 17-51):
```python
# BEFORE (existing end of import block, line 33):
    index_cmd,
)

_COMMAND_MODULES = [
    ...
    index_cmd,        # last existing entry
]

# AFTER (additive — two insertion points):
from ba_tools.commands import (
    ...
    index_cmd,
    mermaid_render_cmd,   # ADD after index_cmd
)

_COMMAND_MODULES = [
    ...
    index_cmd,
    mermaid_render_cmd,   # ADD after index_cmd
]
```

No other changes. `register(subparsers)` and `run(args)` in `mermaid_render_cmd.py` handle the rest automatically.

---

### `.agents/skills/ba-mermaid/SKILL.md` (new skill index)

**Analog:** `.agents/skills/ba-srs-analyze/SKILL.md` (lines 1-14)

**Complete file pattern to copy — frontmatter + comment footer only:**
```markdown
---
name: ba-mermaid
description: >
  Turn a use case or requirement set into a Mermaid diagram authored inline as
  a ```mermaid block in a .md artifact, with YAML frontmatter req_ids citing
  the depicted REQ-IDs for traceability. Routes: author | render | full
  (default: author). No Mermaid CLI on the author route; render hard-fails
  exit 2 when mmdc is absent. Trigger phrases: "draw diagram", "create diagram",
  "mermaid diagram", "sequence diagram", "flowchart", "state diagram",
  "$ba-mermaid".
---

<!-- Workflow file: .agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md -->
<!-- No body content required — SKILL.md is a discovery index only              -->
```

Rule: `name` + `description` ONLY in YAML frontmatter (Codex enforced — no other fields).

---

### `.agents/skills/ba-mermaid/agents/openai.yaml` (new skill config)

**Analog:** `.agents/skills/ba-srs-analyze/agents/openai.yaml` (lines 1-17)

**Complete file pattern — copy nesting exactly:**
```yaml
interface:
  display_name: "BA Mermaid"
  short_description: "UC/requirement → Mermaid diagram .md with req_ids frontmatter; traceability via trace write + index update."
  default_prompt: |
    Use the ba-mermaid workflow on the given SRS slug, route `author` (default).
    Run `ba-tools resolve-route ba-mermaid` to confirm the default route.

    To start: open .agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md
    and follow the `author` route steps:
      1. Run `ba-tools resolve-route ba-mermaid` to confirm route = author.
      2. Run `ba-tools init ba-mermaid` for scaffold context.
      3. Read .ba-ops/srs/<slug>/requirements.json.
      4. Open .agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md and follow the diagrammer role.
      5. For full traceability: use route `full` (author → trace write → index update).

    Provide the SRS slug. Example: slug = order-management
policy:
  allow_implicit_invocation: false
```

Critical nesting: `interface.*` and `policy.allow_implicit_invocation` — match analog exactly (ba-srs-analyze/agents/openai.yaml lines 1-17).

---

### `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` (new thin workflow)

**Analog:** `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md`

**Frontmatter pattern** (ba-srs-analyze.md lines 1-11 — copy structure):
```markdown
---
operator: ba-mermaid
default_route: author
routes:
  - author
  - render
  - full
---
```

**Header + determinism-boundary block pattern** (ba-srs-analyze.md lines 13-30):
```markdown
# ba-mermaid Workflow

Turn a use case or requirement into a Mermaid diagram authored as an inline
` ```mermaid ` block in `.ba-ops/mermaid/<slug>/diagram.md`, with YAML
frontmatter `req_ids` citing the depicted REQ-IDs.

**Determinism boundary:** `ba-tools` commands do ONLY file/command/hash-provable
work. All diagram-type selection, REQ-ID subset selection, and diagram authoring
is agent-owned. The CLI never calls an LLM.

**Pass paths, not content:** The workflow hands the agent the slug and
`requirements.json` path. The agent reads the file and writes the diagram `.md`.
```

**Route section pattern** (ba-srs-analyze.md route blocks — copy `## Route:` heading + Steps list):

`author` route (no CLI, no trace):
```markdown
## Route: author

Write the inline ` ```mermaid ` diagram `.md` artifact only. No CLI invocation, no trace write.

**Steps:**
1. Run `ba-tools resolve-route ba-mermaid` to confirm default route = `author`.
2. Run `ba-tools init ba-mermaid` for scaffold context.
3. Open `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md` and follow the diagrammer role contract.
4. Pass this payload (paths only):
   ```
   requirements_json: .ba-ops/srs/<slug>/requirements.json
   slug:              <slug>
   diagram_type:      <optional --diagram-type override, or agent-chosen>
   route:             author
   ```
5. The diagrammer writes `.ba-ops/mermaid/<slug>/diagram.md` with YAML frontmatter + inline ` ```mermaid ` block.

**Output:** `.ba-ops/mermaid/<slug>/diagram.md`
```

`full` route (author → trace write → index update):
```markdown
## Route: full

End-to-end: author → trace write → index update.

**Steps:**
### Step 1 — Author diagram
Follow the **author route** steps above.

### Step 2 — Trace write
Read the `req_ids:` list from the YAML frontmatter of `.ba-ops/mermaid/<slug>/diagram.md`.
Run:
```
ba-tools trace write \
  --kind mermaid \
  --slug <slug> \
  --artifact .ba-ops/mermaid/<slug>/diagram.md \
  --source-doc .ba-ops/srs/<slug>/requirements.json \
  --requirements .ba-ops/srs/<slug>/requirements.json \
  --req-ids <comma-separated req_ids from frontmatter>
```

### Step 3 — Index update
Run `ba-tools index update`
(populates INDEX.md mermaid column; flags orphans if any REQ-ID from trace is absent from requirements.json).

**Output:** `diagram.md` + trace record `.ba-ops/traces/mermaid-<slug>.json` + updated `INDEX.md`
```

`render` route (opt-in mmdc export):
```markdown
## Route: render

Export-only: run `ba-tools mermaid-render` from an existing `diagram.md`.
Never auto-invoked by `author` or `full`. Hard-fails exit 2 when `mmdc` is absent.

**Steps:**
1. Confirm `.ba-ops/mermaid/<slug>/diagram.md` exists (author route must have run first).
2. Run:
   ```
   ba-tools mermaid-render --slug <slug> \
     --artifact .ba-ops/mermaid/<slug>/diagram.md \
     --format svg
   ```
3. On exit 2 with `NO_MERMAID_CLI`: install `mmdc` (`npm install -g @mermaid-js/mermaid-cli`)
   and retry. Do NOT generate a synthetic image.

**Output:** `.ba-ops/mermaid/<slug>/diagram.mmd` + `diagram.svg` (or `.png`)
```

---

### `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md` (new agent prompt)

**Analog:** `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md`

**Role header + determinism-boundary pattern** (ba-srs-writer.md lines 1-9):
```markdown
# ba-diagrammer Agent Role

**Role:** Diagram-authoring agent. Read the SRS `requirements.json`, select the
REQ-ID subset the diagram depicts, choose the fitting Mermaid type, and write
the diagram `.md` artifact.

**Determinism boundary:** You author and judge. `ba-tools` handles all
file/hash/CLI-provable work. You NEVER call an LLM sub-service, shell out to
`mmdc`, or invoke any CLI render tool. You READ source files and WRITE Markdown.
```

**Inputs block pattern** (ba-srs-writer.md lines 11-22 — "paths only"):
```markdown
## Inputs (paths only — no raw content forwarded)

You receive this payload:
```
requirements_json: .ba-ops/srs/<slug>/requirements.json
slug:              <slug>
diagram_type:      <optional override — agent chooses if absent>
route:             <author | full>
```
Read `requirements_json` yourself. No content is forwarded to you — only paths.
```

**Output section pattern** (ba-srs-writer.md lines 28-48 — adapt for diagram.md):
```markdown
## Output: diagram.md

Write to `.ba-ops/mermaid/<slug>/diagram.md`.

**Schema:**
```markdown
---
req_ids: [FR-001, FR-002]
diagram_type: flowchart
slug: <slug>
---

# <Title derived from slug/UC>

```mermaid
<diagram body — the selected Mermaid type>
```
```

**Field rules:**

| Field | Rule |
|-------|------|
| `req_ids` | List of REQ-IDs (from `requirements.json`) that this diagram depicts. Agent-chosen subset — never invent IDs. |
| `diagram_type` | One of: `flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `erDiagram`, `classDiagram`. Match the shape of the UC/requirement. |
| `slug` | The slug passed in — copy verbatim. |
```

**Diagram-type selection guidance** (Claude's Discretion — agent prompt body):
```markdown
## Diagram type selection

Choose the fitting type from the UC/requirement shape:

| Shape | Mermaid type |
|-------|-------------|
| Step-by-step user flow / decision tree | `flowchart` (default) |
| Actor interactions over time / API calls | `sequenceDiagram` |
| Object lifecycle / status transitions | `stateDiagram-v2` |
| Data model / entity relationships | `erDiagram` |
| System components / inheritance | `classDiagram` |

If `--diagram-type` is provided in the payload, use it without override.
```

**req_ids discipline rule** (critical — mirrors ba-srs-writer verbatim-span discipline):
```markdown
## req_ids discipline

The `req_ids` list is the single human-visible claim of what this diagram depicts.

- Read all IDs from `requirements.json`. Select only those the diagram actually depicts.
- Do NOT invent REQ-IDs not present in `requirements.json`. Any unknown ID surfaces as
  an orphan in `INDEX.md` (D-05 orphan detection via `ba-tools index update`).
- A single diagram rarely spans every requirement. Pick the focused subset.
```

---

### Test modules (3 new files) — analog: `tests/test_render.py`

**Analog confirmed:** `tests/test_render.py` (subprocess-based CLI tests with `tmp_path`, `sys.executable`, path-traversal guards)

**Test module header + import pattern** (test_render.py lines 1-23):
```python
"""Tests for mermaid_render_cmd.py (Phase 3, MMD-03 + success criterion 3).

Tests cover:
  - Fence extraction: valid block → body, absent block → NO_MERMAID_FENCE exit 2
  - mmdc resolution: NO_MERMAID_CLI hard-fail when all sources absent (patch shutil.which)
  - PATH_TRAVERSAL guard on --slug
  - Success path: mock mmdc, assert .mmd written + ok_json stdout
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PYTHON = sys.executable
```

**Subprocess CLI invocation pattern** (test_render.py lines 26-43):
```python
def _run(args: list[str], cwd=None, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, "-m", "ba_tools"] + args,
        capture_output=True, text=True, cwd=cwd, env=env,
    )
```

**tmp_path fixture + repo-root pattern** (test_render.py implicit — copy from test_render.py structure):
```python
def _make_repo(tmp_path: Path) -> Path:
    """Minimal repo layout for mermaid-render tests."""
    mermaid_dir = tmp_path / ".ba-ops" / "mermaid" / "test-slug"
    mermaid_dir.mkdir(parents=True, exist_ok=True)
    diagram_md = mermaid_dir / "diagram.md"
    diagram_md.write_text(
        "---\nreq_ids: [FR-001]\n---\n\n```mermaid\nflowchart TD\n  A-->B\n```\n",
        encoding="utf-8",
    )
    return tmp_path
```

**Exit-2 assertion pattern** (test_render.py hard-fail checks):
```python
def test_no_cli_hard_fail(tmp_path):
    """Criterion 3: mermaid-render exits 2 with NO_MERMAID_CLI; no output files written."""
    repo = _make_repo(tmp_path)
    with patch("shutil.which", return_value=None):
        result = _run(
            ["mermaid-render", "--slug", "test-slug",
             "--artifact", str(repo / ".ba-ops/mermaid/test-slug/diagram.md")],
            cwd=str(repo),
        )
    assert result.returncode == 2
    err = json.loads(result.stderr)
    assert err["ok"] is False
    codes = [f["code"] for f in err["failures"]]
    assert "NO_MERMAID_CLI" in codes
    # No output files
    assert not (repo / ".ba-ops/mermaid/test-slug/diagram.mmd").exists()
    assert not (repo / ".ba-ops/mermaid/test-slug/diagram.svg").exists()
```

---

## Shared Patterns

### BaToolsError / exit-2 hard-fail
**Source:** `.agents/ba-daily-operators/ba-tools/ba_tools/errors.py`
**Apply to:** `mermaid_render_cmd.py` — all failure paths
```python
from ba_tools.errors import BaToolsError
# Usage: raise BaToolsError([{"code": "NO_MERMAID_CLI", "message": "..."}])
# Dispatcher in __main__.py prints {"ok": false, "failures": [...]} to stderr; exits 2
```

### ok_json envelope
**Source:** `.agents/ba-daily-operators/ba-tools/ba_tools/output.py`
**Apply to:** `mermaid_render_cmd.py` success path
```python
from ba_tools.output import ok_json
ok_json(slug=slug, mmd=str(mmd_path), image=str(image_path), argv=argv)
# Prints {"ok": true, "slug": ..., "mmd": ..., "image": ..., "argv": [...]} to stdout
```

### Path-traversal guard
**Source:** `.agents/ba-daily-operators/ba-tools/ba_tools/repo.py` + `render_cmd.py` lines 135-144
**Apply to:** `mermaid_render_cmd.py` — slug-derived output path + artifact input path
```python
from ba_tools.repo import is_within_root, resolve_repo_root
root = resolve_repo_root(getattr(args, "repo_root", None))
out_dir = (root / ".ba-ops" / "mermaid" / slug).resolve()
if not is_within_root(out_dir, root):
    raise BaToolsError([{"code": "PATH_TRAVERSAL", "slug": slug, "message": "..."}])
```

### FileLock write guard
**Source:** `render_cmd.py` `_guarded_write()`, lines 54-76
**Apply to:** `mermaid_render_cmd.py` — `.mmd` file write
```python
from filelock import FileLock, Timeout
_LOCK_TIMEOUT = 10
lock = FileLock(str(lock_path), timeout=_LOCK_TIMEOUT)
try:
    with lock:
        file_path.write_text(content, encoding="utf-8")
except Timeout:
    raise BaToolsError([{"code": "LOCK_TIMEOUT", ...}])
```

### Determinism-boundary comment block
**Source:** `render_cmd.py` lines 1-20 (module docstring)
**Apply to:** `mermaid_render_cmd.py` module docstring
```
Determinism boundary (D-05):
    NO import of openai, anthropic, or any model client.
```

---

## No Analog Found

All files have close analogs. No entries in this section.

---

## Reuse-As-Is (consume, no edit)

These files already support Phase 3 — no modifications planned:

| File | Confirmed State |
|------|----------------|
| `ba_tools/commands/trace_cmd.py` | `--kind mermaid` + `--req-ids` already accepted |
| `ba_tools/commands/index_cmd.py` | mermaid column population + orphan detection already wired |
| `ba_tools/commands/resolve_route.py` | `"ba-mermaid": "author"` already in `DEFAULT_ROUTES` |
| `ba_tools/commands/init_cmd.py` | `"ba-mermaid": ["author", "render", "full"]` already in `OPERATOR_ROUTES` |
| `ba_tools/repo.py` | `resolve_under_root` / `is_within_root` — import and call |
| `ba_tools/output.py` | `ok_json` — import and call |
| `ba_tools/errors.py` | `BaToolsError` — import and call |

---

## Metadata

**Analog search scope:** `.agents/ba-daily-operators/ba-tools/`, `.agents/skills/ba-srs-analyze/`, `.agents/ba-daily-operators/ba-core/`
**Files read:** `render_cmd.py`, `__main__.py`, `ba-srs-analyze/SKILL.md`, `ba-srs-analyze/agents/openai.yaml`, `ba-srs-analyze.md` (workflow), `ba-srs-writer.md`, `test_render.py` (shape only)
**Pattern extraction date:** 2026-06-18
