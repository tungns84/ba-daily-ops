# BA Daily Operators — Architecture Design

> Greenfield design for a GSD-grade Business-Analyst operator suite.
> Runtime: **CodexApp first (v1)**, **Claude Code roadmap (v2)**.
> Built to the standard in `FIS_GSARCHITECTURE.md` (GSD Core).
> **Current version: 0.2.2.** Reflects: a conductor (`ba-uc`), default routes,
> and the hardened grounding gate (citation must be a real verbatim substring).

---

## 0. Why this exists

A BA does the same handful of deliverable-producing loops every day: turn a use
case into a controlled hand-off package, draw a process, extract requirements
into an SRS/BRD, groom a backlog, and embed diagrams into specs. Today each of
those is ad-hoc. This suite turns each repeated loop into an **operator** — a
skill backed by a deterministic CLI and verified by gates — so the output is
reproducible, hash-provable, and portable across machines and runtimes.

The design directly mirrors GSD Core's five-layer model:

```
USER  →  $ba-<operator> [args]
          │
COMMAND / SKILL LAYER       .agents/skills/ba-*/SKILL.md   (Codex skills, flat)
          │
WORKFLOW LAYER              .agents/ba-daily-operators/ba-core/workflows/*.md          (thin orchestrators)
          │
AGENT LAYER                 .agents/ba-daily-operators/ba-core/agents/*.md             (fresh-context specialists)
          │
CLI TOOLS LAYER             .agents/ba-daily-operators/ba-tools/ba_tools.py            (deterministic, verifiable)
          │
FILE-STATE LAYER            .ba-ops/                         (persistent, survives /clear)
```

---

## 1. Design principles (inherited from GSD, adapted for BA)

| # | Principle | BA-specific meaning |
|---|-----------|--------------------|
| 1 | **Fresh context per agent** | Each operator delegates to specialist roles (analyst, diagrammer, srs-writer, critic, groomer). *Codex v1 caveat:* Codex has no autonomous cross-skill spawn, so the `ba-uc` conductor runs these as one sequential agent loop, not true separate-context subagents; real fresh-context spawn is the Claude/Task v2 model (§9). The independence that matters (ba-critic re-deriving from source) is preserved by instruction. |
| 2 | **Thin orchestrators** | Workflow `.md` files load context via `ba-tools init`, spawn agents, run gates, update `.ba-ops/` — never do heavy lifting inline. |
| 3 | **File-based state** | All BA state in `.ba-ops/` as Markdown+JSON. Survives `/clear`, inspectable, git-committable. |
| 4 | **Absent = enabled** | `.ba-ops/config.json` feature flags default `true` when missing. Users disable, not enable. |
| 5 | **Defense in depth** | Spec verified before build (spec-checker), build produces manifest+hash, post-build verifier checks artifact vs spec, human UAT is final gate. |
| 6 | **Deterministic core, reasoning at the edge** | `ba-tools` (Python) owns everything file/hash/command-verifiable. Agents own analysis, authoring, judgement. Hard line — see §5. |
| 7 | **Lean files, lazy references** | SKILL.md/workflow files stay under byte budgets (§7). Deep knowledge lives in `.agents/ba-daily-operators/ba-core/references/*.md`, Read only at the step that needs it. |
| 8 | **One source format, transform per runtime** | Authored Codex-native; the installer transforms to Claude Code in v2 (§9). |

---

## 2. The operators (1 conductor + 3 spine + 3 plugins)

Each operator is a self-contained skill. `--route` is **optional**: omitted, it
resolves to the operator's main route via `ba-tools resolve-route` (the single
source of truth, `DEFAULT_ROUTE`). Operators still never infer intent from free
text — they only fall back to a known-safe default route.

Scoped to the actual daily workload (detail SRS/BRD analysis + Mermaid + mockup),
with the heavy render/DOCX machinery demoted to optional plugins. See
`.agents/ba-daily-operators/ba-core/references/gsd-adaptation.md` for why each GSD idea was borrowed,
adapted, or dropped.

**Conductor (orchestration):**

| Operator skill | Daily loop | Default route | Notes |
|----------------|-----------|---------------|-------|
| `ba-uc` | deliver ONE use case end-to-end (srs-analyze → mermaid → mockup → index) | `deliver` | Single sequential agent loop, Quality gate between steps, resumable via `ba-tools uc-status`. Routes: `deliver\|resume\|status\|iterate`. |

**Spine (daily):**

| Operator skill | Daily loop | Artifact | Render |
|----------------|-----------|----------|--------|
| `ba-srs-analyze` | sources → atomic, grounded, verifiable requirements + SRS/BRD | requirements JSON + SRS `.md` | — (text; quality-gated) |
| `ba-mermaid` | UC/requirement → Mermaid diagram, MD-inline first | ```mermaid in `.md` (`.mmd`/PNG optional) | `mmdc` only when exported |
| `ba-mockup` | requirements → UI mockup at `--fidelity html\|wireframe` | `.html` or inline wireframe | browser shot (optional, html) |

**Optional plugins (the rare ~20% — off the spine, still discoverable):**

| Operator skill | When | Artifact | Render |
|----------------|------|----------|--------|
| `ba-make-diagram` | a formal BPMN swimlane is explicitly required | `.drawio` + PNG | draw.io CLI |
| `ba-uc-delivery` | a stakeholder DOCX deliverable is required | DOCX + hash-manifest | draw.io CLI (embedded) |
| `ba-backlog-grooming` | epics need SPIDR splitting | backlog `.md` + `stories.json` | — |

Notes:
- The hash-manifest / CLI-render invariant lives in the **plugins**, where a
  binary diagram is embedded in a binary doc — not on the daily text-first spine.
- `ba-mermaid` (daily, lightweight flows) and `ba-make-diagram` (formal BPMN,
  draw.io) are distinct backends, never crossed.

### Operator relationships

```
ba-uc (conductor) ──runs in order──► ba-srs-analyze → ba-mermaid → ba-mockup → index
                                       (one agent loop; Quality gate after srs-analyze)

ba-srs-analyze ──REQ-IDs──► ba-mermaid      (diagrams cite the REQ-IDs they depict)
               ──REQ-IDs──► ba-mockup       (screens cite the REQ-IDs they realize)
               ──REQ-IDs──► ba-backlog-grooming  (stories trace to REQ-IDs)
ba-make-diagram ◄────────── ba-uc-delivery  (plugin: uc-delivery embeds a draw.io BPMN)
```

`ba-uc` is the only operator that *invokes* others (by reading their workflows and
running them in sequence). Everything else is connected only by the `.ba-ops/`
REQ-ID traceability matrix (§8), not by calling each other.

---

## 3. Layer 1 — Command / Skill (Codex-first)

### Discovery & layout

Codex scans `.agents/skills/` from cwd up to repo root (verified vs official
Codex docs). Codex is a **recursive skill loader**, so we keep the layout
**flat** — namespace routers only pay off past ~67 skills. Spine and plugins are
all flat (so all are discoverable); plugins are marked "OPTIONAL" in their
`description` so the model knows they are not the daily path:

```
.agents/skills/
├── ba-uc/                  # conductor (orchestrates the spine for one UC)
│   ├── SKILL.md            (required: name + description frontmatter)
│   └── agents/openai.yaml  (UI metadata + invocation policy)
├── ba-srs-analyze/         # spine
│   ├── SKILL.md
│   └── agents/openai.yaml
├── ba-mermaid/             # spine
├── ba-mockup/              # spine
├── ba-make-diagram/        # optional plugin (formal BPMN)
├── ba-uc-delivery/         # optional plugin (stakeholder DOCX)
└── ba-backlog-grooming/    # optional secondary
```

### SKILL.md contract

Frontmatter carries **only** `name` + `description` (the sole fields Codex reads
for routing — keep the description keyword-dense and trigger-oriented). Body is a
thin bootstrap that:

1. Resolves `--route`; if absent, falls back to the operator's default route
   (`ba-tools resolve-route <operator>` — e.g. `ba-uc`→`deliver`, `ba-mermaid`→`author`).
2. Maps route → workflow file under `.agents/ba-daily-operators/ba-core/workflows/`.
3. Reads that workflow and follows it.

### openai.yaml contract

```yaml
interface:
  display_name: "BA UC Delivery"
  short_description: "Route BA UC delivery operator with explicit --route."
  default_prompt: "$ba-uc-delivery --route prepare --uc \"<file>: ## UC-001. <name>\""
  allow_implicit_invocation: false   # explicit-only: this skill fires only when named
```

Per operator: `allow_implicit_invocation: false` on the conductor, spine, and the
DOCX/backlog plugins so they only fire on an explicit `$` mention (the analysis/
build path must never be auto-triggered). `ba-make-diagram` MAY allow implicit
(pure generator, safe to auto-fire from a process description). Note: this flag
governs *whether the skill fires*; the `--route` default (above) only governs
*which route runs once it has fired*.

---

## 4. Layer 2 — Workflow (thin orchestrators)

`.agents/ba-daily-operators/ba-core/workflows/<operator>.md`, one per operator, plus shared mode/template
extraction when a file exceeds its byte tier (§7).

Each workflow follows the GSD orchestrator pattern:

```
1. Load context:   ba-tools init <operator> --config <cfg>   → JSON (project, config, state, route)
2. Resolve route:  dispatch on --route
3. Per step:
     a. Spawn agent (fresh context) with focused prompt + context payload
     b. Collect agent output (path to artifact, never raw content)
     c. Run gate(s) — see §6
     d. ba-tools state update   → write .ba-ops/STATE.md
4. Emit manifest + verification result
```

Route table (canonical across operators where applicable):

| Route | Responsibility |
|-------|----------------|
| `prepare` | Extract source, draft analysis, write hand-off docs, write generated config. |
| `analysis` | Refresh the analysis/requirements artifact from source. |
| `diagram` | Invoke the diagram agent/skill, write `.drawio`/`.mmd`, render via CLI. |
| `export` | Render only (draw.io/mermaid CLI) from existing source. |
| `build` | Assemble the deliverable (DOCX/SRS), embed rendered media, write manifest. |
| `full` | Run the whole operator pipeline end-to-end with all gates. |
| `package` | Zip the operator artifacts for hand-off. |

Per-operator routes and the default (used when `--route` is omitted):

| Operator | Routes | Default |
|----------|--------|---------|
| `ba-uc` | deliver, resume, status, iterate | `deliver` |
| `ba-srs-analyze` | extract, draft, lint, verify, full, iterate | `full` |
| `ba-mermaid` | author, render, full | `author` (inline MD, no CLI dependency) |
| `ba-mockup` | screen, full | `full` (`--fidelity` still required) |
| `ba-make-diagram` | diagram, export | `diagram` |
| `ba-uc-delivery` | prepare, analysis, diagram, export, build, full, package | `full` |
| `ba-backlog-grooming` | split, criteria, order, full | `full` |

---

## 5. Layer 4 — `ba-tools` deterministic CLI

One shared CLI (GSD's `gsd-tools.cjs` analog). **Language: Python** — the heavy
verifiable work is DOCX manipulation (`python-docx`), UC/Markdown extraction, and
hashing, all already Python in the existing harness. It shells out to the two
render backends (draw.io desktop CLI, `mmdc`) but renders nothing itself.

### The determinism boundary (non-negotiable)

`ba-tools` does ONLY what a file, a command, or a hash can prove:

- parse/extract source sections (UC, requirements)
- fill templates deterministically
- run `draw.io` / `mmdc` and capture exact command + exit code
- embed rendered media into DOCX by **media-replacement** (not append)
- compute SHA-256 of source, rendered, and embedded media
- **verify a `stated` requirement's citation exists**: open `source_trace.doc` and
  confirm `source_trace.span` is a real verbatim substring (≥12 chars). Proves the
  quote is *real*; whether it *justifies* the statement stays `ba-critic`'s call.
- write/verify manifest; update `.ba-ops/STATE.md`; package zip

Agents do everything requiring judgement: UC analysis depth, BPMN/Mermaid
content, requirement phrasing, story splitting, acceptance criteria.

### Command families

```
ba-tools init <operator> [--config <cfg>]        → context JSON (config, routes, default_route, state)
ba-tools resolve-route <operator>                → the default route when --route is omitted
ba-tools state update|patch|advance              → .ba-ops/STATE.md (lockfile-guarded)
ba-tools template fill <tpl> --out <path>        → scaffold artifact from .agents/ba-daily-operators/ba-core/templates
ba-tools extract-uc --uc "<spec>"                → UC section + parsed identity
ba-tools export-diagram --config <cfg>           → draw.io CLI render → PNG + hashes
ba-tools render-mermaid --config <cfg>           → mmdc render → PNG/SVG + hashes
ba-tools update-docx --config <cfg>              → media-replace + caption/source/changelog (stub)
ba-tools manifest write --config <cfg>           → delivery manifest JSON
ba-tools lint-requirements --requirements <f>    → ambiguity/atomicity/grounding/verifiability/citation flags
ba-tools verify --config <cfg>                   → gate checks (folds the lint; hash match, coverage)
ba-tools trace write --kind --slug --req-ids …   → record artifact→REQ-ID trace (+ statement hash)
ba-tools index update                            → .ba-ops/INDEX.md matrix (orphans, gaps, drift)
ba-tools uc-status --config <cfg>                → single-UC pipeline state + next_step (resumable)
ba-tools discovery add|list                      → capture/list iteration discoveries
ba-tools scan --file <f>                          → prompt-injection scan (advisory)
ba-tools package --out <zip> [--with-tests|--with-docs] → portable installer bundle
```

Every success prints UTF-8 JSON to stdout. Every `BaToolsError` exits `2`.
All config paths resolve relative to `--repo-root` (default = git root / cwd —
**no hard-coded machine paths**; Python resolved via `sys.executable`).

### Render backend resolution

- **draw.io**: `--drawio-cli` → `$DRAWIO_CLI` → PATH (`drawio`/`draw.io`/`diagrams.net`)
  → common install paths. Not found → hard fail. No fallback renderer.
- **mermaid**: `--mermaid-cli` → `$MERMAID_CLI` → PATH (`mmdc`) → `npx @mermaid-js/mermaid-cli`.
  Not found → hard fail.

---

## 6. Verification — three gates (trimmed from GSD's four)

Three canonical gate types (`.agents/ba-daily-operators/ba-core/references/gates.md`). GSD's "Transition"
gate is dropped — advancing a step just means the prior gate passed and
`ba-tools state update` recorded it. Deterministic checks all live in
`ba-tools verify`; the gates are how the workflow acts on that verdict.

| Gate | Fires | Enforces |
|------|-------|----------|
| **Confirm** | Before irreversible/outward steps | Human checkpoint (e.g. before overwriting a delivered DOCX/SRS). |
| **Quality** | After an agent produces an artifact | `ba-tools verify` (REQ-ID grounding *incl. verbatim citation-exists check*, coverage, atomicity, verifiability, ambiguity lint, hash-match) + `ba-critic` judgement. |
| **Safety** | Before any render/embed (plugins only) | draw.io/mermaid CLI only; no Pillow/SVG/screenshot synthetic; path-traversal & injection scan on `.ba-ops/` writes; media extension == `.png`/`.svg`. |

One reasoning-side quality agent (deterministic checks are in `ba-tools verify`):

- **`ba-critic`** — independent, fresh-context, Chain-of-Verification self-critique
  of a drafted analysis/SRS: generates per-requirement verification questions,
  answers them from the source independently of the draft, returns findings
  (≤3 revision loops). Read-only; never edits.

### Manifest = control evidence (plugins)

Render/build in the optional plugins (`ba-make-diagram`, `ba-uc-delivery`, and
`ba-mermaid` only when exporting an image) writes a manifest JSON: operator,
route, `generated_at`, per-step results, render CLI executable + exact command,
SHA-256 of source / rendered / embedded media, and policy flags
(`diagram_source = "draw.io CLI" | "mermaid CLI"`,
`no_synthetic_diagram_fallback = true`). Pass condition:
`rendered_sha256 == embedded_sha256`. The text-first spine has no manifest.

---

## 7. Byte budgets (Codex `project_doc_max_bytes` aware)

Codex truncates instruction docs past **32,768 bytes**. AGENTS.md and any
eagerly-loaded doc must stay under it. Workflow files (loaded on invocation)
adopt GSD tiers:

| Tier | Limit | Use |
|------|-------|-----|
| AGENTS.md / eager refs | < 32,768 B | Hard limit — Codex truncates beyond. |
| `DEFAULT` workflow | < 38,000 B | Focused single-operator workflows (target). |
| `LARGE` workflow | < 54,000 B | uc-delivery `full` orchestration. |

When a workflow grows past tier: extract per-route bodies to
`workflows/<operator>/routes/<route>.md` and shared knowledge to
`.agents/ba-daily-operators/ba-core/references/`, leaving the parent a thin dispatcher that Reads only the
route file it needs (no eager `@`-import behind a conditional).

---

## 8. Layer 5 — `.ba-ops/` file-state (traceability spine)

The point of `.ba-ops/` is **REQ-ID traceability**, not an artifact dump. One
requirement, seen consistently across SRS, diagram, mockup, and backlog — drift
surfaces the moment it appears. This is the suite's core value (confirmed: high
UC volume + real cross-artifact traceability pain).

```
.ba-ops/
├── PROJECT.md          # BA engagement: product, scope, stakeholders, constraints
├── REQUIREMENTS.md     # the REQ-ID registry: requirements + business rules
├── INDEX.md            # TRACEABILITY MATRIX: REQ-ID → SRS § → mermaid → mockup → story; + orphans + source-drift
├── STATE.md            # living memory: current operator, last route, gate verdicts, blockers
├── config.json         # suite + per-operator config (absent = enabled)
├── srs/<slug>/         # requirements.json, analysis.md, SRS sections
├── mermaid/<slug>/     # .mmd / inline-diagram refs (+ renders only if exported)
├── mockup/<slug>/      # .html or wireframe blocks
├── backlog/<slug>/     # groomed backlog .md + stories.json   (optional)
└── plugins/<slug>/     # draw.io / DOCX plugin outputs + manifest  (optional, rare)
```

Every downstream artifact carries a `req_ids` field; `ba-tools index update`
rebuilds INDEX.md from them and flags **gaps** (missing coverage), **orphans**
(req_ids that don't exist), and **stale** (source hash changed → re-run needed —
the BA-flavored "source drift" gate adapted from GSD's codebase-drift gate).

`STATE.md` writes are lockfile-guarded (`STATE.md.lock`, `O_EXCL`, stale-lock
10s) so concurrent operators can't clobber each other.

---

## 9. Runtime abstraction — Codex v1, Claude v2

Authored once in Codex-native form; the installer transforms per runtime
(GSD's single-source/transform-at-install model).

| Surface | Codex (v1, build now) | Claude Code (v2, roadmap) |
|---------|----------------------|---------------------------|
| Invocation | `.agents/skills/ba-*/SKILL.md`, `$ba-*` | `commands/ba-*.md` slash commands + `~/.claude/skills/ba-*` |
| Agents | `.agents/ba-daily-operators/ba-core/agents/*.md` + per-agent metadata | same `.md`, spawned via Task subagents |
| Guardrails | `.agents/ba-daily-operators/AGENTS.md` (Read by skills; not root-auto-loaded — avoids clashing with the project's own AGENTS.md) | `CLAUDE.md` + slash-command body |
| Config/hooks | `.codex/config.toml` (trusted projects), `agents/openai.yaml` | `.claude/settings.json` hooks |
| Render CLIs | draw.io desktop, `mmdc` | identical (host-independent) |

v2 deferred work: install-time transform script, Claude command frontmatter
(`allowed-tools`), Task-subagent spawn wiring, statusline/context-monitor hooks.
The `ba-tools` CLI and `.ba-ops/` state are **runtime-agnostic** and ship
unchanged into v2.

---

## 10. Build order (greenfield)

Spine first — it carries the daily value and the blast-radius control.
As of 0.2.2, steps 1–6 are built; step 8 (Claude v2 transform) is the open work.

1. `ba-tools` CLI: `lint-requirements` + `verify` core, then
   `init`/`state`/`index`/`resolve-route`/`uc-status`/`discovery`/`trace`. **DONE**
2. `ba-srs-analyze` end-to-end: `ba-srs-writer` emits the quality-contract schema
   → `ba-tools verify` gates it (incl. citation-exists, 0.2.2) → `ba-critic` loop. **DONE**
3. `.ba-ops/` traceability matrix: `ba-tools index update` with gap/orphan/stale. **DONE**
4. `ba-mermaid` (MD-inline; `mmdc` render optional). **DONE**
5. `ba-mockup` (`--fidelity html|wireframe`). **DONE**
6. `ba-uc` conductor (sequential spine loop, gates, resumable) + default routes. **DONE**
7. Optional plugins: `ba-make-diagram` (draw.io), `ba-uc-delivery`
   (DOCX media-replace — `update-docx` still a stub), `ba-backlog-grooming`. **partial**
8. v2: Claude transform (Task-subagent spawn, command frontmatter, hooks). **open**

Packaging (installer `install.py` + test-gated `build.py` → versioned `dist/` zip)
and the docs (`METHODOLOGY.md`, `METHODOLOGY-TOUR.html`, `USER-GUIDE.md`) ship today.

---

## 10b. UI — in-Codex only (DECIDED)

No bespoke GUI, no separate web dashboard. The harness lives inside the Codex App
chat. Effectiveness over looks. The UI is three layers, all native:

1. **Picker / chip** — `$` skill mention shows `display_name` + `short_description`
   from each `agents/openai.yaml`; selecting prefills `default_prompt`.
2. **Chat stream** — tool calls (`ba-tools …` JSON) interleaved with agent
   reasoning and gate verdicts (`✓ ok:true` / `✗ ok:false` + failures). The
   fail→critic→pass loop is visible inline — that *is* the blast-radius control
   surface, not a dashboard.
3. **Artifacts** — Markdown renders: the SRS `.md`, `INDEX.md` traceability
   matrix, inline ```mermaid, and (html fidelity) the mockup `.html`.

Implication for design: keep `ba-tools` output **terse and scannable** (it is read
by a human in the chat, not just parsed) — short JSON, explicit `ok`/`failures`,
no noise. A standalone viewer over `.ba-ops/` is explicitly out of scope unless
demand changes.

---

## 11. Non-negotiables (forbidden shortcuts)

- Render diagram PNG with Pillow / SVG converter / screenshot / hand-pasted image.
- Embed a stale render when the source changed.
- Append a new image to the DOCX instead of replacing the placeholder media.
- Replace media without checking the `.png`/`.svg` extension.
- Let any operator skill infer its route from free text when `--route` is absent.
- Run `build`/`export` without a Safety gate, or `package` without a passing manifest.
- Hard-code machine-specific paths (`D:\...\python.exe`, `D:\codex\demo_ba_ops`) in committed config.
