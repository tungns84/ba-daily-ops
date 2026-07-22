"""Ordered dependency-aware, read-only local diagnostics."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ba_tools import __version__
from ba_tools.errors import BaToolsError
from ba_tools.paths import ResolvedRepoRoot, resolve_business_path
from ba_tools.state.validation import (
    STATE_SCHEMA_BY_PATH,
    load_schema,
    validate_state_file,
)

TOOL_VERSION = "0.1.0"
POINTER_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
VERSION_PATTERN = re.compile(r"(?<!\d)(\d+)(?:\.(\d+))?(?:\.(\d+))?")
MAX_PROCESS_OUTPUT = 4096


class CheckScope(StrEnum):
    """Selection group for one diagnostic definition."""

    CORE = "core"
    STATE = "state"
    OPTIONAL = "optional"


class CheckStatus(StrEnum):
    """Stable status values exposed by doctor."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class DoctorContext:
    """Read-only facts shared by all selected probes."""

    root: ResolvedRepoRoot
    initialized: bool
    profile: str
    enabled_plugins: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProbeObservation:
    """Allowlisted probe outcome before requiredness is applied."""

    ok: bool
    summary: str
    observed: dict[str, object]
    remediation: tuple[str, ...] = ()


RequiredWhen = bool | Callable[[DoctorContext], bool]
Probe = Callable[[DoctorContext], ProbeObservation]


@dataclass(frozen=True, slots=True)
class CheckDefinition:
    """One immutable registry entry."""

    id: str
    scope: CheckScope
    required_when: RequiredWhen
    prerequisites: tuple[str, ...]
    probe: Probe
    timeout: float


@dataclass(frozen=True, slots=True)
class CheckResult:
    """One complete ordered diagnostic result."""

    id: str
    status: CheckStatus
    summary: str
    observed: dict[str, object]
    remediation: tuple[str, ...]
    blocked_by: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        """Return the stable process representation."""

        return {
            "id": self.id,
            "status": self.status.value,
            "summary": self.summary,
            "observed": self.observed,
            "remediation": list(self.remediation),
            "blocked_by": list(self.blocked_by),
        }


@dataclass(frozen=True, slots=True)
class DoctorResult:
    """Complete snapshot and aggregate status."""

    status: CheckStatus
    checks: tuple[CheckResult, ...]

    def as_dict(self) -> dict[str, object]:
        """Return the complete ordered snapshot."""

        return {
            "status": self.status.value,
            "checks": [check.as_dict() for check in self.checks],
        }


def _safe_process_env() -> dict[str, str]:
    allowed = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TMP", "TEMP")
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONUTF8"] = "1"
    return environment


def _command_output(arguments: list[str], *, timeout: float) -> tuple[bool, str]:
    """Run one fixed argument vector and return bounded decoded output."""

    try:
        result = subprocess.run(
            arguments,
            shell=False,
            check=False,
            capture_output=True,
            timeout=timeout,
            env=_safe_process_env(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    combined = result.stdout + result.stderr
    if result.returncode != 0 or len(combined) > MAX_PROCESS_OUTPUT:
        return False, ""
    try:
        return True, combined.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        return False, ""


def _version_tuple(text: str) -> tuple[int, int, int] | None:
    match = VERSION_PATTERN.search(text)
    if match is None:
        return None
    return tuple(int(value or 0) for value in match.groups())


def _required(definition: CheckDefinition, context: DoctorContext) -> bool:
    value = definition.required_when
    return value(context) if callable(value) else value


def validate_registry(definitions: Iterable[CheckDefinition]) -> tuple[CheckDefinition, ...]:
    """Reject invalid registries before any probe executes."""

    registry = tuple(definitions)
    if not any(definition.scope is CheckScope.CORE for definition in registry):
        raise ValueError("core registry cannot be empty")

    by_id: dict[str, CheckDefinition] = {}
    for definition in registry:
        if not definition.id or definition.id in by_id:
            raise ValueError(f"duplicate check id: {definition.id}")
        if definition.timeout <= 0:
            raise ValueError(f"check timeout must be positive: {definition.id}")
        if len(set(definition.prerequisites)) != len(definition.prerequisites):
            raise ValueError(f"duplicate prerequisite for check: {definition.id}")
        by_id[definition.id] = definition

    positions = {definition.id: index for index, definition in enumerate(registry)}
    for definition in registry:
        for prerequisite in definition.prerequisites:
            if prerequisite not in by_id:
                raise ValueError(f"unknown prerequisite {prerequisite} for {definition.id}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(check_id: str) -> None:
        if check_id in visiting:
            raise ValueError(f"check dependency cycle includes {check_id}")
        if check_id in visited:
            return
        visiting.add(check_id)
        for prerequisite in by_id[check_id].prerequisites:
            visit(prerequisite)
        visiting.remove(check_id)
        visited.add(check_id)

    for definition in registry:
        visit(definition.id)
        for prerequisite in definition.prerequisites:
            if positions[prerequisite] >= positions[definition.id]:
                raise ValueError(
                    f"prerequisite {prerequisite} must precede {definition.id}"
                )
    return registry


def select_checks(
    definitions: Iterable[CheckDefinition],
    context: DoctorContext,
    *,
    include_all: bool,
) -> tuple[CheckDefinition, ...]:
    """Select checks without changing their declared order."""

    registry = validate_registry(definitions)
    selected: list[CheckDefinition] = []
    for definition in registry:
        if definition.scope is CheckScope.CORE:
            selected.append(definition)
        elif definition.scope is CheckScope.STATE and context.initialized:
            selected.append(definition)
        elif definition.scope is CheckScope.OPTIONAL and (
            include_all or _required(definition, context)
        ):
            selected.append(definition)
    return tuple(selected)


def run_probe(definition: CheckDefinition, context: DoctorContext) -> ProbeObservation:
    """Execute one local probe and convert unexpected probe errors to safe evidence."""

    try:
        observation = definition.probe(context)
    except (BaToolsError, OSError, UnicodeError, ValueError):
        return ProbeObservation(
            ok=False,
            summary="The local diagnostic could not be completed safely.",
            observed={"error": "probe_failed"},
            remediation=("Check the local repository state, then rerun doctor.",),
        )
    if not isinstance(observation, ProbeObservation):
        return ProbeObservation(
            ok=False,
            summary="The local diagnostic returned an invalid result.",
            observed={"error": "invalid_probe_result"},
            remediation=("Reinstall the exact ba-tools package and rerun doctor.",),
        )
    return observation


def execute_check_registry(
    definitions: Iterable[CheckDefinition],
    context: DoctorContext,
) -> DoctorResult:
    """Execute every selected check once, skipping only blocked descendants."""

    registry = validate_registry(definitions)
    result_by_id: dict[str, CheckResult] = {}
    results: list[CheckResult] = []
    for definition in registry:
        blocked_by = tuple(
            prerequisite
            for prerequisite in definition.prerequisites
            if result_by_id[prerequisite].status is not CheckStatus.PASS
        )
        if blocked_by:
            result = CheckResult(
                id=definition.id,
                status=CheckStatus.SKIPPED,
                summary="The check was skipped because a prerequisite did not pass.",
                observed={},
                remediation=("Resolve the blocking checks, then rerun doctor.",),
                blocked_by=blocked_by,
            )
        else:
            observation = run_probe(definition, context)
            status = (
                CheckStatus.PASS
                if observation.ok
                else CheckStatus.FAIL
                if _required(definition, context)
                else CheckStatus.WARNING
            )
            result = CheckResult(
                id=definition.id,
                status=status,
                summary=observation.summary,
                observed=observation.observed,
                remediation=observation.remediation,
            )
        results.append(result)
        result_by_id[result.id] = result

    if any(result.status is CheckStatus.FAIL for result in results):
        status = CheckStatus.FAIL
    elif any(result.status is CheckStatus.WARNING for result in results):
        status = CheckStatus.WARNING
    else:
        status = CheckStatus.PASS
    return DoctorResult(status=status, checks=tuple(results))


def _os_probe(_context: DoctorContext) -> ProbeObservation:
    if sys.platform == "win32":
        system = "Windows"
        observed_version = sys.getwindowsversion()
        version = (
            observed_version.major,
            observed_version.minor,
            observed_version.build,
        )
        release = ".".join(map(str, version))
        supported = version is not None and version >= (10, 0, 0)
        remediation = () if supported else ("Use Windows 10 or newer.",)
    elif sys.platform == "darwin":
        system = "Darwin"
        release = os.uname().release
        version = _version_tuple(release)
        supported = False
        remediation = ("Current release scope supports Windows 10+ only.",)
    elif sys.platform.startswith("linux"):
        system = "Linux"
        release = os.uname().release
        supported = False
        remediation = ("Current release scope supports Windows 10+ only.",)
    else:
        system = sys.platform
        release = ""
        supported = False
        remediation = ("Use Windows 10 or newer.",)
    return ProbeObservation(
        ok=supported,
        summary=(
            "The operating system is supported."
            if supported
            else "The operating system is unsupported."
        ),
        observed={"system": system, "release": release},
        remediation=remediation,
    )


def _python_probe(_context: DoctorContext) -> ProbeObservation:
    version = sys.version_info[:3]
    supported = version >= (3, 14, 0)
    rendered = ".".join(map(str, version))
    return ProbeObservation(
        ok=supported,
        summary="Python meets the supported version floor."
        if supported
        else "Python 3.14 or newer is required.",
        observed={"version": rendered, "minimum": "3.14"},
        remediation=()
        if supported
        else ("Install Python 3.14 or newer, then rerun the repository installer.",),
    )


def _utf8_probe(_context: DoctorContext) -> ProbeObservation:
    stream_encodings = {
        name: str(getattr(getattr(sys, name), "encoding", "") or "").lower().replace("-", "")
        for name in ("stdin", "stdout", "stderr")
    }
    supported = (
        sys.flags.utf8_mode == 1
        and sys.getfilesystemencoding().lower().replace("-", "") == "utf8"
        and all(value == "utf8" for value in stream_encodings.values())
    )
    return ProbeObservation(
        ok=supported,
        summary="Python and standard streams use UTF-8."
        if supported
        else "Python UTF-8 mode or a standard stream is not UTF-8.",
        observed={
            "utf8_mode": bool(sys.flags.utf8_mode),
            "filesystem_encoding": sys.getfilesystemencoding(),
            "stream_encodings": stream_encodings,
        },
        remediation=()
        if supported
        else ("Run ba-tools through the generated repository-root launcher.",),
    )


def _git_probe(_context: DoctorContext) -> ProbeObservation:
    executable = shutil.which("git")
    if executable is None:
        return ProbeObservation(
            ok=False,
            summary="Git is not available.",
            observed={"available": False},
            remediation=("Install Git 2 or newer, then rerun doctor.",),
        )
    succeeded, output = _command_output([executable, "--version"], timeout=5.0)
    version = _version_tuple(output) if succeeded else None
    supported = version is not None and version >= (2, 0, 0)
    return ProbeObservation(
        ok=supported,
        summary="Git meets the supported version floor."
        if supported
        else "Git 2 or newer is required.",
        observed={
            "available": succeeded,
            "version": ".".join(map(str, version)) if version is not None else None,
            "minimum": "2.0",
        },
        remediation=()
        if supported
        else ("Install Git 2 or newer, then rerun doctor.",),
    )


def _repo_probe(context: DoctorContext) -> ProbeObservation:
    marker = context.root.path / ".git"
    supported = marker.is_dir() or marker.is_file()
    return ProbeObservation(
        ok=supported,
        summary="The repository root contains Git metadata."
        if supported
        else "The selected root is not a Git repository.",
        observed={"root": ".", "git_metadata": supported},
        remediation=()
        if supported
        else ("Run doctor from a Git repository root.",),
    )


def _active_generation(context: DoctorContext) -> tuple[Path, dict[str, object]] | None:
    runtime = context.root.path / ".ba-tools-runtime"
    pointer = runtime / "current-env.txt"
    try:
        lines = pointer.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    if (
        len(lines) != 1
        or POINTER_COMPONENT.fullmatch(lines[0]) is None
        or lines[0] in {".", ".."}
    ):
        return None
    envs = (runtime / "envs").resolve()
    generation = (envs / lines[0]).resolve()
    try:
        generation.relative_to(envs)
    except ValueError:
        return None
    identity_path = generation / ".ba-tools-install.json"
    try:
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(identity, dict):
        return None
    return generation, identity


def _generation_python(generation: Path) -> Path:
    return generation / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _install_version_probe(context: DoctorContext) -> ProbeObservation:
    active = _active_generation(context)
    if active is None:
        return ProbeObservation(
            ok=False,
            summary="No valid project-local BA Tools generation is active.",
            observed={"active": False},
            remediation=("Rerun the repository installer, then retry doctor.",),
        )
    generation, _identity = active
    interpreter = _generation_python(generation)
    if not interpreter.is_file():
        return ProbeObservation(
            ok=False,
            summary="The active BA Tools interpreter is unavailable.",
            observed={"active": True, "version": None},
            remediation=("Rerun the repository installer, then retry doctor.",),
        )
    is_active_interpreter = Path(sys.executable).resolve() == interpreter.resolve()
    try:
        metadata_version = importlib.metadata.version("ba-tools")
        module_version = __version__
    except importlib.metadata.PackageNotFoundError:
        metadata_version, module_version = None, None
    valid = (
        is_active_interpreter
        and metadata_version == module_version == TOOL_VERSION == __version__
    )
    return ProbeObservation(
        ok=valid,
        summary="The installed BA Tools version is exactly 0.1.0."
        if valid
        else "The installed BA Tools version does not match 0.1.0.",
        observed={
            "expected": TOOL_VERSION,
            "metadata_version": metadata_version,
            "module_version": module_version,
            "active_interpreter": is_active_interpreter,
        },
        remediation=()
        if valid
        else ("Rerun the repository installer to synchronize ba-tools 0.1.0.",),
    )


def _lock_digest_probe(context: DoctorContext) -> ProbeObservation:
    active = _active_generation(context)
    lock_path = context.root.path / "packages" / "ba-tools" / "requirements.lock"
    try:
        actual = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    except OSError:
        actual = None
    approved = active[1].get("lock_digest") if active is not None else None
    valid = isinstance(approved, str) and actual == approved
    return ProbeObservation(
        ok=valid,
        summary="The active generation matches the approved dependency lock."
        if valid
        else "The active generation does not match the approved dependency lock.",
        observed={
            "approved": bool(valid),
            "digest": actual if valid else None,
        },
        remediation=()
        if valid
        else ("Rerun the repository installer to synchronize the approved lock.",),
    )


def _active_generation_probe(context: DoctorContext) -> ProbeObservation:
    active = _active_generation(context)
    valid = False
    generation_name: str | None = None
    if active is not None:
        generation, identity = active
        generation_name = generation.name
        valid = (
            generation.is_dir()
            and _generation_python(generation).is_file()
            and identity.get("package") == "ba-tools==0.1.0"
            and identity.get("format_version") == 1
        )
    return ProbeObservation(
        ok=valid,
        summary="The active generation is contained and complete."
        if valid
        else "The active generation is invalid or incomplete.",
        observed={"generation": generation_name if valid else None, "contained": valid},
        remediation=()
        if valid
        else ("Rerun the repository installer to publish a verified generation.",),
    )


def _launcher_probe(context: DoctorContext) -> ProbeObservation:
    if os.name == "nt":
        launcher_name = "ba-tools.ps1"
        template_name = "ba-tools.ps1"
    else:
        launcher_name = "ba-tools"
        template_name = "ba-tools"
    launcher = context.root.path / launcher_name
    template = context.root.path / "installer" / "launcher-templates" / template_name
    try:
        valid = launcher.read_bytes() == template.read_bytes()
        if os.name != "nt":
            valid = valid and os.access(launcher, os.X_OK)
    except OSError:
        valid = False
    return ProbeObservation(
        ok=valid,
        summary="The current-platform repository launcher matches its template."
        if valid
        else "The current-platform repository launcher is missing or stale.",
        observed={"launcher": launcher_name, "current": valid},
        remediation=()
        if valid
        else ("Rerun the repository installer to regenerate the launcher.",),
    )


def _state_file_probe(relative_path: str) -> Probe:
    def probe(context: DoctorContext) -> ProbeObservation:
        target = resolve_business_path(context.root, relative_path)
        try:
            payload = target.path.read_bytes()
        except OSError:
            return ProbeObservation(
                ok=False,
                summary="A required workspace state file is unavailable.",
                observed={"path": relative_path, "present": False, "diagnostics": []},
                remediation=("Run init --repair to create missing state files only.",),
            )
        diagnostics = validate_state_file(relative_path, payload)
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            decoded = {}
        observed: dict[str, object] = {
            "path": relative_path,
            "present": True,
            "schema_version": decoded.get("schema_version")
            if isinstance(decoded, dict)
            else None,
            "diagnostics": [diagnostic.as_dict() for diagnostic in diagnostics],
        }
        return ProbeObservation(
            ok=not diagnostics,
            summary="The workspace state file is valid."
            if not diagnostics
            else "The workspace state file is invalid.",
            observed=observed,
            remediation=()
            if not diagnostics
            else ("Correct the reported fields, then retry.",),
        )

    return probe


def _schemas_probe(_context: DoctorContext) -> ProbeObservation:
    for schema_name in STATE_SCHEMA_BY_PATH.values():
        load_schema(schema_name)
    return ProbeObservation(
        ok=True,
        summary="All packaged workspace schemas are valid and local.",
        observed={"schemas": list(STATE_SCHEMA_BY_PATH.values()), "draft": "2020-12"},
    )


def _profile_policy_probe(context: DoctorContext) -> ProbeObservation:
    config_path = resolve_business_path(context.root, ".ba-ops/config.json").path
    policy_path = resolve_business_path(context.root, ".ba-ops/coverage-policy.json").path
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        config, policy = {}, {}
    profile = config.get("profile") if isinstance(config, dict) else None
    policy_profile = policy.get("profile") if isinstance(policy, dict) else None
    artifact_kinds = policy.get("required_artifact_kinds") if isinstance(policy, dict) else None
    valid = (
        profile == policy_profile == "light"
        and artifact_kinds == ["srs", "flow", "mockup"]
    )
    return ProbeObservation(
        ok=valid,
        summary="The current profile and coverage policy are consistent."
        if valid
        else "The current profile and coverage policy are inconsistent.",
        observed={
            "profile": profile,
            "policy_profile": policy_profile,
            "required_artifact_kinds": artifact_kinds
            if isinstance(artifact_kinds, list)
            else [],
        },
        remediation=()
        if valid
        else ("Correct the profile and coverage policy, then rerun doctor.",),
    )


def _abandoned_temps_probe(context: DoctorContext) -> ProbeObservation:
    found: list[str] = []
    quarantine_prefix = ".ba-ops/quarantine"
    pattern = re.compile(r"^\..+\.ba-tmp-[A-Za-z0-9][A-Za-z0-9._-]*$")
    for current_text, directories, filenames in os.walk(
        context.root.path,
        followlinks=False,
    ):
        current = Path(current_text)
        relative_directory = current.relative_to(context.root.path).as_posix()
        if relative_directory == quarantine_prefix or relative_directory.startswith(
            f"{quarantine_prefix}/"
        ):
            directories[:] = []
            continue
        for filename in sorted(filenames):
            if pattern.fullmatch(filename):
                found.append((current / filename).relative_to(context.root.path).as_posix())
    return ProbeObservation(
        ok=not found,
        summary="No abandoned atomic-write temporary files were found."
        if not found
        else "Abandoned atomic-write temporary files require inspection.",
        observed={"count": len(found), "paths": found},
        remediation=()
        if not found
        else ("Run init to quarantine abandoned atomic-write evidence safely.",),
    )


def _optional_command_probe(
    executable_names: tuple[str, ...],
    arguments: tuple[str, ...],
    *,
    minimum: tuple[int, int, int] | None = None,
) -> Probe:
    def probe(_context: DoctorContext) -> ProbeObservation:
        executable = next(
            (candidate for name in executable_names if (candidate := shutil.which(name))),
            None,
        )
        if executable is None:
            return ProbeObservation(
                ok=False,
                summary="The optional local tool is unavailable.",
                observed={"available": False, "version": None},
                remediation=("Install the optional tool only if its plugin is enabled.",),
            )
        succeeded, output = _command_output(
            [executable, *arguments],
            timeout=5.0,
        )
        version = _version_tuple(output) if succeeded else None
        valid = succeeded and (minimum is None or (version is not None and version >= minimum))
        return ProbeObservation(
            ok=valid,
            summary="The optional local tool is available."
            if valid
            else "The optional local tool is unavailable or unsupported.",
            observed={
                "available": succeeded,
                "version": ".".join(map(str, version)) if version is not None else None,
                "minimum": ".".join(map(str, minimum)) if minimum is not None else None,
            },
            remediation=()
            if valid
            else ("Install a supported optional tool only if its plugin is enabled.",),
        )

    return probe


def _plugin_required(*plugin_names: str) -> Callable[[DoctorContext], bool]:
    names = frozenset(plugin_names)
    return lambda context: bool(names.intersection(context.enabled_plugins))


CORE_CHECKS = (
    CheckDefinition("os.supported", CheckScope.CORE, True, (), _os_probe, 1.0),
    CheckDefinition("python.version", CheckScope.CORE, True, (), _python_probe, 1.0),
    CheckDefinition(
        "python.utf8",
        CheckScope.CORE,
        True,
        ("python.version",),
        _utf8_probe,
        1.0,
    ),
    CheckDefinition("git.version", CheckScope.CORE, True, (), _git_probe, 5.0),
    CheckDefinition("repo.root", CheckScope.CORE, True, (), _repo_probe, 1.0),
    CheckDefinition(
        "install.version",
        CheckScope.CORE,
        True,
        ("repo.root",),
        _install_version_probe,
        10.0,
    ),
    CheckDefinition(
        "install.lock_digest",
        CheckScope.CORE,
        True,
        ("install.version",),
        _lock_digest_probe,
        2.0,
    ),
    CheckDefinition(
        "install.active_generation",
        CheckScope.CORE,
        True,
        ("install.lock_digest",),
        _active_generation_probe,
        2.0,
    ),
    CheckDefinition(
        "launcher.current",
        CheckScope.CORE,
        True,
        ("install.active_generation",),
        _launcher_probe,
        2.0,
    ),
)

PROFILE_CHECKS = (
    CheckDefinition(
        "state.config",
        CheckScope.STATE,
        True,
        (),
        _state_file_probe(".ba-ops/config.json"),
        2.0,
    ),
    CheckDefinition(
        "state.coverage_policy",
        CheckScope.STATE,
        True,
        (),
        _state_file_probe(".ba-ops/coverage-policy.json"),
        2.0,
    ),
    CheckDefinition(
        "state.business_goals",
        CheckScope.STATE,
        True,
        (),
        _state_file_probe(".ba-ops/business-goals.json"),
        2.0,
    ),
    CheckDefinition(
        "state.schemas",
        CheckScope.STATE,
        True,
        ("state.config", "state.coverage_policy", "state.business_goals"),
        _schemas_probe,
        2.0,
    ),
    CheckDefinition(
        "state.profile_policy",
        CheckScope.STATE,
        True,
        ("state.config", "state.coverage_policy"),
        _profile_policy_probe,
        2.0,
    ),
    CheckDefinition(
        "state.abandoned_temps",
        CheckScope.STATE,
        False,
        (),
        _abandoned_temps_probe,
        5.0,
    ),
)

OPTIONAL_CHECKS = (
    CheckDefinition(
        "optional.node",
        CheckScope.OPTIONAL,
        _plugin_required("mermaid", "bpmn"),
        (),
        _optional_command_probe(("node",), ("--version",), minimum=(18, 0, 0)),
        5.0,
    ),
    CheckDefinition(
        "optional.mmdc",
        CheckScope.OPTIONAL,
        _plugin_required("mermaid"),
        (),
        _optional_command_probe(("mmdc",), ("--version",)),
        5.0,
    ),
    CheckDefinition(
        "optional.drawio",
        CheckScope.OPTIONAL,
        _plugin_required("bpmn"),
        (),
        _optional_command_probe(
            ("drawio", "draw.io", "drawio.exe", "draw.io.exe"),
            ("--version",),
        ),
        5.0,
    ),
)

CHECK_REGISTRY = validate_registry((*CORE_CHECKS, *PROFILE_CHECKS, *OPTIONAL_CHECKS))


def _context(root: ResolvedRepoRoot) -> DoctorContext:
    initialized = resolve_business_path(root, ".ba-ops").path.is_dir()
    profile = "light"
    enabled_plugins: tuple[str, ...] = ()
    config_path = resolve_business_path(root, ".ba-ops/config.json").path
    if initialized:
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            config = {}
        if isinstance(config, dict):
            if isinstance(config.get("profile"), str):
                profile = config["profile"]
            plugins = config.get("enabled_plugins")
            if isinstance(plugins, list) and all(isinstance(item, str) for item in plugins):
                enabled_plugins = tuple(plugins)
    return DoctorContext(
        root=root,
        initialized=initialized,
        profile=profile,
        enabled_plugins=enabled_plugins,
    )


def run_doctor(
    root: ResolvedRepoRoot,
    *,
    include_all: bool = False,
    registry: Iterable[CheckDefinition] = CHECK_REGISTRY,
) -> DoctorResult:
    """Return one complete, ordered, read-only local snapshot."""

    context = _context(root)
    selected = select_checks(registry, context, include_all=include_all)
    return execute_check_registry(selected, context)
