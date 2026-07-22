"""Raw-process contract for every current ba-tools gateway path."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

ANSI_ESCAPE = re.compile(rb"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def _document(raw: bytes) -> dict[str, object]:
    assert raw
    assert raw.startswith(b"{")
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")
    assert raw.count(b"\n") == 1
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert ANSI_ESCAPE.search(raw) is None
    return json.loads(raw.decode("utf-8"))


def _assert_process_contract(result: subprocess.CompletedProcess[bytes]) -> dict[str, object]:
    assert result.returncode in {0, 2}
    if result.returncode == 0:
        assert result.stderr == b""
        payload = _document(result.stdout)
        assert payload["ok"] is True
    else:
        assert result.stdout == b""
        payload = _document(result.stderr)
        assert payload["ok"] is False
    assert payload["schema_version"] == 1
    return payload


def test_every_process_path_emits_once(
    temp_repo: Path,
    run_cli_bytes: Callable[..., subprocess.CompletedProcess[bytes]],
    inject_cli_fault: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    results = [
        run_cli_bytes(cwd=temp_repo),
        run_cli_bytes("--help", cwd=temp_repo),
        run_cli_bytes("--version", cwd=temp_repo),
        run_cli_bytes("--repo-root", str(temp_repo), "init", cwd=temp_repo),
        run_cli_bytes("--not-an-option", cwd=temp_repo),
        run_cli_bytes("not-a-command", cwd=temp_repo),
        inject_cli_fault("expected", "init", cwd=temp_repo),
        inject_cli_fault("interrupt", "init", cwd=temp_repo),
        inject_cli_fault("unexpected", "init", cwd=temp_repo),
    ]

    payloads = [_assert_process_contract(result) for result in results]

    assert [result.returncode for result in results] == [0, 0, 0, 0, 2, 2, 2, 2, 2]
    assert [payload["command"] for payload in payloads[:4]] == [
        "help",
        "help",
        "version",
        "init",
    ]
    assert [payload["error"]["code"] for payload in payloads[4:]] == [  # type: ignore[index]
        "CLI_USAGE_ERROR",
        "CLI_USAGE_ERROR",
        "EXPECTED_TEST_ERROR",
        "COMMAND_INTERRUPTED",
        "INTERNAL_ERROR",
    ]


def test_success_uses_stdout_and_exit_zero(
    temp_repo: Path,
    run_cli_bytes: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    result = run_cli_bytes("--help", cwd=temp_repo)

    payload = _assert_process_contract(result)

    assert result.returncode == 0
    assert result.stdout
    assert result.stderr == b""
    assert payload["command"] == "help"
    assert isinstance(payload["data"]["help"], str)  # type: ignore[index]


def test_failure_uses_stderr_and_exit_two(
    temp_repo: Path,
    run_cli_bytes: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    result = run_cli_bytes("--repo-root", str(temp_repo / "missing"), "init", cwd=temp_repo)

    payload = _assert_process_contract(result)

    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr
    assert payload["command"] == "init"
    assert payload["error"]["code"] == "REPO_ROOT_INVALID"  # type: ignore[index]


def test_exact_version_surfaces_match(
    temp_repo: Path,
    run_cli_bytes: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    result = run_cli_bytes("--version", cwd=temp_repo)

    payload = _assert_process_contract(result)

    assert payload["data"] == {"version": "0.1.0"}


def test_json_bytes_are_canonical_utf8(
    temp_repo: Path,
    inject_cli_fault: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    result = inject_cli_fault("unicode-success", cwd=temp_repo)

    payload = _assert_process_contract(result)

    assert "Tiếng Việt — mục tiêu trống".encode() in result.stdout
    assert b"\\u" not in result.stdout
    assert payload["data"] == {
        "text": "Tiếng Việt — mục tiêu trống",
        "empty": "",
        "items": [],
        "unicode_items": ["mục tiêu trống"],
        "arguments": [],
    }
    expected = (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    assert result.stdout == expected


def test_concurrent_process_outputs_are_independent(
    unicode_repo_with_spaces: Path,
    process_barrier: Callable[..., list[subprocess.CompletedProcess[bytes]]],
) -> None:
    argument_sets = [
        ["--version"],
        ["--help"],
        ["--repo-root", str(unicode_repo_with_spaces), "init"],
        ["--version"],
        ["--help"],
        ["--repo-root", str(unicode_repo_with_spaces), "init"],
    ]

    results = process_barrier(argument_sets, cwd=unicode_repo_with_spaces)
    payloads = [_assert_process_contract(result) for result in results]

    assert all(result.returncode == 0 for result in results)
    assert [payload["command"] for payload in payloads] == [
        "version",
        "help",
        "init",
        "version",
        "help",
        "init",
    ]
    assert sum(payload["data"].get("changed") is True for payload in payloads) == 1  # type: ignore[union-attr]
    assert sum(payload["data"].get("changed") is False for payload in payloads) == 1  # type: ignore[union-attr]


def test_command_name_ignores_substrings_in_paths() -> None:
    from ba_tools.__main__ import _command_name

    assert _command_name(["--repo-root", r"D:\projects\init-toolkit", "doctor"]) == "doctor"
    assert _command_name(["--repo-root", r"D:\projects\doctor-notes", "init"]) == "init"
    assert _command_name(["--not-an-option"]) == "unknown"


def test_unexpected_error_is_redacted(
    temp_repo: Path,
    inject_cli_fault: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    result = inject_cli_fault("unexpected", "init", cwd=temp_repo)

    payload = _assert_process_contract(result)

    assert payload["error"] == {
        "code": "INTERNAL_ERROR",
        "message": "BA Tools could not complete the command.",
        "details": [],
        "remediation": ["Retry after checking the reported diagnostic code."],
    }
    assert b"secret-marker" not in result.stderr
    assert b"Traceback" not in result.stderr
    assert str(temp_repo).encode("utf-8") not in result.stderr
