"""Shared exact-version, project-local BA Tools installer."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKAGE_NAME = "ba-tools"
PACKAGE_VERSION = "0.1.0"
FORMAT_VERSION = 1
LOCK_TIMEOUT_SECONDS = 30.0
POINTER_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
IDENTITY_FILE = ".ba-tools-install.json"
STAGES = (
    "[1/4] Checking prerequisites",
    "[2/4] Preparing the project-local environment",
    "[3/4] Installing locked dependencies",
    "[4/4] Verifying the repo-root launcher",
)
CONSENT_PROMPT = (
    "Download and install locked project dependencies? "
    "This requires network access. [y/N]"
)
CANCELLED = (
    "Installation cancelled before network access. "
    "No launcher or active environment was changed."
)
NONINTERACTIVE_CONSENT = (
    "Network consent is required. Re-run with --yes or provide an offline wheelhouse."
)
WINDOWS_NEXT = r"Next: .\ba-tools.ps1 doctor"
POSIX_NEXT = "Next: ./ba-tools doctor"


class InstallerError(RuntimeError):
    """Safe installer failure with an actionable next step."""

    def __init__(self, message: str, next_action: str = "Correct the error and rerun the installer."):
        super().__init__(message)
        self.next_action = next_action


class InstallerCancelled(InstallerError):
    """Expected default-No cancellation."""


@dataclass(frozen=True)
class InstallerOptions:
    yes: bool
    offline: Path | None


@dataclass(frozen=True)
class PrerequisiteResult:
    python: Path
    git: str


@dataclass(frozen=True)
class GenerationIdentity:
    package_version: str
    lock_digest: str
    python_version: str
    os_name: str
    architecture: str
    format_version: int

    def canonical_text(self) -> str:
        """Return the stable generation input, including the exact package requirement."""

        payload = {
            "architecture": self.architecture,
            "format_version": self.format_version,
            "lock_digest": self.lock_digest,
            "os_name": self.os_name,
            "package": f"{PACKAGE_NAME}=={self.package_version}",
            "python_version": self.python_version,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @property
    def generation_prefix(self) -> str:
        digest = hashlib.sha256(self.canonical_text().encode("utf-8")).hexdigest()[:20]
        version = self.package_version.replace(".", "_")
        python = self.python_version.replace(".", "")
        return f"ba-tools-{version}-py{python}-{digest}"


@dataclass(frozen=True)
class InstallResult:
    generation: str
    changed: bool


def _run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: float = 300.0,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        command,
        capture_output=True,
        check=False,
        env=env,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise InstallerError(
            "A project-local package command failed.",
            "Review the approved lock and wheelhouse, then rerun the installer.",
        )
    return result


def discover_prerequisites() -> PrerequisiteResult:
    """Find compatible host tools without installing or modifying them."""

    if sys.version_info < (3, 14):
        raise InstallerError(
            "Python 3.14 or newer is required.",
            "Install Python from https://www.python.org/downloads/ and "
            "rerun the installer after Python is available.",
        )
    git = shutil.which("git")
    if git is None:
        raise InstallerError(
            "Git is required.",
            "Install Git from https://git-scm.com/downloads and "
            "rerun the installer after Git is available.",
        )
    return PrerequisiteResult(Path(sys.executable).resolve(), git)


def request_network_consent(
    *,
    yes: bool,
    offline: Path | None,
    interactive: bool,
    read_input: Callable[[], str | None],
    write: Callable[[str], None],
) -> bool:
    """Obtain default-No, invocation-scoped consent only when network may be used."""

    if offline is not None or yes:
        return True
    if not interactive:
        raise InstallerError(
            NONINTERACTIVE_CONSENT,
            "Rerun with --yes or provide an approved offline wheelhouse.",
        )

    while True:
        write(CONSENT_PROMPT)
        answer = read_input()
        normalized = "" if answer is None else answer.strip().lower()
        if normalized in {"y", "yes"}:
            return True
        if normalized in {"", "n", "no"}:
            write(CANCELLED)
            return False
        write("Enter y or n.")


def _python_major_minor(python: Path) -> str:
    if python.resolve() == Path(sys.executable).resolve():
        return f"{sys.version_info.major}.{sys.version_info.minor}"
    result = _run(
        [
            str(python),
            "-X",
            "utf8",
            "-c",
            "import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}')",
        ],
        timeout=20,
    )
    return result.stdout.decode("ascii").strip()


def compute_generation_identity(
    python: Path,
    lock_path: Path,
    *,
    package_version: str = PACKAGE_VERSION,
) -> GenerationIdentity:
    """Bind a generation to package, lock, interpreter family, OS, and architecture."""

    return GenerationIdentity(
        package_version=package_version,
        lock_digest=hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        python_version=_python_major_minor(python),
        os_name=platform.system().lower(),
        architecture=platform.machine().lower(),
        format_version=FORMAT_VERSION,
    )


def _runtime_root(repo_root: Path) -> Path:
    return repo_root / ".ba-tools-runtime"


def _interpreter(generation: Path) -> Path:
    if os.name == "nt":
        return generation / "Scripts" / "python.exe"
    return generation / "bin" / "python"


def _identity_path(generation: Path) -> Path:
    return generation / IDENTITY_FILE


def _write_identity(generation: Path, identity: GenerationIdentity) -> None:
    payload = (identity.canonical_text() + "\n").encode("utf-8")
    target = _identity_path(generation)
    target.write_bytes(payload)


def _read_identity(generation: Path) -> str | None:
    try:
        return _identity_path(generation).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def _clean_process_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return env


def _parse_json_document(raw: bytes, surface: str) -> dict[str, Any]:
    if not raw.endswith(b"\n") or raw.startswith(b"\xef\xbb\xbf"):
        raise InstallerError(f"The candidate {surface} did not emit canonical UTF-8 JSON.")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise InstallerError(f"The candidate {surface} did not emit valid UTF-8 JSON.") from error
    if not isinstance(value, dict):
        raise InstallerError(f"The candidate {surface} did not emit a JSON object.")
    return value


def _version_surfaces(
    repo_root: Path,
    generation: Path,
) -> tuple[str, str, str, dict[str, Any]]:
    python = _interpreter(generation)
    env = _clean_process_env()
    probe = _run(
        [
            str(python),
            "-X",
            "utf8",
            "-c",
            (
                "import json,ba_tools,importlib.metadata as m;"
                "print(json.dumps([m.version('ba-tools'),ba_tools.__version__]))"
            ),
        ],
        env=env,
        timeout=30,
    )
    try:
        metadata_version, module_version = json.loads(probe.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise InstallerError("The candidate package version surfaces could not be read.") from error

    version = _run(
        [
            str(python),
            "-X",
            "utf8",
            "-m",
            "ba_tools",
            "--repo-root",
            str(repo_root),
            "--version",
        ],
        env=env,
        timeout=30,
    )
    if version.stderr:
        raise InstallerError("The candidate launcher wrote unexpected version diagnostics.")
    version_payload = _parse_json_document(version.stdout, "version command")
    cli_version = str(version_payload.get("data", {}).get("version", ""))

    help_result = _run(
        [
            str(python),
            "-X",
            "utf8",
            "-m",
            "ba_tools",
            "--repo-root",
            str(repo_root),
            "--help",
        ],
        env=env,
        timeout=30,
    )
    if help_result.stderr:
        raise InstallerError("The candidate launcher wrote unexpected help diagnostics.")
    help_payload = _parse_json_document(help_result.stdout, "help command")
    if help_payload.get("command") != "help":
        raise InstallerError("The candidate help command returned the wrong envelope.")
    return str(metadata_version), str(module_version), cli_version, version_payload


def verify_generation(
    repo_root: Path,
    generation: Path,
    identity: GenerationIdentity,
) -> None:
    """Require the identity marker and all installed version surfaces to agree."""

    if _read_identity(generation) != identity.canonical_text():
        raise InstallerError("The candidate generation does not match the approved lock identity.")
    metadata_version, module_version, cli_version, payload = _version_surfaces(
        repo_root,
        generation,
    )
    if (
        metadata_version != PACKAGE_VERSION
        or module_version != PACKAGE_VERSION
        or cli_version != PACKAGE_VERSION
        or payload.get("data", {}).get("version") != PACKAGE_VERSION
    ):
        raise InstallerError("The candidate does not expose the exact version 0.1.0.")


def _create_environment(python: Path, candidate: Path) -> None:
    _run([str(python), "-X", "utf8", "-m", "venv", str(candidate)], timeout=180)


def build_generation(
    repo_root: Path,
    prerequisites: PrerequisiteResult,
    options: InstallerOptions,
    identity: GenerationIdentity,
) -> Path:
    """Build and verify a unique generation without changing active state."""

    runtime = _runtime_root(repo_root)
    envs = runtime / "envs"
    envs.mkdir(parents=True, exist_ok=True)
    candidate = envs / f"{identity.generation_prefix}-{uuid.uuid4().hex[:12]}"
    candidate.mkdir()
    try:
        _create_environment(prerequisites.python, candidate)
        candidate_python = _interpreter(candidate)
        lock_path = repo_root / "packages" / "ba-tools" / "requirements.lock"
        package_root = repo_root / "packages" / "ba-tools"
        dependency_command = [
            str(candidate_python),
            "-X",
            "utf8",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--require-hashes",
            "--only-binary=:all:",
        ]
        if options.offline is not None:
            dependency_command.extend(
                ["--no-index", "--find-links", str(options.offline.resolve())]
            )
        dependency_command.extend(["-r", str(lock_path)])
        _run(dependency_command, env=_clean_process_env(), timeout=600)
        _run(
            [
                str(candidate_python),
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "--no-deps",
                "--no-build-isolation",
                str(package_root),
            ],
            env=_clean_process_env(),
            timeout=300,
        )
        _write_identity(candidate, identity)
        verify_generation(repo_root, candidate, identity)
        return candidate
    except BaseException:
        shutil.rmtree(candidate, ignore_errors=True)
        raise


def _current_generation(repo_root: Path) -> str | None:
    pointer = _runtime_root(repo_root) / "current-env.txt"
    try:
        lines = pointer.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    if len(lines) != 1 or POINTER_COMPONENT.fullmatch(lines[0]) is None:
        return None
    if lines[0] in {".", ".."}:
        return None
    return lines[0]


def _atomic_write_if_changed(target: Path, payload: bytes, *, executable: bool = False) -> bool:
    try:
        if target.read_bytes() == payload:
            if executable and os.name != "nt":
                target.chmod(target.stat().st_mode | 0o111)
            return False
    except OSError:
        pass
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".{target.name}.tmp-{uuid.uuid4().hex}"
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if executable and os.name != "nt":
            temporary.chmod(0o755)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def publish_launchers(repo_root: Path) -> bool:
    """Publish stable root launchers without touching identical generations."""

    templates = repo_root / "installer" / "launcher-templates"
    changed_windows = _atomic_write_if_changed(
        repo_root / "ba-tools.ps1",
        (templates / "ba-tools.ps1").read_bytes(),
    )
    changed_posix = _atomic_write_if_changed(
        repo_root / "ba-tools",
        (templates / "ba-tools").read_bytes(),
        executable=True,
    )
    return changed_windows or changed_posix


@contextmanager
def _install_lock(runtime: Path) -> Iterator[None]:
    runtime.mkdir(parents=True, exist_ok=True)
    lock_path = runtime / "install.lock"
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise InstallerError(
                    "Another installer did not finish in time.",
                    "Retry after the other installer completes.",
                ) from None
            time.sleep(0.05)
    try:
        os.write(descriptor, f"{os.getpid()}\n".encode("ascii"))
        os.close(descriptor)
        descriptor = None
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def switch_active_generation(repo_root: Path, generation_name: str) -> None:
    if POINTER_COMPONENT.fullmatch(generation_name) is None or generation_name in {".", ".."}:
        raise InstallerError("The candidate generation name is not allowed.")
    pointer = _runtime_root(repo_root) / "current-env.txt"
    _atomic_write_if_changed(pointer, f"{generation_name}\n".encode("utf-8"))


def _publish_verified_candidate(
    repo_root: Path,
    candidate: Path,
    identity: GenerationIdentity,
) -> str:
    """Reverify under the activation lock, then publish one contained component."""

    verify_generation(repo_root, candidate, identity)
    runtime = _runtime_root(repo_root)
    envs = runtime / "envs"
    envs.mkdir(parents=True, exist_ok=True)
    with _install_lock(runtime):
        verify_generation(repo_root, candidate, identity)
        destination = envs / candidate.name
        if candidate.resolve() != destination.resolve():
            if destination.exists():
                raise InstallerError("The candidate generation name is already in use.")
            os.replace(candidate, destination)
        verify_generation(repo_root, destination, identity)
        switch_active_generation(repo_root, destination.name)
        publish_launchers(repo_root)
        return destination.name


def _verified_current(
    repo_root: Path,
    identity: GenerationIdentity,
) -> str | None:
    generation_name = _current_generation(repo_root)
    if generation_name is None:
        return None
    generation = _runtime_root(repo_root) / "envs" / generation_name
    try:
        verify_generation(repo_root, generation, identity)
    except InstallerError:
        return None
    return generation_name


def install(
    repo_root: Path,
    prerequisites: PrerequisiteResult,
    options: InstallerOptions,
    *,
    interactive: bool,
    read_input: Callable[[], str | None] | None = None,
    write: Callable[[str], None] = print,
) -> InstallResult:
    """Synchronize to one verified exact-version generation."""

    repo_root = repo_root.resolve()
    lock_path = repo_root / "packages" / "ba-tools" / "requirements.lock"
    write(STAGES[0])
    if not lock_path.is_file():
        raise InstallerError("The approved dependency lock is missing.")
    if options.offline is not None and not options.offline.resolve().is_dir():
        raise InstallerError(
            "The approved offline wheelhouse is not available.",
            "Provide an existing approved wheelhouse and rerun the installer.",
        )
    identity = compute_generation_identity(prerequisites.python, lock_path)

    current = _verified_current(repo_root, identity)
    if current is not None:
        write("[SKIP] Preparing the project-local environment: exact generation is active")
        write("[SKIP] Installing locked dependencies: approved generation is already verified")
        write(STAGES[3])
        launchers_changed = publish_launchers(repo_root)
        write("BA Tools is ready.")
        write(WINDOWS_NEXT if os.name == "nt" else POSIX_NEXT)
        return InstallResult(current, launchers_changed)

    reader = read_input
    if reader is None:
        def read_stdin() -> str:
            return sys.stdin.readline()

        reader = read_stdin
    consented = request_network_consent(
        yes=options.yes,
        offline=options.offline,
        interactive=interactive,
        read_input=reader,
        write=write,
    )
    if not consented:
        raise InstallerCancelled(CANCELLED)

    write(STAGES[1])
    write(STAGES[2])
    candidate = build_generation(repo_root, prerequisites, options, identity)
    write(STAGES[3])
    active = _publish_verified_candidate(repo_root, candidate, identity)
    write("BA Tools is ready.")
    write(WINDOWS_NEXT if os.name == "nt" else POSIX_NEXT)
    return InstallResult(active, True)


def _parse_options(arguments: list[str] | None) -> InstallerOptions:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--offline", type=Path)
    parsed = parser.parse_args(arguments)
    return InstallerOptions(yes=parsed.yes, offline=parsed.offline)


def main(arguments: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        options = _parse_options(arguments)
        prerequisites = discover_prerequisites()
        install(
            repo_root,
            prerequisites,
            options,
            interactive=(
                sys.stdin.isatty()
                and os.environ.get("BA_TOOLS_NONINTERACTIVE") != "1"
            ),
        )
        return 0
    except InstallerCancelled:
        return 1
    except InstallerError as error:
        print(f"[FAIL] Installer: {error}", file=sys.stderr)
        print(f"    Next: {error.next_action}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("[FAIL] Installer: Installation was interrupted.", file=sys.stderr)
        print("    Next: Rerun the installer when ready.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
