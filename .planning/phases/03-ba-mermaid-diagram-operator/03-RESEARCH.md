# Phase 3: ba-mermaid Diagram Operator - Research

**Researched:** 2026-06-18
**Domain:** Mermaid diagram authoring CLI + traceability wiring
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Input is an existing SRS `--slug`; reads `.ba-ops/srs/<slug>/requirements.json`; mermaid slug ties to srs slug; artifacts under `.ba-ops/mermaid/<slug>/`.
- **D-01a:** REQ-ID subset selection is agent judgement — ba-tools never infers which reqs to depict.
- **D-02:** One diagram per invocation; agent chooses Mermaid type (flowchart/sequence/state/ER/class).
- **D-02a:** Optional `--diagram-type` flag overrides agent choice; multiple-diagrams-per-invocation is out of scope v1.
- **D-03:** Agent writes depicted REQ-IDs into `.md` YAML frontmatter (`req_ids: [FR-001, FR-002]`); thin workflow reads frontmatter → calls `ba-tools trace write --kind mermaid --slug <slug> --req-ids <list> --artifact <md> --source-doc <?>`.
- **D-03a:** No new ba-tools parser — uses existing explicit `--req-ids` flag on `trace write`; workflow does the frontmatter→flag hand-off.
- **D-04:** Routes `author` (default) / `render` / `full`. `author` = write inline ```mermaid `.md` only, no CLI, no trace. `full` = author → trace write → index update (no render). `render` = export-only from an existing `.md`, separate opt-in.
- **D-05cmd:** New `ba-tools` command (`mermaid-render`). Resolution chain: `--mermaid-cli` flag → `$MERMAID_CLI` env → PATH `mmdc` → `npx -p @mermaid-js/mermaid-cli mmdc`. No CLI resolves → `BaToolsError` exit 2. Never a synthetic image.
- **D-05fmt:** Default output SVG; `--format png|svg` override. Outputs: `.ba-ops/mermaid/<slug>/diagram.mmd` + `diagram.svg` (or `.png`).
- **D-05 (orphan):** REQ-ID validation is downstream — `index update` flags orphans. `trace write` records what it receives without validation. No change to `trace_cmd.py`.

### Claude's Discretion

- Exact agent-prompt filename + body (suggest `ba-core/agents/ba-diagrammer.md`).
- Exact `mermaid-render` subcommand name + flag spelling, and inline-block extraction implementation.
- The `--source-doc` argument shape for `trace write` when kind=mermaid.
- Skill/workflow physical file-layout reconciliation.
- `openai.yaml` `interface.*` wording + SKILL.md `description`.
- Whether `mermaid-render` reuses `render_cmd.py` dispatch or is a new module.
- Test-fixture design for the 3 success criteria.

### Deferred Ideas (OUT OF SCOPE)

- Multiple diagrams per invocation.
- Pre-validating REQ-IDs at `trace write` (block orphans at write time).
- `full` route running render.
- Formal BPMN / draw.io diagrams (`ba-make-diagram`).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MMD-01 | UC/requirement → Mermaid diagram, MD-inline first (no Mermaid CLI on default route) | Author route pattern confirmed; inline fence extraction technique documented below |
| MMD-02 | Each diagram cites `req_ids`; after `ba-tools index update` those REQ-IDs appear in INDEX.md mermaid column (no orphans introduced) | `trace write --kind mermaid` confirmed working as-is; frontmatter→flag hand-off pattern specified |
| MMD-03 | `mmdc` render optional; default route `author` has no CLI dependency; export hard-fails with `BaToolsError` exit 2 when no CLI found; never a synthetic image | Resolution chain + hard-fail implementation specified; validation test approach documented |
</phase_requirements>

---

## Summary

Phase 3 adds the `ba-mermaid` operator — the first render-capable route in the daily spine. The
author route (default) produces a `.md` artifact with an inline ` ```mermaid ` block and YAML
frontmatter carrying `req_ids`; it invokes zero external CLI. The full route chains author →
`ba-tools trace write --kind mermaid` → `ba-tools index update` to populate the INDEX.md
mermaid column. The render route shells out to `mmdc` (resolved via a 4-step chain) and
hard-fails exit 2 if none resolves.

Most of the infrastructure already exists: `resolve_route.py` already has `ba-mermaid → author`,
`init_cmd.py` already has `["author", "render", "full"]`, and `trace_cmd.py` already accepts
`--kind mermaid` with explicit `--req-ids`. The only genuinely new code is `mermaid_render_cmd.py`
and the skill/workflow/agent files that mirror the Phase-2 `ba-srs-analyze` layout.

**Primary recommendation:** Create `mermaid_render_cmd.py` as a new, independent module (not
reusing `render_cmd.py` dispatch) — different render target (mmdc image vs JSON→MD), different
I/O surface (reads `.md`, extracts fence, writes `.mmd` + image), different hard-fail contract.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Diagram type + REQ-ID subset selection | Agent (`ba-diagrammer`) | — | Judgement; determinism boundary — ba-tools never infers which reqs to depict |
| Inline ` ```mermaid ` block authoring | Agent (`ba-diagrammer`) | — | Creative/analytical output; agent writes the `.md` artifact |
| YAML frontmatter `req_ids` write | Agent (`ba-diagrammer`) | — | Part of the `.md` artifact the agent authors |
| Frontmatter parse → `--req-ids` flag hand-off | Thin workflow (`ba-mermaid.md`) | — | Orchestration step; reads frontmatter, calls ba-tools with explicit list |
| Trace record write + INDEX update | `ba-tools trace write` + `ba-tools index update` | — | File/hash-provable work; reuse Phase-2 commands as-is |
| mmdc resolution + subprocess invocation + hard-fail | `ba-tools mermaid-render` (new) | — | CLI/command/hash-provable; agents never shell out to mmdc |
| Inline fence extraction → `.mmd` file | `ba-tools mermaid-render` (new) | — | Deterministic text operation; belongs in ba-tools |
| Route resolution | `ba-tools resolve-route` | `ba-tools init` | Static table lookup already wired |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`re`, `pathlib`, `subprocess`, `json`, `argparse`) | 3.11+ | `mermaid_render_cmd.py` implementation | Zero external deps; matches determinism boundary; `[ASSUMED]` — matches existing codebase pattern |
| `filelock` | 3.x | Lockfile for any future `.mmd`/output file writes under contention | Already in project deps; `[ASSUMED]` — used in `render_cmd.py` and `trace_cmd.py` |

### Supporting
| Library | Purpose | Notes |
|---------|---------|-------|
| `@mermaid-js/mermaid-cli` (`mmdc`) | Optional render backend: `.mmd` → SVG/PNG | Node binary; NOT a Python dep; only invoked by `mermaid-render`; resolution chain avoids hard install requirement |

### Not Needed
- No `python-yaml` / `pyyaml` for frontmatter parsing — YAML frontmatter in the `.md` is parsed by the thin workflow (agent-side), which passes the explicit `--req-ids` list to ba-tools. ba-tools never touches the frontmatter.
- No Pillow, SVG converter, or screenshot — DESIGN §11 non-negotiable.

---

## Package Legitimacy Audit

> No new Python packages are introduced in this phase. All dependencies (`filelock`, stdlib) are
> already installed and verified in Phase 1/2. `mmdc` is an optional Node binary, not a Python
> package install in this phase.

| Package | Ecosystem | Verdict | Disposition |
|---------|-----------|---------|-------------|
| `filelock` | PyPI (already installed) | OK | Approved — existing dep |
| `@mermaid-js/mermaid-cli` | npm (runtime optional dep) | OK | Not installed by this phase; invoked if present |

**Packages removed due to SLOP verdict:** none
**Packages flagged as SUS:** none

---

## Architecture Patterns

### System Architecture Diagram

```
[Codex / User]
      |
      | ba-mermaid --slug <slug> [--route author|full|render] [--diagram-type X]
      v
[ba-tools init ba-mermaid]  ──→  returns {routes, default_route:"author", config, state}
      |
      |──── route=author ──────────────────────────────────────────────────────┐
      |                                                                        |
      |  [ba-diagrammer agent]                                                 |
      |    reads .ba-ops/srs/<slug>/requirements.json                          |
      |    selects REQ-ID subset (judgement)                                   |
      |    writes .ba-ops/mermaid/<slug>/diagram.md                            |
      |      (YAML frontmatter: req_ids:[...] + inline ```mermaid block)       |
      |                                                                  [DONE — author]
      |
      |──── route=full ─────────────────────────────────────────────────────┐
      |     (author step first, then:)                                      |
      |  [workflow parses frontmatter req_ids]                              |
      |      |                                                              |
      |  [ba-tools trace write]                                             |
      |    --kind mermaid --slug <slug>                                     |
      |    --artifact .ba-ops/mermaid/<slug>/diagram.md                     |
      |    --source-doc .ba-ops/srs/<slug>/requirements.json                |
      |    --requirements .ba-ops/srs/<slug>/requirements.json              |
      |    --req-ids FR-001,FR-002,...                                       |
      |    writes .ba-ops/traces/mermaid-<slug>.json                        |
      |      |                                                              |
      |  [ba-tools index update]                                            |
      |    populates INDEX.md mermaid column for <slug>                     |
      |    flags orphans (REQ-IDs in trace absent from requirements.json)   |
      |                                                              [DONE — full]
      |
      └──── route=render ──────────────────────────────────────────────────┐
        [ba-tools mermaid-render]                                          |
          --artifact .ba-ops/mermaid/<slug>/diagram.md                    |
          --format svg|png  (default: svg)                                |
          1. Extract ```mermaid fence → write diagram.mmd                 |
          2. Resolve mmdc: --mermaid-cli → $MERMAID_CLI → PATH → npx -p  |
          3. subprocess(mmdc -i diagram.mmd -o diagram.svg, capture argv) |
          4. No CLI found → BaToolsError exit 2                           |
          writes .ba-ops/mermaid/<slug>/diagram.mmd                       |
                 .ba-ops/mermaid/<slug>/diagram.svg (or .png)             |
                                                                   [DONE — render]
```

### Recommended Project Structure

New files only (everything else reused as-is):

```
.agents/
├── skills/
│   └── ba-mermaid/
│       ├── SKILL.md                        # name + description only (Codex frontmatter)
│       └── agents/
│           └── openai.yaml                 # interface.* + policy.allow_implicit_invocation
│
└── ba-daily-operators/
    ├── ba-core/
    │   ├── workflows/
    │   │   └── ba-mermaid.md               # thin per-route workflow (mirrors ba-srs-analyze.md)
    │   └── agents/
    │       └── ba-diagrammer.md            # diagram-author agent prompt
    │
    └── ba-tools/
        └── ba_tools/
            └── commands/
                └── mermaid_render_cmd.py   # NEW: inline fence extract + mmdc subprocess

# Existing files requiring ADDITIVE edits:
# ba_tools/__main__.py  — add mermaid_render_cmd import + _COMMAND_MODULES entry
# (resolve_route.py and init_cmd.py already have ba-mermaid registered — NO CHANGE NEEDED)
```

### Pattern 1: Inline Mermaid Fence Extraction

**What:** Extract a single ` ```mermaid ` fenced block from a `.md` file.
**When to use:** `mermaid-render` command before writing `.mmd`.
**Edge cases:**
- Info-string is exactly `mermaid` (case-sensitive match; do not match `mermaidjs` etc.)
- Fence may use 3+ backticks; standardize to match `^`{3,}` `mermaid`
- CRLF line endings: normalize `\r\n` → `\n` before regex
- Leading whitespace before fence marker: CONTEXT D-02a locks single block per artifact (v1), so find the FIRST match; if none found → `BaToolsError` `NO_MERMAID_FENCE`
- Indented fence (e.g. inside a blockquote): reject — standard `.md` authored by agent will not indent; match only `^\s{0,3}` opening fence per CommonMark fence rule

```python
# Source: [ASSUMED] — standard Python regex over CommonMark fence spec
import re

_FENCE_RE = re.compile(
    r"^(?P<indent>\s{0,3})(?P<fence>`{3,})[ \t]*mermaid[ \t]*\r?\n"  # opening
    r"(?P<body>.*?)"                                                    # diagram body
    r"^(?P=indent)(?P=fence)[ \t]*(?:\r?\n|$)",                       # closing (same indent+fence)
    re.MULTILINE | re.DOTALL,
)


def extract_mermaid_fence(md_text: str) -> str:
    """Return diagram body from the first ```mermaid block. Raises BaToolsError if absent."""
    m = _FENCE_RE.search(md_text)
    if not m:
        from ba_tools.errors import BaToolsError
        raise BaToolsError([{
            "code": "NO_MERMAID_FENCE",
            "message": "No ```mermaid fenced block found in artifact.",
        }])
    return m.group("body")
```

### Pattern 2: mmdc Resolution Chain + subprocess Invocation

**What:** Resolve `mmdc` binary path via 4-step priority chain; invoke with `subprocess.run`.
**Exact chain** (CLAUDE.md verified, `-p` flag required for npx):

```python
# Source: CLAUDE.md [VERIFIED] — mmdc resolution chain
import os
import shutil
import subprocess
from ba_tools.errors import BaToolsError


def resolve_mmdc(cli_flag: str | None) -> list[str]:
    """Return argv prefix to invoke mmdc, or raise BaToolsError NO_MERMAID_CLI."""
    # 1. Explicit --mermaid-cli flag
    if cli_flag:
        return [cli_flag]
    # 2. $MERMAID_CLI env var
    env_cli = os.environ.get("MERMAID_CLI")
    if env_cli:
        return [env_cli]
    # 3. PATH mmdc
    path_mmdc = shutil.which("mmdc")
    if path_mmdc:
        return [path_mmdc]
    # 4. npx fallback — -p flag REQUIRED (package name != binary name)
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


def invoke_mmdc(mmdc_argv: list[str], mmd_path: str, out_path: str) -> dict:
    """Run mmdc and return {argv, exit_code}. Raises BaToolsError on non-zero exit."""
    argv = mmdc_argv + ["-i", mmd_path, "-o", out_path]
    result = subprocess.run(argv, capture_output=True)
    if result.returncode != 0:
        raise BaToolsError([{
            "code": "MMDC_FAILED",
            "argv": argv,
            "exit_code": result.returncode,
            "stderr": result.stderr.decode("utf-8", errors="replace")[:500],
            "message": f"mmdc exited {result.returncode}.",
        }])
    return {"argv": argv, "exit_code": result.returncode}
```

### Pattern 3: trace write call for kind=mermaid

**What:** Thin workflow invokes `ba-tools trace write` after reading `req_ids` from frontmatter.
**`--source-doc` for kind=mermaid:** The source the diagram depicts is the SRS requirements
document, not the diagram `.md` itself. Pass `.ba-ops/srs/<slug>/requirements.json` as
`--source-doc`. This gives `source_hash` = SHA-256 of the requirements that were current when
the diagram was authored — exactly the drift-detection semantics D-06 intends. The diagram `.md`
goes to `--artifact`.

```
ba-tools trace write \
  --kind mermaid \
  --slug <slug> \
  --artifact .ba-ops/mermaid/<slug>/diagram.md \
  --source-doc .ba-ops/srs/<slug>/requirements.json \
  --requirements .ba-ops/srs/<slug>/requirements.json \
  --req-ids FR-001,FR-002,...
```

Note: `--source-doc` and `--requirements` point to the same file for kind=mermaid. This is
intentional — `--requirements` is used for statement-hash lookup; `--source-doc` is what gets
SHA-256'd for `source_hash`. Both are `requirements.json`. [ASSUMED] — consistent with D-06
semantics and trace_cmd.py code reading confirmed; the two args are independent in the implementation.

### Pattern 4: New command module registration in `__main__.py`

`mermaid_render_cmd.py` follows the exact same pattern as all existing command modules:

```python
# In ba_tools/__main__.py — ADDITIVE ONLY:
from ba_tools.commands import (
    # ... existing imports ...
    mermaid_render_cmd,   # ADD
)

_COMMAND_MODULES = [
    # ... existing list ...
    mermaid_render_cmd,   # ADD
]
```

The `register(subparsers)` function in `mermaid_render_cmd.py` adds the `mermaid-render`
subcommand. Subcommand name `mermaid-render` (hyphenated, matches ba-tools naming convention).

### Anti-Patterns to Avoid

- **Importing a model client in `mermaid_render_cmd.py`:** Violates determinism boundary. Zero model imports in ba-tools commands.
- **Calling `mmdc` from the agent or workflow:** Agents never shell out to render CLIs. Only ba-tools does.
- **Synthesizing an image when mmdc fails:** Any fallback to Pillow / SVG converter / screenshot is a DESIGN §11 non-negotiable violation. Hard-fail exit 2.
- **Reusing `render_cmd.py` dispatch for mermaid-render:** Different render target (image vs MD), different I/O surface, different failure modes. New module is cleaner.
- **Writing the `.mmd` to a temp directory:** All outputs must land under `.ba-ops/mermaid/<slug>/` (DESIGN §11 no hard-coded paths; use `--repo-root`).
- **Parsing YAML frontmatter in ba-tools:** ba-tools receives explicit `--req-ids` from the workflow. No YAML parsing in the CLI.
- **Using `python` or `python3` as subprocess call:** Use `sys.executable` for any Python sub-invocation (none needed here, but rule applies).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Cross-platform lockfile | `os.open(path, O_EXCL)` | `filelock.FileLock(timeout=10)` — handles Windows edge cases |
| SHA-256 file digest | custom chunked read | `ba_tools.hashing._sha256_file` — already exists, imported by trace_cmd |
| Trace record write | custom JSON writer | `ba-tools trace write --kind mermaid` — already works, no change needed |
| INDEX mermaid column population | custom index writer | `ba-tools index update` — already reads mermaid traces from D-05 records |

**Key insight:** The traceability spine was explicitly designed in Phase 2 to carry `kind=mermaid`
records. The INDEX and trace machinery needs zero modification — just invoke with the correct args.

---

## Route Registration: Confirmed State

Both `resolve_route.py` and `init_cmd.py` **already have `ba-mermaid` registered**
as of the current codebase (confirmed by reading the files). No changes required to these files.

```python
# resolve_route.py DEFAULT_ROUTES — already present [VERIFIED: codebase read]
"ba-mermaid": "author"

# init_cmd.py OPERATOR_ROUTES — already present [VERIFIED: codebase read]
"ba-mermaid": ["author", "render", "full"]
```

The planner must NOT include tasks to modify these files.

---

## Skill / Workflow / Agent File Layout

Confirmed by reading `.agents/skills/ba-srs-analyze/` structure. The layout `ba-mermaid` copies:

```
# Phase-2 ba-srs-analyze layout (confirmed by ls) [VERIFIED: codebase read]
.agents/skills/ba-srs-analyze/
├── SKILL.md               # name + description ONLY (Codex frontmatter rule)
└── agents/
    └── openai.yaml        # interface.display_name, interface.short_description,
                           # interface.default_prompt, policy.allow_implicit_invocation

.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md   # thin workflow
.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md        # agent prompt
```

`ba-mermaid` mirrors this exactly:

```
.agents/skills/ba-mermaid/
├── SKILL.md
└── agents/
    └── openai.yaml

.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md
.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md
```

SKILL.md frontmatter: `name` + `description` only — no other fields (confirmed Codex rule from CLAUDE.md).
`openai.yaml` nesting: `interface.display_name`, `interface.short_description`, `interface.default_prompt`, `policy.allow_implicit_invocation: false`.

---

## Common Pitfalls

### Pitfall 1: `npx` without `-p` flag
**What goes wrong:** `npx @mermaid-js/mermaid-cli` fails because the package name is not the same as the binary name. npx cannot resolve the binary from the package name alone without `-p`.
**Why it happens:** `mmdc` is the binary; `@mermaid-js/mermaid-cli` is the package. These differ.
**How to avoid:** Always use `npx -p @mermaid-js/mermaid-cli mmdc` (CLAUDE.md verified).
**Warning signs:** `npx` call hangs or prints "command not found: @mermaid-js/mermaid-cli".

### Pitfall 2: Forgetting CRLF normalization in fence extraction
**What goes wrong:** Regex fails to match the closing fence on Windows where files use CRLF.
**Why it happens:** `re.MULTILINE` anchors match `\n`; `\r\n` leaves `\r` on the end of fence lines.
**How to avoid:** `text = md_text.replace('\r\n', '\n')` before regex; or use `\r?\n` in pattern (shown in Pattern 1).

### Pitfall 3: Passing the diagram `.md` as `--source-doc` instead of `requirements.json`
**What goes wrong:** `source_hash` drifts incorrectly — every re-author of the diagram changes the hash, breaking the drift-detection signal.
**Why it happens:** Misreading D-06: `source_hash` should be the hash of what the diagram *depicts*, not the artifact itself.
**How to avoid:** `--source-doc` = `.ba-ops/srs/<slug>/requirements.json`; `--artifact` = `.ba-ops/mermaid/<slug>/diagram.md`.

### Pitfall 4: Modifying `resolve_route.py` or `init_cmd.py`
**What goes wrong:** Introduces a regression or duplicate key in the route tables.
**Why it happens:** Not checking that ba-mermaid is already registered in both dicts.
**How to avoid:** Both dicts already contain `ba-mermaid` entries (confirmed by read). No modification needed.

### Pitfall 5: Generating a synthetic image when mmdc is absent
**What goes wrong:** DESIGN §11 non-negotiable violation; safety gate would reject; criterion 3 validation fails.
**Why it happens:** Trying to be "helpful" when the CLI is missing.
**How to avoid:** When `resolve_mmdc()` raises `NO_MERMAID_CLI`, propagate it immediately. No fallback image generation, ever.

### Pitfall 6: Writing `.mmd` outside `.ba-ops/mermaid/<slug>/`
**What goes wrong:** Violates portability constraint; temp-dir paths may leak outside repo root.
**How to avoid:** Always resolve output directory as `root / ".ba-ops" / "mermaid" / slug`; apply `is_within_root` guard (same pattern as `render_cmd.py` and `trace_cmd.py`).

---

## Validation Architecture

> `workflow.nyquist_validation` is not explicitly `false` — section is REQUIRED.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, confirmed in Phase 1/2) |
| Config file | `pytest.ini` or `pyproject.toml [tool.pytest]` (check Wave 0) |
| Quick run | `pytest .agents/ba-daily-operators/ba-tools/tests/ -x -q` |
| Full suite | `pytest .agents/ba-daily-operators/ba-tools/ -v` |

### 3 ROADMAP Success Criteria → Test Map

| Criterion | Behavior | Test Type | Automated Command | Notes |
|-----------|----------|-----------|-------------------|-------|
| 1. author-no-CLI | `author` route produces inline ` ```mermaid ` block in `.md`; Mermaid CLI is NOT invoked | Unit (mock) | `pytest tests/test_mermaid_author.py -x` | Assert: output `.md` contains ` ```mermaid ` + closing fence; assert `subprocess.run` is NOT called (mock or check no mmdc process spawned) |
| 2. req_ids→INDEX mermaid column, no orphans | After `trace write --kind mermaid` + `index update`, INDEX.md shows mermaid cell for slug; no entry in Orphans section | Integration (fixture) | `pytest tests/test_mermaid_trace_index.py -x` | Fixture: real `requirements.json` with 2 reqs; agent writes `.md` with `req_ids: [FR-001]`; workflow calls trace write; index update; assert INDEX row mermaid cell non-empty; assert Orphans section empty |
| 3. render hard-fail when no CLI | `ba-tools mermaid-render` exits 2 with `NO_MERMAID_CLI` and writes NO output file when PATH has no `mmdc`, no `$MERMAID_CLI`, no `--mermaid-cli`, and `npx` not on PATH | Unit (environment isolation) | `pytest tests/test_mermaid_render_cmd.py::test_no_cli_hard_fail -x` | Patch `shutil.which` to return `None` for all names; assert `BaToolsError` raised with code `NO_MERMAID_CLI`; assert `.mmd` and image files do NOT exist after call |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| MMD-01 | UC/requirement → Mermaid, MD-inline first, no CLI on author | Unit | `pytest tests/test_mermaid_author.py -x` |
| MMD-02 | Each diagram carries `req_ids`; INDEX mermaid column populated, no orphans | Integration | `pytest tests/test_mermaid_trace_index.py -x` |
| MMD-03 | export hard-fails with exit 2 when CLI missing; never synthetic | Unit | `pytest tests/test_mermaid_render_cmd.py -x` |

### Sampling Rate

- **Per task commit:** `pytest .agents/ba-daily-operators/ba-tools/tests/ -x -q`
- **Per wave merge:** Full test suite
- **Phase gate:** All 3 criterion tests green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_mermaid_render_cmd.py` — covers MMD-03 + criterion 3 (no-CLI hard-fail, fence extraction, mmdc invocation)
- [ ] `tests/test_mermaid_author.py` — covers MMD-01 + criterion 1 (author no-CLI)
- [ ] `tests/test_mermaid_trace_index.py` — covers MMD-02 + criterion 2 (req_ids→INDEX)
- [ ] Fixture files: `tests/fixtures/mermaid/sample_diagram.md` (valid ` ```mermaid ` block + frontmatter), `tests/fixtures/mermaid/no_fence.md` (fence-absent case)

---

## Project Constraints (from CLAUDE.md)

These directives are MANDATORY. Research recommendations are all consistent with them.

| Directive | Constraint | Status |
|-----------|------------|--------|
| Python 3.11+ stdlib-first | All new ba-tools code uses only stdlib + `filelock` | Compliant |
| `sys.executable` for Python subprocess | No new Python sub-invocations in this phase | N/A |
| No hard-coded paths | All paths relative to `--repo-root` | Compliant |
| No Pillow/SVG-convert/screenshot | Enforced by NO_MERMAID_CLI hard-fail | Compliant |
| `npx -p @mermaid-js/mermaid-cli mmdc` (with `-p`) | Pattern 2 above uses exact form | Compliant |
| Determinism boundary: ba-tools never infers | `mermaid_render_cmd.py` has no model import | Compliant |
| Every success prints UTF-8 JSON stdout; `BaToolsError` exits 2 | All new code uses `ok_json` / `BaToolsError` | Compliant |
| Codex skill: SKILL.md `name`+`description` only | Skill layout follows Phase-2 pattern | Compliant |
| `openai.yaml`: `interface.*` + `policy.allow_implicit_invocation` | Confirmed from Phase-2 read | Compliant |
| Byte budgets: AGENTS.md/eager refs < 32,768 B | Workflow + agent files must stay under limit | Must verify during authoring |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `--source-doc` and `--requirements` both pointing to `requirements.json` is valid (same file for two flags) | Pattern 3 | `trace_cmd.py` validates both paths exist and are under root; both point to same file — low risk, implementation confirms they are read independently |
| A2 | `filelock` is already in `requirements.txt` / `pyproject.toml` for ba-tools | Standard Stack | If not, `mermaid_render_cmd.py` would need it added; check Wave 0 |
| A3 | `.ba-ops/mermaid/` parent dir is already scaffolded by Phase 1 `scaffold.py` | Architecture | CONTEXT.md states "already scaffolded (Phase 1)"; if not, `mermaid-render` must call `mkdir(parents=True, exist_ok=True)` |

**All three assumptions are LOW risk** — A1 is confirmed by trace_cmd.py code reading; A2/A3 are addressable in Wave 0 with a single check.

---

## Open Questions (RESOLVED)

1. **Frontmatter parsing in the thin workflow**
   - What we know: The workflow reads `req_ids:` from YAML frontmatter and passes to `--req-ids`.
   - What's unclear: Does the thin workflow use a YAML library or simple regex? Codex workflows are Markdown with agent instructions.
   - Recommendation: The workflow instructs the agent to extract `req_ids:` list from frontmatter and format it as a comma-separated string for the `--req-ids` flag. No YAML library needed — the agent reads the list it wrote.

2. **`ba-diagrammer.md` agent prompt: diagram type heuristics**
   - What we know: D-02 says agent chooses the fitting type; D-02a allows `--diagram-type` override.
   - What's unclear: Exact heuristic rules to embed in the prompt.
   - Recommendation: Planner's discretion (CONTEXT.md Claude's Discretion). Research has no additional input.

---

## Environment Availability

| Dependency | Required By | Available | Notes |
|------------|------------|-----------|-------|
| Python 3.11+ | `mermaid_render_cmd.py` | Assumed ✓ | Phase 1/2 confirmed working |
| `mmdc` (PATH) | `render` route only | Unknown — optional by design | Resolution chain handles absent gracefully via hard-fail |
| `npx` (Node 18+) | `render` route fallback | Unknown — optional | Not required if PATH `mmdc` present |
| `filelock` (PyPI) | lockfile writes | Assumed ✓ | Already in Phase 1/2 deps |

**Missing dependencies with no fallback:** none (render route is opt-in; hard-fail IS the contract).
**Missing dependencies with fallback:** mmdc / npx — render route will fail exit 2 (intended behavior).

---

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | Yes | `_SLUG_RE` in `trace_cmd.py` reused; new `mermaid-render` must validate `--slug` and paths via `resolve_under_root` + `is_within_root` |
| V6 Cryptography | No | SHA-256 via `ba_tools.hashing` (stdlib); no new crypto |
| Path traversal (T-02-07b pattern) | Yes | All path inputs validated via `repo.py::resolve_under_root` + `is_within_root`; slug-derived output path re-confirmed under root |

**Known Threat Patterns:**

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| `--slug` path injection (e.g. `../../../etc`) | Tampering | `_SLUG_RE` validation + `is_within_root` on composed output path |
| `--mermaid-cli` flag pointing to arbitrary executable | Elevation of Privilege | `resolve_under_root` on flag value; or document that this is a trusted operator input (same as subprocess argv — caller controls) |
| Fence body containing shell metacharacters passed to mmdc | Tampering | mmdc receives the `.mmd` file path via argv, not the fence body as a string arg; no shell injection vector |

---

## Sources

### Primary (HIGH confidence)
- `03-CONTEXT.md` [VERIFIED: codebase read] — All locked decisions D-01 through D-05fmt
- `trace_cmd.py` [VERIFIED: codebase read] — `--kind mermaid` flag confirmed; `--source-doc`/`--requirements` are separate args; explicit `--req-ids` required for non-srs kinds
- `resolve_route.py` [VERIFIED: codebase read] — `ba-mermaid → author` already registered
- `init_cmd.py` [VERIFIED: codebase read] — `["author", "render", "full"]` already registered
- `__main__.py` [VERIFIED: codebase read] — dispatcher pattern confirmed; `mermaid_render_cmd` not yet present
- `render_cmd.py` [VERIFIED: codebase read] — command-module shape (`register`/`run`/subparsers) confirmed; different render target (JSON→MD)
- `CLAUDE.md` (repo root) [VERIFIED: codebase — loaded as project instructions] — mmdc resolution chain, `-p` flag requirement, `mmdc -i in.mmd -o out.svg` invocation, determinism boundary

### Secondary (MEDIUM confidence)
- `.agents/skills/ba-srs-analyze/` directory listing [VERIFIED: codebase read] — exact layout confirmed (SKILL.md + `agents/openai.yaml`)
- `.agents/ba-daily-operators/ba-core/workflows/` listing [VERIFIED: codebase read] — `ba-srs-analyze.md` exists; `ba-mermaid.md` to create
- `.agents/ba-daily-operators/ba-core/agents/` listing [VERIFIED: codebase read] — `ba-srs-writer.md` confirmed; `ba-diagrammer.md` to create

---

## Metadata

**Confidence breakdown:**
- Route registration: HIGH — confirmed by reading the actual dicts in source files
- trace_cmd.py reuse: HIGH — confirmed `--kind mermaid` + `--req-ids` in actual code
- mermaid_render_cmd design: HIGH — derived from CLAUDE.md verified patterns + render_cmd.py shape
- Skill layout: HIGH — confirmed by reading Phase-2 directory structure
- Fence extraction regex: MEDIUM — standard CommonMark pattern, ASSUMED (not verified against an authoritative test suite)
- `--source-doc` = requirements.json reasoning: MEDIUM — inferred from D-06 drift-detection semantics + trace_cmd.py code; marked A1 in Assumptions Log

**Research date:** 2026-06-18
**Valid until:** 2026-07-18 (stable stack; Python stdlib + existing ba-tools patterns)
