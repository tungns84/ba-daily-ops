---
phase: BAOPS-01-harness-foundation
depth: standard
reviewed_at: 2026-07-22T05:01:00Z
file_count: 47
verdict: BLOCK
files_reviewed: 47
files_reviewed_list:
  - .gitattributes
  - .github/workflows/foundation.yml
  - .gitignore
  - install.ps1
  - install.sh
  - installer/bootstrap.py
  - installer/launcher-templates/ba-tools
  - installer/launcher-templates/ba-tools.ps1
  - packages/ba-tools/pyproject.toml
  - packages/ba-tools/requirements-dev.lock
  - packages/ba-tools/requirements.lock
  - packages/ba-tools/src/ba_tools/__init__.py
  - packages/ba-tools/src/ba_tools/__main__.py
  - packages/ba-tools/src/ba_tools/cli.py
  - packages/ba-tools/src/ba_tools/contracts.py
  - packages/ba-tools/src/ba_tools/doctor.py
  - packages/ba-tools/src/ba_tools/errors.py
  - packages/ba-tools/src/ba_tools/init_command.py
  - packages/ba-tools/src/ba_tools/paths.py
  - packages/ba-tools/src/ba_tools/state/__init__.py
  - packages/ba-tools/src/ba_tools/state/atomic.py
  - packages/ba-tools/src/ba_tools/state/locking.py
  - packages/ba-tools/src/ba_tools/state/resources/defaults/business-goals.json
  - packages/ba-tools/src/ba_tools/state/resources/defaults/config.json
  - packages/ba-tools/src/ba_tools/state/resources/defaults/coverage-policy.json
  - packages/ba-tools/src/ba_tools/state/resources/schemas/business-goals.schema.json
  - packages/ba-tools/src/ba_tools/state/resources/schemas/config.schema.json
  - packages/ba-tools/src/ba_tools/state/resources/schemas/coverage-policy.schema.json
  - packages/ba-tools/src/ba_tools/state/validation.py
  - packages/ba-tools/tests/conftest.py
  - packages/ba-tools/tests/contract/test_cli_io.py
  - packages/ba-tools/tests/contract/test_dependency_locks.py
  - packages/ba-tools/tests/contract/test_foundation_workflow.py
  - packages/ba-tools/tests/e2e/test_walking_skeleton.py
  - packages/ba-tools/tests/integration/test_doctor.py
  - packages/ba-tools/tests/integration/test_init.py
  - packages/ba-tools/tests/integration/test_installer.py
  - packages/ba-tools/tests/portability/test_supported_versions.py
  - packages/ba-tools/tests/portability/test_terminal_states.py
  - packages/ba-tools/tests/portability/test_utf8.py
  - packages/ba-tools/tests/reliability/test_atomic_write.py
  - packages/ba-tools/tests/reliability/test_locking.py
  - packages/ba-tools/tests/security/test_path_containment.py
  - packages/ba-tools/tests/security/test_zero_network.py
  - packages/ba-tools/tests/unit/test_defaults.py
  - scripts/smoke_foundation.py
  - scripts/verify_dependency_locks.py
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase BAOPS-01: Code Review Report

**Reviewed:** 2026-07-22T05:01:00Z  
**Depth:** standard  
**Files Reviewed:** 47  
**Verdict:** BLOCK  
**Status:** issues_found

## Summary

Reviewed the full Phase 1 foundation surface: `ba_tools` CLI/state/doctor modules, installer bootstrap and wrappers, smoke script, CI workflow, and associated tests. Core path containment, workspace locking, atomic publication, JSON envelope contracts, and hash-pinned offline install paths are well implemented and heavily tested.

One **Critical** installer locking defect can permanently block re-installation after abnormal termination. Three **Warnings** cover prerequisite/version gating inconsistency on Windows, a POSIX launcher containment gap relative to Windows, and fragile CLI command identification in the entrypoint. No secret leakage, command injection, or path-traversal bypass was found in reviewed production code.

**Recommendation:** Fix CR-01 (stale `install.lock` recovery) before treating Phase 1 as merge-ready. Address WR-01–WR-03 in the same pass or immediately after; they are lower severity but affect NFR-06 messaging and defense-in-depth.

## Critical Issues

### CR-01: Stale `install.lock` permanently blocks future installs

**File:** `installer/bootstrap.py:466-489`  
**Issue:** `_install_lock` creates `.ba-tools-runtime/install.lock` with `O_CREAT | O_EXCL` and removes it only in the holder's `finally` block. If the installer process is killed (`SIGKILL`), crashes hard, or loses power while holding the lock, the file persists. Subsequent runs spin until the 30-second deadline and fail; they never unlink the orphaned lock, so every future install attempt repeats the failure until manual deletion.

**Fix:**

```python
def _read_lock_owner(lock_path: Path) -> int | None:
    try:
        text = lock_path.read_text(encoding="ascii").strip()
        pid = int(text)
        return pid if pid > 0 else None
    except (OSError, ValueError):
        return None


def _is_stale_install_lock(lock_path: Path) -> bool:
    pid = _read_lock_owner(lock_path)
    if pid is None:
        return True  # malformed lock is stale
    # Reuse ba_tools.state.locking.probe_process_liveness or equivalent
    from ba_tools.state.locking import ProcessLiveness, probe_process_liveness
    return probe_process_liveness(pid) is ProcessLiveness.DEAD


@contextmanager
def _install_lock(runtime: Path) -> Iterator[None]:
    runtime.mkdir(parents=True, exist_ok=True)
    lock_path = runtime / "install.lock"
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    while True:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            if _is_stale_install_lock(lock_path):
                lock_path.unlink(missing_ok=True)
                continue
            if time.monotonic() >= deadline:
                raise InstallerError(
                    "Another installer did not finish in time.",
                    "Retry after the other installer completes.",
                ) from None
            time.sleep(0.05)
    # ... remainder unchanged
```

## Warnings

### WR-01: `install.ps1` `py -3` path accepts Python 3.11–3.13

**File:** `install.ps1:25`  
**Issue:** When the Windows `py` launcher is present, the wrapper accepts any Python `>= 3.11`, but `bootstrap.discover_prerequisites()` requires `>= 3.14` (NFR-06). Users with `py -3` mapped to 3.11–3.13 pass the shell prerequisite stage and fail later inside bootstrap with a weaker, misattributed error. On hosts where `py -3` resolves below 3.14 but a compliant interpreter exists on PATH, the wrapper may select the wrong interpreter first.

**Fix:** Align the `py -3` probe with bootstrap:

```powershell
& $py.Source -3 -c "import sys;raise SystemExit(0 if sys.version_info >= (3, 14) else 1)" 2>$null
```

### WR-02: POSIX launcher lacks resolved-path containment check

**File:** `installer/launcher-templates/ba-tools:17-20`  
**Issue:** The Windows launcher (`ba-tools.ps1:26-31`) resolves `envs/$generation` and verifies it remains under the `envs` root. The POSIX launcher concatenates `$repo_root/.ba-tools-runtime/envs/$generation/bin/python` without resolving or rejecting symlink/junction escapes. A writable `.ba-tools-runtime/current-env.txt` paired with a symlinked generation directory could execute an interpreter outside the intended runtime tree.

**Fix:** Mirror the Windows containment check before `exec`:

```sh
envs_root=$(CDPATH= cd "$repo_root/.ba-tools-runtime/envs" && pwd -P) || launcher_not_ready
generation_root=$(CDPATH= cd "$envs_root/$generation" 2>/dev/null && pwd -P) || launcher_not_ready
case "$generation_root" in
    "$envs_root"/*) ;;
    *) launcher_not_ready ;;
esac
python=$generation_root/bin/python
```

### WR-03: Entrypoint command identity uses substring matching

**File:** `packages/ba-tools/src/ba_tools/__main__.py:14-23`  
**Issue:** `_command_name()` infers the envelope `command` field via `"init" in arguments` / `"doctor" in arguments`. A repository path or argument value containing those substrings (e.g. `--repo-root D:\projects\init-toolkit`) yields an incorrect `command` label in error envelopes, violating the single-emission CLI contract for malformed-input paths.

**Fix:** Parse with `argparse` or walk flags to locate the first positional subcommand:

```python
def _command_name(arguments: list[str]) -> str:
    if "--version" in arguments:
        return "version"
    if not arguments or "--help" in arguments:
        return "help"
    idx = 0
    while idx < len(arguments):
        token = arguments[idx]
        if token in {"--repo-root", "--repair", "--all"}:
            idx += 2 if token == "--repo-root" else 1
            continue
        if token in {"init", "doctor"}:
            return token
        idx += 1
    return "unknown"
```

## Info

### IN-01: `CheckDefinition.timeout` is never enforced

**File:** `packages/ba-tools/src/ba_tools/doctor.py:238-257`  
**Issue:** Each check declares a `timeout`, but `run_probe()` ignores it; subprocess probes hard-code their own timeouts (e.g. 5.0s in `_git_probe`). Registry metadata is misleading for future probes.

**Fix:** Pass `definition.timeout` into `_command_output` and add a watchdog for non-subprocess probes.

### IN-02: `atomic_replace` is implemented but unused in production paths

**File:** `packages/ba-tools/src/ba_tools/state/atomic.py:154-169`  
**Issue:** Only reliability tests call `atomic_replace`; production init uses create-only publication. Not a defect today, but the unused surface increases maintenance burden.

**Fix:** Either wire it into a future repair/replace path or narrow exports until needed.

---

_Reviewed: 2026-07-22T05:01:00Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
