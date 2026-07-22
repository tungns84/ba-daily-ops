"""Project-local installer and transparent launcher contracts."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BOOTSTRAP_PATH = PROJECT_ROOT / "installer" / "bootstrap.py"
PACKAGE_ROOT = PROJECT_ROOT / "packages" / "ba-tools"
LOCK_PATH = PACKAGE_ROOT / "requirements.lock"
POWERSHELL_INSTALLER = PROJECT_ROOT / "install.ps1"
POSIX_INSTALLER = PROJECT_ROOT / "install.sh"
WINDOWS_LAUNCHER = PROJECT_ROOT / "installer" / "launcher-templates" / "ba-tools.ps1"
POSIX_LAUNCHER = PROJECT_ROOT / "installer" / "launcher-templates" / "ba-tools"
VERSION = "0.1.0"


def load_bootstrap():
    """Load the installer without making it part of the runtime package."""

    spec = importlib.util.spec_from_file_location("ba_tools_installer", BOOTSTRAP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_document(raw: bytes) -> dict[str, object]:
    assert raw.endswith(b"\n")
    assert not raw.startswith(b"\xef\xbb\xbf")
    return json.loads(raw)


def test_installer_surfaces_and_repository_boundaries_exist() -> None:
    for path in (
        POWERSHELL_INSTALLER,
        POSIX_INSTALLER,
        BOOTSTRAP_PATH,
        WINDOWS_LAUNCHER,
        POSIX_LAUNCHER,
    ):
        assert path.is_file(), path

    ignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    attributes = (PROJECT_ROOT / ".gitattributes").read_text(encoding="utf-8")
    for pattern in (
        "/ba-tools",
        "/ba-tools.ps1",
        "/.ba-tools-runtime/",
        "/.ba-ops/quarantine/",
    ):
        assert pattern in ignore
    assert "*.py text eol=lf" in attributes
    assert "*.sh text eol=lf" in attributes
    assert "*.json text eol=lf" in attributes
    assert "installer/launcher-templates/ba-tools text eol=lf" in attributes


def test_generation_identity_includes_exact_tool_version(dev_python: Path) -> None:
    bootstrap = load_bootstrap()
    from ba_tools import __version__

    pyproject = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    identity = bootstrap.compute_generation_identity(dev_python, LOCK_PATH)
    changed = bootstrap.compute_generation_identity(
        dev_python,
        LOCK_PATH,
        package_version="0.1.1",
    )

    assert pyproject["project"]["version"] == __version__ == identity.package_version == VERSION
    assert identity.lock_digest == hashlib.sha256(LOCK_PATH.read_bytes()).hexdigest()
    assert identity.python_version == f"{sys.version_info.major}.{sys.version_info.minor}"
    assert identity.os_name
    assert identity.architecture
    assert identity.format_version == 1
    assert identity != changed
    assert "ba-tools==0.1.0" in identity.canonical_text()
    assert identity.generation_prefix != changed.generation_prefix


@pytest.mark.parametrize("answer", ["", "n", "NO", None])
def test_network_consent_is_default_no(answer: str | None) -> None:
    bootstrap = load_bootstrap()
    responses = iter(()) if answer is None else iter((answer,))
    output: list[str] = []

    assert not bootstrap.request_network_consent(
        yes=False,
        offline=None,
        interactive=True,
        read_input=lambda: next(responses, None),
        write=output.append,
    )
    assert output[0] == (
        "Download and install locked project dependencies? "
        "This requires network access. [y/N]"
    )
    assert output[-1] == (
        "Installation cancelled before network access. "
        "No launcher or active environment was changed."
    )


def test_network_consent_reprompts_and_is_invocation_scoped() -> None:
    bootstrap = load_bootstrap()
    responses = iter(("maybe", "YES"))
    output: list[str] = []

    assert bootstrap.request_network_consent(
        yes=False,
        offline=None,
        interactive=True,
        read_input=lambda: next(responses),
        write=output.append,
    )
    assert "Enter y or n." in output
    assert not hasattr(bootstrap.InstallerOptions, "persist_consent")


def test_noninteractive_requires_yes_or_offline() -> None:
    bootstrap = load_bootstrap()
    with pytest.raises(bootstrap.InstallerError, match="Network consent is required"):
        bootstrap.request_network_consent(
            yes=False,
            offline=None,
            interactive=False,
            read_input=lambda: pytest.fail("noninteractive install read stdin"),
            write=lambda _line: None,
        )


def test_approved_offline_install_never_prompts_or_uses_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dev_python: Path,
) -> None:
    bootstrap = load_bootstrap()
    wheelhouse = tmp_path / "approved wheelhouse"
    wheelhouse.mkdir()
    observed: list[list[str]] = []

    monkeypatch.setattr(bootstrap, "_create_environment", lambda *_args: None)

    def record(command: list[str], **_kwargs):
        observed.append([str(item) for item in command])
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(bootstrap, "_run", record)
    monkeypatch.setattr(
        bootstrap,
        "_version_surfaces",
        lambda *_args: (VERSION, VERSION, VERSION, {"data": {"version": VERSION}}),
    )
    monkeypatch.setattr(bootstrap, "_verified_current", lambda *_args: None)
    monkeypatch.setattr(bootstrap, "_publish_verified_candidate", lambda *_args: "candidate")

    options = bootstrap.InstallerOptions(yes=False, offline=wheelhouse)
    result = bootstrap.install(
        PROJECT_ROOT,
        bootstrap.PrerequisiteResult(dev_python, "git"),
        options,
        interactive=False,
        read_input=lambda: pytest.fail("offline install prompted"),
        write=lambda _line: None,
    )

    assert result.generation == "candidate"
    flattened = [item for command in observed for item in command]
    assert "--no-index" in flattened
    assert "--find-links" in flattened
    assert str(wheelhouse.resolve()) in flattened
    assert not any("http://" in item or "https://" in item for item in flattened)


def test_candidate_rejects_version_surface_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap = load_bootstrap()
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    identity = bootstrap.compute_generation_identity(Path(sys.executable), LOCK_PATH)
    bootstrap._write_identity(candidate, identity)
    monkeypatch.setattr(
        bootstrap,
        "_version_surfaces",
        lambda *_args: (VERSION, "0.1.1", VERSION, {"data": {"version": VERSION}}),
    )

    with pytest.raises(bootstrap.InstallerError, match="exact version"):
        bootstrap.verify_generation(PROJECT_ROOT, candidate, identity)


def test_installer_ui_has_exact_four_stages_and_success_copy() -> None:
    source = BOOTSTRAP_PATH.read_text(encoding="utf-8")
    for stage in (
        "[1/4] Checking prerequisites",
        "[2/4] Preparing the project-local environment",
        "[3/4] Installing locked dependencies",
        "[4/4] Verifying the repo-root launcher",
        "BA Tools is ready.",
        r"Next: .\ba-tools.ps1 doctor",
        "Next: ./ba-tools doctor",
    ):
        assert stage in source


def test_installer_sources_forbid_global_or_policy_mutation() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (POWERSHELL_INSTALLER, POSIX_INSTALLER, BOOTSTRAP_PATH)
    )
    for forbidden in (
        "setx ",
        "pip install --user",
        "set-executionpolicy",
        "$profile",
        "/etc/profile",
        ".bashrc",
    ):
        assert forbidden not in source


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows PowerShell")
def test_windows_powershell_51_install_path() -> None:
    observation = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "$PSVersionTable.PSEdition + '|' + $PSVersionTable.PSVersion.ToString()",
        ],
        capture_output=True,
        check=True,
        timeout=20,
    )
    edition, version = observation.stdout.decode("ascii").strip().split("|", 1)
    assert edition == "Desktop"
    assert tuple(map(int, version.split(".")[:2])) >= (5, 1)

    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-File", str(POWERSHELL_INSTALLER), "--yes"],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        timeout=30,
    )
    combined = (result.stdout + result.stderr).decode("utf-8")
    assert result.returncode == 0
    assert "BA Tools is ready." in combined
    assert "[FAIL]" not in combined
    assert "pwsh" not in POWERSHELL_INSTALLER.read_text(encoding="utf-8").lower()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="PowerShell 7 is optional")
def test_powershell7_remains_compatible() -> None:
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(POWERSHELL_INSTALLER), "--yes"],
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        timeout=30,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0
    assert b"BA Tools is ready." in combined
    assert b"[FAIL]" not in combined


def test_posix_wrapper_is_quoted_posix_sh() -> None:
    source = POSIX_INSTALLER.read_text(encoding="utf-8")
    assert source.startswith("#!/bin/sh\n")
    assert "$BASH_SOURCE" not in source
    assert "eval " not in source
    shell = shutil.which("sh")
    if shell is not None:
        subprocess.run([shell, "-n", str(POSIX_INSTALLER)], check=True, timeout=10)


def test_launchers_forward_argv_streams_and_code(
    tmp_path: Path,
    dev_python: Path,
) -> None:
    bootstrap = load_bootstrap()
    repo = tmp_path / "Dự án launcher có khoảng trắng"
    repo.mkdir()
    shutil.copytree(PROJECT_ROOT / "installer", repo / "installer")
    runtime = repo / ".ba-tools-runtime"
    generation = runtime / "envs" / "gen-test"
    scripts = generation / ("Scripts" if sys.platform == "win32" else "bin")
    scripts.mkdir(parents=True)
    interpreter = scripts / ("python.exe" if sys.platform == "win32" else "python")
    shutil.copy2(dev_python, interpreter)
    source_cfg = dev_python.parents[1] / "pyvenv.cfg"
    if source_cfg.exists():
        shutil.copy2(source_cfg, generation / "pyvenv.cfg")
    (runtime / "current-env.txt").write_text("gen-test\n", encoding="utf-8", newline="\n")
    bootstrap.publish_launchers(repo)

    launcher = repo / ("ba-tools.ps1" if sys.platform == "win32" else "ba-tools")
    arguments = ["--version"]
    command = (
        ["powershell.exe", "-NoProfile", "-File", str(launcher), *arguments]
        if sys.platform == "win32"
        else [str(launcher), *arguments]
    )
    dev_site_packages = next(
        path for path in map(Path, sys.path) if path.name == "site-packages"
    )
    result = subprocess.run(
        command,
        cwd=tmp_path,
        capture_output=True,
        check=False,
        timeout=30,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                (str(PACKAGE_ROOT / "src"), str(dev_site_packages))
            ),
        },
    )
    assert result.returncode == 0
    assert result.stderr == b""
    payload = parse_document(result.stdout)
    assert payload["data"] == {"version": VERSION}

    failure_command = command[:-1] + ["--not-a-real-option", "mục tiêu"]
    failure = subprocess.run(
        failure_command,
        cwd=tmp_path,
        capture_output=True,
        check=False,
        timeout=30,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                (str(PACKAGE_ROOT / "src"), str(dev_site_packages))
            ),
        },
    )
    assert failure.returncode == 2
    assert failure.stdout == b""
    assert parse_document(failure.stderr)["error"]["code"] == "CLI_USAGE_ERROR"


def test_malicious_pointer_is_rejected(tmp_path: Path) -> None:
    bootstrap = load_bootstrap()
    repo = tmp_path / "repo"
    shutil.copytree(PROJECT_ROOT / "installer", repo / "installer")
    runtime = repo / ".ba-tools-runtime"
    runtime.mkdir(parents=True)
    (runtime / "current-env.txt").write_text("../outside\n", encoding="utf-8")
    bootstrap.publish_launchers(repo)
    launcher = repo / ("ba-tools.ps1" if sys.platform == "win32" else "ba-tools")
    command = (
        ["powershell.exe", "-NoProfile", "-File", str(launcher), "--version"]
        if sys.platform == "win32"
        else [str(launcher), "--version"]
    )
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, check=False, timeout=20)

    assert result.returncode == 2
    assert result.stdout == b""
    payload = parse_document(result.stderr)
    assert payload["error"]["code"] == "LAUNCHER_NOT_READY"
    assert str(tmp_path).encode() not in result.stderr


def test_installer_rerun_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dev_python: Path,
) -> None:
    bootstrap = load_bootstrap()
    repo = tmp_path / "repo"
    shutil.copytree(PROJECT_ROOT / "installer", repo / "installer")
    shutil.copytree(PACKAGE_ROOT, repo / "packages" / "ba-tools")
    runtime = repo / ".ba-tools-runtime"
    generation = runtime / "envs" / "verified-generation"
    generation.mkdir(parents=True)
    identity = bootstrap.compute_generation_identity(
        dev_python,
        repo / "packages/ba-tools/requirements.lock",
    )
    bootstrap._write_identity(generation, identity)
    runtime.mkdir(exist_ok=True)
    (runtime / "current-env.txt").write_text(
        "verified-generation\n",
        encoding="utf-8",
        newline="\n",
    )
    bootstrap.publish_launchers(repo)
    tracked = [runtime / "current-env.txt", repo / "ba-tools", repo / "ba-tools.ps1"]
    before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in tracked]
    monkeypatch.setattr(bootstrap, "verify_generation", lambda *_args: None)
    monkeypatch.setattr(
        bootstrap,
        "build_generation",
        lambda *_args, **_kwargs: pytest.fail("verified rerun rebuilt generation"),
    )

    result = bootstrap.install(
        repo,
        bootstrap.PrerequisiteResult(dev_python, "git"),
        bootstrap.InstallerOptions(yes=True, offline=None),
        interactive=False,
        write=lambda _line: None,
    )

    assert result.changed is False
    assert before == [(path.read_bytes(), path.stat().st_mtime_ns) for path in tracked]


def test_missing_python_or_git_fails_before_packages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap = load_bootstrap()
    calls: list[list[str]] = []
    monkeypatch.setattr(bootstrap, "_run", lambda command, **_kwargs: calls.append(command))
    monkeypatch.setattr(bootstrap.shutil, "which", lambda _name: None)
    monkeypatch.setattr(bootstrap.sys, "version_info", (3, 13))

    with pytest.raises(bootstrap.InstallerError, match="Python 3.14 or newer is required"):
        bootstrap.discover_prerequisites()
    assert calls == []


def test_stale_install_lock_is_recovered(tmp_path: Path) -> None:
    bootstrap = load_bootstrap()
    runtime = tmp_path / ".ba-tools-runtime"
    runtime.mkdir(parents=True)
    lock_path = runtime / "install.lock"
    lock_path.write_text("424242\n", encoding="ascii")

    assert bootstrap._is_stale_install_lock(lock_path)
    with bootstrap._install_lock(runtime):
        assert lock_path.exists()
    assert not lock_path.exists()


def test_windows_installer_requires_python_314_for_py_launcher() -> None:
    source = POWERSHELL_INSTALLER.read_text(encoding="utf-8")
    assert "sys.version_info >= (3, 14)" in source
    assert "sys.version_info >= (3, 11)" not in source


def test_posix_launcher_resolves_generation_under_envs_root(tmp_path: Path) -> None:
    source = POSIX_LAUNCHER.read_text(encoding="utf-8")
    assert "envs_root=$(CDPATH= cd" in source
    assert "generation_root=$(CDPATH= cd" in source
    assert 'case "$generation_root" in' in source

    repo = tmp_path / "repo"
    runtime = repo / ".ba-tools-runtime"
    envs = runtime / "envs"
    outside = tmp_path / "outside"
    outside.mkdir()
    envs.mkdir(parents=True)
    redirect = envs / "escape"
    try:
        redirect.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        if os.name != "nt":
            pytest.skip(f"symbolic-link capability unavailable: {error}")
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(redirect), str(outside)],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            pytest.skip("junction creation unavailable")

    (runtime / "current-env.txt").write_text("escape\n", encoding="utf-8", newline="\n")
    shutil.copytree(PROJECT_ROOT / "installer", repo / "installer")
    load_bootstrap().publish_launchers(repo)
    launcher = repo / "ba-tools"
    shell = shutil.which("sh")
    if shell is None:
        pytest.skip("POSIX shell is unavailable")
    result = subprocess.run(
        [shell, str(launcher), "--version"],
        cwd=tmp_path,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 2
    assert result.stdout == b""
    payload = parse_document(result.stderr)
    assert payload["error"]["code"] == "LAUNCHER_NOT_READY"


def test_concurrent_activation_never_publishes_unverified_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap = load_bootstrap()
    repo = tmp_path / "repo"
    shutil.copytree(PROJECT_ROOT / "installer", repo / "installer")
    candidates = [
        tmp_path / "candidate-a",
        tmp_path / "candidate-b",
        tmp_path / "candidate-c",
    ]
    for candidate in candidates:
        candidate.mkdir()
    identity = bootstrap.compute_generation_identity(Path(sys.executable), LOCK_PATH)
    verified_names = {candidates[1].name, candidates[2].name}
    monkeypatch.setattr(
        bootstrap,
        "verify_generation",
        lambda _repo, candidate, _identity: (
            None
            if candidate.name in verified_names
            else (_ for _ in ()).throw(bootstrap.InstallerError("candidate not verified"))
        ),
    )

    with pytest.raises(bootstrap.InstallerError, match="candidate not verified"):
        bootstrap._publish_verified_candidate(repo, candidates[0], identity)
    assert not (repo / ".ba-tools-runtime/current-env.txt").exists()

    with ThreadPoolExecutor(max_workers=2) as pool:
        active_names = set(
            pool.map(
                lambda candidate: bootstrap._publish_verified_candidate(
                    repo,
                    candidate,
                    identity,
                ),
                candidates[1:],
            )
        )
    pointer = (repo / ".ba-tools-runtime/current-env.txt").read_text(encoding="utf-8").strip()
    assert active_names == verified_names
    assert pointer in verified_names
    assert all((repo / ".ba-tools-runtime/envs" / name).is_dir() for name in verified_names)
