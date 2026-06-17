# Phase 1: Deterministic ba-tools CLI + Foundational Gates - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning

<domain>
## Phase Boundary

A functionally-complete `ba-tools` Python CLI where every command does ONLY
file/hash/command-provable work (the determinism boundary — agents own all
judgement), the `.ba-ops/` file-state spine is scaffolded, and the four
foundational gates are operational so no later operator has to retrofit them:

1. **Byte-check** (GATE-04) — fail when an eager doc ≥ 32,768 B
2. **Lockfile** (TOOL-03) — STATE.md writes guarded, stale-reclaim after 10s
3. **Deterministic route resolution** (TOOL-02) — `resolve-route` returns the
   static `DEFAULT_ROUTE` only, never infers from free text
4. **REQ-ID stability** (TOOL-05) — flags material statement change on an
   existing REQ-ID, never silently renumbers

**Phase 1 requirements (19):** TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-05,
TOOL-06, TOOL-09, TOOL-10, TOOL-11, TOOL-12, TOOL-13, TOOL-14, TOOL-15,
TRACE-01, TRACE-02, GATE-02, GATE-04, CDX-04, CDX-05.

**Explicitly NOT this phase** (per ROADMAP traceability): `trace write` (TOOL-07)
and `index update` (TOOL-08) land in Phase 2 with the traceability core; the
Quality gate + `ba-critic` (GATE-01) is Phase 2; the Safety gate contract
(GATE-03) is Phase 5. Phase 1 builds the deterministic substrate only.

</domain>

<decisions>
## Implementation Decisions

### Lockfile (STATE.md.lock)
- **D-01:** Use the **`filelock` library** (`FileLock(timeout=10)`), NOT raw
  `os.open(..., O_EXCL)`. Chosen because the dev/target env is Windows 11 and
  CLAUDE.md verified-research flags known raw-`O_EXCL` edge cases on Windows
  network shares / virtual filesystems.
- **D-02 (deviation, recorded deliberately):** This overrides the literal
  wording of **TOOL-03** ("`O_EXCL` lockfile") and the "zero external Python
  deps for the spine" ideal in CLAUDE.md's stack patterns. `filelock` becomes
  the **single runtime dependency** of the spine; everything else stays stdlib
  (`hashlib`, `json`, `argparse`, `re`, `pathlib`, `subprocess`). The 10s
  stale-lock threshold is implemented via `FileLock(timeout=10)`. The behavioral
  contract of TOOL-03 (guarded writes, never clobber, 10s stale reclaim) is
  preserved — only the mechanism changes.

### JSON output envelope (applies to all ~19 commands)
- **D-03:** **Flat envelope** — every response is `{ok: <bool>, failures: [...],
  ...<command fields merged at top level>}`. `failures` is always present (empty
  array on success). Chosen for max scannability — CDX-05 / DESIGN §10b: output
  is read by a human in the Codex chat, not just machine-parsed. Avoid a nested
  `data: {}` wrapper.
- **D-04:** **Success JSON → stdout. Error JSON → stderr, then exit code 2**
  (`BaToolsError`). Keeps stdout a clean success channel; the error still emits
  structured JSON (with `ok:false` + `failures`) so the failure is inspectable,
  not just an exit code.

### Byte-check gate (GATE-04)
- **D-05:** Two-layer wiring — the deterministic check is a **`ba-tools`
  subcommand** (the portable core, part of the CLI contract), AND a **committed
  git pre-commit hook** calls it so the build fails locally before commit. No
  dependency on an external CI service (Codex-first, none defined yet).
- **D-06 (planner note):** The repo is not yet git-initialized (env reports "Is
  a git repository: false"). The `ba-tools` subcommand is the source of truth and
  works regardless; the pre-commit hook is the enforcement layer that activates
  once the repo is under git. Planner should not block the subcommand on the hook.

### Lint severity model (lint-requirements → folded by `ba-tools verify`)
- **D-07:** **FAIL** (blocks `ba-tools verify`): grounding, verifiability,
  atomicity, citation-exists. **WARN** (advisory, does not block): ambiguity
  (inherently fuzzy — leave the judgement to `ba-critic`/human). REQ-ID
  material-change (TOOL-05) is **always FAIL**.
- **D-08:** This mirrors the already-locked `injection=advisory` precedent
  (REQUIREMENTS Open Decisions #2): objective/deterministic checks gate hard;
  subjective signals warn. `verify` exit code is non-zero only on a FAIL-class
  finding.

### Carried forward (already locked — do NOT re-decide)
- Python 3.11+, stdlib-first; resolve interpreter via `sys.executable`.
- `argparse` for dispatch (CLAUDE.md: click only past ~10 nested subgroups).
- All paths relative to `--repo-root` (git root / cwd); no hard-coded machine
  paths (TOOL-14, DESIGN §11).
- Citation-exists = **section-scoped**, ≥12-char real verbatim substring, with
  `--cite-scope document` override (REQUIREMENTS Open Decision #1, TOOL-06).
- `WARN_INJECTION` scan is **advisory** in v1 (TOOL-15, Open Decision #2).
- REQ-ID stability lint lands in **Phase 1** with a renumbered-requirements
  fixture (Open Decision #4).
- `.ba-ops/config.json` feature flags default `true` when missing (absent =
  enabled — TRACE-02, DESIGN §1 principle 4).

### Claude's Discretion (researcher / planner own these)
- CLI module layout (single `ba_tools.py` vs `ba_tools/` package with per-command
  modules) — DESIGN §5 shows a single file; CLAUDE.md references
  `ba_tools/commands/update_docx.py` for the deferred plugin path. Planner picks.
- Exact lint heuristics (weasel-word list for ambiguity, atomicity detection,
  verifiability cues).
- Test-fixture design for the 5 success criteria (renumbered-requirements
  fixture, citation pass/fail fixtures, concurrent-write test).
- `.ba-ops/` scaffold seed content / template bodies for PROJECT.md,
  REQUIREMENTS.md, INDEX.md, STATE.md, config.json.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture spec (source of truth)
- `DESIGN.md` — v0.2.2, repo root. THE architecture this build aligns to.
  Most relevant Phase-1 sections: §5 (ba-tools determinism boundary + command
  families + render-backend resolution), §6 (three gates), §7 (byte budgets),
  §8 (`.ba-ops/` file-state spine), §11 (non-negotiables / forbidden shortcuts).
  Note: §10 "DONE" build-order markers are **aspirational targets, not current
  state** — this is a greenfield build from zero.

### Requirements & scope
- `.planning/REQUIREMENTS.md` — REQ-ID registry; Phase-1 requirement text +
  the "Open Decisions" table (4 already-resolved defaults).
- `.planning/ROADMAP.md` — Phase 1 goal + 5 success criteria (the TRUE-conditions
  the verifier checks).
- `.planning/PROJECT.md` — v1 = daily spine only; determinism boundary; UI
  in-Codex-chat only; key decisions table.

### Tech stack (verified research — pinned versions, patterns, what-NOT-to-use)
- `CLAUDE.md` (repo root, project instructions) — verified stack table
  (Python 3.11+, `filelock`, `hashlib.file_digest`, `argparse`), CLI output
  convention, lockfile pattern, DESIGN verification flags, byte budgets.

### Referenced-but-absent (planner: confirm before relying on)
- `FIS_GSARCHITECTURE.md` — cited by DESIGN.md (line 5) and PROJECT.md as the
  GSD Core standard mirrored, but NOT present in repo root (only `CLAUDE.md` and
  `DESIGN.md` exist). Treat its standard as already distilled into DESIGN.md.
- `.agents/ba-daily-operators/ba-core/references/*.md` (gates.md, gsd-adaptation.md,
  scout-codebase analog) — referenced throughout DESIGN but not yet created;
  these are Phase-1+ build targets, not existing inputs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield. No `ba-tools`, `ba_tools`, `ba-core`, `.agents`, or
  `.ba-ops` directories exist yet. No `.planning/codebase/` maps.

### Established Patterns
- The only patterns are the contracts dictated by DESIGN.md + CLAUDE.md (JSON
  output convention, lockfile pattern, render-backend resolution chain). Adopt
  those verbatim; nothing to reverse-engineer from existing code.

### Integration Points
- `.ba-ops/` (this phase scaffolds it) is the persistent file-state spine every
  later operator reads/writes. Phase 1 establishes its shape; Phase 2 fills the
  traceability matrix (INDEX.md) into it.

</code_context>

<specifics>
## Specific Ideas

- Keep `ba-tools` JSON output terse and scannable — short objects, explicit
  `ok`/`failures`, no noise (DESIGN §10b: it is read by a human in the chat).
- The four gates must be operational in Phase 1, not stubbed — the whole point
  of the phase is that no later operator retrofits them.

</specifics>

<deferred>
## Deferred Ideas

- `WARN_INJECTION` promoted from advisory to a hard gate for external-source
  `stated` requirements — Open Decision #2, deferred to a later milestone.
- `trace write` (TOOL-07) + `index update` (TOOL-08) + INDEX.md matrix — Phase 2.
- Quality gate + `ba-critic` CoVe loop (GATE-01) — Phase 2.
- Safety gate contract for render/embed (GATE-03) — Phase 5 (plugin-enforced).
- Render subcommands (`export-diagram`, `render-mermaid`, `update-docx`,
  `manifest`, `package`) — DESIGN §5 lists them but they belong to the optional
  plugins / later phases, off the Phase-1 deterministic spine.

</deferred>

---

*Phase: 1-Deterministic ba-tools CLI + Foundational Gates*
*Context gathered: 2026-06-17*
