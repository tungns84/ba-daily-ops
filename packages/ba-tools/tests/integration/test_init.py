"""D-11 through D-15 schema-backed initialization state matrix."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from ba_tools.errors import BaToolsError
from ba_tools.init_command import REQUIRED_STATE_FILES
from ba_tools.paths import resolve_repo_root
from ba_tools.state.atomic import canonical_file_bytes
from ba_tools.state.locking import WorkspaceLock

RunCli = Callable[..., subprocess.CompletedProcess[bytes]]
ProcessBarrier = Callable[..., list[subprocess.CompletedProcess[bytes]]]


def _state_path(repo: Path, relative: str) -> Path:
    return repo.joinpath(*relative.split("/"))


def _write_default(repo: Path, relative: str) -> None:
    target = _state_path(repo, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_file_bytes(target.name))


def _snapshot(repo: Path) -> dict[str, tuple[bytes, str, int]]:
    return {
        path.relative_to(repo).as_posix(): (
            path.read_bytes(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_mtime_ns,
        )
        for path in sorted(repo.rglob("*"))
        if path.is_file()
    }


def _payload(process: subprocess.CompletedProcess[bytes]) -> dict[str, object]:
    stream = process.stdout if process.returncode == 0 else process.stderr
    opposite = process.stderr if process.returncode == 0 else process.stdout
    assert opposite == b""
    assert stream.endswith(b"\n")
    assert stream.count(b"\n") == 1
    return json.loads(stream)


def _run_init(
    run_cli_bytes: RunCli,
    repo: Path,
    *,
    repair: bool = False,
    timeout: float = 10.0,
) -> subprocess.CompletedProcess[bytes]:
    arguments = ["--repo-root", str(repo), "init"]
    if repair:
        arguments.append("--repair")
    return run_cli_bytes(*arguments, cwd=repo.parent, timeout=timeout)


def _assert_preserved(
    before: dict[str, tuple[bytes, str, int]],
    repo: Path,
) -> None:
    assert _snapshot(repo) == before


def test_fresh_init_creates_exact_files(temp_repo: Path, run_cli_bytes: RunCli) -> None:
    """D-11/D-15: absent state creates exactly three defaults in declared order."""

    process = _run_init(run_cli_bytes, temp_repo)

    assert process.returncode == 0
    payload = _payload(process)
    assert payload["data"] == {
        "changed": True,
        "created": list(REQUIRED_STATE_FILES),
        "quarantined": [],
    }
    assert [
        path.relative_to(temp_repo).as_posix()
        for path in temp_repo.rglob("*")
        if path.is_file()
    ] == list(REQUIRED_STATE_FILES)
    for relative in REQUIRED_STATE_FILES:
        target = _state_path(temp_repo, relative)
        assert target.read_bytes() == canonical_file_bytes(target.name)


def test_complete_init_is_byte_and_mtime_noop(
    temp_repo: Path,
    run_cli_bytes: RunCli,
) -> None:
    """D-11: complete valid state is a byte, hash, and mtime preserving no-op."""

    first = _run_init(run_cli_bytes, temp_repo)
    assert first.returncode == 0
    before = _snapshot(temp_repo)

    second = _run_init(run_cli_bytes, temp_repo)

    assert second.returncode == 0
    assert _payload(second)["data"] == {
        "changed": False,
        "created": [],
        "quarantined": [],
    }
    _assert_preserved(before, temp_repo)


def test_partial_plain_init_writes_nothing(
    temp_repo: Path,
    run_cli_bytes: RunCli,
) -> None:
    """D-12: plain init preserves partial state and gives exact repair guidance."""

    _write_default(temp_repo, REQUIRED_STATE_FILES[0])
    before = _snapshot(temp_repo)

    process = _run_init(run_cli_bytes, temp_repo)

    assert process.returncode == 2
    error = _payload(process)["error"]
    assert error == {
        "code": "STATE_INCOMPLETE",
        "message": "Required workspace files are missing.",
        "details": [],
        "remediation": ["Run init --repair to create missing files only."],
    }
    _assert_preserved(before, temp_repo)


def test_repair_creates_only_missing_files(
    temp_repo: Path,
    run_cli_bytes: RunCli,
) -> None:
    """D-13: explicit repair creates missing canonical targets and never replaces."""

    _write_default(temp_repo, REQUIRED_STATE_FILES[0])
    existing = _state_path(temp_repo, REQUIRED_STATE_FILES[0])
    existing_before = (existing.read_bytes(), existing.stat().st_mtime_ns)

    process = _run_init(run_cli_bytes, temp_repo, repair=True)

    assert process.returncode == 0
    assert _payload(process)["data"] == {
        "changed": True,
        "created": list(REQUIRED_STATE_FILES[1:]),
        "quarantined": [],
    }
    assert (existing.read_bytes(), existing.stat().st_mtime_ns) == existing_before
    for relative in REQUIRED_STATE_FILES[1:]:
        target = _state_path(temp_repo, relative)
        assert target.read_bytes() == canonical_file_bytes(target.name)


def test_invalid_json_is_preserved(temp_repo: Path, run_cli_bytes: RunCli) -> None:
    """D-14: malformed JSON is diagnosed and preserved before any repair write."""

    config = _state_path(temp_repo, REQUIRED_STATE_FILES[0])
    config.parent.mkdir()
    config.write_bytes(b'{"profile":"light",')
    before = _snapshot(temp_repo)

    process = _run_init(run_cli_bytes, temp_repo, repair=True)

    assert process.returncode == 2
    assert _payload(process)["error"] == {
        "code": "STATE_SCHEMA_INVALID",
        "message": "Existing state is invalid and was preserved.",
        "details": [
            {
                "message": "File is not valid UTF-8 JSON.",
                "path": ".ba-ops/config.json",
                "pointer": "",
                "validator": "parse",
            }
        ],
        "remediation": ["Correct the reported fields, then retry."],
    }
    _assert_preserved(before, temp_repo)


def test_schema_invalid_state_reports_all_diagnostics(
    temp_repo: Path,
    run_cli_bytes: RunCli,
) -> None:
    """D-14: every schema violation is returned in stable file and pointer order."""

    for relative in reversed(REQUIRED_STATE_FILES):
        _write_default(temp_repo, relative)
    _state_path(temp_repo, REQUIRED_STATE_FILES[0]).write_text(
        '{"extra":true,"profile":"verbose","schema_version":1}\n',
        encoding="utf-8",
        newline="\n",
    )
    _state_path(temp_repo, REQUIRED_STATE_FILES[2]).write_text(
        '{"business_goals":"not-an-array","schema_version":1}\n',
        encoding="utf-8",
        newline="\n",
    )
    before = _snapshot(temp_repo)

    process = _run_init(run_cli_bytes, temp_repo, repair=True)

    assert process.returncode == 2
    assert _payload(process)["error"]["details"] == [
        {
            "message": "Additional properties are not allowed ('extra' was unexpected)",
            "path": ".ba-ops/config.json",
            "pointer": "",
            "validator": "additionalProperties",
        },
        {
            "message": "'verbose' is not one of ['light', 'standard', 'strict']",
            "path": ".ba-ops/config.json",
            "pointer": "/profile",
            "validator": "enum",
        },
        {
            "message": "'not-an-array' is not of type 'array'",
            "path": ".ba-ops/business-goals.json",
            "pointer": "/business_goals",
            "validator": "type",
        },
    ]
    _assert_preserved(before, temp_repo)


def test_unsupported_schema_version_is_preserved(
    temp_repo: Path,
    run_cli_bytes: RunCli,
) -> None:
    """D-14: unsupported state versions fail locally without changing any file."""

    for relative in REQUIRED_STATE_FILES:
        _write_default(temp_repo, relative)
    config = _state_path(temp_repo, REQUIRED_STATE_FILES[0])
    config.write_text(
        '{"profile":"light","schema_version":2}\n',
        encoding="utf-8",
        newline="\n",
    )
    before = _snapshot(temp_repo)

    process = _run_init(run_cli_bytes, temp_repo, repair=True)

    assert process.returncode == 2
    assert _payload(process)["error"]["details"] == [
        {
            "message": "Unsupported schema_version; expected 1.",
            "path": ".ba-ops/config.json",
            "pointer": "/schema_version",
            "validator": "const",
        }
    ]
    _assert_preserved(before, temp_repo)


def test_duplicate_targets_fail_before_io(
    temp_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-11: duplicate required targets fail before target resolution or access."""

    from ba_tools.state import validation

    root = resolve_repo_root(temp_repo)
    monkeypatch.setattr(
        validation,
        "resolve_business_path",
        lambda *_args, **_kwargs: pytest.fail("duplicate targets reached filesystem resolution"),
    )

    with pytest.raises(BaToolsError) as captured:
        validation.classify_workspace_state(
            root,
            required_files=(
                ".ba-ops/config.json",
                ".ba-ops/config.json",
            ),
        )

    assert captured.value.code == "DUPLICATE_STATE_TARGET"
    assert list(temp_repo.iterdir()) == []


def test_lock_timeout_writes_nothing(temp_repo: Path, run_cli_bytes: RunCli) -> None:
    """D-11/D-16: bounded lock timeout produces one error and zero state mutation."""

    before = _snapshot(temp_repo)
    with WorkspaceLock(resolve_repo_root(temp_repo)):
        process = _run_init(run_cli_bytes, temp_repo, timeout=10.0)

    assert process.returncode == 2
    assert _payload(process)["error"] == {
        "code": "WORKSPACE_LOCK_TIMEOUT",
        "message": "Another workspace writer did not finish in time.",
        "details": [],
        "remediation": ["Retry after the other ba-tools command completes."],
    }
    _assert_preserved(before, temp_repo)


def test_concurrent_init_and_repair_are_serialized(
    temp_repo: Path,
    process_barrier: ProcessBarrier,
) -> None:
    """D-11/D-13: synchronized init and repair share one serialized transition."""

    _write_default(temp_repo, REQUIRED_STATE_FILES[0])
    arguments: Sequence[Sequence[str]] = (
        ("--repo-root", str(temp_repo), "init"),
        ("--repo-root", str(temp_repo), "init", "--repair"),
    )

    plain, repair = process_barrier(arguments, cwd=temp_repo.parent)

    repair_payload = _payload(repair)
    assert repair.returncode == 0
    assert repair_payload["data"]["changed"] is True
    assert repair_payload["data"]["created"] == list(REQUIRED_STATE_FILES[1:])
    if plain.returncode == 0:
        assert _payload(plain)["data"]["changed"] is False
    else:
        assert _payload(plain)["error"]["code"] == "STATE_INCOMPLETE"
    assert _snapshot(temp_repo).keys() == set(REQUIRED_STATE_FILES)
