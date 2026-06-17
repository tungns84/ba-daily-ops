# Project Research Summary: BA Daily Operators

**Domain:** Requirements-engineering / BA tooling — deterministic CLI + LLM agent suite
**Researched:** 2026-06-17
**Confidence:** HIGH

## Executive Summary

BA Daily Operators is a CodexApp-first Python CLI suite for grounded requirements
engineering. It combines a deterministic file/hash/command-verifiable CLI layer
(`ba-tools`, Layer 4) with LLM agents (Layer 3) orchestrated by a thin conductor
workflow, backed by persistent `.ba-ops/` state (Layer 5).

The key differentiator is architectural: the citation-exists gate is enforced
mechanically (≥12-char verbatim substring check in `ba-tools verify`, outside the
agent boundary), making confabulation structurally impossible for `stated`
requirements. REQ-ID traceability propagates end-to-end (SRS → diagram → mockup →
backlog) with automated gap/orphan/stale detection.

The primary risk is **determinism-boundary erosion**: judgement leaking into the CLI,
or verification leaking into agents. Mitigation requires deterministic tests, hard
architectural lines (lockfile guard on STATE.md, `allow_implicit_invocation: false`
on spine skills, hard-fail on missing render CLIs), and a CI byte-check gate.

## Key Findings

### Recommended Stack

**Core (v1 spine):**
- **Python 3.11+** — `ba-tools` runtime (3.11+ for `hashlib.file_digest()`); resolve via `sys.executable`.
- **stdlib hashlib / json / argparse** — SHA-256, UTF-8 JSON to stdout (errors exit 2), ~10 subcommands.
- **filelock (PyPI 3.x)** — cross-platform STATE.md lock; preferred over raw `os.open(..., O_EXCL)`.

**Plugin-path (deferred):**
- **@mermaid-js/mermaid-cli 11.15.0** — only maintained renderer; no synthetic fallback.
- **python-docx 1.2.0** — **NO native `replace_image()`** (issue #192, open since 2015); media-replace = direct OOXML blip rId surgery.
- **draw.io desktop CLI** — export-to-PNG; flags from community/issue tracker (no official CLI ref page).

### Expected Features

**Table stakes:** atomicity/verifiability checks (IEEE 830 §3.5), REQ-ID registry,
source-grounded requirements (`source_trace` schema), traceability matrix (ISO 29148),
gap/orphan/stale detection, resumable pipeline, deterministic JSON, inline Mermaid,
two-tier mockups.

**Differentiators:** verbatim citation-exists gate (mechanical, outside agent boundary);
CoVe `ba-critic` loop (4-stage, ≤3 revisions, semantic support); REQ-ID traceability
spine with drift detection; source-hash STALE flagging; Quality gates between conductor
steps.

**Anti-features (deliberately NOT built):** synthetic diagram rendering; GUI dashboard;
implicit invocation on spine; DOCX/draw.io on the daily spine (plugin-only).

### Architecture Approach

Five layers: Skills (L1) → Workflows (L2) → Agents (L3) → CLI (L4) → File-state (L5).
`ba-uc` conductor is the only inter-operator coupling; all others communicate only via
REQ-IDs in `.ba-ops/` metadata, which `ba-tools index update` scans to rebuild INDEX.md.
Resumability = STATE.md + `uc-status` (not saga/checkpoint frameworks). Lockfile-guarding
(`O_EXCL`, stale-lock 10s) makes concurrent writes safe without a DB.

### Critical Pitfalls

1. **Citation substring gaming** — span exists but doesn't justify the requirement → `ba-critic` semantic check + `lint` boilerplate flag.
2. **CoVe false convergence** — critic primed by draft context → critic receives source + requirements only, NOT the draft (instruction-enforced in v1).
3. **Determinism erosion (judgement in CLI)** — free-text route inference / suggested rewrites → reasoning stays in agents; `resolve-route` returns only static DEFAULT_ROUTE.
4. **Determinism erosion (verification in agents)** — inline hash/citation checks → workflow always calls explicit `ba-tools verify`.
5. **Byte-budget silent truncation** — files silently cut at 32,768 B with no warning → CI byte-check gate before any skill authored.
6. **REQ-ID churn** — highest-cost recovery → ID-stability lint from Phase 1 (IDs permanent, never renumbered).

## Implications for Roadmap

**Build order — all four researchers agree:**
`ba-tools` → `ba-srs-analyze` + traceability core → `ba-mermaid` / `ba-mockup` → `ba-uc` conductor → plugins (deferred).

Suggested phase shape:
1. **`ba-tools` deterministic CLI core** — init, lint (incl. ID-stability), verify (citation-exists), state (lockfile), resolve-route, index, uc-status, trace, template, extract-uc + **CI byte-check gate**.
2. **`ba-srs-analyze` + Quality gate + CoVe `ba-critic`** — highest-value differentiator; REQUIREMENTS.md registry + `source_trace` schema; `allow_implicit_invocation: false`.
3. **Traceability spine (INDEX.md) + drift detection** — validate REQ-ID coupling before more operators.
4. **`ba-mermaid`** — inline Mermaid (flowchart/sequence/state), REQ-ID coverage gate.
5. **`ba-mockup`** — `--fidelity wireframe|html`, REQ-ID coverage gate. (4 and 5 are independent.)
6. **`ba-uc` conductor + E2E** — sequential loop, Quality gate per step, resumable; integration fixtures (concurrent-write, resume-from-step, gate-reject).
7. **Plugins** — deferred milestone (mermaid render export, draw.io BPMN, DOCX media-replace).

## Cross-Cutting Corrections Against DESIGN.md

1. **`allow_implicit_invocation` nesting (§3)** — belongs under `policy:`, not flat YAML.
2. **npx fallback (§5)** — must be `npx -p @mermaid-js/mermaid-cli mmdc` (package name ≠ binary name).
3. **python-docx media-replace (§5)** — no `replace_image()`; direct OOXML rId surgery (traverse `InlineShape._inline...blipFill.blip`, swap `r:embed`, `drop_rel`/`relate_to`). python-docx 1.2.0.
4. **Byte budget (§7)** — 32,768 B truncation is SILENT (GitHub #7138, closed not-planned) → CI gate non-negotiable.

## Open Decisions — Resolve Before Phase 1

1. **Citation-exists scope** — section-scoped vs whole-doc substring match. *Recommend section-scoped* (closes boilerplate-gaming gap); implement via `--cite-scope section|document`.
2. **WARN_INJECTION** — advisory vs hard gate. *Recommend advisory in P1, promote to hard gate in P2* for external-source `stated` requirements.
3. **`ba-critic` loop termination** — early-exit on convergence vs always 3 loops. *Recommend early-exit with logging* ("passed early" vs "passed after N").
4. **REQ-ID stability lint phase** — Phase 1 vs Phase 3. *Recommend Phase 1* with a renumbered-requirements fixture; flag material statement changes on an existing ID.

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Stack | HIGH | Codex docs + PyPI + GitHub issues (#192, #7138) verified |
| Features | HIGH | IEEE 830 / ISO 29148 + DESIGN §2/§5/§6 + CoVe (arXiv 2309.11495) |
| Architecture | HIGH | DESIGN §0–§10; build order confirmed independently by all 4 researchers |
| Pitfalls | HIGH | DESIGN invariants + §11 non-negotiables; testable prevention |

**Overall: HIGH.**

---
*Sources: STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md in `.planning/research/`.*
