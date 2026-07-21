# Phase 1: Harness Foundation - Pattern Map

**Mapped:** 2026-07-21  
**Files analyzed:** 45 named files (39 authored/committed surfaces and 6 generated artifacts), plus 3 dynamic runtime file families  
**Analogs found:** 0 / 45

## Greenfield Finding

The repository contains 20 planning, product, and configuration documents and no implementation analogs: no Python, PowerShell, POSIX shell, TOML, test, workflow, package-lock, `.gitignore`, `.gitattributes`, project rule, or project skill files exist. This confirms `01-CONTEXT.md` lines 69-85 and `01-RESEARCH.md` lines 71-79.

Accordingly:

- Every `Closest Existing Analog` below is `none`.
- The cited excerpts are **planning contract seeds**, not code already implemented in this repository.
- The planner should use the locked decisions in `01-CONTEXT.md` first, the exact terminal contract in `01-UI-SPEC.md` second, and the proposed technical patterns in `01-RESEARCH.md` third.
- No external-project or framework sample is promoted to an in-repository analog.

## File Classification

### Authored or Committed Files

| New/Modified File | Origin | Role | Data Flow | Closest Existing Analog | Planning Pattern Source |
|---|---|---|---|---|---|
| `install.ps1` | explicit | config / bootstrap adapter | request-response, subprocess | none | `01-RESEARCH.md` 201-243, 247-252; `01-UI-SPEC.md` 127-167 |
| `install.sh` | explicit | config / bootstrap adapter | request-response, subprocess | none | `01-RESEARCH.md` 201-243, 247-252; `01-UI-SPEC.md` 127-167 |
| `installer/bootstrap.py` | explicit | service | batch, subprocess, file-I/O | none | `01-RESEARCH.md` 247-252, 317-321 |
| `installer/launcher-templates/ba-tools` | explicit | utility / launcher template | request-response, subprocess | none | `01-RESEARCH.md` 317-321; `01-UI-SPEC.md` 214-220 |
| `installer/launcher-templates/ba-tools.ps1` | explicit | utility / launcher template | request-response, subprocess | none | `01-RESEARCH.md` 317-321; `01-UI-SPEC.md` 214-220 |
| `ba-tools/pyproject.toml` | explicit | config | batch | none | `01-RESEARCH.md` 102-120, 596-607, 642-645 |
| `ba-tools/requirements.lock` | explicit | config / dependency lock | batch | none | `01-RESEARCH.md` 132-165, 642-645 |
| `ba-tools/requirements-dev.lock` | explicit | config / dependency lock | batch | none | `01-RESEARCH.md` 114-120, 642-645 |
| `ba-tools/src/ba_tools/__init__.py` | explicit | package config | static | none | `01-RESEARCH.md` 201-243 |
| `ba-tools/src/ba_tools/__main__.py` | explicit | controller / process entrypoint | request-response | none | `01-RESEARCH.md` 261-277, 410-454 |
| `ba-tools/src/ba_tools/cli.py` | explicit | controller / command router | request-response | none | `01-RESEARCH.md` 247-256, 261-277 |
| `ba-tools/src/ba_tools/contracts.py` | explicit | utility / serializer | transform | none | `01-RESEARCH.md` 261-277, 410-454; `01-UI-SPEC.md` 169-185 |
| `ba-tools/src/ba_tools/errors.py` | explicit | model / typed error contract | transform | none | `01-RESEARCH.md` 410-451; `01-UI-SPEC.md` 106-152, 181-185 |
| `ba-tools/src/ba_tools/doctor.py` | explicit | service | batch, request-response | none | `01-RESEARCH.md` 253-255, 323-329; `01-UI-SPEC.md` 187-198 |
| `ba-tools/src/ba_tools/init_command.py` | explicit | service | CRUD, request-response, file-I/O | none | `01-RESEARCH.md` 256-259, 287-307; `01-UI-SPEC.md` 200-212 |
| `ba-tools/src/ba_tools/paths.py` | explicit | utility / filesystem boundary | transform, file-I/O | none | `01-RESEARCH.md` 253-255, 279-285, 456-481 |
| `ba-tools/src/ba_tools/state/atomic.py` | explicit | utility / storage boundary | file-I/O | none | `01-RESEARCH.md` 257-259, 309-315, 483-513 |
| `ba-tools/src/ba_tools/state/locking.py` | explicit | service / concurrency boundary | file-I/O, event-driven wait | none | `01-RESEARCH.md` 257-259, 309-315, 515-535 |
| `ba-tools/src/ba_tools/state/validation.py` | explicit | utility / validator | transform, file-I/O | none | `01-RESEARCH.md` 257-259, 287-307 |
| `ba-tools/src/ba_tools/state/resources/defaults/config.json` | implied | config / default model | file-I/O | none | `01-CONTEXT.md` 32-37; `01-RESEARCH.md` 229-231, 293-307 |
| `ba-tools/src/ba_tools/state/resources/defaults/coverage-policy.json` | implied | config / default model | file-I/O | none | `01-CONTEXT.md` 32-37; `01-RESEARCH.md` 229-231, 293-307 |
| `ba-tools/src/ba_tools/state/resources/defaults/business-goals.json` | implied | config / default model | file-I/O | none | `01-CONTEXT.md` 32-37; `01-RESEARCH.md` 229-231, 293-307 |
| `ba-tools/src/ba_tools/state/resources/schemas/config.schema.json` | implied | model / JSON Schema | transform | none | `01-RESEARCH.md` 92-94, 229-231, 257-259 |
| `ba-tools/src/ba_tools/state/resources/schemas/coverage-policy.schema.json` | implied | model / JSON Schema | transform | none | `01-RESEARCH.md` 92-94, 229-231, 257-259 |
| `ba-tools/src/ba_tools/state/resources/schemas/business-goals.schema.json` | implied | model / JSON Schema | transform | none | `01-RESEARCH.md` 92-94, 229-231, 257-259 |
| `ba-tools/tests/conftest.py` | explicit | test support / fixtures | file-I/O, subprocess, multiprocessing | none | `01-RESEARCH.md` 624-633, 642-647 |
| `ba-tools/tests/contract/test_cli_io.py` | explicit | contract test | request-response, subprocess | none | `01-RESEARCH.md` 609-614, 624-627, 646-647 |
| `ba-tools/tests/integration/test_doctor.py` | explicit | integration test | batch, request-response | none | `01-RESEARCH.md` 613-615, 633 |
| `ba-tools/tests/integration/test_installer.py` | explicit | integration test | batch, subprocess, file-I/O | none | `01-RESEARCH.md` 615, 607, 627, 632 |
| `ba-tools/tests/integration/test_init.py` | explicit | integration test | CRUD, file-I/O | none | `01-RESEARCH.md` 616, 628 |
| `ba-tools/tests/security/test_path_containment.py` | explicit | security test | transform, file-I/O | none | `01-RESEARCH.md` 617, 648, 686 |
| `ba-tools/tests/reliability/test_atomic_write.py` | explicit | reliability test | file-I/O, fault injection | none | `01-RESEARCH.md` 618, 629-630, 649 |
| `ba-tools/tests/reliability/test_locking.py` | explicit | reliability test | multiprocessing, event-driven wait | none | `01-RESEARCH.md` 618, 629, 649 |
| `ba-tools/tests/security/test_zero_network.py` | explicit | security test | request-response, static analysis | none | `01-RESEARCH.md` 620, 631, 685 |
| `ba-tools/tests/portability/test_utf8.py` | explicit | portability test | subprocess, file-I/O | none | `01-RESEARCH.md` 621, 626-627, 650 |
| `ba-tools/tests/unit/test_defaults.py` | explicit | unit test | transform | none | `01-RESEARCH.md` 622, 650 |
| `.github/workflows/foundation.yml` | explicit | config / CI workflow | event-driven, batch | none | `01-RESEARCH.md` 239-242, 619, 651 |
| `.gitignore` | explicit | config | transform | none | `01-RESEARCH.md` 241-245, 652 |
| `.gitattributes` | explicit | config | transform | none | `01-RESEARCH.md` 241-243, 653 |

`resources/defaults/*.json` and `resources/schemas/*.schema.json` are inferred names. The source artifacts require three bundled defaults and three local schemas but show only the `defaults/` and `schemas/` directories. The planner may adjust exact package-resource filenames while preserving one unambiguous default/schema mapping for each durable state file.

### Named Generated Artifacts

| Generated File | Role | Data Flow | Closest Existing Analog | Generator / Consumer Contract |
|---|---|---|---|---|
| `ba-tools` | generated POSIX launcher | request-response, subprocess | none | Generated from `installer/launcher-templates/ba-tools`; resolves its own repo root |
| `ba-tools.ps1` | generated PowerShell launcher | request-response, subprocess | none | Generated from `installer/launcher-templates/ba-tools.ps1`; resolves `$PSScriptRoot` |
| `.ba-tools-runtime/current-env.txt` | generated config pointer | file-I/O | none | Installer writes one allowlisted generation name; launchers read it |
| `.ba-ops/config.json` | durable state model | CRUD, file-I/O | none | `init_command.py` creates; `validation.py` and `doctor.py` read |
| `.ba-ops/coverage-policy.json` | durable state model | CRUD, file-I/O | none | `init_command.py` creates; `validation.py` and `doctor.py` read |
| `.ba-ops/business-goals.json` | durable state model | CRUD, file-I/O | none | `init_command.py` creates; `validation.py` and `doctor.py` read |

### Dynamic Runtime File Families

These are runtime-created families, not standalone source-file implementation tasks:

| Runtime Family | Role | Data Flow | Constraint |
|---|---|---|---|
| `.ba-tools-runtime/envs/<generation>/**` | project-local environment | batch, file-I/O | Build and verify a new generation before changing `current-env.txt`; never rename an installed venv |
| `.ba-ops.lock` plus owner metadata sidecar | concurrency state | event-driven wait, file-I/O | One bounded native workspace lock; sidecar naming is planner discretion; never infer ownership from lock-file existence |
| `.ba-ops/quarantine/atomic/*` | recovery evidence | file-I/O | Preserve abandoned temp bytes and repo-relative target identity; never auto-promote |

## Pattern Assignments

### Installer and Launcher Surfaces

**Files:**

- `install.ps1`
- `install.sh`
- `installer/bootstrap.py`
- `installer/launcher-templates/ba-tools`
- `installer/launcher-templates/ba-tools.ps1`

**Existing analog:** none.

**Planning contract to follow:**

- Keep shell wrappers thin: script-root discovery, prerequisite discovery, OS-specific remediation, and delegation only (`01-RESEARCH.md` lines 247-252).
- Keep consent, hash-locked environment generation, local package installation, verification, and active-pointer switching in `installer/bootstrap.py`.
- The network-capable branch ends at the installer. Runtime launchers and `ba_tools` remain zero-network.
- Build under `.ba-tools-runtime/envs/<digest>/`, verify, then atomically switch the allowlisted `current-env.txt` value (`01-RESEARCH.md` lines 317-321).
- Do not install Python or Git, edit `PATH`, change execution policy, modify shell profiles, or activate an environment.

**Exact installer stage convention** (`01-UI-SPEC.md` lines 158-167):

```text
[1/4] Checking prerequisites
[2/4] Preparing the project-local environment
[3/4] Installing locked dependencies
[4/4] Verifying the repo-root launcher
```

**Exact consent convention** (`01-UI-SPEC.md` lines 127-140):

```text
Download and install locked project dependencies? This requires network access. [y/N]
```

Default is No. `--yes` is invocation-scoped consent; an approved offline wheelhouse requires no prompt. Non-interactive execution without either must fail before network access.

**Launcher contract** (`01-UI-SPEC.md` lines 214-220):

- Preserve every argument, both child streams, and the child exit code.
- Resolve the repository from the launcher file, not the invocation CWD.
- Add no banner, activation text, path echo, or formatting.
- If startup fails, emit one compact UTF-8 `LAUNCHER_NOT_READY` envelope on stderr and exit 2.
- Never expose an absolute interpreter, home, runtime, or repository path.

### CLI Gateway, Contracts, and Errors

**Files:**

- `ba-tools/src/ba_tools/__main__.py`
- `ba-tools/src/ba_tools/cli.py`
- `ba-tools/src/ba_tools/contracts.py`
- `ba-tools/src/ba_tools/errors.py`

**Existing analog:** none.

**Planning-only code seed:** `01-RESEARCH.md` lines 410-451. This is research guidance, not repository code:

```python
def emit_json(stream: object, payload: dict[str, object]) -> None:
    text = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    buffer = getattr(stream, "buffer", None)
    if buffer is not None:
        buffer.write(text.encode("utf-8"))
        buffer.flush()
    else:
        stream.write(text)
        stream.flush()


def main(argv: list[str] | None = None) -> int:
    try:
        result = cli.main(
            args=argv,
            prog_name="ba-tools",
            standalone_mode=False,
        )
    except BaToolsError as exc:
        emit_json(sys.stderr, error_envelope(exc))
        return 2
    except click.ClickException as exc:
        emit_json(sys.stderr, usage_error_envelope(exc))
        return 2
    except Exception:
        emit_json(sys.stderr, internal_error_envelope())
        return 2

    emit_json(sys.stdout, result)
    return 0
```

**Assignment boundaries:**

- `__main__.py`: process entry and returned exit code only.
- `cli.py`: parsing and dispatch with Click `standalone_mode=False`; callbacks return data and never print.
- `contracts.py`: the sole UTF-8 serializer and success/error envelope constructors.
- `errors.py`: typed `BaToolsError` values with stable code, safe message, ordered details, and remediation.

The single-emission contract covers no arguments, help, version, usage errors, unknown commands, expected errors, Ctrl+C, and unexpected failures (`01-UI-SPEC.md` lines 169-185). No command handler may use `print`, `click.echo`, a configured output logger, or direct `sys.exit`.

### Doctor Check DAG

**File:** `ba-tools/src/ba_tools/doctor.py`  
**Existing analog:** none.

Use the registry/check-DAG convention in `01-RESEARCH.md` lines 323-329 and the result contract in `01-UI-SPEC.md` lines 187-198:

- Each check has stable `id`, `status`, `summary`, `observed`, and `remediation`; skipped checks also identify failed prerequisites.
- Registry order, not discovery order, determines output.
- Independent checks continue after failures. Only checks with failed prerequisites become `skipped`.
- Missing core/current-profile requirements produce `fail` and exit 2.
- Missing optional dependencies for disabled plugins produce `warning` and exit 0.
- Default scope is core plus current profile and enabled plugins; `--all` adds every known optional.
- Pre-init checks host/repository. Post-init also checks durable state, schemas, and abandoned temps.
- Local process probes use argument arrays, `shell=False`, and a timeout; no probe installs or queries the network.

### Init State Machine and Durable Defaults

**Files:**

- `ba-tools/src/ba_tools/init_command.py`
- `ba-tools/src/ba_tools/state/validation.py`
- `ba-tools/src/ba_tools/state/resources/defaults/*.json`
- `ba-tools/src/ba_tools/state/resources/schemas/*.schema.json`

**Existing analog:** none.

Classify every existing required file before any mutation (`01-RESEARCH.md` lines 287-307):

1. Absent state directory: fresh.
2. All files present and valid: complete, no-op.
3. Some files missing: partial.
4. Any existing file malformed or schema-invalid: invalid.

Plain `init` writes only from fresh state. `init --repair` writes only missing files from partial state. Both write zero bytes if any existing file is invalid. A valid rerun returns `changed: false`, preserves bytes and mtimes, and has an empty created list.

**Exact default payload seeds** (`01-RESEARCH.md` lines 293-305):

```json
{"profile":"light","schema_version":1}
```

```json
{"per_req":{},"profile":"light","required_artifact_kinds":["srs","flow","mockup"],"schema_version":1,"waivers":[]}
```

```json
{"business_goals":[],"schema_version":1}
```

Schemas remain bundled, versioned, local-only resources. Validation must use explicit validator selection, self-check schemas, reject unsupported versions, collect all stable field-addressed errors, and never retrieve remote `$ref` content.

### Repo-Root Path Capability

**File:** `ba-tools/src/ba_tools/paths.py`  
**Existing analog:** none.

**Planning-only code seed:** `01-RESEARCH.md` lines 456-478:

```python
def resolve_business_path(repo_root: Path, value: str) -> Path:
    if "\x00" in value or "\\" in value:
        raise PathPolicyError("PATH_INVALID")

    portable = PurePosixPath(value)
    if portable.is_absolute() or ".." in portable.parts:
        raise PathPolicyError("PATH_TRAVERSAL")

    root = repo_root.resolve(strict=True)
    candidate = (root / Path(*portable.parts)).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PathPolicyError("PATH_TRAVERSAL") from exc

    reject_existing_symlink_or_reparse_components(root, portable.parts)
    return candidate
```

The implementation must additionally reject Windows drive and UNC forms even on POSIX, reject symlink/reparse components for write targets, and pass validated path capabilities—not unchecked strings—into every state I/O function. Never use CWD, string-prefix containment, or silent normalization as authority.

### Atomic Publication and Quarantine

**File:** `ba-tools/src/ba_tools/state/atomic.py`  
**Existing analog:** none.

**Planning-only code seed:** `01-RESEARCH.md` lines 483-510:

```python
def prepare_temp(target: Path, payload: bytes) -> Path:
    fd, raw_path = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.ba-tmp-",
    )
    temp = Path(raw_path)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return temp


def publish_replace(temp: Path, target: Path) -> None:
    os.replace(temp, target)


def publish_create_only(temp: Path, target: Path) -> None:
    os.link(temp, target, follow_symlinks=False)
    temp.unlink()
```

Keep replacement and create-only publication as separate APIs. `init --repair` must use create-only publication and never fall back to an overwriting or partial direct write. Create temps beside the target, serialize canonical UTF-8 bytes before publication, sync where supported, and quarantine recognizable abandoned temps under the workspace lock. Never auto-promote a temp.

### Bounded Workspace Lock

**File:** `ba-tools/src/ba_tools/state/locking.py`  
**Existing analog:** none.

**Planning-only code seed:** `01-RESEARCH.md` lines 515-532:

```python
from filelock import FileLock, Timeout


def acquire_workspace_lock(repo_root: Path, timeout_seconds: float = 5.0):
    lock = FileLock(repo_root / ".ba-ops.lock", timeout=timeout_seconds)
    try:
        return lock.acquire()
    except Timeout as exc:
        raise BaToolsError(
            code="WORKSPACE_LOCK_TIMEOUT",
            message="Another workspace writer did not finish in time.",
            remediation=["Retry after the other ba-tools command completes."],
        ) from exc
```

The final implementation must hold the native lock through the complete mutation, manage owner metadata after acquisition and before release, and fail closed when owner state is ambiguous. A persistent lock file is not proof of ownership and must not be deleted as “stale.” Recovery requires native lock availability plus proof that the recorded owner process is no longer active.

### Package, Lock, CI, and Repository Configuration

**Files:**

- `ba-tools/pyproject.toml`
- `ba-tools/requirements.lock`
- `ba-tools/requirements-dev.lock`
- `.github/workflows/foundation.yml`
- `.gitignore`
- `.gitattributes`

**Existing analog:** none.

Apply these planning conventions:

- Python floor is `>=3.11`; package layout is `src/ba_tools`.
- Build backend, runtime dependencies, development dependencies, pytest, and Ruff configuration begin in `pyproject.toml`.
- Dependency locks require exact direct and transitive pins plus SHA-256 hashes; runtime installation uses hash mode, binary-only dependencies, and local package `--no-deps`.
- The six proposed direct packages are marked `SUS` by the legitimacy seam. Planning must include a blocking human-verification checkpoint and rerun legitimacy checks for resolved transitives before final lock creation (`01-RESEARCH.md` lines 149-165).
- CI covers Python 3.11 and a current supported version on Windows, macOS, and Linux, plus installer/launcher smoke. Newer hosted runners do not prove Windows 10 or macOS 12 minimum-version support.
- `.gitignore` excludes `.ba-tools-runtime/`, native lock/owner files, `.ba-ops/quarantine/`, caches, and build output while preserving canonical `.ba-ops/*.json`.
- `.gitattributes` forces LF for POSIX launcher/template and text resources; no committed file may gain a machine-specific absolute path.

### Test Pattern Assignments

There is no existing pytest style to copy. Use the test contract, fixture, and command mapping already specified by `01-RESEARCH.md` lines 596-650.

| Test File | Primary Contract |
|---|---|
| `tests/conftest.py` | Temporary repo under Unicode/space paths, byte subprocess runner, fake executables, lock-holder process, and fault-injection helpers |
| `tests/contract/test_cli_io.py` | Exactly one UTF-8 JSON document, one LF, no BOM/ANSI/logging, correct stream, and exit 0/2 for every parser and runtime path |
| `tests/integration/test_doctor.py` | Check DAG ordering, pre/post-init scope, optional warning policy, core failure policy, and skipped prerequisites |
| `tests/integration/test_installer.py` | Missing prerequisites, consent/refusal, offline mode, path with spaces, lock synchronization, launcher verification, no PATH mutation |
| `tests/integration/test_init.py` | Fresh, no-op, partial failure, repair, invalid-preserve, exact defaults, bytes/hash/mtime unchanged on no-op and failure |
| `tests/security/test_path_containment.py` | `..`, absolute, drive-relative, UNC, backslash, NUL, sibling prefix, Unicode, symlink, and junction/reparse cases |
| `tests/reliability/test_atomic_write.py` | Faults before/after write, flush, fsync, link, replace, cleanup, and quarantine; canonical remains absent or previously complete |
| `tests/reliability/test_locking.py` | Contention timeout, process crash, live/dead/unknown owner, no age-only stale break, and single-writer behavior |
| `tests/security/test_zero_network.py` | Runtime import scan plus socket/DNS denial while invoking every Phase 1 command; installer reviewed separately |
| `tests/portability/test_utf8.py` | Vietnamese bytes through redirected streams, JSON files, error envelopes, and Unicode repo paths on every OS |
| `tests/unit/test_defaults.py` | Byte-stable minimal defaults and absence of inferred/sample business content |

Tests should assert bytes and filesystem effects, not only in-process Python objects. Use real subprocesses for stream/encoding behavior, multiprocessing for lock behavior, and injected failures for durability. Keep test data deterministic and report repo-relative paths only.

## Shared Patterns

### Single Process Emission

**Source:** `01-RESEARCH.md` lines 261-277 and 410-454; `01-UI-SPEC.md` lines 169-185  
**Apply to:** `__main__.py`, `cli.py`, `contracts.py`, `errors.py`, `doctor.py`, `init_command.py`, and launcher fallback paths

One outer boundary owns serialization and stream selection. Success and warnings use one stdout JSON object and exit 0. Any failure uses one stderr JSON object and exit 2. Command and service functions return data or raise typed errors; they never emit.

### Canonical UTF-8 JSON

**Source:** `01-RESEARCH.md` lines 267-277 and 410-451; `01-UI-SPEC.md` lines 169-185  
**Apply to:** all CLI envelopes, packaged defaults, durable state, and launcher fallback errors

Use `ensure_ascii=False`, `allow_nan=False`, compact separators, deterministic ordering, no BOM/ANSI, and exactly one trailing LF. Launch Python with `-X utf8`, but still write final process bytes explicitly.

### Typed, Safe Errors

**Source:** `01-UI-SPEC.md` lines 106-152 and 181-185  
**Apply to:** every runtime boundary

Stable code, concise safe message, ordered details, and actionable remediation are data. Do not include tracebacks, environment dumps, secrets, home directories, absolute repository paths, or interpreter/runtime paths.

### Validate Before Mutating

**Source:** `01-CONTEXT.md` lines 32-43; `01-RESEARCH.md` lines 287-315  
**Apply to:** `init_command.py`, `validation.py`, `locking.py`, and `atomic.py`

Acquire one workspace lock, quarantine recognizable abandoned temps, classify and validate all existing canonical state, select one allowed transition, then publish. Never interleave validation with repair writes.

### Repo-Root Capability

**Source:** `01-CONTEXT.md` lines 81-85; `01-RESEARCH.md` lines 279-285  
**Apply to:** installer, launchers, CLI dispatch, doctor, init, validation, locking, atomic I/O, and all displayed paths

The launcher's location or explicit `--repo-root` establishes authority. Every business path is a validated canonical POSIX-relative path contained under the resolved root.

### Runtime Zero-Network Boundary

**Source:** `01-RESEARCH.md` lines 94-95, 331-340, 669-688  
**Apply to:** all `ba_tools` modules and doctor probes

Only the explicitly consented installer may access dependency sources. Runtime code performs local file, schema, process, and host checks only; it has no update checks, telemetry, DNS, HTTP, or LLM calls.

### No Authentication Pattern

Phase 1 has no user identity, credentials, sessions, remote principals, or authorization middleware. Do not invent auth code. The relevant security patterns are repository containment, create-only repair, dependency integrity, safe process invocation, fail-closed lock recovery, and redacted errors (`01-RESEARCH.md` lines 655-681).

## No Analog Found

| File Group | Role / Flow | Why No Analog Exists | Planner Fallback |
|---|---|---|---|
| Installers and launcher templates | bootstrap; subprocess/file-I/O | No `.ps1`, `.sh`, or launcher source exists | Use locked decisions D-01 through D-06 and UI installer/launcher contract |
| Python CLI and services | controller/service; request-response/batch | No Python package or manifest exists | Use research process-boundary, doctor-DAG, and init-state-machine seeds |
| State boundary | utility/service; file-I/O/concurrency | No storage, lock, validation, or path code exists | Use research containment, atomic, native-lock, and validation seeds |
| Defaults and schemas | config/model; transform/file-I/O | No product JSON/schema files exist | Use the three exact research defaults and canonical BRD/SRS compatibility |
| Tests | test; subprocess/file-I/O/multiprocessing | No test framework or test files exist | Use the requirement-to-test map and Wave 0 fixture list |
| Build, dependency, CI, repository config | config; batch/event-driven | No TOML, lock, workflow, ignore, or attributes files exist | Use Standard Stack, legitimacy checkpoint, and Validation Architecture |
| Generated launchers and durable state | generated utility/model; subprocess/CRUD | Workspace has not been installed or initialized | Generate only through installer/init behavior; do not commit machine-local runtime paths |

## Planning Guardrails

- D-03 overrides the roadmap's literal “on PATH” phrase: acceptance means direct invocation through the repo-root launchers, with no persistent PATH modification.
- Do not plan REQ-ID registries, SRS commands, workflow execution, artifact generation, trace/INDEX behavior, plugins, or team mode in Phase 1.
- Do not treat the planning-only code seeds as complete production implementations; they intentionally omit final imports, ownership metadata lifecycle, Windows reparse implementation, directory syncing, schema packaging details, and complete exception taxonomy.
- Do not create a second serializer, generic overwrite-capable repair API, global temp path, age-only stale-lock breaker, CWD-derived business path, or installer/runtime network coupling.
- Exact resource filenames, lock sidecar name, timeout value, quarantine naming, and package marker placement remain planner discretion where the source artifacts do not fix them.

## Metadata

**Analog search scope:** Full repository, including Python, PowerShell, POSIX shell, TOML, JSON/schema, tests, workflows, repository config, `.cursor/rules/`, `.cursor/skills/`, and `.agents/skills/`  
**Repository files inventoried:** 20  
**Implementation candidates found:** 0  
**Project rules found:** 0  
**Project skills found:** 0  
**Pattern extraction date:** 2026-07-21  
**Primary scope sources:** `01-CONTEXT.md`, `01-RESEARCH.md`, `01-UI-SPEC.md`, `.planning/ROADMAP.md`
