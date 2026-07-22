---
phase: BAOPS-01-harness-foundation
slug: harness-foundation
status: verified
threats_open: 0
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: 2026-07-22
verified: 2026-07-22
---

# Phase BAOPS-01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> **Scope:** Windows 10+ x64 + CPython 3.14 (NFR-06). Multi-OS threats deferred to Phase 7 (NFR-02).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Host OS / shell | PowerShell 5.1+, POSIX sh wrappers invoke bootstrap | Prerequisite probes, consent prompts |
| Installer bootstrap | `installer/bootstrap.py` acquires wheels, activates generation | Hash-locked PyPI artifacts (consented online or approved wheelhouse) |
| Project-local runtime | `.ba-tools-runtime/envs/<generation>/` | Exact ba-tools 0.1.0 + approved lock digest |
| Repo-root launchers | `ba-tools.ps1`, `ba-tools` | Resolved generation pointer only; no absolute path disclosure on failure |
| CLI gateway | `ba_tools.__main__.entrypoint` | Single JSON envelope per invocation (stdout success / stderr failure) |
| Business state | `.ba-ops/` under `--repo-root` | Canonical JSON config files; path containment enforced |
| Doctor probes | Read-only subprocess checks | Redacted host/repo facts; zero-network under test |
| Remote CI evidence | GitHub Actions foundation workflow | Redacted run metadata; no secrets or absolute runner paths |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-BAOPS-01-SC | Tampering | Dependency closure | high | mitigate | `verify_dependency_locks.py`, `test_dependency_locks.py`, bootstrap `--require-hashes --only-binary --no-deps`, doctor lock digest check | closed |
| T-BAOPS-01-01-SPOOF | Spoofing | Package legitimacy | high | mitigate | 01-01 approval record; PyPI + source pairing for 17 packages | closed |
| T-BAOPS-01-01-INFO | Information Disclosure | Dry-run reports | low | accept | Public metadata only; see Accepted Risks Log | closed |
| T-BAOPS-01-02-VERSION | Tampering | Package identity | medium | mitigate | Fixed 0.1.0 in metadata + `__version__`; CLI contract tests | closed |
| T-BAOPS-01-02-ENV | Elevation of Privilege | Dev interpreter | high | mitigate | Locked `.ba-tools-runtime/dev`; conftest gate | closed |
| T-BAOPS-01-03-PATH | Tampering | Path resolution | high | mitigate | `paths.py` grammar + containment; `test_path_containment.py` | closed |
| T-BAOPS-01-03-RACE | Tampering / DoS | Init publication | high | mitigate | Native workspace lock; create-only atomic writes | closed |
| T-BAOPS-01-03-ERR | Information Disclosure | CLI errors | medium | mitigate | Allowlisted error envelopes; redaction tests | closed |
| T-BAOPS-01-04-ERR | Information Disclosure | Process gateway | high | mitigate | Centralized emission; no traceback/path leakage | closed |
| T-BAOPS-01-04-NET | Information Disclosure | Runtime network | high | mitigate | AST import scan + socket/DNS denial tests | closed |
| T-BAOPS-01-04-LOCKSET | Tampering | Lock files | high | mitigate | Permanent closure equality tests | closed |
| T-BAOPS-01-05-PATH | Tampering | Path resolution | high | mitigate | Same as 03-PATH + adversarial concurrent tests | closed |
| T-BAOPS-01-05-LOCK | Tampering / DoS | Workspace lock | high | mitigate | `state/locking.py`; stale owner recovery | closed |
| T-BAOPS-01-05-PARTIAL | Tampering / DoS | Atomic publication | high | mitigate | `state/atomic.py`; fault injection + quarantine | closed |
| T-BAOPS-01-06-OVERWRITE | Tampering | Init overwrite | high | mitigate | Classify-before-mutate; create-only; byte preservation | closed |
| T-BAOPS-01-06-SCHEMA | Tampering | State validation | high | mitigate | Bundled local schemas; remote `$ref` rejected | closed |
| T-BAOPS-01-06-RACE | Tampering / DoS | Init race | high | mitigate | Single lock scope across quarantine→read-back | closed |
| T-BAOPS-01-07-DEPS | Tampering / EoP | Installer deps | high | mitigate | Hash-locked binary-only offline install | closed |
| T-BAOPS-01-07-PTR | Tampering / EoP | Generation pointer | high | mitigate | Allowlisted component; containment on both launchers | closed |
| T-BAOPS-01-07-SHELL | Tampering / EoP | Shell invocation | high | mitigate | No eval; PS arg arrays; POSIX `"$@"` | closed |
| T-BAOPS-01-07-CONSENT | Repudiation | Network consent | medium | mitigate | Default-No; invocation-scoped; offline bypass only with wheelhouse | closed |
| T-BAOPS-01-08-CMD | Tampering / EoP | Doctor probes | high | mitigate | `shell=False`, bounded output, fixed argv | closed |
| T-BAOPS-01-08-NET | Information Disclosure | Doctor network | high | mitigate | Zero-network doctor tests | closed |
| T-BAOPS-01-08-MUT | Tampering | Doctor mutation | high | mitigate | Read-only; byte/mtime snapshot tests | closed |
| T-BAOPS-01-08-ERR | Information Disclosure | Doctor output | medium | mitigate | Allowlisted observed values; repo-relative paths | closed |
| T-BAOPS-01-09-CI | Tampering / EoP | Workflow source | high | mitigate | Read-only permissions; SHA-pinned actions; contract tests | closed |
| T-BAOPS-01-09-NET | Information Disclosure | CI network boundary | high | mitigate | Wheelhouse setup isolated; product zero-network | closed |
| T-BAOPS-01-09-CLAIM | Repudiation | CI claims | medium | mitigate | Source does not claim remote success | closed |
| T-BAOPS-01-10-EVIDENCE | Spoofing / Repudiation | CI evidence | high | mitigate | Run 29886063228 bound to SHA dcd9859; single-job scope honest | closed |
| T-BAOPS-01-10-LEAK | Information Disclosure | CI logs | medium | mitigate | Redacted step identities; no secrets/abs paths | closed |
| T-BAOPS-01-11-EVIDENCE | Spoofing / Repudiation | Portability handoff | high | mitigate | NFR-02 pending; no false multi-OS claim | closed |
| T-BAOPS-01-11-LEAK | Information Disclosure | Handoff evidence | medium | mitigate | Supplementary evidence labeled non-qualifying | closed |

*32 threats registered. 32 closed. `threats_open: 0` (blocking gate: severity ≥ high).*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01-01 | T-BAOPS-01-01-INFO | Dependency dry-run reports contain public PyPI metadata and temporary local paths only. No credentials, private repository URLs, or customer data appear in approval artifacts or summaries. | Phase 1 security audit | 2026-07-22 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open (blocking) | Run By |
|------------|---------------|--------|-----------------|--------|
| 2026-07-22 | 32 | 32 | 0 | gsd-security-auditor |

**Evidence highlights:** path containment (`paths.py`), workspace locking (`locking.py`), atomic publication (`atomic.py`), zero-network suite, installer hash lock + stale lock recovery (CR-01 fix), POSIX launcher containment (WR-02 fix), CI run 29886063228 at `dcd9859`.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-22
