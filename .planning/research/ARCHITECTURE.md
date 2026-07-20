# Architecture Patterns

**Domain:** BA workflow harness — local-first agent + deterministic CLI + file-state traceability
**Researched:** 2026-07-20
**Confidence:** HIGH (normative BRD/SRS-SPEC) / MEDIUM (ecosystem analogs)

## Recommended Architecture

BA Daily Ops follows a **four-layer harness** pattern common in production agent systems (Plan-Execute-Verify, bounded workflows, file-as-state): probabilistic reasoning stays in skills; provable integrity stays in `ba-tools` and `.ba-ops/`. The executable workflow runner is the **control plane** — not the LLM — and owns route order, gate interpretation, and candidate→canonical promotion (BRD-027, R-1).

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     USER / BA (golden path = 1 command)                │
│                         $ba-deliver run --uc <slug>                      │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│              SKILL LAYER — judgement, authoring, UX ($ba-*)              │
├─────────────────────────────────────────────────────────────────────────┤
│  $ba-deliver (conductor)  │  $ba-srs  │  $ba-flow  │  $ba-mockup  │ …   │
│  SKILL.md workflows       │  writes candidates only; calls ba-tools     │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ subprocess: ba-tools <cmd> (JSON I/O)
┌───────────────────────────────────▼─────────────────────────────────────┐
│           DETERMINISTIC LAYER — ba-tools CLI (Python 3.11+)              │
├─────────────────────────────────────────────────────────────────────────┤
│  init │ doctor │ verify │ render │ trace │ index │ gate │ run (runner)  │
│  hash │ schema │ path containment │ atomic write │ filelock │ promote   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ read/write canonical + staging
┌───────────────────────────────────▼─────────────────────────────────────┐
│              FILE-STATE LAYER — `.ba-ops/` (Git-committed)               │
├─────────────────────────────────────────────────────────────────────────┤
│  config.json │ coverage-policy │ business-goals │ STATE.md │ INDEX.md   │
│  srs/<slug>/ │ mermaid/ │ mockup/ │ analysis/ │ runs/<id>/candidates/   │
│  plugins/ (bpmn, docx, backlog) │ MANIFEST.json (strict publish)        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Ecosystem alignment:** Similar to deterministic orchestrators (e.g. YAML phase machines with disk artifacts, PEV loops with CI gates) — the harness is the **operating system around the model**, not a chat transcript. Skills ≈ procedures; `ba-tools` ≈ sensors + actuators with exit codes; `.ba-ops/` ≈ durable workflow state.

### Component Boundaries

| Component | Responsibility | Communicates With | Must NOT |
|-----------|---------------|-------------------|----------|
| **BA / chat runtime** | One-command golden path; human sign-off at strict | `$ba-deliver` skill only (ideal) | Mutate canonical files without runner |
| **`$ba-*` skills** | Domain authoring (SRS prose, diagrams, mockups); invoke `ba-tools` per workflow step | Agent runtime, `ba-tools` subprocess, reads source docs | Own route order, promotion, or coverage verdict |
| **`$ba-deliver` (conductor)** | User-facing orchestration entry; delegates to runner + child skills | Runner CLI, `$ba-srs`/`$ba-flow`/… workflows | Bypass gates; write canonical without promote |
| **Executable workflow runner** | Route selection/order; gate orchestration; resume; **only** promoter candidate→canonical | `coverage-policy.json`, `STATE.md`, `runs/*/journal`, all gate cmds | Call LLM; infer business semantics |
| **`ba-tools` core** | Provable ops: schema, hash, verify, render, trace, index, path safety | `.ba-ops/` files, local render CLIs (mmdc, draw.io) | Network, LLM, MoSCoW judgement |
| **Gate modules** | Mechanical pass/fail + evidence JSON | Candidate/canonical artifacts, source files | Replace human validation |
| **`.ba-ops/` file-state** | Single source of truth for config, registry, trace, RTM views | Git, all layers above | Hold chat history as authority |
| **Profile tier (`config.profile`)** | Single control plane for ceremony, required artifacts, gates | Runner, INDEX, skills (via policy) | Hard-code one pipeline for all projects |
| **Plugins (`$ba-bpmn`, `$ba-docx`, `$ba-backlog`)** | Optional downstream artifacts; same candidate/promote pattern | Runner when policy requires | Silent fallback renderers |

### Determinism Boundary (hard rule)

```
┌──────────────────────┐     ┌──────────────────────┐
│  AGENT / SKILL       │     │  ba-tools            │
│  (judgement)         │     │  (provable)          │
├──────────────────────┤     ├──────────────────────┤
│ Analysis, prose      │     │ file read/write      │
│ MoSCoW, critic rubric│     │ schema validate      │
│ Stakeholder impact   │     │ hash / trace / index │
│ Author candidates    │     │ gate pass/fail       │
│                      │     │ promote (runner)     │
└──────────┬───────────┘     └──────────┬───────────┘
           │  candidates only            │ canonical + evidence
           └──────────────► .ba-ops/runs/<id>/candidates/
                              runner promote ──► canonical paths
```

## Recommended Project Structure

```
ba-daily-ops/                          # product repo (ba-daily-ops slug)
├── docs/                              # BRD, SRS-SPEC (normative contracts)
├── .agents/ba-daily-ops/            # or .cursor/skills/ — skill discovery root
│   ├── ba-deliver/SKILL.md            # conductor + run/status/resume routes
│   ├── ba-srs/SKILL.md
│   ├── ba-flow/SKILL.md
│   ├── ba-mockup/SKILL.md
│   └── ba-*/scripts/                  # thin wrappers → ba-tools (optional)
├── ba-tools/                          # Python package — deterministic CLI
│   ├── ba_core/
│   │   ├── cli.py                     # JSON stdout contract, exit 2 errors
│   │   ├── paths.py                   # --repo-root containment
│   │   ├── hash.py                    # SHA-256, canonical JSON serialization
│   │   ├── gates/                     # citation, quality, render-safety, …
│   │   ├── render/                    # srs_render.py, mermaid, docx hooks
│   │   ├── trace/                     # trace records, drift / stale detection
│   │   ├── index/                     # INDEX.md generator (derived view)
│   │   ├── runner/                    # executable workflow runner (BRD-027)
│   │   └── templates/                 # srs.md, INDEX templates
│   └── tests/                         # conformance corpus (≥50 mutations)
├── installer/                         # one-shot Windows + POSIX setup
└── .ba-ops/                           # per-BA-project file-state (often in UC repo)
    ├── config.json
    ├── coverage-policy.json
    ├── business-goals.json
    ├── STATE.md
    ├── INDEX.md                       # derived — never hand-edited as SoT
    ├── srs/<slug>/
    ├── runs/<run-id>/
    └── …
```

### Structure Rationale

- **`ba-tools/` separate from skills:** Runtime-agnostic CLI usable in CI, conformance suite, and any chat host (BRD §12.1 footnote, R-9).
- **Skills colocated under `.agents/` or `.cursor/skills/`:** Progressive disclosure — BA sees `$ba-*`; `ba-tools` stays internal to skill workflows.
- **`.ba-ops/` in the BA project repo:** Traceability travels with the use-case repo Git history; harness is portable via `--repo-root`.
- **`runs/<id>/candidates/` staging:** Enforces BR-007 — candidates never count toward coverage until runner promotes.

## Architectural Patterns

### Pattern 1: Candidate → Gate → Promote

**What:** Agent writes only to staging; runner runs gates; atomic promotion updates canonical + trace + INDEX.

**When to use:** Every mutating artifact route (SRS, flow, mockup, plugins).

**Trade-offs:** More disk I/O and ceremony; eliminates false-green and LLM "already passed" prose (R-1).

**Example:**
```python
# Skill workflow (conceptual) — agent never touches canonical directly
# 1. Agent writes .ba-ops/runs/<run-id>/candidates/srs/requirements.json
# 2. ba-tools verify --candidate ...  → exit 0 + evidence JSON
# 3. ba-tools run promote --step srs  → atomic replace canonical pair
# 4. ba-tools trace write + index regen
```

### Pattern 2: Executable Runner as Sole Sequencer

**What:** `$ba-deliver run` invokes `ba-tools run` (or equivalent) which reads `coverage-policy.json` + `config.profile` and advances **one route at a time** (SRS → flow → mockup → index per light tier).

**When to use:** Always for delivery; skills may be invoked standalone but conductor path goes through runner.

**Trade-offs:** Duplicates some orchestration logic that agents could "describe"; buys resume, audit journal, and ordering guarantees (BRD-027, US-07).

**Example:**
```json
// .ba-ops/runs/<run-id>/plan.json (runner-owned)
{
  "uc": "user-registration",
  "profile": "light",
  "routes": ["srs", "flow", "mockup", "index"],
  "current": "flow",
  "completed": ["srs"]
}
```

### Pattern 3: Derived Views, Canonical Registries

**What:** `requirements.json` is canonical; `SRS.md` and `INDEX.md` are deterministic projections (SRS-SPEC N-1…N-5, BRD-003).

**When to use:** All REQ-ID spine artifacts.

**Trade-offs:** Requires render step on every registry change; prevents Markdown-only drift.

### Pattern 4: Profile Tier as Control Plane

**What:** One `profile` field (`light` | `standard` | `strict`) drives coverage policy, gate set, and optional plugins — not scattered flags.

**When to use:** All projects; default `light` for golden path (BRD-028, Appendix D).

**Trade-offs:** Policy JSON must stay in sync with tier matrix; regression tests needed to prevent ceremony creep into `light` (R-11).

### Pattern 5: REQ-ID Trace Spine

**What:** Stable IDs flow registry → downstream `req_ids` metadata → trace hashes → INDEX rows (`ok|gap|orphan|stale|waived`).

**When to use:** Core product value (OBJ-2); built after SRS canonical exists.

**Trade-offs:** Up-front ID discipline; pays off in drift detection and handoff trust.

## Data Flow

### Golden Path (light tier)

```
Source (UC / brief)
    │
    ▼
$ba-deliver run --uc <slug>
    │
    ├──► ba-tools run start ──► STATE.md + runs/<id>/journal.jsonl
    │
    ├──► [route: srs]
    │       $ba-srs workflow ──► candidate requirements.json + inputs
    │       ba-tools verify/lint/render ──► gate evidence
    │       runner promote ──► .ba-ops/srs/<slug>/requirements.json + SRS.md
    │       ba-tools trace write ──► hash links source ↔ registry
    │
    ├──► [route: flow]
    │       $ba-flow ──► mermaid/<slug>/*.md (frontmatter req_ids)
    │       gates + promote + trace
    │
    ├──► [route: mockup]
    │       $ba-mockup ──► mockup/<slug>/*.html|md
    │       gates + promote + trace
    │
    └──► [route: index]
            ba-tools index ──► INDEX.md (derived RTM)
    │
    ▼
BA reads INDEX.md ──► fix gaps ──► $ba-deliver resume (if needed)
    │
    ▼
Handoff-ready (0 gap/orphan/stale for UC REQs)
```

### Drift Detection Flow

```
Edit source OR canonical registry OR downstream artifact
    │
    ▼
ba-tools trace compare (on status/run/index)
    │
    ├── hash match ──► coverage row stays current
    │
    └── hash mismatch ──► artifact marked stale
              │
              ▼
        INDEX ≠ ok; publish blocked (BR-004, BR-004)
              │
              ▼
        Re-run affected route → promote → trace refresh
```

### State Management

```
.ba-ops/STATE.md          ← runner cursor (open UC, current route, resume token)
.ba-ops/runs/<id>/        ← append-only journal + gate evidence + candidates
Canonical artifact dirs   ← only runner promote writes
INDEX.md                  ← regenerated; never authoritative input
Chat session              ← ephemeral; not source of truth (BRD-021)
```

### Key Data Flows

1. **Authoring flow:** Source text → agent analysis → **candidate** JSON/MD → gates → **canonical** → trace record with content hashes.
2. **Coverage flow:** `requirements.json` registry + `coverage-policy.json` + trace records → INDEX status per REQ-ID (anti false-green, BRD-026).
3. **Resume flow:** `STATE.md` + journal → runner skips completed routes with unchanged input hashes (BRD-011, AC-BRD-027-03).
4. **Strict publish flow:** All routes current → `$ba-docx` bundle → `MANIFEST.json` hashes → human sign-off ID (validation, not verification — SRS-SPEC C.5).

## Suggested Build Order

Dependencies dictate **vertical slices**: each phase should deliver end-to-end capability for one spine segment before adding ceremony tiers.

| Order | Component | Depends On | Delivers | Roadmap rationale |
|-------|-----------|------------|----------|-------------------|
| **1** | `ba-tools` skeleton: CLI contract, `--repo-root`, errors JSON, `doctor`, `init` | — | Repo bootstrap, preflight | Nothing else can enforce gates without I/O contract (BRD-019–022) |
| **2** | File-state schemas: `config.json`, `business-goals.json`, `coverage-policy.json`, atomic write + filelock | 1 | `.ba-ops/` layout | Profile and coverage are inputs to runner and INDEX (Appendix B) |
| **3** | Hash + path + schema utilities; `verify` foundation | 1–2 | Deterministic checks | Shared by all gates (NFR-005, NFR-009) |
| **4** | SRS vertical: `$ba-srs` + `requirements.json` schema + `render` + citation-exists gate | 1–3 | First canonical artifact + REQ-ID spine | Core value starts here (US-01, BRD-006–007) |
| **5** | Trace + INDEX: trace write, `index` command, stale detection | 4 | RTM view, drift signal | Enables OBJ-2/OBJ-4 before full deliver loop |
| **6** | Flow + mockup skills + artifact gates (req_ids metadata) | 4–5 | Spine SRS→flow→mockup | Completes light-tier artifact chain |
| **7** | Executable workflow runner + `$ba-deliver` (run/status/resume) | 4–6 | Golden path 1 command | Highest integration risk — build after gates proven (BRD-027, US-03, US-07) |
| **8** | Confirmation gate + promotion atomicity | 7 | Safe overwrites | BRD-015, NFR-010 |
| **9** | Tier extensions: `$ba-intake`, critic, `$ba-bpmn`, `$ba-backlog`, `$ba-docx` | 7–8 | standard/strict | Plugins opt-in; light path already shippable |
| **10** | Team mode (owner guard, `report team`) | 2, 7 | Multi-BA read aggregate | BRD-023–025; strict governance |
| **11** | Installer + conformance corpus (≥50 mutations) | 1–7 | Pilot release gate | BRD §13.4 — blocks false-green regressions |

**Critical path:** 1 → 2 → 3 → 4 → 5 → 7. Flow/mockup (6) can parallel 5 only if trace schema is stable.

**Do not build early:** DOCX/BPMN renderers, blind critic, team report — all depend on runner + promote pattern being correct.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 BA, ≤10 UC (pilot) | Monolithic `ba-tools` + local `.ba-ops/`; no server |
| ≤5 BA, team mode | Owner-folder guards; read-only aggregate via `report team`; no shared write |
| ≤500 REQ / project | Linear verify/index (<8s per NFR-001); conformance corpus on each CLI release |
| 100k+ users | **Out of scope v1** — would need remote state store; contradicts local-first BRD |

### Scaling Priorities

1. **First bottleneck:** Gate + index runtime at 200–500 REQs — optimize hash caching and incremental trace compare before splitting services.
2. **Second bottleneck:** Parallel BA edits — filelock + owner guard (already specified); avoid multi-writer canonical without migration workflow.

## Anti-Patterns

### Anti-Pattern 1: Agent-Owned Workflow Graph

**What people do:** Let `$ba-deliver` skill prose describe "now do flow" without runner enforcing transitions.

**Why it's wrong:** LLM skips steps; trace breaks silently (R-1).

**Do this instead:** Runner is the only component that marks routes complete and calls promote.

### Anti-Pattern 2: Markdown as Requirements Source of Truth

**What people do:** Edit `SRS.md` directly for speed.

**Why it's wrong:** Violates SRS-SPEC N-1; INDEX/orphans undetectable.

**Do this instead:** Edit `requirements.json`; render `SRS.md`.

### Anti-Pattern 3: Candidate Counts as Coverage

**What people do:** Point INDEX at staging files before gate pass.

**Why it's wrong:** False-green handoff (R-2).

**Do this instead:** BR-007 — only post-promote canonical paths in trace and INDEX.

### Anti-Pattern 4: LLM Inside `ba-tools`

**What people do:** Call cloud API from verify/render for "smart lint."

**Why it's wrong:** Breaks determinism, zero-network, auditability (NFR-006, NFR-009).

**Do this instead:** Agent produces evidence; CLI checks structure, hashes, citations.

### Anti-Pattern 5: Screenshot / Synthetic Render Fallback

**What people do:** Pillow or manual PNG when draw.io/mmdc missing.

**Why it's wrong:** BR-002; non-reproducible artifacts.

**Do this instead:** `doctor` hard-fail with install instructions; tier `light` uses inline Mermaid text.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Chat skill runtime (Cursor, etc.) | Discovers `$ba-*` SKILL.md; runs shell for `ba-tools` | Skills runtime-neutral; `.ba-ops/` survives host changes (R-9) |
| `@mermaid-js/mermaid-cli` | Subprocess from `ba-tools render` | Optional at light; required for PNG/SVG export |
| draw.io Desktop CLI | Subprocess for BPMN/DOCX embed | Opt-in plugin; hard-fail if missing |
| Git | BA commits `.ba-ops/` | Audit trail; not invoked by core CLI for network |
| LLM provider (org policy) | **Outside** `ba-tools`; inside agent host only | NFR-009 — product does not claim data never leaves repo with cloud LLM |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Skill ↔ `ba-tools` | Subprocess, stdout JSON / stderr JSON, exit 2 = fail | Skills must parse exit code, not agent prose |
| Runner ↔ gates | In-process or subcommand calls; evidence → `runs/<id>/` | Fixed gate order for SRS (SRS-SPEC D.3) |
| Runner ↔ skills | Runner triggers skill routes (via host) or embedded step handlers | Conductor skill wraps runner invocation |
| INDEX ↔ registry | Read-only derive | Regenerated after every successful promote on index route |
| Team report ↔ owner roots | Read-only JSON aggregate | Never mutates foreign `.ba-ops/` (BRD-025) |

## Sources

- `docs/BRD-v1.0.md` v1.0 — §5–6 harness model, §8.E–G runtime, Appendix A–B, BRD-027 runner (HIGH)
- `docs/SRS-SPEC.md` v1.0 — Part A determinism, Part D workflow, D.3 gate ordering (HIGH)
- `.planning/PROJECT.md` — product architecture summary, constraints (HIGH)
- [Harness Engineering for AI Coding Agents (Augment Code)](https://www.augmentcode.com/guides/harness-engineering-ai-coding-agents) — PEV, rules + deterministic gates (MEDIUM)
- [Building AI Coding Agents for the Terminal (arXiv)](https://arxiv.org/html/2603.05344v1) — harness vs scaffolding layers (MEDIUM)
- [orc — deterministic agent orchestrator CLI](https://github.com/jorge-barreto/orc) — file-state phase machine analog (MEDIUM)
- [Cursor Agent Skills docs](https://cursor.com/help/customization/skills) — skill vs script determinism split (MEDIUM)

---
*Architecture research for: ba-daily-ops (BA Daily Ops)*
*Researched: 2026-07-20*
