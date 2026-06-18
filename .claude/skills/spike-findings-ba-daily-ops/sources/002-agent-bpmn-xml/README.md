---
spike: 002
name: agent-bpmn-xml
type: standard
validates: "Given an agent authors a .drawio BPMN diagram, when exported, then the XML is valid and the output is a clean, readable BPMN process"
verdict: VALIDATED
related: [001, 003]
tags: [drawio, bpmn, authoring, render, plugin-ba-make-diagram]
---

# Spike 002: Agent-Authored BPMN XML

## What This Validates
Given an agent (no GUI) authors a `.drawio` BPMN diagram with pool, start/end events, tasks, exclusive gateway, and labeled sequence flows, when exported via the draw.io CLI, then the XML is valid and the rendered output is a clean, readable BPMN process. **The core risk for `ba-make-diagram`.**

## How to Run
```
DRAWIO="/c/Program Files/draw.io/draw.io.exe"
"$DRAWIO" -x -f png -s 2 -o uc-001-bpmn.png uc-001-bpmn.drawio --no-sandbox
"$DRAWIO" -x -f svg -o uc-001-bpmn.svg uc-001-bpmn.drawio --no-sandbox
```

## What to Expect
Exit 0; PNG/SVG showing a horizontal pool "SRS Generator" with: start event → Validate (FR-002) → gateway "Valid?" → (yes) Produce SRS (FR-001) → Complete within 30s (NFR-001) → success end; (no) → Rejected end.

## Investigation Trail
- Authored UC-001 flow as BPMN using a mix of (a) a native `mxgraph.bpmn.shape` start-event stencil and (b) draw.io primitives for the rest.
- Export succeeded (exit 0); PNG 114.5 KB, SVG 90.3 KB. All REQ-ID labels (FR-001/FR-002/NFR-001), pool title, and gateway label present in SVG; zero error/warning strings.
- PNG visually verified: correct, readable BPMN process.
- **Surprise:** the native `mxgraph.bpmn.shape;symbol=general` start event rendered as a plain circle (the general-event icon did not draw). Not a blocker — it still reads as a BPMN start event.

## Results
**VALIDATED.** An agent can author valid `.drawio` BPMN that exports to an acceptable-quality diagram, with REQ-IDs embedded in task labels (feeds traceability).

### Findings / build guidance
- **Prefer draw.io primitives over native `mxgraph.bpmn.*` stencils:** `ellipse` (events; thin stroke=start, thick=end), `rounded=1` (tasks), `rhombus` (exclusive gateway), `swimlane;horizontal=0` (pool), `edgeStyle=orthogonalEdgeStyle` (sequence flows). These render reliably and ARE the BPMN visual vocabulary. Native stencils are higher-risk (icon may not render).
- Embed REQ-IDs in task labels → the `ba-make-diagram` operator can pass them to `trace write --req-ids` (see spike 003).
- Minor cosmetic: end-event labels near the pool edge can overlap; tune `mxGeometry` x/y. The authoring operator should leave margin.
