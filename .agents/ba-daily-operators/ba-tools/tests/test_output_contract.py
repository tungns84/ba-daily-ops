"""Integration tests for the output contract — all commands emit flat JSON (TOOL-13, CDX-05)."""

import json
import subprocess
import sys
import pytest

BA_TOOLS = [sys.executable, "-m", "ba_tools"]


def _run_stub_command(cmd_args: list[str], repo_root: str) -> subprocess.CompletedProcess:
    """Run a ba-tools stub command and return the completed process."""
    return subprocess.run(
        BA_TOOLS + ["--repo-root", repo_root] + cmd_args,
        capture_output=True,
        text=True,
    )


def test_error_command_exits_2(tmp_path):
    """BaToolsError commands exit 2 with ok:false and flat JSON on stderr (TOOL-13).

    Uses 'uc-status' on a directory with no STATE.md — a reliable error path
    that always raises BaToolsError(NO_STATE) and exits 2.
    (Wave-0 stub test updated in 01-06: all commands are now implemented.)
    """
    result = _run_stub_command(["uc-status"], str(tmp_path))
    assert result.returncode == 2, f"Expected exit 2, got {result.returncode}"


def test_error_command_stderr_is_flat_json(tmp_path):
    """Error commands emit flat JSON to stderr with ok:false and failures list (TOOL-13, D-04)."""
    result = _run_stub_command(["uc-status"], str(tmp_path))
    try:
        payload = json.loads(result.stderr)
    except json.JSONDecodeError as exc:
        pytest.fail(f"stderr is not valid JSON: {exc}\nstderr: {result.stderr!r}")
    assert payload.get("ok") is False, f"Expected ok:false, got {payload}"
    assert isinstance(payload.get("failures"), list), \
        f"Expected failures:list, got {payload}"
    assert "data" not in payload, "Envelope must be flat (no nested 'data' key)"


@pytest.mark.xfail(reason="Wave 1: success commands must emit flat ok:true envelope (TOOL-13)")
def test_success_command_stdout_is_flat_json(tmp_path):
    """A fully implemented command emits flat JSON to stdout with ok:true and failures:[]."""
    raise NotImplementedError


@pytest.mark.xfail(reason="Wave 1: no stack trace in error output (T-1-07)")
def test_no_stack_trace_in_error_output(tmp_path):
    """Error output never contains 'Traceback' or file path stack trace lines."""
    raise NotImplementedError
