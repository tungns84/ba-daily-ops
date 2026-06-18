# Roadmap: BA Daily Operators

## Current Status

**Milestone v1.0 — CodexApp-first daily spine: ✅ SHIPPED 2026-06-18** (audit passed)

The v1 daily spine is complete: deterministic `ba-tools` CLI + `.ba-ops/` spine, four foundational gates, and the four spine operators driven by the `ba-uc` conductor (use case → SRS → diagram → mockup → traceability index, REQ-ID-traced end-to-end).

→ Next milestone not yet defined. Run `/gsd-new-milestone` to scope **v2** (Claude Code transform + deferred plugins).

## Shipped Milestones

<details>
<summary><strong>v1.0 — CodexApp-first daily spine</strong> (Phases 1–5, 20 plans, shipped 2026-06-18)</summary>

- **Phase 1: Deterministic ba-tools CLI + Foundational Gates** — file/hash/command-provable CLI, `.ba-ops/` scaffold, lockfile state, REQ-ID stability lint, citation-exists verify, CI byte-check gate.
- **Phase 2: ba-srs-analyze + Quality Gate + Traceability Core** — sources → atomic grounded requirements with `source_trace`, gated by `verify` + fresh-context `ba-critic` CoVe loop; INDEX.md matrix + gap/orphan/stale drift detection.
- **Phase 3: ba-mermaid Diagram Operator** — UC/requirement → MD-inline Mermaid diagram citing its REQ-IDs, optional `mmdc` export.
- **Phase 4: ba-mockup Operator** — requirements → UI mockup at `--fidelity html|wireframe`, each screen citing its REQ-IDs.
- **Phase 5: ba-uc Conductor + End-to-End Integration** — resumable sequential loop (srs-analyze → mermaid → mockup → index) with Quality + index-integrity gates; the spine's integration test.

Full detail: [`milestones/v1.0-ROADMAP.md`](milestones/v1.0-ROADMAP.md) · requirements: [`milestones/v1.0-REQUIREMENTS.md`](milestones/v1.0-REQUIREMENTS.md) · audit: [`v1.0-MILESTONE-AUDIT.md`](v1.0-MILESTONE-AUDIT.md) · index: [`MILESTONES.md`](MILESTONES.md)

</details>

---
*Last updated: 2026-06-18 — v1.0 milestone complete (5/5 phases, 44/44 requirements, audit passed). Run `/gsd-new-milestone` to begin v2.*
