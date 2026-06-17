"""Integration tests for the output contract — all commands emit flat JSON (TOOL-13, CDX-05).

For every covered subcommand:
  - Success path: returncode 0, stdout is valid JSON, ok:true, failures:[], no 'data' key (D-03)
  - Error path:   returncode 2, stderr is valid JSON, ok:false, failures: non-empty list (D-04)

Commands covered: resolve-route, byte-check, init, state, uc-status, lint-requirements,
verify, extract-uc, template, discovery, scan, confirm.

All subprocess invocations use sys.executable (DESIGN §11, TOOL-14) — never a bare 'python' string.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

BA_TOOLS = [sys.executable, "-m", "ba_tools"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(args: list[str], repo_root: str | None = None,
         cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run ba-tools and return the completed process."""
    cmd = list(BA_TOOLS)
    if repo_root is not None:
        cmd += ["--repo-root", repo_root]
    cmd += args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def _assert_success(result: subprocess.CompletedProcess, cmd_label: str) -> dict:
    """Assert success contract (D-03): returncode 0, stdout JSON, ok:true, failures:[], no data."""
    assert result.returncode == 0, (
        f"[{cmd_label}] Expected exit 0, got {result.returncode}\n"
        f"  stderr: {result.stderr!r}\n"
        f"  stdout: {result.stdout!r}"
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(f"[{cmd_label}] stdout is not valid JSON: {exc}\n  stdout: {result.stdout!r}")
    assert payload.get("ok") is True, f"[{cmd_label}] Expected ok:true, got {payload}"
    assert payload.get("failures") == [], (
        f"[{cmd_label}] Expected failures:[], got {payload.get('failures')!r}"
    )
    assert "data" not in payload, (
        f"[{cmd_label}] Envelope must be flat (no nested 'data' key). Keys: {list(payload.keys())}"
    )
    return payload


def _assert_error(result: subprocess.CompletedProcess, cmd_label: str) -> dict:
    """Assert error contract (D-04): returncode 2, stderr JSON, ok:false, failures non-empty."""
    assert result.returncode == 2, (
        f"[{cmd_label}] Expected exit 2, got {result.returncode}\n"
        f"  stdout: {result.stdout!r}\n"
        f"  stderr: {result.stderr!r}"
    )
    try:
        payload = json.loads(result.stderr)
    except json.JSONDecodeError as exc:
        pytest.fail(f"[{cmd_label}] stderr is not valid JSON: {exc}\n  stderr: {result.stderr!r}")
    assert payload.get("ok") is False, f"[{cmd_label}] Expected ok:false, got {payload}"
    failures = payload.get("failures")
    assert isinstance(failures, list) and len(failures) > 0, (
        f"[{cmd_label}] Expected non-empty failures list, got {failures!r}"
    )
    return payload


def _seed_template(repo_root: Path, name: str, content: str) -> None:
    """Create a named template in the ba-core/templates dir."""
    tpl_dir = (
        repo_root
        / ".agents" / "ba-daily-operators" / "ba-tools" / "ba-core" / "templates"
    )
    tpl_dir.mkdir(parents=True, exist_ok=True)
    (tpl_dir / f"{name}.md").write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# resolve-route — success + UNKNOWN_OPERATOR error
# ---------------------------------------------------------------------------

def test_resolve_route_ok(tmp_path):
    """resolve-route ba-mermaid -> ok:true, failures:[], default_route present (D-03)."""
    result = _run(["resolve-route", "ba-mermaid"], repo_root=str(tmp_path))
    payload = _assert_success(result, "resolve-route")
    assert "default_route" in payload, "resolve-route success must include 'default_route'"
    assert "operator" in payload


def test_resolve_route_unknown_operator_exits_2(tmp_path):
    """resolve-route UNKNOWN-OP -> ok:false, failures non-empty, exit 2 (D-04)."""
    result = _run(["resolve-route", "UNKNOWN-OPERATOR-XYZ"], repo_root=str(tmp_path))
    payload = _assert_error(result, "resolve-route UNKNOWN_OPERATOR")
    assert any(f.get("code") == "UNKNOWN_OPERATOR" for f in payload["failures"])


# ---------------------------------------------------------------------------
# byte-check — success + EXCEEDS_LIMIT error
# ---------------------------------------------------------------------------

def test_byte_check_ok(tmp_path):
    """byte-check on a small file -> ok:true, failures:[], checks list present (D-03)."""
    small = tmp_path / "small.md"
    small.write_bytes(b"hello" * 10)  # 50 bytes — well under limit
    result = _run(["byte-check", "small.md"], repo_root=str(tmp_path))
    payload = _assert_success(result, "byte-check ok")
    assert "checks" in payload


def test_byte_check_exceeds_limit_exits_2(tmp_path):
    """byte-check on a file >= 32768 B -> ok:false, EXCEEDS_LIMIT, exit 2 (D-04)."""
    big = tmp_path / "big.md"
    big.write_bytes(b"x" * 32768)  # exactly at limit — must FAIL (strict less-than)
    result = _run(["byte-check", "big.md"], repo_root=str(tmp_path))
    payload = _assert_error(result, "byte-check EXCEEDS_LIMIT")
    assert any(f.get("code") == "EXCEEDS_LIMIT" for f in payload["failures"])


# ---------------------------------------------------------------------------
# init — success
# ---------------------------------------------------------------------------

def test_init_ok(tmp_path):
    """init ba-uc -> ok:true, failures:[], operator/routes present (D-03)."""
    result = _run(["init", "ba-uc"], repo_root=str(tmp_path))
    payload = _assert_success(result, "init")
    assert "operator" in payload
    assert "routes" in payload
    assert "default_route" in payload


# ---------------------------------------------------------------------------
# state — success + BAD_DATA error
# ---------------------------------------------------------------------------

def test_state_update_ok(tmp_path):
    """state update --data JSON -> ok:true, failures:[], action echoed (D-03)."""
    result = _run(["state", "update", "--data", '{"step": "1"}'], repo_root=str(tmp_path))
    payload = _assert_success(result, "state update ok")
    assert payload.get("action") == "update"


def test_state_bad_data_exits_2(tmp_path):
    """state update --data invalid-json -> ok:false, BAD_DATA, exit 2 (D-04)."""
    result = _run(["state", "update", "--data", "NOT_JSON!!!"], repo_root=str(tmp_path))
    payload = _assert_error(result, "state BAD_DATA")
    assert any(f.get("code") == "BAD_DATA" for f in payload["failures"])


# ---------------------------------------------------------------------------
# uc-status — NO_STATE error (no STATE.md)
# ---------------------------------------------------------------------------

def test_uc_status_no_state_exits_2(tmp_path):
    """uc-status with no .ba-ops/STATE.md -> ok:false, NO_STATE, exit 2 (D-04)."""
    result = _run(["uc-status"], repo_root=str(tmp_path))
    payload = _assert_error(result, "uc-status NO_STATE")
    assert any(f.get("code") == "NO_STATE" for f in payload["failures"])


def test_uc_status_ok_after_init(tmp_path):
    """uc-status after init -> ok:true, steps and next_step present (D-03)."""
    # First create the .ba-ops/STATE.md via init
    _run(["init", "ba-uc"], repo_root=str(tmp_path))
    result = _run(["uc-status"], repo_root=str(tmp_path))
    payload = _assert_success(result, "uc-status after init")
    assert "steps" in payload
    assert "next_step" in payload


# ---------------------------------------------------------------------------
# lint-requirements — success
# ---------------------------------------------------------------------------

def test_lint_requirements_ok(tmp_path):
    """lint-requirements on a clean file -> ok:true, failures:[], findings list (D-03)."""
    reqs_file = tmp_path / "reqs.md"
    reqs_file.write_text(
        "# Requirements\n\n"
        "| ID | Statement | Source |\n"
        "|----|-----------|--------|\n"
        "| TOOL-01 | The system shall return JSON with ok:true on success. | SRS §3.1 |\n",
        encoding="utf-8",
    )
    # Pass absolute path — lint-requirements resolves file relative to cwd, not --repo-root
    result = _run(["lint-requirements", str(reqs_file)], repo_root=str(tmp_path))
    payload = _assert_success(result, "lint-requirements ok")
    assert "findings" in payload
    assert "checked" in payload


# ---------------------------------------------------------------------------
# verify — success + CITATION_NOT_FOUND error
# ---------------------------------------------------------------------------

def test_verify_ok_no_spans(tmp_path):
    """verify on a requirements file with no Span column -> ok:true, no citation checks (D-03)."""
    reqs_file = tmp_path / "reqs.md"
    reqs_file.write_text(
        "# Requirements\n\n"
        "| ID | Statement | Source |\n"
        "|----|-----------|--------|\n"
        "| TOOL-01 | The system shall return JSON with ok:true on success. | SRS §3.1 |\n",
        encoding="utf-8",
    )
    # Pass absolute path — verify resolves file relative to cwd, not --repo-root
    result = _run(["verify", "--reqs", str(reqs_file)], repo_root=str(tmp_path))
    payload = _assert_success(result, "verify ok no spans")
    assert "findings" in payload


def test_verify_citation_error_exits_2(tmp_path):
    """verify with a span not in cited section -> ok:false, CITATION_NOT_FOUND, exit 2 (D-04)."""
    # Source document with Background section but span not present there
    source = tmp_path / "source.md"
    source.write_text(
        "## Background\n\nThis section has no target span.\n\n"
        "## Requirements\n\nThe system validates all input paths.\n",
        encoding="utf-8",
    )
    reqs_file = tmp_path / "reqs.md"
    reqs_file.write_text(
        "# Requirements\n\n"
        "| ID | Statement | Source | Section | Span | Status |\n"
        "|----|-----------|--------|---------|------|--------|\n"
        f"| TOOL-01 | The system shall validate paths. | {source} | Background | this span does not exist here | stated |\n",
        encoding="utf-8",
    )
    # Pass absolute paths for both --reqs
    result = _run(["verify", "--reqs", str(reqs_file)], repo_root=str(tmp_path))
    payload = _assert_error(result, "verify CITATION_NOT_FOUND")
    assert any(f.get("code") == "CITATION_NOT_FOUND" for f in payload["failures"])


# ---------------------------------------------------------------------------
# extract-uc — success + FILE_NOT_FOUND error
# ---------------------------------------------------------------------------

def test_extract_uc_ok(tmp_path):
    """extract-uc on a Markdown file with a UC heading -> ok:true, section present (D-03)."""
    uc_doc = tmp_path / "uc_doc.md"
    uc_doc.write_text(
        "# Project\n\n## UC-001. Create Report\n\nThe user submits a report request.\n",
        encoding="utf-8",
    )
    result = _run(
        ["extract-uc", "--uc", "uc_doc.md: ## UC-001. Create Report"],
        repo_root=str(tmp_path),
    )
    payload = _assert_success(result, "extract-uc ok")
    assert payload.get("uc_id") == "UC-001"
    assert "section" in payload


def test_extract_uc_missing_file_exits_2(tmp_path):
    """extract-uc with a non-existent file -> ok:false, FILE_NOT_FOUND, exit 2 (D-04)."""
    result = _run(
        ["extract-uc", "--uc", "no_such_file.md: ## UC-001. Test UC"],
        repo_root=str(tmp_path),
    )
    payload = _assert_error(result, "extract-uc FILE_NOT_FOUND")
    assert any(f.get("code") == "FILE_NOT_FOUND" for f in payload["failures"])


# ---------------------------------------------------------------------------
# template — success + TEMPLATE_NOT_FOUND error
# ---------------------------------------------------------------------------

def test_template_fill_ok(tmp_path):
    """template fill with a seeded template -> ok:true, out path in payload (D-03)."""
    _seed_template(tmp_path, "sample", "# ${title}\n\nContent here.\n")
    out = tmp_path / "result.md"
    result = _run(
        ["template", "fill", "sample", "--out", str(out), "--var", "title=My Report"],
        repo_root=str(tmp_path),
        cwd=str(tmp_path),
    )
    payload = _assert_success(result, "template fill ok")
    assert "out" in payload


def test_template_fill_not_found_exits_2(tmp_path):
    """template fill with unknown name -> ok:false, TEMPLATE_NOT_FOUND, exit 2 (D-04)."""
    out = tmp_path / "result.md"
    result = _run(
        ["template", "fill", "nonexistent-xyz", "--out", str(out)],
        repo_root=str(tmp_path),
        cwd=str(tmp_path),
    )
    payload = _assert_error(result, "template TEMPLATE_NOT_FOUND")
    assert any(f.get("code") == "TEMPLATE_NOT_FOUND" for f in payload["failures"])


# ---------------------------------------------------------------------------
# discovery — success
# ---------------------------------------------------------------------------

def test_discovery_list_ok(tmp_path):
    """discovery list on empty repo -> ok:true, discoveries list present (D-03)."""
    result = _run(["discovery", "list"], repo_root=str(tmp_path))
    payload = _assert_success(result, "discovery list ok")
    assert "discoveries" in payload
    assert isinstance(payload["discoveries"], list)


def test_discovery_add_ok(tmp_path):
    """discovery add -> ok:true, failures:[], added:true (D-03)."""
    result = _run(
        ["discovery", "add", "--note", "Found a data anomaly", "--tag", "UC-001"],
        repo_root=str(tmp_path),
    )
    payload = _assert_success(result, "discovery add ok")
    assert payload.get("added") is True


# ---------------------------------------------------------------------------
# scan — success
# ---------------------------------------------------------------------------

def test_scan_ok(tmp_path):
    """scan on a clean file -> ok:true, failures:[], findings list, blocked:false (D-03)."""
    clean_file = tmp_path / "clean.md"
    clean_file.write_text("# Normal content\n\nThis is a standard document.\n", encoding="utf-8")
    result = _run(["scan", "--file", "clean.md"], repo_root=str(tmp_path))
    payload = _assert_success(result, "scan ok")
    assert "findings" in payload
    assert payload.get("blocked") is False


def test_scan_missing_file_exits_2(tmp_path):
    """scan on a non-existent file -> ok:false, FILE_NOT_FOUND, exit 2 (D-04)."""
    result = _run(["scan", "--file", "no_such.md"], repo_root=str(tmp_path))
    payload = _assert_error(result, "scan FILE_NOT_FOUND")
    assert any(f.get("code") == "FILE_NOT_FOUND" for f in payload["failures"])


# ---------------------------------------------------------------------------
# confirm — success
# ---------------------------------------------------------------------------

def test_confirm_ok(tmp_path):
    """confirm -> ok:true, failures:[], confirmed:true (D-03)."""
    result = _run(["confirm"], repo_root=str(tmp_path))
    payload = _assert_success(result, "confirm ok")
    assert payload.get("confirmed") is True


# ---------------------------------------------------------------------------
# Cross-cutting: no stack traces in error output (T-1-07)
# ---------------------------------------------------------------------------

def test_no_stack_trace_in_error_output(tmp_path):
    """Error output never contains 'Traceback' — structured failures only (T-1-07)."""
    # Use uc-status NO_STATE as the representative error path
    result = _run(["uc-status"], repo_root=str(tmp_path))
    assert result.returncode == 2
    assert "Traceback" not in result.stderr, (
        "Error output must not contain Python tracebacks (T-1-07)\n"
        f"  stderr: {result.stderr!r}"
    )
    assert "Traceback" not in result.stdout


# ---------------------------------------------------------------------------
# Cross-cutting: error goes to STDERR not STDOUT (D-04)
# ---------------------------------------------------------------------------

def test_error_output_on_stderr_not_stdout(tmp_path):
    """Error JSON is on stderr; stdout is empty for error paths (D-04)."""
    result = _run(["resolve-route", "UNKNOWN-OPERATOR-XYZ"], repo_root=str(tmp_path))
    assert result.returncode == 2
    # stdout should be empty on error
    assert result.stdout.strip() == "", (
        f"stdout must be empty on error paths, got: {result.stdout!r}"
    )
    # stderr should have the failure payload
    payload = json.loads(result.stderr)
    assert payload["ok"] is False


# ---------------------------------------------------------------------------
# Cross-cutting: success output on STDOUT not STDERR (D-03)
# ---------------------------------------------------------------------------

def test_success_output_on_stdout_not_stderr(tmp_path):
    """Success JSON is on stdout; stderr is empty for success paths (D-03)."""
    result = _run(["confirm"], repo_root=str(tmp_path))
    assert result.returncode == 0
    assert result.stderr.strip() == "", (
        f"stderr must be empty on success paths, got: {result.stderr!r}"
    )
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


# ---------------------------------------------------------------------------
# Legacy stubs (preserved from Wave-0, now satisfied by the tests above)
# ---------------------------------------------------------------------------

def test_error_command_exits_2(tmp_path):
    """BaToolsError commands exit 2 with ok:false and flat JSON on stderr (TOOL-13)."""
    result = _run(["uc-status"], repo_root=str(tmp_path))
    assert result.returncode == 2, f"Expected exit 2, got {result.returncode}"


def test_error_command_stderr_is_flat_json(tmp_path):
    """Error commands emit flat JSON to stderr with ok:false and failures list (TOOL-13, D-04)."""
    result = _run(["uc-status"], repo_root=str(tmp_path))
    try:
        payload = json.loads(result.stderr)
    except json.JSONDecodeError as exc:
        pytest.fail(f"stderr is not valid JSON: {exc}\nstderr: {result.stderr!r}")
    assert payload.get("ok") is False, f"Expected ok:false, got {payload}"
    assert isinstance(payload.get("failures"), list), \
        f"Expected failures:list, got {payload}"
    assert "data" not in payload, "Envelope must be flat (no nested 'data' key)"
