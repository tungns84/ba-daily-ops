# Milestones

Shipped milestones for BA Daily Operators. Each links to its archived roadmap + requirements snapshot.

| Version | Name | Shipped | Phases | Plans | Status | Archive |
|---------|------|---------|--------|-------|--------|---------|
| v1.0 | CodexApp-first daily spine | 2026-06-18 | 1–5 | 20 | ✅ passed | [roadmap](milestones/v1.0-ROADMAP.md) · [requirements](milestones/v1.0-REQUIREMENTS.md) |

## v1.0 — CodexApp-first daily spine

**Shipped:** 2026-06-18 · **Audit:** passed (44/44 requirements, 5/5 phases verified, 18/18 integration links, E2E spine proven, all phases threats_open:0)

The v1 daily spine: a deterministic `ba-tools` Python CLI + `.ba-ops/` file-state spine, the four foundational gates, and the four spine operators driven by the `ba-uc` conductor — turning use case → SRS → process diagram → UI mockup → traceability index into one resumable, hash-provable, REQ-ID-traced loop.

**Key accomplishments:**
- **Deterministic `ba-tools` CLI** (Phase 1) — 16 commands, stdlib-only spine, UTF-8 JSON contract, `BaToolsError` exit 2, lockfile-guarded `STATE.md`, REQ-ID-stability lint, citation-exists verify, 32,768 B byte-check gate.
- **`ba-srs-analyze` + Quality gate + traceability core** (Phase 2) — sources → atomic grounded requirements with `source_trace`, gated by `verify` + fresh-context `ba-critic` CoVe loop; INDEX.md matrix with gap/orphan/stale drift detection.
- **`ba-mermaid`** (Phase 3) — UC/requirement → MD-inline Mermaid diagram citing its REQ-IDs; optional `mmdc` export, no synthetic render.
- **`ba-mockup`** (Phase 4) — requirements → UI mockup at `--fidelity html|wireframe`, each screen citing its REQ-IDs; no synthetic-render path.
- **`ba-uc` conductor + E2E integration** (Phase 5) — the only operator that invokes others: srs-analyze → mermaid → mockup → index as a resumable sequential loop with D-G1 Quality + D-G2 index-integrity gates; GATE-03 Safety contract (plugin-deferred, spine-exempt). Spine's integration test proven live (full deliver, gate-reject, resume).

**Stats:** 165 commits, 218 files, +38,444 LOC, 2026-06-17 → 2026-06-18. ba-tools 4,252 LOC; tests 8,712 LOC; 305-test suite green.

**Carried forward (non-blocking):**
- `/gsd-validate-phase 2` — Phase 2 VALIDATION `nyquist_compliant: false` (partial test-sampling; VERIFICATION passed).
- Tech debt: Phase 1 WR-01/02/05 + IN-01/02/03; `ba-tools --help` UnicodeEncodeError on Windows cp1252 stdout (JSON output safe; workaround `PYTHONUTF8=1`).

**Next:** v2 — Claude Code transform (Task-subagent spawn, command frontmatter, hooks, install-time transform); deferred plugins (`ba-make-diagram`, `ba-uc-delivery`, `ba-backlog-grooming`). `ba-tools` + `.ba-ops/` carry into v2 unchanged.
