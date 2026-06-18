---
spike: 004
name: bpmn-layout-engine
type: comparison
validates: "Given one logical BPMN model (pool, 2 lanes, start, 6 tasks, exclusive gateway, 2 ends), when laid out by each engine and exported, then which yields the cleanest overlap-free lane'd BPMN at acceptable integration cost"
verdict: A WINS
related: [001, 002, 003]
tags: [bpmn, layout, elk, bpmn-auto-layout, drawio, plugin-ba-make-diagram]
---

# Spike 004: BPMN Auto-Layout Engine — A vs B vs C

The architecture-deciding spike ([[bpmn-quality-architecture]]). Root principle: the agent must NOT place coordinates; a deterministic engine lays out a logical model. Which engine?

Shared input: `model.json` — pool "Study Draft Creation", lanes [BA, System], start + 6 flow nodes + exclusive gateway (yes/no) + 2 end events. Same model fed to every path.

## Environment
- node v22.22.0, npm 11.12.1 ✓ · npm registry reachable ✓
- **graphviz `dot` NOT installed** → Path C not run (would need a system install; A/B are the real architecture fork anyway).

## How to Run
```
npm install elkjs bpmn-auto-layout
node pathA-elk.mjs            # -> pathA.drawio
"$DRAWIO" -x -f png -s 2 -o pathA.png pathA.drawio --no-sandbox
node pathB-bpmnautolayout.mjs # -> pathB-input.bpmn (semantic) + pathB.bpmn (laid out)
```

## Results — head to head

| Criterion | A: ELK → .drawio | B: bpmn-auto-layout → .bpmn | C: graphviz dot |
|-----------|------------------|-----------------------------|-----------------|
| No overlap | ✅ ELK layering | ✅ (flow nodes) | not run |
| **Lane fidelity** | ✅ nodes in correct lanes (ELK x-layering + deterministic lane-band y) | ❌ **lanes dropped — 0 lane DI emitted** | not run |
| Edge routing | ✅ orthogonal (minor: draw.io re-routes "no" branch; fixable by passing ELK bend points as waypoints) | ✅ edges routed (14 BPMNEdge) | — |
| Readability (rendered) | ✅ **PNG verified** — professional, clean | ⚠ **not rendered** — draw.io CLI cannot import `.bpmn` ("Export failed"); needs bpmn-js/puppeteer | — |
| Integration effort | **Low** — reuse proven draw.io CLI (spike 001/002) + ~90-line emitter | **High** — puppeteer render stack + lanes need a separate layout pass | n/a (system install) |
| Portability | draw.io-bound (`.drawio`) | ✅ standard `.bpmn` (Camunda/Signavio) — but lane-less DI | — |

### Path A — WINNER ✓
ELK `layered` (direction RIGHT) gave clean x-layering with zero overlap; deterministic lane bands placed every node in its correct lane. draw.io CLI exported the `.drawio` to a professional, readable BPMN PNG (verified visually). Markedly cleaner than the hand-authored spike 002 (which had label overlap). Blemish: the gateway "no" branch was re-routed by draw.io (origin looks near the next task, not the gateway) — fix by emitting ELK edge `sections` bend points as `mxGeometry` waypoints instead of letting draw.io auto-route.

### Path B — weaker for this project
`layoutProcess()` ran and produced valid BPMN-DI for the 8 flow nodes with sane, non-overlapping bounds (branch end correctly dropped to a second row). BUT: **it emitted no lane DI (`bpmnElement="lane_*"` count = 0)** — `bpmn-auto-layout` does not lay out swimlanes. For this project, where lanes (roles/systems) are central to the BPMN, that is disqualifying without extra work. Also: draw.io CLI cannot import `.bpmn` for export, so rendering requires the bpmn-js/puppeteer browser stack (a much heavier dependency than the already-present draw.io desktop). Its one win is standard-`.bpmn` portability.

### Path C — not run
`dot` is not installed; deferred (system install, and not needed given A is decisive).

## Decision
**Adopt Path A for `ba-make-diagram`:** agent → logical model (no coords) → ELK x-layering + deterministic lane-band y → emit `.drawio` (with ELK bend-point waypoints) → draw.io CLI export → geometry gate + REQ-ID trace/index. If standard-`.bpmn` portability is required later, emit a *secondary* semantic `.bpmn` (the emitter already works) — accept lane-less DI for tool exchange, or add a lane layout pass then.

## Investigation Trail
1. Installed elkjs 0.11.1 + bpmn-auto-layout (pure JS, ~5s).
2. Path A: ELK layered on the flow graph → x positions sane (start:12 … end_ok:1122); snapped y to lane bands; emitted `.drawio`; draw.io export → PNG verified clean, correct lanes, no overlap.
3. Path B: emitted semantic BPMN 2.0 (with `laneSet`) → `layoutProcess` → DI present but **lane DI absent**; draw.io can't import `.bpmn` → no render without puppeteer.
4. Path C: skipped — `dot` unavailable.
