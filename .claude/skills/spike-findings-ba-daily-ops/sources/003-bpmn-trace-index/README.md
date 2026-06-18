---
spike: 003
name: bpmn-trace-index
type: standard
validates: "Given an exported BPMN diagram, when trace write --kind diagram + index update run, then its REQ-IDs join the traceability matrix"
verdict: VALIDATED
related: [001, 002]
tags: [trace, index, traceability, bpmn, plugin-ba-make-diagram, ba-tools]
---

# Spike 003: BPMN → Trace → Index Integration

## What This Validates
Given an exported BPMN diagram artifact, when `ba-tools trace write --kind diagram` then `ba-tools index update` run, then the diagram's REQ-IDs join the traceability matrix exactly like mermaid/mockup do. Confirms the existing v1 `ba-tools` needs NO change to support a BPMN plugin's trace/index step.

## How to Run
(Run in a throwaway `--repo-root` scratch.)
```
ba-tools init ba-uc
ba-tools trace write --kind srs --slug uc-001 --artifact requirements.json --source-doc docs/uc-001.md --requirements requirements.json
ba-tools trace write --kind diagram --slug uc-001 --req-ids FR-001,FR-002 --artifact uc-001.drawio --source-doc docs/uc-001.md --requirements requirements.json
ba-tools index update
```

## What to Expect
`trace write --kind diagram` returns ok with the req_ids; `index update` returns `gaps: []`, `orphans: []` (the diagram covers the SRS REQ-IDs).

## Results
**VALIDATED.** `--kind diagram` (a new kind string) is accepted — `trace_cmd` validates kind against `^[a-z0-9][a-z0-9-]*$`, which `diagram` satisfies. `index_cmd` treats all non-srs kinds uniformly for coverage, so the diagram trace covered FR-001/FR-002 → `gaps: []`, `orphans: []`. No ba-tools code change required; the BPMN plugin reuses the existing trace/index contract verbatim.

### Finding
The traceability spine is kind-agnostic for non-srs artifacts. A `ba-make-diagram` BPMN export plugs into trace/index with zero core changes — only the operator workflow + draw.io export wrapper are new work.
