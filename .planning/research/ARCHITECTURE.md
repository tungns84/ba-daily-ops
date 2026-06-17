# Architecture Research

**Domain:** BA Operator Suite — deterministic CLI + LLM agent orchestration
**Researched:** 2026-06-17
**Confidence:** HIGH (derived directly from DESIGN.md v0.2.2 and PROJECT.md)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — COMMAND / SKILL  (.agents/skills/ba-*/SKILL.md)           │
│  ┌──────────┐ ┌──────────────┐ ┌───────────┐ ┌──────────────────┐   │
│  │  ba-uc   │ │ba-srs-analyze│ │ ba-mermaid│ │   ba-mockup      │   │
│  │(conductor│ │  (spine)     │ │  (spine)  │ │   (spine)        │   │
│  │ explicit)│ │  explicit)   │ │ explicit) │ │   explicit)      │   │
│  └────┬─────┘ └──────┬───────┘ └─────┬─────┘ └────────┬─────────┘   │
├───────┴──────────────┴───────────────┴────────────────┴─────────────┤
│  LAYER 2 — WORKFLOW  (.agents/ba-daily-operators/ba-core/workflows/) │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │  thin orchestrator: init → route → [spawn agent → gate →       │   │
│  │  state update] × N steps → emit manifest                       │   │
│  └───────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 3 — AGENT  (.agents/ba-daily-operators/ba-core/agents/)       │
│  ┌────────────┐ ┌──────────┐ ┌────────────┐ ┌──────────────────┐    │
│  │ba-srs-writer│ │ba-critic │ │ba-diagrammer│ │ba-mockup-designer│    │
│  │(judgement) │ │(CoV loop)│ │(judgement) │ │(judgement)       │    │
│  └────────────┘ └──────────┘ └────────────┘ └──────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 4 — CLI TOOLS  (ba_tools.py, Python)                          │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  file / hash / command-provable only:                         │    │
│  │  init · state · resolve-route · lint-requirements · verify    │    │
│  │  trace · index · uc-status · discovery · template · extract   │    │
│  └──────────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 5 — FILE-STATE  (.ba-ops/)                                    │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────────┐    │
│  │REQUIREMENTS.md│ │   INDEX.md  │ │ STATE.md │ │  config.json  │    │
│  │ (REQ-ID reg) │ │(trace matrix│ │(lockguard│ │ absent=enabled│    │
│  └──────────────┘ └─────────────┘ └──────────┘ └───────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Layer |
|-----------|---------------|-------|
| `ba-uc` skill | Entry point for conductor; resolves `--route`, maps to workflow | L1 |
| `ba-srs-analyze` skill | Entry for SRS/requirements extraction; explicit-only invocation | L1 |
| `ba-mermaid` skill | Entry for diagram authoring; explicit-only | L1 |
| `ba-mockup` skill | Entry for UI mockup generation; explicit-only | L1 |
| `ba-uc` workflow | Sequential spine loop with Quality gate between steps; resumable | L2 |
| Spine workflows | One workflow `.md` per operator; thin dispatch only | L2 |
| `ba-srs-writer` agent | Produces requirements JSON + SRS `.md`; judgement only | L3 |
| `ba-critic` agent | Fresh-context CoV self-critique, ≤3 loops, read-only | L3 |
| `ba-diagrammer` agent | Mermaid diagram content decisions | L3 |
| `ba-mockup-designer` agent | UI mockup structure and layout decisions | L3 |
| `ba_tools.py` | All file/hash/command-verifiable work; Python CLI | L4 |
| `.ba-ops/` | Persistent file state; REQ-ID registry + traceability matrix | L5 |

---

## Recommended Project Structure

```
.agents/
├── skills/
│   ├── ba-uc/
│   │   ├── SKILL.md              # frontmatter: name + description only
│   │   └── agents/openai.yaml    # allow_implicit_invocation: false
│   ├── ba-srs-analyze/
│   ├── ba-mermaid/
│   ├── ba-mockup/
│   ├── ba-make-diagram/          # optional plugin
│   ├── ba-uc-delivery/           # optional plugin
│   └── ba-backlog-grooming/      # optional secondary
│
└── ba-daily-operators/
    └── ba-core/
        ├── AGENTS.md             # Read by skills; NOT root-auto-loaded (<32,768 B)
        ├── workflows/
        │   ├── ba-uc.md          # conductor sequential loop
        │   ├── ba-srs-analyze.md
        │   ├── ba-mermaid.md
        │   ├── ba-mockup.md
        │   └── <operator>/routes/<route>.md  # extracted when workflow > byte tier
        ├── agents/
        │   ├── ba-srs-writer.md
        │   ├── ba-critic.md
        │   ├── ba-diagrammer.md
        │   └── ba-mockup-designer.md
        ├── references/
        │   ├── gates.md
        │   ├── gsd-adaptation.md
        │   └── *.md              # deep knowledge, lazy-loaded per step
        └── templates/            # template fill sources for ba-tools

ba-tools/
└── ba_tools.py                   # single-file Python CLI

.ba-ops/
├── PROJECT.md
├── REQUIREMENTS.md               # REQ-ID registry
├── INDEX.md                      # traceability matrix
├── STATE.md                      # lockfile-guarded
├── config.json                   # absent = enabled
├── srs/<slug>/
├── mermaid/<slug>/
├── mockup/<slug>/
├── backlog/<slug>/               # optional
└── plugins/<slug>/               # optional
```

### Structure Rationale

- **Flat `.agents/skills/`:** Codex is a recursive skill loader; flat layout makes all skills discoverable without namespace routers, which only pay off past ~67 skills.
- **`.agents/ba-daily-operators/ba-core/` separation:** Keeps operator internals out of the root `.agents/skills/` scan; AGENTS.md here is Read by skills, not root-auto-loaded, avoiding collision with the project's own AGENTS.md.
- **`workflows/` vs `agents/`:** Hard separation enforces the determinism boundary — workflows orchestrate, agents reason.
- **`references/` lazy-loaded:** Deep knowledge files are Read only at the step that needs them, preserving byte budget.
- **`.ba-ops/` as single state root:** Survives `/clear`, git-committable, inspectable without tooling.

---

## Architectural Patterns

### Pattern 1: Determinism Boundary (Hard Line)

**What:** A strict partition between what `ba-tools` (the CLI) is allowed to do and what agents are allowed to do. `ba-tools` may only perform file operations, hash computations, command execution with captured output, and template filling. Agents own all analysis, authoring, and judgement.

**When to use:** Every time a new command or capability is added to the system. The question is always: "Can a file, a command, or a hash prove this?" If yes → `ba-tools`. If no → agent.

**Trade-offs:**
- Pro: outputs are reproducible and auditable regardless of LLM non-determinism
- Pro: gates can be re-run independently of the agent that produced the artifact
- Con: requires discipline; the boundary is enforced by convention, not enforcement mechanism

**Concrete boundary examples:**

```
ba-tools DOES:
  - Open source_trace.doc, check source_trace.span is a ≥12-char verbatim substring
  - Compute SHA-256 of .mmd / .drawio / .png / .docx
  - Run `mmdc -i diagram.mmd -o diagram.png`, capture exit code
  - Rebuild INDEX.md from req_ids fields across .ba-ops/ artifacts
  - Write STATE.md with O_EXCL lock

AGENTS DO:
  - Decide which requirements are atomic, grounded, verifiable
  - Author Mermaid diagram content (actors, flows, conditions)
  - Phrase acceptance criteria
  - Judge whether a requirement justifies a design decision
  - ba-critic: re-derive verification questions from source independently
```

### Pattern 2: Conductor with Sequential Agent Loop + Quality Gate

**What:** `ba-uc` is the only operator that invokes other operators. It runs them as a single sequential agent loop (Codex v1 constraint — no true cross-skill spawn). A Quality gate fires between steps: `ba-tools verify` checks the artifact deterministically, then `ba-critic` applies Chain-of-Verification judgement.

**When to use:** Any multi-step pipeline where intermediate artifacts must be quality-checked before the next step consumes them.

**Trade-offs:**
- Pro: blast radius contained — a bad SRS doesn't propagate to diagram/mockup
- Pro: resumable via `ba-tools uc-status` — STATE.md records `last_completed_step` and `next_step`
- Con: Codex v1 doesn't have true fresh-context subagents; independence of `ba-critic` is preserved by instruction, not architecture

**Conductor loop structure:**

```
ba-uc deliver:
  1. ba-tools init ba-uc → context JSON
  2. ba-tools uc-status → check if resuming
  3. [Step: srs-analyze]
       spawn ba-srs-writer agent → requirements.json + analysis.md
       Quality gate: ba-tools verify (citation-exists, lint, hash) + ba-critic CoV
       ba-tools state update → record step complete
  4. [Step: mermaid]
       spawn ba-diagrammer agent → .mmd / inline Mermaid
       Quality gate: ba-tools verify (req_id coverage)
       ba-tools state update
  5. [Step: mockup]
       spawn ba-mockup-designer agent → .html or wireframe
       Quality gate: ba-tools verify (req_id coverage)
       ba-tools state update
  6. ba-tools index update → INDEX.md with gaps/orphans/stale
  7. Emit summary
```

### Pattern 3: REQ-ID as the Only Inter-Operator Coupling

**What:** Operators do not call each other (except `ba-uc` calling spine operators). The sole coupling between `ba-srs-analyze`, `ba-mermaid`, `ba-mockup`, and `ba-backlog-grooming` is the `req_ids` field each artifact carries. `ba-tools index update` reads those fields and builds the traceability matrix.

**When to use:** Any time two operators need to "know about each other" — they don't. They only need to reference the same REQ-ID.

**Trade-offs:**
- Pro: operators are independently runnable without knowing about each other
- Pro: INDEX.md drift detection is a pure file scan — no orchestration needed
- Pro: REQ-ID registry in REQUIREMENTS.md is the single source of truth; orphan detection is `O(n)` set membership check
- Con: REQ-ID discipline must be maintained by agents; `ba-tools lint-requirements` flags orphans but cannot prevent them at authoring time

**Data coupling diagram:**

```
REQUIREMENTS.md (REQ-ID registry)
        │
        ├──► ba-srs-analyze writes: srs/<slug>/requirements.json  {req_ids: [...]}
        │
        ├──► ba-mermaid writes: mermaid/<slug>/<diagram>.mmd      {req_ids: [...]}
        │
        ├──► ba-mockup writes: mockup/<slug>/<screen>.html        {req_ids: [...]}
        │
        └──► ba-tools index update reads all req_ids fields
                 → INDEX.md: REQ-ID × artifact coverage matrix
                              + gaps (no artifact covers this REQ-ID)
                              + orphans (artifact references non-existent REQ-ID)
                              + stale (source SHA-256 changed since last verify)
```

### Pattern 4: Lockfile-Guarded State Writes

**What:** `STATE.md` writes use a companion `.lock` file created with `O_EXCL` (atomic create — fails if file already exists). If the lock is older than 10 seconds, it is treated as stale and forcibly removed.

**When to use:** Any write to `.ba-ops/STATE.md` via `ba-tools state update|patch|advance`.

**Trade-offs:**
- Pro: prevents concurrent operators (e.g. `ba-uc` and a manual `ba-srs-analyze` run) from clobbering each other
- Pro: 10-second stale-lock timeout prevents permanent deadlock from a crashed process
- Con: `O_EXCL` is POSIX; on Windows this requires Python's `os.open` with `os.O_CREAT | os.O_EXCL` — available but less commonly documented

**Implementation contract:**

```python
# ba_tools.py state write contract
import os

lock_path = ".ba-ops/STATE.md.lock"

# Acquire
try:
    fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
except FileExistsError:
    # Check age; if > 10s, os.remove and retry once
    ...

# Write STATE.md

# Release
os.remove(lock_path)
```

### Pattern 5: Absent = Enabled Feature Flags

**What:** `.ba-ops/config.json` absence means all features are enabled. Users opt out by setting flags to `false`. The CLI never requires the file to exist.

**When to use:** All feature-flag reads in `ba_tools.py` and workflow files.

**Trade-offs:**
- Pro: zero-config startup; new installs work immediately
- Pro: disabling a feature is explicit and visible in git history
- Con: adding a new feature that some users would want disabled requires a documented convention for the flag name

---

## Data Flow

### Primary Flow: `ba-uc deliver` (end-to-end UC)

```
User: $ba-uc --route deliver --uc "UC-001. Login"
         │
         ▼
SKILL.md bootstrap
  ba-tools resolve-route ba-uc       → "deliver"
  Read workflows/ba-uc.md
         │
         ▼
WORKFLOW: ba-uc.md
  ba-tools init ba-uc                → context JSON (config, state, route)
  ba-tools uc-status                 → {last_completed: null, next_step: "srs-analyze"}
         │
         ▼ Step 1: srs-analyze
  Spawn ba-srs-writer agent
    reads: source docs
    writes: .ba-ops/srs/<slug>/requirements.json  {req_ids: ["REQ-001", ...]}
            .ba-ops/srs/<slug>/analysis.md
  QUALITY GATE:
    ba-tools verify                  → {ok: true/false, failures: [...]}
      ├─ lint-requirements (atomicity, grounding, ambiguity)
      ├─ citation-exists (source_trace.span ≥12-char verbatim substring check)
      └─ hash match
    ba-critic agent (if verify ok)   → CoV findings, ≤3 revision loops
  ba-tools state update              → STATE.md {last_completed: "srs-analyze"}
         │
         ▼ Step 2: mermaid
  Spawn ba-diagrammer agent
    reads: requirements.json
    writes: .ba-ops/mermaid/<slug>/diagram.mmd    {req_ids: ["REQ-001", ...]}
  QUALITY GATE:
    ba-tools verify (req_id coverage)
  ba-tools state update
         │
         ▼ Step 3: mockup
  Spawn ba-mockup-designer agent
    reads: requirements.json
    writes: .ba-ops/mockup/<slug>/screen.html     {req_ids: ["REQ-001", ...]}
  QUALITY GATE:
    ba-tools verify (req_id coverage)
  ba-tools state update
         │
         ▼ Step 4: index
  ba-tools index update              → .ba-ops/INDEX.md
    reads: all {req_ids} fields across srs/, mermaid/, mockup/
    reads: REQUIREMENTS.md (REQ-ID registry)
    reads: stored source SHA-256 hashes
    writes: INDEX.md {gaps, orphans, stale}
         │
         ▼
  Emit: summary JSON {ok, steps, index_path}
```

### Resume Flow: `ba-uc resume`

```
User: $ba-uc --route resume
         │
         ▼
WORKFLOW: ba-uc.md (resume route)
  ba-tools uc-status --config <cfg>  → {last_completed: "srs-analyze", next_step: "mermaid"}
  Jump to Step 2 (mermaid) and continue
```

### Standalone Operator Flow

```
User: $ba-srs-analyze --route full
         │
         ▼
SKILL.md → workflows/ba-srs-analyze.md
  ba-tools init → context JSON
  spawn ba-srs-writer → requirements.json
  QUALITY GATE → verify + ba-critic
  ba-tools state update
  (no index update — standalone; user runs ba-tools index update separately)
```

### Traceability Drift Detection Flow

```
Source doc changes on disk
         │
         ▼
Developer runs: ba-tools index update
         │
         ▼
ba_tools.py:
  For each artifact in .ba-ops/{srs,mermaid,mockup}/:
    read stored source_sha256 from requirements.json / artifact metadata
    compute current SHA-256 of the source doc
    if stored != current → mark artifact as STALE in INDEX.md
         │
         ▼
INDEX.md output:
  | REQ-001 | srs/login/... | mermaid/login/... | mockup/login/... | STALE (srs) |
  | REQ-002 | srs/login/... | (gap)             | mockup/login/... | ok          |
  | REQ-999 | (orphan: no such REQ-ID in registry) |
```

---

## Component Boundaries

### What Talks to What

| From | To | Via | Notes |
|------|----|-----|-------|
| SKILL.md | Workflow `.md` | `Read` file | Bootstrap only — no logic in skill |
| Workflow | `ba-tools` | shell / tool call | Returns JSON stdout |
| Workflow | Agent `.md` | `Read` + spawn | Passes focused context payload |
| Agent | `ba-tools` | shell / tool call | Agent calls CLI for verifiable work |
| `ba-tools` | `.ba-ops/` | direct file I/O | STATE.md write is lockfile-guarded |
| `ba-tools` | `mmdc` / `draw.io` CLI | subprocess shell-out | Captures exact command + exit code |
| `ba-uc` workflow | Spine workflows | `Read` workflow `.md` | Only conductor does this |
| Operators (non-conductor) | Other operators | **never** | Decoupled via REQ-IDs in `.ba-ops/` |

### Hard Boundaries

1. `ba-tools` → no LLM calls, no analysis, no authoring. If it requires judgement, it is not in `ba-tools`.
2. Agents → no direct `.ba-ops/` writes except via `ba-tools` commands. Agents emit artifact paths, not file content.
3. Spine operators (`ba-srs-analyze`, `ba-mermaid`, `ba-mockup`) → never invoke each other. Only `ba-uc` orchestrates.
4. SKILL.md → no workflow logic inline. Body must fit in byte budget; logic lives in the workflow file.
5. `ba-tools` render commands → shell out to `mmdc` / `draw.io` CLI only. No Pillow, SVG converter, screenshot, or hand-pasted image.

---

## Build Order and Dependencies

The build order from DESIGN.md §10 reflects explicit dependency direction:

```
Step 1: ba_tools.py (core commands)
   └── Provides: init, state, resolve-route, lint-requirements, verify,
                 trace, index, uc-status, discovery, template, extract-uc
   └── No dependencies on other components
   └── Rationale: Every other component depends on this; build it first and completely

Step 2: ba-srs-analyze (spine operator)
   └── Depends on: ba_tools.py (verify, lint-requirements, citation-exists, state)
   └── Produces: requirements.json with REQ-IDs — source of truth for all downstream
   └── Rationale: Must exist before mermaid/mockup can consume REQ-IDs

Step 3: .ba-ops/ traceability (index + trace commands)
   └── Depends on: ba_tools.py (index update), ba-srs-analyze artifacts (req_ids)
   └── Produces: INDEX.md with gaps/orphans/stale detection
   └── Rationale: Validates the REQ-ID coupling before adding more operators

Step 4: ba-mermaid (spine operator)
   └── Depends on: ba_tools.py (verify, trace), .ba-ops/ REQ-IDs from step 2-3
   └── Produces: .mmd files with req_ids field
   └── Rationale: Consumes REQ-IDs; traceability matrix must work first

Step 5: ba-mockup (spine operator)
   └── Depends on: ba_tools.py (verify, trace), .ba-ops/ REQ-IDs
   └── Produces: .html / wireframe with req_ids field
   └── Rationale: Same pattern as ba-mermaid; both spine ops can build in parallel

Step 6: ba-uc conductor
   └── Depends on: ALL of steps 1-5 (orchestrates them in sequence)
   └── Produces: end-to-end UC delivery with gates and resumable state
   └── Rationale: Can only be built after all its sub-operators work independently

Step 7: Optional plugins (deferred)
   └── ba-make-diagram, ba-uc-delivery, ba-backlog-grooming
   └── Depends on: ba_tools.py (render commands, manifest, update-docx)
   └── Rationale: Off the daily spine; ba-tools stubs exist, plugins complete later

Step 8: v2 Claude Code transform (roadmap)
   └── Depends on: entire v1 system (transform-at-install model)
   └── ba_tools.py and .ba-ops/ are unchanged; only CLI entry points and
       invocation mechanism transform
```

**Dependency graph summary:**

```
ba_tools.py
    ├──► ba-srs-analyze (L4→L3+L2)
    │        └──► .ba-ops/ INDEX.md (traceability spine)
    │                  ├──► ba-mermaid
    │                  ├──► ba-mockup
    │                  └──► ba-uc conductor ◄── all spine operators
    │
    └──► Optional plugins (render/manifest commands)
```

---

## Anti-Patterns

### Anti-Pattern 1: Logic in SKILL.md

**What people do:** Put routing logic, conditional branching, or inline workflow steps directly in SKILL.md.

**Why it's wrong:** SKILL.md is read on every invocation for routing. Logic there bloats the byte budget (Codex truncates past 32,768 B) and mixes the entry-point contract with orchestration concerns.

**Do this instead:** SKILL.md body is strictly: resolve `--route` via `ba-tools resolve-route`, map route → workflow path, `Read` that workflow file. All logic in the workflow.

### Anti-Pattern 2: Agents Writing Directly to `.ba-ops/`

**What people do:** Have an agent emit JSON directly to `.ba-ops/STATE.md` or append to `REQUIREMENTS.md`.

**Why it's wrong:** Bypasses the lockfile guard on STATE.md; bypasses hash/format validation on requirements.json; makes the write non-auditable.

**Do this instead:** Agent emits output to a temp path or returns structured content. Workflow calls `ba-tools state update` / `ba-tools trace write` to perform the actual write.

### Anti-Pattern 3: `ba-tools` Performing Judgement Calls

**What people do:** Add "smart" logic to `ba-tools` — for example, auto-selecting which requirements are relevant to a diagram, or inferring the `--route` from free text when it is omitted.

**Why it's wrong:** Breaks the determinism boundary. A judgement call in a Python CLI produces a result that cannot be independently verified or re-derived. It also silently couples the CLI to LLM-quality expectations.

**Do this instead:** `ba-tools resolve-route` returns only the registered `DEFAULT_ROUTE` for an operator — a static lookup. Relevance judgements stay in agents.

### Anti-Pattern 4: Operators Calling Each Other Directly

**What people do:** `ba-mermaid` reads `ba-srs-analyze`'s latest output by calling `ba-srs-analyze` internally, or workflow B imports workflow A.

**Why it's wrong:** Creates hidden orchestration dependencies. Any operator must be runnable standalone. Cross-operator coupling makes it impossible to run `ba-mermaid` without `ba-srs-analyze` having run first in the same session.

**Do this instead:** Each operator reads from `.ba-ops/srs/<slug>/requirements.json` directly. The REQ-ID is the coupling, not the operator. Only `ba-uc` orchestrates; it does so explicitly by reading spine workflows in sequence.

### Anti-Pattern 5: Synthetic Diagram Rendering

**What people do:** Use Pillow, an SVG-to-PNG converter, a screenshot tool, or a hand-pasted image when `mmdc` or `draw.io` CLI is unavailable.

**Why it's wrong:** The Safety gate checks `diagram_source` in the manifest and enforces `no_synthetic_diagram_fallback = true`. A synthetic render is unverifiable and breaks hash-manifest integrity.

**Do this instead:** Hard fail with a clear error if the render CLI is not found. Never fall back silently.

### Anti-Pattern 6: Hard-Coded Machine Paths in Config

**What people do:** Write absolute paths like `D:\codex\demo_ba_ops\ba_tools.py` into committed config files.

**Why it's wrong:** Breaks portability across machines and the "runtime-agnostic" contract for v2. Other users cannot run the suite.

**Do this instead:** All paths resolve relative to `--repo-root` (defaults to git root / cwd). Python resolved via `sys.executable`. No hard-coded paths in any committed file.

---

## Where Real-World Suites Get the Determinism Boundary Wrong

These are patterns observed in LLM-tool suites (labeled [Inference] — based on common patterns in the domain):

[Inference] **Mixing LLM calls into the CLI layer.** Some suites add a `--smart` flag to their CLI that calls an LLM to "auto-fix" a failing lint. This makes the CLI non-deterministic: the same input produces different output on different runs, breaking reproducibility and making gate re-runs unreliable.

[Inference] **Letting the CLI "guess" intent from free text.** A CLI that accepts `--action "make the diagram cleaner"` and interprets it with an embedded LLM is not a CLI — it is an agent. The fix is explicit commands with explicit routes; agents handle the fuzzy interpretation and then call the explicit command.

[Inference] **State written by multiple layers without coordination.** When both the agent and the workflow write to state files, race conditions and partial writes appear. The lockfile pattern (`O_EXCL`) is not applied because "agents don't run in parallel." They don't until they do (v2 Task subagents).

[Inference] **Overly chatty CLI output.** CLIs in LLM tool suites that emit prose explanations instead of structured JSON make the output difficult to parse for the workflow layer and noisy in the chat UI. The contract should be: success → JSON stdout; error → exit 2 + JSON stderr.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| `mmdc` (Mermaid CLI) | subprocess shell-out from `ba-tools render-mermaid` | Resolved via `--mermaid-cli` → `$MERMAID_CLI` → PATH → `npx @mermaid-js/mermaid-cli`. Hard fail if not found. |
| `draw.io` desktop CLI | subprocess shell-out from `ba-tools export-diagram` | Resolved via `--drawio-cli` → `$DRAWIO_CLI` → PATH → common install paths. Plugin-only (v1). |
| `python-docx` | Python import in `ba_tools.py` | DOCX media-replace; plugin `ba-uc-delivery` only. `update-docx` is a stub in v1. |
| Codex App | Skill discovery via `.agents/skills/` scan | Flat layout; `agents/openai.yaml` per skill for UI metadata. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| SKILL.md ↔ Workflow | `Read` file call | One-way; skill reads workflow, not vice versa |
| Workflow ↔ `ba-tools` | JSON stdout / exit code | All `ba-tools` commands return UTF-8 JSON on success, exit 2 on error |
| Workflow ↔ Agent | `Read` agent `.md` + focused prompt | Agent receives context payload; returns artifact path |
| Agent ↔ `ba-tools` | JSON stdout / exit code | Same contract as workflow ↔ ba-tools |
| `ba-tools` ↔ `.ba-ops/` | Direct file I/O | STATE.md writes: `O_EXCL` lock; index writes: full rebuild, no incremental patch |
| `ba-uc` ↔ Spine workflows | `Read` workflow `.md` | Conductor reads each spine workflow and follows it; only inter-workflow coupling |
| Operators via `.ba-ops/` | REQ-IDs in artifact metadata | Operators never call each other; only `ba-uc` orchestrates |

---

## Sources

- DESIGN.md v0.2.2 (repo root) — canonical architecture spec; HIGH confidence (first-party)
- PROJECT.md (`.planning/PROJECT.md`) — milestone scope and constraints; HIGH confidence (first-party)

---
*Architecture research for: BA Daily Operators — GSD-grade BA operator suite*
*Researched: 2026-06-17*
