"""Integrated terminal-state contracts for every approved UI category."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from ba_tools.contracts import canonical_json_bytes
from ba_tools.doctor import OPTIONAL_CHECKS, PROFILE_CHECKS, CORE_CHECKS
from ba_tools.init_command import REQUIRED_STATE_FILES
from scripts.smoke_foundation import assert_single_json

PROJECT_ROOT = Path(__file__).resolve().parents[4]
BOOTSTRAP_PATH = PROJECT_ROOT / "installer" / "bootstrap.py"
EMPTY_HEADING = "No business goals are configured."
EMPTY_BODY = (
    "The empty registry is valid; initialization does not infer or create sample goals."
)


def _load_bootstrap():
    spec = importlib.util.spec_from_file_location("terminal_state_installer", BOOTSTRAP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _payload(process) -> dict[str, object]:
    stream = process.stdout if process.returncode == 0 else process.stderr
    opposite = process.stderr if process.returncode == 0 else process.stdout
    assert opposite == b""
    return assert_single_json(stream)


def test_empty_state_contract(temp_repo: Path, run_cli_bytes) -> None:
    bootstrap = _load_bootstrap()
    for answer in ("", None):
        output: list[str] = []
        responses = iter(()) if answer is None else iter((answer,))
        assert not bootstrap.request_network_consent(
            yes=False,
            offline=None,
            interactive=True,
            read_input=lambda: next(responses, None),
            write=output.append,
        )
        assert output[-1] == bootstrap.CANCELLED

    result = run_cli_bytes("--repo-root", str(temp_repo), "init", cwd=PROJECT_ROOT)
    assert result.returncode == 0
    goals = json.loads((temp_repo / REQUIRED_STATE_FILES[-1]).read_bytes())
    assert goals["business_goals"] == []
    assert isinstance(goals["business_goals"], list)
    assert EMPTY_HEADING == "No business goals are configured."
    assert "does not infer" in EMPTY_BODY
    assert len(CORE_CHECKS) == 9


def test_loading_state_contract(temp_repo: Path, run_cli_bytes) -> None:
    bootstrap = _load_bootstrap()
    assert bootstrap.STAGES == (
        "[1/4] Checking prerequisites",
        "[2/4] Preparing the project-local environment",
        "[3/4] Installing locked dependencies",
        "[4/4] Verifying the repo-root launcher",
    )

    result = run_cli_bytes("--version", cwd=temp_repo, env={"NO_COLOR": "1"})
    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout.count(b"\n") == 1
    for forbidden in (b"\x1b[", b"[1/4]", b"progress", b"spinner"):
        assert forbidden not in result.stdout.lower()


def test_error_state_contract(
    tmp_path: Path,
    inject_cli_fault,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    process = inject_cli_fault("unexpected", cwd=tmp_path)
    assert process.returncode == 2
    payload = _payload(process)
    assert payload["error"] == {
        "code": "INTERNAL_ERROR",
        "message": "BA Tools could not complete the command.",
        "details": [],
        "remediation": ["Retry after checking the reported diagnostic code."],
    }
    text = process.stderr.decode("utf-8")
    assert "Traceback" not in text
    assert str(tmp_path) not in text

    bootstrap = _load_bootstrap()
    monkeypatch.setattr(
        bootstrap,
        "discover_prerequisites",
        lambda: (_ for _ in ()).throw(
            bootstrap.InstallerError("Safe failure.", "Run doctor.")
        ),
    )
    assert bootstrap.main([]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines() == [
        "[FAIL] Installer: Safe failure.",
        "    Next: Run doctor.",
    ]


def test_populated_state_contract(temp_repo: Path, run_cli_bytes) -> None:
    initialized = run_cli_bytes("--repo-root", str(temp_repo), "init", cwd=PROJECT_ROOT)
    assert initialized.returncode == 0
    init_data = _payload(initialized)["data"]
    assert init_data["created"] == list(REQUIRED_STATE_FILES)

    result = run_cli_bytes(
        "--repo-root",
        str(temp_repo),
        "doctor",
        "--all",
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 2
    snapshot = _payload(result)["error"]["details"][0]
    expected = [
        *(definition.id for definition in CORE_CHECKS),
        *(definition.id for definition in PROFILE_CHECKS),
        *(definition.id for definition in OPTIONAL_CHECKS),
    ]
    assert [check["id"] for check in snapshot["checks"]] == expected
    assert all(isinstance(check["remediation"], list) for check in snapshot["checks"])
    assert len(snapshot["checks"]) == len(expected)


def test_partial_state_contract(temp_repo: Path, run_cli_bytes) -> None:
    initialized = run_cli_bytes("--repo-root", str(temp_repo), "init", cwd=PROJECT_ROOT)
    assert initialized.returncode == 0
    missing = temp_repo / REQUIRED_STATE_FILES[1]
    missing.unlink()
    preserved = (temp_repo / REQUIRED_STATE_FILES[0]).read_bytes()

    partial = run_cli_bytes("--repo-root", str(temp_repo), "init", cwd=PROJECT_ROOT)
    assert partial.returncode == 2
    error = _payload(partial)["error"]
    assert error["code"] == "STATE_INCOMPLETE"
    assert error["remediation"] == [
        "Run init --repair to create missing files only."
    ]
    assert (temp_repo / REQUIRED_STATE_FILES[0]).read_bytes() == preserved
    assert not missing.exists()

    doctor = run_cli_bytes("--repo-root", str(temp_repo), "doctor", cwd=PROJECT_ROOT)
    snapshot = _payload(doctor)["error"]["details"][0]
    checks = {check["id"]: check for check in snapshot["checks"]}
    assert checks["state.coverage_policy"]["status"] == "fail"
    assert checks["state.schemas"]["status"] == "skipped"
    assert checks["state.schemas"]["blocked_by"] == ["state.coverage_policy"]


def test_overflow_state_contract(tmp_path: Path, process_barrier) -> None:
    long_text = "Tiếng Việt — " + ("chi tiết đầy đủ " * 700)
    payload = {
        "schema_version": 1,
        "ok": True,
        "command": "overflow",
        "data": {"text": long_text, "items": [long_text, long_text]},
        "warnings": [],
    }
    result = process_barrier([[]], cwd=tmp_path, payload=payload)[0]

    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == canonical_json_bytes(payload)
    assert result.stdout.count(b"\n") == 1
    assert b"..." not in result.stdout
    assert assert_single_json(result.stdout)["data"]["text"] == long_text


def test_zero_one_many_state_contract() -> None:
    for items in ([], ["một"], ["một", "hai", "ba"]):
        payload = {
            "schema_version": 1,
            "ok": True,
            "command": "cardinality",
            "data": {"items": items},
            "warnings": [],
        }
        parsed = assert_single_json(canonical_json_bytes(payload))
        assert parsed["data"]["items"] == items
        assert isinstance(parsed["data"]["items"], list)
        assert parsed["warnings"] == []


def test_long_text_state_contract(tmp_path: Path, process_barrier) -> None:
    relative = "bằng-chứng/Đường dẫn tiếng Việt có khoảng trắng.json"
    text = "Mục tiêu nghiệp vụ tiếng Việt — giữ nguyên từng byte. " * 80
    payload = {
        "schema_version": 1,
        "ok": True,
        "command": "long-text",
        "data": {"path": relative, "text": text},
        "warnings": [],
    }
    result = process_barrier(
        [[]],
        cwd=tmp_path,
        payload=payload,
        env={"NO_COLOR": "1"},
    )[0]

    assert result.stdout == canonical_json_bytes(payload)
    assert b"\x1b[" not in result.stdout
    parsed = assert_single_json(result.stdout)
    assert parsed["data"] == {"path": relative, "text": text}
