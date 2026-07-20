# Phase 1: Harness Foundation - Context

**Gathered:** 2026-07-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a portable, local-first foundation that lets a BA bootstrap and validate a project workspace on Windows or POSIX: a project-local `ba-tools` installation, repo-root launchers, `doctor`, safe `init`/repair behavior, the initial `.ba-ops/` files, path containment, UTF-8 JSON I/O, and crash-safe writes.

REQ-ID registries, SRS authoring, workflow execution, artifact generation, trace/INDEX semantics, plugins, and team mode remain in later phases.

</domain>

<decisions>
## Implementation Decisions

### Installer and invocation
- **D-01:** Install `ba-tools` into an isolated, project-local environment. Do not install it per-user or system-wide.
- **D-02:** Generate repo-root launchers: `.\ba-tools.ps1` on Windows and `./ba-tools` on POSIX. They must work without activating a virtual environment and without modifying user or system `PATH`.
- **D-03:** Treat the roadmap phrase “working `ba-tools` on PATH” as “directly runnable from the repo-root launcher.” This intentionally rejects persistent `PATH` modification and must be reflected in planning and acceptance tests.
- **D-04:** Do not automatically install missing system prerequisites such as Python or Git. Fail early with actionable, OS-specific guidance.
- **D-05:** Once a compatible Python exists, the installer may download locked project dependencies only after explicit user consent.
- **D-06:** Pin the exact `ba-tools` version and dependencies per repository. Re-running the installer synchronizes to the lockfile; upgrades are explicit rather than automatic.

### Doctor policy
- **D-07:** Missing core requirements produce overall `fail` and exit code 2. Missing dependencies for plugins that are not enabled produce `warning` and exit code 0.
- **D-08:** Default `doctor` scope is core plus the current profile and enabled plugins. `doctor --all` checks every known optional dependency.
- **D-09:** `doctor` works before and after initialization. Pre-init checks the host and repository; post-init additionally validates config, policy, and durable file-state.
- **D-10:** Continue running independent checks after a failure. Mark checks whose prerequisites failed as `skipped`, then return all actionable findings in one result.

### Init and re-init safety
- **D-11:** Re-running `init` against a valid `.ba-ops/` is an idempotent success with `changed: false`; it must not rewrite files.
- **D-12:** Plain `init` fails safely when required files are missing and recommends explicit `init --repair`.
- **D-13:** `init --repair` may create missing required files only. It must never replace an existing file.
- **D-14:** If an existing JSON file is invalid or violates its schema, preserve it and fail with precise validation errors. Do not reset or back it up automatically.
- **D-15:** Initialize minimal, valid state without business inference or sample data: `profile: light`, the standard light coverage policy, and a valid empty `business-goals.json`.

### Locking and crash recovery
- **D-16:** A writer waits for a bounded interval when another process holds a valid lock, then returns a structured timeout error with retry guidance. Never wait indefinitely.
- **D-17:** Automatically recover a stale lock only when staleness can be established safely, including that the owner process is no longer active. Ambiguous cases fail without removing the lock.
- **D-18:** If a crash leaves an atomic-write temporary file, keep the canonical file unchanged and quarantine the temporary file for inspection. Never auto-promote it.
- **D-19:** Use one workspace-wide write lock for `.ba-ops/` mutations in v1. Pilot scale does not justify concurrent writers or multi-lock complexity.

### Claude's Discretion
No discussed decision was delegated. The planner may choose unconstrained implementation details such as the exact bounded timeout, JSON field names, lock metadata format, quarantine naming, and environment tooling, provided all behavior above remains true.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase contracts
- `.planning/PROJECT.md` — product boundary, deterministic/agent split, portability, security, and CLI constraints.
- `.planning/REQUIREMENTS.md` — Phase 1 requirements `FOUND-01` through `FOUND-06` and `NFR-02` through `NFR-05`.
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria; apply decision D-03 when interpreting the literal `PATH` wording.
- `docs/BRD-v1.0.md` — normative requirements for doctor, installer, file-state, CLI output, UTF-8, zero-network operation, path containment, locking, and atomic writes.
- `docs/SRS-SPEC.md` — upstream canonical SRS contract; Phase 1 scaffolding must remain compatible with the schemas and deterministic behavior required in Phase 2.

### Implementation research
- `.planning/research/STACK.md` — researched Python packaging, CLI, validation, locking, and cross-platform tooling options.
- `.planning/research/ARCHITECTURE.md` — proposed repository layout, deterministic CLI boundary, and `.ba-ops/` integration points.
- `.planning/research/PITFALLS.md` — Windows/UTF-8, path, state-corruption, lock, and recovery failure modes to cover in planning.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No implementation source, Python package manifest, installer scripts, tests, or project skills exist yet. Phase 1 is greenfield.
- Existing assets are planning and product documents only; there is no code to preserve or adapt.

### Established Patterns
- No code conventions have been established.
- Research proposes a separate deterministic `ba-tools/` Python package, an `installer/` surface, and Git-committed `.ba-ops/` state. These are recommendations rather than existing code.
- The deterministic boundary is already fixed: CLI code performs provable file, schema, path, lock, and JSON operations; it must not infer business meaning or call network services.

### Integration Points
- Repo-root launchers connect users to the project-local Python environment.
- `--repo-root` anchors every business path and all `.ba-ops/` access.
- `.ba-ops/config.json`, `.ba-ops/coverage-policy.json`, and `.ba-ops/business-goals.json` are the initial durable state surfaces consumed by later phases.
- Future skills and the workflow runner will call the stable `ba-tools` JSON interface; Phase 1 must establish that contract without implementing later-phase capabilities.

</code_context>

<specifics>
## Specific Ideas

- Preserve the explicit command names `doctor --all` and `init --repair`.
- Preserve the observable no-op result `changed: false`.
- Launcher spelling is platform-specific: `.\ba-tools.ps1` for PowerShell and `./ba-tools` for POSIX shells.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Harness Foundation*
*Context gathered: 2026-07-20*
