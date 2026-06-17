# Phase 1: Deterministic ba-tools CLI + Foundational Gates - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-17
**Phase:** 1-Deterministic ba-tools CLI + Foundational Gates
**Areas discussed:** Lockfile impl, JSON envelope shape, Byte-check wiring, Lint severity model

---

## Lockfile (STATE.md.lock)

| Option | Description | Selected |
|--------|-------------|----------|
| filelock library | CLAUDE.md recommendation; handles Windows network-share/venv edge cases raw O_EXCL misses; one tiny maintained dep, FileLock(timeout=10) | ✓ |
| Raw O_EXCL stdlib | REQUIREMENTS TOOL-03 literal; zero deps; known edge cases on Windows shares; hand-rolled 10s stale-reclaim | |

**User's choice:** filelock library
**Notes:** Deliberate deviation from the literal TOOL-03 wording and the zero-dep-spine ideal. Dev/target env is Windows 11. filelock becomes the spine's single runtime dependency; behavioral contract (guarded writes, never clobber, 10s stale) preserved.

---

## JSON envelope shape

| Option | Description | Selected |
|--------|-------------|----------|
| Flat {ok, failures[], ...} | ok:bool + failures:[] + command fields at top level; most scannable in chat; errors→stderr/exit-2, success→stdout | ✓ |
| Nested {ok, error, data} | Payload under data:{}, errors under error:{}; cleaner machine-parse, less human-scannable | |

**User's choice:** Flat {ok, failures[], ...}
**Notes:** Driven by CDX-05 / DESIGN §10b — output is read by a human in the Codex chat. Success JSON to stdout; error JSON to stderr then exit 2.

---

## Byte-check wiring (GATE-04)

| Option | Description | Selected |
|--------|-------------|----------|
| ba-tools subcmd + pre-commit hook | Deterministic check is a CLI subcommand; committed git pre-commit hook calls it; portable, self-enforcing, no external CI | ✓ |
| ba-tools subcmd only | Logic ships as subcommand; hook/CI wiring deferred; not auto-enforced | |
| Standalone script only | Plain scripts/check_bytes.py, manual/CI; not part of the CLI contract | |

**User's choice:** ba-tools subcmd + pre-commit hook
**Notes:** Repo not yet git-initialized — subcommand is source of truth and works regardless; hook activates once under git. Planner must not block the subcommand on the hook.

---

## Lint severity model

| Option | Description | Selected |
|--------|-------------|----------|
| FAIL: ground/verify/atomic/citation; WARN: ambiguity | Objective checks block verify; fuzzy ambiguity advises only; REQ-ID material-change always FAIL | ✓ |
| All FAIL (strict) | Any lint issue blocks verify; max rigor, max friction | |
| All WARN (lenient) | Lint never blocks; ba-critic + human own judgement | |

**User's choice:** FAIL: ground/verify/atomic/citation; WARN: ambiguity
**Notes:** Mirrors the locked injection=advisory precedent (Open Decision #2). `verify` exits non-zero only on a FAIL-class finding.

---

## Claude's Discretion

- CLI module layout (single `ba_tools.py` vs `ba_tools/` package).
- Exact lint heuristics (ambiguity weasel-words, atomicity/verifiability detection).
- Test-fixture design for the 5 success criteria.
- `.ba-ops/` scaffold seed content / template bodies.

## Deferred Ideas

- `WARN_INJECTION` promoted to hard gate for external-source `stated` reqs — later milestone.
- `trace write` / `index update` / INDEX.md matrix — Phase 2.
- Quality gate + `ba-critic` CoVe loop — Phase 2.
- Safety gate contract (render/embed) — Phase 5.
- Render subcommands (export-diagram, render-mermaid, update-docx, manifest, package) — plugins / later phases.
