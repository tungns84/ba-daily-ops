# Phase 5: ba-uc Conductor + End-to-End Integration — Pattern Map

**Mapped:** 2026-06-18
**Files analyzed:** 7 (5 new, 2 modified/extended)
**Analogs found:** 7 / 7

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `.agents/skills/ba-uc/SKILL.md` | config / skill index | request-response | `.agents/skills/ba-mockup/SKILL.md` | exact |
| `.agents/skills/ba-uc/agents/openai.yaml` | config / CDX contract | request-response | `.agents/skills/ba-mockup/agents/openai.yaml` | exact |
| `.agents/ba-daily-operators/ba-core/workflows/ba-uc.md` | orchestration workflow | request-response + sequential | `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` (layout) + `ba-srs-analyze.md` (multi-route) | role-match (conductor adds sequential loop over sub-workflows) |
| `.agents/ba-daily-operators/ba-core/agents/ba-uc-conductor.md` | agent prompt / role contract | event-driven sequential loop | `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` | role-match |
| `.agents/ba-daily-operators/ba-core/references/gates.md` (extend) | reference doc / gate contract | — | itself (extend with Safety section) | exact — add `## Safety Gate Contract` section |
| `tests/test_uc_conductor_state.py` | test | CRUD + state-machine | `.agents/ba-daily-operators/ba-tools/tests/test_uc_status.py` + `test_state.py` | exact |
| `tests/test_index_gate_predicate.py` | test | CRUD + index verification | `.agents/ba-daily-operators/ba-tools/tests/test_index.py` (inferred analog) | role-match |

---

## Pattern Assignments

### `.agents/skills/ba-uc/SKILL.md` (config, skill index)

**Analog:** `.agents/skills/ba-mockup/SKILL.md` (lines 1–14)

**Full analog to copy** (lines 1–14):
```markdown
---
name: ba-mockup
description: >
  Turn requirements into a UI mockup at a required --fidelity of html or wireframe.
  html fidelity writes a self-contained static .html file (inline CSS, no framework).
  wireframe fidelity writes markdown-structural blocks in a .md (headings + lists + tables).
  Each screen carries req_ids citing the REQ-IDs it realizes for traceability.
  Routes: screen | full (default: full). Fidelity is required — rejects missing/invalid.
  Trigger phrases: "create mockup", "ui mockup", "wireframe", "html mockup",
  "screen mockup", "$ba-mockup".
---

<!-- Workflow file: .agents/ba-daily-operators/ba-core/workflows/ba-mockup.md -->
<!-- No body content required — SKILL.md is a discovery index only              -->
```

**Adapt for ba-uc:**
- `name: ba-uc`
- `description:` — keyword-dense, include: routes `deliver / resume / status / iterate` (default `deliver`), sequential loop over `srs-analyze → mermaid → mockup → index`, resumable via `uc-status`, `--fidelity html|wireframe` required, `--uc "<file>: ## UC-001. <name>"`.
- Trigger phrases: `"deliver use case"`, `"ba-uc deliver"`, `"run use case"`, `"$ba-uc"`.
- Workflow pointer: `.agents/ba-daily-operators/ba-core/workflows/ba-uc.md`
- Rules: `name` + `description` frontmatter ONLY — no other YAML keys (CDX constraint).

---

### `.agents/skills/ba-uc/agents/openai.yaml` (config, CDX contract)

**Analog:** `.agents/skills/ba-mockup/agents/openai.yaml` (lines 1–19)

**Full analog to copy** (lines 1–19):
```yaml
interface:
  display_name: "BA Mockup"
  short_description: "Requirements → UI mockup .html or wireframe .md; req_ids traceability via trace write + index update."
  default_prompt: |
    Use the ba-mockup workflow on the given SRS slug with --fidelity html|wireframe.
    Run `ba-tools resolve-route ba-mockup` to confirm the default route = full.

    To start: open .agents/ba-daily-operators/ba-core/workflows/ba-mockup.md
    and follow the `full` route steps:
      1. Run `ba-tools resolve-route ba-mockup` to confirm route = full.
      2. Validate --fidelity (required: html or wireframe).
      3. Run `ba-tools init ba-mockup` for scaffold context.
      4. Open .agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md and follow the author role.
      5. After authoring: extract req_ids from artifact, run trace write --kind mockup, run index update.

    Provide the SRS slug and --fidelity. Example: slug = order-management, --fidelity html
policy:
  allow_implicit_invocation: false
```

**Adapt for ba-uc:**
- `display_name: "BA UC Conductor"`
- `short_description:` — one line: "Delivers one UC end-to-end: srs-analyze → mermaid → mockup → index; resumable via uc-status; gate after each step."
- `default_prompt:` — explicit first steps:
  1. Run `ba-tools resolve-route ba-uc` to confirm default route = `deliver`.
  2. Validate `--uc` (required) and `--fidelity` (required: `html` or `wireframe`).
  3. Run `ba-tools init ba-uc` for scaffold context.
  4. Open `.agents/ba-daily-operators/ba-core/workflows/ba-uc.md` and follow the `deliver` route.
- `policy.allow_implicit_invocation: false` — mandatory on the conductor (REQUIREMENTS CDX-02).
- Nesting MUST be `interface:` → fields; `policy:` → field. Do NOT flatten.

---

### `.agents/ba-daily-operators/ba-core/workflows/ba-uc.md` (orchestration workflow)

**Primary analog:** `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` (header + route structure)
**Secondary analog for multi-route layout:** `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` (lines 1–50, route list)

**Header pattern** (ba-mockup.md lines 1–32):
```markdown
---
operator: ba-mockup
default_route: full
routes:
  - screen
  - full
---

# ba-mockup Workflow

...

**Determinism boundary:** `ba-tools` commands do ONLY file/command/hash-provable
work. All fidelity selection, REQ-ID subset selection, and mockup authoring is
agent-owned. The CLI never calls an LLM.

**Sequential execution:** This is a Codex v1 operator — there is no autonomous
parallel subagent spawn. Each step runs sequentially; each step must complete
before the next begins.

**Pass paths, not content:** The workflow hands the agent the slug and
`requirements.json` path. The agent reads the file and writes the mockup artifact.
```

**Adapt for ba-uc:**
```markdown
---
operator: ba-uc
default_route: deliver
routes:
  - deliver
  - resume
  - status
  - iterate
---
```

Keep the three boilerplate paragraphs (Determinism boundary, Sequential execution, Pass paths not content) verbatim — they apply identically to the conductor.

**Route section pattern** (ba-mockup.md lines 28–55 for `screen` route; ba-srs-analyze.md lines 34–50 for extract route):
```markdown
## Route: deliver

End-to-end: srs-analyze (full) → mermaid (full) → mockup (full) → index update.
Gate after each step before writing pipeline status.

### Step 0 — Pre-flight

Run `ba-tools resolve-route ba-uc` to confirm default route = `deliver`.
Validate `--uc` (required) and `--fidelity` (required: `html` or `wireframe`).
Run `ba-tools init ba-uc` for scaffold context. Verify all four pipeline rows exist.

### Step 1 — srs-analyze (full route)

Open `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` and follow
the `full` route.
...
After srs full route completes: capture slug from output. Apply Quality gate
(gates.md). If gate fails: set pipeline_step srs-analyze pipeline_status failed → STOP.
If gate passes: set pipeline_status complete.

### Step 2 — mermaid (full route, explicit — NOT default author)

Open `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` and follow
the `full` route (NOT the default `author` route).
...
After index update: apply index-integrity gate (D-G2). If orphans or step req_ids
still in gaps: set pipeline_status failed → STOP. If passes: set pipeline_status complete.
```

**Key rules for the conductor workflow:**
- Each step sets `pipeline_status = failed` on gate FAIL via `ba-tools state patch --data '{"pipeline_step":"<step>","pipeline_status":"failed"}'`, then STOPs.
- Each step sets `pipeline_status = complete` only after its gate passes.
- Slug is captured from srs step output and threaded verbatim to mermaid/mockup/index.
- `--fidelity` is forwarded to the mockup step.
- The `index` final step is a bare `ba-tools index update` CLI call, not a sub-workflow.
- Byte budget: keep under DEFAULT < 38,000 B by referencing sub-workflows by path, not embedding their bodies.

---

### `.agents/ba-daily-operators/ba-core/agents/ba-uc-conductor.md` (agent prompt, role contract)

**Analog:** `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` (lines 1–26)

**Header + Inputs pattern** (ba-mockup-author.md lines 1–26):
```markdown
# ba-mockup-author Agent Role

**Role:** Mockup-authoring agent. Read the SRS `requirements.json`, select the
REQ-ID subset the screen realizes, and write either a self-contained `.html` or
a wireframe `.md` artifact depending on `--fidelity`.

**Determinism boundary:** You author and judge. `ba-tools` handles all
file/hash/CLI-provable work. You NEVER call an LLM sub-service or any external
tool. You READ source files and WRITE the mockup artifact.

---

## Inputs (paths only — no raw content forwarded)

You receive this payload:

```
requirements_json: .ba-ops/srs/<slug>/requirements.json
slug:              <slug>
fidelity:          <html|wireframe>
screen_name:       <chosen by you from the UC/requirement context>
route:             <screen | full>
```

Read `requirements_json` yourself. No content is forwarded to you — only paths.
```

**Adapt for ba-uc-conductor:**
```markdown
# ba-uc-conductor Agent Role

**Role:** Conductor agent. Orchestrate the sequential ba-uc pipeline loop
(srs-analyze → mermaid → mockup → index), apply per-step gates, write pipeline
status between steps, and thread the shared slug + --fidelity end-to-end.

**Determinism boundary:** You orchestrate and judge gate verdicts. `ba-tools`
handles all provable work (uc-status, state patch, trace write, index update,
verify). You NEVER embed raw artifact content between steps — pass paths only.

---

## Inputs (paths only — no raw content forwarded)

You receive this payload:

```
uc:        <file>: ## UC-001. <name>   # the --uc argument
fidelity:  html | wireframe            # forwarded to mockup step
route:     deliver | resume | status | iterate
```
```

**Key conductor-specific rules to add (no analog — unique to conductor):**
- Slug threading: capture slug from srs step output; forward verbatim to every subsequent step.
- Gate verdicts: write to `## Gate Verdicts` table in STATE.md AND `note` frontmatter key.
- Status discipline: `complete` only after gate passes; `failed` on gate fail; never skip non-complete steps on resume.
- Sub-workflow reading: open the sub-operator workflow file and follow it — do NOT summarize or abbreviate.

---

### `.agents/ba-daily-operators/ba-core/references/gates.md` (extend — add Safety Gate Contract section)

**Analog:** `gates.md` itself — existing `## Gate 3: trace write + index update` section (lines 97–120) for section formatting. Also the `## Prohibition summary` table (lines 156–164) for the safety-gate analogous prohibition table.

**Section heading + scope marker pattern** (gates.md lines 1–8 for title convention):
```markdown
## Safety Gate Contract

**Scope:** Plugin-enforced. The spine (`ba-srs-analyze`, `ba-mermaid`, `ba-mockup`,
`ba-uc`) invokes no render CLI; the conductor **never fires the Safety gate**.
This contract governs the deferred plugins: `ba-make-diagram`, `ba-uc-delivery`.

**Phase-5 status:** Contract defined. Enforcement deferred to plugin implementation.
```

**Clause format** — mirror Gates 1/2/3 prose blocks:
```markdown
### Clause 1 — Render CLI only

Any render/export step must invoke a real CLI: `draw.io -x -f png -o` or
`mmdc -i <file> -o <file>`. No Pillow, no SVG-converter, no screenshot, no
hand-pasted image. (DESIGN §6, §11.)

### Clause 2 — Path-traversal and injection scan

Before any `.ba-ops/` write triggered by a plugin, validate via
`resolve_under_root` + `is_within_root` (repo.py). Any path passed to a render
CLI must resolve under `--repo-root`.

### Clause 3 — Media extension check

A rendered media file must have extension `.png` or `.svg` (`.pdf` for
export-only). No other extension is valid for embedded media. Reject at write time.

### Clause 4 — Hash manifest (PLUG-04, deferred)

The render step writes a manifest JSON `{rendered_sha256, embedded_sha256}`;
pass condition `rendered_sha256 == embedded_sha256`. Enforced only when PLUG-04
is implemented.
```

**Prohibition table** — mirror existing table at gates.md lines 156–164:
```markdown
## Safety Gate — Prohibition summary

| Prohibition | Rule |
|-------------|------|
| Never use Pillow/SVG-converter/screenshot for render | DESIGN §6/§11 |
| Never write media with extension outside .png/.svg/.pdf | Clause 3 |
| Never pass paths outside --repo-root to render CLI | Clause 2 |
| Never fire Safety gate from the spine | Scope marker |
```

---

### `tests/test_uc_conductor_state.py` (test, state-machine CRUD)

**Analog:** `.agents/ba-daily-operators/ba-tools/tests/test_uc_status.py` (all) + `test_state.py` (lines 1–80)

**State helper pattern** (test_uc_status.py lines 11–57):
```python
def _make_state_md(ba_ops: Path, steps: dict[str, str], uc_id: str = "") -> None:
    """Write a .ba-ops/STATE.md with the given pipeline step statuses."""
    ba_ops.mkdir(parents=True, exist_ok=True)

    rows = []
    for step, status in steps.items():
        rows.append(f"| {step} | {status} | |")
    table = "\n".join(rows)

    state_content = f"""\
---
step: 0
...
---

## Pipeline Steps

| Step | Status | Completed At |
|------|--------|--------------|
{table}
...
"""
    (ba_ops / "STATE.md").write_text(state_content, encoding="utf-8")
```

**CLI invocation pattern** (test_state.py lines 29–40):
```python
def _run_state(action: str, data: str, repo_root: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, "-m", "ba_tools",
            "--repo-root", repo_root,
            "state", action,
            "--data", data,
        ],
        capture_output=True,
        text=True,
    )
```

**Test structure pattern** (test_uc_status.py lines 68–103 — one positive, one assertion, one error path per test):
```python
def test_uc_status_partial_pipeline_next_step(tmp_path):
    """Given STATE.md with srs-analyze complete, next_step is 'mermaid'."""
    ba_ops = tmp_path / ".ba-ops"
    _make_state_md(ba_ops, {
        "srs-analyze": "complete",
        "mermaid": "pending",
        "mockup": "pending",
        "index": "pending",
    })

    result = _run_uc_status(tmp_path)
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["next_step"] == "mermaid", (
        f"next_step should be 'mermaid' when only srs-analyze is complete, got {payload['next_step']!r}"
    )
```

**New tests to add in this file** (all use `_make_state_md` + `_run_uc_status` or `_run_state`):
- `test_failed_step_is_next_step` — srs-analyze `failed` → next_step = `srs-analyze`
- `test_in_progress_step_is_next_step` — mermaid `in_progress` → next_step = `mermaid`
- `test_gate_fail_state_not_clobbered` — write srs=complete, mermaid=failed; assert both preserved
- `test_resume_entry_point` — after mermaid=failed, uc-status next_step = `mermaid`
- `test_pipeline_patch_round_trip` — `state patch pipeline_step=mermaid pipeline_status=complete` → uc-status next_step = `mockup`
- `test_concurrent_pipeline_patch_no_clobber` — two threads patching different steps; assert both writes survive (copy concurrent-write pattern from test_state.py lines 150+)
- `test_scaffold_seeds_all_four_rows` — `ensure_scaffold(tmp_path)` → uc-status returns all four steps

**Concurrent-write pattern** to look up: `test_state.py` has a concurrent-write test past line 150 — read that section for the `multiprocessing` / threading approach to copy.

---

### `tests/test_index_gate_predicate.py` (test, index verification)

**Analog:** `.agents/ba-daily-operators/ba-tools/tests/test_index.py` and `test_trace.py` for fixture setup.

**Pattern to follow** (from test_uc_status.py fixture approach + RESEARCH.md Q6 predicate):

Tests use `tmp_path` + scaffold, write trace records programmatically, invoke `ba-tools index update`, parse JSON stdout, assert on `orphans` and `gaps` fields.

```python
def test_index_gate_no_orphans_after_mermaid_trace(tmp_path):
    """After trace write --kind mermaid with req_ids from srs, orphans == []."""
    # 1. Scaffold + write srs trace with FR-001, FR-002
    # 2. Write mermaid trace with req_ids FR-001
    # 3. Run ba-tools index update
    result = subprocess.run(
        [sys.executable, "-m", "ba_tools", "--repo-root", str(tmp_path), "index", "update"],
        capture_output=True, text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["orphans"] == [], f"Expected no orphans, got {payload['orphans']}"
    assert "FR-001" not in payload["gaps"], "FR-001 must be covered after mermaid trace"

def test_index_gate_orphan_detected(tmp_path):
    """Mermaid trace citing unknown REQ-ID surfaces as orphan."""
    # Write mermaid trace with XX-999 (not in srs traces)
    # Run index update
    payload = json.loads(result.stdout)
    assert "XX-999" in payload["orphans"]
```

**D-G2 predicate to implement in tests:**
```python
# FAIL if:
assert len(payload["orphans"]) == 0                        # no new orphan
assert all(rid not in payload["gaps"] for rid in step_req_ids)  # step's own req_ids covered
```

---

## Shared Patterns

### Determinism boundary boilerplate
**Source:** `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` lines 14–25
**Apply to:** `ba-uc.md` workflow — copy verbatim, replacing operator-specific wording.
```markdown
**Determinism boundary:** `ba-tools` commands do ONLY file/command/hash-provable
work. All fidelity selection, REQ-ID subset selection, and mockup authoring is
agent-owned. The CLI never calls an LLM.

**Sequential execution:** This is a Codex v1 operator — there is no autonomous
parallel subagent spawn. Each step runs sequentially; each step must complete
before the next begins.

**Pass paths, not content:** The workflow hands the agent the slug and
`requirements.json` path. The agent reads the file and writes the mockup artifact.
```

### CDX skill layout (SKILL.md + openai.yaml)
**Source:** `.agents/skills/ba-mockup/SKILL.md` + `.agents/skills/ba-mockup/agents/openai.yaml`
**Apply to:** `.agents/skills/ba-uc/` — same two-file flat layout under repo root.
Key invariants: SKILL.md frontmatter = `name` + `description` only; `openai.yaml` nesting = `interface:` block + `policy:` block; `allow_implicit_invocation: false` always on the conductor.

### Pipeline state-machine test helper
**Source:** `.agents/ba-daily-operators/ba-tools/tests/test_uc_status.py` lines 11–65 (`_make_state_md` + `_run_uc_status`)
**Apply to:** `test_uc_conductor_state.py` — copy both helpers as-is; add `_run_state_patch` helper mirroring `_run_state` from `test_state.py` lines 29–40.

### Gate section format
**Source:** `.agents/ba-daily-operators/ba-core/references/gates.md` — `## Gate 1:` through `## Gate 3:` structure (header, command block, pass/fail semantics, blocking semantics).
**Apply to:** `## Safety Gate Contract` addition in `gates.md` — use same heading level (`##` for contract, `###` for clauses), same command-block fencing, same prohibition table format.

### Pipeline status write
**Source:** RESEARCH.md Q3 (confirmed from `state_store.py`) — single pattern used everywhere the conductor sets step status:
```bash
ba-tools state patch --data '{"pipeline_step":"<step>","pipeline_status":"<status>"}'
```
Valid `<status>` values: `pending`, `in_progress`, `complete`, `failed` (and variants `completed`, `done` for complete; anything not in `{complete, completed, done}` is non-complete for uc-status purposes).

---

## No Analog Found

No files are without a codebase analog. All patterns have direct matches in the Phase 2/3/4 skill/workflow/agent/test corpus.

---

## Metadata

**Analog search scope:** `.agents/skills/`, `.agents/ba-daily-operators/ba-core/`, `.agents/ba-daily-operators/ba-tools/tests/`
**Files read:** 10 (SKILL.md, openai.yaml, ba-mockup.md, ba-srs-analyze.md, ba-mockup-author.md, gates.md, test_uc_status.py, test_state.py, conftest.py + 05-CONTEXT.md/RESEARCH.md)
**Pattern extraction date:** 2026-06-18

---

## PATTERN MAPPING COMPLETE
