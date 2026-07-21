---
phase: BAOPS-01
slug: harness-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-21
---

# Phase BAOPS-01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest==9.1.1` (pending dependency-legitimacy approval) |
| **Config file** | `ba-tools/pyproject.toml` — Wave 0 creates it |
| **Quick run command** | `python -m pytest ba-tools/tests/unit ba-tools/tests/contract -q` |
| **Full suite command** | `python -m pytest ba-tools/tests -q -m "not online_install"` |
| **Estimated runtime** | ~20 seconds quick; ~180 seconds full |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest ba-tools/tests/unit ba-tools/tests/contract -q`
- **After every plan wave:** Run `python -m pytest ba-tools/tests -q -m "not online_install"`
- **After installer-affecting waves:** Run cached/offline installer smoke tests through the generated Windows and POSIX launchers
- **Before `/gsd-verify-work`:** Full suite and the Windows/macOS/Linux CI matrix must be green
- **Max feedback latency:** 180 seconds for the local full suite

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | FOUND-01 | T-01 | Every process path emits one JSON document on exactly one stream | subprocess contract | `python -m pytest ba-tools/tests/contract/test_cli_io.py -q` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | FOUND-05 | T-02 | Absolute, traversal, drive, UNC, symlink, and junction escapes fail closed | security | `python -m pytest ba-tools/tests/security/test_path_containment.py -q` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | NFR-03 | T-03 | Runtime CLI performs no HTTP, DNS, telemetry, or LLM calls | static + socket denial | `python -m pytest ba-tools/tests/security/test_zero_network.py -q` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | NFR-04 | T-04 | Vietnamese UTF-8 survives redirected streams, paths, and files without BOM or mojibake | subprocess portability | `python -m pytest ba-tools/tests/portability/test_utf8.py -q` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | FOUND-06 | T-05 | Bounded native locking and atomic publication preserve canonical bytes through contention and faults | multiprocessing + fault injection | `python -m pytest ba-tools/tests/reliability -q` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 2 | FOUND-04 | T-06 | Fresh, no-op, partial, repair, and invalid-state transitions never overwrite existing files | integration | `python -m pytest ba-tools/tests/integration/test_init.py -q` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 2 | NFR-05 | — | Defaults remain fixed product policy and contain no inferred business content | unit + golden bytes | `python -m pytest ba-tools/tests/unit/test_defaults.py -q` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 3 | FOUND-02 | T-07 | Doctor aggregates independent checks and applies fail/warning/skipped policy without network access | unit + integration | `python -m pytest ba-tools/tests/integration/test_doctor.py -q` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 3 | FOUND-03 | T-08 | Installers require consent, avoid PATH mutation, handle spaces, and activate only a verified local generation | installer smoke | `python -m pytest ba-tools/tests/integration/test_installer.py -q` | ❌ W0 | ⬜ pending |
| 01-03-03 | 03 | 3 | NFR-02 | — | Python 3.11+ behavior passes on Windows, macOS, and Linux | CI matrix | `python -m pytest ba-tools/tests -q -m "not online_install"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `ba-tools/pyproject.toml` — package metadata, exact build backend, pytest configuration, and Ruff configuration
- [ ] `ba-tools/requirements.lock` and `ba-tools/requirements-dev.lock` — exact direct/transitive pins and SHA-256 hashes after dependency-legitimacy approval
- [ ] `ba-tools/tests/conftest.py` — temporary repo, Unicode/space path, fake executable, lock-holder, and byte-level subprocess fixtures
- [ ] `ba-tools/tests/contract/test_cli_io.py` — strict FOUND-01 process contract
- [ ] `ba-tools/tests/security/test_path_containment.py` — adversarial FOUND-05 path matrix
- [ ] `ba-tools/tests/security/test_zero_network.py` — runtime import and socket/DNS guards
- [ ] `ba-tools/tests/reliability/test_atomic_write.py` and `ba-tools/tests/reliability/test_locking.py` — FOUND-06 fault and concurrency harness
- [ ] `ba-tools/tests/portability/test_utf8.py` — Vietnamese UTF-8 byte fixtures
- [ ] `ba-tools/tests/integration/test_init.py`, `test_doctor.py`, and `test_installer.py` — command and bootstrap integration seams
- [ ] `.github/workflows/foundation.yml` — Python 3.11/latest matrix on Windows, macOS, and Linux with installer smoke jobs

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Direct and transitive packages are legitimate and organization-approved | FOUND-03, NFR-03 | The automated legitimacy seam returned `SUS` because download evidence was unavailable | Before generating/installing locks, review official registry/source provenance for `click`, `filelock`, `jsonschema`, `pytest`, `hatchling`, `ruff`, and every resolved transitive package; record approval or approved substitutions |
| Installer and launcher work on exact minimum Windows 10 and macOS 12 hosts | NFR-02 | Current local and hosted-latest runners do not prove minimum OS versions | Run the reusable offline installer smoke script on Windows 10 and macOS 12, invoke the generated launcher from a Unicode path with spaces, and attach stdout/stderr and exit-code evidence |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verification or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verification
- [ ] Wave 0 covers all missing references
- [ ] No watch-mode flags
- [ ] Quick feedback latency is under 20 seconds and full local feedback latency is under 180 seconds
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
