"""Smoke tests for ba-tools command registration (Phase-2 Wave-0 scaffold).

Tests assert by command NAME present in parser subparser choices — NOT by
_COMMAND_MODULES list length (addresses Codex LOW "module-list length is brittle").
"""

import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Phase-1 registered command names (canonical list)
# Addresses: Codex LOW feedback — assert by name, not module-list length.
# Extension point: plan 03 adds "trace" and "index" to this list when those
# commands are wired into __main__.py.
# ---------------------------------------------------------------------------

PHASE_1_COMMANDS = [
    "init",
    "resolve-route",
    "state",
    "lint-requirements",
    "verify",
    "uc-status",
    "extract-uc",
    "template",
    "discovery",
    "scan",
    "byte-check",
    "confirm",
]

# ---------------------------------------------------------------------------
# EXTENSION POINT (plan 03): add "trace" and "index" to the list below once
# trace_cmd and index_cmd are registered in __main__.py.
# ---------------------------------------------------------------------------
# PHASE_2_COMMANDS = ["trace", "index"]  # uncomment in plan 03


class TestCommandsRegistered:
    """Assert each Phase-1 command name is discoverable via the built parser."""

    def test_commands_registered(self):
        """Every Phase-1 command name is present in the parser's subparser choices."""
        from ba_tools.__main__ import build_parser

        parser = build_parser()
        # The subparser choices dict keyed by command name
        subparser_choices = parser._subparsers._group_actions[0].choices
        registered_names = set(subparser_choices.keys())

        missing = [cmd for cmd in PHASE_1_COMMANDS if cmd not in registered_names]
        assert missing == [], (
            f"Expected all Phase-1 commands registered; missing: {missing}\n"
            f"Registered: {sorted(registered_names)}"
        )


@pytest.mark.parametrize("cmd_name", PHASE_1_COMMANDS)
def test_command_help_exits_zero(cmd_name):
    """Every Phase-1 command's --help exits 0 (not ImportError / AttributeError)."""
    result = subprocess.run(
        [sys.executable, "-m", "ba_tools", cmd_name, "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"`ba-tools {cmd_name} --help` exited {result.returncode}\n"
        f"stderr: {result.stderr[:500]}"
    )
    assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower(), (
        f"`ba-tools {cmd_name} --help` produced no usage line\n"
        f"stdout: {result.stdout[:300]}"
    )
