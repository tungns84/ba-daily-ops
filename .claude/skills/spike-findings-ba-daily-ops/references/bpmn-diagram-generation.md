# BPMN Diagram Generation (`ba-make-diagram`)

Implementation blueprint for the v2 `ba-make-diagram` operator: turn a UC/requirements into a formal BPMN diagram (draw.io) that joins the REQ-ID traceability matrix. Synthesized from spikes 001–004 — all proven, working code. Follow this; do not re-spike.

## Requirements (non-negotiable)

- **Agent emits a logical model, never coordinates.** Hand-authored x/y is the quality ceiling (LLMs are weak at spatial math; overlaps appear and the draw.io export does NOT catch them — exits 0 anyway). A deterministic engine must lay out.
- **Layout engine = ELK (elkjs) → `.drawio` (Path A).** NOT `bpmn-auto-layout` (drops swimlane DI) and NOT a `.bpmn` render path (draw.io CLI cannot import `.bpmn`).
- **BPMN with draw.io primitives, not native `mxgraph.bpmn.*` stencils** — native event stencils drop their icon on headless export.
- **Resolve draw.io by absolute path / flag / env — never PATH** (not on PATH on Windows).
- **Embed REQ-IDs in task labels** → feed `ba-tools trace write --kind diagram --req-ids`. Reuse the existing trace/index contract (no ba-tools core change).
- **Export headless via the draw.io CLI**, then run a geometry gate before declaring done.

## How to Build It

Pipeline: `agent → logical model (JSON) → ELK layout → emit .drawio → draw.io CLI export → geometry gate → trace + index`.

### 1. Agent emits a logical BPMN model (no coordinates)
Schema (see `sources/004-bpmn-layout-engine/model.json`):
```json
{ "pool": "...", "lanes": ["BA","System"],
  "nodes": [{ "id","type":"start|task|gateway|end","lane","label","req_ids":[] }],
  "edges": [{ "id","source","target","label" }] }
```
The reference skill `ba-make-diagram-bpmn-2-drawio` is a good *semantic* spec for THIS step (BPMN classification, Pool-vs-Lane, Message-vs-Sequence, sub-process compaction for big UCs). Use its rules to produce the model — but ignore its manual layout rules / coordinate authoring / "XML-only output".

### 2. ELK layout (deterministic) — `sources/004-bpmn-layout-engine/pathA-elk.mjs`
```
npm install elkjs            # 0.11.1, pure JS, ~5s
```
- `import ELK from 'elkjs/lib/elk.bundled.js'`
- `elk.algorithm=layered`, `elk.direction=RIGHT`, `elk.edgeRouting=ORTHOGONAL`, spacing ~50–70.
- Use ELK's **x** (layer ordering, overlap-free); assign **y** by deterministic lane band (`laneIndex * LANE_H`, node centered in its lane). This hybrid keeps cross-lane fidelity ELK alone won't give.

### 3. Emit `.drawio` (primitives + ELK waypoints)
- Pool = `swimlane;horizontal=0;startSize=30`; each lane = nested `swimlane;horizontal=0`.
- Node styles: start `ellipse;fillColor=#d5e8d4;strokeColor=#82b366`; end `ellipse;strokeWidth=3;fillColor=#f8cecc;strokeColor=#b85450`; gateway `rhombus;fillColor=#ffe6cc;strokeColor=#d79b00`; task `rounded=1;whiteSpace=wrap;arcSize=20;fillColor=#dae8fc;strokeColor=#6c8ebf`.
- Edges: `edgeStyle=orthogonalEdgeStyle;endArrow=block`. **Emit ELK edge `sections` bend-points as `mxGeometry` `Array as="points"` waypoints** — otherwise draw.io re-routes branches (the spike-004 "no" branch drifted to the wrong origin).
- Escape labels: `&amp; &lt; &gt; &quot;`. No negative coords.

### 4. Export (draw.io CLI) — `sources/001-drawio-cli-env/`
```
"C:\Program Files\draw.io\draw.io.exe" -x -f svg -o out.svg in.drawio --no-sandbox
"C:\Program Files\draw.io\draw.io.exe" -x -f png -s 2 -o out.png in.drawio --no-sandbox
```
Exit 0 + `in.drawio -> out.svg` line = success. Headless, no GUI. Resolve the exe via flag/env/known-paths chain (mirror CLAUDE.md render-CLI resolution).

### 5. Geometry gate (ba-tools, deterministic)
Assert: bounding-box overlap = 0; all coords in-canvas; width within budget; edges don't cut node boxes. Exit 2 if violated → operator re-lays-out. This replaces the reference skill's agent-side "validate it yourself" — quality must be CLI-proven.

### 6. Trace + index — `sources/003-bpmn-trace-index/`
```
ba-tools trace write --kind diagram --slug <slug> --req-ids FR-001,FR-002 \
  --artifact <.drawio or exported img> --source-doc <uc.md> --requirements <requirements.json>
ba-tools index update
```
`--kind diagram` is accepted (regex `^[a-z0-9][a-z0-9-]*$`); index covers the REQ-IDs (gaps/orphans computed) with zero ba-tools change. Route `diagram` = author+export+trace+index; route `export` = the CLI export step.

## What to Avoid

- **Agent-authored coordinates / spacing / waypoints** — the failure mode. Let ELK place.
- **`mxgraph.bpmn.*` native event stencils** — icon drops on headless export (spike 002). Use primitives.
- **`bpmn-auto-layout`** — emits no swimlane DI; lanes vanish (spike 004). Only consider for a *secondary* lane-less standard-`.bpmn` export if cross-tool portability is needed.
- **Feeding `.bpmn` to the draw.io CLI** — "Export failed"; the CLI takes `.drawio` only. Rendering `.bpmn` needs bpmn-js/puppeteer (heavy) — avoid.
- **Assuming draw.io on PATH** — it isn't (Windows); resolve by absolute path.
- **Trusting export exit code for layout quality** — export exits 0 even with overlaps. Layout quality = the geometry gate's job.

## Constraints

- draw.io desktop CLI: `.drawio` input only; no headless auto-layout command (export-only); not on PATH.
- elkjs 0.11.1 (pure JS, no native deps). bpmn-auto-layout is ESM-only and lane-incomplete.
- Windows: run any `ba-tools` subprocess with `PYTHONUTF8=1` (cp1252 `--help`/non-ASCII crash).
- Determinism boundary (CLAUDE.md §5): agent owns the model (judgement); ELK layout + draw.io export + geometry gate + trace/index are the deterministic side.

## Origin

Synthesized from spikes: 001 (draw.io CLI env), 002 (agent BPMN authoring), 003 (trace/index `--kind diagram`), 004 (layout-engine comparison — ELK wins).
Source files: `sources/001-drawio-cli-env/`, `sources/002-agent-bpmn-xml/`, `sources/003-bpmn-trace-index/`, `sources/004-bpmn-layout-engine/`.
