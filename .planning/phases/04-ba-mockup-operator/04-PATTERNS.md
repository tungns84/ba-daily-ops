# Phase 4: ba-mockup Operator — Pattern Map

**Mapped:** 2026-06-18
**Files analyzed:** 9 new files + 2 reuse-as-is
**Analogs found:** 9 / 9

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.agents/skills/ba-mockup/SKILL.md` | skill/config | request-response | `.agents/skills/ba-mermaid/SKILL.md` | exact |
| `.agents/skills/ba-mockup/agents/openai.yaml` | config | request-response | `.agents/skills/ba-mermaid/agents/openai.yaml` | exact |
| `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` | workflow/orchestrator | request-response | `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` | exact |
| `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` | agent-prompt | request-response | `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md` | exact |
| `tests/test_mockup_author.py` | test | request-response | `.agents/ba-daily-operators/ba-tools/tests/test_mermaid_author.py` | exact |
| `tests/test_mockup_trace_index.py` | test | CRUD/integration | `.agents/ba-daily-operators/ba-tools/tests/test_mermaid_trace_index.py` | exact |
| `tests/fixtures/mockup/authored_html.html` | test fixture | — | `tests/fixtures/mermaid/authored_diagram.md` | role-match |
| `tests/fixtures/mockup/authored_wireframe.md` | test fixture | — | `tests/fixtures/mermaid/authored_diagram.md` | exact |
| `tests/fixtures/mockup/mockup_requirements.json` | test fixture | — | `tests/fixtures/mermaid/index_requirements.json` | exact |

**Reuse as-is (no new file):**
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/trace_cmd.py` — accepts `--kind mockup` + `--req-ids`; no changes
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/index_cmd.py` — Mockup column already rendered; no changes

---

## Pattern Assignments

### `.agents/skills/ba-mockup/SKILL.md` (skill/config, request-response)

**Analog:** `.agents/skills/ba-mermaid/SKILL.md`

**Full analog** (lines 1–15):
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

**What to change for mockup (copy above, replace exactly these lines):**

| Line | Mermaid value | Mockup value |
|------|--------------|--------------|
| `name:` | `ba-mermaid` | `ba-mockup` |
| `description:` block | mermaid-specific text | See canonical below |
| Workflow comment | `ba-mermaid.md` | `ba-mockup.md` |

**Canonical mockup description block:**
```yaml
description: >
  Turn requirements into a UI mockup at a required --fidelity of html or wireframe.
  html fidelity writes a self-contained static .html file (inline CSS, no framework).
  wireframe fidelity writes markdown-structural blocks in a .md (headings + lists + tables).
  Each screen carries req_ids citing the REQ-IDs it realizes for traceability.
  Routes: screen | full (default: full). Fidelity is required — rejects missing/invalid.
  Trigger phrases: "create mockup", "ui mockup", "wireframe", "html mockup",
  "screen mockup", "$ba-mockup".
```

**CDX contract enforced:** frontmatter has ONLY `name` + `description` — no extra fields.

---

### `.agents/skills/ba-mockup/agents/openai.yaml` (config, request-response)

**Analog:** `.agents/skills/ba-mermaid/agents/openai.yaml`

**Full analog** (lines 1–19):
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

**What to change for mockup:**

| Field | Mermaid value | Mockup value |
|-------|--------------|--------------|
| `display_name` | `"BA Mermaid"` | `"BA Mockup"` |
| `short_description` | mermaid text | `"Requirements → UI mockup .html or wireframe .md; req_ids traceability via trace write + index update."` |
| `default_prompt` route ref | `ba-mermaid` / `author` | `ba-mockup` / `full` |
| agent ref in step 4 | `ba-diagrammer.md` | `ba-mockup-author.md` |
| fidelity instruction | absent | add step 2: `Validate --fidelity (required: html or wireframe).` |
| `allow_implicit_invocation` | `false` | `false` (keep) |

**Nesting structure is mandatory:** `interface:` and `policy:` are top-level keys; `allow_implicit_invocation` is nested under `policy:`, not flat.

---

### `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` (workflow/orchestrator, request-response)

**Analog:** `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md`

**Frontmatter pattern** (lines 1–8):
```yaml
---
operator: ba-mermaid
default_route: author
routes:
  - author
  - render
  - full
---
```

**Change for mockup:**
```yaml
---
operator: ba-mockup
default_route: full
routes:
  - screen
  - full
---
```

**Preamble pattern** (lines 10–26) — copy verbatim, change operator name:
```markdown
**Determinism boundary:** `ba-tools` commands do ONLY file/command/hash-provable
work. All [...] is agent-owned. The CLI never calls an LLM.

**Sequential execution:** This is a Codex v1 operator — there is no autonomous
parallel subagent spawn. Each step runs sequentially; each step must complete
before the next begins.

**Pass paths, not content:** The workflow hands the agent the slug and
`requirements.json` path. The agent reads the file and writes the [...] `.md`.
```

**Route: author pattern** (lines 29–49 of ba-mermaid.md) — template for Route: screen:
```markdown
## Route: screen

Write the artifact only. No CLI invocation, no trace write.

**Steps:**

1. Run `ba-tools resolve-route ba-mockup` to confirm default route = `full`.
2. Validate `--fidelity`: must be `html` or `wireframe`. If absent or invalid, stop with error message.
3. Run `ba-tools init ba-mockup` for scaffold context.
4. Open `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` and follow
   the author role contract.
5. Pass this payload (paths only):
   ```
   requirements_json: .ba-ops/srs/<slug>/requirements.json
   slug:              <slug>
   fidelity:          <html|wireframe>
   screen_name:       <chosen by agent from UC/requirement context>
   route:             screen
   ```
6. Agent writes `.ba-ops/mockup/<slug>/<screen-name>.html` (html) or
              `.ba-ops/mockup/<slug>/<screen-name>.md` (wireframe).

**Output:** `.ba-ops/mockup/<slug>/<screen-name>.<ext>`
```

**Key difference from mermaid author route:** step 2 (fidelity gate) is ADDED; there is no render route at all.

**Route: full pattern** (lines 53–88 of ba-mermaid.md) — template for Route: full:

Step 1 reference:
```markdown
### Step 1 — Author screen
Follow the **screen route** steps above (steps 1–6).
```

Step 2 — req_ids extraction (replaces mermaid's single frontmatter read):
```markdown
### Step 2 — Extract req_ids

Read the authored artifact.

- **html fidelity:** First line of the file contains `<!-- req_ids: [FR-001, FR-002] -->`.
  Extract the bracketed list, split on `,`, strip whitespace.
- **wireframe fidelity:** YAML frontmatter (between `---` delimiters) contains `req_ids: [FR-001, FR-002]`.
  Extract the bracketed list, split on `,`, strip whitespace.
```

Step 3 — trace write command (copy mermaid Step 2, change `--kind mermaid` → `--kind mockup`, path `mermaid/` → `mockup/`):
```
ba-tools trace write \
  --kind mockup \
  --slug <slug> \
  --artifact .ba-ops/mockup/<slug>/<screen-name>.<ext> \
  --source-doc .ba-ops/srs/<slug>/requirements.json \
  --requirements .ba-ops/srs/<slug>/requirements.json \
  --req-ids <comma-separated req_ids from Step 2>
```

Note (copy verbatim from mermaid, update artifact reference):
```
Note: `--source-doc` is the SRS `requirements.json` — NOT the mockup artifact itself.
This records `source_hash` = SHA-256 of the requirements current when the screen was
authored, enabling drift detection.
```

Step 4 — index update (identical to mermaid Step 3):
```
Run `ba-tools index update`
```

**What is NOT in this workflow (vs mermaid):**
- No `## Route: render` section at all — mockup has no render route (D-05, DESIGN §11)
- No `mmdc` or `mermaid-render` references anywhere

---

### `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` (agent-prompt, request-response)

**Analog:** `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md`

**Header pattern** (lines 1–12):
```markdown
# ba-diagrammer Agent Role

**Role:** Diagram-authoring agent. Read the SRS `requirements.json`, select the
REQ-ID subset the diagram depicts, choose the fitting Mermaid type, and write
the diagram `.md` artifact.

**Determinism boundary:** You author and judge. `ba-tools` handles all
file/hash/CLI-provable work. You NEVER call an LLM sub-service, shell out to
`mmdc`, or invoke any CLI render tool. You READ source files and WRITE Markdown.
```

**Change for mockup-author:**
```markdown
# ba-mockup-author Agent Role

**Role:** Mockup-authoring agent. Read the SRS `requirements.json`, select the
REQ-ID subset the screen realizes, and write either a self-contained `.html` or
a wireframe `.md` artifact depending on `--fidelity`.

**Determinism boundary:** You author and judge. `ba-tools` handles all
file/hash/CLI-provable work. You NEVER call an LLM sub-service or any external
tool. You READ source files and WRITE the mockup artifact.
```

**Inputs payload pattern** (lines 14–24 of ba-diagrammer.md):
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

**Change for mockup-author** — replace `diagram_type` with `fidelity` + `screen_name`:
```
requirements_json: .ba-ops/srs/<slug>/requirements.json
slug:              <slug>
fidelity:          <html|wireframe>
screen_name:       <chosen by you from the UC/requirement context>
route:             <screen | full>
```

**Output section pattern** (lines 26–46 of ba-diagrammer.md):
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
<diagram body>
```
```
```

**Replace entirely with fidelity-branched output section:**

```markdown
## Output: fidelity-determined artifact

### If fidelity = html

Write to `.ba-ops/mockup/<slug>/<screen-name>.html`

**First line MUST be:** `<!-- req_ids: [FR-001, FR-002] -->`
Then: `<!DOCTYPE html>` ... self-contained HTML with inline `<style>`. No `<script>`, no external `src=`/`href=`.

### If fidelity = wireframe

Write to `.ba-ops/mockup/<slug>/<screen-name>.md`

**YAML frontmatter MUST include:** `req_ids: [FR-001, FR-002]`, `fidelity: wireframe`, `slug:`, `screen:`
Then: headings + lists + tables describing layout regions. No ASCII box-drawing characters.
```

**req_ids discipline section** (lines 72–86 of ba-diagrammer.md) — copy verbatim, update orphan reference:
```markdown
## req_ids discipline

The `req_ids` list is the single human-visible claim of what this screen realizes.

- Read all IDs from `requirements.json`. Select only those the screen actually realizes.
- Do NOT invent REQ-IDs not present in `requirements.json`. Any unknown ID surfaces as
  an orphan in `INDEX.md` (D-06 orphan detection via `ba-tools index update`).
- A single screen rarely realizes every requirement. Pick the focused subset.
- If the payload includes an explicit subset (e.g. `--req-ids FR-001,FR-002`), honor
  it exactly — do not add or remove IDs.
```

**Sections to DROP** (mermaid-specific, no mockup equivalent):
- `## Diagram type selection` (flowchart/sequenceDiagram/etc.)
- `## Mermaid syntax guidelines`

**Sections to ADD** (mockup-specific):
- HTML scaffold rules (D-03): inline CSS only, semantic elements, no `<script>`, no external URLs
- Wireframe layout rules (D-04): headings + lists + tables, no ASCII box-drawing
- Pitfall callout: req_ids HTML comment MUST be first line (before `<!DOCTYPE html>`)

---

### `tests/test_mockup_author.py` (test, request-response)

**Analog:** `.agents/ba-daily-operators/ba-tools/tests/test_mermaid_author.py`

**Path constants pattern** (lines 18–25):
```python
_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent  # 5 levels up = repo root
_FIXTURE = (
    Path(__file__).parent / "fixtures" / "mermaid" / "authored_diagram.md"
)
_WORKFLOW_PATH = (
    _REPO_ROOT / ".agents" / "ba-daily-operators" / "ba-core" / "workflows" / "ba-mermaid.md"
)
```

**Change for mockup:**
```python
_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent  # 5 levels up = repo root
_FIXTURE_HTML = Path(__file__).parent / "fixtures" / "mockup" / "authored_html.html"
_FIXTURE_WF   = Path(__file__).parent / "fixtures" / "mockup" / "authored_wireframe.md"
_WORKFLOW_PATH = (
    _REPO_ROOT / ".agents" / "ba-daily-operators" / "ba-core" / "workflows" / "ba-mockup.md"
)
```

**Frontmatter scan pattern** (lines 44–83) — reuse for wireframe fixture test:
```python
in_frontmatter = False
req_ids_found = False
req_ids_value = ""
for line in lines:
    stripped = line.strip()
    if stripped == "---":
        if not in_frontmatter:
            in_frontmatter = True
            continue
        else:
            break
    if in_frontmatter and stripped.startswith("req_ids:"):
        req_ids_found = True
        req_ids_value = stripped[len("req_ids:"):].strip()
        break
```

**Route section slice pattern** (lines 120–141) — reuse for `## Route: screen` slice:
```python
screen_start = None
screen_end = len(lines)
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == "## Route: screen":
        screen_start = i
        continue
    if screen_start is not None and stripped.startswith("## Route:") and i > screen_start:
        screen_end = i
        break
screen_section = "\n".join(lines[screen_start:screen_end])
```

**New tests to write (no mermaid equivalent — mockup-specific):**

`test_html_artifact_has_req_ids_comment`: `_FIXTURE_HTML` first line matches `<!-- req_ids: [...] -->`, list non-empty.

```python
def test_html_artifact_has_req_ids_comment():
    text = _FIXTURE_HTML.read_text(encoding="utf-8")
    first_line = text.splitlines()[0]
    import re
    m = re.match(r'<!--\s*req_ids:\s*\[([^\]]*)\]\s*-->', first_line)
    assert m, f"First line must be HTML req_ids comment; got: {first_line!r}"
    items = [x.strip() for x in m.group(1).split(",") if x.strip()]
    assert items, "req_ids comment must list at least one ID"
```

`test_html_artifact_has_doctype`: second line (or body) contains `<!DOCTYPE html>`.

`test_wireframe_artifact_has_frontmatter`: `_FIXTURE_WF` frontmatter has `req_ids:` non-empty inline list (use frontmatter scan pattern above).

`test_wireframe_has_no_ascii_box_drawing`: fixture body contains no `+--` pattern.

`test_screen_route_invokes_no_render_cli`: `## Route: screen` section of `ba-mockup.md` contains none of `render`, `mmdc`, `mermaid-render`, `drawio`.

`test_workflow_rejects_missing_fidelity`: `ba-mockup.md` contains the words `fidelity`, `html`, `wireframe` in the screen route preamble (text-presence assertion).

---

### `tests/test_mockup_trace_index.py` (test, CRUD/integration)

**Analog:** `.agents/ba-daily-operators/ba-tools/tests/test_mermaid_trace_index.py`

**Imports + constants pattern** (lines 1–41):
```python
import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mermaid"
_INDEX_REQS_FIXTURE = _FIXTURE_DIR / "index_requirements.json"

_MATRIX_HEADER = "| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |"
_ORPHANS_SECTION = "## Orphans"

PYTHON = sys.executable
```

**Change for mockup:**
```python
_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mockup"
_INDEX_REQS_FIXTURE = _FIXTURE_DIR / "mockup_requirements.json"

_MATRIX_HEADER = "| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |"  # same
_ORPHANS_SECTION = "## Orphans"  # same
```

**Helper functions** (lines 51–73) — copy verbatim (unchanged):
```python
def _run(*args: str, root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, "-m", "ba_tools", "--repo-root", str(root), *args],
        capture_output=True, text=True,
    )

def _read_index(root: Path) -> str:
    return (root / ".ba-ops" / "INDEX.md").read_text(encoding="utf-8")

def _orphans_body(index_md: str) -> str: ...   # copy verbatim
def _matrix_rows(index_md: str) -> list[str]: ...  # copy verbatim
```

**Fixture pattern** (lines 102–162) — `trace_index_env` pytest fixture:
```python
@pytest.fixture()
def trace_index_env(tmp_path):
    slug = "test-diagram"
    srs_dir = tmp_path / ".ba-ops" / "srs" / slug
    srs_dir.mkdir(parents=True)
    reqs_dst = srs_dir / "requirements.json"
    shutil.copy(_INDEX_REQS_FIXTURE, reqs_dst)
    source_doc = tmp_path / "source.md"
    source_doc.write_text("# Source\n...", encoding="utf-8")
    # ... artifact dir setup ...
    return {"root": tmp_path, "slug": slug, "reqs_file": reqs_dst,
            "source_doc": source_doc, "srs_artifact": srs_artifact}
```

**Change for mockup fixture:** replace mermaid artifact with a mockup `.html` file:
```python
mockup_dir = tmp_path / ".ba-ops" / "mockup" / slug
mockup_dir.mkdir(parents=True)
mockup_artifact = mockup_dir / "screen.html"
mockup_artifact.write_text(
    "<!-- req_ids: [FR-001] -->\n"
    "<!DOCTYPE html>\n<html lang='en'><head><title>Screen</title></head>"
    "<body><main><p>Test screen</p></main></body></html>\n",
    encoding="utf-8",
)
# return dict: include mockup_artifact instead of diagram_md
return {..., "mockup_artifact": mockup_artifact}
```

**`_write_srs_trace` helper** (lines 170–183) — copy verbatim (unchanged).

**`_write_mermaid_trace` pattern** (lines 186–205) — replace with `_write_mockup_trace`:
```python
def _write_mockup_trace(env, req_ids, *, force=False):
    root = env["root"]
    args = [
        "trace", "write",
        "--kind", "mockup",
        "--slug", env["slug"],
        "--artifact", str(env["mockup_artifact"]),
        "--source-doc", str(env["reqs_file"]),
        "--requirements", str(env["reqs_file"]),
        "--req-ids", req_ids,
    ]
    if force:
        args.append("--force")
    return _run(*args, root=root)
```

**Three test classes** (lines 218–398) — same class structure, replace `_write_mermaid_trace` with `_write_mockup_trace` and update docstrings:
- `TestReqIdsAppearInIndexMockupColumn` (was `...MermaidColumn`) — assert FR-001 row has `ok`, not in Orphans
- `TestNoOrphansForRealIds` — unchanged logic, `--kind mockup`
- `TestInventedIdSurfacesAsOrphan` — unchanged logic, `--kind mockup`

**`TestIndexMdStructure`** (lines 360–398) — copy verbatim (these validate `_MATRIX_HEADER` + `_ORPHANS_SECTION` match `index_cmd.py` — the same constants apply).

---

### `tests/fixtures/mockup/authored_html.html` (test fixture)

**Analog:** `tests/fixtures/mermaid/authored_diagram.md`

**What the analog provides:** a concrete hand-authored artifact that the fixture-based tests assert against.

**authored_html.html must contain:**
1. Line 1: `<!-- req_ids: [FR-001, FR-002] -->`
2. Line 2: `<!DOCTYPE html>`
3. A `<style>` block (inline CSS)
4. No `<script>` tags
5. No external `src=` or `href=` URLs

Minimal valid skeleton (from RESEARCH.md §1 HTML Scaffold Conventions):
```html
<!-- req_ids: [FR-001, FR-002] -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Login — test-slug</title>
  <style>
    body { font-family: system-ui, sans-serif; padding: 1rem; }
    .card { border: 1px solid #dee2e6; border-radius: 4px; padding: 1rem; }
    button { padding: 0.5rem 1rem; background: #0d6efd; color: #fff;
             border: none; border-radius: 4px; cursor: pointer; }
  </style>
</head>
<body>
  <header><h1>Login</h1></header>
  <main>
    <div class="card">
      <label>Username <input type="text"></label>
      <label>Password <input type="password"></label>
      <button>Sign in</button>
    </div>
  </main>
  <footer>Mockup — test-slug | req_ids: [FR-001, FR-002]</footer>
</body>
</html>
```

---

### `tests/fixtures/mockup/authored_wireframe.md` (test fixture)

**Analog:** `tests/fixtures/mermaid/authored_diagram.md` (lines 1–5 — frontmatter schema)

**authored_diagram.md frontmatter:**
```yaml
---
req_ids: [FR-001, FR-002]
diagram_type: flowchart
slug: test-slug
---
```

**authored_wireframe.md must contain:**
1. YAML frontmatter with `req_ids: [FR-001, FR-002]`, `fidelity: wireframe`, `slug:`, `screen:`
2. Headings + lists + tables describing layout regions
3. No ASCII box-drawing characters (`+--`, `│`, `─`)

Minimal valid skeleton:
```markdown
---
req_ids: [FR-001, FR-002]
fidelity: wireframe
slug: test-slug
screen: login
---

# Login

> Wireframe — req_ids: [FR-001, FR-002]

## Layout

### Header
- **Logo** [left]
- **App title** [center]

### Main Content

| Region | Type | Content |
|--------|------|---------|
| Center panel | form | Username + Password fields, Sign-in button |

### Footer
- Status info [left]
```

---

### `tests/fixtures/mockup/mockup_requirements.json` (test fixture)

**Analog:** `tests/fixtures/mermaid/index_requirements.json` (full file)

**Copy verbatim** — the schema and IDs (FR-001, FR-002) are identical. The file is kind-agnostic; `index update` reads it regardless of trace kind.

```json
{
  "requirements": [
    {
      "id": "FR-001",
      "statement": "The system shall record artifact provenance via trace records.",
      "status": "stated",
      "source_trace": {
        "doc": "source.md",
        "section": "Requirements",
        "span": "The system shall record artifact provenance via trace records."
      }
    },
    {
      "id": "FR-002",
      "statement": "The system shall detect stale artifacts via source_hash comparison.",
      "status": "stated",
      "source_trace": {
        "doc": "source.md",
        "section": "Requirements",
        "span": "The system shall detect stale artifacts via source_hash comparison."
      }
    }
  ]
}
```

---

## Reuse As-Is (no new file)

### `trace_cmd.py` — relevant signature

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/trace_cmd.py`

Key verified facts (from RESEARCH.md §Phase 3 Reuse Verification):
- `--kind` help string includes `mockup` (line 54–55)
- `BaToolsError MISSING_REQ_IDS` raised when `kind != srs` and no `--req-ids` (lines 229–236)
- `--source-doc` = source_hash semantics identical to mermaid

No changes. Call as:
```
ba-tools trace write --kind mockup --slug <slug> --artifact <path> \
  --source-doc .ba-ops/srs/<slug>/requirements.json \
  --requirements .ba-ops/srs/<slug>/requirements.json \
  --req-ids <comma-list>
```

### `index_cmd.py` — relevant signature

**File:** `.agents/ba-daily-operators/ba-tools/ba_tools/commands/index_cmd.py`

Key verified facts:
- Matrix header line 213: `"| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |"`
- Orphan detection lines 159–167: iterates all records where `kind != "srs"` — mockup records captured automatically

No changes. Call as: `ba-tools index update`

---

## Shared Patterns

### Authentication / Guards
Not applicable — no auth layer in this operator. All path safety is handled by `repo.py::resolve_under_root` in `trace_cmd.py` (reused as-is).

### Workflow Preamble (copy to all workflow files)
**Source:** `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` lines 10–26

```markdown
**Determinism boundary:** `ba-tools` commands do ONLY file/command/hash-provable
work. All [...] is agent-owned. The CLI never calls an LLM.

**Sequential execution:** This is a Codex v1 operator — there is no autonomous
parallel subagent spawn. Each step runs sequentially; each step must complete
before the next begins.

**Pass paths, not content:** The workflow hands the agent the slug and
`requirements.json` path. The agent reads the file and writes the artifact.
```

### req_ids Discipline (copy to all agent prompts)
**Source:** `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md` lines 72–86

```markdown
- Read all IDs from `requirements.json`. Select only those the artifact actually depicts.
- Do NOT invent REQ-IDs not present in `requirements.json`. Any unknown ID surfaces as
  an orphan in `INDEX.md`.
- A single artifact rarely spans every requirement. Pick the focused subset.
- If the payload includes an explicit subset, honor it exactly.
```

### Test Helper Pattern (copy to all integration test files)
**Source:** `.agents/ba-daily-operators/ba-tools/tests/test_mermaid_trace_index.py` lines 51–73

```python
PYTHON = sys.executable

def _run(*args: str, root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, "-m", "ba_tools", "--repo-root", str(root), *args],
        capture_output=True, text=True,
    )
```

### Frontmatter Scan Pattern (copy to all fixture-based tests)
**Source:** `.agents/ba-daily-operators/ba-tools/tests/test_mermaid_author.py` lines 44–61

```python
in_frontmatter = False
req_ids_found = False
req_ids_value = ""
for line in lines:
    stripped = line.strip()
    if stripped == "---":
        if not in_frontmatter:
            in_frontmatter = True
            continue
        else:
            break
    if in_frontmatter and stripped.startswith("req_ids:"):
        req_ids_found = True
        req_ids_value = stripped[len("req_ids:"):].strip()
        break
```

---

## No Analog Found

None — all 9 new files have exact or role-match analogs in the codebase.

---

## Metadata

**Analog search scope:** `.agents/skills/ba-mermaid/`, `.agents/ba-daily-operators/ba-core/`, `.agents/ba-daily-operators/ba-tools/tests/`, `tests/fixtures/mermaid/`
**Files read:** 9 analog files
**Pattern extraction date:** 2026-06-18
