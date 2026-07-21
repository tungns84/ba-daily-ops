"""Prove the installed runtime stays local-only under real process execution."""

from __future__ import annotations

import ast
import json
import subprocess
from collections.abc import Callable
from pathlib import Path

from ba_tools.cli import cli

PROJECT_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_ROOT = PROJECT_ROOT / "packages" / "ba-tools" / "src" / "ba_tools"
NETWORK_IMPORT_ROOTS = {
    "aiohttp",
    "ftplib",
    "http",
    "httpx",
    "requests",
    "smtplib",
    "socket",
    "telnetlib",
    "urllib",
    "websockets",
    "xmlrpc",
}


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def _payload(result: subprocess.CompletedProcess[bytes]) -> dict[str, object]:
    assert result.returncode in {0, 2}, (
        f"guarded command failed with {result.returncode}: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    selected, opposite = (
        (result.stdout, result.stderr)
        if result.returncode == 0
        else (result.stderr, result.stdout)
    )
    assert opposite == b""
    return json.loads(selected.decode("utf-8"))


def test_runtime_imports_exclude_network_clients() -> None:
    scanned = [
        path
        for path in RUNTIME_ROOT.rglob("*.py")
        if "installer" not in path.relative_to(RUNTIME_ROOT).parts
    ]
    violations = {
        path.relative_to(RUNTIME_ROOT).as_posix(): sorted(
            _import_roots(path) & NETWORK_IMPORT_ROOTS
        )
        for path in scanned
        if _import_roots(path) & NETWORK_IMPORT_ROOTS
    }

    assert scanned
    assert violations == {}


def test_every_runtime_command_is_zero_network(
    tmp_path: Path,
    deny_network: dict[str, str],
    run_cli_bytes: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    repo = tmp_path / "guarded repo"
    repo.mkdir()
    command_arguments = {
        "init": ["--repo-root", str(repo), "init"],
        "doctor": ["--repo-root", str(repo), "doctor", "--all"],
    }

    assert set(cli.commands) == set(command_arguments)
    results = [
        run_cli_bytes(cwd=tmp_path, env=deny_network),
        run_cli_bytes("--help", cwd=tmp_path, env=deny_network),
        run_cli_bytes("--version", cwd=tmp_path, env=deny_network),
        *(
            run_cli_bytes(*arguments, cwd=tmp_path, env=deny_network)
            for arguments in command_arguments.values()
        ),
    ]

    payloads = [_payload(result) for result in results]
    assert [payload["command"] for payload in payloads] == [
        "help",
        "help",
        "version",
        "init",
        "doctor",
    ]


def test_parallel_runtime_commands_are_zero_network(
    unicode_repo_with_spaces: Path,
    deny_network: dict[str, str],
    process_barrier: Callable[..., list[subprocess.CompletedProcess[bytes]]],
) -> None:
    argument_sets = [
        ["--version"],
        ["--help"],
        ["--repo-root", str(unicode_repo_with_spaces), "init"],
        ["--repo-root", str(unicode_repo_with_spaces), "doctor", "--all"],
        ["--version"],
        ["--help"],
        ["--repo-root", str(unicode_repo_with_spaces), "init"],
        ["--repo-root", str(unicode_repo_with_spaces), "doctor", "--all"],
    ]

    results = process_barrier(
        argument_sets,
        cwd=unicode_repo_with_spaces,
        env=deny_network,
    )
    payloads = [_payload(result) for result in results]

    assert all(result.returncode != 97 for result in results)
    assert [payload["command"] for payload in payloads].count("init") == 2
    assert [payload["command"] for payload in payloads].count("doctor") == 2
