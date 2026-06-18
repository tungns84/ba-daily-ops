# Phase 5: ba-uc Conductor + End-to-End Integration — Research

**Researched:** 2026-06-18
**Domain:** Orchestration / Integration — internal conductor over Phases 2/3/4 operators
**Confidence:** HIGH (all findings from codebase source files; no external lookups needed)

---

## Summary

Phase 5 is an orchestration + contract + integration-test phase. Every
component it needs already exists; nothing requires new ba-tools commands.
The conductor (`ba-uc`) reads the three spine operators' workflow files in
sequence, applies the per-step gate, and writes pipeline state between steps.
All ba-tools surface (uc-status, state advance, trace write, index update,
resolve_route, init) is already registered and tested.

One factual correction relative to CONTEXT.md: `scaffold.py` **already seeds
the `index` row** in the STATE.md Pipeline Steps table (scaffold.py:133 —
`| index | pending | |`). WR-02 as described ("scaffold seeds only
srs/mermaid/mockup") does **not exist** in the current codebase. The planner
should note this and NOT include a scaffold-patch task.

One genuine gap: `index update`'s `ok_json` does **not emit per-column
coverage** — it emits `orphans`, `gaps`, `req_ids`, `stale`, but the
`covered_by` dict (which would prove "step's own req_ids landed in mermaid/mockup
column") is computed internally and discarded. The D-G2 self-coverage predicate
requires either (a) parsing INDEX.md directly, or (b) the conductor storing the
just-written trace's `req_ids` and checking that `gaps` shrinks accordingly.

**Primary recommendation:** Plan the conductor as pure workflow orchestration
with a thin agent prompt; zero new ba-tools commands; close D-G2 with the
INDEX.md-parse approach (simpler than adding a new `ok_json` field).

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-G1** — Gate after each step is operator-appropriate:
- After `srs-analyze`: full Quality gate (verify → ba-critic CoVe ≤3) from gates.md.
- After `mermaid` and `mockup`: index-integrity check (index update → assert no new orphan AND step's own req_ids in its column). No new ba-tools command.

**D-G2** — Index-integrity gate FAILs iff step introduced a new orphan OR step's own req_ids did not appear in its INDEX column. Gaps in other columns are NOT a fail condition.

**D-INV** — Conductor reads each spine operator's workflow file inline and follows it sequentially (Codex v1). Owns only the per-step gate + state write. Exact route per step: reconcile against real workflow bodies.

**D-IN** — Input: `ba-uc --uc "<file>: ## UC-001. <name>" --fidelity html|wireframe`. Slug captured from srs step output (Phase 2 D-19) and threaded verbatim to mermaid/mockup/index.

**D-RES1** — Pipeline step status set to `complete` only after its gate passes. Gate FAIL → set `failed` → STOP. Kill mid-step → leaves `pending`/`in_progress`. Either way step is non-complete → uc-status next_step lands on that step.

**D-RES2** — `resume` route re-enters at uc-status next_step and re-runs from scratch.

**D-RES3** — Conductor guarantees all four pipeline rows exist before writing statuses. (Researcher finding: scaffold already seeds all four rows; see WR-02 correction below.)

**D-TEST** — Verification splits: automatable pytest (no LLM) + agent-run E2E UAT.

**D-SAFE** — GATE-03 is contract-only this phase. Document in ba-core/references/ (extend gates.md or sibling safety-gate.md — planner's call).

### Claude's Discretion
- Exact route driven per spine step inside `deliver` — reconcile against real workflow bodies.
- Whether conductor needs any new ba-tools surface (expected: none; confirm).
- The `iterate` route body.
- Exact `failed` status string + failure-reason surface (STATE.md note vs uc-status field).
- WR-02 fix mechanism (researcher finding: no fix needed — already seeded).
- GATE-03 doc location (extend gates.md vs new safety-gate.md) and exact wording.
- Conductor workflow byte budget.
- `openai.yaml` `interface.*` wording + keyword-dense SKILL.md `description`.
- Test-fixture design.

### Deferred Ideas (OUT OF SCOPE)
- Actual Safety-gate enforcement (render-CLI checks, extension validation, manifest hash comparison) — lives in deferred plugins.
- True fresh-context subagent spawn — v2.
- Multi-UC batch delivery.
- Promoting index-integrity gate to a new ba-tools `gate` command.
- `--diagram-type` surface on the conductor.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UC-01 | `ba-uc` delivers ONE use case end-to-end: srs-analyze → mermaid → mockup → index | Route reconciliation (Q1); ba-tools surface confirmation (Q4) |
| UC-02 | `ba-uc` runs as a single sequential agent loop with a Quality gate between steps | Gate semantics (Q2); route bodies confirmed (Q1) |
| UC-03 | `ba-uc` is resumable via `uc-status`; routes deliver/resume/status/iterate (default `deliver`) | Resume/kill-recovery analysis (Q3); uc_status.py source (Q3) |
| GATE-03 | Safety gate contract defined for render/embed steps (enforced by deferred plugins): render CLI only, path-traversal + injection scan, .png/.svg extension check | GATE-03 contract design (Q5) |
</phase_requirements>

---

## Q1: Per-Step Route Reconciliation (D-INV)

### Source confirmation

Routes confirmed from workflow YAML frontmatter:

| Operator | Default Route | Available Routes | Source |
|----------|--------------|------------------|--------|
| ba-srs-analyze | `full` | extract, draft, lint, verify, full, iterate | ba-srs-analyze.md:7 |
| ba-mermaid | `author` | author, render, full | ba-mermaid.md:6 |
| ba-mockup | `full` | screen, full | ba-mockup.md:6 |
| ba-uc | `deliver` | deliver, resume, status, iterate | resolve_route.py:14, init_cmd.py:27 |

### What each conductor step drives

**Step 1 — srs-analyze:** Drive the `full` route.

The `full` route body (ba-srs-analyze.md:136) = extract → draft (ba-srs-writer) → render → verify → CoVe loop (≤3) → trace write + index update + state advance.

Gate after this step = the full Quality gate (gates.md). CONTEXT.md D-G1 is confirmed by the workflow: the srs `full` route already embeds verify + ba-critic + trace + index (Steps 4/5/6 of ba-srs-analyze.md:167–253).

The conductor captures the derived slug from the srs step output (Phase 2 D-19). The slug derives from `--slug` if provided, else source filename slugify, else UC id (ba-srs-analyze.md:44–46).

**Step 2 — mermaid:** Drive the `full` route (NOT the default `author`).

The ba-mermaid default route is `author` (ba-mermaid.md:4), but the conductor must drive `full` to get trace write + index update. The `full` route (ba-mermaid.md:56) = author → trace write (`--kind mermaid`) → index update. There is no index update in the `author` route.

**MISMATCH FLAG:** CONTEXT.md states "mermaid `full` = author→trace→index" which is correct — but the mermaid default route is `author`, not `full`. The conductor cannot rely on `ba-tools resolve-route ba-mermaid` returning `full`. It must explicitly drive the `full` route by following the `full` route steps directly. The planner must instruct the conductor to read the `## Route: full` section of ba-mermaid.md, not the default.

**Step 3 — mockup:** Drive the `full` route (which IS the default).

The mockup default route is `full` (ba-mockup.md:6). The `full` route (ba-mockup.md:57) = screen (author) → extract req_ids from artifact → trace write (`--kind mockup`) → index update.

`--fidelity` is passed from conductor input to the mockup step (D-IN). The workflow validates fidelity first (ba-mockup.md:37): must be `html` or `wireframe`, rejects missing/invalid.

**Step 4 — index:** Run `ba-tools index update` as the final canonical step.

This is a standalone CLI call, not a sub-operator invocation. `index update` is idempotent (full rebuild from trace records — index_cmd.py:52). The mermaid `full` and mockup `full` routes already run `index update`; the conductor's final standalone `index update` is the canonical end-state rebuild that ensures the complete INDEX.md is consistent after all three prior trace writes.

### Route summary table for conductor

| Step | Drive route | Why | Confirms D-INV |
|------|-------------|-----|----------------|
| srs-analyze | `full` | Embeds verify + ba-critic + trace + index (ba-srs-analyze.md:134) | Yes |
| mermaid | `full` (explicit, not default) | Default `author` skips trace+index; `full` includes them (ba-mermaid.md:54) | Yes — must be explicit |
| mockup | `full` (default) | Full route = author → trace → index (ba-mockup.md:57) | Yes |
| index | `ba-tools index update` (CLI) | Final idempotent rebuild | Yes |

---

## Q2: Per-Step Gate Semantics (D-G1/D-G2)

### After srs-analyze: Quality gate

Confirmed from gates.md and ba-srs-analyze.md `full` route. The srs `full` route runs the Quality gate internally (verify → CoVe → trace+index+state advance at Step 6). The conductor's role after srs: check that the srs step completed without escalation. If the CoVe loop escalated (non-convergence-escalation), the srs step leaves STATE.md without advancing — the conductor detects this and sets status `failed` for the srs step per D-RES1.

### After mermaid and mockup: Index-integrity gate (D-G2)

The `index update` ok_json emits (index_cmd.py:244–250):

```json
{
  "ok": true,
  "updated": ".ba-ops/INDEX.md",
  "req_ids": ["FR-001", "FR-002"],
  "gaps": ["FR-002"],
  "orphans": [],
  "stale": []
}
```

**Fields available for D-G2:**
- `orphans` — list of REQ-IDs cited by non-srs traces but absent from all SRS traces. A non-empty list after a step = new orphan introduced → FAIL condition 1 of D-G2.
- `gaps` — list of REQ-IDs from SRS traces with no non-SRS coverage. This does NOT directly tell the conductor which req_ids from the current step's trace landed in which column.
- `req_ids` — full list of valid REQ-IDs from srs traces (does NOT indicate column coverage).

**Gap in D-G2 coverage:** The `covered_by` dict (which maps req_id → set of non-srs trace keys that cover it) is computed in index_cmd.py:137–147 but **NOT emitted in ok_json**. The "step's own req_ids landed in its INDEX column" sub-predicate is therefore NOT directly readable from the JSON output alone.

**Workable resolution (no new ba-tools command):** The conductor can verify self-coverage by comparing the `gaps` list before and after the step's trace write:
1. Before the step runs `trace write`, read the current `gaps` list (or assume all step req_ids are gapped).
2. After `index update`, check that none of the step's own `req_ids` appear in `gaps`.

Alternatively, the conductor can parse INDEX.md directly after `index update` — the matrix rows have status `ok` when covered, `gap` when not, `orphan` for orphan rows. This is a simple Markdown table read.

**Recommendation:** Conductor stores the `req_ids` list it passed to `trace write` (available from the artifact's YAML frontmatter extraction step that the `full` route already performs). After `index update`, assert that none of those req_ids appear in `gaps`. This is computable from the existing JSON output without a new command.

### D-G2 exact fail predicate (computable from existing output)

```
FAIL if:
  len(index_update_output["orphans"]) > 0          # new orphan from this step
  OR
  any(rid in index_update_output["gaps"]            # step's own req_ids not covered
      for rid in step_trace_req_ids)
```

Where `step_trace_req_ids` = req_ids extracted from the artifact's frontmatter/comment (already extracted in the workflow's trace write step).

---

## Q3: Resume / Kill-Recovery (D-RES1/D-RES2/D-RES3)

### uc-status next_step computation (confirmed)

From uc_status.py:87–93:

```python
PIPELINE_STEPS: list[str] = list(_PIPELINE_STEPS)  # ("srs-analyze","mermaid","mockup","index")
_COMPLETE_STATUSES: frozenset[str] = frozenset({"complete", "completed", "done"})

def _compute_next_step(steps: dict[str, str]) -> str:
    for step in PIPELINE_STEPS:
        status = steps.get(step, "pending").lower()
        if status not in _COMPLETE_STATUSES:
            return step
    return "done"
```

`next_step` = first step in canonical order (`srs-analyze → mermaid → mockup → index`) whose status is NOT in `{complete, completed, done}`. This is confirmed to handle `pending`, `in_progress`, and `failed` statuses as non-complete — all correctly land on the failed/killed step.

`uc_status.py` imports `PIPELINE_STEPS` from `state_store.PIPELINE_STEPS` (state_store.py:126):
```python
PIPELINE_STEPS: tuple[str, ...] = ("srs-analyze", "mermaid", "mockup", "index")
```
All four steps are in the canonical order. Single source of truth in state_store.

### WR-02 correction: scaffold.py already seeds the `index` row

**CONTEXT.md D-RES3 states:** "The current `scaffold.py` seeds only the first three rows, and `pipeline_step` silently no-ops when the row / section is absent (tech-debt WR-02)."

**Codebase reality (scaffold.py:128–133):**

```python
_STATE_MD = """\
...
## Pipeline Steps

| Step | Status | Completed At |
|------|--------|--------------|
| srs-analyze | pending | |
| mermaid | pending | |
| mockup | pending | |
| index | pending | |      ← line 133: index row IS present
```

The `index` row is seeded by the existing scaffold template. WR-02 as described **does not exist** in the current code. The planner must NOT include a scaffold-patch task — it would be a no-op or risk breaking the idempotency guarantee (`ensure_scaffold` never overwrites existing files).

**What is true:** `update_pipeline_step` (state_store.py:134–185) does silently return the body unmodified when the row is not found (no error raised). But since the scaffold already seeds all four rows, this silent no-op path is not triggered on a normal init → pipeline flow.

**Conductor defensive strategy (still recommended):** After `ba-tools init ba-uc`, verify the Pipeline Steps table has all four rows before writing statuses. If a hand-edited or legacy STATE.md is missing the `index` row (possible in dev), the conductor should surface a clear error rather than silently failing. This is a defensive check, not a structural fix.

### update_pipeline_step no-op behavior (confirmed)

state_store.py:174: when `cells[0] == step_name` is not matched, `out.append(line)` — the body is returned unchanged, no error. The conductor must validate row presence explicitly if defensive coding is required.

### Pipeline status values the conductor writes

From state_store.ALLOWED_KEYS and merge_state logic:
- `pipeline_step` + `pipeline_status` are the reserved directive keys (state_store.py:248–264).
- `pipeline_step` must be one of `PIPELINE_STEPS` — else `UNKNOWN_PIPELINE_STEP` error (exit 2).
- `pipeline_status` must be a non-empty string.
- These are written via `ba-tools state patch --data '{"pipeline_step":"mermaid","pipeline_status":"complete"}'`.

The exact `failed` status string is at planner's discretion (CONTEXT.md). Recommendation: use `"failed"` (matches D-RES1 wording, unambiguous, not in `_COMPLETE_STATUSES`).

---

## Q4: Zero-New-ba-tools Confirmation

### Full ba-tools surface the conductor needs

| Command | Purpose | Registered | Source |
|---------|---------|------------|--------|
| `ba-tools resolve-route ba-uc` | Confirm default route = `deliver` | YES | resolve_route.py:14 |
| `ba-tools init ba-uc` | Scaffold .ba-ops/, return context JSON | YES | init_cmd.py:27 |
| `ba-tools uc-status` | Read pipeline state + next_step | YES | uc_status.py |
| `ba-tools state patch --data '{"pipeline_step":...,"pipeline_status":...}'` | Write step status | YES | state_store.py:248 |
| `ba-tools state advance` | Record gate verdict | YES | state_store.py (advance action) |
| `ba-tools trace write --kind srs|mermaid|mockup` | Per-step trace (run within sub-operator workflows) | YES | trace_cmd.py |
| `ba-tools index update` | Rebuild INDEX.md; exposes orphans/gaps for D-G2 | YES | index_cmd.py |

The sub-operator workflows also call:
- `ba-tools verify` — within srs `full` route
- `ba-tools lint-requirements` — within srs `full` route
- `ba-tools render srs` — within srs `full` route
- `ba-tools extract-uc` — within srs extract step (if UC-shaped source)

All of these are Phase 1 commands — confirmed registered.

**Verdict: ZERO NEW ba-tools commands.** The conductor is pure orchestration over the existing surface. This mirrors Phase 4's pattern (04-CONTEXT.md: "no schema change, no new ba-tools command").

---

## Q5: GATE-03 Safety Contract (D-SAFE)

### Doc location recommendation

**Extend `gates.md` with a new `## Safety Gate Contract` section** rather than creating a sibling file.

Rationale: gates.md is the single canonical gate reference already read by the spine operators. Adding a Safety section keeps all gate contracts co-located and avoids a second discovery path. A sibling `safety-gate.md` would require updating all operator workflow "see also" references. The Safety gate is explicitly contract-only this phase (not enforced on the spine), so a lightweight addition to gates.md is lower-risk.

### Exact clauses (D-SAFE)

The following content belongs in `## Safety Gate Contract` in gates.md:

**Scope:** This gate is **enforced by the deferred plugins** (`ba-make-diagram`, `ba-uc-delivery`). The spine (`ba-srs-analyze`, `ba-mermaid`, `ba-mockup`, `ba-uc`) invokes no render CLI; therefore the conductor **never fires the Safety gate**.

**Clause 1 — Render CLI only:**
Any render/export step must invoke a real CLI: `draw.io -x -f png -o` or `mmdc -i <file> -o <file>`. No Pillow, no SVG-converter, no screenshot, no hand-pasted image. (DESIGN §6, §11.)

**Clause 2 — Path-traversal and injection scan:**
Before any `.ba-ops/` write triggered by a plugin, run `ba-tools scan --file <artifact>` (TOOL-15, advisory). Any path passed to a render CLI must resolve under `--repo-root` (validate via `resolve_under_root` + `is_within_root` from repo.py).

**Clause 3 — Media extension check:**
A rendered media file must have extension `.png` or `.svg` (for raster/vector; `.pdf` for export-only). No other extension is valid for embedded media. Reject at write time.

**Clause 4 — Hash manifest (PLUG-04, deferred):**
The render step writes a manifest JSON `{rendered_sha256, embedded_sha256}`; pass condition `rendered_sha256 == embedded_sha256`. (This clause is enforced only when PLUG-04 is implemented — not this phase.)

**Phase-5 scope marker:** "Phase 5 defines this contract. Enforcement is plugin-responsibility. The spine is exempt."

---

## Q6: Byte Budget

### Current Phase 3/4 workflow sizes

Phase 3 (`ba-mermaid.md`) and Phase 4 (`ba-mockup.md`) are single thin workflow files. Checking sizes:

- `ba-mermaid.md` — 112 lines, approx 3.5 KB: well within DEFAULT < 38,000 B.
- `ba-mockup.md` — 99 lines, approx 3.0 KB: well within DEFAULT.
- `ba-srs-analyze.md` — 295 lines, approx 9.5 KB: well within DEFAULT.

### ba-uc conductor workflow estimate

The `ba-uc` conductor workflow has four routes (`deliver`, `resume`, `status`, `iterate`). The `deliver` route is the most complex: it reads three sub-operator workflows inline (by reference, not by embedding them). The conductor workflow describes orchestration steps, not the full bodies of srs/mermaid/mockup workflows.

Estimated conductor workflow size: 200–350 lines, ~7–12 KB. Well within DEFAULT < 38,000 B if the conductor workflow references the sub-operator workflows by path ("Open .agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md and follow the `full` route") rather than embedding their full bodies.

**Recommendation:** Keep the conductor workflow as a DEFAULT-tier file. Do NOT embed the sub-operator workflow bodies — reference them by path (matches DESIGN §4 "pass paths, not content" and the established pattern in existing conductor prompts). If the byte budget is tight, the `deliver` route can reference an extracted `deliver.md` per-route file, but this is unlikely to be necessary.

**Monitor for:** If the agent prompt (`ba-core/agents/ba-uc-conductor.md`) needs to carry full role contracts for srs-writer + diagrammer + mockup-author inline, the combined size could approach DEFAULT. Mitigate by having the conductor agent read each specialist's role contract file rather than embedding it.

---

## Validation Architecture

This phase IS the spine's integration test. Validation splits into deterministic (pytest, no LLM) and agent-judgement (UAT).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (confirmed in use from Phase 1) |
| Config file | Check for `pytest.ini` / `pyproject.toml [tool.pytest]` in ba-tools dir |
| Quick run command | `pytest .agents/ba-daily-operators/ba-tools/tests/ -x -q` |
| Full suite command | `pytest .agents/ba-daily-operators/ba-tools/tests/ -v` |

### Part A — Deterministic / Automatable (pytest, no LLM)

These test the ba-tools state-machine directly, without invoking the agent conductor.

#### Test 1: uc-status next_step correctness

**Success criterion (UC-03):** `uc-status` returns `next_step = first step not complete` over canonical order.

**Simulated pipeline approach:** Write STATE.md programmatically with known pipeline states, call `uc_status.run()` directly, assert `next_step`.

| Fixture | Expected next_step |
|---------|--------------------|
| All steps `pending` | `srs-analyze` |
| srs-analyze `complete`, rest `pending` | `mermaid` |
| srs-analyze + mermaid `complete`, rest `pending` | `mockup` |
| srs-analyze + mermaid + mockup `complete`, index `pending` | `index` |
| All four `complete` | `done` |
| srs-analyze `failed`, rest `pending` | `srs-analyze` |
| srs-analyze `complete`, mermaid `failed` | `mermaid` |
| Kill mid-step: mermaid `in_progress` | `mermaid` |

**Coverage:** Covers all UC-03 criteria 1–3 (resume, gate-fail, kill).

**Sampling rate:** Run on every commit touching uc_status.py or state_store.py.

#### Test 2: state advance / pipeline_step write

**Success criterion:** `state patch --data '{"pipeline_step":"mermaid","pipeline_status":"complete"}'` correctly updates the Pipeline Steps table body; subsequent `uc-status` returns `next_step = mockup`.

**Approach:** Use existing state_store tests (Phase 1 pattern). New test: round-trip patch → uc-status read.

**Sampling rate:** Every commit touching state_store.py or state_cmd.py.

#### Test 3: resume-from-failed-step

**Success criterion (UC-03 criterion 2):** Gate FAIL on mermaid step → conductor sets `pipeline_status = failed` → `uc-status next_step = mermaid` → `resume` route enters at `mermaid`.

**Approach (no LLM):** Simulate gate failure by patching STATE.md with `mermaid = failed` directly; assert `next_step = mermaid`. The resume route's re-entry logic is tested by asserting it calls `uc-status` and follows `next_step`.

**Sampling rate:** Per-wave.

#### Test 4: gate-reject leaves recoverable state

**Success criterion (UC-03 criterion 3 + D-RES1):** After simulated gate FAIL, STATE.md is recoverable: previous complete steps remain `complete`, failed step is `failed`, subsequent steps are `pending`.

**Approach:** Write srs-analyze = `complete`, mermaid = `failed`, mockup = `pending`, index = `pending`. Assert `uc-status steps` matches exactly; assert `next_step = mermaid`.

**Sampling rate:** Per-wave.

#### Test 5: concurrent-write no-clobber

**Success criterion (TOOL-03 + D-TEST):** Two concurrent `state patch` calls do not clobber each other's pipeline_step write; FileLock serializes them.

**Approach:** Reuse Phase 1 lockfile test pattern. Two threads each call `merge_state` with different `pipeline_step` values; assert final STATE.md contains both writes (second overwrote first on same step, or both wrote different steps — depends on test design).

**Phase 1 pattern reference:** Check `.agents/ba-daily-operators/ba-tools/tests/` for existing concurrent-write tests.

**Sampling rate:** Per-wave (slow test — uses threading).

#### Test 6: D-G2 orphan/self-coverage predicate

**Success criterion:** After `index update` following a `trace write --kind mermaid` with known req_ids, `orphans` list is empty and none of the written req_ids appear in `gaps`.

**Approach:** Create fixture trace records (`traces/srs-test.json` with FR-001/FR-002; `traces/mermaid-test.json` with req_ids FR-001). Run `index update`. Assert `orphans == []` and `"FR-001" not in gaps`.

Negative case: trace record with REQ-ID not in srs traces → assert `orphans == ["XX-999"]`.

**Sampling rate:** Per-commit touching index_cmd.py or trace_cmd.py.

#### Test 7: WR-02 scaffold seed verification

**Success criterion (corrected D-RES3):** `ensure_scaffold` creates STATE.md with all four pipeline rows. `uc-status` on a freshly scaffolded project returns `next_step = srs-analyze` and `steps = {srs-analyze: pending, mermaid: pending, mockup: pending, index: pending}`.

**Approach:** Call `ensure_scaffold(tmp_path)`, then `uc_status.run()` against it.

**Sampling rate:** Per-commit touching scaffold.py.

### Part B — Agent-Judgement / UAT (non-deterministic)

These cannot be scripted. They require a real conductor invocation.

#### UAT-1: End-to-end deliver (UC-01)

**Success criterion:** One UC (fixture use case) delivered end-to-end — SRS.md, diagram.md, mockup artifact, and INDEX.md all exist with the same slug; INDEX.md has `ok` status for the UC's req_ids; no orphans.

**Fixture UC:** A minimal pre-written UC file (UC-001 with 2–3 simple requirements) stored in `tests/fixtures/` as a deterministic input.

**Not scripted** — agent authoring is non-deterministic. Documented as UAT criteria with a human verifier running `ba-tools uc-status` and `ba-tools index update` to check machine-verifiable outcomes.

#### UAT-2: Gate-reject → resume (UC-03 criteria 2)

**Success criterion:** After the conductor stops on a gate failure (simulated or real), running `ba-uc --route resume --uc <slug>` re-enters at the failed step and completes the pipeline. `uc-status next_step = done` at the end.

**Approach:** Can be partly automated if the conductor exposes a `--inject-failure` flag, but in v1 the most practical approach is to:
1. Manually break the SRS (e.g. add an ungrounded requirement) so verify exits 2.
2. Run conductor — confirm it stops and sets status `failed` on srs-analyze.
3. Fix the SRS, run `ba-uc --route resume` — confirm it completes.

#### UAT-3: Kill → resume (UC-03 criterion 3)

**Success criterion:** After a mid-step kill (Ctrl-C during mermaid step), `uc-status next_step = mermaid`; `ba-uc --route resume` completes the full pipeline.

**Approach:** Manual — interrupt the conductor mid-step, verify STATE.md is consistent, resume.

### ROADMAP Success Criteria Coverage (Nyquist assessment)

| ROADMAP Criterion | Tests | Coverage | Nyquist Sufficient? |
|-------------------|-------|----------|---------------------|
| 1. E2E deliver with gate after each step | UAT-1 + Test 6 (gate predicate) | Agent-run full path + deterministic gate logic | YES — agent path needed; machine checks gate predicate |
| 2. Gate-reject → uc-status next_step → resume continues | Tests 1,3,4 + UAT-2 | State-machine deterministic + agent resume | YES — state machine fully covered; resume re-entry deterministic |
| 3. Kill → recoverable state → resume completes | Tests 1,4,5 + UAT-3 | Concurrent-write + state consistency | YES — lockfile + state tests cover the machine contract; human verifies resume path |
| 4. Safety gate contract defined + plugin-enforced, no synthetic spine render | GATE-03 doc (Q5) | Documentation check only | PARTIAL — no automated test for "spine never fires Safety gate"; add a smoke test that runs ba-uc deliver on fixture and asserts no `.png`/`.svg` was written to .ba-ops/ |

**Gap:** No automated test for ROADMAP criterion 4 (no synthetic render on spine). Add: `assert not list(Path(".ba-ops").glob("**/*.png"))` after a UAT-1 run.

### Wave 0 Test Gaps

- [ ] `tests/test_uc_conductor_state.py` — covers Tests 1–5 (pipeline state-machine; reuse state_store fixture pattern from Phase 1)
- [ ] `tests/test_index_gate_predicate.py` — covers Test 6 (orphan + self-coverage D-G2)
- [ ] `tests/test_scaffold_all_four_rows.py` — covers Test 7 (WR-02 regression guard)
- [ ] Fixture file: `tests/fixtures/uc-001-test.md` — minimal UC for UAT-1/2/3

---

## Q7 / Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Pipeline step order | Custom enum/list | `state_store.PIPELINE_STEPS` — single source of truth (state_store.py:126) |
| Next-step computation | Custom parser | `uc_status._compute_next_step` — already handles all status variants |
| STATE.md write concurrency | Raw O_EXCL | `state_store.acquire_state_lock` (FileLock timeout=10) |
| INDEX.md write concurrency | Raw lock | `acquire_state_lock` re-exported for INDEX.md.lock (index_cmd.py:231) |
| Orphan detection | Custom trace parser | `index update` ok_json `orphans` field |
| Route validation | String match | `OPERATOR_ROUTES` table in init_cmd.py:27 |
| Index column coverage (D-G2) | New ba-tools command | Read `gaps` from `index update` output + check against step's own req_ids (extracted already by the trace write step) |

---

## Skill Layout Pattern (CDX)

From `.agents/skills/ba-mockup/SKILL.md` and `agents/openai.yaml` (confirmed):

**SKILL.md** — frontmatter `name` + `description` only; comment line pointing to workflow file. No body content.

**agents/openai.yaml** — nesting:
```yaml
interface:
  display_name: "..."
  short_description: "..."
  default_prompt: |
    ...explicit first steps...
policy:
  allow_implicit_invocation: false
```

The `ba-uc` skill must follow this exactly. `allow_implicit_invocation: false` on the conductor (CONTEXT.md, REQUIREMENTS.md CDX-02).

**ba-uc skill directory:** `.agents/skills/ba-uc/` (flat layout under repo root — discoverable by Codex recursive loader).

---

## Open Questions

1. **D-G2 self-coverage: parse INDEX.md vs check gaps list**
   - What we know: `index update` emits `gaps` (req_ids with no non-SRS coverage), `orphans`, `req_ids`, `stale`.
   - What's unclear: whether the conductor should parse INDEX.md matrix rows directly (simpler for column-specific coverage) or rely on the `gaps` list (requires storing step req_ids from trace write step).
   - Recommendation: use the `gaps` list approach — no file parse needed, all data in the JSON output. Store step req_ids from the artifact frontmatter extraction (already done in the workflow's trace write step).

2. **Failure-reason surface (D-RES1, Claude's Discretion)**
   - What we know: `state patch` can write arbitrary string values; `note` is an ALLOWED_KEY in state_store (state_store.py:46).
   - What's unclear: whether to write the failure reason to `STATE.md note` field (frontmatter) or a custom `## Gate Verdicts` table row (body).
   - Recommendation: write to `note` frontmatter key (already in ALLOWED_KEYS) AND add a row to the `## Gate Verdicts` table — both are low-cost and provide human-readable + machine-readable surfaces.

3. **Conductor workflow file: single file vs per-route extraction**
   - What we know: estimated 7–12 KB, well within DEFAULT 38 KB limit.
   - What's unclear: whether the four routes (deliver/resume/status/iterate) fit cleanly in a single file without confusion.
   - Recommendation: single file with `## Route: deliver`, `## Route: resume`, etc. — matches the ba-srs-analyze.md pattern exactly.

---

## Sources

All findings are from codebase source files. No external lookups performed per objective directive.

| File | Key findings |
|------|-------------|
| `05-CONTEXT.md` | Locked decisions D-G1/G2/INV/IN/RES1/2/3/TEST/SAFE; Claude's Discretion areas |
| `ba-srs-analyze.md` | Route list; `full` = extract→draft→verify→CoVe→trace+index; slug derivation |
| `ba-mermaid.md` | Route list; default `author`; `full` = author→trace→index |
| `ba-mockup.md` | Route list; default `full`; `full` = screen→trace→index; --fidelity validation |
| `uc_status.py` | PIPELINE_STEPS order; `_COMPLETE_STATUSES`; `_compute_next_step` logic |
| `state_store.py` | `PIPELINE_STEPS` tuple; `update_pipeline_step` no-op-when-absent; `merge_state` pipeline_* directive; ALLOWED_KEYS |
| `scaffold.py` | `_STATE_MD` template seeds all 4 rows including `index` at line 133 — WR-02 not present |
| `gates.md` | Quality gate sequence; Gate 1/2/3 contracts; escalation protocol; WARN semantics |
| `index_cmd.py` | ok_json fields: updated, req_ids, gaps, orphans, stale; `covered_by` not emitted |
| `resolve_route.py` | `ba-uc → deliver` registered; all operator defaults |
| `init_cmd.py` | `ba-uc: [deliver, resume, status, iterate]` registered |
| `.agents/skills/ba-mockup/SKILL.md` | CDX skill layout pattern (name+description frontmatter only) |
| `.agents/skills/ba-mockup/agents/openai.yaml` | interface.* + policy.allow_implicit_invocation nesting |

---

## RESEARCH COMPLETE
