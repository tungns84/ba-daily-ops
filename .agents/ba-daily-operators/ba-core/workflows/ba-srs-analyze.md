---
operator: ba-srs-analyze
default_route: full
routes:
  - extract
  - draft
  - lint
  - verify
  - full
  - iterate
---

# ba-srs-analyze Workflow

Turn an arbitrary source document into atomic, grounded, verifiable requirements
(`requirements.json`) and a rendered IEEE-830 SRS.md, quality-gated by
`ba-tools verify` and a fresh-context `ba-critic` Chain-of-Verification (CoVe) loop.

**Determinism boundary:** `ba-tools` commands do ONLY file/command/hash-provable
work (citation checks, rendering, hashing, trace writes, index updates). All
analysis, authoring, and judgement is agent-owned. The CLI never calls an LLM.

**Sequential execution:** This is a Codex v1 operator — there is no autonomous
parallel subagent spawn. The writer step and the critic step run as a single
sequential agent loop; each step must complete before the next begins.

**Pass paths, not content:** The workflow hands agents file paths and a small
manifest. Agents Read the files they need. The workflow never forwards raw
artifact bodies between steps.

---

## Route: extract

Extract source document sections into `.ba-ops/srs/<slug>/` for downstream steps.

**When to use:** Before `draft` on a new source, or standalone to inspect
section splits.

**Steps:**

1. Determine the slug:
   - Use `--slug` if provided; otherwise derive from the source filename
     (slugify: lowercase, hyphens); or the UC id if the source is UC-shaped.
   - This is deterministic — `ba-tools` owns slug derivation (D-19).

2. Check if the source is UC-shaped (has a structured UC header with id/title/actors):
   - **UC-shaped source:** run `ba-tools extract-uc <source_path> --slug <slug>`
     to split sections AND parse UC identity.
   - **Generic source (meeting notes, brief, project spec, freeform Markdown/text):**
     Agent performs section extraction using the document's Markdown heading
     boundaries (as defined by `markdown_sections` logic — stop at same-or-higher
     heading level). There is **no generic `ba-tools extract` command in v1**;
     generic extraction is agent-owned. Write each section to
     `.ba-ops/srs/<slug>/sections/<section-slug>.md`.

3. Confirm sections exist under `.ba-ops/srs/<slug>/sections/` before continuing.

**Output:** Section files under `.ba-ops/srs/<slug>/sections/`.

---

## Route: draft

Author `requirements.json` and `analysis.md` from the extracted sections.

**When to use:** After `extract`, or standalone if sections already exist.

**Steps:**

1. Open `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md` and follow
   the writer role contract.

2. Run the ba-srs-writer step with this payload (paths only):
   ```
   source_path:  <path to source document>
   sections_dir: .ba-ops/srs/<slug>/sections/
   slug:         <slug>
   route:        draft
   ```

3. The writer emits:
   - `.ba-ops/srs/<slug>/requirements.json` — canonical requirements list
   - `.ba-ops/srs/<slug>/analysis.md` — writer working notes (NOT shared with critic)

4. After the writer step completes, run `ba-tools render srs --slug <slug>` to
   produce `SRS.md` and `REQUIREMENTS.md` deterministically from the JSON.

**Output:** `requirements.json`, `SRS.md`, `analysis.md` under `.ba-ops/srs/<slug>/`.

---

## Route: lint

Run lint-requirements advisory report (non-blocking, always exit 0).

**When to use:** Standalone quality check without the hard gate.

**Steps:**

1. Run `ba-tools lint-requirements .ba-ops/srs/<slug>/requirements.json`
   (or provide the absolute path).
2. Review WARN findings for: ambiguity, non-atomic statements, weak words,
   missing classification.
3. This step never blocks — it is advisory only (D-07/D-08).

**Output:** Console WARN report; no file changes.

---

## Route: verify

Run the deterministic hard gate (citation-exists + lint fold). Exit 2 on any FAIL.

**When to use:** After `draft`, or standalone to re-gate existing requirements.

**Steps:**

1. Run `ba-tools verify --reqs .ba-ops/srs/<slug>/requirements.json
   --reqs-format json --source <source_path>`.
2. If exit code is 2: inspect `failures[]` in the JSON envelope. Each entry
   has a `code` (e.g. `CITATION_NOT_FOUND`) and `req_id`. Fix the offending
   requirements in `requirements.json` (re-run the writer, or edit manually)
   and re-verify.
3. Exit 0 = all `stated` requirements have real ≥12-char verbatim spans in
   the cited source section.

**Output:** JSON envelope `{ok, failures[]}` to stdout; exit 0 or 2.

---

## Route: full

End-to-end: extract → draft → verify → ba-critic CoVe loop (≤3) → trace + index.

This is the default route (`ba-tools resolve-route ba-srs-analyze` returns `full`).

**Steps:**

### Step 1 — Resolve route and slug

1. Run `ba-tools resolve-route ba-srs-analyze` to confirm the default route.
2. Determine the slug per the extract route rules (D-19).
3. Run `ba-tools init ba-srs-analyze` for scaffold context (creates `.ba-ops/`
   subdirectories including `traces/`; returns config, routes, state).

### Step 2 — Extract sections

Follow the **extract route** steps above (UC-shaped → `extract-uc`; generic →
agent-owned section extraction to `.ba-ops/srs/<slug>/sections/`).

### Step 3 — Draft requirements (ba-srs-writer step)

Run the ba-srs-writer step with this payload:
```
source_path:  <path to source document>
sections_dir: .ba-ops/srs/<slug>/sections/
slug:         <slug>
route:        full
```

Open `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md` for the
writer role contract. The writer emits `requirements.json` + `analysis.md`.

After the writer step, run:
- `ba-tools render srs --slug <slug>` → produces `SRS.md` + `REQUIREMENTS.md`

### Step 4 — Verify (deterministic hard gate)

Run `ba-tools verify --reqs .ba-ops/srs/<slug>/requirements.json
--reqs-format json --source <source_path>`.

- Exit 2 → fold the `failures[]` back to the ba-srs-writer for a re-draft
  (return to Step 3 with failures in context); re-verify; continue to Step 5.
- Exit 0 → proceed to the CoVe loop.

### Step 5 — CoVe loop (≤3 revisions)

This loop runs sequentially. Do not run writer and critic concurrently.

For n = 1, 2, 3:

1. **Run the ba-critic step** (FRESH CONTEXT, sequential — not a parallel spawn):
   Open `.agents/ba-daily-operators/ba-core/agents/ba-critic.md` for the critic
   role contract. Pass this payload (paths only):
   ```
   source_path:            <path to source document>
   requirements_json_path: .ba-ops/srs/<slug>/requirements.json
   ```
   The critic receives ONLY these two paths. Do NOT pass `analysis.md`,
   `SRS.md`, or any writer working notes to the critic (D-21, G3).

2. The critic emits a JSON findings array:
   ```json
   {
     "converged": false,
     "findings": [
       {
         "req_id": "FR-001",
         "severity": "fail",
         "question": "Does the source assert this obligation?",
         "answer": "The source mentions X but not Y as stated.",
         "verdict": "ungrounded"
       }
     ]
   }
   ```

3. **Check convergence:** Count new FAIL-severity findings (severity == "fail")
   that were not present in the prior loop. Converged = zero new FAIL findings
   (D-11). WARN findings are logged but non-blocking.

4. **If converged:**
   - Log: `"passed early"` if n == 1; `"passed after <n>"` if n > 1.
   - Break out of the loop → proceed to Step 6.

5. **If not converged and n < 3:**
   - Pass the FAIL findings back to ba-srs-writer for a re-draft (return to
     the writer step with findings in context).
   - Re-run `ba-tools verify` (Step 4) after re-draft. If verify fails, fold
     those failures into the re-draft before calling the critic again.
   - Increment n; continue loop.

6. **If not converged after loop 3:**
   - Log: `"non-convergence-escalation"`.
   - Run `ba-tools confirm` and surface the open FAIL findings to the user.
   - **Stop. Do not proceed to Step 6 (trace + index) until the human resolves.**
   - Never emit "converged" or proceed with open FAILs (D-10, G2).

**Convergence vocabulary (log to STATE.md):**
- `"passed early"` — converged on loop 1
- `"passed after <n>"` — converged on loop n (n > 1)
- `"non-convergence-escalation"` — loop 3 still has FAIL findings; human required

### Step 6 — Trace write + index update (only on convergence)

Only reach this step if the CoVe loop converged.

1. Run `ba-tools trace write --kind srs --slug <slug>
   --artifact .ba-ops/srs/<slug>/SRS.md
   --source <source_path>
   --req-ids .ba-ops/srs/<slug>/requirements.json`

2. Run `ba-tools index update`
   (rebuilds INDEX.md with gap/orphan/stale detection — D-13).

3. Run `ba-tools state advance` to record the gate verdict in STATE.md
   (lockfile-guarded via filelock, FileLock(timeout=10)).

**Output:** Converged `requirements.json` + `SRS.md` + trace record + updated
`INDEX.md` + updated `STATE.md`.

---

## Route: iterate

Re-run on an existing slug, folding prior `ba-tools discovery` entries and
critic findings into a fresh draft. Use after new discoveries or source updates.

**Steps:**

1. Confirm the slug exists: `.ba-ops/srs/<slug>/requirements.json` must be present.

2. Run `ba-tools discovery` to surface accumulated findings for this slug.

3. Run the ba-srs-writer step with this payload:
   ```
   source_path:  <path to source document>
   sections_dir: .ba-ops/srs/<slug>/sections/
   slug:         <slug>
   route:        iterate
   ```
   Pass the prior critic findings and discovery entries as context so the writer
   addresses them in the re-draft.

4. Run `ba-tools render srs --slug <slug>` to regenerate `SRS.md`.

5. Continue from the **verify** step (Step 4) of the `full` route, then the
   CoVe loop, then trace + index on convergence.

**Output:** Updated `requirements.json`, `SRS.md`, trace record, `INDEX.md`.

---

## Quality gate contract

See `.agents/ba-daily-operators/ba-core/references/gates.md` for the complete
verify → ba-critic CoVe → trace + index contract, including escalation protocol
and WARN non-blocking semantics.

## Agent prompts

- Writer role: `.agents/ba-daily-operators/ba-core/agents/ba-srs-writer.md`
- Critic role: `.agents/ba-daily-operators/ba-core/agents/ba-critic.md`
