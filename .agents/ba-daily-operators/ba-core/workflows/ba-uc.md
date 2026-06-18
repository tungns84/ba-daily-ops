---
operator: ba-uc
default_route: deliver
routes:
  - deliver
  - resume
  - status
  - iterate
---

# ba-uc Workflow

Deliver one use case end-to-end as a sequential agent loop: srs-analyze (full)
→ mermaid (full, explicit — NOT the default author route) → mockup (full) →
index update. A Quality gate runs after srs-analyze; an index-integrity gate
(D-G2) runs after mermaid and mockup. Pipeline status is written between steps:
`complete` only after the gate passes, `failed` on gate fail then STOP (D-RES1).
Resumable via uc-status (D-RES2).

**Determinism boundary:** `ba-tools` commands do ONLY file/command/hash-provable
work. All analysis, authoring, gate verdict judgement, and slug threading is
agent-owned. The CLI never calls an LLM.

**Sequential execution:** This is a Codex v1 operator — there is no autonomous
parallel subagent spawn. Each step runs sequentially; each step must complete
before the next begins.

**Pass paths, not content:** The workflow hands sub-operators the slug,
`requirements.json` path, and `--fidelity`. Sub-operators read their own inputs.
The conductor never forwards raw artifact bodies between steps.

---

## Route: deliver

End-to-end: srs-analyze (full) → mermaid (full) → mockup (full) → index update.
Gate after each step before writing pipeline status.

### Step 0 — Pre-flight

1. Run `ba-tools resolve-route ba-uc` to confirm the default route = `deliver`.
2. Validate `--uc` (required): must be `"<file>: ## UC-001. <name>"`. If absent or
   malformed, stop with error: "`--uc` is required and must be `\"<file>: ## UC-NNN. <name>\"`."
3. Validate `--fidelity` (required): must be `html` or `wireframe`. If absent or
   invalid, stop with error: "`--fidelity` is required and must be `html` or `wireframe`."
4. Run `ba-tools init ba-uc` for scaffold context.
5. Verify all four pipeline rows exist in `.ba-ops/STATE.md`. The scaffold seeds them
   (`srs-analyze`, `mermaid`, `mockup`, `index`) as `pending` — check for defensive
   presence only; do NOT patch scaffold rows.

### Step 1 — srs-analyze (full route)

1. Open `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` and follow
   the `full` route steps completely. Pass the source file from `--uc` (the `<file>`
   portion before the `: ##` separator).
2. After the srs full route completes: capture the derived slug from the srs step
   output (Phase 2 D-19 — slug derives from `--slug` if provided, else source
   filename slugify, else UC id). Thread this slug verbatim to every subsequent step.
3. **Quality gate (D-G1):** Check whether the CoVe loop converged.
   - If the srs `full` route emitted `non-convergence-escalation` (loop 3 still has
     FAIL findings): the gate has FAILED.
   - Run:
     ```
     ba-tools state patch --data '{"pipeline_step":"srs-analyze","pipeline_status":"failed"}'
     ```
     Then STOP. Do not proceed to Step 2.
   - If the srs `full` route converged (emitted `passed early` or `passed after <n>`):
     the gate has PASSED. Run:
     ```
     ba-tools state patch --data '{"pipeline_step":"srs-analyze","pipeline_status":"complete"}'
     ```

### Step 2 — mermaid (full route — NOT the default author route)

Open `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` and follow the
`full` route steps specifically. This is NOT the default `author` route — the
conductor must explicitly navigate to `## Route: full` in ba-mermaid.md because
the `author` route skips trace write and index update. Passing `--route full`
explicitly to ba-mermaid is required; relying on the default will use `author`.

Pass:
```
slug:       <slug from Step 1>
source_doc: .ba-ops/srs/<slug>/requirements.json
```

After the mermaid full route completes (trace write + index update done), collect:
- `step_trace_req_ids` — the req_ids passed to `ba-tools trace write --kind mermaid`
  in the full route (available from the artifact's frontmatter/comment extraction).
- `index_output` — JSON from `ba-tools index update` (stdout).

**Index-integrity gate (D-G2):**

```
FAIL if:
  len(index_output["orphans"]) > 0
  OR any(rid in index_output["gaps"] for rid in step_trace_req_ids)
```

- Gate FAILED → Run:
  ```
  ba-tools state patch --data '{"pipeline_step":"mermaid","pipeline_status":"failed"}'
  ```
  Then STOP. Do not proceed to Step 3.
- Gate PASSED → Run:
  ```
  ba-tools state patch --data '{"pipeline_step":"mermaid","pipeline_status":"complete"}'
  ```

### Step 3 — mockup (full route)

Open `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` and follow the
`full` route steps. The mockup default route IS `full` — no explicit route override
needed.

Pass:
```
slug:      <slug from Step 1>
fidelity:  <--fidelity value from conductor input>
```

`--fidelity` is forwarded verbatim from the conductor's input (D-IN).

After the mockup full route completes (trace write + index update done), collect:
- `step_trace_req_ids` — req_ids passed to `ba-tools trace write --kind mockup` in
  the full route (extracted from artifact req_ids header or frontmatter).
- `index_output` — JSON from `ba-tools index update` (stdout).

**Index-integrity gate (D-G2):**

```
FAIL if:
  len(index_output["orphans"]) > 0
  OR any(rid in index_output["gaps"] for rid in step_trace_req_ids)
```

- Gate FAILED → Run:
  ```
  ba-tools state patch --data '{"pipeline_step":"mockup","pipeline_status":"failed"}'
  ```
  Then STOP. Do not proceed to Step 4.
- Gate PASSED → Run:
  ```
  ba-tools state patch --data '{"pipeline_step":"mockup","pipeline_status":"complete"}'
  ```

### Step 4 — index (final canonical rebuild)

Run `ba-tools index update` as the final standalone step. This is an idempotent
full rebuild of INDEX.md from all trace records, ensuring the complete index is
consistent after all three prior trace writes.

```
ba-tools index update
```

After index update succeeds, run:
```
ba-tools state patch --data '{"pipeline_step":"index","pipeline_status":"complete"}'
```

**Delivery complete.** INDEX.md now reflects the full UC pipeline trace.

---

## Route: resume

Re-enter at the step indicated by `uc-status next_step` and re-run that step
from scratch.

**Steps:**

1. Run `ba-tools uc-status` (or `ba-tools state uc-status`) to determine `next_step`.
2. If `next_step == "done"`: the pipeline is already complete. Report status and stop.
3. Re-enter the `deliver` route at the step matching `next_step`. Re-run that step
   and all subsequent steps from scratch (D-RES2 — resume re-runs from next_step,
   not from start).
4. Follow the same gate + state write protocol as the `deliver` route for each
   remaining step.

**Note:** Resume always re-runs the step from scratch. It does not attempt to
continue a partially-completed step.

---

## Route: status

Surface the current pipeline state without modifying any files.

**Steps:**

1. Run `ba-tools uc-status` to read the current pipeline step statuses and `next_step`.
2. Display the pipeline status table from the JSON output.

**Output:** Pipeline status JSON to stdout; no file writes.

---

## Route: iterate

Re-run the full pipeline on an existing slug, folding prior discoveries into the
srs re-draft and re-running mermaid + mockup fresh.

**Steps:**

1. Confirm the slug exists: `.ba-ops/srs/<slug>/requirements.json` must be present.
2. Run `ba-tools discovery` to surface accumulated findings for this slug.
3. Re-run the `deliver` route from Step 1 (srs-analyze full route), passing prior
   critic findings and discovery entries as context to the srs-writer for the
   re-draft.
4. Apply the same gate + state write protocol for each step.

**Note:** `iterate` always re-runs the full pipeline. Use `resume` to re-enter at
the last failed/pending step.

---

## Gate contract reference

See `.agents/ba-daily-operators/ba-core/references/gates.md` for:
- Quality gate (Gate 1/2/3 + escalation + WARN semantics) — applies after srs-analyze
- Safety Gate Contract (GATE-03, Clauses 1-4) — plugin-enforced; spine is exempt

## Agent prompt

Conductor role: `.agents/ba-daily-operators/ba-core/agents/ba-uc-conductor.md`
