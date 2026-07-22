---
phase: BAOPS-01
slug: harness-foundation
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-21
revised: 2026-07-22
validated: 2026-07-22
scope_record: .planning/phases/BAOPS-01-harness-foundation/01-SCOPE.md
---

# Phase BAOPS-01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> **Scope (2026-07-22):** Current gates prove **Windows 10+ x64 + CPython 3.14** (NFR-06). Deferred gates prove **multi-OS / Python 3.11+ / minimum-host** (NFR-02, Phase 7). See `01-SCOPE.md`.

---

## Current vs Deferred Gates

| Gate | Requirement | Status | Owner |
|------|-------------|--------|-------|
| Local suite + Ruff via `DEV_PYTHON` | FOUND-*, NFR-03…05 | **Current** | Plans 01-02…01-09 |
| One-job `foundation` CI (windows-latest + 3.14) | NFR-06 | **Current** | Plan 01-10 |
| Portability handoff record | NFR-02 **not complete** | **Current (honest close)** | Plan 01-11 |
| Six-job CI matrix (3 OS × 2 Python) | NFR-02 | **Deferred** | Phase 7 |
| Exact Windows 10 / macOS 12 host smoke | NFR-02 | **Deferred** | Phase 7 |
| cp311 `typing-extensions` closure fix | NFR-02 | **Deferred** | Phase 7 |
| POSIX symlink test fixture fix | NFR-02 | **Deferred** | Phase 7 |

## Locked Development Interpreter Contract

Plan 01-02 creates the only Python interpreter used by later local verification:

| Host | `DEV_PYTHON` |
|---|---|
| Windows | `.\.ba-tools-runtime\dev\Scripts\python.exe` |
| POSIX | `./.ba-tools-runtime/dev/bin/python` |

Every command below that begins with `DEV_PYTHON` means:

- PowerShell: `& ".\.ba-tools-runtime\dev\Scripts\python.exe" <arguments>`
- POSIX sh: `./.ba-tools-runtime/dev/bin/python <arguments>`

The prerequisite host interpreter may run the standard-library lock comparator once before `.ba-tools-runtime/dev` exists. After the environment is installed, Plan 01-02 reruns that comparator through `DEV_PYTHON`; all pytest, Ruff, support scripts, and sampling commands from Plan 01-03 onward use `DEV_PYTHON`.

## Test Infrastructure

| Property | Value |
|---|---|
| **Framework** | `pytest==9.1.1` from the approved development lock |
| **Config file** | `packages/ba-tools/pyproject.toml` |
| **Quick run command** | `DEV_PYTHON -m pytest packages/ba-tools/tests/unit packages/ba-tools/tests/contract -q` |
| **Fast workflow command** | `DEV_PYTHON -m pytest packages/ba-tools/tests/contract/test_foundation_workflow.py -q` |
| **Full suite command** | `DEV_PYTHON -m pytest packages/ba-tools/tests -q -m "not online_install"` |
| **Lint command** | `DEV_PYTHON -m ruff check packages/ba-tools/src packages/ba-tools/tests installer scripts` |
| **Estimated runtime** | under 20 seconds quick/static; approximately 180 seconds full |

---

## Sampling Rate

- **After every task commit:** `DEV_PYTHON -m pytest packages/ba-tools/tests/unit packages/ba-tools/tests/contract -q`
- **After every plan wave:** `DEV_PYTHON -m pytest packages/ba-tools/tests -q -m "not online_install"`
- **After installer-affecting waves:** `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_installer.py -q`, followed by cached/offline smoke through generated launchers
- **After workflow edits:** `DEV_PYTHON -m pytest packages/ba-tools/tests/contract/test_foundation_workflow.py -q`
- **Before `/gsd-verify-work` (current scope):** full suite and Ruff through `DEV_PYTHON`, a successful exact-commit **one-job** Windows/Python 3.14 GitHub Actions run (Plan 01-10), and approved portability handoff record (Plan 01-11)
- **Before Phase 7 NFR-02 close (deferred):** six-job CI or equivalent, exact Windows 10/macOS 12 host evidence, cp311 closure fix, POSIX fixture fix
- **Max local feedback latency:** under 20 seconds for quick/static sampling; approximately 180 seconds for the full local gate

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Automated Command | File Exists |
|---|---:|---:|---|---|---|---|---|
| 01-01-01 | 01 | 1 | FOUND-03, NFR-03 | T-BAOPS-01-SC | Binary-only target closures and unions are approved before locks/install | `node C:\Users\TungNS\.cursor\gsd-core\bin\gsd-tools.cjs package-legitimacy check --ecosystem pypi click filelock jsonschema hatchling pytest ruff` | ✅ tool |
| 01-02-01 | 02 | 2 | FOUND-03 | T-BAOPS-01-02-ENV | Final target sets/unions equal approval exactly before environment creation | Bootstrap exception: prerequisite host Python runs `scripts/verify_dependency_locks.py` once | ✅ `contract/test_dependency_locks.py` |
| 01-02-02 | 02 | 2 | FOUND-03 | T-BAOPS-01-02-VERSION | Installed metadata and `__version__` equal exact project version 0.1.0 | `DEV_PYTHON -c "import ba_tools,importlib.metadata as m; assert ba_tools.__version__ == m.version('ba-tools') == '0.1.0'"` | ✅ `integration/test_installer.py`, `e2e/test_walking_skeleton.py` |
| 01-02-03 | 02 | 2 | FOUND-01, FOUND-04 | T-BAOPS-01-02-VERSION | Walking skeleton is RED for behavior after healthy package startup | `DEV_PYTHON -m pytest packages/ba-tools/tests/e2e/test_walking_skeleton.py -q` | ✅ `e2e/test_walking_skeleton.py` |
| 01-03-01 | 03 | 3 | FOUND-01 | T-BAOPS-01-03-ERR | Exact-version single-emission process boundary | `DEV_PYTHON -m pytest packages/ba-tools/tests/e2e/test_walking_skeleton.py::test_cli_version_is_exactly_0_1_0 -q` | ✅ `e2e/test_walking_skeleton.py` |
| 01-03-02 | 03 | 3 | FOUND-04, FOUND-05, FOUND-06 | T-BAOPS-01-03-RACE | Real contained lock/atomic/read-back path | `DEV_PYTHON -m pytest packages/ba-tools/tests/e2e/test_walking_skeleton.py -q` | ✅ `e2e/test_walking_skeleton.py` |
| 01-04-01 | 04 | 4 | FOUND-01, NFR-03, NFR-04 | T-BAOPS-01-04-LOCKSET | Package/process/network/UTF-8 matrices exist and expose intended gaps | `DEV_PYTHON -m pytest packages/ba-tools/tests/contract packages/ba-tools/tests/security/test_zero_network.py packages/ba-tools/tests/portability/test_utf8.py -q` | ✅ contract, security, portability |
| 01-04-02 | 04 | 4 | FOUND-01, NFR-03, NFR-04 | T-BAOPS-01-04-ERR | All process paths emit one safe document and remain zero-network | `DEV_PYTHON -m pytest packages/ba-tools/tests/e2e/test_walking_skeleton.py packages/ba-tools/tests/contract packages/ba-tools/tests/security/test_zero_network.py packages/ba-tools/tests/portability/test_utf8.py -q` | ✅ e2e, contract, security, portability |
| 01-05-01 | 05 | 4 | FOUND-05, FOUND-06 | T-BAOPS-01-05-PARTIAL | RED adversarial/fault/concurrency matrix | `DEV_PYTHON -m pytest packages/ba-tools/tests/security/test_path_containment.py packages/ba-tools/tests/reliability -q` | ✅ security, reliability |
| 01-05-02 | 05 | 4 | FOUND-05, FOUND-06 | T-BAOPS-01-05-LOCK | Containment, owner recovery, atomic publication, and quarantine pass | `DEV_PYTHON -m pytest packages/ba-tools/tests/security/test_path_containment.py packages/ba-tools/tests/reliability -q` | ✅ security, reliability |
| 01-06-01 | 06 | 5 | FOUND-04, NFR-05 | T-BAOPS-01-06-OVERWRITE | RED full init/repair/invalid state matrix | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_init.py packages/ba-tools/tests/unit/test_defaults.py -q` | ✅ `integration/test_init.py`, `unit/test_defaults.py` |
| 01-06-02 | 06 | 5 | FOUND-04, NFR-05 | T-BAOPS-01-06-SCHEMA | Local schemas and mutation-free classification produce complete diagnostics | `DEV_PYTHON -m pytest packages/ba-tools/tests/unit/test_defaults.py packages/ba-tools/tests/integration/test_init.py -q` | ✅ `unit/test_defaults.py`, `integration/test_init.py` |
| 01-06-03 | 06 | 5 | FOUND-04, NFR-05 | T-BAOPS-01-06-OVERWRITE | Locked transitions preserve invalid/existing bytes and repair missing only | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_init.py packages/ba-tools/tests/unit/test_defaults.py packages/ba-tools/tests/contract/test_cli_io.py packages/ba-tools/tests/security/test_path_containment.py packages/ba-tools/tests/reliability -q` | ✅ init, defaults, contract, security, reliability |
| 01-07-01 | 07 | 5 | FOUND-03, NFR-02 | T-BAOPS-01-07-SHELL | RED installer covers PowerShell 5.1, exact version, consent, and rollback | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_installer.py -q` | ✅ `integration/test_installer.py` |
| 01-07-02 | 07 | 5 | FOUND-03, NFR-02 | T-BAOPS-01-07-PTR | Verified exact-version generations and launchers pass | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_installer.py -q` | ✅ `integration/test_installer.py` |
| 01-08-01 | 08 | 6 | FOUND-02 | T-BAOPS-01-08-MUT | RED doctor scope/severity/DAG/read-only matrix | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_doctor.py -q` | ✅ `integration/test_doctor.py` |
| 01-08-02 | 08 | 6 | FOUND-02 | T-BAOPS-01-08-NET | Doctor passes integration, contract, and zero-network checks | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_doctor.py packages/ba-tools/tests/contract/test_cli_io.py packages/ba-tools/tests/security/test_zero_network.py -q` | ✅ doctor, contract, security |
| 01-09-01 | 09 | 7 | NFR-02, NFR-04 | T-BAOPS-01-09-NET | Exact version floors and eight UI categories pass in offline smoke | `DEV_PYTHON -m pytest packages/ba-tools/tests/portability/test_supported_versions.py packages/ba-tools/tests/portability/test_terminal_states.py -q` | ✅ portability (current-scope version floors) |
| 01-09-02 | 09 | 7 | all phase IDs | T-BAOPS-01-09-CI | Workflow source is read-only, pinned, complete, locked, and PowerShell 5.1-aware | `DEV_PYTHON -m pytest packages/ba-tools/tests/contract/test_foundation_workflow.py -q` | ✅ `contract/test_foundation_workflow.py` |
| 01-10-01 | 10 | 8 | NFR-06 | T-BAOPS-01-10-EVIDENCE | Exact-commit one-job Windows/3.14 remote run concludes success | `gh run view FOUNDATION_RUN_ID --json headSha,conclusion,event,jobs,url,startedTime,updatedAt` | ✅ external CLI (run 29886063228) |
| 01-11-01 | 11 | 9 | FOUND-03, NFR-04 | T-BAOPS-01-11-EVIDENCE | Portability handoff recorded; NFR-02 remains pending | Review `01-11-SUMMARY.md` `Portability Handoff` section | ✅ manual (handoff approved) |

*Status legend: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `packages/ba-tools/pyproject.toml` — exact version 0.1.0, package metadata, backend, pytest, Ruff
- [x] `packages/ba-tools/requirements.lock`, `requirements-dev.lock` — approved target-aware exact pins/hashes
- [x] `.ba-tools-runtime/dev/{Scripts/python.exe|bin/python}` — canonical locked development interpreter
- [x] `scripts/verify_dependency_locks.py` — target marker and exact-set comparator
- [x] `packages/ba-tools/tests/conftest.py` — Unicode/space repo, bytes, process, fault, and network fixtures
- [x] `packages/ba-tools/tests/e2e/test_walking_skeleton.py`
- [x] `packages/ba-tools/tests/contract/test_cli_io.py`, `test_dependency_locks.py`, `test_foundation_workflow.py`
- [x] `packages/ba-tools/tests/security/test_path_containment.py`, `test_zero_network.py`
- [x] `packages/ba-tools/tests/reliability/test_atomic_write.py`, `test_locking.py`
- [x] `packages/ba-tools/tests/portability/test_utf8.py`, `test_supported_versions.py`, `test_terminal_states.py`
- [x] `packages/ba-tools/tests/integration/test_init.py`, `test_doctor.py`, `test_installer.py`
- [x] `packages/ba-tools/tests/unit/test_defaults.py`
- [x] `.github/workflows/foundation.yml` — explicit read-only permissions and **current-scope** one-job Windows/Python 3.14 matrix (multi-OS expansion deferred Phase 7)

---

## Manual and External Evidence Gates

### Current scope (Phase 1 close)

| Behavior | Requirement | Why External/Human | Test Instructions |
|---|---|---|---|
| All target dependency closures are legitimate and approved | FOUND-03, NFR-03 | Legitimacy seam returned `SUS`; organizational approval is human | Review direct/transitive binary-only target tables and approve exact substitutions/closures before lock creation |
| Actual **one-job** Windows/Python 3.14 CI completed successfully | NFR-06 | Workflow YAML and local tests cannot prove remote job ran | Inspect exact-commit `foundation` run and single job/step conclusion via `gh` and run URL |
| Portability handoff approved | NFR-02 pending | Prevents false multi-OS completion claim | Review `01-11-SUMMARY.md` — NFR-02 deferred to Phase 7 |

### Deferred (Phase 7 — NFR-02)

| Behavior | Requirement | Why Deferred | Notes |
|---|---|---|---|
| Six-job ordinary CI matrix | NFR-02 | Scope narrowed 2026-07-22 | Re-enable with workflow expansion |
| Exact Windows 10 + PowerShell 5.1 and macOS 12 hosts | NFR-02 | No current host evidence | `smoke_foundation.py` on real hosts |
| cp311 typing-extensions in approved closure | NFR-02 | Known gap | Fix before 3.11 targets |
| POSIX symlink test fixture | NFR-02 | Wrong interpreter resolution | Fix before POSIX CI/host evidence |

---

## Validation Sign-Off

- [x] Every task has `<automated>` verification
- [x] Every Python verification after environment creation uses `DEV_PYTHON`
- [x] Sampling continuity has no three consecutive tasks without automated feedback
- [x] Fast workflow-source feedback is under 20 seconds
- [x] Full local suite remains the final local gate
- [x] Read-only workflow permissions are source-tested
- [x] Actual **one-job** remote evidence is approved (NFR-06)
- [x] Portability handoff record approved — NFR-02 **not** marked complete
- [x] Deferred gates documented for Phase 7 (six-job CI, minimum hosts, cp311, POSIX fixture)
- [x] `nyquist_compliant: true` set after **current-scope** gates pass

**Approval:** validated 2026-07-22 (Nyquist audit)

---

## Validation Audit Trail

| Field | Value |
|---|---|
| **Date** | 2026-07-22 |
| **Auditor** | gsd-nyquist-auditor |
| **Scope** | Current gates only (Windows 10+ x64 + CPython 3.14, NFR-06); NFR-02 deferred Phase 7 |
| **Full suite** | `171 passed, 1 skipped` in 52.4s (`-m "not online_install"`) |
| **Test files** | 16 Python modules under `packages/ba-tools/tests/` |
| **Gap classification** | 21/21 current-scope tasks **COVERED**; 0 MISSING; 0 PARTIAL |
| **Repairs** | 3 stale installer assertions updated (verified-generation short-circuit, offline mock isolation) |
| **Deferred (not audited)** | Six-job CI matrix, exact Windows 10/macOS 12 hosts, cp311 closure, POSIX symlink fixture |
| **External evidence** | CI run [29886063228](https://github.com/tungns84/ba-daily-ops/actions/runs/29886063228); portability handoff approved in `01-11-SUMMARY.md` |
