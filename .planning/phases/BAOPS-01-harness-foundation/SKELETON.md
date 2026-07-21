# Walking Skeleton — BA Daily Ops

**Phase:** 1
**Generated:** 2026-07-21

## Capability Proven End-to-End

> From the repository root, a developer can invoke the locked development interpreter (`.ba-tools-runtime/dev/Scripts/python.exe` on Windows or `.ba-tools-runtime/dev/bin/python` on POSIX) with `-X utf8 -m ba_tools --repo-root . init`, receive exactly one UTF-8 JSON success envelope, and observe the three canonical `.ba-ops/` JSON files created and read back through the contained, locked, atomic file-state boundary.

The installed BA-facing equivalent is `.\ba-tools.ps1 init` on Windows and `./ba-tools init` on POSIX. Phase 1 preserves the same CLI and state contracts when the project-local installer and generated launchers replace the development invocation.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | Exact `ba-tools==0.1.0` Python 3.11+ package with Click 8.4.2 invoked using `standalone_mode=False` | `project.version`, `ba_tools.__version__`, CLI `--version`, installed metadata, and installer generation identity stay synchronized while Click owns tokenization and the application owns JSON emission. |
| Data layer | Git-committable `.ba-ops/*.json`, bundled JSON Schemas, one native workspace lock, and same-directory atomic publication | The product is local-first and requires inspectable durable state, deterministic bytes, containment, and crash safety rather than a database. |
| Authentication | None | Phase 1 has no user identity, remote principal, session, or credential boundary; repository containment and local process ownership are the applicable controls. |
| Deployment target | Versioned project-local virtual environments under `.ba-tools-runtime/envs/`, selected by an allowlisted `current-env.txt` pointer and generated repo-root launchers; Windows support includes stock Windows PowerShell Desktop 5.1 | Generation identity includes exact package version, lock digest, Python, OS, and architecture. This satisfies portable one-command bootstrap without activation, global installation, persistent `PATH` changes, a PowerShell 7 prerequisite, or machine-specific committed paths. |
| Directory layout | Root installers and launchers; `installer/` for host bootstrap; `packages/ba-tools/` for the Python package; `.ba-ops/` for durable state; `.ba-tools-runtime/` for ignored machine state | `packages/ba-tools/` deliberately leaves the root pathname `./ba-tools` available for the required POSIX launcher; a root source directory named `ba-tools/` would collide with that launcher. |
| Validation | Pytest subprocess, multiprocessing, security, portability, and installer suites through the locked development interpreter; a read-only Windows/macOS/Linux CI matrix; separate remote-run and exact-minimum-host evidence gates | Byte-level and fault-injection evidence is required for stream, UTF-8, path, lock, and atomicity claims; workflow YAML alone never proves a job ran. |

## Stack Touched in Phase 1

- [ ] Project scaffold — exact `ba-tools==0.1.0`, target-aware approved hash locks, locked development interpreter, Ruff, and pytest
- [ ] Routing — Click dispatch for JSON help/version, `init`, `init --repair`, `doctor`, and `doctor --all`
- [ ] Data read/write — the three `.ba-ops/` JSON files through contained, locked, atomic local storage
- [ ] UI — one terminal invocation with deterministic JSON plus the installer's explicit consent interaction
- [ ] Deployment equivalent — locked source-tree command, Windows PowerShell 5.1/POSIX installers that verify generated repo-root launchers, actual six-job CI evidence, then exact Windows 10/macOS 12 evidence

## Out of Scope (Deferred to Later Slices)

- REQ-ID registries, source citations, and SRS authoring
- Workflow route execution, candidate promotion, status, and resume
- Flow, mockup, backlog, BPMN, DOCX, trace, and INDEX generation
- Coverage and stale/orphan semantics beyond the initial fixed light-profile policy file
- Plugin implementation, standard/strict profile behavior, team mode, and shared services
- Any SaaS backend, database, authentication system, cloud renderer, telemetry, or runtime network client

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without changing its local deterministic boundary:

- Phase 2: A BA authors a canonical REQ-ID registry and deterministic SRS view.
- Phase 3: A BA runs, inspects, and resumes a gated delivery route.
- Phase 4: A BA produces the light-tier flow and mockup artifacts from one delivery entry point.
- Phase 5: A BA sees truthful coverage, drift, stale, orphan, gap, and waiver status.
- Phase 6: The harness exposes profile and plugin extension seams without changing the light path.
- Phase 7: A pilot BA completes the cross-platform conformance and release gate.
