"""Shared process, repository, fault, and network fixtures."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def pytest_sessionstart() -> None:
    """Keep explicit source paths stable when subprocesses change cwd."""

    pythonpath = os.environ.get("PYTHONPATH")
    if pythonpath is None:
        return

    entries = (
        path if path.is_absolute() else (PROJECT_ROOT / path).resolve()
        for value in pythonpath.split(os.pathsep)
        if value
        for path in (Path(value),)
    )
    os.environ["PYTHONPATH"] = os.pathsep.join(map(str, entries))


@pytest.fixture
def dev_python() -> Path:
    """Return and enforce the locked development interpreter."""

    relative = (
        Path(".ba-tools-runtime/dev/Scripts/python.exe")
        if sys.platform == "win32"
        else Path(".ba-tools-runtime/dev/bin/python")
    )
    expected = (PROJECT_ROOT / relative).resolve()
    assert Path(sys.executable).resolve() == expected
    return expected


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create an otherwise empty repository root."""

    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


@pytest.fixture
def unicode_repo_with_spaces(tmp_path: Path) -> Path:
    """Create a repository whose path exercises Vietnamese UTF-8 and spaces."""

    repo = tmp_path / "Dự án Tiếng Việt — có khoảng trắng"
    repo.mkdir()
    return repo


@pytest.fixture
def run_cli_bytes(
    dev_python: Path,
) -> Callable[..., subprocess.CompletedProcess[bytes]]:
    """Run the installed CLI as a real UTF-8 subprocess and retain raw bytes."""

    def run(
        *arguments: str,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout: float = 10.0,
    ) -> subprocess.CompletedProcess[bytes]:
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        return subprocess.run(
            [str(dev_python), "-X", "utf8", "-m", "ba_tools", *arguments],
            cwd=cwd,
            env=process_env,
            capture_output=True,
            check=False,
            timeout=timeout,
        )

    return run


@pytest.fixture
def inject_cli_fault(
    dev_python: Path,
) -> Callable[..., subprocess.CompletedProcess[bytes]]:
    """Inject a boundary result or failure in a fresh process."""

    script = r"""
import sys
import ba_tools.__main__ as gateway
from ba_tools.errors import BaToolsError

kind = sys.argv[1]
arguments = sys.argv[2:]

def injected(_arguments):
    if kind == "expected":
        raise BaToolsError(
            code="EXPECTED_TEST_ERROR",
            message="Tiếng Việt — mục tiêu trống",
            details=("", [], ["mục tiêu trống"]),
            remediation=("Thử lại an toàn.",),
        )
    if kind == "interrupt":
        raise KeyboardInterrupt
    if kind == "unexpected":
        raise RuntimeError("secret-marker-from-unexpected-failure")
    if kind == "unicode-success":
        return {
            "schema_version": 1,
            "ok": True,
            "command": "test",
            "data": {
                "text": "Tiếng Việt — mục tiêu trống",
                "empty": "",
                "items": [],
                "unicode_items": ["mục tiêu trống"],
                "arguments": arguments,
            },
            "warnings": [],
        }
    raise AssertionError(f"unknown injected fault: {kind}")

gateway.invoke_cli = injected
raise SystemExit(gateway.entrypoint(arguments))
"""

    def run(
        kind: str,
        *arguments: str,
        cwd: Path,
        timeout: float = 10.0,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [str(dev_python), "-X", "utf8", "-c", script, kind, *arguments],
            cwd=cwd,
            capture_output=True,
            check=False,
            timeout=timeout,
        )

    return run


@pytest.fixture
def process_barrier(
    dev_python: Path,
    tmp_path: Path,
) -> Callable[..., list[subprocess.CompletedProcess[bytes]]]:
    """Release real child processes only after every child reports ready."""

    script = r"""
import json
import sys
import time
from pathlib import Path

ready = Path(sys.argv[1])
release = Path(sys.argv[2])
payload = json.loads(sys.argv[3])
ready.write_bytes(b"ready")
deadline = time.monotonic() + 10.0
while not release.exists():
    if time.monotonic() >= deadline:
        raise SystemExit(98)
    time.sleep(0.005)

import ba_tools.__main__ as gateway
if payload is not None:
    gateway.invoke_cli = lambda _arguments: payload
raise SystemExit(gateway.entrypoint(sys.argv[4:]))
"""

    def run(
        argument_sets: Sequence[Sequence[str]],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        payload: dict[str, object] | None = None,
        timeout: float = 15.0,
    ) -> list[subprocess.CompletedProcess[bytes]]:
        barrier_dir = tmp_path / f"barrier-{time.monotonic_ns()}"
        barrier_dir.mkdir()
        release = barrier_dir / "release"
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        processes: list[subprocess.Popen[bytes]] = []
        ready_paths: list[Path] = []
        for index, arguments in enumerate(argument_sets):
            ready = barrier_dir / f"ready-{index}"
            ready_paths.append(ready)
            processes.append(
                subprocess.Popen(
                    [
                        str(dev_python),
                        "-X",
                        "utf8",
                        "-c",
                        script,
                        str(ready),
                        str(release),
                        __import__("json").dumps(payload, ensure_ascii=False),
                        *arguments,
                    ],
                    cwd=cwd,
                    env=process_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            )

        deadline = time.monotonic() + timeout
        while not all(path.exists() for path in ready_paths):
            if time.monotonic() >= deadline:
                for process in processes:
                    process.kill()
                raise AssertionError("child processes did not reach the synchronization barrier")
            time.sleep(0.005)
        release.write_bytes(b"go")

        results: list[subprocess.CompletedProcess[bytes]] = []
        for process, arguments in zip(processes, argument_sets, strict=True):
            remaining = max(0.1, deadline - time.monotonic())
            stdout, stderr = process.communicate(timeout=remaining)
            results.append(
                subprocess.CompletedProcess(
                    args=list(arguments),
                    returncode=process.returncode,
                    stdout=stdout,
                    stderr=stderr,
                )
            )
        return results

    return run


@pytest.fixture
def deny_network(
    dev_python: Path,
    tmp_path: Path,
) -> dict[str, str]:
    """Install a process-start guard that exits 97 on socket or DNS access."""

    guard_dir = tmp_path / "network-guard"
    guard_dir.mkdir()
    (guard_dir / "sitecustomize.py").write_text(
        """
import os
import sys

def _audit(event, _args):
    if event.startswith("socket."):
        os._exit(97)

sys.addaudithook(_audit)
""".lstrip(),
        encoding="utf-8",
        newline="\n",
    )
    prior = os.environ.get("PYTHONPATH")
    env = {"PYTHONPATH": str(guard_dir) if not prior else os.pathsep.join((str(guard_dir), prior))}
    probe = subprocess.run(
        [str(dev_python), "-X", "utf8", "-c", "import socket; socket.socket()"],
        env={**os.environ, **env},
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert probe.returncode == 97, "network denial fixture was not active"
    return env
