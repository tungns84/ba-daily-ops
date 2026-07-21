"""UTF-8 byte evidence across redirected, path, error, and concurrent boundaries."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

VIETNAMESE = "Tiếng Việt — mục tiêu trống"
VIETNAMESE_BYTES = VIETNAMESE.encode("utf-8")


def _canonical(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _one_document(raw: bytes) -> dict[str, object]:
    assert raw.startswith(b"{")
    assert raw.endswith(b"\n")
    assert raw.count(b"\n") == 1
    assert b"\xef\xbb\xbf" not in raw
    assert VIETNAMESE_BYTES in raw
    payload = json.loads(raw.decode("utf-8"))
    assert raw == _canonical(payload)
    return payload


def test_vietnamese_bytes_round_trip(
    temp_repo: Path,
    inject_cli_fault: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    result = inject_cli_fault("unicode-success", cwd=temp_repo)

    payload = _one_document(result.stdout)

    assert result.returncode == 0
    assert result.stderr == b""
    assert payload["data"]["text"] == VIETNAMESE  # type: ignore[index]
    assert b"\\u" not in result.stdout


def test_empty_unicode_values_round_trip(
    temp_repo: Path,
    inject_cli_fault: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    result = inject_cli_fault("unicode-success", cwd=temp_repo)

    payload = _one_document(result.stdout)
    data = payload["data"]

    assert data["empty"] == ""  # type: ignore[index]
    assert data["items"] == []  # type: ignore[index]
    assert data["unicode_items"] == ["mục tiêu trống"]  # type: ignore[index]
    assert data["arguments"] == []  # type: ignore[index]


def test_redirected_streams_are_utf8(
    temp_repo: Path,
    inject_cli_fault: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    success = inject_cli_fault("unicode-success", cwd=temp_repo)
    failure = inject_cli_fault("expected", "init", cwd=temp_repo)

    success_payload = _one_document(success.stdout)
    failure_payload = _one_document(failure.stderr)

    assert success.returncode == 0
    assert success.stderr == b""
    assert failure.returncode == 2
    assert failure.stdout == b""
    assert success.stdout == _canonical(success_payload)
    assert failure.stderr == _canonical(failure_payload)
    assert failure_payload["error"]["message"] == VIETNAMESE  # type: ignore[index]
    assert failure_payload["error"]["details"] == ["", [], ["mục tiêu trống"]]  # type: ignore[index]


def test_unicode_repo_and_files_round_trip(
    tmp_path: Path,
    unicode_repo_with_spaces: Path,
    run_cli_bytes: Callable[..., subprocess.CompletedProcess[bytes]],
    inject_cli_fault: Callable[..., subprocess.CompletedProcess[bytes]],
) -> None:
    external_cwd = tmp_path / "thư mục gọi bên ngoài"
    external_cwd.mkdir()
    relative_file = Path("tài liệu") / "mục tiêu trống.json"
    unicode_file = unicode_repo_with_spaces / relative_file
    unicode_file.parent.mkdir()
    file_bytes = _canonical({"text": VIETNAMESE, "empty": [], "name": relative_file.as_posix()})
    unicode_file.write_bytes(file_bytes)

    init_result = run_cli_bytes(
        "--repo-root",
        str(unicode_repo_with_spaces),
        "init",
        cwd=external_cwd,
    )
    echo_result = inject_cli_fault(
        "unicode-success",
        relative_file.as_posix(),
        cwd=external_cwd,
    )

    assert init_result.returncode == 0
    assert init_result.stderr == b""
    assert unicode_file.read_bytes() == file_bytes
    payload = _one_document(echo_result.stdout)
    assert payload["data"]["arguments"] == [relative_file.as_posix()]  # type: ignore[index]


def test_concurrent_utf8_outputs_are_complete(
    unicode_repo_with_spaces: Path,
    process_barrier: Callable[..., list[subprocess.CompletedProcess[bytes]]],
) -> None:
    payload = {
        "schema_version": 1,
        "ok": True,
        "command": "test",
        "data": {
            "text": VIETNAMESE,
            "empty": "",
            "items": [],
            "unicode_items": ["mục tiêu trống", "dữ liệu"],
        },
        "warnings": [],
    }

    results = process_barrier(
        [["parallel", str(index)] for index in range(8)],
        cwd=unicode_repo_with_spaces,
        payload=payload,
    )

    assert len(results) == 8
    for result in results:
        assert result.returncode == 0
        assert result.stderr == b""
        assert result.stdout == _canonical(payload)
        assert _one_document(result.stdout) == payload
