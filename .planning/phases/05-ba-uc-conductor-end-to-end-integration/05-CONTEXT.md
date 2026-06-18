# Phase 5: ba-uc Conductor + End-to-End Integration - Context

**Gathered:** 2026-06-18
**Status:** Ready for planning

<domain>
## Phase Boundary

One use case is delivered **end-to-end** by the `ba-uc` conductor running the
three spine operators as a **single sequential agent loop**
(`srs-analyze → mermaid → mockup → index`) with a **gate after each step** and
full **resumability via `uc-status`**. This phase **doubles as the spine's
integration test** (resume-from-step, gate-reject recovery, concurrent-write).

`ba-uc` is the **only operator that invokes others** — it reads each spine
operator's workflow file and runs them in sequence; it owns only the gate +
state between steps. Everything else is coupled solely through the `.ba-ops/`
REQ-ID traceability matrix (DESIGN §2).

**Phase 5 requirements (4):** UC-01 (deliver ONE UC end-to-end:
srs-analyze → mermaid → mockup → index), UC-02 (single sequential agent loop,
Quality gate between steps), UC-03 (resumable via `uc-status`; routes
deliver/resume/status/iterate, default `deliver`), GATE-03 (Safety gate
contract defined + documented as plugin-enforced; no synthetic render on spine).

**Components delivered this phase:**
1. `ba-uc` skill (CDX pattern) — flat `.agents/skills/ba-uc/` SKILL.md
   (`name`+`description` only) + `agents/openai.yaml` (`interface.*`,
   `policy.allow_implicit_invocation: false`), copying the Phase-2/3/4 layout.
2. `ba-uc` thin conductor workflow — routes `deliver` (default) / `resume` /
   `status` / `iterate`; reads each spine operator's workflow and runs them
   sequentially, applying the per-step gate + `state` write between steps.
3. A conductor agent prompt (`ba-core/agents/`) — drives the sequential loop,
   threads the shared slug + `--fidelity`, enforces gate verdicts.
4. **GATE-03 Safety-gate contract doc** in `ba-core/references/` — render-CLI-only,
   path-traversal + injection scan, `.png`/`.svg` extension check; marked
   plugin-enforced / spine-exempt (DESIGN §6).
5. Integration test suite (pytest over the ba-tools spine state-machine) +
   an agent-run E2E UAT on a fixture UC.
6. Reuse of existing ba-tools (`uc-status`, `state advance` w/ `pipeline_step`,
   `trace write`, `index update`, the sub-operator workflows + their gates) —
   **likely zero new ba-tools commands** (mirrors ba-mockup); confirm in planning.

**Explicitly NOT this phase:** the deferred plugins (`ba-make-diagram` draw.io,
`ba-uc-delivery` DOCX, `ba-backlog-grooming`) and their actual Safety-gate
**enforcement** (GATE-03 is contract-only here); any synthetic render on the
spine; true fresh-context subagent spawn (Codex v1 = one sequential loop;
v2 Claude/Task model); multi-UC batch delivery.

</domain>

<decisions>
## Implementation Decisions

### Per-step gate semantics (Area 1)
- **D-G1:** The "gate after each step" is **operator-appropriate**, not a single
  uniform gate:
  - **After `srs-analyze`** — the full **Quality gate** (`ba-tools verify` →
    `ba-critic` CoVe loop ≤3), exactly as defined in `ba-core/references/gates.md`
    (Phase 2). This is the only step with citation-bearing requirements.
  - **After `mermaid` and `mockup`** — an **index-integrity check**: run
    `ba-tools index update` and assert the step introduced **no new orphan** and
    the step's own `req_ids` **landed in its INDEX column**. This is the
    hash-provable, determinism-boundary-respecting "gate" for non-SRS steps —
    reuses Phase 2/3/4 machinery, **no new check, no new ba-tools command**.
  - So ROADMAP criterion 1 ("Quality gate run after each step") = full Quality
    gate for srs, traceability-integrity gate for the diagram/mockup steps.
    (Reconciles DESIGN §2 "Quality gate after srs-analyze" with the ROADMAP's
    "after each step" — the diagram/mockup steps get the strongest *applicable*
    provable check.)
- **D-G2:** The index-integrity gate **FAILs** (stops the conductor) iff the step
  **introduced an orphan** (cited a REQ-ID absent from `requirements.json`) **OR**
  the step's **own `req_ids` did not appear** in its INDEX column (artifact
  didn't actually trace). **Gaps in OTHER columns are ignored** — a gap is
  *expected* mid-pipeline (e.g. the mockup column is empty until the mockup step
  runs), so a gap is **never** a stop condition. Exact fail predicate is read
  from `index update`'s existing output (orphan list + per-column coverage).

### Step invocation, routes, slug + fidelity threading (Area 2)
- **D-INV:** The conductor **reads each spine operator's workflow file and
  follows it inline**, sequentially (Codex v1 — no subagent spawn; independence
  by instruction per PROJECT.md caveat). The conductor **reuses the sub-workflows
  verbatim** and owns **only** the per-step gate (D-G1) + the `state` write
  between steps. Exact route per step is reconciled by the planner against the
  actual workflow bodies, within this principle:
  - `srs-analyze` is driven such that **its** Quality gate runs (its `full`
    route already embeds verify + ba-critic + trace + index).
  - `mermaid` / `mockup` are driven to **author + trace** (their `full` routes
    already do author→trace→index; the conductor wraps each with the D-G1/D-G2
    index-integrity gate). `index` is the final canonical step.
  - `index update` is **idempotent** (full rebuild from trace records), so any
    redundant per-step index updates are harmless.
- **D-IN:** Conductor input is **`ba-uc --uc "<file>: ## UC-001. <name>"
  --fidelity html|wireframe`**:
  - **`srs-analyze` runs first and derives the slug** (Phase 2 D-19: explicit
    `--slug` → source filename slugify → UC id). The conductor **captures that
    slug from the srs step output** and **threads it verbatim** to mermaid,
    mockup, and index — **one shared slug across all four steps**.
  - **`--fidelity` is required on `ba-uc`** (the mockup step needs it) and is
    **forwarded to the mockup step**. mermaid diagram-type is left to the agent
    default (optional `--diagram-type` not surfaced on the conductor unless the
    planner finds cause).

### Resume / fail-stop / kill-recovery (Area 3)
- **D-RES1:** A step's pipeline status is set to **`complete` strictly after its
  gate passes**. On **gate FAIL** the conductor sets status **`failed`** (an
  explicit non-complete value that surfaces the failure) and **STOPs**; a **kill
  mid-step** leaves the row at `pending` / `in_progress`. In all cases the step
  is **non-complete**, so `uc-status` `next_step` (= first step not `complete`)
  **lands on that step** (UC-03 criteria 2 & 3). Earlier complete steps are never
  clobbered. The failure reason is surfaced (STATE.md note and/or uc-status field
  — exact surface is planner's call).
- **D-RES2:** The **`resume` route re-enters at `uc-status`'s `next_step` and
  re-runs that step from scratch** (a failed step's partial artifacts are
  overwritten — per-slug authoring is idempotent), then proceeds forward through
  the remaining steps to a fully-traced UC. Resume does **not** skip ahead past a
  non-complete step.
- **D-RES3:** The conductor **guarantees all four pipeline rows exist** —
  `srs-analyze`, `mermaid`, `mockup`, **and `index`** — in the STATE.md Pipeline
  Steps table **before** writing statuses. The current `scaffold.py` seeds only
  the first three rows, and `pipeline_step` **silently no-ops** when the row /
  section is absent (tech-debt **WR-02**). Planner decides the mechanism:
  patch `scaffold.py` to seed the `index` row, or have the conductor seed/repair
  the row defensively (or both). This closes WR-02 for the conductor path.

### Integration test + GATE-03 Safety contract (Area 4)
- **D-TEST:** Verification splits provable-from-judgement:
  - **Automatable pytest** (deterministic, no LLM): drive `ba-tools` through a
    **simulated pipeline** — `state advance` / `pipeline_step` per step,
    `uc-status` `next_step` correctness, **resume-from-failed-step**,
    **gate-reject stops + leaves recoverable state**, **concurrent-write
    no-clobber** (reuse Phase 1 lockfile test pattern), and the index
    orphan / self-coverage predicate (D-G2).
  - **Agent-run E2E UAT**: the real conductor loop
    (`srs-analyze → mermaid → mockup` on a fixture UC) — non-deterministic agent
    authoring, so it is documented as UAT criteria, not scripted assertions.
- **D-SAFE:** GATE-03 is **contract-only** this phase. Document the Safety-gate
  contract as a **standalone discoverable doc in `ba-core/references/`** (extend
  `gates.md` with a Safety section, or a sibling `safety-gate.md` — planner's
  call): **render CLI only** (draw.io / `mmdc`), **path-traversal + injection
  scan** on `.ba-ops/` writes, **media extension == `.png`/`.svg`**, **no
  Pillow/SVG/screenshot synthetic** (DESIGN §6/§11). Explicitly scoped
  **"enforced by the deferred plugins; the spine invokes no render, so the
  conductor never fires the Safety gate."**

### Claude's Discretion (researcher / planner own these)
- Exact route driven per spine step inside `deliver` (within D-INV) — reconcile
  against the real `ba-srs-analyze.md` / `ba-mermaid.md` / `ba-mockup.md` bodies.
- Whether the conductor needs **any** new ba-tools surface (expected: none;
  confirm `uc-status` + `state` + the existing trace/index cover it).
- The `iterate` route body for the conductor (re-run an existing UC folding
  `discovery` entries — analogous to srs-analyze `iterate`, D-16).
- The exact `failed` status string + how the failure reason surfaces
  (STATE.md note vs a `uc-status` field).
- WR-02 fix mechanism (patch `scaffold.py` seed vs conductor self-seed the
  `index` row).
- The GATE-03 doc location (extend `gates.md` vs new `safety-gate.md`) and exact
  wording.
- Conductor workflow **byte budget** — if the `deliver` orchestration exceeds the
  DEFAULT < 38,000 B tier, extract per-route bodies (`LARGE` < 54,000 B applies
  to full orchestration per DESIGN §7).
- `openai.yaml` `interface.*` wording + keyword-dense SKILL.md `description`.
- Test-fixture design for the integration suite (the simulated-pipeline state
  fixtures + the E2E UAT fixture UC).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture spec (source of truth)
- `DESIGN.md` — repo root. Most relevant Phase-5 sections: **§2** (operator
  relationships — `ba-uc` is the only operator that invokes others; "one agent
  loop; Quality gate after srs-analyze"), **§3** (SKILL.md + `openai.yaml` flat
  layout; `ba-uc` skill dir; `allow_implicit_invocation: false` on the
  conductor), **§4** (thin-orchestrator pattern, route table — `ba-uc` →
  `deliver, resume, status, iterate`, default `deliver`; "pass paths not
  content"), **§5** (determinism boundary — conductor orchestrates, agents
  author, ba-tools proves), **§6** (the three gates — **Safety gate row** is the
  GATE-03 contract source; Quality gate + ba-critic), **§7** (byte budgets —
  DEFAULT < 38,000 B, LARGE < 54,000 B), **§8** (`.ba-ops/` spine, INDEX matrix),
  **§11** (non-negotiables: real render CLIs only, no synthetic image, no
  hard-coded paths). §10 "DONE" markers are aspirational, not current state.

### Requirements & scope
- `.planning/REQUIREMENTS.md` — REQ-ID registry; Phase-5 requirement text
  UC-01/02/03 + GATE-03; Out-of-Scope table (no synthetic render, implicit
  invocation off on conductor, plugins off the spine).
- `.planning/ROADMAP.md` — Phase 5 goal + 4 success criteria (the TRUE-conditions
  the verifier checks: end-to-end deliver w/ gate after each step; gate-reject →
  uc-status next_step → resume continues; kill → recoverable state → resume
  completes; Safety gate contract defined + plugin-enforced, no synthetic spine
  render).
- `.planning/PROJECT.md` — v1 daily spine; **Codex caveat** (no autonomous
  cross-skill spawn → `ba-uc` runs specialists as one sequential agent loop;
  ba-critic independence preserved by instruction); core value = REQ-ID
  traceability across artifacts.

### Gate contract (the Quality gate this phase reuses + the Safety gate it defines)
- `.agents/ba-daily-operators/ba-core/references/gates.md` — the authoritative
  Quality-gate contract (verify → ba-critic CoVe ≤3 → trace+index → state
  advance; escalation protocol; WARN semantics). **The conductor reuses this
  verbatim for the srs-analyze step gate (D-G1)** and **extends this file (or a
  sibling) with the GATE-03 Safety-gate contract (D-SAFE).**

### Spine operators the conductor invokes (read the workflows + the agent prompts)
- `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md` — the srs step;
  its `full` route embeds verify + ba-critic + trace + index. Slug derivation
  (Phase 2 D-19) happens here → the conductor captures the slug from here (D-IN).
- `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md` — the mermaid step
  (`full` = author→trace write→index update; `--source-doc` = srs
  `requirements.json`). Conductor wraps with the index-integrity gate (D-G1/G2).
- `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md` — the mockup step
  (`full` = author→trace→index; `--fidelity` required). Conductor forwards
  `--fidelity` here (D-IN).
- `.agents/ba-daily-operators/ba-core/agents/` — `ba-srs-writer.md`,
  `ba-critic.md`, `ba-diagrammer.md`, `ba-mockup-author.md` — the role contracts
  the sequential loop drives. The new conductor agent prompt lands here too.

### Phase 1 ba-tools the conductor drives (reuse as-is; confirm no new command)
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/uc_status.py` — **the
  resumability engine.** Pure read: parses the "## Pipeline Steps" table, computes
  `next_step` = first step not in `{complete, completed, done}` over canonical
  order `srs-analyze → mermaid → mockup → index`. Drives D-RES1/D-RES2.
- `.agents/ba-daily-operators/ba-tools/ba_tools/state_store.py` —
  `PIPELINE_STEPS = ("srs-analyze","mermaid","mockup","index")`;
  `update_pipeline_step` (sets a row's status cell); `state advance` is
  lockfile-guarded (`FileLock(timeout=10)`). **WR-02:** `pipeline_step` silently
  no-ops when the row / section is absent → D-RES3 must ensure all 4 rows exist.
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/state_cmd.py` — the
  `state update|patch|advance` surface incl. `--pipeline-step`/`--pipeline-status`
  directive keys the conductor writes between steps.
- `.agents/ba-daily-operators/ba-tools/ba_tools/scaffold.py` — seeds the Pipeline
  Steps table (lines ~130-132 seed srs-analyze/mermaid/mockup — **NOT `index`**;
  the WR-02 / D-RES3 gap to close); `.ba-ops/` subdir seeding.
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/trace_cmd.py` +
  `index_cmd.py` — `trace write` (per-kind record + source/statement hash) and
  `index update` (gap/orphan/stale + per-column coverage) — the D-G2 fail
  predicate is read from `index update`'s output. **Reuse as-is.**
- `.agents/ba-daily-operators/ba-tools/ba_tools/commands/resolve_route.py`
  (`ba-uc → deliver` **already registered**) + `init_cmd.py` (`OPERATOR_ROUTES`
  `ba-uc: [deliver, resume, status, iterate]` **already registered**).
- `.agents/ba-daily-operators/ba-tools/ba_tools/repo.py` (`resolve_under_root` /
  `is_within_root`), `output.py` (`ok_json`), `errors.py` (`BaToolsError`,
  exit 2) — reuse for any new path inputs / output contract.

### Sibling-operator context (the build template this phase mirrors)
- `.planning/phases/04-ba-mockup-operator/04-CONTEXT.md` — the most recent spine
  operator; **established "zero new ba-tools command" for an operator** (D-05a).
  The conductor likely follows the same shape (orchestration-only).
- `.planning/phases/03-ba-mermaid-diagram-operator/03-CONTEXT.md` +
  `.planning/phases/02-ba-srs-analyze-quality-gate-traceability-core/02-CONTEXT.md`
  — the skill/workflow/agent layout, slug threading (D-19), trace/index contract
  (D-04/D-05), and the Quality-gate authority (D-10/D-11) the conductor reuses.

### Tech stack (verified research)
- `CLAUDE.md` (repo root) — Python 3.11+ stdlib-first, `sys.executable`, paths
  under `--repo-root`; Codex skill contract (SKILL.md `name`+`description` only;
  `openai.yaml` `interface.*` + `policy.*` nesting); byte budgets (AGENTS.md /
  eager refs < 32,768 B; DEFAULT workflow < 38,000 B; LARGE < 54,000 B).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`uc_status.py`** — the resumability read engine; `next_step` over the static
  spine order. No change needed; the conductor consumes it for `resume`/`status`.
- **`state_store.py` / `state_cmd.py`** — `pipeline_step`+`pipeline_status`
  directives + lockfile-guarded `advance`; the conductor writes step status
  between steps via this. **WR-02 caveat** (no-op when row absent) → D-RES3.
- **`trace_cmd.py` / `index_cmd.py`** — the conductor's per-step gate (D-G2)
  reads `index update` output (orphan list, per-column coverage). Reuse as-is.
- **`resolve_route.py` / `init_cmd.py`** — `ba-uc` routes + default `deliver`
  **already registered in Phase 1** — no additive change needed.
- **The three spine workflows + their agent prompts + `gates.md`** — the
  conductor reads and runs them; it adds orchestration, not new spine behavior.
- **Phase 1 concurrent-write lockfile test pattern** — the template for the
  D-TEST concurrent-write integration test.

### Established Patterns
- Skill = flat `.agents/skills/<op>/` (SKILL.md `name`+`description` only) +
  `agents/openai.yaml` (`interface.*`, `policy.allow_implicit_invocation:false`)
  + thin workflow `ba-core/workflows/<op>.md` resolving route→steps + agent
  prompt `ba-core/agents/<role>.md`. The conductor follows this exactly.
- "Pass paths, not content" — the conductor threads slug + paths between steps,
  never raw artifact content (DESIGN §4).
- ba-tools proves (state/trace/index/uc-status); agents author + judge. The
  conductor is pure orchestration over this boundary — **expected: zero new
  ba-tools command** (confirm in planning; matches Phase 4).
- A step is `complete` only after its gate passes (D-RES1) — the gate-before-
  advance discipline already used by the srs `full` route's Gate 3.

### Integration Points
- The conductor is the **only operator that invokes others** — it sits atop the
  whole `.ba-ops/` spine, reading `srs/<slug>/`, `mermaid/<slug>/`,
  `mockup/<slug>/` and rebuilding INDEX.md, threading one slug end-to-end.
- This phase is the **integration surface** the milestone audit's broken E2E flow
  ("srs-analyze → mermaid → mockup → index") finally closes — it proves the
  Phase 2 trace/index contract is consumed correctly by all downstream operators.

</code_context>

<specifics>
## Specific Ideas

- The conductor's value is **traceability end-to-end on one slug**: a single UC
  enters, and SRS + diagram + mockup all cite REQ-IDs that resolve in one
  INDEX.md with no orphans. If everything else slips, that spine must work.
- **Resumability is the differentiator**: `uc-status` already computes
  `next_step` deterministically; the conductor's job is to keep STATE.md honest
  (complete-after-gate-only) so a kill or gate-reject is always recoverable.
- **No synthetic render, ever** — the spine invokes no render CLI; GATE-03 is a
  contract for the deferred plugins, and the conductor never fires it (DESIGN §11).
- Expect **zero new ba-tools commands** — the deterministic surface (uc-status,
  state, trace, index, the sub-operator workflows) is already complete; Phase 5
  is orchestration + contract docs + integration tests.

</specifics>

<deferred>
## Deferred Ideas

- **Actual Safety-gate enforcement** (render-CLI checks, extension validation,
  manifest `rendered_sha256 == embedded_sha256`) — lives in the deferred plugins
  (`ba-make-diagram`, `ba-uc-delivery`); GATE-03 here is contract-only.
- **True fresh-context subagent spawn** for the spine steps — Codex v1 is one
  sequential agent loop; the v2 Claude/Task transform delivers real fresh-context
  specialists (REQUIREMENTS V2-02).
- **Multi-UC batch delivery** (conductor over several UCs in one run) — v1 is one
  UC per `deliver` invocation; batching is a future capability.
- **Promoting the index-integrity gate to a new ba-tools `gate` command** — chose
  reusing `index update` output at the workflow level (D-G1/D-G2); promote only
  if the predicate proves to need hash-provable rigor of its own.
- **A `--diagram-type` surface on the conductor** — left to the mermaid agent
  default; surface only if a conductor caller needs to force a type.

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 5-ba-uc Conductor + End-to-End Integration*
*Context gathered: 2026-06-18*
