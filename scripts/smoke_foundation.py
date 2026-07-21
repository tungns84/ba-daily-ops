"""Reusable offline installer-to-launcher foundation smoke."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EXPECTED_VERSION = "0.1.0"
UNICODE_REPO_NAME = "Dự án nền tảng có khoảng trắng"
STATE_FILES = (
    ".ba-ops/config.json",
    ".ba-ops/coverage-policy.json",
    ".ba-ops/business-goals.json",
)


@dataclass(frozen=True, slots=True)
class SmokeOptions:
    repo_source: Path
    work_dir: Path
    wheelhouse: Path
    expected_platform: str
    evidence_out: Path


@dataclass(frozen=True, slots=True)
class CommandEvidence:
    command_id: str
    exit_code: int
    stdout_kind: str
    stderr_kind: str


@dataclass(frozen=True, slots=True)
class HostEvidence:
    os_version: str
    architecture: str
    python_version: str
    powershell_edition: str | None
    powershell_version: str | None


def run_command_bytes(
    arguments: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float = 120.0,
) -> subprocess.CompletedProcess[bytes]:
    """Run one fixed argument vector without a shell and retain exact bytes."""

    return subprocess.run(
        arguments,
        cwd=cwd,
        env=env,
        shell=False,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def assert_single_json(raw: bytes) -> dict[str, Any]:
    """Require one canonical UTF-8 JSON object and return it."""

    if raw.startswith(b"\xef\xbb\xbf") or not raw.endswith(b"\n"):
        raise AssertionError("JSON output must be UTF-8 without BOM and end in one LF")
    if raw.count(b"\n") != 1:
        raise AssertionError("JSON output must contain exactly one physical line")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise AssertionError("output is not valid UTF-8 JSON") from error
    if not isinstance(payload, dict):
        raise AssertionError("JSON output must be an object")
    canonical = (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    if raw != canonical:
        raise AssertionError("JSON output is not canonical")
    return payload


def _platform_name() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    return sys.platform


def _powershell_host() -> tuple[str | None, str | None]:
    if os.name != "nt":
        return None, None
    observation = run_command_bytes(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "$PSVersionTable.PSEdition + '|' + $PSVersionTable.PSVersion.ToString()",
        ],
        cwd=Path.cwd(),
        timeout=30,
    )
    if observation.returncode != 0 or observation.stderr:
        raise AssertionError("Windows PowerShell host could not be inspected")
    edition, version = observation.stdout.decode("ascii").strip().split("|", maxsplit=1)
    components = tuple(int(item) for item in version.split(".")[:2])
    if edition != "Desktop" or components < (5, 1):
        raise AssertionError("Windows smoke requires powershell.exe Desktop 5.1 or newer")
    return edition, version


def collect_host_evidence() -> HostEvidence:
    """Collect redacted host facts without machine-specific paths."""

    powershell_edition, powershell_version = _powershell_host()
    if sys.platform == "win32":
        version = sys.getwindowsversion()
        os_version = f"{version.major}.{version.minor}.{version.build}"
    elif hasattr(os, "uname"):
        os_version = os.uname().release
    else:
        os_version = platform.release()
    return HostEvidence(
        os_version=os_version,
        architecture=platform.machine().lower(),
        python_version=".".join(map(str, sys.version_info[:3])),
        powershell_edition=powershell_edition,
        powershell_version=powershell_version,
    )


def _source_ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = {
        ".git",
        ".ba-ops",
        ".ba-tools-runtime",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
    }
    return ignored.intersection(names)


def _copy_repository(source: Path, work_dir: Path) -> Path:
    destination = work_dir / UNICODE_REPO_NAME
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=_source_ignore)
    (destination / ".git").mkdir()
    return destination


def _network_guard(work_dir: Path) -> Path:
    guard = work_dir / "network-guard"
    if guard.exists():
        shutil.rmtree(guard)
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        """
import os
import sys

def _deny_network(event, _args):
    if event.startswith("socket."):
        os._exit(97)

sys.addaudithook(_deny_network)
""".lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    return guard


def _stream_kind(raw: bytes) -> str:
    if not raw:
        return "empty"
    try:
        payload = assert_single_json(raw)
    except AssertionError:
        return "prose"
    return "json-success" if payload.get("ok") is True else "json-error"


def _record(command_id: str, result: subprocess.CompletedProcess[bytes]) -> CommandEvidence:
    return CommandEvidence(
        command_id=command_id,
        exit_code=result.returncode,
        stdout_kind=_stream_kind(result.stdout),
        stderr_kind=_stream_kind(result.stderr),
    )


def _assert_result(
    result: subprocess.CompletedProcess[bytes],
    *,
    command: str,
    exit_code: int,
    error_code: str | None = None,
) -> dict[str, Any]:
    if result.returncode != exit_code:
        raise AssertionError(f"{command} returned {result.returncode}, expected {exit_code}")
    selected = result.stdout if exit_code == 0 else result.stderr
    opposite = result.stderr if exit_code == 0 else result.stdout
    if opposite:
        raise AssertionError(f"{command} wrote to both streams")
    payload = assert_single_json(selected)
    if payload.get("command") != command:
        raise AssertionError(f"{command} returned the wrong command identity")
    if error_code is not None and payload.get("error", {}).get("code") != error_code:
        raise AssertionError(f"{command} returned the wrong error code")
    return payload


def _git_commit(source: Path) -> str:
    result = run_command_bytes(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        cwd=source,
        timeout=30,
    )
    if result.returncode != 0 or result.stderr:
        raise AssertionError("source commit identity is unavailable")
    commit = result.stdout.decode("ascii").strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise AssertionError("source commit identity is not a full SHA")
    return commit


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _installer_command(repo: Path, wheelhouse: Path) -> list[str]:
    if os.name == "nt":
        return [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(repo / "install.ps1"),
            "--offline",
            str(wheelhouse),
        ]
    return ["/bin/sh", str(repo / "install.sh"), "--offline", str(wheelhouse)]


def _launcher_command(repo: Path, *arguments: str) -> list[str]:
    if os.name == "nt":
        return [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(repo / "ba-tools.ps1"),
            *arguments,
        ]
    return [str(repo / "ba-tools"), *arguments]


def run_foundation_smoke(options: SmokeOptions) -> dict[str, Any]:
    """Run the complete offline install and generated-launcher foundation journey."""

    source = options.repo_source.resolve()
    wheelhouse = options.wheelhouse.resolve()
    work_dir = options.work_dir.resolve()
    if _platform_name() != options.expected_platform:
        raise AssertionError(
            f"expected platform {options.expected_platform}, observed {_platform_name()}"
        )
    if not wheelhouse.is_dir() or not any(wheelhouse.glob("*.whl")):
        raise AssertionError("approved wheelhouse is missing or empty")
    work_dir.mkdir(parents=True, exist_ok=True)
    repo = _copy_repository(source, work_dir)
    guard = _network_guard(work_dir)
    host = collect_host_evidence()
    evidence: list[CommandEvidence] = []

    installer = run_command_bytes(
        _installer_command(repo, wheelhouse),
        cwd=repo,
        env={**os.environ, "NO_COLOR": "1"},
        timeout=900,
    )
    evidence.append(_record("installer.offline", installer))
    if installer.returncode != 0 or installer.stderr:
        raise AssertionError("offline installer failed")
    installer_text = installer.stdout.decode("utf-8")
    expected_stages = [
        "[1/4] Checking prerequisites",
        "[2/4] Preparing the project-local environment",
        "[3/4] Installing locked dependencies",
        "[4/4] Verifying the repo-root launcher",
    ]
    positions = [installer_text.index(stage) for stage in expected_stages]
    if positions != sorted(positions):
        raise AssertionError("installer stages were not emitted in order")
    if "BA Tools is ready." not in installer_text:
        raise AssertionError("installer did not report readiness")

    command_env = {
        **os.environ,
        "NO_COLOR": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": str(guard),
    }

    def launch(
        command_id: str,
        *arguments: str,
        command: str,
        exit_code: int = 0,
        error_code: str | None = None,
    ) -> dict[str, Any]:
        result = run_command_bytes(
            _launcher_command(repo, *arguments),
            cwd=work_dir,
            env=command_env,
            timeout=120,
        )
        evidence.append(_record(command_id, result))
        if result.returncode == 97:
            raise AssertionError(f"{command_id} attempted network access")
        return _assert_result(
            result,
            command=command,
            exit_code=exit_code,
            error_code=error_code,
        )

    launch("launcher.no_args", command="help")
    launch("launcher.help", "--help", command="help")
    version = launch("launcher.version", "--version", command="version")
    if version.get("data") != {"version": EXPECTED_VERSION}:
        raise AssertionError("launcher did not expose exact version 0.1.0")

    pre_default = launch("launcher.doctor.pre", "doctor", command="doctor")
    pre_all = launch("launcher.doctor_all.pre", "doctor", "--all", command="doctor")
    if len(pre_default["data"]["checks"]) != 9 or len(pre_all["data"]["checks"]) != 12:
        raise AssertionError("pre-init doctor snapshots are incomplete")

    fresh = launch("launcher.init.fresh", "init", command="init")
    if fresh["data"] != {"changed": True, "created": list(STATE_FILES)}:
        raise AssertionError("fresh init returned unexpected state")
    no_op = launch("launcher.init.noop", "init", command="init")
    if no_op["data"] != {"changed": False, "created": []}:
        raise AssertionError("no-op init returned unexpected state")

    missing = repo / "packages" / "ba-tools" / "requirements.lock"
    if _sha256(missing) != _sha256(source / "packages" / "ba-tools" / "requirements.lock"):
        raise AssertionError("copied dependency lock changed")
    (repo / STATE_FILES[1]).unlink()
    partial = launch(
        "launcher.init.partial",
        "init",
        command="init",
        exit_code=2,
        error_code="STATE_INCOMPLETE",
    )
    if partial["error"]["remediation"] != [
        "Run init --repair to create missing files only."
    ]:
        raise AssertionError("partial init guidance changed")
    repair = launch("launcher.init.repair", "init", "--repair", command="init")
    if repair["data"] != {"changed": True, "created": [STATE_FILES[1]]}:
        raise AssertionError("repair did not create only the missing file")

    post_default = launch("launcher.doctor.post", "doctor", command="doctor")
    post_all = launch("launcher.doctor_all.post", "doctor", "--all", command="doctor")
    if len(post_default["data"]["checks"]) != 15 or len(post_all["data"]["checks"]) != 18:
        raise AssertionError("post-init doctor snapshots are incomplete")

    payload = {
        "schema_version": 1,
        "platform": options.expected_platform,
        "host": asdict(host),
        "source": {
            "commit": _git_commit(source),
            "runtime_lock_sha256": _sha256(
                source / "packages" / "ba-tools" / "requirements.lock"
            ),
            "development_lock_sha256": _sha256(
                source / "packages" / "ba-tools" / "requirements-dev.lock"
            ),
        },
        "network": {
            "installer": "offline-wheelhouse",
            "product": "process-audit-deny",
        },
        "commands": [asdict(item) for item in evidence],
        "result": "pass",
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    forbidden = (str(source), str(Path.home()), str(repo), str(sys.executable))
    if any(value and value in serialized for value in forbidden):
        raise AssertionError("evidence contains an absolute repository, home, or interpreter path")
    return payload


def write_evidence(path: Path, payload: dict[str, Any]) -> None:
    """Write canonical redacted evidence with one trailing LF."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        (
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    )


def _parse_options(arguments: list[str] | None = None) -> SmokeOptions:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-source", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument(
        "--expected-platform",
        choices=("windows", "macos", "linux"),
        required=True,
    )
    parser.add_argument("--evidence-out", type=Path, required=True)
    parsed = parser.parse_args(arguments)
    return SmokeOptions(
        repo_source=parsed.repo_source,
        work_dir=parsed.work_dir,
        wheelhouse=parsed.wheelhouse,
        expected_platform=parsed.expected_platform,
        evidence_out=parsed.evidence_out,
    )


def main(arguments: list[str] | None = None) -> int:
    options = _parse_options(arguments)
    payload = run_foundation_smoke(options)
    write_evidence(options.evidence_out, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
