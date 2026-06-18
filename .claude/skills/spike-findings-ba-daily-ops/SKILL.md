---
name: spike-findings-ba-daily-ops
description: Implementation blueprint from spike experiments. Requirements, proven patterns, and verified knowledge for building the ba-make-diagram BPMN operator in ba-daily-ops. Use when building or planning BPMN/draw.io diagram generation, ELK layout, or the v2 ba-make-diagram plugin.
---

<context>
## Project: ba-daily-ops

BA Daily Operators — a CodexApp-first operator suite turning daily BA deliverables (use case → SRS → diagram → mockup → traceability index) into reproducible, hash-provable operators. These findings cover the **v2 `ba-make-diagram`** plugin: generating formal BPMN diagrams (draw.io) that join the REQ-ID traceability matrix.

Spike sessions wrapped: 2026-06-18
</context>

<requirements>
## Requirements (non-negotiable for the real build)

- Agent emits a **logical model** (nodes/edges/lanes/req_ids); a deterministic engine lays it out. **Never hand-author coordinates.**
- Layout engine = **ELK (elkjs)** → emit `.drawio`. NOT `bpmn-auto-layout` (drops swimlanes), NOT a `.bpmn` render path (draw.io can't import `.bpmn`).
- Author BPMN with **draw.io primitives** (`ellipse`/`rhombus`/`rounded`/`swimlane`), not native `mxgraph.bpmn.*` stencils (icons drop on export).
- Embed **REQ-IDs in task labels** → `ba-tools trace write --kind diagram --req-ids` → `index update`. Zero ba-tools core change.
- Resolve **draw.io by absolute path / flag / env** (not on PATH). Export headless: `-x -f svg|png [-s 2] -o … --no-sandbox`.
- A deterministic **geometry gate** (overlap=0, in-canvas, width, no edge-through-node) proves layout quality — export exit code does NOT.
</requirements>

<findings_index>
## Feature Areas

| Area | Reference | Key Finding |
|------|-----------|-------------|
| BPMN diagram generation | references/bpmn-diagram-generation.md | Logical-model + ELK layout + draw.io primitives + geometry gate; reuse trace/index `--kind diagram` with no core change |

## Source Files

Original spike source files preserved in `sources/` (001 draw.io env, 002 agent BPMN authoring, 003 trace/index, 004 ELK-vs-bpmn-auto-layout comparison) for complete reference, including the working `pathA-elk.mjs` ELK layout script and example `.drawio` files.
</findings_index>

<metadata>
## Processed Spikes

- 001-drawio-cli-env (VALIDATED)
- 002-agent-bpmn-xml (VALIDATED)
- 003-bpmn-trace-index (VALIDATED)
- 004-bpmn-layout-engine (A WINS — ELK → .drawio)
</metadata>
