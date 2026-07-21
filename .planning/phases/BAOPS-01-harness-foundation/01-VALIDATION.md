---
phase: BAOPS-01
slug: harness-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-21
revised: 2026-07-21
---

# Phase BAOPS-01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

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
- **Before `/gsd-verify-work`:** full suite and Ruff through `DEV_PYTHON`, a successful exact-commit six-job GitHub Actions run, and exact Windows 10/macOS 12 host evidence
- **Max local feedback latency:** under 20 seconds for quick/static sampling; approximately 180 seconds for the full local gate

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Automated Command | File Exists |
|---|---:|---:|---|---|---|---|---|
| 01-01-01 | 01 | 1 | FOUND-03, NFR-03 | T-BAOPS-01-SC | Binary-only target closures and unions are approved before locks/install | `node C:\Users\TungNS\.cursor\gsd-core\bin\gsd-tools.cjs package-legitimacy check --ecosystem pypi click filelock jsonschema hatchling pytest ruff` | ✅ tool |
| 01-02-01 | 02 | 2 | FOUND-03 | T-BAOPS-01-02-ENV | Final target sets/unions equal approval exactly before environment creation | Bootstrap exception: prerequisite host Python runs `scripts/verify_dependency_locks.py` once | ❌ W0 |
| 01-02-02 | 02 | 2 | FOUND-03 | T-BAOPS-01-02-VERSION | Installed metadata and `__version__` equal exact project version 0.1.0 | `DEV_PYTHON -c "import ba_tools,importlib.metadata as m; assert ba_tools.__version__ == m.version('ba-tools') == '0.1.0'"` | ❌ W0 |
| 01-02-03 | 02 | 2 | FOUND-01, FOUND-04 | T-BAOPS-01-02-VERSION | Walking skeleton is RED for behavior after healthy package startup | `DEV_PYTHON -m pytest packages/ba-tools/tests/e2e/test_walking_skeleton.py -q` | ❌ W0 |
| 01-03-01 | 03 | 3 | FOUND-01 | T-BAOPS-01-03-ERR | Exact-version single-emission process boundary | `DEV_PYTHON -m pytest packages/ba-tools/tests/e2e/test_walking_skeleton.py::test_cli_version_is_exactly_0_1_0 -q` | ❌ W0 |
| 01-03-02 | 03 | 3 | FOUND-04, FOUND-05, FOUND-06 | T-BAOPS-01-03-RACE | Real contained lock/atomic/read-back path | `DEV_PYTHON -m pytest packages/ba-tools/tests/e2e/test_walking_skeleton.py -q` | ❌ W0 |
| 01-04-01 | 04 | 4 | FOUND-01, NFR-03, NFR-04 | T-BAOPS-01-04-LOCKSET | Package/process/network/UTF-8 matrices exist and expose intended gaps | `DEV_PYTHON -m pytest packages/ba-tools/tests/contract packages/ba-tools/tests/security/test_zero_network.py packages/ba-tools/tests/portability/test_utf8.py -q` | ❌ W0 |
| 01-04-02 | 04 | 4 | FOUND-01, NFR-03, NFR-04 | T-BAOPS-01-04-ERR | All process paths emit one safe document and remain zero-network | `DEV_PYTHON -m pytest packages/ba-tools/tests/e2e/test_walking_skeleton.py packages/ba-tools/tests/contract packages/ba-tools/tests/security/test_zero_network.py packages/ba-tools/tests/portability/test_utf8.py -q` | ❌ W0 |
| 01-05-01 | 05 | 4 | FOUND-05, FOUND-06 | T-BAOPS-01-05-PARTIAL | RED adversarial/fault/concurrency matrix | `DEV_PYTHON -m pytest packages/ba-tools/tests/security/test_path_containment.py packages/ba-tools/tests/reliability -q` | ❌ W0 |
| 01-05-02 | 05 | 4 | FOUND-05, FOUND-06 | T-BAOPS-01-05-LOCK | Containment, owner recovery, atomic publication, and quarantine pass | `DEV_PYTHON -m pytest packages/ba-tools/tests/security/test_path_containment.py packages/ba-tools/tests/reliability -q` | ❌ W0 |
| 01-06-01 | 06 | 5 | FOUND-04, NFR-05 | T-BAOPS-01-06-OVERWRITE | RED full init/repair/invalid state matrix | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_init.py packages/ba-tools/tests/unit/test_defaults.py -q` | ❌ W0 |
| 01-06-02 | 06 | 5 | FOUND-04, NFR-05 | T-BAOPS-01-06-SCHEMA | Local schemas and mutation-free classification produce complete diagnostics | `DEV_PYTHON -m pytest packages/ba-tools/tests/unit/test_defaults.py packages/ba-tools/tests/integration/test_init.py -q` | ❌ W0 |
| 01-06-03 | 06 | 5 | FOUND-04, NFR-05 | T-BAOPS-01-06-OVERWRITE | Locked transitions preserve invalid/existing bytes and repair missing only | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_init.py packages/ba-tools/tests/unit/test_defaults.py packages/ba-tools/tests/contract/test_cli_io.py packages/ba-tools/tests/security/test_path_containment.py packages/ba-tools/tests/reliability -q` | ❌ W0 |
| 01-07-01 | 07 | 5 | FOUND-03, NFR-02 | T-BAOPS-01-07-SHELL | RED installer covers PowerShell 5.1, exact version, consent, and rollback | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_installer.py -q` | ❌ W0 |
| 01-07-02 | 07 | 5 | FOUND-03, NFR-02 | T-BAOPS-01-07-PTR | Verified exact-version generations and launchers pass | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_installer.py -q` | ❌ W0 |
| 01-08-01 | 08 | 6 | FOUND-02 | T-BAOPS-01-08-MUT | RED doctor scope/severity/DAG/read-only matrix | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_doctor.py -q` | ❌ W0 |
| 01-08-02 | 08 | 6 | FOUND-02 | T-BAOPS-01-08-NET | Doctor passes integration, contract, and zero-network checks | `DEV_PYTHON -m pytest packages/ba-tools/tests/integration/test_doctor.py packages/ba-tools/tests/contract/test_cli_io.py packages/ba-tools/tests/security/test_zero_network.py -q` | ❌ W0 |
| 01-09-01 | 09 | 7 | NFR-02, NFR-04 | T-BAOPS-01-09-NET | Exact version floors and eight UI categories pass in offline smoke | `DEV_PYTHON -m pytest packages/ba-tools/tests/portability/test_supported_versions.py packages/ba-tools/tests/portability/test_terminal_states.py -q` | ❌ W0 |
| 01-09-02 | 09 | 7 | all phase IDs | T-BAOPS-01-09-CI | Workflow source is read-only, pinned, complete, locked, and PowerShell 5.1-aware | `DEV_PYTHON -m pytest packages/ba-tools/tests/contract/test_foundation_workflow.py -q` | ❌ W0 |
| 01-10-01 | 10 | 8 | all phase IDs | T-BAOPS-01-10-EVIDENCE | Exact-commit six-job remote run concludes success | `gh run view FOUNDATION_RUN_ID --json headSha,conclusion,event,jobs,url,startedTime,updatedAt` | ✅ external CLI |
| 01-11-01 | 11 | 9 | FOUND-03, NFR-02, NFR-04 | T-BAOPS-01-11-EVIDENCE | Real minimum hosts pass; Windows uses Desktop PowerShell 5.1 | `DEV_PYTHON -m pytest packages/ba-tools/tests/portability/test_supported_versions.py packages/ba-tools/tests/portability/test_terminal_states.py -q` plus host evidence | ❌ W0 |

*Status legend: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `packages/ba-tools/pyproject.toml` — exact version 0.1.0, package metadata, backend, pytest, Ruff
- [ ] `packages/ba-tools/requirements.lock`, `requirements-dev.lock` — approved target-aware exact pins/hashes
- [ ] `.ba-tools-runtime/dev/{Scripts/python.exe|bin/python}` — canonical locked development interpreter
- [ ] `scripts/verify_dependency_locks.py` — target marker and exact-set comparator
- [ ] `packages/ba-tools/tests/conftest.py` — Unicode/space repo, bytes, process, fault, and network fixtures
- [ ] `packages/ba-tools/tests/e2e/test_walking_skeleton.py`
- [ ] `packages/ba-tools/tests/contract/test_cli_io.py`, `test_dependency_locks.py`, `test_foundation_workflow.py`
- [ ] `packages/ba-tools/tests/security/test_path_containment.py`, `test_zero_network.py`
- [ ] `packages/ba-tools/tests/reliability/test_atomic_write.py`, `test_locking.py`
- [ ] `packages/ba-tools/tests/portability/test_utf8.py`, `test_supported_versions.py`, `test_terminal_states.py`
- [ ] `packages/ba-tools/tests/integration/test_init.py`, `test_doctor.py`, `test_installer.py`
- [ ] `packages/ba-tools/tests/unit/test_defaults.py`
- [ ] `.github/workflows/foundation.yml` — explicit read-only permissions and six-job ordinary matrix

---

## Manual and External Evidence Gates

| Behavior | Requirement | Why External/Human | Test Instructions |
|---|---|---|---|
| All target dependency closures are legitimate and approved | FOUND-03, NFR-03 | Legitimacy seam returned `SUS`; organizational approval is human | Review direct/transitive binary-only target tables and approve exact substitutions/closures before lock creation |
| Actual ordinary CI matrix completed successfully | all phase IDs | Workflow YAML and local tests cannot prove remote jobs ran | Inspect exact-commit `foundation` run and all six job/step conclusions via `gh` and run URL |
| Exact Windows 10 + PowerShell 5.1 and macOS 12 hosts pass | NFR-02 | Hosted latest runners do not prove exact minimum versions | Run `smoke_foundation.py` on real hosts and attach redacted host/version/hash/stream evidence |

---

## Validation Sign-Off

- [ ] Every task has `<automated>` verification
- [ ] Every Python verification after environment creation uses `DEV_PYTHON`
- [ ] Sampling continuity has no three consecutive tasks without automated feedback
- [ ] Fast workflow-source feedback is under 20 seconds
- [ ] Full local suite remains the final local gate
- [ ] Read-only workflow permissions are source-tested
- [ ] Actual six-job remote evidence is approved
- [ ] Exact-minimum host evidence includes Windows PowerShell Desktop 5.1
- [ ] `nyquist_compliant: true` set after all gates pass

**Approval:** pending
